# Job Agent Dashboard API

This is the Phase 2 read-only REST API for the AI-Powered Autonomous Job Discovery & Application Agent. It reads the existing `job_agent.db` SQLite database and exposes safe dashboard data for a future Next.js frontend.

## Architecture

```text
GitHub Actions Job Agent -> job_agent.db -> FastAPI Dashboard API -> Next.js Dashboard
```

The dashboard backend does not run the agent, call Gemini, access Gmail, create tables, run migrations, or modify database records.

## Installation

From `dashboard/backend`:

```powershell
python -m pip install -r requirements.txt
```

The repository's existing dependencies may already provide FastAPI, SQLAlchemy, and Uvicorn.

## Run locally

From the repository root:

```powershell
cd dashboard/backend
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at:

- http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The database path is resolved to the repository-root `job_agent.db`, even when Uvicorn is started from `dashboard/backend`.

## Environment variables

- `DASHBOARD_DATABASE_URL`: Optional SQLAlchemy database URL. Defaults to the existing repository SQLite database.
- `DASHBOARD_CORS_ORIGINS`: Comma-separated frontend origins. Defaults to `http://localhost:3000`.

Example:

```powershell
$env:DASHBOARD_CORS_ORIGINS = "http://localhost:3000"
```

## Endpoints

- `GET /health`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/runs?page=1&page_size=20`
- `GET /api/dashboard/runs/{run_uuid}`
- `GET /api/dashboard/jobs?page=1&page_size=25&status=MATCHED&min_score=0.8`
- `GET /api/dashboard/applications?page=1&page_size=25`
- `GET /api/dashboard/system`

Example requests:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard/overview
curl "http://localhost:8000/api/dashboard/jobs?page=1&page_size=25&status=MATCHED"
curl "http://localhost:8000/api/dashboard/runs?page=1&page_size=20"
curl http://localhost:8000/api/dashboard/system
```

All collection endpoints return `items`, `page`, `page_size`, `total`, and `pages`. Page sizes are limited to 100.

## Testing

From the repository root:

```powershell
$env:PYTHONPATH = "dashboard/backend;src"
python -m pytest dashboard/backend/tests -q
```

Dashboard tests use isolated temporary SQLite databases and do not modify production data.

## Security

This API is read-only and does not expose resume files or extracted resume text, application draft bodies, raw job descriptions, raw ATS payloads, OAuth tokens, API keys, credentials, refresh tokens, or database secrets. Gmail draft IDs are represented only as a boolean presence flag.

Recruiter email fields are currently returned because they are part of the requested dashboard application data contract. Authentication and a stricter public/private projection should be added before public deployment.
