from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime, timezone
from .base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, nullable=False)
    source = Column(String, nullable=False)
    source_job_id = Column(String, index=True, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    country = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    url = Column(String, nullable=False)
    
    posted_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="NEW")  # NEW, SEEN, PROCESSED, MATCHED, DRAFT_CREATED, IGNORED, EXPIRED
    
    raw_data = Column(Text, nullable=True)  # Store JSON representation of original ATS data
    content_hash = Column(String, unique=True, index=True, nullable=False)
    selected_resume = Column(String, nullable=True)
    match_confidence = Column(Float, nullable=True)
