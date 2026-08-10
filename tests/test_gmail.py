import pytest
import os
from unittest.mock import MagicMock, patch
from job_agent.core.gmail import GmailService
from job_agent.models.application import Application
from job_agent.models.job import Job
from job_agent.models.candidate import Resume

@pytest.fixture
def dummy_pdf_for_gmail(tmp_path):
    pdf = tmp_path / "resume.pdf"
    pdf.write_text("dummy pdf content")
    return str(pdf)

def test_create_draft(db_session, dummy_pdf_for_gmail):
    # Setup Job and Application
    job = Job(
        company_name="TestComp",
        source="test",
        title="Engineer",
        url="http://test.com",
        status="DRAFT_CREATED",
        content_hash="xyz"
    )
    db_session.add(job)
    db_session.commit()
    
    resume = Resume(filename=dummy_pdf_for_gmail, domains=["backend"])
    db_session.add(resume)
    db_session.commit()
    
    application = Application(
        job_id=job.id,
        resume_id=resume.id,
        draft_subject="Test Subject",
        draft_body="Test Body",
        status="DRAFT_CREATED"
    )
    db_session.add(application)
    db_session.commit()
    
    # Mock GmailService Auth and API
    with patch("job_agent.core.gmail.GmailService._authenticate", return_value=MagicMock()):
        with patch("job_agent.core.gmail.build") as mock_build:
            # Setup deep mock chain for: self.service.users().drafts().create().execute()
            mock_service = MagicMock()
            mock_users = MagicMock()
            mock_drafts = MagicMock()
            mock_create = MagicMock()
            
            mock_build.return_value = mock_service
            mock_service.users.return_value = mock_users
            mock_users.drafts.return_value = mock_drafts
            mock_drafts.create.return_value = mock_create
            mock_create.execute.return_value = {'id': 'mock_draft_123'}
            
            gmail_service = GmailService(db_session)
            success = gmail_service.create_draft(application)
            
            assert success is True
            assert application.gmail_draft_id == "mock_draft_123"
            assert application.status == "DRAFT_SAVED"

def test_process_pending_drafts(db_session):
    job = Job(
        company_name="TestComp",
        source="test",
        title="Engineer",
        url="http://test.com",
        status="DRAFT_CREATED",
        content_hash="abc"
    )
    db_session.add(job)
    db_session.commit()
    
    application = Application(
        job_id=job.id,
        draft_subject="Subject",
        draft_body="Body",
        status="DRAFT_CREATED"
    )
    db_session.add(application)
    db_session.commit()
    
    with patch("job_agent.core.gmail.GmailService._authenticate", return_value=MagicMock()):
        with patch("job_agent.core.gmail.build"):
            gmail_service = GmailService(db_session)
            
            # Mock the create_draft method directly to test the loop
            with patch.object(gmail_service, 'create_draft', return_value=True):
                processed = gmail_service.process_pending_drafts()
                assert processed == 1

def test_send_notification_email(db_session):
    job = Job(
        company_name="TestComp",
        source="test",
        title="Engineer",
        url="http://test.com",
        status="DRAFT_SAVED",
        content_hash="abc_notif",
        match_confidence=0.95
    )
    db_session.add(job)
    db_session.commit()
    
    application = Application(
        job_id=job.id,
        draft_subject="Subject",
        draft_body="Body",
        status="DRAFT_SAVED"
    )
    db_session.add(application)
    db_session.commit()
    
    with patch("job_agent.core.gmail.GmailService._authenticate", return_value=MagicMock()):
        with patch("job_agent.core.gmail.build") as mock_build:
            mock_service = MagicMock()
            mock_users = MagicMock()
            mock_messages = MagicMock()
            mock_send = MagicMock()
            
            mock_build.return_value = mock_service
            mock_service.users.return_value = mock_users
            mock_users.messages.return_value = mock_messages
            mock_messages.send.return_value = mock_send
            
            gmail_service = GmailService(db_session)
            success = gmail_service.send_notification_email(application, "test@example.com")
            
            assert success is True
            assert application.notification_sent is True
            assert application.status == "NOTIFIED"

def test_process_pending_notifications(db_session):
    job = Job(
        company_name="TestComp",
        source="test",
        title="Engineer",
        url="http://test.com",
        status="DRAFT_SAVED",
        content_hash="abc_notif_2"
    )
    db_session.add(job)
    db_session.commit()
    
    application = Application(
        job_id=job.id,
        draft_subject="Subject",
        draft_body="Body",
        status="DRAFT_SAVED",
        notification_sent=False
    )
    db_session.add(application)
    db_session.commit()
    
    with patch("job_agent.core.gmail.GmailService._authenticate", return_value=MagicMock()):
        with patch("job_agent.core.gmail.build"):
            gmail_service = GmailService(db_session)
            
            with patch.object(gmail_service, 'send_notification_email', return_value=True):
                processed = gmail_service.process_pending_notifications("test@example.com")
                assert processed == 1
