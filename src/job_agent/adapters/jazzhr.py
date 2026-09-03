import re
import json
import httpx
import logging
import hashlib
from typing import List, Dict, Any
from datetime import datetime, timezone

from .base import JobSourceAdapter
from ..models.company import Company
from ..models.job import Job
from ..utils.url import generate_canonical_content_hash

logger = logging.getLogger(__name__)

class JazzhrAdapter(JobSourceAdapter):
    """
    Adapter for JazzHR Applicant Tracking System.
    Fetches jobs by parsing the public JazzHR careers page HTML.
    """

    async def discover_jobs(self, company: Company) -> List[Job]:
        if not company.career_url:
            logger.error(f"No career URL provided for JazzHR company {company.name}")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(company.career_url)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching JazzHR jobs for {company.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching JazzHR jobs for {company.name}: {e}")
            raise
            
        jobs = []
        
        # Regex to match the job block in the HTML list
        pattern = r'<h3 class=\'list-group-item-heading\'>\s*<a href="([^"]+)">(.*?)</a>\s*</h3>\s*<ul class=\'list-inline list-group-item-text\'>(.*?)</ul>'
        matches = re.finditer(pattern, html, re.DOTALL | re.IGNORECASE)
        
        for m in matches:
            try:
                url = m.group(1).strip()
                title = m.group(2).strip()
                ul_content = m.group(3)
                
                # Extract location from the list items
                li_matches = re.findall(r'<li[^>]*>(.*?)</li>', ul_content, re.DOTALL | re.IGNORECASE)
                location_parts = []
                for li in li_matches:
                    clean_li = re.sub(r'<[^>]+>', '', li).strip()
                    if clean_li:
                        location_parts.append(clean_li)
                
                location_str = " | ".join(location_parts)
                
                # Extract stable job ID from URL (e.g. /apply/plUu5XLKTA/Account-Manager -> plUu5XLKTA)
                source_job_id = ""
                url_parts = url.split('/')
                if 'apply' in url_parts:
                    apply_idx = url_parts.index('apply')
                    if apply_idx + 1 < len(url_parts):
                        source_job_id = url_parts[apply_idx + 1]

                # Create a stable hash to deduplicate jobs uniquely
                content_hash = generate_canonical_content_hash(
                    company_name=company.name,
                    title=title,
                    url=url,
                    source_job_id=source_job_id
                )
                
                job = Job(
                    company_name=company.name,
                    source="jazzhr",
                    source_job_id=source_job_id,
                    title=title,
                    description="", # Description is not extracted from the list view
                    location=location_str,
                    url=url,
                    posted_at=None,
                    raw_data=json.dumps({"title": title, "url": url, "location": location_str}),
                    content_hash=content_hash,
                    status="NEW"
                )
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing job for {company.name}: {e}")
                
        return jobs
        
    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        # Not used because we parse HTML directly in discover_jobs
        pass
