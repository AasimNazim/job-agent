import pytest
from unittest.mock import MagicMock
from job_agent.models.job import Job
from job_agent.models.application import Application
from job_agent.models.candidate import CandidateProfile, Resume
from job_agent.core.deduplicator import JobDeduplicator
from job_agent.core.generator import ApplicationGenerator, EmailDraftResult
from job_agent.utils.url import generate_canonical_content_hash


def test_stable_canonical_hash_ignores_location_change():
    hash1 = generate_canonical_content_hash(
        company_name="Game District",
        title="IT Support Associate",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        source_job_id="yMBEyD0VLp"
    )
    hash2 = generate_canonical_content_hash(
        company_name="Game District",
        title="IT Support Associate",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        source_job_id="yMBEyD0VLp"
    )
    assert hash1 == hash2


def test_deduplicator_same_url_changed_location(db_session):
    deduplicator = JobDeduplicator(db_session)
    job1 = Job(
        company_name="Game District",
        source="jazzhr",
        title="IT Support Associate",
        location="Pakistan",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        content_hash="hash_v1",
        status="NEW"
    )
    stats1 = deduplicator.save_and_deduplicate([job1])
    assert stats1["new_jobs"] == 1

    # Second run: same URL & title, different content_hash & updated location
    job2 = Job(
        company_name="Game District",
        source="jazzhr",
        title="IT Support Associate",
        location="Lahore, Pakistan",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        content_hash="hash_v2",
        status="NEW"
    )
    stats2 = deduplicator.save_and_deduplicate([job2])
    assert stats2["new_jobs"] == 0
    assert stats2["seen_jobs"] == 1
    assert db_session.query(Job).count() == 1
    updated_job = db_session.query(Job).first()
    assert updated_job.location == "Lahore, Pakistan"


def test_deduplicator_same_source_job_id(db_session):
    deduplicator = JobDeduplicator(db_session)
    job1 = Job(
        company_name="Acme",
        source="lever",
        source_job_id="job123",
        title="Engineer",
        url="https://jobs.lever.co/acme/job123",
        content_hash="hashA",
        status="NEW"
    )
    deduplicator.save_and_deduplicate([job1])

    job2 = Job(
        company_name="Acme",
        source="lever",
        source_job_id="job123",
        title="Senior Engineer",
        url="https://jobs.lever.co/acme/job123-modified",
        content_hash="hashB",
        status="NEW"
    )
    stats = deduplicator.save_and_deduplicate([job2])
    assert stats["new_jobs"] == 0
    assert stats["seen_jobs"] == 1
    assert db_session.query(Job).count() == 1


def test_generator_skips_existing_application_for_same_url(db_session):
    candidate = CandidateProfile(
        profile_data={"full_name": "Test Candidate", "email": "test@test.com"},
        career_level="entry_level"
    )
    resume = Resume(
        filename="resume.pdf",
        domains=["backend"],
        extracted_text="Test resume text"
    )
    db_session.add(candidate)
    db_session.add(resume)
    db_session.commit()

    job1 = Job(
        company_name="Game District",
        source="jazzhr",
        title="IT Support Associate",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        content_hash="hash1",
        status="MATCHED",
        selected_resume="backend"
    )
    db_session.add(job1)
    db_session.commit()

    app1 = Application(
        job_id=job1.id,
        resume_id=resume.id,
        status="DRAFT_CREATED",
        gmail_draft_id="draft123"
    )
    db_session.add(app1)
    db_session.commit()

    job2 = Job(
        company_name="Game District",
        source="jazzhr",
        title="IT Support Associate",
        url="https://gamedistrict.applytojob.com/apply/yMBEyD0VLp/IT-Support-Associate",
        content_hash="hash2",
        status="MATCHED",
        selected_resume="backend"
    )
    db_session.add(job2)
    db_session.commit()

    mock_llm = MagicMock()
    generator = ApplicationGenerator(db_session, mock_llm)

    result_app = generator.generate_draft(job2)

    assert result_app.id == app1.id
    assert db_session.query(Application).count() == 1
    assert job2.status == "DRAFT_CREATED"
    mock_llm.generate_structured_response.assert_not_called()


def test_generator_idempotency(db_session):
    candidate = CandidateProfile(
        profile_data={"full_name": "Test Candidate"},
        career_level="entry_level"
    )
    resume = Resume(
        filename="software.pdf",
        domains=["software_engineering"],
        extracted_text="Python web development."
    )
    job = Job(
        company_name="Acme",
        source="test",
        title="Junior Python Engineer",
        url="http://example.com/job1",
        status="MATCHED",
        selected_resume="software_engineering",
        content_hash="h1"
    )
    db_session.add_all([candidate, resume, job])
    db_session.commit()

    mock_llm = MagicMock()
    mock_llm.generate_structured_response.return_value = EmailDraftResult(
        subject="Application for Junior Python Engineer - Acme",
        body="Dear Hiring Team,\n\nI am applying for this role.\n\nThank you."
    )
    generator = ApplicationGenerator(db_session, mock_llm)

    # First call
    app1 = generator.generate_draft(job)
    assert app1 is not None
    assert db_session.query(Application).count() == 1

    # Second call for same job
    job.status = "MATCHED"
    app2 = generator.generate_draft(job)
    assert app2.id == app1.id
    assert db_session.query(Application).count() == 1
