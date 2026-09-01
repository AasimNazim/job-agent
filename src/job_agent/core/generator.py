import logging
import re
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .llm import LLMService
from ..models.job import Job
from ..models.candidate import CandidateProfile, Resume
from ..models.application import Application
from ..models.company import Company
from .recruiter_email import RecruiterEmailDiscovery
from .evaluator import JobEvaluator

logger = logging.getLogger(__name__)

class EmailDraftResult(BaseModel):
    subject: str = Field(description="A professional email subject line for the job application.")
    body: str = Field(description="The professional, tailored email body text. It should read naturally, avoid sounding overly robotic, and match the candidate's skills to the job description.")

class ApplicationGenerator:
    """
    Uses the LLM to generate highly tailored application drafts.
    """
    def __init__(self, db: Session, llm_service: LLMService, recruiter_email_service: Optional[RecruiterEmailDiscovery] = None):
        self.db = db
        self.llm = llm_service
        self.recruiter_email_service = recruiter_email_service
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

    @staticmethod
    def _word_count(text: str) -> int:
        return len(re.findall(r"\b[\w'-]+\b", text))

    @classmethod
    def _polish_cover_letter(cls, body: str, job: Job, resume: Optional[Resume]) -> str:
        """Keep model output concise and remove obvious resume duplication."""
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body.strip()) if paragraph.strip()]
        job_requests_academics = bool(re.search(r"\b(gpa|cgpa|academic performance|grade point)\b", job.description or "", re.IGNORECASE))
        resume_phrases = set()
        resume_words = re.findall(r"\b[\w'-]+\b", (resume.extracted_text or "").lower()) if resume else []
        for index in range(len(resume_words) - 7):
            resume_phrases.add(" ".join(resume_words[index:index + 8]))

        kept_sentences = []
        seen = set()
        for paragraph in paragraphs:
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
                normalized = re.sub(r"\s+", " ", sentence).strip()
                key = normalized.lower()
                if not normalized or key in seen:
                    continue
                if not job_requests_academics and re.search(r"\b(gpa|cgpa|grade point)\b", key):
                    continue
                sentence_words = re.findall(r"\b[\w'-]+\b", key)
                if len(sentence_words) >= 8 and any(" ".join(sentence_words[index:index + 8]) in resume_phrases for index in range(len(sentence_words) - 7)):
                    continue
                seen.add(key)
                kept_sentences.append(normalized)

        polished = "\n\n".join(kept_sentences)
        if cls._word_count(polished) > 110:
            words = polished.split()[:110]
            polished = " ".join(words).rstrip(" ,;:")
            if polished and polished[-1] not in ".!?":
                polished += "."
        return polished

    def generate_draft(self, job: Job) -> Optional[Application]:
        """
        Generates an application draft for a MATCHED job using the selected resume.
        Saves the application to the database.
        """
        if not self.candidate:
            logger.error("Cannot generate draft: Candidate profile missing.")
            return None
            
        if job.status != "MATCHED":
            logger.error(f"Job {job.id} is not ready for draft generation: status={job.status}.")
            return None

        if not job.selected_resume or not self._get_resume(job.selected_resume):
            selected_resume = JobEvaluator.select_resume_domain(job, self.db.query(Resume).all())
            if not selected_resume:
                logger.error(f"Job {job.id} is not ready for draft generation: no suitable resume found.")
                return None
            job.selected_resume = selected_resume
            self.db.commit()
            logger.info(f"Resolved resume for job {job.id}: {selected_resume}")
            
        resume = self._get_resume(job.selected_resume)
        resume_text_truncated = (resume.extracted_text if resume and resume.extracted_text else "Resume text unavailable.")[:1200]
        job_desc_truncated = (job.description or "")[:1000]
        
        prompt = f"""
        You are a job candidate writing a short, clean, human cover letter email.
        
        Candidate Name: {self.candidate.profile_data.get('full_name', '')}
        Candidate Email: {self.candidate.profile_data.get('email', '')}
        Candidate Skills: {self.candidate.profile_data.get('skills_summary', '')}
        Resume Excerpt:
        {resume_text_truncated}
        
        Job Title: {job.title}
        Company: {job.company_name}
        Job Description Excerpt:
        {job_desc_truncated}
        
        Instructions:
        1. Keep the total email body between 70 and 100 words max.
        2. Write in a clear, natural, direct, and professional human tone.
        3. Do NOT use heavy corporate jargon or robotic buzzwords (avoid words like 'meticulous', 'disciplined approach', 'honed', 'spearheaded', 'synergy', 'cross-functional').
        4. Opening: State application for the {job.title} position at {job.company_name} in 1 simple sentence.
        5. Middle: 2 short sentences linking 1-2 key matching technical skills to the job description.
        6. Closing: 1 brief thank-you sentence expressing interest in discussing the role.
        7. Address 'Dear Hiring Team,'. Return only the letter body in the JSON response; subject is set by system.
        
        Return your result as JSON.
        """
        
        try:
            result: EmailDraftResult = self.llm.generate_structured_response(prompt, EmailDraftResult)

            email_result = None
            if self.recruiter_email_service:
                company = self.db.query(Company).filter_by(name=job.company_name).first()
                email_result = self.recruiter_email_service.discover(job, company.career_url if company else None)

            recruiter_email = email_result.email if email_result and email_result.status == "VERIFIED" else None
            recruiter_status = email_result.status if email_result else "NOT_FOUND"
            recruiter_source = email_result.source_url if email_result else None
            body = self._polish_cover_letter(result.body, job, resume)
            if recruiter_status == "NOT_FOUND":
                body += f"\n\nJob URL: {job.url}\nCompany: {job.company_name}\nJob title: {job.title}\nRecruiter email could not be verified automatically."
            
            # Create Application record
            application = Application(
                job_id=job.id,
                resume_id=resume.id if resume else None,
                status="DRAFT_CREATED",
                draft_subject=f"Application for {job.title} - {job.company_name}",
                draft_body=body,
                recruiter_email=recruiter_email,
                recruiter_email_status=recruiter_status,
                recruiter_email_source=recruiter_source,
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
