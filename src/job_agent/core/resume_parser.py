import logging
import os
import re
import urllib.request
from pathlib import Path
import pymupdf as fitz  # PyMuPDF
from sqlalchemy.orm import Session
from ..models.candidate import Resume

logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Parses PDF resumes using PyMuPDF to extract raw text and clean it for the LLM.
    Supports local files, in-memory PDF byte streams, remote Supabase Storage URLs,
    and database-preserved text fallback for serverless/CI runners.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extracts raw text from a PDF byte stream using PyMuPDF.
        """
        if not pdf_bytes:
            return ""
            
        text = ""
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"Error parsing PDF byte stream: {type(e).__name__}")
            return ""
            
        return self._clean_text(text)

    def extract_text_from_url(self, url: str) -> str:
        """
        Downloads a PDF from a remote URL (e.g. Supabase Storage) and extracts text.
        """
        if not url:
            return ""
            
        try:
            headers = {}
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            if supabase_key:
                headers["Authorization"] = f"Bearer {supabase_key}"
                headers["apikey"] = supabase_key
                
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                pdf_bytes = resp.read()
                return self.extract_text_from_bytes(pdf_bytes)
        except Exception as e:
            logger.warning(f"Could not fetch PDF from remote storage: {type(e).__name__}")
            return ""

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extracts raw text from a PDF file using PyMuPDF.
        """
        path = Path(file_path)
        if not path.exists():
            return ""
            
        text = ""
        try:
            with fitz.open(path) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {type(e).__name__}")
            return ""
            
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """
        Cleans the extracted text by removing excessive whitespace and unreadable characters.
        """
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def process_all_resumes(self) -> int:
        """
        Finds all resumes in the database, parses their PDFs (from local disk, remote storage,
        or existing database cache), and updates the extracted text.
        Returns the number of successfully processed resumes.
        """
        resumes = self.db.query(Resume).all()
        processed_count = 0
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_STORAGE_URL")
        
        for resume in resumes:
            if not resume.filename:
                continue
                
            extracted_text = ""
            file_path = Path(resume.filename)
            
            # Tier 1: Local PDF File
            if file_path.exists():
                logger.info(f"Extracting text from local PDF file: {resume.filename}")
                extracted_text = self.extract_text_from_pdf(resume.filename)
            # Tier 2: Remote URL / Supabase Storage
            elif resume.filename.startswith(("http://", "https://")):
                logger.info(f"Fetching PDF from remote URL for domain {resume.domains}...")
                extracted_text = self.extract_text_from_url(resume.filename)
            elif supabase_url:
                object_name = file_path.name
                storage_endpoint = f"{supabase_url.rstrip('/')}/storage/v1/object/authenticated/resumes/{object_name}"
                logger.info(f"Attempting Supabase Storage fetch for {object_name}...")
                extracted_text = self.extract_text_from_url(storage_endpoint)
                
            # Tier 3: Database Preserved Text Cache Fallback
            if not extracted_text and resume.extracted_text and len(resume.extracted_text.strip()) > 0:
                logger.info(f"Preserved existing database text for resume ID {resume.id} ({len(resume.extracted_text)} chars)")
                processed_count += 1
                continue
                
            if extracted_text:
                resume.extracted_text = extracted_text
                processed_count += 1
            else:
                logger.warning(f"Resume text unavailable for ID {resume.id} ({resume.filename})")
                
        self.db.commit()
        return processed_count

