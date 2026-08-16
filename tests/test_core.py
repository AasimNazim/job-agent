import pytest
import asyncio
from job_agent.models.company import Company
from job_agent.models.job import Job
from job_agent.core.deduplicator import JobDeduplicator
from job_agent.core.discovery import DiscoveryEngine
from job_agent.adapters.registry import AdapterRegistry
from job_agent.adapters.base import JobSourceAdapter

class DummyFastAdapter(JobSourceAdapter):
    async def discover_jobs(self, company):
        return [Job(company_name=company.name, source="dummy", title="Test Job", url="url", content_hash=f"{company.name}_hash")]

def test_deduplicator(db_session):
    deduplicator = JobDeduplicator(db_session)
    
    # Simulate first run
    jobs = [
        Job(company_name="A", source="dummy", title="Job 1", url="url1", content_hash="hash1", status="NEW"),
        Job(company_name="A", source="dummy", title="Job 2", url="url2", content_hash="hash2", status="NEW")
    ]
    
    stats1 = deduplicator.save_and_deduplicate(jobs)
    assert stats1["new_jobs"] == 2
    assert stats1["seen_jobs"] == 0
    
    # Simulate second run with 1 new job and 2 existing
    jobs_run2 = [
        Job(company_name="A", source="dummy", title="Job 1", url="url1", content_hash="hash1", status="NEW"),
        Job(company_name="A", source="dummy", title="Job 2", url="url2", content_hash="hash2", status="NEW"),
        Job(company_name="B", source="dummy", title="Job 3", url="url3", content_hash="hash3", status="NEW")
    ]
    
    stats2 = deduplicator.save_and_deduplicate(jobs_run2)
    assert stats2["new_jobs"] == 1
    assert stats2["seen_jobs"] == 2
    
    # Verify DB count
    count = db_session.query(Job).count()
    assert count == 3


def test_deduplicator_skips_duplicate_hashes_within_same_batch(db_session):
    deduplicator = JobDeduplicator(db_session)

    jobs = [
        Job(company_name="A", source="dummy", title="Job 1", url="url1", content_hash="shared-hash", status="NEW"),
        Job(company_name="A", source="dummy", title="Job 1 duplicate", url="url1", content_hash="shared-hash", status="NEW"),
        Job(company_name="B", source="dummy", title="Job 2", url="url2", content_hash="hash2", status="NEW"),
    ]

    stats = deduplicator.save_and_deduplicate(jobs)

    assert stats["new_jobs"] == 2
    assert stats["seen_jobs"] == 1
    assert db_session.query(Job).count() == 2
    assert db_session.query(Job).filter_by(content_hash="shared-hash").count() == 1
    assert db_session.query(Job).filter_by(content_hash="hash2").count() == 1

@pytest.mark.asyncio
async def test_discovery_engine():
    AdapterRegistry.register("dummy", DummyFastAdapter)
    
    companies = [
        Company(name="Comp1", platform="dummy", enabled=True),
        Company(name="Comp2", platform="dummy", enabled=True),
        Company(name="Comp3", platform="dummy", enabled=False) # Should be skipped
    ]
    
    engine = DiscoveryEngine(max_concurrent=2)
    jobs = await engine.run_discovery(companies)
    
    assert len(jobs) == 2
    assert jobs[0].company_name in ["Comp1", "Comp2"]
    assert jobs[1].company_name in ["Comp1", "Comp2"]
