from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime, timezone
from .base import Base

class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False)  # Foreign key conceptually
    name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    email = Column(String, nullable=False)
    company = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
