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
from .core.recruiter_email import RecruiterEmailDiscovery
from .models.company import Company
from .models.job import Job

MAX_NEW_GEMINI_EVALUATIONS_PER_RUN = 20
MAX_DRAFT_GENERATIONS_PER_RUN = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def evaluate_jobs_with_limits(new_jobs, evaluator, llm, max_evaluations):
    prefiltered_jobs = [job for job in new_jobs if evaluator.passes_entry_level_prefilter(job)]
    evaluation_jobs = prefiltered_jobs[:max_evaluations]

    matched_count = 0
    for job in evaluation_jobs:
        if evaluator.evaluate_job(job):
            matched_count += 1

    return {
        "jobs_after_prefilter": len(prefiltered_jobs),
        "sent_to_gemini": len(evaluation_jobs),
        "matched_jobs": matched_count,
        "gemini_successes": llm.success_count,
        "retries_429": llm.retry_429_count,
        "gemini_failures": llm.failure_count,
    }


def generate_drafts_with_limit(matched_jobs, generator, max_generations):
    generation_jobs = matched_jobs[:max_generations]
    drafts_generated = 0
    for job in generation_jobs:
        app = generator.generate_draft(job)
        if app:
            drafts_generated += 1
    return drafts_generated

async def async_main():
    """
    The main autonomous loop for the Job Agent.
    """
    logger.info("Initializing Autonomous Job Agent...")
    metrics = {
        "jobs_discovered": 0,
        "jobs_after_prefilter": 0,
        "already_evaluated": 0,
        "sent_to_gemini": 0,
        "gemini_successes": 0,
        "retries_429": 0,
        "gemini_failures": 0,
        "matched_jobs": 0,
        "drafts_generated": 0,
        "gmail_drafts_pushed": 0,
        "recruiter_emails_verified": 0,
        "recruiter_emails_not_found": 0,
    }
    
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
        metrics["jobs_discovered"] = len(scraped_jobs)
        
        # 5. Deduplication
        logger.info("Deduplicating and saving jobs...")
        deduplicator = JobDeduplicator(db)
        stats = deduplicator.save_and_deduplicate(scraped_jobs)
        logger.info(f"Discovery complete. New jobs added: {stats['new_jobs']}")
        metrics["already_evaluated"] = stats["seen_jobs"]
        
        # 6. Job Evaluation
        logger.info("Evaluating NEW jobs with LLM...")
        llm = LLMService()
        evaluator = JobEvaluator(db, llm)
        
        # Fetch only NEW jobs
        new_jobs = db.query(Job).filter_by(status="NEW").all()
        evaluation_stats = evaluate_jobs_with_limits(
            new_jobs,
            evaluator,
            llm,
            MAX_NEW_GEMINI_EVALUATIONS_PER_RUN,
        )
        metrics.update(evaluation_stats)

        logger.info(f"Evaluation complete. Found {metrics['matched_jobs']} matching entry-level jobs.")
        
        # 7. Generate Applications
        logger.info("Generating application drafts for MATCHED jobs...")
        recruiter_email_service = RecruiterEmailDiscovery()
        generator = ApplicationGenerator(db, llm, recruiter_email_service)
        matched_jobs = db.query(Job).filter_by(status="MATCHED").all()
        drafts_generated = generate_drafts_with_limit(
            matched_jobs,
            generator,
            MAX_DRAFT_GENERATIONS_PER_RUN,
        )
        metrics["drafts_generated"] = drafts_generated
        metrics["recruiter_emails_verified"] = recruiter_email_service.verified_count if hasattr(recruiter_email_service, "verified_count") else 0
        metrics["recruiter_emails_not_found"] = recruiter_email_service.not_found_count if hasattr(recruiter_email_service, "not_found_count") else 0
                
        logger.info(f"Generated {drafts_generated} new application drafts.")
        
        # 8. Push to Gmail and Send Notifications
        logger.info("Pushing pending drafts to Gmail...")
        gmail_service = GmailService(db)
        if gmail_service.service:
            pushed_count = gmail_service.process_pending_drafts()
            logger.info(f"Successfully pushed {pushed_count} drafts to Gmail.")
            metrics["gmail_drafts_pushed"] = pushed_count
            
            # Send email notifications for the created drafts (DISABLED FOR SAFE TEST)
            # logger.info("Sending Gmail notifications for new drafts...")
            # candidate_email = candidate.profile_data.get("email")
            # notif_count = gmail_service.process_pending_notifications(candidate_email)
            # logger.info(f"Sent {notif_count} email notifications.")
            
        else:
            logger.warning("Gmail service not authenticated. Skipping Gmail push.")

        logger.info(f"Jobs discovered: {metrics['jobs_discovered']}")
        logger.info(f"Jobs after pre-filter: {metrics['jobs_after_prefilter']}")
        logger.info(f"Already evaluated: {metrics['already_evaluated']}")
        logger.info(f"Sent to Gemini: {metrics['sent_to_gemini']}")
        logger.info(f"Gemini successes: {metrics['gemini_successes']}")
        logger.info(f"429 retries: {metrics['retries_429']}")
        logger.info(f"Gemini failures: {metrics['gemini_failures']}")
        logger.info(f"Entry-level jobs matched: {metrics['matched_jobs']}")
        logger.info(f"Drafts generated: {metrics['drafts_generated']}")
        logger.info(f"Gmail drafts created: {metrics['gmail_drafts_pushed']}")
        logger.info(f"Recruiter emails verified: {metrics['recruiter_emails_verified']}")
        logger.info(f"Recruiter emails not found: {metrics['recruiter_emails_not_found']}")
            
        logger.info("Autonomous loop completed successfully.")

    except Exception as e:
        logger.error(f"Agent encountered a fatal error: {e}", exc_info=True)
    finally:
        db.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
