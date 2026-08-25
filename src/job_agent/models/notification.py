from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from uuid import uuid4
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
    run_uuid = Column(String, default=lambda: str(uuid4()), nullable=False, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    # Retained for compatibility with the original JobRun schema.
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="RUNNING")
    trigger_type = Column(String, default="SCHEDULED")
    agent_version = Column(String, nullable=True)
    
    companies_scanned = Column(Integer, default=0)
    jobs_discovered = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    duplicate_jobs = Column(Integer, default=0)
    jobs_prefiltered = Column(Integer, default=0)
    jobs_evaluated = Column(Integer, default=0)
    jobs_matched = Column(Integer, default=0)
    jobs_ignored = Column(Integer, default=0)
    applications_generated = Column(Integer, default=0)
    gmail_drafts_created = Column(Integer, default=0)
    drafts_created = Column(Integer, default=0)
    recruiter_emails_verified = Column(Integer, default=0)
    recruiter_emails_not_found = Column(Integer, default=0)
    llm_calls = Column(Integer, default=0)
    llm_successes = Column(Integer, default=0)
    llm_failures = Column(Integer, default=0)
    rate_limit_retries = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    failure_summary = Column(String, nullable=True)
    
    summary_data = Column(JSON, nullable=True)
