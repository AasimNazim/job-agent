import pytest
import httpx
from datetime import datetime
from job_agent.models.company import Company
from job_agent.adapters.greenhouse import GreenhouseAdapter

@pytest.fixture
def greenhouse_adapter():
    return GreenhouseAdapter()

@pytest.fixture
def sample_company():
    return Company(
        name="VentureDive",
        career_url="https://boards.greenhouse.io/venturedive",
        platform="greenhouse",
        enabled=True
    )

def test_extract_board_token(greenhouse_adapter):
    token = greenhouse_adapter._extract_board_token("https://boards.greenhouse.io/venturedive")
    assert token == "venturedive"
    
    token2 = greenhouse_adapter._extract_board_token("https://boards.greenhouse.io/company-name/jobs")
    assert token2 == "company-name"

@pytest.mark.asyncio
async def test_discover_jobs(httpx_mock, greenhouse_adapter, sample_company):
    mock_response = {
        "jobs": [
            {
                "id": 123456,
                "title": "Software Engineering Intern",
                "absolute_url": "https://boards.greenhouse.io/venturedive/jobs/123456",
                "location": {"name": "Karachi, Pakistan"},
                "content": "<p>Job description here</p>",
                "updated_at": "2024-03-27T10:45:00-04:00"
            }
        ]
    }
    
    httpx_mock.add_response(
        url="https://boards-api.greenhouse.io/v1/boards/venturedive/jobs?content=true",
        json=mock_response
    )
    
    jobs = await greenhouse_adapter.discover_jobs(sample_company)
    
    assert len(jobs) == 1
    job = jobs[0]
    
    assert job.company_name == "VentureDive"
    assert job.title == "Software Engineering Intern"
    assert job.location == "Karachi, Pakistan"
    assert job.source_job_id == "123456"
    assert job.url == "https://boards.greenhouse.io/venturedive/jobs/123456"
    assert job.description == "<p>Job description here</p>"
    assert job.content_hash is not None
