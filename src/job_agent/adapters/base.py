from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.company import Company
from ..models.job import Job

class JobSourceAdapter(ABC):
    """
    Base interface for all Job ATS/Career page adapters.
    """
    
    @abstractmethod
    async def discover_jobs(self, company: Company) -> List[Job]:
        """
        Discover jobs for a specific company and return them as normalized Job models.
        """
        pass
        
    def _normalize_job(self, raw_data: Dict[str, Any], company: Company) -> Job:
        """
        Helper method to normalize raw ATS data into a standard Job model.
        Should be implemented/used by subclasses.
        """
        raise NotImplementedError
