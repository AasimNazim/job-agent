import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from job_agent.models.base import Base
from job_agent.models.company import Company
from job_agent.models.job import Job

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

def test_company_creation(db_session):
    company = Company(name="Test Company", career_url="https://test.com/careers", platform="lever")
    db_session.add(company)
    db_session.commit()
    
    saved_company = db_session.query(Company).filter_by(name="Test Company").first()
    assert saved_company is not None
    assert saved_company.platform == "lever"

def test_job_creation(db_session):
    job = Job(
        company_name="Test Company",
        source="lever",
        title="Software Engineer Intern",
        url="https://test.com/jobs/123",
        content_hash="hash123"
    )
    db_session.add(job)
    db_session.commit()
    
    saved_job = db_session.query(Job).filter_by(title="Software Engineer Intern").first()
    assert saved_job is not None
    assert saved_job.status == "NEW"
