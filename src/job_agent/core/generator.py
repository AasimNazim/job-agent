import logging
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .llm import LLMService
from ..models.job import Job
from ..models.candidate import CandidateProfile, Resume
from ..models.application import Application

logger = logging.getLogger(__name__)

class EmailDraftResult(BaseModel):
    subject: str = Field(description="A professional email subject line for the job application.")
    body: str = Field(description="The professional, tailored email body text. It should read naturally, avoid sounding overly robotic, and match the candidate's skills to the job description.")

class ApplicationGenerator:
    """
    Uses the LLM to generate highly tailored application drafts.
    """
    def __init__(self, db: Session, llm_service: LLMService):
        self.db = db
        self.llm = llm_service
        self.candidate = self._load_candidate()
        
    def _load_candidate(self) -> CandidateProfile:
        return self.db.query(CandidateProfile).first()
        
    def _get_resume(self, domain_name: str) -> Optional[Resume]:
        if not self.candidate or not domain_name:
            return None
        # We search by matching the domain inside the JSON array. 
        # For simplicity in Python, we fetch all for candidate and filter manually since SQLite JSON operations vary.
        resumes = self.db.query(Resume).all()
        for r in resumes:
            if r.domains and domain_name in r.domains:
                return r
        return None

    def generate_draft(self, job: Job) -> Optional[Application]:
        """
        Generates an application draft for a MATCHED job using the selected resume.
        Saves the application to the database.
        """
        if not self.candidate:
            logger.error("Cannot generate draft: Candidate profile missing.")
            return None
            
        if job.status != "MATCHED" or not job.selected_resume:
            logger.error(f"Job {job.id} is not ready for draft generation.")
            return None
            
        resume = self._get_resume(job.selected_resume)
        resume_text = resume.extracted_text if resume and resume.extracted_text else "Resume text unavailable."
        
        prompt = f"""
        You are an expert copywriter and career coach helping a candidate apply for a job.
        
        Write a professional, concise, and highly tailored email application for this job.
        
        Candidate Name: {self.candidate.profile_data.get('full_name', '')}
        Candidate Email: {self.candidate.profile_data.get('email', '')}
        Candidate Skills: {self.candidate.profile_data.get('skills_summary', '')}
        Candidate Resume Content (Raw Extracted Text):
        {resume_text}
        
        Job Title: {job.title}
        Company: {job.company_name}
        Job Description:
        {job.description}
        
        Instructions:
        1. The email should be addressed to the Hiring Manager or Recruiting Team.
        2. Highlight 1-2 specific achievements or skills from the resume that directly match the job description.
        3. Keep it under 250 words. Be respectful, confident, and professional.
        4. Include a clear subject line (e.g., "Application for [Title] - [Candidate Name]").
        
        Return your result as JSON.
        """
        
        try:
            result: EmailDraftResult = self.llm.generate_structured_response(prompt, EmailDraftResult)
            
            # Create Application record
            application = Application(
                job_id=job.id,
                resume_id=resume.id if resume else None,
                status="DRAFT_CREATED",
                draft_subject=result.subject,
                draft_body=result.body
            )
            self.db.add(application)
            
            # Update job status
            job.status = "DRAFT_CREATED"
            
            self.db.commit()
            logger.info(f"Generated application draft for {job.title} at {job.company_name}.")
            return application
            
        except Exception as e:
            logger.error(f"Failed to generate draft for job {job.id}: {e}")
            return None
