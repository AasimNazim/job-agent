from job_agent.models.notification import JobRun
from app.db import get_db

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_overview_uses_run_and_current_state_metrics(client):
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["jobs_discovered"] == 10
    assert body["companies_scanned"] == 1
    assert body["jobs_matched"] == 1
    assert body["applications_generated"] == 1
    assert body["duplicate_jobs_removed"] == 3
    assert body["llm_calls"] == 2
    assert body["last_run_status"] == "SUCCEEDED"


def test_overview_aggregates_multiple_runs(client):
    # Retrieve DB session from app dependency override
    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)

    # Add a second run with LLM calls and matched jobs
    run2 = JobRun(
        run_uuid="run-2",
        status="SUCCEEDED",
        trigger_type="MANUAL",
        jobs_discovered=5,
        companies_scanned=1,
        jobs_matched=3,
        applications_generated=2,
        drafts_created=2,
        llm_calls=4,
        llm_successes=3,
        llm_failures=1,
        duplicate_jobs=1
    )
    db.add(run2)
    db.commit()

    response = client.get("/api/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    # Aggregated metrics across run-1 and run-2
    assert body["jobs_matched"] == 4  # 1 + 3
    assert body["llm_calls"] == 6      # 2 + 4
    assert body["llm_successes"] == 5  # 2 + 3
    assert body["llm_failures"] == 1   # 0 + 1
