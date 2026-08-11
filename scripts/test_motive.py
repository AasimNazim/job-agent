import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from job_agent.adapters import AdapterRegistry
from job_agent.models.company import Company

async def test_motive():
    company = Company(name="Motive", career_url="https://boards.greenhouse.io/motive", platform="greenhouse", enabled=True)
    adapter = AdapterRegistry.get_adapter("greenhouse")
    jobs = await adapter.discover_jobs(company)
    
    print(f"Total jobs found: {len(jobs)}")
    for i, job in enumerate(jobs[:3]):
        print(f"{i+1}. {job.title}")
        print(f"   {job.url}")

if __name__ == "__main__":
    asyncio.run(test_motive())
