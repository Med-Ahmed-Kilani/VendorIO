from typing import Optional
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class FinalProduct(Base, TimestampMixin):
    __tablename__ = "final_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="product")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
