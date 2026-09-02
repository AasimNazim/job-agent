from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.common import PaginatedResponse

class CompanyDashboard(BaseModel):
    id: int
    name: str
    ats: str
    jobs_found: int
    matching_jobs: int
    last_scan: Optional[datetime]
    scan_status: str
    monitoring_status: str

class CompaniesResponse(PaginatedResponse[CompanyDashboard]):
    pass
