def test_run_history_is_newest_first_and_paginated(client):
    response = client.get("/api/dashboard/runs?page=1&page_size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["items"][0]["run_uuid"] == "run-1"
    assert body["items"][0]["jobs_after_prefilter"] == 0


def test_single_run_and_missing_run(client):
    response = client.get("/api/dashboard/runs/run-1")
    assert response.status_code == 200
    assert response.json()["llm_calls"] == 2

    response = client.get("/api/dashboard/runs/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}
