import re
import json
import httpx
import logging
import hashlib
from typing import List, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse

from .base import JobSourceAdapter
from ..models.company import Company
from ..models.job import Job
from ..utils.url import generate_canonical_content_hash

logger = logging.getLogger(__name__)

class HirestreamAdapter(JobSourceAdapter):
    """
    Adapter for Hirestream ATS.
    Fetches jobs via the Hirestream published-jobs API.
    """

    async def discover_jobs(self, company: Company) -> List[Job]:
        if not company.career_url:
            logger.error(f"No career URL provided for Hirestream company {company.name}")
            return []
            
        # Parse base domain
        parsed_url = urlparse(company.career_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        api_url = f"{base_domain}/api/v1/jobs/published-jobs/"
        
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(api_url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Hirestream jobs for {company.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Hirestream jobs for {company.name}: {e}")
            raise
            
        jobs = []
        
        # The API returns a dict with 'results'
        results = data.get("results", []) if isinstance(data, dict) else data
        
        for raw_job in results:
            try:
                job = self._normalize_job(raw_job, company, base_domain)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing job for {company.name}: {e}")
                
        return jobs
        
    def _normalize_job(self, raw_data: Dict[str, Any], company: Company, base_domain: str = "") -> Job:
        # Some methods to call this only pass 2 arguments based on JobSourceAdapter signature
        # We handle the default base_domain in discover_jobs and call it with 3 arguments directly.
        pass
        
    # We override the helper method to accept base_domain
    def _normalize_job(self, raw_data: Dict[str, Any], company: Company, base_domain: str = "") -> Job:
        title = raw_data.get("title", "")
        location_str = raw_data.get("location", "")
        # Hirestream returns 'uuid' which is the unique stable identifier
        source_job_id = str(raw_data.get("uuid", raw_data.get("id", "")))
        
        absolute_url = f"{base_domain}/careers/{source_job_id}"
        
        posted_at = None
        modified_str = raw_data.get("modified")
        if modified_str:
            try:
                posted_at = datetime.fromisoformat(modified_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        content_hash = generate_canonical_content_hash(
            company_name=company.name,
            title=title,
            url=absolute_url,
            source_job_id=source_job_id
        )

        return Job(
            company_name=company.name,
            source="hirestream",
            source_job_id=source_job_id,
            title=title,
            description="", 
            location=location_str,
            url=absolute_url,
            posted_at=posted_at,
            raw_data=json.dumps(raw_data),
            content_hash=content_hash,
            status="NEW"
        )
