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
