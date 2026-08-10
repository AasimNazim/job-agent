from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from .base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    career_url = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # greenhouse, lever, workable, etc.
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
