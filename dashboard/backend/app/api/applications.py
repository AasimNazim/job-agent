import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.utils import pages
from app.db import get_db
from app.schemas.applications import ApplicationResponse, PaginatedApplicationsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/dashboard/applications", response_model=PaginatedApplicationsResponse)
def get_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        items, total = DashboardService(db).applications(page, page_size)
        response = [ApplicationResponse(
            id=application.id,
            job_id=application.job_id,
            company_name=job.company_name if job else None,
            job_title=job.title if job else None,
            status=application.status,
            resume=resume.filename if resume else None,
            recruiter_email_status=application.recruiter_email_status,
            recruiter_email=application.recruiter_email,
            recruiter_email_source=application.recruiter_email_source,
            gmail_draft_created=bool(application.gmail_draft_id),
            created_at=application.created_at,
        ) for application, job, resume in items]
        return {"items": response, "page": page, "page_size": page_size, "total": total, "pages": pages(total, page_size)}
    except Exception:
        logger.exception("Dashboard applications query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")
