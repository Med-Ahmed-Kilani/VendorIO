from datetime import date, datetime
from typing import Optional
from sqlalchemy import Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class InventorySnapshot(Base, TimestampMixin):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    stock_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    holding_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    snapshot_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    product: Mapped["Product"] = relationship(back_populates="inventory_snapshots")
