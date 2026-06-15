from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=True, index=True
    )
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="orders")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", "size", name="uq_order_product_size"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("final_products.id"), nullable=False, index=True
    )
    recipe_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("recipes.id"), nullable=True, index=True
    )
    size: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    line_total: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["FinalProduct"] = relationship(back_populates="order_items")
    recipe: Mapped[Optional["Recipe"]] = relationship(back_populates="order_items")
