from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.crud.product import product as product_crud
from backend.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from backend.schemas.common import PaginatedResponse
from backend.utils.errors import NotFoundError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProductResponse]:
    """List all active products, optionally filtered by category."""
    if category:
        items = product_crud.get_by_category(db, category=category, skip=skip, limit=limit)
        total = len(items)
    else:
        items = product_crud.get_active(db, skip=skip, limit=limit)
        total = product_crud.count_active(db)
    return PaginatedResponse(data=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    """Create a new product."""
    return product_crud.create(db, obj_in=payload)


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)) -> list[str]:
    """Return all distinct product categories."""
    return product_crud.get_categories(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Retrieve a product by ID."""
    p = product_crud.get(db, product_id)
    if not p or p.is_deleted:
        raise NotFoundError("Product", product_id)
    return p


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)
) -> ProductResponse:
    """Update a product."""
    p = product_crud.get(db, product_id)
    if not p or p.is_deleted:
        raise NotFoundError("Product", product_id)
    return product_crud.update(db, db_obj=p, obj_in=payload)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    """Soft-delete a product."""
    p = product_crud.soft_delete(db, product_id=product_id)
    if not p:
        raise NotFoundError("Product", product_id)
