from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.optimization import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead)
def health(db: Session = Depends(get_db)) -> HealthRead:
    database_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"
    return HealthRead(
        status="ok" if database_status == "connected" else "degraded",
        database=database_status,
        ai_provider=settings.ai_provider,
        ai_configured=settings.ai_configured,
    )
