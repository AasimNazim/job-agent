import pytest
import os
from unittest.mock import patch, MagicMock
import pymupdf as fitz # PyMuPDF
from job_agent.core.resume_parser import ResumeParser
from job_agent.models.candidate import Resume

@pytest.fixture
def dummy_pdf_bytes():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 50), "Test Candidate\nSoftware Engineer\nPython, React")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

@pytest.fixture
def dummy_pdf_path(tmp_path, dummy_pdf_bytes):
    pdf_path = tmp_path / "dummy_resume.pdf"
    pdf_path.write_bytes(dummy_pdf_bytes)
    return str(pdf_path)

def test_extract_text(db_session, dummy_pdf_path):
    parser = ResumeParser(db_session)
    text = parser.extract_text_from_pdf(dummy_pdf_path)
    
    assert "Test Candidate" in text
    assert "Software Engineer" in text
    assert "Python, React" in text

def test_extract_text_from_bytes(db_session, dummy_pdf_bytes):
    parser = ResumeParser(db_session)
    text = parser.extract_text_from_bytes(dummy_pdf_bytes)
    
    assert "Test Candidate" in text
    assert "Software Engineer" in text

def test_process_all_resumes_local_file(db_session, dummy_pdf_path):
    resume = Resume(filename=dummy_pdf_path, domains=["test"])
    db_session.add(resume)
    db_session.commit()
    
    parser = ResumeParser(db_session)
    processed = parser.process_all_resumes()
    
    assert processed == 1
    
    db_resume = db_session.query(Resume).filter_by(filename=dummy_pdf_path).first()
    assert db_resume.extracted_text is not None
    assert "Software Engineer" in db_resume.extracted_text

def test_process_all_resumes_db_fallback(db_session):
    # Simulate production DB state on CI runner where PDF file does not exist on disk
    resume = Resume(
        filename="Resume/NonExistentFolder/NonExistent_Resume.pdf",
        domains=["software_engineering"],
        extracted_text="Pre-extracted Candidate Resume Text for Production Evaluation"
    )
    db_session.add(resume)
    db_session.commit()

    parser = ResumeParser(db_session)
    processed = parser.process_all_resumes()

    assert processed == 1
    db_resume = db_session.query(Resume).filter_by(filename=resume.filename).first()
    assert db_resume.extracted_text == "Pre-extracted Candidate Resume Text for Production Evaluation"

@patch("urllib.request.urlopen")
def test_process_all_resumes_remote_url(mock_urlopen, db_session, dummy_pdf_bytes):
    mock_response = MagicMock()
    mock_response.read.return_value = dummy_pdf_bytes
    mock_urlopen.return_value.__enter__.return_value = mock_response

    resume = Resume(filename="https://example.com/resumes/remote_resume.pdf", domains=["data_science"])
    db_session.add(resume)
    db_session.commit()

    parser = ResumeParser(db_session)
    processed = parser.process_all_resumes()

    assert processed == 1
    db_resume = db_session.query(Resume).filter_by(filename=resume.filename).first()
    assert db_resume.extracted_text is not None
    assert "Test Candidate" in db_resume.extracted_text

