import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.job import Job

from ..utils.url import normalize_url

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

            # 1. Check content_hash against DB
            existing_job = self.db.query(Job).filter_by(content_hash=job.content_hash).first()

            # 2. Check source_job_id + company_name fallback if available
            if not existing_job and job.source_job_id and job.company_name:
                existing_job = self.db.query(Job).filter(
                    Job.source_job_id == job.source_job_id,
                    Job.company_name == job.company_name
                ).first()

            # 3. Check canonical job URL fallback if available
            if not existing_job and job.url:
                norm_job_url = normalize_url(job.url)
                existing_job = self.db.query(Job).filter(Job.url == job.url).first()
                if not existing_job:
                    all_company_jobs = self.db.query(Job).filter(Job.company_name == job.company_name).all()
                    for c_job in all_company_jobs:
                        if normalize_url(c_job.url) == norm_job_url:
                            existing_job = c_job
                            break

            # 4. Check company + normalized title fallback when URL and source_job_id are missing
            if not existing_job and not job.source_job_id and not job.url:
                norm_title = job.title.strip().lower() if job.title else ""
                all_company_jobs = self.db.query(Job).filter(Job.company_name == job.company_name).all()
                for c_job in all_company_jobs:
                    if c_job.title and c_job.title.strip().lower() == norm_title:
                        existing_job = c_job
                        break

            if existing_job:
                existing_job.last_seen_at = datetime.now(timezone.utc)
                if job.location and existing_job.location != job.location:
                    existing_job.location = job.location
                if job.description and not existing_job.description:
                    existing_job.description = job.description
                stats["seen_jobs"] += 1
                continue

            # Batch deduplication guard within the same scraped batch
            batch_key = (job.content_hash, normalize_url(job.url) if job.url else "", job.source_job_id or "")
            if (job.content_hash in seen_in_batch or 
                (job.url and normalize_url(job.url) in seen_in_batch) or
                (job.source_job_id and job.source_job_id in seen_in_batch)):
                stats["seen_jobs"] += 1
                continue

            seen_in_batch.add(job.content_hash)
            if job.url:
                seen_in_batch.add(normalize_url(job.url))
            if job.source_job_id:
                seen_in_batch.add(job.source_job_id)

            self.db.add(job)
            stats["new_jobs"] += 1

        self.db.commit()

        if stats["total_processed"] > 0:
            logger.info(
                f"Deduplication complete: {stats['new_jobs']} new, "
                f"{stats['seen_jobs']} seen."
            )

        return stats
