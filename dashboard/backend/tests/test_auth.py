import os

def test_health_without_token(unauth_client):
    response = unauth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_endpoints_with_demo_mode(unauth_client):
    os.environ["DEMO_MODE"] = "true"
    try:
        # Public allowed endpoints
        for endpoint in ["/api/dashboard/overview", "/api/dashboard/jobs", "/api/dashboard/companies", "/api/dashboard/analytics"]:
            res = unauth_client.get(endpoint)
            assert res.status_code == 200, f"Failed on {endpoint}"
            
        # Restricted endpoints return 401
        for endpoint in ["/api/dashboard/system", "/api/dashboard/runs", "/api/dashboard/applications"]:
            res = unauth_client.get(endpoint)
            assert res.status_code == 401, f"Should be restricted on {endpoint}"
    finally:
        os.environ["DEMO_MODE"] = "false"


def test_dashboard_with_invalid_token(unauth_client):
    os.environ["DEMO_MODE"] = "false"
    response = unauth_client.get(
        "/api/dashboard/system",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_dashboard_with_valid_token(client):
    response = client.get("/api/dashboard/system")
    assert response.status_code == 200
    assert "token" not in response.text.lower()

