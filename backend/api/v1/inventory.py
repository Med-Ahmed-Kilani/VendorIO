from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.services import inventory_service
from backend.schemas.inventory import InventoryStatusItem, InventoryHealthResponse
from backend.utils.errors import NotFoundError

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/status", response_model=list[InventoryStatusItem])
def inventory_status(db: Session = Depends(get_db)) -> list[InventoryStatusItem]:
    """Current stock levels, turnover rates, and reorder flags for all raw materials."""
    return inventory_service.get_inventory_status(db)


@router.get("/{material_id}/health", response_model=InventoryHealthResponse)
def material_inventory_health(
    material_id: int, db: Session = Depends(get_db)
) -> InventoryHealthResponse:
    """Detailed inventory health for a single raw material: DTS, holding cost, EOQ, turnover rank."""
    result = inventory_service.get_product_health(db, material_id)
    if not result:
        raise NotFoundError("Material", material_id)
    return result


@router.post("/sync", status_code=200)
def sync_inventory(db: Session = Depends(get_db)) -> dict:
    """Refresh inventory metrics — returns current status counts."""
    statuses = inventory_service.get_inventory_status(db)
    critical = sum(1 for s in statuses if s.status == "critical")
    warning = sum(1 for s in statuses if s.status == "warning")
    needs_reorder = sum(1 for s in statuses if s.needs_reorder)
    return {
        "synced": len(statuses),
        "critical": critical,
        "warning": warning,
        "needs_reorder": needs_reorder,
    }
