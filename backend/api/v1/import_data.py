"""CSV import endpoints for the recipe-based schema."""
import io
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.models.customer import Customer
from backend.models.final_product import FinalProduct
from backend.models.order import Order, OrderItem
from backend.models.raw_material import RawMaterial, RawMaterialInventory
from backend.models.recipe import Recipe, RecipeItem
from backend.models.transaction import Transaction
from backend.utils.logger import get_logger

router = APIRouter(prefix="/import", tags=["import"])
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared CSV helpers
# ---------------------------------------------------------------------------

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


# Size normalisation: accept "Small"/"Medium"/"Large" as well as "S"/"M"/"L"
_SIZE_MAP = {
    "s": "S", "small": "S",
    "m": "M", "medium": "M",
    "l": "L", "large": "L",
}
_VALID_SIZES = set(_SIZE_MAP.keys())


def _normalize_size(raw: Optional[str]) -> Optional[str]:
    """Return S/M/L from any capitalisation of Small/Medium/Large/S/M/L, or None."""
    if not raw:
        return None
    key = raw.strip().lower()
    return _SIZE_MAP.get(key)  # None if unrecognised


def _resolve_product(db, raw_id: str) -> Optional["FinalProduct"]:
    """Look up FinalProduct by numeric id, external_id, or name."""
    raw_id = str(raw_id).strip()
    try:
        result = db.query(FinalProduct).filter(FinalProduct.id == int(raw_id)).first()
        if result:
            return result
    except (ValueError, TypeError):
        pass
    # external_id match (e.g. "PRD-002")
    result = db.query(FinalProduct).filter(FinalProduct.external_id == raw_id).first()
    if result:
        return result
    # name match as last resort
    return db.query(FinalProduct).filter(FinalProduct.name == raw_id).first()


def _resolve_recipe(db, raw_id: str) -> Optional["Recipe"]:
    """Look up Recipe by numeric id or external_id (e.g. 'RCP-001')."""
    raw_id = str(raw_id).strip()
    try:
        result = db.query(Recipe).filter(Recipe.id == int(raw_id)).first()
        if result:
            return result
    except (ValueError, TypeError):
        pass
    return db.query(Recipe).filter(Recipe.external_id == raw_id).first()


def _resolve_order(db, raw_id: str) -> Optional["Order"]:
    """Look up Order by numeric id or by import_key stored in metadata (e.g. 'ORD-001')."""
    raw_id = str(raw_id).strip()
    try:
        result = db.query(Order).filter(Order.id == int(raw_id)).first()
        if result:
            return result
    except (ValueError, TypeError):
        pass
    return (
        db.query(Order)
        .filter(Order.metadata_["import_key"].astext == raw_id)
        .first()
    )


def _resolve_material(db, raw_id: str) -> Optional["RawMaterial"]:
    """Look up RawMaterial by numeric id, external_id (e.g. 'MAT-001'), or name."""
    raw_id = str(raw_id).strip()
    try:
        result = db.query(RawMaterial).filter(RawMaterial.id == int(raw_id)).first()
        if result:
            return result
    except (ValueError, TypeError):
        pass
    result = db.query(RawMaterial).filter(RawMaterial.external_id == raw_id).first()
    if result:
        return result
    return db.query(RawMaterial).filter(RawMaterial.name == raw_id).first()


# ---------------------------------------------------------------------------
# 1. Raw Materials
# ---------------------------------------------------------------------------

_RAW_MATERIALS_REQUIRED = {"name"}


@router.post("/raw_materials")
async def import_raw_materials(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import raw materials and seed their inventory.

    Required: name
    Optional: category, unit, cost_per_unit, current_stock, reorder_point, lead_time_days
    """
    df = _parse_csv(await file.read())
    missing = _RAW_MATERIALS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = updated = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            name = _opt_str(row, "name")
            if not name:
                skipped += 1
                continue

            # Store CSV material_id (e.g. "MAT-001") as external_id for cross-file resolution
            ext_id = _opt_str(row, "material_id")

            material = db.query(RawMaterial).filter(RawMaterial.name == name).first()
            if not material and ext_id:
                material = db.query(RawMaterial).filter(RawMaterial.external_id == ext_id).first()

            stock = _opt_int(row, "current_stock", default=0)

            if material:
                material.category = _opt_str(row, "category") or material.category
                material.unit = _opt_str(row, "unit") or material.unit
                cpu = _opt_float(row, "cost_per_unit")
                if cpu is not None:
                    material.cost_per_unit = cpu
                rp = _opt_int(row, "reorder_point")
                if rp is not None:
                    material.reorder_point = rp
                lt = _opt_int(row, "lead_time_days")
                if lt is not None:
                    material.lead_time_days = lt
                if ext_id and not material.external_id:
                    material.external_id = ext_id
                if stock is not None:
                    _upsert_inventory(db, material.id, stock)
                updated += 1
            else:
                material = RawMaterial(
                    name=name,
                    external_id=ext_id,
                    category=_opt_str(row, "category"),
                    unit=_opt_str(row, "unit") or "units",
                    cost_per_unit=_opt_float(row, "cost_per_unit"),
                    reorder_point=_opt_int(row, "reorder_point"),
                    lead_time_days=_opt_int(row, "lead_time_days", default=7),
                )
                db.add(material)
                db.flush()
                inv = RawMaterialInventory(material_id=material.id, current_stock=stock or 0)
                db.add(inv)
                created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"RawMaterials import: created={created} updated={updated} skipped={skipped}")
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors[:20]}


def _upsert_inventory(db: Session, material_id: int, stock: int) -> None:
    inv = (
        db.query(RawMaterialInventory)
        .filter(RawMaterialInventory.material_id == material_id)
        .order_by(RawMaterialInventory.id.desc())
        .first()
    )
    if inv:
        inv.current_stock = stock
    else:
        db.add(RawMaterialInventory(material_id=material_id, current_stock=stock))


# ---------------------------------------------------------------------------
# 2. Final Products
# ---------------------------------------------------------------------------

_FINAL_PRODUCTS_REQUIRED = {"name", "unit_price"}


@router.post("/products")
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import final products (sellable items, no cost here — cost lives in Recipes).

    Required: name, unit_price
    Optional: product_id (stored as external_id for cross-file lookups), category
    """
    df = _parse_csv(await file.read())
    missing = _FINAL_PRODUCTS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = updated = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
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

            # Store the CSV product_id (e.g. "PRD-002") as external_id for cross-file resolution
            ext_id = _opt_str(row, "product_id")

            product = db.query(FinalProduct).filter(FinalProduct.name == name).first()
            if not product and ext_id:
                product = db.query(FinalProduct).filter(FinalProduct.external_id == ext_id).first()

            if product:
                product.unit_price = unit_price
                product.category = _opt_str(row, "category") or product.category
                if ext_id and not product.external_id:
                    product.external_id = ext_id
                updated += 1
            else:
                product = FinalProduct(
                    name=name,
                    external_id=ext_id,
                    unit_price=unit_price,
                    category=_opt_str(row, "category"),
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
# 3. Recipes
# ---------------------------------------------------------------------------

_RECIPES_REQUIRED = {"product_id", "unit_cost"}


@router.post("/recipes")
async def import_recipes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import recipe headers (one row per product/size combination).

    Required: product_id, unit_cost
    Optional: size (S/M/L or blank for non-sized items)
    """
    df = _parse_csv(await file.read())
    missing = _RECIPES_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = updated = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            raw_pid = _opt_str(row, "product_id")
            if not raw_pid:
                errors.append(f"Row {row_num}: missing product_id")
                skipped += 1
                continue

            product = _resolve_product(db, raw_pid)
            if not product:
                errors.append(f"Row {row_num}: product '{raw_pid}' not found")
                skipped += 1
                continue

            unit_cost = _opt_float(row, "unit_cost")
            if unit_cost is None or unit_cost < 0:
                errors.append(f"Row {row_num}: invalid unit_cost")
                skipped += 1
                continue

            raw_size = _opt_str(row, "size")
            size = _normalize_size(raw_size)
            if raw_size and size is None:
                errors.append(f"Row {row_num}: size must be S/Small, M/Medium, L/Large or blank — got '{raw_size}'")
                skipped += 1
                continue

            # CSV recipe_id (e.g. "RCP-001") stored as external_id for cross-file resolution
            ext_rid = _opt_str(row, "recipe_id")

            recipe = (
                db.query(Recipe)
                .filter(Recipe.product_id == product.id, Recipe.size == size)
                .first()
            )
            if not recipe and ext_rid:
                recipe = db.query(Recipe).filter(Recipe.external_id == ext_rid).first()

            if recipe:
                recipe.unit_cost = unit_cost
                if ext_rid and not recipe.external_id:
                    recipe.external_id = ext_rid
                updated += 1
            else:
                db.add(Recipe(
                    product_id=product.id,
                    external_id=ext_rid,
                    size=size,
                    unit_cost=unit_cost,
                ))
                created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"Recipes import: created={created} updated={updated} skipped={skipped}")
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors[:20]}


# ---------------------------------------------------------------------------
# 4. Recipe Items
# ---------------------------------------------------------------------------

_RECIPE_ITEMS_REQUIRED = {"recipe_id", "material_id", "quantity_needed"}


@router.post("/recipe_items")
async def import_recipe_items(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import ingredient lines for recipes.

    Required: recipe_id, material_id, quantity_needed
    Optional: unit, notes
    """
    df = _parse_csv(await file.read())
    missing = _RECIPE_ITEMS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = updated = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            raw_rid = _opt_str(row, "recipe_id")
            raw_mid = _opt_str(row, "material_id")
            qty = _opt_float(row, "quantity_needed")

            if not raw_rid or not raw_mid or qty is None or qty <= 0:
                errors.append(f"Row {row_num}: recipe_id, material_id, and quantity_needed are required and must be positive")
                skipped += 1
                continue

            recipe = _resolve_recipe(db, raw_rid)
            if not recipe:
                errors.append(f"Row {row_num}: recipe '{raw_rid}' not found — import recipes first")
                skipped += 1
                continue

            recipe_id = recipe.id

            material = _resolve_material(db, raw_mid)
            if not material:
                errors.append(f"Row {row_num}: material '{raw_mid}' not found")
                skipped += 1
                continue

            item = (
                db.query(RecipeItem)
                .filter(RecipeItem.recipe_id == recipe_id, RecipeItem.material_id == material.id)
                .first()
            )
            if item:
                item.quantity_needed = qty
                item.unit = _opt_str(row, "unit") or item.unit
                item.notes = _opt_str(row, "notes") or item.notes
                updated += 1
            else:
                db.add(RecipeItem(
                    recipe_id=recipe_id,
                    material_id=material.id,
                    quantity_needed=qty,
                    unit=_opt_str(row, "unit"),
                    notes=_opt_str(row, "notes"),
                ))
                created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"RecipeItems import: created={created} updated={updated} skipped={skipped}")
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors[:20]}


# ---------------------------------------------------------------------------
# 5a. Raw Material Inventory  (update stock levels for existing materials)
# ---------------------------------------------------------------------------

_RMI_REQUIRED = {"material_id"}


@router.post("/raw_material_inventory")
async def import_raw_material_inventory(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update live stock levels for existing raw materials.
    Use this when you want to adjust inventory without re-importing material specs.

    Required: material_id (numeric) OR material_name
    Required (one of): current_stock
    """
    df = _parse_csv(await file.read())

    has_id = "material_id" in df.columns
    has_name = "material_name" in df.columns
    if not has_id and not has_name:
        raise HTTPException(
            status_code=400,
            detail="CSV must have either 'material_id' or 'material_name' column",
        )
    if "current_stock" not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required column: current_stock")

    updated = skipped = 0
    not_found: list[str] = []
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            material = None
            if has_id:
                raw_mid = _opt_str(row, "material_id")
                if raw_mid:
                    material = _resolve_material(db, raw_mid)
            if material is None and has_name:
                name = _opt_str(row, "material_name")
                if name:
                    material = db.query(RawMaterial).filter(RawMaterial.name == name).first()

            if not material:
                identifier = _opt_str(row, "material_id") or _opt_str(row, "material_name") or f"row {row_num}"
                not_found.append(str(identifier))
                skipped += 1
                continue

            stock = _opt_int(row, "current_stock")
            if stock is None:
                errors.append(f"Row {row_num}: missing current_stock")
                skipped += 1
                continue

            _upsert_inventory(db, material.id, stock)
            updated += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"RawMaterialInventory import: updated={updated} skipped={skipped}")
    return {"updated": updated, "skipped": skipped, "not_found": not_found[:20], "errors": errors[:20]}


# ---------------------------------------------------------------------------
# 5b. Order Items  (add line items to existing orders — relational 2-file format)
# ---------------------------------------------------------------------------

_ORDER_ITEMS_REQUIRED = {"order_id", "product_id", "quantity"}


@router.post("/order_items")
async def import_order_items(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import order line items for orders already in the database.
    Use this as the second file in a two-file (headers + items) import workflow.
    Hard-blocks rows where the product has no matching recipe.

    Required: order_id, product_id, quantity
    Optional: size, unit_price
    """
    df = _parse_csv(await file.read())
    missing = _ORDER_ITEMS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    # Pre-load all lookup tables into memory — avoids N×3 round-trip queries
    all_orders_by_id: dict[int, Order] = {o.id: o for o in db.query(Order).all()}
    all_orders_by_key: dict[str, Order] = {
        o.metadata_.get("import_key"): o
        for o in all_orders_by_id.values()
        if o.metadata_ and o.metadata_.get("import_key")
    }
    all_products_by_id: dict[int, FinalProduct] = {p.id: p for p in db.query(FinalProduct).all()}
    all_products_by_ext: dict[str, FinalProduct] = {
        p.external_id: p for p in all_products_by_id.values() if p.external_id
    }
    all_products_by_name: dict[str, FinalProduct] = {
        p.name: p for p in all_products_by_id.values()
    }
    # recipe lookup: (product_id, size) → Recipe
    all_recipes: dict[tuple, Recipe] = {
        (r.product_id, r.size): r for r in db.query(Recipe).all()
    }
    # Existing order items — keyed by (order_id, product_id, size) to detect duplicates.
    # NULL size is normalised to None so the key is consistent.
    existing_items: set[tuple] = {
        (oi.order_id, oi.product_id, oi.size)
        for oi in db.query(OrderItem).all()
    }

    def _fast_order(raw_id: str) -> Optional[Order]:
        try:
            return all_orders_by_id.get(int(raw_id))
        except (ValueError, TypeError):
            pass
        return all_orders_by_key.get(raw_id)

    def _fast_product(raw_id: str) -> Optional[FinalProduct]:
        try:
            p = all_products_by_id.get(int(raw_id))
            if p:
                return p
        except (ValueError, TypeError):
            pass
        return all_products_by_ext.get(raw_id) or all_products_by_name.get(raw_id)

    created = skipped = 0
    errors: list[str] = []
    order_totals: dict[int, float] = {}

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            raw_oid = _opt_str(row, "order_id")
            raw_pid = _opt_str(row, "product_id")
            qty = _opt_int(row, "quantity")

            if not raw_oid or not raw_pid or not qty or qty <= 0:
                errors.append(f"Row {row_num}: order_id, product_id, and quantity are required")
                skipped += 1
                continue

            order = _fast_order(raw_oid)
            if not order:
                errors.append(f"Row {row_num}: order '{raw_oid}' not found — import orders first")
                skipped += 1
                continue

            product = _fast_product(raw_pid)
            if not product:
                errors.append(f"Row {row_num}: product '{raw_pid}' not found")
                skipped += 1
                continue

            raw_size = _opt_str(row, "size")
            size = _normalize_size(raw_size)
            if raw_size and size is None:
                errors.append(f"Row {row_num}: size must be S/Small, M/Medium, L/Large or blank — got '{raw_size}'")
                skipped += 1
                continue

            recipe = all_recipes.get((product.id, size))
            if not recipe:
                size_label = f" (size={size})" if size else ""
                errors.append(
                    f"Row {row_num}: no recipe for product '{raw_pid}'{size_label} — import recipes first"
                )
                skipped += 1
                continue

            unit_price = _opt_float(row, "unit_price") or float(product.unit_price)
            unit_cost = float(recipe.unit_cost)
            line_total = round(unit_price * qty, 2)

            key = (order.id, product.id, size)
            if key in existing_items:
                errors.append(f"Row {row_num}: duplicate (order+product+size already imported)")
                skipped += 1
                continue

            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                recipe_id=recipe.id,
                size=size,
                quantity=qty,
                unit_price=round(unit_price, 2),
                unit_cost=round(unit_cost, 4),
                line_total=line_total,
            ))
            existing_items.add(key)
            order_totals[order.id] = order_totals.get(order.id, 0.0) + line_total
            created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)[:120]}")
            skipped += 1

    # Update order total_amount
    for oid, extra in order_totals.items():
        o = all_orders_by_id.get(oid)
        if o:
            o.total_amount = round((float(o.total_amount or 0)) + extra, 2)

    db.commit()
    _refresh_customer_stats(db)
    db.commit()
    logger.info(f"OrderItems import: created={created} skipped={skipped}")
    return {"created": created, "skipped": skipped, "errors": errors[:20]}


# ---------------------------------------------------------------------------
# 6. Orders  (hard-block if no recipe for product/size)
# ---------------------------------------------------------------------------

@router.post("/orders")
async def import_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import orders. Supports two CSV formats automatically:

    **Relational (headers-only)** — one row per order, no product columns:
      Required: order_date
      Optional: order_id (stored as import_key), customer_email, total_amount, status

    **Flat (line-items)** — one row per order line item, includes product:
      Required: order_date, product_id, quantity
      Optional: order_id, size, customer_email, unit_price, status
      Hard-blocks rows where the product has no matching recipe.
    """
    df = _parse_csv(await file.read())
    if "order_date" not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required column: order_date")

    # Detect format: if neither product_id nor quantity present → headers-only
    flat_mode = "product_id" in df.columns and "quantity" in df.columns
    has_order_id = "order_id" in df.columns
    has_email = "customer_email" in df.columns

    orders_created = items_created = skipped = 0
    errors: list[str] = []

    if not flat_mode:
        # ── Relational / headers-only format ──────────────────────────────
        # Pre-load all existing import_keys in one query — avoids per-row table scans
        existing_keys: set[str] = {
            o.metadata_.get("import_key")
            for o in db.query(Order).all()
            if o.metadata_ and o.metadata_.get("import_key")
        }

        for i, row in df.iterrows():
            row_num = int(i) + 2
            try:
                order_date_raw = _opt_str(row, "order_date")
                if not order_date_raw:
                    errors.append(f"Row {row_num}: missing order_date")
                    skipped += 1
                    continue

                order_date = pd.to_datetime(order_date_raw)
                import_key = _opt_str(row, "order_id") or f"row-{row_num}"
                status = _opt_str(row, "status") or "completed"
                total_amount = _opt_float(row, "total_amount")

                customer_id = None
                if has_email:
                    email = _opt_str(row, "customer_email")
                    if email:
                        customer = _get_or_create_customer(db, email)
                        customer_id = customer.id

                if import_key in existing_keys:
                    skipped += 1
                    continue

                order = Order(
                    order_date=order_date,
                    customer_id=customer_id,
                    status=status,
                    total_amount=total_amount,
                    metadata_={"source": "csv_import", "import_key": import_key},
                )
                db.add(order)
                existing_keys.add(import_key)
                orders_created += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {e}")
                skipped += 1

        db.commit()
        _refresh_customer_stats(db)
        db.commit()
        logger.info(f"Orders import (relational): orders={orders_created} skipped={skipped}")
        return {"orders_created": orders_created, "items_created": 0, "skipped": skipped, "errors": errors[:20]}

    # ── Flat / line-items format ───────────────────────────────────────────
    def _group_key(row: pd.Series) -> str:
        if has_order_id and _opt_str(row, "order_id"):
            return str(row["order_id"]).strip()
        date_str = str(row["order_date"]).strip()
        email = _opt_str(row, "customer_email") or "anonymous"
        return f"{date_str}|{email}"

    df["_group"] = df.apply(_group_key, axis=1)
    groups = df.groupby("_group", sort=False)

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
            group_had_error = False

            for row_i, row in group_df.iterrows():
                row_num = int(row_i) + 2
                raw_pid = _opt_str(row, "product_id")
                if not raw_pid:
                    errors.append(f"Row {row_num}: missing product_id")
                    group_had_error = True
                    continue

                product = _resolve_product(db, raw_pid)
                if not product:
                    errors.append(f"Row {row_num}: product '{raw_pid}' not found")
                    group_had_error = True
                    continue

                qty = _opt_int(row, "quantity")
                if not qty or qty <= 0:
                    errors.append(f"Row {row_num}: invalid quantity")
                    group_had_error = True
                    continue

                raw_size = _opt_str(row, "size")
                size = _normalize_size(raw_size)
                if raw_size and size is None:
                    errors.append(f"Row {row_num}: size must be S/Small, M/Medium, L/Large or blank — got '{raw_size}'")
                    group_had_error = True
                    continue

                recipe = (
                    db.query(Recipe)
                    .filter(Recipe.product_id == product.id, Recipe.size == size)
                    .first()
                )
                if not recipe:
                    size_label = f" (size={size})" if size else ""
                    errors.append(
                        f"Row {row_num}: no recipe found for product '{raw_pid}'{size_label}. "
                        f"Import recipes.csv first."
                    )
                    group_had_error = True
                    continue

                unit_price = _opt_float(row, "unit_price") or float(product.unit_price)
                unit_cost = float(recipe.unit_cost)
                line_total = round(unit_price * qty, 2)
                order_total += line_total

                db.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    recipe_id=recipe.id,
                    size=size,
                    quantity=qty,
                    unit_price=round(unit_price, 2),
                    unit_cost=round(unit_cost, 4),
                    line_total=line_total,
                ))
                items_created += 1

            if group_had_error:
                db.expunge(order)
                skipped += 1
            else:
                order.total_amount = round(order_total, 2)
                orders_created += 1

        except Exception as e:
            errors.append(f"Group '{group_key}': {e}")
            skipped += 1

    db.commit()
    _refresh_customer_stats(db)
    db.commit()
    logger.info(f"Orders import (flat): orders={orders_created} items={items_created} skipped={skipped}")
    return {
        "orders_created": orders_created,
        "items_created": items_created,
        "skipped": skipped,
        "errors": errors[:20],
    }


def _get_or_create_customer(db: Session, email: str) -> Customer:
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        customer = Customer(email=email, order_count=0)
        db.add(customer)
        db.flush()
    return customer


def _refresh_customer_stats(db: Session) -> None:
    from sqlalchemy import func as _func
    rows = (
        db.query(
            Order.customer_id,
            _func.count(Order.id).label("order_count"),
            _func.sum(Order.total_amount).label("total_spent"),
            _func.min(Order.order_date).label("first_order"),
        )
        .filter(Order.customer_id.isnot(None), Order.status == "completed")
        .group_by(Order.customer_id)
        .all()
    )
    for row in rows:
        customer = db.query(Customer).filter(Customer.id == row.customer_id).first()
        if customer:
            customer.order_count = row.order_count
            customer.total_spent = float(row.total_spent or 0)
            if row.first_order:
                customer.first_order_date = (
                    row.first_order.date()
                    if hasattr(row.first_order, "date")
                    else row.first_order
                )


# ---------------------------------------------------------------------------
# 6. Transactions
# ---------------------------------------------------------------------------

_TRANSACTIONS_REQUIRED = {"order_id", "amount_paid"}


@router.post("/transactions")
async def import_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Import payment transactions.

    Required: order_id, amount_paid
    Optional: payment_method
    """
    df = _parse_csv(await file.read())
    missing = _TRANSACTIONS_REQUIRED - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {sorted(missing)}")

    created = skipped = 0
    errors: list[str] = []

    for i, row in df.iterrows():
        row_num = int(i) + 2
        try:
            raw_oid = _opt_str(row, "order_id")
            amount = _opt_float(row, "amount_paid")

            if not raw_oid or amount is None or amount < 0:
                errors.append(f"Row {row_num}: order_id and amount_paid are required")
                skipped += 1
                continue

            order = _resolve_order(db, raw_oid)
            if not order:
                errors.append(f"Row {row_num}: order '{raw_oid}' not found")
                skipped += 1
                continue

            db.add(Transaction(
                order_id=order.id,
                amount_paid=round(amount, 2),
                payment_method=_opt_str(row, "payment_method"),
            ))
            created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {e}")
            skipped += 1

    db.commit()
    logger.info(f"Transactions import: created={created} skipped={skipped}")
    return {"created": created, "skipped": skipped, "errors": errors[:20]}


# ---------------------------------------------------------------------------
# Clear all data
# ---------------------------------------------------------------------------

@router.post("/clear")
def clear_all_data(
    confirm: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    """Delete all imported data in dependency order."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Pass confirm=true to delete all data. This cannot be undone.",
        )
    counts = {}
    counts["transactions"] = db.query(Transaction).delete()
    counts["order_items"] = db.query(OrderItem).delete()
    counts["orders"] = db.query(Order).delete()
    counts["customers"] = db.query(Customer).delete()
    counts["recipe_items"] = db.query(RecipeItem).delete()
    counts["recipes"] = db.query(Recipe).delete()
    counts["final_products"] = db.query(FinalProduct).delete()
    counts["raw_material_inventory"] = db.query(RawMaterialInventory).delete()
    counts["raw_materials"] = db.query(RawMaterial).delete()
    db.commit()
    logger.warning(f"All data cleared: {counts}")
    return {"deleted": counts}
