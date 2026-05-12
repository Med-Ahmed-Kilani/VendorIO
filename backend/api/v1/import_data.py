"""CSV import endpoints for products and orders."""
import io
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models.customer import Customer
from backend.models.order import Order, OrderItem
from backend.models.product import Product
from backend.utils.logger import get_logger

router = APIRouter(prefix="/import", tags=["import"])
logger = get_logger(__name__)

_PRODUCTS_REQUIRED = {"name", "unit_price"}
_ORDERS_REQUIRED = {"order_date", "product_name", "quantity"}


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _parse_csv(content: bytes) -> pd.DataFrame:
    try:
        return _normalize_cols(pd.read_csv(io.BytesIO(content)))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")


def _opt_float(row: pd.Series, col: str) -> Optional[float]:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _opt_int(row: pd.Series, col: str, default: Optional[int] = None) -> Optional[int]:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _opt_str(row: pd.Series, col: str) -> Optional[str]:
    val = row.get(col)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@router.post("/products")
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import products from a CSV file. Upserts by product name.

    Required columns: name, unit_price
    Optional columns: category, cost_per_unit, current_stock, reorder_point, lead_time_days
    """
    df = _parse_csv(await file.read())

    missing = _PRODUCTS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = updated = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2  # 1-indexed + header row
        try:
            name = _opt_str(row, "name")
            if not name:
                skipped += 1
                continue

            unit_price = _opt_float(row, "unit_price")
            if unit_price is None or unit_price < 0:
                errors.append(f"Row {row_num}: invalid unit_price")
                skipped += 1
                continue

            product = db.query(Product).filter(Product.name == name).first()
            if product:
                product.unit_price = unit_price
                product.category = _opt_str(row, "category") or product.category
                product.cost_per_unit = _opt_float(row, "cost_per_unit") or product.cost_per_unit
                stock = _opt_int(row, "current_stock")
                if stock is not None:
                    product.current_stock = stock
                rp = _opt_int(row, "reorder_point")
                if rp is not None:
                    product.reorder_point = rp
                lt = _opt_int(row, "lead_time_days")
                if lt is not None:
                    product.lead_time_days = lt
                updated += 1
            else:
                product = Product(
                    name=name,
                    unit_price=unit_price,
                    category=_opt_str(row, "category"),
                    cost_per_unit=_opt_float(row, "cost_per_unit"),
                    current_stock=_opt_int(row, "current_stock", default=0),
                    reorder_point=_opt_int(row, "reorder_point"),
                    lead_time_days=_opt_int(row, "lead_time_days", default=7),
                )
                db.add(product)
                created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"Products import: created={created} updated={updated} skipped={skipped}")
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors[:20]}


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def _get_or_create_product(db: Session, name: str, unit_price: float) -> Product:
    product = db.query(Product).filter(Product.name == name).first()
    if not product:
        product = Product(
            name=name,
            unit_price=unit_price,
            category="Imported",
            cost_per_unit=round(unit_price * 0.5, 2),
            current_stock=0,
            lead_time_days=7,
        )
        db.add(product)
        db.flush()
    return product


def _get_or_create_customer(db: Session, email: str) -> Customer:
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        customer = Customer(email=email, order_count=0)
        db.add(customer)
        db.flush()
    return customer


@router.post("/orders")
async def import_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import orders from a flat line-items CSV. Groups rows into orders by order_id
    (if present) or by (order_date, customer_email).

    Required columns: order_date, product_name, quantity
    Optional columns: order_id, customer_email, unit_price, status
    """
    df = _parse_csv(await file.read())

    missing = _ORDERS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    has_order_id = "order_id" in df.columns
    has_email = "customer_email" in df.columns

    # Build grouping key for each row
    def _group_key(row: pd.Series) -> str:
        if has_order_id and _opt_str(row, "order_id"):
            return str(row["order_id"]).strip()
        date_str = str(row["order_date"]).strip()
        email = _opt_str(row, "customer_email") or "anonymous"
        return f"{date_str}|{email}"

    df["_group"] = df.apply(_group_key, axis=1)
    groups = df.groupby("_group", sort=False)

    orders_created = items_created = skipped = 0
    errors: list[str] = []

    for group_key, group_df in groups:
        try:
            first = group_df.iloc[0]
            order_date = pd.to_datetime(str(first["order_date"]).strip())
            status = _opt_str(first, "status") or "completed"

            customer_id = None
            if has_email:
                email = _opt_str(first, "customer_email")
                if email:
                    customer = _get_or_create_customer(db, email)
                    customer_id = customer.id

            order = Order(
                order_date=order_date,
                customer_id=customer_id,
                status=status,
                metadata_={"source": "csv_import", "import_key": str(group_key)},
            )
            db.add(order)
            db.flush()

            order_total = 0.0
            for row_i, row in group_df.iterrows():
                row_num = int(row_i) + 2
                product_name = _opt_str(row, "product_name")
                if not product_name:
                    errors.append(f"Row {row_num}: empty product_name, skipped")
                    skipped += 1
                    continue

                qty = _opt_int(row, "quantity")
                if not qty or qty <= 0:
                    errors.append(f"Row {row_num}: invalid quantity, skipped")
                    skipped += 1
                    continue

                unit_price_col = _opt_float(row, "unit_price")
                product = _get_or_create_product(
                    db, product_name, unit_price_col or 0.0
                )
                unit_price = unit_price_col or float(product.unit_price)
                line_total = round(unit_price * qty, 2)
                order_total += line_total

                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=round(unit_price, 2),
                    line_total=line_total,
                )
                db.add(item)
                items_created += 1

            order.total_amount = round(order_total, 2)
            orders_created += 1

        except Exception as e:
            errors.append(f"Group '{group_key}': {e}")
            skipped += 1

    db.commit()
    logger.info(
        f"Orders import: orders={orders_created} items={items_created} skipped={skipped}"
    )
    return {
        "orders_created": orders_created,
        "items_created": items_created,
        "skipped": skipped,
        "errors": errors[:20],
    }


# ---------------------------------------------------------------------------
# Clear data
# ---------------------------------------------------------------------------

@router.post("/clear")
def clear_all_data(
    confirm: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    """Delete all imported data (order_items → orders → customers → products)."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Pass confirm=true to delete all data. This cannot be undone.",
        )
    counts = {}
    counts["order_items"] = db.query(OrderItem).delete()
    counts["orders"] = db.query(Order).delete()
    counts["customers"] = db.query(Customer).delete()
    counts["products"] = db.query(Product).delete()
    db.commit()
    logger.warning(f"All data cleared: {counts}")
    return {"deleted": counts}
