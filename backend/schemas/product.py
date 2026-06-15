from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    unit_price: float

    @field_validator("unit_price", mode="before")
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("unit_price must be non-negative")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
