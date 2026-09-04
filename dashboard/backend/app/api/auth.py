import os
import secrets
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

strict_security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)

def is_demo_mode_active() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

def require_dashboard_auth(credentials: HTTPAuthorizationCredentials = Depends(strict_security)) -> str:
    expected_token = os.getenv("DASHBOARD_API_TOKEN")
    
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="DASHBOARD_API_TOKEN is not configured in the environment."
        )
        
    if not secrets.compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token."
        )
    
    return credentials.credentials

def allow_public_or_admin_auth(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)) -> dict:
    expected_token = os.getenv("DASHBOARD_API_TOKEN")
    
    # Check if a valid admin token was provided
    if credentials and credentials.credentials and expected_token:
        if secrets.compare_digest(credentials.credentials, expected_token):
            return {"is_admin": True}
    
    # If no valid admin token, check if DEMO_MODE allows public recruiter access
    if is_demo_mode_active():
        return {"is_admin": False}
    
    # Otherwise, reject unauthenticated access
    raise HTTPException(
        status_code=401,
        detail="Authentication token required. Set DEMO_MODE=true for public recruiter view."
    )

