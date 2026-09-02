def test_jobs_pagination_and_status_filter(client):
    response = client.get("/api/dashboard/jobs?page=1&page_size=1&status=MATCHED")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["company_name"] == "Careem"
    assert body["items"][0]["match_confidence"] == 0.9
    assert "description" not in body["items"][0]


def test_jobs_min_score_filter(client):
    assert client.get("/api/dashboard/jobs?min_score=0.95").json()["total"] == 0
