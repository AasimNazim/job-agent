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
    assert application.draft_subject == "Application for Junior Backend Engineer - TestComp"
    assert "Dear Hiring Manager" in application.draft_body
    
    # Check job status updated
    assert job.status == "DRAFT_CREATED"
    
    # Verify DB persistence
    db_app = db_session.query(Application).filter_by(job_id=job.id).first()
    assert db_app is not None
    assert db_app.draft_subject == "Application for Junior Backend Engineer - TestComp"


def test_generate_draft_resolves_empty_resume_without_extra_llm_call(db_session):
    db_session.add(CandidateProfile(profile_data={"full_name": "Test Candidate"}, career_level="entry_level"))
    db_session.add(Resume(filename="finance.pdf", domains=["bank_it"], extracted_text="Finance accounting and audit experience."))
    job = Job(company_name="TestComp", source="test", title="Management Trainee Finance", description="Entry-level finance role.", url="http://test.com/job9", status="MATCHED", selected_resume="", content_hash="yz1")
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    mock_llm.generate_structured_response.return_value = EmailDraftResult(subject="ignored", body="Dear Hiring Team,\n\nI am applying for this role.\n\nThank you.")
    application = ApplicationGenerator(db_session, mock_llm).generate_draft(job)

    assert application is not None
    assert job.selected_resume == "bank_it"
    assert application.resume_id is not None
    mock_llm.generate_structured_response.assert_called_once()


def test_generate_draft_does_not_call_llm_without_suitable_resume(db_session):
    db_session.add(CandidateProfile(profile_data={"full_name": "Test Candidate"}, career_level="entry_level"))
    db_session.add(Resume(filename="software.pdf", domains=["software_engineering"], extracted_text="Python web development."))
    job = Job(company_name="TestComp", source="test", title="Management Trainee Finance", description="Entry-level finance role.", url="http://test.com/job10", status="MATCHED", selected_resume="", content_hash="yz2")
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    assert ApplicationGenerator(db_session, mock_llm).generate_draft(job) is None
    mock_llm.generate_structured_response.assert_not_called()


def test_cover_letter_is_concise_and_does_not_copy_resume_or_default_cgpa(db_session):
    db_session.add(CandidateProfile(profile_data={"full_name": "Test Candidate"}, career_level="entry_level"))
    resume_text = "Built a production platform that processed 500,000 reviews with Python and Django. CGPA 3.8."
    db_session.add(Resume(filename="software.pdf", domains=["software_engineering"], extracted_text=resume_text))
    job = Job(company_name="TestComp", source="test", title="Junior Python Engineer", description="Build Python services and APIs with the engineering team.", url="http://test.com/job11", status="MATCHED", selected_resume="software_engineering", content_hash="yz3")
    db_session.add(job)
    db_session.commit()

    long_body = " ".join(["I am writing to apply for this role and would welcome the opportunity to contribute to the engineering team."] * 30)
    mock_llm = MagicMock()
    mock_llm.generate_structured_response.return_value = EmailDraftResult(subject="ignored", body=long_body + " CGPA 3.8. Built a production platform that processed 500,000 reviews with Python and Django.")
    application = ApplicationGenerator(db_session, mock_llm).generate_draft(job)

    words = application.draft_body.split()
    assert len(words) <= 180
    assert "CGPA" not in application.draft_body
    assert "Built a production platform that processed 500,000 reviews" not in application.draft_body
