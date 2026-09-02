from datetime import datetime

from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    api_status: str
    database_status: str
    agent_last_run: datetime | None
    agent_last_success: datetime | None
    agent_version: str | None
    companies_configured: int | None
    database_jobs: int | None
    database_applications: int | None
