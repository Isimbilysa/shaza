from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness plus a real query, so a broken database cannot report healthy."""
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        database = "up"
    except Exception:  # noqa: BLE001 - the endpoint's job is to report, not raise
        database = "down"

    return {
        "ok": database == "up",
        "data": {
            "service": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "database": database,
            "engine": "postgresql" if settings.is_postgres else "sqlite",
        },
    }
