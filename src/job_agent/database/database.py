from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings
from ..models.base import Base

# Import all models to ensure they are registered with Base
from ..models.company import Company
from ..models.job import Job
from ..models.candidate import Resume, CandidateProfile
from ..models.recruiter import Recruiter
from ..models.application import Application
from ..models.notification import Notification, JobRun

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
