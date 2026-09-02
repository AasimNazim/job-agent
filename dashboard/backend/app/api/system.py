import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.auth import require_dashboard_auth
from app.db import get_db
from app.schemas.system import SystemStatusResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/dashboard/system", response_model=SystemStatusResponse, dependencies=[Depends(require_dashboard_auth)])
def get_system_status(db: Session = Depends(get_db)):
    try:
        return DashboardService(db).system_status()
    except Exception:
        logger.exception("Dashboard system query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        logger.exception("Dashboard health check failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")
