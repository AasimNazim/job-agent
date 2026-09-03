from sqlalchemy import create_engine, inspect, text
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

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        existing_columns = {column["name"] for column in inspect(engine).get_columns("applications")}
        additions = {
            "recruiter_email": "VARCHAR",
            "recruiter_email_status": "VARCHAR NOT NULL DEFAULT 'NOT_FOUND'",
            "recruiter_email_source": "VARCHAR",
        }
        with engine.begin() as connection:
            for column_name, column_type in additions.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE applications ADD COLUMN {column_name} {column_type}"))

        existing_run_columns = {column["name"] for column in inspect(engine).get_columns("job_runs")}
        run_additions = {
            "run_uuid": "VARCHAR",
            "completed_at": "DATETIME",
            "trigger_type": "VARCHAR DEFAULT 'SCHEDULED'",
            "agent_version": "VARCHAR",
            "duplicate_jobs": "INTEGER DEFAULT 0",
            "jobs_prefiltered": "INTEGER DEFAULT 0",
            "jobs_evaluated": "INTEGER DEFAULT 0",
            "jobs_matched": "INTEGER DEFAULT 0",
            "jobs_ignored": "INTEGER DEFAULT 0",
            "applications_generated": "INTEGER DEFAULT 0",
            "gmail_drafts_created": "INTEGER DEFAULT 0",
            "recruiter_emails_verified": "INTEGER DEFAULT 0",
            "recruiter_emails_not_found": "INTEGER DEFAULT 0",
            "llm_calls": "INTEGER DEFAULT 0",
            "llm_successes": "INTEGER DEFAULT 0",
            "llm_failures": "INTEGER DEFAULT 0",
            "rate_limit_retries": "INTEGER DEFAULT 0",
            "error_count": "INTEGER DEFAULT 0",
            "failure_summary": "VARCHAR",
        }
        with engine.begin() as connection:
            for column_name, column_type in run_additions.items():
                if column_name not in existing_run_columns:
                    connection.execute(text(f"ALTER TABLE job_runs ADD COLUMN {column_name} {column_type}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
