from datetime import datetime

from pydantic import BaseModel

from .common import PaginatedResponse


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    company_name: str | None
    job_title: str | None
    status: str | None
    resume: str | None
    recruiter_email_status: str | None
    recruiter_email: str | None
    recruiter_email_source: str | None
    gmail_draft_created: bool
    created_at: datetime | None


class PaginatedApplicationsResponse(PaginatedResponse[ApplicationResponse]):
    pass
