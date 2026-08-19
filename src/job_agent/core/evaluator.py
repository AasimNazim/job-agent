import logging
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .llm import LLMService
from ..models.job import Job
from ..models.candidate import CandidateProfile, Resume

logger = logging.getLogger(__name__)

ENTRY_LEVEL_KEYWORDS = (
    "intern",
    "internship",
    "internee",
    "trainee",
    "graduate trainee",
    "management trainee",
    "mto",
    "fresh graduate",
    "entry level",
    "junior",
    "apprentice",
    "associate",
    "graduate program",
    "early careers",
    "campus",
)

class EvaluationResult(BaseModel):
    is_entry_level: bool = Field(description="True if this job is suitable for a fresh graduate or entry-level candidate. False if it requires significant prior experience (e.g., 3+ years) or is a senior role.")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    reason: str = Field(description="Brief explanation of why this job is or isn't entry-level.")
    selected_resume_domain: str = Field(description="The domain_name of the best matching resume for this job. If not entry-level, this can be empty.")

class JobEvaluator:
    """
    Evaluates jobs using an LLM to determine entry-level suitability and select the best resume.
    """
    def __init__(self, db: Session, llm_service: LLMService):
        self.db = db
        self.llm = llm_service
        self.candidate = self._load_candidate()
        self.resumes = self._load_resumes()
        
    def _load_candidate(self) -> CandidateProfile:
        return self.db.query(CandidateProfile).first()
        
    def _load_resumes(self) -> List[Resume]:
        if not self.candidate:
            return []
        return self.db.query(Resume).all()

    @staticmethod
    def select_resume_domain(job: Job, resumes: List[Resume]) -> Optional[str]:
        """Select the best resume locally when an LLM result is incomplete."""
        job_text = f"{job.title or ''} {job.description or ''}".lower()
        job_terms = set(re.findall(r"[a-z0-9]+", job_text))
        aliases = {
            "data_science": {"data", "science", "analytics", "analyst", "machine", "learning", "statistics"},
            "bank_it": {"bank", "banking", "finance", "financial", "accounting", "audit", "risk", "it", "support"},
            "flutter_mobile": {"flutter", "dart", "mobile", "android", "ios", "app"},
            "software_engineering": {"software", "developer", "development", "backend", "frontend", "python", "api", "web"},
            "product_management": {"product", "management", "manager", "agile", "scrum", "roadmap", "stakeholder"},
        }
        stop_words = {"a", "an", "and", "for", "from", "in", "of", "on", "or", "the", "to", "with", "is", "this", "role", "looking"}
        best_domain = None
        best_score = 0
        for resume in resumes:
            if not resume.domains:
                continue
            domain = resume.domains[0]
            domain_terms = set(re.findall(r"[a-z0-9]+", domain.replace("_", " ")))
            relevant_terms = aliases.get(domain, domain_terms)
            score = 4 * len(job_terms & relevant_terms)
            resume_terms = set(re.findall(r"[a-z0-9]+", (resume.extracted_text or "").lower())) - stop_words
            score += len(job_terms & resume_terms)
            if score > best_score or (score == best_score and score > 0 and domain < (best_domain or domain)):
                best_domain = domain
                best_score = score
        return best_domain

    def _valid_resume_domain(self, domain: str) -> bool:
        return any(resume.domains and domain in resume.domains for resume in self.resumes)

    @staticmethod
    def passes_entry_level_prefilter(job: Job) -> bool:
        text = f"{job.title or ''} {job.description or ''}".lower()
        return any(keyword in text for keyword in ENTRY_LEVEL_KEYWORDS)
        
    def evaluate_job(self, job: Job) -> bool:
        """
        Evaluates a single job. Updates the job state in the database.
        Returns True if matched, False otherwise.
        """
        if job.status != "NEW":
            logger.debug(f"Skipping already-evaluated job {job.id} with status={job.status}.")
            return job.status == "MATCHED"

        if not self.passes_entry_level_prefilter(job):
            job.status = "IGNORED"
            self.db.commit()
            logger.debug(f"IGNORED by pre-filter: {job.title} at {job.company_name}")
            return False

        if not self.candidate or not self.resumes:
            logger.error("Cannot evaluate job: Candidate profile or resumes missing.")
            return False
            
        # Build prompt context
        available_domains = [r.domains[0] for r in self.resumes if r.domains]
        
        prompt = f"""
        You are an expert technical recruiter AI.
        
        Evaluate the following job description for an applicant who is a {self.candidate.career_level} candidate.
        
        Candidate Skills: {self.candidate.profile_data.get('skills_summary', '')}
        
        Job Title: {job.title}
        Company: {job.company_name}
        Job Description: {job.description}
        
        Determine if this job is truly an entry-level or junior role suitable for someone with 0-2 years of experience.
        If it requires 3+ years of professional experience, it is NOT entry-level.
        
        If it IS entry-level, select the MOST APPROPRIATE resume domain from this list: {available_domains}.
        
        Return your analysis as JSON.
        """
        
        try:
            result: EvaluationResult = self.llm.generate_structured_response(prompt, EvaluationResult)
            
            if result.is_entry_level and result.confidence >= 0.7:
                selected_resume = result.selected_resume_domain.strip()
                if not self._valid_resume_domain(selected_resume):
                    selected_resume = self.select_resume_domain(job, self.resumes) or ""
                if not selected_resume:
                    job.status = "IGNORED"
                    job.selected_resume = None
                    job.match_confidence = None
                    self.db.commit()
                    logger.warning(f"MATCHED result discarded for job {job.id}: no suitable resume found.")
                    return False
                job.status = "MATCHED"
                job.selected_resume = selected_resume
                job.match_confidence = result.confidence
                logger.info(f"MATCHED: {job.title} at {job.company_name}. Selected resume: {job.selected_resume}")
            else:
                job.status = "IGNORED"
                logger.debug(f"IGNORED: {job.title} at {job.company_name}. Reason: {result.reason}")
                
            self.db.commit()
            return job.status == "MATCHED"
            
        except Exception as e:
            logger.error(f"Failed to evaluate job {job.id}: {e}")
            return False
