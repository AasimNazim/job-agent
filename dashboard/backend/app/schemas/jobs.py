from datetime import datetime

from pydantic import BaseModel

from .common import PaginatedResponse


class JobResponse(BaseModel):
    id: int
    company_name: str
    title: str
    status: str | None
    match_confidence: float | None
    selected_resume: str | None
    url: str
    source: str
    created_at: datetime | None
    updated_at: datetime | None


class PaginatedJobsResponse(PaginatedResponse[JobResponse]):
    pass
