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
        seen_in_batch = set()

        for job in jobs:
            stats["total_processed"] += 1

            # Preserve the existing cross-run deduplication check against the database.
            existing_job = self.db.query(Job).filter_by(content_hash=job.content_hash).first()
            if existing_job:
                existing_job.last_seen_at = datetime.now(timezone.utc)
                stats["seen_jobs"] += 1
                continue

            # Guard against duplicate content_hash values within the same scraped batch.
            if job.content_hash in seen_in_batch:
                stats["seen_jobs"] += 1
                continue

            seen_in_batch.add(job.content_hash)
            self.db.add(job)
            stats["new_jobs"] += 1

        self.db.commit()

        if stats["total_processed"] > 0:
            logger.info(
                f"Deduplication complete: {stats['new_jobs']} new, "
                f"{stats['seen_jobs']} seen."
            )

        return stats
