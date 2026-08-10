import pytest
from unittest.mock import MagicMock
from job_agent.core.evaluator import JobEvaluator, EvaluationResult
from job_agent.models.candidate import CandidateProfile, Resume
from job_agent.models.job import Job

def test_evaluator_match(db_session):
    # Setup candidate
    candidate = CandidateProfile(profile_data={"skills_summary": "Python"}, career_level="entry_level")
    db_session.add(candidate)
    db_session.commit()
    
    resume = Resume(filename="test.pdf", domains=["backend"])
    db_session.add(resume)
    
    # Setup job
    job = Job(
        company_name="TestComp",
        source="test",
        title="Junior Backend Engineer",
        description="Looking for a junior engineer.",
        url="http://test.com/job1",
        status="NEW",
        content_hash="abc"
    )
    db_session.add(job)
    db_session.commit()
    
    # Mock LLM Service
    mock_llm = MagicMock()
    mock_result = EvaluationResult(
        is_entry_level=True,
        confidence=0.9,
        reason="It says junior",
        selected_resume_domain="backend"
    )
    mock_llm.generate_structured_response.return_value = mock_result
    
    evaluator = JobEvaluator(db_session, mock_llm)
    
    matched = evaluator.evaluate_job(job)
    
    assert matched is True
    assert job.status == "MATCHED"
    assert job.selected_resume == "backend"
    assert job.match_confidence == 0.9

def test_evaluator_ignore(db_session):
    # Same setup but LLM rejects
    candidate = CandidateProfile(profile_data={"skills_summary": "Python"}, career_level="entry_level")
    db_session.add(candidate)
    db_session.commit()
    
    resume = Resume(filename="test2.pdf", domains=["backend"])
    db_session.add(resume)
    db_session.commit()
    
    job = Job(
        company_name="TestComp",
        source="test",
        title="Senior Principal Engineer",
        description="Looking for 10+ years experience.",
        url="http://test.com/job2",
        status="NEW",
        content_hash="def"
    )
    db_session.add(job)
    db_session.commit()
    
    mock_llm = MagicMock()
    mock_result = EvaluationResult(
        is_entry_level=False,
        confidence=0.95,
        reason="Requires 10 years experience",
        selected_resume_domain=""
    )
    mock_llm.generate_structured_response.return_value = mock_result
    
    evaluator = JobEvaluator(db_session, mock_llm)
    
    matched = evaluator.evaluate_job(job)
    
    assert matched is False
    assert job.status == "IGNORED"
