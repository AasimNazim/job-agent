import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import allow_public_or_admin_auth
from app.api.utils import pages
from app.db import get_db
from app.schemas.jobs import JobResponse, PaginatedJobsResponse
from app.services.dashboard_service import DashboardService
from app.services.privacy import sanitize_resume_name

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/dashboard/jobs", response_model=PaginatedJobsResponse)
def get_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = None,
    company: str | None = None,
    min_score: float | None = Query(None, ge=0, le=1),
    auth_info: dict = Depends(allow_public_or_admin_auth),
    db: Session = Depends(get_db),
):
    try:
        is_admin = auth_info.get("is_admin", False)
        items, total = DashboardService(db).jobs(page, page_size, status, company, min_score)
        response = [JobResponse(
            id=job.id,
            company_name=job.company_name,
            title=job.title,
            status=job.status,
            match_confidence=job.match_confidence,
            selected_resume=job.selected_resume if is_admin else sanitize_resume_name(job.selected_resume),
            url=job.url,
            source=job.source,
            created_at=job.first_seen_at,
            updated_at=None,
        ) for job in items]
        return {"items": response, "page": page, "page_size": page_size, "total": total, "pages": pages(total, page_size)}
    except Exception:
        logger.exception("Dashboard jobs query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")
