from typing import Optional
from sqlalchemy.orm import Session
from backend.crud.base import CRUDBase
from backend.models.final_product import FinalProduct
from backend.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct(CRUDBase[FinalProduct, ProductCreate, ProductUpdate]):
    def get_by_category(self, db: Session, category: str, skip: int = 0, limit: int = 100) -> list[FinalProduct]:
        return (
            db.query(FinalProduct)
            .filter(FinalProduct.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> list[FinalProduct]:
        return db.query(FinalProduct).offset(skip).limit(limit).all()

    def count_active(self, db: Session) -> int:
        return db.query(FinalProduct).count()

    def get_categories(self, db: Session) -> list[str]:
        rows = (
            db.query(FinalProduct.category)
            .filter(FinalProduct.category.isnot(None))
            .distinct()
            .all()
        )
        return [r[0] for r in rows]

    # soft_delete kept for API compatibility but now does a hard delete
    def soft_delete(self, db: Session, *, product_id: int) -> Optional[FinalProduct]:
        p = self.get(db, product_id)
        if p:
            db.delete(p)
            db.commit()
        return p


product = CRUDProduct(FinalProduct)
