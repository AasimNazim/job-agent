import logging
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api import overview, runs, jobs, applications, system, companies, analytics
from app.api.auth import require_dashboard_auth, allow_public_or_admin_auth

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Job Agent Dashboard API", version="1.0.0")

cors_origins = [
    origin.strip()
    for origin in os.getenv("DASHBOARD_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost:80").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Publicly viewable in DEMO_MODE or Admin with token
app.include_router(companies.router, dependencies=[Depends(allow_public_or_admin_auth)])
app.include_router(analytics.router, dependencies=[Depends(allow_public_or_admin_auth)])
app.include_router(overview.router, dependencies=[Depends(allow_public_or_admin_auth)])
app.include_router(jobs.router, dependencies=[Depends(allow_public_or_admin_auth)])

# Restricted Admin-Only Endpoints (Always require valid token)
app.include_router(runs.router, dependencies=[Depends(require_dashboard_auth)])
app.include_router(applications.router, dependencies=[Depends(require_dashboard_auth)])

# System (has internal route protection for /api/dashboard/system, while /health is public)
app.include_router(system.router)
