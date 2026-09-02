from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.companies import CompaniesResponse

router = APIRouter(prefix="/api/dashboard/companies", tags=["companies"])

@router.get("", response_model=CompaniesResponse)
def get_companies(db: Session = Depends(get_db)):
    service = DashboardService(db)
    items, total = service.companies()
    return CompaniesResponse(
        items=items,
        total=total,
        page=1,
        page_size=25,
        pages=1
    )
