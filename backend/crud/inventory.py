from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from backend.crud.base import CRUDBase
from backend.models.inventory import InventorySnapshot
from backend.schemas.inventory import InventorySnapshotCreate, InventorySnapshotBase


class CRUDInventorySnapshot(CRUDBase[InventorySnapshot, InventorySnapshotCreate, InventorySnapshotBase]):
    def get_latest_for_product(self, db: Session, product_id: int) -> Optional[InventorySnapshot]:
        return (
            db.query(InventorySnapshot)
            .filter(InventorySnapshot.product_id == product_id)
            .order_by(InventorySnapshot.snapshot_date.desc(), InventorySnapshot.created_at.desc())
            .first()
        )

    def get_history_for_product(
        self, db: Session, product_id: int, limit: int = 30
    ) -> list[InventorySnapshot]:
        return (
            db.query(InventorySnapshot)
            .filter(InventorySnapshot.product_id == product_id)
            .order_by(InventorySnapshot.snapshot_date.desc())
            .limit(limit)
            .all()
        )

    def bulk_create(self, db: Session, *, snapshots: list[dict]) -> list[InventorySnapshot]:
        db_objs = [InventorySnapshot(**s) for s in snapshots]
        db.bulk_save_objects(db_objs)
        db.commit()
        return db_objs


inventory_snapshot = CRUDInventorySnapshot(InventorySnapshot)
