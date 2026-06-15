from typing import Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class RawMaterial(Base, TimestampMixin):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # grams, ml, pieces
    cost_per_unit: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)

    inventory: Mapped[list["RawMaterialInventory"]] = relationship(
        back_populates="material", cascade="all, delete-orphan"
    )
    recipe_items: Mapped[list["RecipeItem"]] = relationship(back_populates="material")


class RawMaterialInventory(Base, TimestampMixin):
    __tablename__ = "raw_material_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("raw_materials.id"), nullable=False, index=True
    )
    current_stock: Mapped[int] = mapped_column(Integer, default=0)

    material: Mapped["RawMaterial"] = relationship(back_populates="inventory")
