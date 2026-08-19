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


def test_entry_level_prefilter_keywords(db_session):
    candidate = CandidateProfile(profile_data={"skills_summary": "Python"}, career_level="entry_level")
    db_session.add(candidate)
    db_session.add(Resume(filename="test3.pdf", domains=["backend"]))
    db_session.commit()

    evaluator = JobEvaluator(db_session, MagicMock())

    entry_job = Job(
        company_name="TestComp",
        source="test",
        title="Campus Associate Software Engineer",
        description="Early careers program for fresh graduate candidates.",
        url="http://test.com/job3",
        status="NEW",
        content_hash="ghi"
    )
    non_entry_job = Job(
        company_name="TestComp",
        source="test",
        title="Senior Staff Engineer",
        description="Requires 8+ years and team leadership experience.",
        url="http://test.com/job4",
        status="NEW",
        content_hash="jkl"
    )

    assert evaluator.passes_entry_level_prefilter(entry_job) is True
    assert evaluator.passes_entry_level_prefilter(non_entry_job) is False


def test_irrelevant_job_does_not_call_gemini(db_session):
    candidate = CandidateProfile(profile_data={"skills_summary": "Python"}, career_level="entry_level")
    db_session.add(candidate)
    db_session.add(Resume(filename="test4.pdf", domains=["backend"]))
    db_session.commit()

    job = Job(
        company_name="TestComp",
        source="test",
        title="Principal Engineering Manager",
        description="10+ years required and managing multiple teams.",
        url="http://test.com/job5",
        status="NEW",
        content_hash="mno"
    )
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    evaluator = JobEvaluator(db_session, mock_llm)

    matched = evaluator.evaluate_job(job)

    assert matched is False
    assert job.status == "IGNORED"
    mock_llm.generate_structured_response.assert_not_called()


def test_already_evaluated_job_does_not_call_gemini(db_session):
    candidate = CandidateProfile(profile_data={"skills_summary": "Python"}, career_level="entry_level")
    db_session.add(candidate)
    db_session.add(Resume(filename="test5.pdf", domains=["backend"]))
    db_session.commit()

    job = Job(
        company_name="TestComp",
        source="test",
        title="Junior Backend Engineer",
        description="Entry level backend role.",
        url="http://test.com/job6",
        status="MATCHED",
        selected_resume="backend",
        content_hash="pqr"
    )
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    evaluator = JobEvaluator(db_session, mock_llm)

    matched = evaluator.evaluate_job(job)

    assert matched is True
    mock_llm.generate_structured_response.assert_not_called()


def test_matched_empty_resume_is_resolved_deterministically(db_session):
    db_session.add(CandidateProfile(profile_data={"skills_summary": "Finance"}, career_level="entry_level"))
    db_session.add(Resume(filename="finance.pdf", domains=["bank_it"], extracted_text="Finance accounting and audit experience."))
    job = Job(company_name="TestComp", source="test", title="Management Trainee Finance", description="Entry-level finance and accounting role.", url="http://test.com/job7", status="NEW", content_hash="stu")
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    mock_llm.generate_structured_response.return_value = EvaluationResult(is_entry_level=True, confidence=.95, reason="entry-level", selected_resume_domain="")

    assert JobEvaluator(db_session, mock_llm).evaluate_job(job) is True
    assert job.status == "MATCHED"
    assert job.selected_resume == "bank_it"
    mock_llm.generate_structured_response.assert_called_once()


def test_matched_result_without_suitable_resume_is_not_persisted(db_session):
    db_session.add(CandidateProfile(profile_data={"skills_summary": "History"}, career_level="entry_level"))
    db_session.add(Resume(filename="software.pdf", domains=["software_engineering"], extracted_text="Python web development."))
    job = Job(company_name="TestComp", source="test", title="Management Trainee Finance", description="Entry-level finance and accounting role.", url="http://test.com/job8", status="NEW", content_hash="vwx")
    db_session.add(job)
    db_session.commit()

    mock_llm = MagicMock()
    mock_llm.generate_structured_response.return_value = EvaluationResult(is_entry_level=True, confidence=.95, reason="entry-level", selected_resume_domain="")

    assert JobEvaluator(db_session, mock_llm).evaluate_job(job) is False
    assert job.status == "IGNORED"
    assert job.selected_resume is None
