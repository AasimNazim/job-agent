from datetime import datetime

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    jobs_discovered: int | None
    companies_scanned: int | None
    jobs_matched: int | None
    jobs_rejected: int | None
    applications_generated: int | None
    duplicate_jobs_removed: int | None
    llm_calls: int | None
    llm_successes: int | None
    llm_failures: int | None
    rate_limit_retries: int | None
    recruiter_emails_verified: int | None
    recruiter_emails_not_found: int | None
    last_run_status: str | None
    last_run_started_at: datetime | None
    last_successful_run: datetime | None
    last_run_duration_seconds: float | None
