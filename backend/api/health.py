from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """Liveness probe — returns DB connectivity status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "db": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
