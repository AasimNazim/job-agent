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

logger = logging.getLogger(__name__)

class GreenhouseAdapter(JobSourceAdapter):
    """
    Adapter for Greenhouse Applicant Tracking System.
    Fetches jobs via the public Greenhouse Boards API.
    """
    
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    async def discover_jobs(self, company: Company) -> List[Job]:
        board_token = self._extract_board_token(company.career_url)
        if not board_token:
            logger.error(f"Could not extract Greenhouse board token for {company.name}")
            return []
            
        url = self.BASE_URL.format(board_token=board_token)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching Greenhouse jobs for {company.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for {company.name}: {e}")
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
        
    def _extract_board_token(self, url: str) -> str:
        """
        Extracts the board token from typical Greenhouse URLs.
        e.g., https://boards.greenhouse.io/venturedive -> venturedive
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # If URL is boards.greenhouse.io/token
        if "greenhouse.io" in parsed.netloc and len(path_parts) > 0:
            return path_parts[0]
            
        # Fallback if the token is passed directly or embedded differently
        if len(path_parts) > 0:
            return path_parts[-1]
            
        return ""

    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        """
        Converts the Greenhouse API response into our standard Job model.
        """
        title = raw_data.get("title", "")
        location_obj = raw_data.get("location", {})
        location_str = location_obj.get("name", "")
        absolute_url = raw_data.get("absolute_url", "")
        
        source_job_id = str(raw_data.get("id", ""))
        
        content = raw_data.get("content", "")
        
        # Optional: attempt to parse updated_at
        # Greenhouse often returns "updated_at": "2024-03-27T10:45:00-04:00"
        posted_at = None
        updated_at_str = raw_data.get("updated_at")
        if updated_at_str:
            try:
                # Basic parsing, might need dateutil for robust tz offsets if needed
                posted_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Create a stable hash to deduplicate jobs uniquely
        hash_input = f"{company.name}|{title}|{location_str}|{absolute_url}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()

        return Job(
            company_name=company.name,
            source="greenhouse",
            source_job_id=source_job_id,
            title=title,
            description=content,
            location=location_str,
            url=absolute_url,
            posted_at=posted_at,
            raw_data=json.dumps(raw_data),
            content_hash=content_hash,
            status="NEW"
        )
