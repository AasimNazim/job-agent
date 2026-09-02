from pydantic import BaseModel

class AnalyticsTimelineItem(BaseModel):
    date: str
    discovered: int
    matched: int
    applied: int

class AnalyticsFunnelItem(BaseModel):
    stage: str
    count: int
    pct: int

class AnalyticsCompany(BaseModel):
    name: str
    ats: str
    jobs_found: int
    matching_jobs: int
    applications: int

class AnalyticsResumePerformance(BaseModel):
    name: str
    selected: int

class AnalyticsResponse(BaseModel):
    timeline: list[AnalyticsTimelineItem]
    funnel: list[AnalyticsFunnelItem]
    top_companies: list[AnalyticsCompany]
    resume_performance: list[AnalyticsResumePerformance]
