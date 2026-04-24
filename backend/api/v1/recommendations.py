from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.services.recommendation_service import generate_recommendations, get_potential_savings

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def list_recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    """Prioritised list of actionable recommendations (critical → low urgency)."""
    recs = generate_recommendations(db, limit=limit)
    total_savings = get_potential_savings(recs)
    return {
        "recommendations": recs,
        "count": len(recs),
        "total_potential_savings": total_savings,
    }


@router.post("/apply")
def apply_recommendation(
    payload: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Mark a recommendation as applied (tracking only — no DB state yet in MVP)."""
    return {
        "status": "applied",
        "recommendation_type": payload.get("type"),
        "product_id": payload.get("product_id"),
        "message": "Recommendation marked as applied",
    }
