def test_applications_are_paginated_and_sanitized(client):
    response = client.get("/api/dashboard/applications?page=1&page_size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    application = body["items"][0]
    assert application["company_name"] == "Careem"
    assert application["resume"] is None
    assert application["recruiter_email"] == "recruiter@example.com"
    assert application["gmail_draft_created"] is True
    assert "gmail_draft_id" not in application
    assert "draft_body" not in application


def test_system_status(client):
    response = client.get("/api/dashboard/system")
    assert response.status_code == 200
    body = response.json()
    assert body["database_status"] == "connected"
    assert body["companies_configured"] == 1
    assert body["database_jobs"] == 1
    assert body["database_applications"] == 1
