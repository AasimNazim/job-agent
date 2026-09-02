def test_get_analytics_default(client):
    response = client.get("/api/dashboard/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "timeline" in data
    assert "funnel" in data
    assert "top_companies" in data
    assert "resume_performance" in data
    
    # Check timeline length (7d = 8 days typically with current day)
    assert len(data["timeline"]) == 8
    
    # Check funnel
    funnel = data["funnel"]
    assert len(funnel) == 6
    assert funnel[0]["stage"] == "Discovered"
    assert funnel[0]["count"] == 10  # From seeded data
    assert funnel[0]["pct"] == 100
    
    assert funnel[-1]["stage"] == "Gmail Draft"

    # Check Top Companies
    companies = data["top_companies"]
    assert len(companies) == 1
    assert companies[0]["name"] == "Careem"
    assert companies[0]["matching_jobs"] == 1

def test_get_analytics_30d(client):
    response = client.get("/api/dashboard/analytics?range=30d")
    assert response.status_code == 200
    data = response.json()
    assert len(data["timeline"]) == 31

def test_get_analytics_invalid_range(client):
    response = client.get("/api/dashboard/analytics?range=100d")
    assert response.status_code == 422 # Validation error
