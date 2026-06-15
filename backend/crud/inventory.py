from typing import Optional
from sqlalchemy.orm import Session
from backend.crud.base import CRUDBase
from backend.models.raw_material import RawMaterialInventory
from backend.schemas.inventory import RawMaterialInventoryCreate, RawMaterialInventoryBase


class CRUDRawMaterialInventory(
    CRUDBase[RawMaterialInventory, RawMaterialInventoryCreate, RawMaterialInventoryBase]
):
    def get_latest_for_material(
        self, db: Session, material_id: int
    ) -> Optional[RawMaterialInventory]:
        return (
            db.query(RawMaterialInventory)
            .filter(RawMaterialInventory.material_id == material_id)
            .order_by(RawMaterialInventory.id.desc())
            .first()
        )

    def upsert_stock(self, db: Session, material_id: int, current_stock: int) -> RawMaterialInventory:
        row = self.get_latest_for_material(db, material_id)
        if row:
            row.current_stock = current_stock
            db.commit()
            db.refresh(row)
            return row
        row = RawMaterialInventory(material_id=material_id, current_stock=current_stock)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


raw_material_inventory = CRUDRawMaterialInventory(RawMaterialInventory)
