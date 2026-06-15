from typing import Optional
from pydantic import BaseModel, ConfigDict


class RawMaterialInventoryBase(BaseModel):
    material_id: int
    current_stock: int = 0


class RawMaterialInventoryCreate(RawMaterialInventoryBase):
    pass


class RawMaterialInventoryResponse(RawMaterialInventoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InventoryStatusItem(BaseModel):
    product_id: int       # maps to material_id in new schema
    product_name: str     # maps to material name
    category: Optional[str]
    current_stock: int
    reorder_point: Optional[int]
    days_to_stockout: Optional[float]
    turnover_rate: Optional[float]
    holding_cost_monthly: Optional[float]
    status: str           # "ok" | "warning" | "critical"
    needs_reorder: bool


class InventoryHealthResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    days_to_stockout: Optional[float]
    holding_cost_monthly: Optional[float]
    turnover_rate: Optional[float]
    turnover_rank: Optional[str]   # "fast" | "average" | "slow"
    reorder_point: Optional[int]
    economic_order_qty: Optional[float]
    status: str
