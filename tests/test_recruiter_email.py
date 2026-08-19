import httpx

from job_agent.core.recruiter_email import RecruiterEmailDiscovery
from job_agent.models.job import Job


def _client(pages):
    def handler(request):
        return httpx.Response(200, text=pages.get(str(request.url), ""), request=request)
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def test_extracts_public_mailto_from_job_page():
    job = Job(company_name="Acme", title="Junior Engineer", url="https://jobs.test/1", description="", source="test", content_hash="1")
    client = _client({"https://jobs.test/1": '<a href="mailto:recruiting@acme.test">Apply</a>'})

    result = RecruiterEmailDiscovery(client=client).discover(job)

    assert result.email == "recruiting@acme.test"
    assert result.status == "VERIFIED"
    assert result.source_url == job.url


def test_rejects_placeholders_and_noreply():
    job = Job(company_name="Acme", title="Junior Engineer", url="https://jobs.test/2", description="Email test@example.com or noreply@acme.test", source="test", content_hash="2")
    client = _client({"https://jobs.test/2": "test@example.com noreply@acme.test"})

    result = RecruiterEmailDiscovery(client=client).discover(job)

    assert result.email is None
    assert result.status == "NOT_FOUND"


def test_finds_email_on_cached_official_page_and_does_not_guess():
    job = Job(company_name="Acme", title="Junior Engineer", url="https://jobs.test/3", description="", source="test", content_hash="3")
    career_url = "https://acme.test/careers"
    client = _client({
        "https://jobs.test/3": "No contact here",
        career_url: '<a href="/contact">Contact</a>',
        "https://acme.test/contact": "Recruiting team: hiring@acme.test",
    })
    service = RecruiterEmailDiscovery(client=client)

    result = service.discover(job, career_url)
    second = service.discover(job, career_url)

    assert result.email == "hiring@acme.test"
    assert result.status == "VERIFIED"
    assert second == result
    assert service.verified_count == 2
    assert "careers@" not in (result.email or "")