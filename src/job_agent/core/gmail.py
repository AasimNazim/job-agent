import os
import base64
import logging
from typing import List, Optional
from email.message import EmailMessage
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from ..models.application import Application
from ..models.candidate import Resume
from ..models.job import Job
from .recruiter_email import RecruiterEmailDiscovery

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

class GmailService:
    """
    Handles creating drafts in Gmail using the Google Workspace API.
    """
    def __init__(self, db: Session, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.db = db
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()
        self.service = build('gmail', 'v1', credentials=self.creds) if self.creds else None
        
    def _authenticate(self) -> Optional[Credentials]:
        """Authenticates with the Google API."""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Could not refresh token: {e}")
                    creds = None
                    
            if not creds:
                if not os.path.exists(self.credentials_path):
                    logger.warning(f"Gmail credentials not found at {self.credentials_path}. Gmail features disabled.")
                    return None
                    
                logger.info("Initiating Google OAuth flow. Please check your browser.")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                # Typically, you run local server for OAuth callback
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                
        return creds

    def create_draft(self, application: Application) -> bool:
        """
        Creates a Gmail draft for a specific application.
        Attaches the associated PDF resume.
        """
        if not self.service:
            logger.error("Gmail service is not authenticated.")
            return False
            
        job = self.db.query(Job).filter_by(id=application.job_id).first()
        resume = self.db.query(Resume).filter_by(id=application.resume_id).first() if application.resume_id else None
        
        if not job or not application.draft_subject or not application.draft_body:
            logger.error("Invalid application data for draft creation.")
            return False

        message = EmailMessage()
        message.set_content(application.draft_body)
        
        if RecruiterEmailDiscovery.is_verified_email(
            application.recruiter_email,
            application.recruiter_email_status,
            application.recruiter_email_source,
        ):
            message['To'] = application.recruiter_email
        else:
            logger.info("[EMAIL] Gmail draft created for manual recipient: %s", job.title)
        message['Subject'] = application.draft_subject
        
        # Attach the PDF resume if available
        if resume and resume.filename and os.path.exists(resume.filename):
            try:
                with open(resume.filename, 'rb') as fp:
                    pdf_data = fp.read()
                    
                message.add_attachment(
                    pdf_data, 
                    maintype='application', 
                    subtype='pdf', 
                    filename=os.path.basename(resume.filename)
                )
            except Exception as e:
                logger.warning(f"Could not attach resume {resume.filename}: {e}")
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        
        try:
            draft = self.service.users().drafts().create(userId="me", body=create_message).execute()
            logger.info(f"Draft created! Draft ID: {draft['id']}")
            
            application.gmail_draft_id = draft['id']
            application.status = "DRAFT_SAVED"
            self.db.commit()
            
            return True
        except HttpError as error:
            logger.error(f"An error occurred calling Gmail API: {error}")
            return False

    def process_pending_drafts(self) -> int:
        """
        Finds all applications that have been generated but not yet drafted in Gmail,
        and creates drafts for them.
        """
        applications = self.db.query(Application).filter_by(status="DRAFT_CREATED").all()
        count = 0
        
        for app in applications:
            if self.create_draft(app):
                count += 1
                
        return count

    def send_notification_email(self, application: Application, candidate_email: str) -> bool:
        """
        Sends an email notification to the candidate's email about the newly drafted application.
        """
        if not self.service:
            logger.error("Gmail service is not authenticated.")
            return False
            
        job = self.db.query(Job).filter_by(id=application.job_id).first()
        if not job:
            return False

        message = EmailMessage()
        
        body = f"""Great news! We found a high-quality job match and created a draft application.
        
Company: {job.company_name}
Position: {job.title}
Location: {job.location or 'Not specified'}
Match Score: {job.match_confidence if job.match_confidence else 'N/A'}
Selected Resume: {job.selected_resume or 'None'}
Recruiter Status: Not Found
Link: {job.url}
"""
        message.set_content(body)
        message['To'] = candidate_email
        message['Subject'] = f"New Job Match: {job.title} at {job.company_name}"
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        try:
            self.service.users().messages().send(userId="me", body=create_message).execute()
            logger.info(f"Notification email sent for {job.company_name} match!")
            
            application.notification_sent = True
            application.status = "NOTIFIED"
            self.db.commit()
            return True
        except HttpError as error:
            logger.error(f"Failed to send notification email: {error}")
            return False
            
    def process_pending_notifications(self, candidate_email: str) -> int:
        """
        Finds all successfully drafted applications that haven't triggered a notification yet.
        """
        if not candidate_email:
            logger.warning("No candidate email provided for notifications.")
            return 0
            
        applications = self.db.query(Application).filter_by(status="DRAFT_SAVED", notification_sent=False).all()
        count = 0
        
        for app in applications:
            if self.send_notification_email(app, candidate_email):
                count += 1
                
        return count

