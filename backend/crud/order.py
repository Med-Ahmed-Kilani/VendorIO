from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from backend.crud.base import CRUDBase
from backend.models.order import Order, OrderItem
from backend.schemas.order import OrderCreate, OrderUpdate


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    def get_with_items(self, db: Session, order_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.id == order_id)
            .first()
        )

    def get_multi_with_items(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[Order], int]:
        q = db.query(Order).options(joinedload(Order.items))
        if start_date:
            q = q.filter(Order.order_date >= start_date)
        if end_date:
            q = q.filter(Order.order_date <= end_date)
        total = q.count()
        rows = q.order_by(Order.order_date.desc()).offset(skip).limit(limit).all()
        return rows, total

    def create_with_items(self, db: Session, *, obj_in: OrderCreate) -> Order:
        items_data = obj_in.items
        order_data = obj_in.model_dump(exclude={"items"})
        db_order = Order(**order_data)
        db.add(db_order)
        db.flush()
        for item in items_data:
            db_item = OrderItem(order_id=db_order.id, **item.model_dump())
            if db_item.unit_price and db_item.quantity:
                db_item.line_total = db_item.unit_price * db_item.quantity
            db.add(db_item)
        if not db_order.total_amount:
            db_order.total_amount = sum(
                (i.unit_price or 0) * i.quantity for i in items_data
            )
        db.commit()
        db.refresh(db_order)
        return db_order

    def get_revenue_by_date(
        self, db: Session, start_date: datetime, end_date: datetime
    ) -> list[tuple]:
        return (
            db.query(
                func.date(Order.order_date).label("date"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("order_count"),
            )
            .filter(Order.order_date >= start_date, Order.order_date <= end_date)
            .group_by(func.date(Order.order_date))
            .order_by(func.date(Order.order_date))
            .all()
        )


order = CRUDOrder(Order)
