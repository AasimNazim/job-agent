import asyncio
import logging
import os
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
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
from .models.notification import JobRun

MAX_NEW_GEMINI_EVALUATIONS_PER_RUN = 20
MAX_DRAFT_GENERATIONS_PER_RUN = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _agent_version():
    try:
        return version("job_agent")
    except PackageNotFoundError:
        return None


def _trigger_type():
    return "MANUAL" if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" else "SCHEDULED"


def _create_run(db):
    try:
        run = JobRun(trigger_type=_trigger_type(), agent_version=_agent_version())
        db.add(run)
        db.commit()
        logger.info("Run started: run_uuid=%s", run.run_uuid)
        return run
    except Exception as error:
        db.rollback()
        logger.error("Could not persist run start: %s", type(error).__name__)
        return None


def _update_run(db, run, metrics):
    if run is None:
        return
    values = {
        "companies_scanned": metrics["companies_scanned"],
        "jobs_discovered": metrics["jobs_discovered"],
        "new_jobs": metrics["new_jobs"],
        "duplicate_jobs": metrics["duplicate_jobs"],
        "jobs_prefiltered": metrics["jobs_after_prefilter"],
        "jobs_evaluated": metrics["jobs_evaluated"],
        "jobs_matched": metrics["matched_jobs"],
        "jobs_ignored": metrics["jobs_ignored"],
        "applications_generated": metrics["drafts_generated"],
        "gmail_drafts_created": metrics["gmail_drafts_pushed"],
        "drafts_created": metrics["drafts_generated"],
        "recruiter_emails_verified": metrics["recruiter_emails_verified"],
        "recruiter_emails_not_found": metrics["recruiter_emails_not_found"],
        "llm_calls": metrics["llm_calls"],
        "llm_successes": metrics["gemini_successes"],
        "llm_failures": metrics["gemini_failures"],
        "rate_limit_retries": metrics["retries_429"],
        "error_count": metrics["error_count"],
    }
    try:
        for name, value in values.items():
            setattr(run, name, value)
        db.commit()
    except Exception as error:
        db.rollback()
        logger.error("Could not persist run metrics: %s", type(error).__name__)


def _finalize_run(db, run, metrics, status, failure_summary=None):
    if run is None:
        return
    completed_at = datetime.now(timezone.utc)
    try:
        _update_run(db, run, metrics)
        run.status = status
        run.completed_at = completed_at
        run.finished_at = completed_at
        run.failure_summary = failure_summary
        db.commit()
        started_at = run.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        duration = (completed_at - started_at).total_seconds()
        logger.info(
            "Run finalized: run_uuid=%s status=%s duration=%.2fs "
            "jobs_discovered=%s new_jobs=%s duplicate_jobs=%s jobs_matched=%s "
            "applications_generated=%s gmail_drafts_created=%s",
            run.run_uuid,
            status,
            duration,
            metrics["jobs_discovered"],
            metrics["new_jobs"],
            metrics["duplicate_jobs"],
            metrics["matched_jobs"],
            metrics["drafts_generated"],
            metrics["gmail_drafts_pushed"],
        )
    except Exception as error:
        db.rollback()
        logger.error("Could not finalize run: %s", type(error).__name__)


def evaluate_jobs_with_limits(new_jobs, evaluator, llm, max_evaluations):
    prefiltered_jobs = []
    ignored_prefilter_count = 0
    for job in new_jobs:
        if evaluator.passes_entry_level_prefilter(job):
            prefiltered_jobs.append(job)
        else:
            job.status = "IGNORED"
            ignored_prefilter_count += 1

    if ignored_prefilter_count > 0:
        evaluator.db.commit()

    evaluation_jobs = prefiltered_jobs[:max_evaluations]

    matched_count = 0
    for job in evaluation_jobs:
        if evaluator.evaluate_job(job):
            matched_count += 1

    return {
        "jobs_after_prefilter": len(prefiltered_jobs),
        "sent_to_gemini": len(evaluation_jobs),
        "matched_jobs": matched_count,
        "jobs_ignored": ignored_prefilter_count + sum(1 for job in evaluation_jobs if job.status == "IGNORED"),
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
        "companies_scanned": 0,
        "jobs_discovered": 0,
        "jobs_after_prefilter": 0,
        "jobs_evaluated": 0,
        "jobs_ignored": 0,
        "new_jobs": 0,
        "duplicate_jobs": 0,
        "already_evaluated": 0,
        "sent_to_gemini": 0,
        "llm_calls": 0,
        "gemini_successes": 0,
        "retries_429": 0,
        "gemini_failures": 0,
        "matched_jobs": 0,
        "drafts_generated": 0,
        "gmail_drafts_pushed": 0,
        "recruiter_emails_verified": 0,
        "recruiter_emails_not_found": 0,
        "error_count": 0,
    }
    
    # 1. Initialize Database
    init_db()
    
    # We use a single session for the entire run for simplicity in this script
    db: Session = next(get_db())
    run = _create_run(db)
    partial_reasons = []
    fatal_error = None
    
    try:
        # 2. Load Configuration
        logger.info("Loading configurations...")
        companies = ConfigurationLoader.load_companies_from_file("config/companies.json", db)
        candidate = ConfigurationLoader.load_candidate_profile("config/candidate.json", db)
        
        if not companies:
            logger.warning("No companies loaded. Exiting.")
            partial_reasons.append("company configuration unavailable")
            return
            
        if not candidate:
            logger.warning("No candidate profile loaded. Exiting.")
            partial_reasons.append("candidate configuration unavailable")
            return

        metrics["companies_scanned"] = sum(1 for company in companies if company.enabled)
        _update_run(db, run, metrics)

        # 3. Parse Resumes
        logger.info("Parsing PDFs for extracted text...")
        parser = ResumeParser(db)
        parser.process_all_resumes()

        # 4. Concurrent Discovery
        logger.info("Starting concurrent job discovery...")
        engine = DiscoveryEngine(max_concurrent=5)
        scraped_jobs = await engine.run_discovery(companies)
        metrics["jobs_discovered"] = len(scraped_jobs)
        _update_run(db, run, metrics)
        
        # 5. Deduplication
        logger.info("Deduplicating and saving jobs...")
        deduplicator = JobDeduplicator(db)
        stats = deduplicator.save_and_deduplicate(scraped_jobs)
        logger.info(f"Discovery complete. New jobs added: {stats['new_jobs']}")
        metrics["already_evaluated"] = stats["seen_jobs"]
        metrics["new_jobs"] = stats["new_jobs"]
        metrics["duplicate_jobs"] = stats["seen_jobs"]
        _update_run(db, run, metrics)
        
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
        metrics["jobs_evaluated"] = evaluation_stats["sent_to_gemini"]
        metrics["llm_calls"] = llm.call_count
        if metrics["gemini_failures"]:
            metrics["error_count"] += metrics["gemini_failures"]
            partial_reasons.append("one or more Gemini evaluations failed")
        _update_run(db, run, metrics)

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
        metrics["llm_calls"] = llm.call_count
        _update_run(db, run, metrics)
                
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
            metrics["error_count"] += 1
            partial_reasons.append("Gmail service unavailable")

        metrics["llm_calls"] = llm.call_count
        _update_run(db, run, metrics)

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
        fatal_error = type(e).__name__
        metrics["error_count"] += 1
    finally:
        if fatal_error:
            status = "FAILED"
            failure_summary = f"fatal error: {fatal_error}"
        elif partial_reasons:
            status = "PARTIAL"
            failure_summary = "; ".join(partial_reasons)[:500]
        else:
            status = "SUCCEEDED"
            failure_summary = None
        _finalize_run(db, run, metrics, status, failure_summary)
        db.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
