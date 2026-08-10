import pytest
import httpx
from datetime import datetime, timezone
from job_agent.models.company import Company
from job_agent.adapters.workable import WorkableAdapter

@pytest.fixture
def workable_adapter():
    return WorkableAdapter()

@pytest.fixture
def sample_company():
    return Company(
        name="Folio3",
        career_url="https://apply.workable.com/folio3/",
        platform="workable",
        enabled=True
    )

def test_extract_account_token(workable_adapter):
    token1 = workable_adapter._extract_account_token("https://apply.workable.com/folio3/")
    assert token1 == "folio3"
    
    token2 = workable_adapter._extract_account_token("https://folio3.workable.com")
    assert token2 == "folio3"

@pytest.mark.asyncio
async def test_discover_jobs(httpx_mock, workable_adapter, sample_company):
    mock_response = {
        "jobs": [
            {
                "shortcode": "ABCD123",
                "title": "Software Engineer Trainee",
                "location": {
                    "city": "Karachi",
                    "country": "Pakistan"
                },
                "type": "Full-time",
                "url": "https://apply.workable.com/folio3/j/ABCD123/",
                "description": "Some HTML description",
                "published_on": "2023-10-15"
            }
        ]
    }
    
    httpx_mock.add_response(
        url="https://apply.workable.com/api/v1/widget/accounts/folio3",
        json=mock_response
    )
    
    jobs = await workable_adapter.discover_jobs(sample_company)
    
    assert len(jobs) == 1
    job = jobs[0]
    
    assert job.company_name == "Folio3"
    assert job.title == "Software Engineer Trainee"
    assert job.location == "Karachi, Pakistan"
    assert job.source_job_id == "ABCD123"
    assert job.employment_type == "Full-time"
    assert job.url == "https://apply.workable.com/folio3/j/ABCD123/"
    assert job.description == "Some HTML description"
    assert job.posted_at == datetime(2023, 10, 15, tzinfo=timezone.utc)
    assert job.content_hash is not None
