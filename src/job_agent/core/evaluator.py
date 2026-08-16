import logging
import json
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
                job.status = "MATCHED"
                job.selected_resume = result.selected_resume_domain
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
