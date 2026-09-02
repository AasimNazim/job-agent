from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.analytics import AnalyticsResponse

router = APIRouter(prefix="/api/dashboard/analytics", tags=["analytics"])

@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    range: str = Query("7d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db)
):
    service = DashboardService(db)
    return service.analytics(range)
