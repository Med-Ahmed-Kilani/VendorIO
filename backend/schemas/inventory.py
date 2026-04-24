from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class InventorySnapshotBase(BaseModel):
    product_id: int
    stock_level: Optional[int] = None
    holding_cost: Optional[float] = None
    snapshot_date: Optional[date] = None


class InventorySnapshotCreate(InventorySnapshotBase):
    pass


class InventorySnapshotResponse(InventorySnapshotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InventoryStatusItem(BaseModel):
    product_id: int
    product_name: str
    category: Optional[str]
    current_stock: int
    reorder_point: Optional[int]
    days_to_stockout: Optional[float]
    turnover_rate: Optional[float]
    holding_cost_monthly: Optional[float]
    status: str  # "ok" | "warning" | "critical"
    needs_reorder: bool


class InventoryHealthResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    days_to_stockout: Optional[float]
    holding_cost_monthly: Optional[float]
    turnover_rate: Optional[float]
    turnover_rank: Optional[str]  # "fast", "average", "slow"
    reorder_point: Optional[int]
    economic_order_qty: Optional[float]
    status: str
