from datetime import datetime

from pydantic import BaseModel

from .common import PaginatedResponse


class RunResponse(BaseModel):
    run_uuid: str | None
    trigger_type: str | None
    status: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    agent_version: str | None
    jobs_discovered: int | None
    jobs_after_prefilter: int | None
    jobs_evaluated: int | None
    jobs_matched: int | None
    applications_generated: int | None
    drafts_created: int | None
    recruiter_emails_verified: int | None
    recruiter_emails_not_found: int | None
    llm_calls: int | None
    llm_successes: int | None
    llm_failures: int | None
    rate_limit_retries: int | None
    failure_summary: str | None


class PaginatedRunsResponse(PaginatedResponse[RunResponse]):
    pass
