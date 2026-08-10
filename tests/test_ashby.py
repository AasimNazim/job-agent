import pytest
import httpx
from datetime import datetime, timezone
from job_agent.models.company import Company
from job_agent.adapters.ashby import AshbyAdapter

@pytest.fixture
def ashby_adapter():
    return AshbyAdapter()

@pytest.fixture
def sample_company():
    return Company(
        name="TestAshby",
        career_url="https://jobs.ashbyhq.com/testashby",
        platform="ashby",
        enabled=True
    )

def test_extract_board_token(ashby_adapter):
    token1 = ashby_adapter._extract_board_token("https://jobs.ashbyhq.com/testashby")
    assert token1 == "testashby"
    
    token2 = ashby_adapter._extract_board_token("https://api.ashbyhq.com/posting-api/job-board/testashby")
    assert token2 == "testashby"

@pytest.mark.asyncio
async def test_discover_jobs(httpx_mock, ashby_adapter, sample_company):
    mock_response = {
        "jobs": [
            {
                "id": "ashby-123",
                "title": "Backend Intern",
                "location": "Remote",
                "employmentType": "Intern",
                "jobUrl": "https://jobs.ashbyhq.com/testashby/ashby-123",
                "descriptionHtml": "<p>Description</p>",
                "publishedAt": "2024-03-27T10:45:00Z"
            }
        ]
    }
    
    httpx_mock.add_response(
        url="https://api.ashbyhq.com/posting-api/job-board/testashby?includeCompensation=true",
        json=mock_response
    )
    
    jobs = await ashby_adapter.discover_jobs(sample_company)
    
    assert len(jobs) == 1
    job = jobs[0]
    
    assert job.company_name == "TestAshby"
    assert job.title == "Backend Intern"
    assert job.location == "Remote"
    assert job.source_job_id == "ashby-123"
    assert job.employment_type == "Intern"
    assert job.url == "https://jobs.ashbyhq.com/testashby/ashby-123"
    assert job.description == "<p>Description</p>"
    assert job.posted_at == datetime.fromisoformat("2024-03-27T10:45:00+00:00")
    assert job.content_hash is not None
