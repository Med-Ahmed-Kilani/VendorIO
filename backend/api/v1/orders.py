from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.crud.order import order as order_crud
from backend.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from backend.schemas.common import PaginatedResponse
from backend.utils.errors import NotFoundError

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PaginatedResponse[OrderResponse]:
    """List orders with optional date filtering."""
    items, total = order_crud.get_multi_with_items(
        db, skip=skip, limit=limit, start_date=start_date, end_date=end_date
    )
    return PaginatedResponse(data=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    """Create a new order with line items."""
    return order_crud.create_with_items(db, obj_in=payload)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    """Retrieve an order by ID, including its line items."""
    o = order_crud.get_with_items(db, order_id)
    if not o:
        raise NotFoundError("Order", order_id)
    return o


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)
) -> OrderResponse:
    """Update an order's top-level fields."""
    o = order_crud.get(db, order_id)
    if not o:
        raise NotFoundError("Order", order_id)
    return order_crud.update(db, db_obj=o, obj_in=payload)


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an order."""
    o = order_crud.remove(db, id=order_id)
    if not o:
        raise NotFoundError("Order", order_id)
