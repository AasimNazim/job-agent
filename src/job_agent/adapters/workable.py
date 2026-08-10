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

logger = logging.getLogger(__name__)

class WorkableAdapter(JobSourceAdapter):
    """
    Adapter for Workable Applicant Tracking System.
    Fetches jobs via the public Workable Widget API.
    """
    
    BASE_URL = "https://apply.workable.com/api/v1/widget/accounts/{account}"

    async def discover_jobs(self, company: Company) -> List[Job]:
        account_token = self._extract_account_token(company.career_url)
        if not account_token:
            logger.error(f"Could not extract Workable account token for {company.name}")
            return []
            
        url = self.BASE_URL.format(account=account_token)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching Workable jobs for {company.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Workable jobs for {company.name}: {e}")
            return []
            
        jobs = []
        jobs_list = data.get("jobs", [])
        
        for raw_job in jobs_list:
            try:
                job = self._normalize_job(raw_job, company)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing job for {company.name}: {e}")
                
        return jobs
        
    def _extract_account_token(self, url: str) -> str:
        """
        Extracts the account token from typical Workable URLs.
        e.g., https://apply.workable.com/folio3/ -> folio3
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if "workable.com" in parsed.netloc:
            # Usually apply.workable.com/account_name
            if len(path_parts) > 0 and path_parts[0] not in ["api", "spi"]:
                return path_parts[0]
                
            # If it's something.workable.com
            subdomain = parsed.netloc.split(".")[0]
            if subdomain and subdomain != "apply" and subdomain != "www":
                return subdomain
                
        # Fallback
        if len(path_parts) > 0:
            return path_parts[-1]
            
        return ""

    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        """
        Converts the Workable API response into our standard Job model.
        """
        title = raw_data.get("title", "")
        
        location_obj = raw_data.get("location", {})
        city = location_obj.get("city", "")
        country = location_obj.get("country", "")
        location_str = f"{city}, {country}".strip(", ")
        
        employment_type = raw_data.get("type", "")
        absolute_url = raw_data.get("url", "")
        source_job_id = str(raw_data.get("shortcode", ""))
        
        # Workable widget API doesn't always provide full description, 
        # sometimes it provides 'description' or we have to rely on title matching.
        description = raw_data.get("description", "")
        
        posted_at_str = raw_data.get("published_on")
        posted_at = None
        if posted_at_str:
            try:
                posted_at = datetime.strptime(posted_at_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        hash_input = f"{company.name}|{title}|{location_str}|{absolute_url}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()

        return Job(
            company_name=company.name,
            source="workable",
            source_job_id=source_job_id,
            title=title,
            description=description,
            location=location_str,
            country=country,
            employment_type=employment_type,
            url=absolute_url,
            posted_at=posted_at,
            raw_data=json.dumps(raw_data),
            content_hash=content_hash,
            status="NEW"
        )
