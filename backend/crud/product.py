from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.crud.base import CRUDBase
from backend.models.product import Product
from backend.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_by_category(self, db: Session, category: str, skip: int = 0, limit: int = 100) -> list[Product]:
        return (
            db.query(Product)
            .filter(Product.category == category, Product.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> list[Product]:
        return (
            db.query(Product)
            .filter(Product.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_active(self, db: Session) -> int:
        return db.query(Product).filter(Product.deleted_at.is_(None)).count()

    def soft_delete(self, db: Session, *, product_id: int) -> Optional[Product]:
        p = self.get(db, product_id)
        if p:
            p.deleted_at = datetime.utcnow()
            db.commit()
            db.refresh(p)
        return p

    def get_categories(self, db: Session) -> list[str]:
        rows = (
            db.query(Product.category)
            .filter(Product.category.isnot(None), Product.deleted_at.is_(None))
            .distinct()
            .all()
        )
        return [r[0] for r in rows]


product = CRUDProduct(Product)
