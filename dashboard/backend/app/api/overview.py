import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.overview import OverviewResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/dashboard/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    try:
        return DashboardService(db).overview()
    except Exception:
        logger.exception("Dashboard overview query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")
