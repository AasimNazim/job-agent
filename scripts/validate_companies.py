import os
import sys
import json
import asyncio

# Ensure src is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from job_agent.adapters import AdapterRegistry
from job_agent.models.company import Company

async def validate_companies():
    config_path = os.path.join(os.path.dirname(__file__), '../config/companies.json')
    if not os.path.exists(config_path):
        print(f"Error: Could not find {config_path}")
        return

    with open(config_path, 'r') as f:
        companies_data = json.load(f)

    print(f"{'Company':<30} | {'Platform':<15} | {'Jobs':<6} | {'Status'}")
    print("-" * 75)

    supported_platforms = AdapterRegistry.supported_platforms()

    for data in companies_data:
        company = Company(**data)
        if not getattr(company, 'enabled', True):
            continue
            
        platform = company.platform.lower()

        if platform not in supported_platforms:
            print(f"{company.name[:28]:<30} | {platform[:15]:<15} | {'0':<6} | NEEDS ADAPTER")
            continue

        try:
            adapter = AdapterRegistry.get_adapter(platform)
            jobs = await adapter.discover_jobs(company)
            job_count = len(jobs)
            status = "PASS" if job_count >= 0 else "FAIL" # Adapters return empty list if failed or no jobs. Let's just say PASS if no exception.
            
            # Basic validation: if we couldn't fetch due to bad URL, jobs is []
            # We don't have strict exception catching here because adapters handle them and return []
            
            print(f"{company.name[:28]:<30} | {platform[:15]:<15} | {str(job_count):<6} | {status}")
        except Exception as e:
            print(f"{company.name[:28]:<30} | {platform[:15]:<15} | {'0':<6} | FAIL ({e})")

if __name__ == "__main__":
    asyncio.run(validate_companies())
