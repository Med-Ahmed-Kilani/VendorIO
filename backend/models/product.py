from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cost_per_unit: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    inventory_snapshots: Mapped[list["InventorySnapshot"]] = relationship(
        back_populates="product"
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def margin(self) -> Optional[float]:
        if self.cost_per_unit and self.unit_price and self.unit_price > 0:
            return (self.unit_price - self.cost_per_unit) / self.unit_price
        return None
