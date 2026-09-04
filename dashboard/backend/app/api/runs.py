import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.utils import pages
from app.db import get_db
from app.schemas.runs import PaginatedRunsResponse, RunResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()
logger = logging.getLogger(__name__)


def serialize_run(run) -> RunResponse:
    return RunResponse(
        run_uuid=run.run_uuid,
        trigger_type=run.trigger_type,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_seconds=DashboardService._duration_seconds(run),
        agent_version=run.agent_version,
        jobs_discovered=run.jobs_discovered,
        jobs_after_prefilter=run.jobs_prefiltered,
        jobs_evaluated=run.jobs_evaluated,
        jobs_matched=run.jobs_matched,
        applications_generated=run.applications_generated,
        drafts_created=run.drafts_created,
        gmail_drafts_created=getattr(run, "gmail_drafts_created", None),
        recruiter_emails_verified=run.recruiter_emails_verified,
        recruiter_emails_not_found=run.recruiter_emails_not_found,
        llm_calls=run.llm_calls,
        llm_successes=run.llm_successes,
        llm_failures=run.llm_failures,
        rate_limit_retries=run.rate_limit_retries,
        failure_summary=run.failure_summary,
    )


@router.get("/api/dashboard/runs", response_model=PaginatedRunsResponse)
def get_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        items, total = DashboardService(db).runs(page, page_size)
        return {"items": [serialize_run(item) for item in items], "page": page, "page_size": page_size, "total": total, "pages": pages(total, page_size)}
    except Exception:
        logger.exception("Dashboard run history query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")


@router.get("/api/dashboard/runs/{run_uuid}", response_model=RunResponse)
def get_run(run_uuid: str, db: Session = Depends(get_db)):
    try:
        run = DashboardService(db).run_by_uuid(run_uuid)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return serialize_run(run)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Dashboard run query failed")
        raise HTTPException(status_code=500, detail="Internal dashboard error")
