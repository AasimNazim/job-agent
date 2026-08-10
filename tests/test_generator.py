import pytest
from unittest.mock import MagicMock
from job_agent.core.generator import ApplicationGenerator, EmailDraftResult
from job_agent.models.candidate import CandidateProfile, Resume
from job_agent.models.job import Job
from job_agent.models.application import Application

def test_generate_draft(db_session):
    # Setup candidate and resume
    candidate = CandidateProfile(
        profile_data={
            "full_name": "Test Candidate",
            "email": "test@test.com",
            "skills_summary": "Python"
        },
        career_level="entry_level"
    )
    db_session.add(candidate)
    db_session.commit()
    
    resume = Resume(
        filename="test.pdf", 
        domains=["backend"], 
        extracted_text="I know Python and Django."
    )
    db_session.add(resume)
    db_session.commit()
    
    # Setup MATCHED job
    job = Job(
        company_name="TestComp",
        source="test",
        title="Junior Backend Engineer",
        description="Looking for Python.",
        url="http://test.com/job",
        status="MATCHED",
        selected_resume="backend",
        content_hash="abc"
    )
    db_session.add(job)
    db_session.commit()
    
    # Mock LLM
    mock_llm = MagicMock()
    mock_result = EmailDraftResult(
        subject="Application for Junior Backend Engineer - Test Candidate",
        body="Dear Hiring Manager,\n\nI am applying for the backend role."
    )
    mock_llm.generate_structured_response.return_value = mock_result
    
    generator = ApplicationGenerator(db_session, mock_llm)
    application = generator.generate_draft(job)
    
    assert application is not None
    assert application.status == "DRAFT_CREATED"
    assert application.draft_subject == "Application for Junior Backend Engineer - Test Candidate"
    assert "Dear Hiring Manager" in application.draft_body
    
    # Check job status updated
    assert job.status == "DRAFT_CREATED"
    
    # Verify DB persistence
    db_app = db_session.query(Application).filter_by(job_id=job.id).first()
    assert db_app is not None
    assert db_app.draft_subject == "Application for Junior Backend Engineer - Test Candidate"
