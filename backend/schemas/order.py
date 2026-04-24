from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int


class OrderBase(BaseModel):
    order_date: datetime
    customer_id: Optional[int] = None
    total_amount: Optional[float] = None
    status: str = "completed"
    metadata_: dict = {}


class OrderCreate(OrderBase):
    items: list[OrderItemCreate] = []


class OrderUpdate(BaseModel):
    order_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    metadata_: Optional[dict] = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    items: list[OrderItemResponse] = []
