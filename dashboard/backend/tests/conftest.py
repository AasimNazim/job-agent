import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from app.db import get_db
from app.main import app
from job_agent.models.application import Application
from job_agent.models.base import Base
from job_agent.models.company import Company
from job_agent.models.job import Job
from job_agent.models.notification import JobRun


@pytest.fixture(autouse=True)
def setup_env():
    os.environ["DASHBOARD_API_TOKEN"] = "test-token"
    yield
    os.environ.pop("DASHBOARD_API_TOKEN", None)


@pytest.fixture
def unauth_client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'dashboard-test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    db.add_all([
        Company(name="Careem", career_url="https://careers.example", platform="custom", enabled=True),
        Job(company_name="Careem", source="test", title="Junior Engineer", url="https://jobs.example/1", content_hash="hash-1", status="MATCHED", match_confidence=0.9),
        Application(job_id=1, status="DRAFT_SAVED", recruiter_email_status="VERIFIED", recruiter_email="recruiter@example.com", gmail_draft_id="draft-1"),
        JobRun(run_uuid="run-1", status="SUCCEEDED", trigger_type="SCHEDULED", jobs_discovered=10, companies_scanned=1, jobs_matched=1, applications_generated=1, drafts_created=1, llm_calls=2, llm_successes=2, duplicate_jobs=3),
    ])
    db.commit()
    db.close()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(unauth_client):
    unauth_client.headers.update({"Authorization": "Bearer test-token"})
    yield unauth_client
