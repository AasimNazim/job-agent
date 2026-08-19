from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean
from datetime import datetime, timezone
from .base import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False)
    resume_id = Column(Integer, index=True, nullable=True)
    
    draft_subject = Column(String, nullable=True)
    draft_body = Column(String, nullable=True)
    recruiter_email = Column(String, nullable=True)
    recruiter_email_status = Column(String, nullable=False, default="NOT_FOUND")
    recruiter_email_source = Column(String, nullable=True)
    gmail_draft_id = Column(String, nullable=True)
    status = Column(String, default="DRAFT_CREATED")
    notification_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
