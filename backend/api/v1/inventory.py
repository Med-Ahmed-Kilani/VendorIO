from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.services import inventory_service
from backend.schemas.inventory import InventoryStatusItem, InventoryHealthResponse
from backend.utils.errors import NotFoundError

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/status", response_model=list[InventoryStatusItem])
def inventory_status(db: Session = Depends(get_db)) -> list[InventoryStatusItem]:
    """Current stock levels, turnover rates, and reorder flags for all products."""
    return inventory_service.get_inventory_status(db)


@router.get("/{product_id}/health", response_model=InventoryHealthResponse)
def product_inventory_health(
    product_id: int, db: Session = Depends(get_db)
) -> InventoryHealthResponse:
    """Detailed inventory health for a single product: DTS, holding cost, EOQ, turnover rank."""
    result = inventory_service.get_product_health(db, product_id)
    if not result:
        raise NotFoundError("Product", product_id)
    return result


@router.post("/sync", status_code=200)
def sync_inventory(db: Session = Depends(get_db)) -> dict:
    """Recalculate all inventory metrics and persist snapshots."""
    from datetime import date
    from backend.crud.inventory import inventory_snapshot as snapshot_crud
    from backend.models.product import Product
    from backend.config import settings

    HOLDING_COST_RATE = settings.holding_cost_rate
    products = db.query(Product).filter(Product.deleted_at.is_(None)).all()
    today = date.today()
    snapshots = []
    for p in products:
        holding = float(p.cost_per_unit or p.unit_price) * p.current_stock * HOLDING_COST_RATE / 12
        snapshots.append({
            "product_id": p.id,
            "stock_level": p.current_stock,
            "holding_cost": round(holding, 2),
            "snapshot_date": today,
        })
    snapshot_crud.bulk_create(db, snapshots=snapshots)
    return {"synced": len(snapshots), "date": str(today)}
