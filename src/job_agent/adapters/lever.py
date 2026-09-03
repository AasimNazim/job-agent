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

class LeverAdapter(JobSourceAdapter):
    """
    Adapter for Lever Applicant Tracking System.
    Fetches jobs via the public Lever API.
    """
    
    BASE_URL = "https://api.lever.co/v0/postings/{site}?mode=json"

    async def discover_jobs(self, company: Company) -> List[Job]:
        site_token = self._extract_site_token(company.career_url)
        if not site_token:
            logger.error(f"Could not extract Lever site token for {company.name}")
            return []
            
        url = self.BASE_URL.format(site=site_token)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching Lever jobs for {company.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Lever jobs for {company.name}: {e}")
            raise
            
        jobs = []
        # Lever API returns a list of jobs directly (not wrapped in a "jobs" key)
        if not isinstance(data, list):
            logger.error(f"Unexpected JSON format from Lever for {company.name}")
            return []
            
        for raw_job in data:
            try:
                job = self._normalize_job(raw_job, company)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing job for {company.name}: {e}")
                
        return jobs
        
    def _extract_site_token(self, url: str) -> str:
        """
        Extracts the site token from typical Lever URLs.
        e.g., https://jobs.lever.co/companyname -> companyname
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # If URL is jobs.lever.co/token
        if "jobs.lever.co" in parsed.netloc and len(path_parts) > 0:
            return path_parts[0]
            
        # If URL is api.lever.co/v0/postings/token
        if "api.lever.co" in parsed.netloc and len(path_parts) > 0:
            return path_parts[-1]
            
        # Fallback if the token is passed directly or embedded differently
        if len(path_parts) > 0:
            return path_parts[-1]
            
        return ""

    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        """
        Converts the Lever API response into our standard Job model.
        """
        title = raw_data.get("text", "")
        
        categories = raw_data.get("categories", {})
        location_str = categories.get("location", "")
        employment_type = categories.get("commitment", "")
        
        absolute_url = raw_data.get("hostedUrl", "")
        source_job_id = str(raw_data.get("id", ""))
        
        description_plain = raw_data.get("descriptionPlain", "")
        
        posted_at_ms = raw_data.get("createdAt")
        posted_at = None
        if posted_at_ms:
            try:
                # Lever provides createdAt as a timestamp in milliseconds
                posted_at = datetime.fromtimestamp(posted_at_ms / 1000.0, tz=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Create a stable hash to deduplicate jobs uniquely
        content_hash = generate_canonical_content_hash(
            company_name=company.name,
            title=title,
            url=absolute_url,
            source_job_id=source_job_id
        )

        return Job(
            company_name=company.name,
            source="lever",
            source_job_id=source_job_id,
            title=title,
            description=description_plain,
            location=location_str,
            employment_type=employment_type,
            url=absolute_url,
            posted_at=posted_at,
            raw_data=json.dumps(raw_data),
            content_hash=content_hash,
            status="NEW"
        )
