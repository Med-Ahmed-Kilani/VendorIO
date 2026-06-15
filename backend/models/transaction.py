from typing import Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=False, index=True
    )
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="transactions")
