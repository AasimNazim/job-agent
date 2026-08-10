import asyncio
import logging
from sqlalchemy.orm import Session

from .config import settings
from .database.database import get_db, init_db
from .core.config_loader import ConfigurationLoader
from .core.discovery import DiscoveryEngine
from .core.deduplicator import JobDeduplicator
from .core.resume_parser import ResumeParser
from .core.llm import LLMService
from .core.evaluator import JobEvaluator
from .core.generator import ApplicationGenerator
from .core.gmail import GmailService
from .models.company import Company
from .models.job import Job

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def async_main():
    """
    The main autonomous loop for the Job Agent.
    """
    logger.info("Initializing Autonomous Job Agent...")
    
    # 1. Initialize Database
    init_db()
    
    # We use a single session for the entire run for simplicity in this script
    db: Session = next(get_db())
    
    try:
        # 2. Load Configuration
        logger.info("Loading configurations...")
        companies = ConfigurationLoader.load_companies_from_file("config/companies.json", db)
        candidate = ConfigurationLoader.load_candidate_profile("config/candidate.json", db)
        
        if not companies:
            logger.warning("No companies loaded. Exiting.")
            return
            
        if not candidate:
            logger.warning("No candidate profile loaded. Exiting.")
            return

        # 3. Parse Resumes
        logger.info("Parsing PDFs for extracted text...")
        parser = ResumeParser(db)
        parser.process_all_resumes()

        # 4. Concurrent Discovery
        logger.info("Starting concurrent job discovery...")
        engine = DiscoveryEngine(max_concurrent=5)
        scraped_jobs = await engine.run_discovery(companies)
        
        # 5. Deduplication
        logger.info("Deduplicating and saving jobs...")
        deduplicator = JobDeduplicator(db)
        stats = deduplicator.save_and_deduplicate(scraped_jobs)
        logger.info(f"Discovery complete. New jobs added: {stats['new_jobs']}")
        
        # 6. Job Evaluation
        logger.info("Evaluating NEW jobs with LLM...")
        llm = LLMService()
        evaluator = JobEvaluator(db, llm)
        
        # Fetch only NEW jobs
        new_jobs = db.query(Job).filter_by(status="NEW").all()
        matched_count = 0
        for job in new_jobs:
            if evaluator.evaluate_job(job):
                matched_count += 1
                
        logger.info(f"Evaluation complete. Found {matched_count} matching entry-level jobs.")
        
        # 7. Generate Applications
        logger.info("Generating application drafts for MATCHED jobs...")
        generator = ApplicationGenerator(db, llm)
        matched_jobs = db.query(Job).filter_by(status="MATCHED").all()
        
        drafts_generated = 0
        for job in matched_jobs:
            app = generator.generate_draft(job)
            if app:
                drafts_generated += 1
                
        logger.info(f"Generated {drafts_generated} new application drafts.")
        
        # 8. Push to Gmail and Send Notifications
        logger.info("Pushing pending drafts to Gmail...")
        gmail_service = GmailService(db)
        if gmail_service.service:
            pushed_count = gmail_service.process_pending_drafts()
            logger.info(f"Successfully pushed {pushed_count} drafts to Gmail.")
            
            # Send email notifications for the created drafts
            logger.info("Sending Gmail notifications for new drafts...")
            candidate_email = candidate.profile_data.get("email")
            notif_count = gmail_service.process_pending_notifications(candidate_email)
            logger.info(f"Sent {notif_count} email notifications.")
            
        else:
            logger.warning("Gmail service not authenticated. Skipping Gmail push.")
            
        logger.info("Autonomous loop completed successfully.")

    except Exception as e:
        logger.error(f"Agent encountered a fatal error: {e}", exc_info=True)
    finally:
        db.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
