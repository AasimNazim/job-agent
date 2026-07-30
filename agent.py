import os
import re
import time
import json
import random
import base64
import pandas as pd
from pypdf import PdfReader
from email.message import EmailMessage
from jobspy import scrape_jobs

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
MAX_DRAFTS = 10
PROCESSED_JOBS_FILE = "processed_jobs.csv"
RESUMES_DIR = "Resume"

DOMAINS = {
    "Flutter/Mobile": ["flutter", "dart", "android", "ios", "mobile app"],
    "AI/ML/Data Science": ["machine learning", "ai", "python", "pytorch", "tensorflow", "data science"],
    "Bank/IT Support": ["bank", "networking", "cisco", "it support", "information technology"],
    "Product Management": ["product manager", "agile", "scrum", "figma", "ui/ux", "user experience"],
    "Software Development": ["software development", "backend", "python", "frontend", "web developer"]
}

def get_gmail_service():
    creds = None
    token_env = os.getenv("GMAIL_TOKEN_JSON")
    if token_env:
        try:
            creds_data = json.loads(token_env)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        except Exception as e:
            print(f"Error parsing GMAIL_TOKEN_JSON: {e}")

    if not creds and os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("No token or credentials.json found. Please authenticate locally first.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def parse_and_classify_resumes():
    classified_resumes = {}
    if not os.path.exists(RESUMES_DIR):
        print(f"Directory {RESUMES_DIR} not found.")
        return classified_resumes

    for root, dirs, files in os.walk(RESUMES_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                try:
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text.lower()
                    
                    best_domain = None
                    max_score = 0
                    
                    for domain, keywords in DOMAINS.items():
                        score = sum(text.count(kw) for kw in keywords)
                        if score > max_score:
                            max_score = score
                            best_domain = domain
                            
                    if best_domain:
                        print(f"Classified {file} as {best_domain} (Score: {max_score})")
                        if best_domain not in classified_resumes:
                            classified_resumes[best_domain] = []
                        classified_resumes[best_domain].append(file_path)
                    else:
                        print(f"Could not confidently classify {file}")
                        
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    
    return classified_resumes


def get_processed_jobs():
    if os.path.exists(PROCESSED_JOBS_FILE):
        return pd.read_csv(PROCESSED_JOBS_FILE)["job_url"].tolist()
    return []


def add_processed_job(job_url):
    df = pd.DataFrame([{"job_url": job_url}])
    if not os.path.exists(PROCESSED_JOBS_FILE):
        df.to_csv(PROCESSED_JOBS_FILE, index=False)
    else:
        df.to_csv(PROCESSED_JOBS_FILE, mode='a', header=False, index=False)


def create_draft(service, subject, body, attachment_path, to_email=None):
    try:
        message = EmailMessage()
        message.set_content(body)
        if to_email:
            message['To'] = to_email
        message['Subject'] = subject
        
        with open(attachment_path, 'rb') as f:
            pdf_data = f.read()
        
        message.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(attachment_path))
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'message': {
                'raw': encoded_message
            }
        }
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        return draft
    except Exception as e:
        print(f"Error creating draft: {e}")
        return None

def main():
    service = get_gmail_service()
    if not service:
        return

    print("Parsing resumes...")
    resumes_by_domain = parse_and_classify_resumes()
    if not resumes_by_domain:
        print("No resumes successfully classified. Exiting.")
        return

    processed_urls = set(get_processed_jobs())
    drafts_created = 0

    for domain, resume_paths in resumes_by_domain.items():
        if drafts_created >= MAX_DRAFTS:
            break

        print(f"Scraping jobs for {domain}...")
        search_term = DOMAINS[domain][0] # use the primary keyword as search term
        try:
            scraper_api_key = os.getenv("SCRAPERAPI_KEY")
            proxy_url = f"http://scraperapi:{scraper_api_key}@proxy-server.scraperapi.com:8001" if scraper_api_key else None
            proxies = [proxy_url] if proxy_url else None
            
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor"],
                search_term=search_term,
                location="Karachi",
                results_wanted=10,
                country_linkedin="pk",
                proxies=proxies
            )
            
            if jobs.empty:
                print(f"No jobs found for {domain}")
                continue

            for _, row in jobs.iterrows():
                if drafts_created >= MAX_DRAFTS:
                    break

                job_url = row.get("job_url")
                if pd.isna(job_url) or job_url in processed_urls:
                    continue

                company = row.get("company", "the company")
                title = row.get("title", search_term)
                description = str(row.get("description", ""))
                
                # Extract email if present in the job description
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', description)
                to_email = email_match.group(0) if email_match else None
                
                print(f"Found new match: {title} at {company}")
                if to_email:
                    print(f"Extracted contact email: {to_email}")
                
                subject = f"Application for Internship Opportunity - {title} / {company}"
                body = f"""Dear Hiring Team,

I hope this email finds you well. I came across the {title} opening at {company}. While I realize this may be a full-time posting, I am highly interested in joining {company} and would love to be considered for an internship position in this department.

I have a strong foundation in these technologies and am highly motivated to bring my skills to your team as an intern. Please find my resume attached for more details regarding my technical expertise and academic projects.

I would welcome the opportunity to discuss how I can contribute to {company}'s ongoing success as an intern. 

Thank you for your time and consideration.

Best regards,
"""
                # Use the first matched resume for this domain
                resume_to_attach = resume_paths[0]
                
                draft = create_draft(service, subject, body, resume_to_attach, to_email)
                if draft:
                    print(f"Draft created for {title} at {company}. (Draft ID: {draft['id']})")
                    add_processed_job(job_url)
                    processed_urls.add(job_url)
                    drafts_created += 1
                    
                    if drafts_created < MAX_DRAFTS:
                        delay = random.randint(120, 240)
                        print(f"Sleeping for {delay} seconds to avoid rate limits...")
                        time.sleep(delay)
                        
        except Exception as e:
            print(f"Error scraping or processing jobs for {domain}: {e}")

    print(f"Agent finished. Total drafts created: {drafts_created}")


if __name__ == "__main__":
    main()
