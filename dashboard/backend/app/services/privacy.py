import os
import re

def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

def is_mask_sensitive_enabled() -> bool:
    return os.getenv("DEMO_MASK_SENSITIVE_DATA", "false").lower() in ("true", "1", "yes") or is_demo_mode()

def sanitize_email(email: str | None) -> str | None:
    if not email:
        return None
    if not is_mask_sensitive_enabled():
        return email
    # Completely exclude/strip private emails in public mode
    return None

def sanitize_resume_name(filename: str | None) -> str | None:
    if not filename:
        return None
    if not is_mask_sensitive_enabled():
        return filename
    # Remove personal names from resume filenames in public demo mode
    # e.g., "John_Doe_Resume.pdf" -> "Resume.pdf"
    clean_name = re.sub(r'^[A-Z][a-z]+_[A-Z][a-z]+_', '', filename)
    if not clean_name.lower().endswith('.pdf'):
        return "Resume.pdf"
    return clean_name

def sanitize_job_dict(job_dict: dict, is_admin: bool = False) -> dict:
    if is_admin or not is_mask_sensitive_enabled():
        return job_dict
    
    # Strip/sanitize sensitive fields for public recruiter view
    sanitized = dict(job_dict)
    if "selected_resume" in sanitized and sanitized["selected_resume"]:
        sanitized["selected_resume"] = sanitize_resume_name(sanitized["selected_resume"])
    return sanitized
