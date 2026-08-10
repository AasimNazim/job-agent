import pytest
import httpx
from datetime import datetime
from job_agent.models.company import Company
from job_agent.adapters.lever import LeverAdapter

@pytest.fixture
def lever_adapter():
    return LeverAdapter()

@pytest.fixture
def sample_company():
    return Company(
        name="TestCompany",
        career_url="https://jobs.lever.co/testcompany",
        platform="lever",
        enabled=True
    )

def test_extract_site_token(lever_adapter):
    token = lever_adapter._extract_site_token("https://jobs.lever.co/testcompany")
    assert token == "testcompany"
    
    token2 = lever_adapter._extract_site_token("https://api.lever.co/v0/postings/some-org")
    assert token2 == "some-org"

@pytest.mark.asyncio
async def test_discover_jobs(httpx_mock, lever_adapter, sample_company):
    mock_response = [
        {
            "id": "abc-123",
            "text": "Data Analyst Intern",
            "hostedUrl": "https://jobs.lever.co/testcompany/abc-123",
            "categories": {
                "location": "Lahore, Pakistan",
                "commitment": "Intern"
            },
            "descriptionPlain": "Job description here",
            "createdAt": 1679904000000  # Some timestamp in ms
        }
    ]
    
    httpx_mock.add_response(
        url="https://api.lever.co/v0/postings/testcompany?mode=json",
        json=mock_response
    )
    
    jobs = await lever_adapter.discover_jobs(sample_company)
    
    assert len(jobs) == 1
    job = jobs[0]
    
    assert job.company_name == "TestCompany"
    assert job.title == "Data Analyst Intern"
    assert job.location == "Lahore, Pakistan"
    assert job.source_job_id == "abc-123"
    assert job.employment_type == "Intern"
    assert job.url == "https://jobs.lever.co/testcompany/abc-123"
    assert job.description == "Job description here"
    assert job.content_hash is not None
