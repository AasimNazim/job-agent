import sys
import logging
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from job_agent.database.database import get_db, init_db
from job_agent.models.job import Job
from job_agent.models.candidate import Resume
from job_agent.core.evaluator import JobEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_job_statuses")

def fix_statuses():
    init_db()
    db = next(get_db())
    
    new_jobs = db.query(Job).filter_by(status="NEW").all()
    logger.info(f"Found {len(new_jobs)} jobs with status='NEW'.")
    
    ignored_count = 0
    retained_new_count = 0
    
    for job in new_jobs:
        if JobEvaluator.passes_entry_level_prefilter(job):
            retained_new_count += 1
            logger.info(f"Retained as NEW (passes pre-filter): Job {job.id} - '{job.title}' at {job.company_name}")
        else:
            job.status = "IGNORED"
            ignored_count += 1
            
    # Check MATCHED jobs with empty selected_resume
    matched_jobs = db.query(Job).filter_by(status="MATCHED").all()
    resumes = db.query(Resume).all()
    fixed_matched = 0
    for job in matched_jobs:
        if not job.selected_resume:
            best_domain = JobEvaluator.select_resume_domain(job, resumes)
            if best_domain:
                job.selected_resume = best_domain
                fixed_matched += 1
                logger.info(f"Fixed MATCHED job {job.id} '{job.title}': assigned resume domain '{best_domain}'")
            else:
                logger.warning(f"MATCHED job {job.id} '{job.title}' has no matching resume domain.")

    db.commit()
    logger.info(f"Cleanup complete:")
    logger.info(f"  - Ignored non-entry-level jobs: {ignored_count}")
    logger.info(f"  - Retained valid entry-level jobs as NEW: {retained_new_count}")
    logger.info(f"  - Fixed MATCHED jobs with missing resume: {fixed_matched}")
    db.close()

if __name__ == "__main__":
    fix_statuses()
