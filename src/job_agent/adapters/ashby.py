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

class AshbyAdapter(JobSourceAdapter):
    """
    Adapter for Ashby Applicant Tracking System.
    Fetches jobs via the public Ashby Job Postings API.
    """
    
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"

    async def discover_jobs(self, company: Company) -> List[Job]:
        board_token = self._extract_board_token(company.career_url)
        if not board_token:
            logger.error(f"Could not extract Ashby board token for {company.name}")
            return []
            
        url = self.BASE_URL.format(board=board_token)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching Ashby jobs for {company.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Ashby jobs for {company.name}: {e}")
            raise
            
        jobs = []
        jobs_list = data.get("jobs", [])
        
        for raw_job in jobs_list:
            try:
                job = self._normalize_job(raw_job, company)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing job for {company.name}: {e}")
                
        return jobs
        
    def _extract_board_token(self, url: str) -> str:
        """
        Extracts the board token from typical Ashby URLs.
        e.g., https://jobs.ashbyhq.com/companyname -> companyname
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if "ashbyhq.com" in parsed.netloc and len(path_parts) > 0:
            if path_parts[0] == "posting-api" and len(path_parts) >= 3:
                return path_parts[2]
            return path_parts[0]
                
        # Fallback
        if len(path_parts) > 0:
            return path_parts[-1]
            
        return ""

    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        """
        Converts the Ashby API response into our standard Job model.
        """
        title = raw_data.get("title", "")
        
        location_str = raw_data.get("location", "")
        employment_type = raw_data.get("employmentType", "")
        
        absolute_url = raw_data.get("jobUrl", "")
        source_job_id = str(raw_data.get("id", ""))
        
        description = raw_data.get("descriptionHtml", "")
        
        posted_at_str = raw_data.get("publishedAt")
        posted_at = None
        if posted_at_str:
            try:
                posted_at = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        hash_input = f"{company.name}|{title}|{location_str}|{absolute_url}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()

        return Job(
            company_name=company.name,
            source="ashby",
            source_job_id=source_job_id,
            title=title,
            description=description,
            location=location_str,
            employment_type=employment_type,
            url=absolute_url,
            posted_at=posted_at,
            raw_data=json.dumps(raw_data),
            content_hash=content_hash,
            status="NEW"
        )
