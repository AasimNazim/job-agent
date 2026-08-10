import logging
import pymupdf as fitz  # PyMuPDF
import re
from pathlib import Path
from sqlalchemy.orm import Session
from ..models.candidate import Resume

logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Parses PDF resumes using PyMuPDF to extract raw text and clean it for the LLM.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extracts raw text from a PDF file using PyMuPDF.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Resume file not found: {file_path}")
            return ""
            
        text = ""
        try:
            with fitz.open(path) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return ""
            
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """
        Cleans the extracted text by removing excessive whitespace and unreadable characters.
        """
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def process_all_resumes(self) -> int:
        """
        Finds all resumes in the database, parses their PDFs, and stores the text.
        Returns the number of successfully processed resumes.
        """
        resumes = self.db.query(Resume).all()
        processed_count = 0
        
        for resume in resumes:
            if not resume.filename:
                continue
                
            logger.info(f"Extracting text from {resume.filename}...")
            extracted_text = self.extract_text_from_pdf(resume.filename)
            
            if extracted_text:
                resume.extracted_text = extracted_text
                processed_count += 1
            else:
                logger.warning(f"Failed to extract text from {resume.filename}")
                
        self.db.commit()
        return processed_count
