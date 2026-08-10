import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.job import Job

logger = logging.getLogger(__name__)

class JobDeduplicator:
    """
    Handles tracking job state, deduplicating fetched jobs, and storing them in the DB.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def save_and_deduplicate(self, jobs: List[Job]) -> Dict[str, Any]:
        """
        Saves new jobs and updates `last_seen_at` for existing ones.
        Returns statistics about the operation.
        """
        stats = {
            "total_processed": 0,
            "new_jobs": 0,
            "seen_jobs": 0
        }
        
        for job in jobs:
            stats["total_processed"] += 1
            
            # Check by content_hash which is extremely stable across platforms
            existing_job = self.db.query(Job).filter_by(content_hash=job.content_hash).first()
            
            if existing_job:
                # Update last_seen_at to keep it fresh
                existing_job.last_seen_at = datetime.now(timezone.utc)
                stats["seen_jobs"] += 1
            else:
                self.db.add(job)
                stats["new_jobs"] += 1
                
        # Commit all changes for this batch
        self.db.commit()
        
        if stats["total_processed"] > 0:
            logger.info(
                f"Deduplication complete: {stats['new_jobs']} new, "
                f"{stats['seen_jobs']} seen."
            )
            
        return stats
