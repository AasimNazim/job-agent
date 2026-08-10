import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.job import Job
from ..adapters.registry import AdapterRegistry

logger = logging.getLogger(__name__)

class DiscoveryEngine:
    """
    Manages concurrent discovery of jobs across multiple companies.
    """
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def _fetch_for_company(self, company: Company) -> List[Job]:
        """
        Fetches jobs for a single company securely bounded by a semaphore.
        """
        async with self.semaphore:
            logger.info(f"Starting discovery for {company.name} ({company.platform})...")
            
            try:
                adapter = AdapterRegistry.get_adapter(company.platform)
            except ValueError as e:
                logger.error(f"Cannot discover jobs for {company.name}: {e}")
                return []
                
            try:
                # Basic timeout wrap is done inside the adapters, but we could wrap here if needed
                jobs = await adapter.discover_jobs(company)
                logger.info(f"Discovered {len(jobs)} jobs for {company.name}.")
                return jobs
            except Exception as e:
                logger.error(f"Fatal error during discovery for {company.name}: {e}")
                return []

    async def run_discovery(self, companies: List[Company]) -> List[Job]:
        """
        Runs discovery concurrently for a list of enabled companies.
        """
        enabled_companies = [c for c in companies if c.enabled]
        logger.info(f"Starting concurrent discovery for {len(enabled_companies)} enabled companies (max_concurrent={self.max_concurrent}).")
        
        tasks = [self._fetch_for_company(company) for company in enabled_companies]
        
        # Gather results (list of lists of Jobs)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs: List[Job] = []
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Uncaught exception in discovery task: {res}")
            elif isinstance(res, list):
                all_jobs.extend(res)
                
        logger.info(f"Total jobs discovered across all companies: {len(all_jobs)}")
        return all_jobs
