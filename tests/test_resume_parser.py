import pytest
import os
import pymupdf as fitz # PyMuPDF
from job_agent.core.resume_parser import ResumeParser
from job_agent.models.candidate import Resume

@pytest.fixture
def dummy_pdf_path(tmp_path):
    pdf_path = tmp_path / "dummy_resume.pdf"
    
    # Create a simple PDF using fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Test Candidate\nSoftware Engineer\nPython, React")
    doc.save(str(pdf_path))
    doc.close()
    
    return str(pdf_path)

def test_extract_text(db_session, dummy_pdf_path):
    parser = ResumeParser(db_session)
    text = parser.extract_text_from_pdf(dummy_pdf_path)
    
    assert "Test Candidate" in text
    assert "Software Engineer" in text
    assert "Python, React" in text

def test_process_all_resumes(db_session, dummy_pdf_path):
    # Insert a dummy resume into the DB
    resume = Resume(filename=dummy_pdf_path, domains=["test"])
    db_session.add(resume)
    db_session.commit()
    
    parser = ResumeParser(db_session)
    processed = parser.process_all_resumes()
    
    assert processed == 1
    
    db_resume = db_session.query(Resume).filter_by(filename=dummy_pdf_path).first()
    assert db_resume.extracted_text is not None
    assert "Software Engineer" in db_resume.extracted_text
