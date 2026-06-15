from typing import Optional
from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin


class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("final_products.id"), nullable=False, index=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    size: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # S, M, L or NULL
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0)

    product: Mapped["FinalProduct"] = relationship(back_populates="recipes")
    items: Mapped[list["RecipeItem"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="recipe")


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id"), nullable=False, index=True
    )
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("raw_materials.id"), nullable=False, index=True
    )
    quantity_needed: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    recipe: Mapped["Recipe"] = relationship(back_populates="items")
    material: Mapped["RawMaterial"] = relationship(back_populates="recipe_items")
