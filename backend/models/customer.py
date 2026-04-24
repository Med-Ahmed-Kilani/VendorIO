from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    first_order_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_spent: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    customer_attributes: Mapped[dict] = mapped_column(JSONB, default=dict)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
