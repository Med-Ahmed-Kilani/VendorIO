from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    unit_price: float
    cost_per_unit: Optional[float] = None
    current_stock: int = 0
    lead_time_days: int = 7
    reorder_point: Optional[int] = None
    attributes: dict = {}

    @field_validator("unit_price", "cost_per_unit", mode="before")
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price values must be non-negative")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    cost_per_unit: Optional[float] = None
    current_stock: Optional[int] = None
    lead_time_days: Optional[int] = None
    reorder_point: Optional[int] = None
    attributes: Optional[dict] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    margin: Optional[float] = None
