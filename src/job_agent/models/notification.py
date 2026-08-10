from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from .base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, index=True, nullable=True)
    platform = Column(String, default="telegram")
    status = Column(String, default="SENT")
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="RUNNING")
    
    companies_scanned = Column(Integer, default=0)
    jobs_discovered = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    drafts_created = Column(Integer, default=0)
    
    summary_data = Column(JSON, nullable=True)
