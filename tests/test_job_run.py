from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from job_agent import __main__ as agent_main
from job_agent.database import database as database_module
from job_agent.models.base import Base
from job_agent.models.notification import JobRun


def _metrics():
    return {
        "companies_scanned": 3,
        "jobs_discovered": 12,
        "jobs_after_prefilter": 8,
        "jobs_evaluated": 8,
        "jobs_ignored": 5,
        "new_jobs": 7,
        "duplicate_jobs": 5,
        "matched_jobs": 3,
        "drafts_generated": 2,
        "gmail_drafts_pushed": 2,
        "recruiter_emails_verified": 1,
        "recruiter_emails_not_found": 1,
        "llm_calls": 8,
        "gemini_successes": 7,
        "gemini_failures": 1,
        "retries_429": 2,
        "error_count": 1,
    }


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_successful_run_lifecycle_persists_metrics():
    db = _session()
    try:
        run = agent_main._create_run(db)
        metrics = _metrics()
        agent_main._finalize_run(db, run, metrics, "SUCCEEDED")

        saved = db.query(JobRun).one()
        assert saved.status == "SUCCEEDED"
        assert saved.started_at is not None
        assert saved.completed_at is not None
        assert saved.finished_at is not None
        assert saved.jobs_discovered == 12
        assert saved.new_jobs == 7
        assert saved.duplicate_jobs == 5
        assert saved.jobs_prefiltered == 8
        assert saved.jobs_evaluated == 8
        assert saved.jobs_matched == 3
        assert saved.jobs_ignored == 5
        assert saved.applications_generated == 2
        assert saved.gmail_drafts_created == 2
        assert saved.llm_calls == 8
        assert saved.llm_successes == 7
        assert saved.llm_failures == 1
        assert saved.rate_limit_retries == 2
    finally:
        db.close()


def test_failed_run_is_finalized_with_safe_summary():
    db = _session()
    try:
        run = agent_main._create_run(db)
        metrics = _metrics()
        metrics["error_count"] = 1
        agent_main._finalize_run(db, run, metrics, "FAILED", "fatal error: RuntimeError")

        saved = db.query(JobRun).one()
        assert saved.status == "FAILED"
        assert saved.completed_at is not None
        assert saved.error_count == 1
        assert saved.failure_summary == "fatal error: RuntimeError"
        assert "traceback" not in saved.failure_summary.lower()
    finally:
        db.close()


def test_partial_run_is_finalized():
    db = _session()
    try:
        run = agent_main._create_run(db)
        agent_main._finalize_run(db, run, _metrics(), "PARTIAL", "Gmail service unavailable")

        saved = db.query(JobRun).one()
        assert saved.status == "PARTIAL"
        assert saved.completed_at is not None
    finally:
        db.close()


def test_multiple_runs_have_unique_run_uuids():
    db = _session()
    try:
        first = agent_main._create_run(db)
        second = agent_main._create_run(db)

        assert first.id != second.id
        assert first.run_uuid != second.run_uuid
        assert db.query(JobRun).count() == 2
    finally:
        db.close()


def test_existing_job_runs_schema_is_upgraded_additively(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE job_runs ("
            "id INTEGER PRIMARY KEY, started_at DATETIME, finished_at DATETIME, "
            "status VARCHAR, companies_scanned INTEGER, jobs_discovered INTEGER, "
            "new_jobs INTEGER, drafts_created INTEGER, summary_data JSON)"
        ))

    monkeypatch.setattr(database_module, "engine", engine)
    database_module.init_db()

    columns = {column["name"] for column in inspect(engine).get_columns("job_runs")}
    assert {"run_uuid", "completed_at", "duplicate_jobs", "llm_calls", "failure_summary"} <= columns

    session = sessionmaker(bind=engine)()
    try:
        session.add(JobRun(status="SUCCEEDED", started_at=datetime.now(timezone.utc)))
        session.commit()
        assert session.query(JobRun).count() == 1
    finally:
        session.close()
