# JobPilot AI (v1.0.0)
> Autonomous AI Job Discovery & Application Drafting Agent with Real-Time Dashboard & Analytics

JobPilot AI is a production-grade, autonomous cloud-based agent designed for personalized entry-level job discovery, AI evaluation, customized application generation, recruiter email verification, and automated Gmail draft creation. It features a high-performance **FastAPI backend** and a modern **React + Vite dashboard** with full pipeline visibility, analytics, and security controls.

---

## 🌟 Key Features

### 🤖 Autonomous Agent Pipeline
* **Multi-ATS Scraping Engine:** Supports native adapters for **Greenhouse**, **Lever**, **Ashby**, **Workable**, **JazzHR**, and **HireStream**, scanning 20+ top tech companies.
* **Smart Pre-Filtering:** Filters out non-entry-level, senior, or irrelevant roles using title and keyword normalization prior to AI evaluation.
* **AI Job Evaluation:** Powered by **Google Gemini LLM** to grade job descriptions against candidate profiles, extracting key skills and fit scores. Built-in retry handling for 503 capacity spikes and 429 rate limits.
* **Resume Matching & Customization:** Dynamically selects and tailors candidate resume profiles (PDF parsing & structured matching) for each job match.
* **Canonical Deduplication:** Prevents duplicate applications and ghost listings using SHA-256 content hashes and URL canonicalization.
* **Recruiter Email Discovery:** Discovers and verifies hiring manager / recruiter emails using Hunter.io and Snov.io API integrations.
* **Automated Gmail Drafts:** Generates customized application emails and recruiter outreach directly inside your Gmail account as ready-to-send drafts via OAuth2 / Service API.

### 📊 SaaS Dashboard & Analytics
* **Real-Time KPI Tracking:** Total jobs discovered, pre-filtered, evaluated, matched, application drafts generated, and recruiter emails verified.
* **Application Conversion Funnel:** Interactive visual funnel tracking conversion from raw discovery to final draft creation.
* **Run History & Detail View:** Deep-dive into historical agent executions (Scheduled & Manual), including LLM call logs, duration, status badges, and failure summaries.
* **Company ATS Monitor:** Real-time health and scan metrics for all monitored company job boards.
* **Role-Based Access Control:** Dual-mode frontend interface separating public recruiter demo views from token-authenticated admin control.

---

## 🏗️ Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Monitored Company ATS   │
                          │ Greenhouse/Lever/Ashby/etc│
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌──────────────────┐      ┌───────────────────────────┐      ┌──────────────────┐
│  FastAPI Backend │ ◄─── │   Autonomous Job Agent    │ ───► │  Google Gemini   │
│ Dashboard REST   │      │ Discovery -> Eval -> Draft│      │   LLM Service    │
└────────┬─────────┘      └─────────────┬─────────────┘      └──────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐      ┌───────────────────────────┐      ┌──────────────────┐
│ SQLite / Postgres│      │  Recruiter Email & Gmail  │ ───► │   Gmail Drafts   │
│  Database Layer  │      │   Hunter.io / Gmail API   │      │    (Ready-to-Send)│
└────────┬─────────┘      └───────────────────────────┘      └──────────────────┘
         │
         ▼
┌──────────────────┐
│  React + Vite    │
│ Frontend UI      │
└──────────────────┘
```

---

## 🛠️ Tech Stack

* **Core Agent & Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Pytest, HTTPX, SQLite / PostgreSQL.
* **AI & External APIs:** Google Gemini API, Gmail API, Hunter.io API, Snov.io API.
* **Frontend Dashboard:** React 19, TypeScript, Vite, Tailwind CSS v4, Recharts.
* **DevOps & Containers:** Docker, Docker Compose, GitHub Actions CI/CD.

---

## 📁 Repository Structure

```
job-agent/
├── src/job_agent/                # Core Autonomous Agent Package
│   ├── adapters/                 # ATS Scraper Adapters (Ashby, Greenhouse, Lever, etc.)
│   ├── core/                     # Agent Pipeline (Evaluator, Generator, Deduplicator, Recruiter)
│   ├── database/                 # SQLAlchemy ORM Models & DB Setup
│   ├── utils/                    # URL Normalization, Resume Parser, Utilities
│   └── config.py                 # Pydantic Settings & Environment Specs
├── dashboard/                    # Dashboard Sub-System
│   ├── backend/                  # FastAPI Dashboard Backend
│   │   ├── app/                  # API Routers, Middleware, & Services
│   │   └── tests/                # Dashboard Backend Test Suite
├── frontend-design/              # React + Vite Frontend Dashboard App
│   ├── src/                      # UI Components, Pages (Dashboard, Runs, Jobs, etc.)
│   └── vite.config.ts            # Vite Build & Proxy Configuration
├── tests/                        # Core Agent Test Suite
├── docker-compose.yml            # Docker Container Orchestration
├── pyproject.toml                # Python Package Dependencies
└── README.md                     # Documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm
* Git

### 1. Environment Setup
Copy the example environment configuration file and fill in your API credentials:
```bash
cp .env.example .env
```

Key environment variables:
```env
DATABASE_URL=sqlite:///./job_agent.db
GEMINI_API_KEY=your_gemini_api_key
HUNTER_API_KEY=your_hunter_api_key
GMAIL_CREDENTIALS_FILE=credentials.json
DASHBOARD_API_TOKEN=your_secure_dashboard_token
DEMO_MODE=false
```

### 2. Install Python Dependencies
```bash
pip install -e ".[dev]"
```

### 3. Run the Agent Pipeline
Execute an on-demand job discovery and application drafting run:
```bash
python -m job_agent
```

### 4. Run the Dashboard Backend & Frontend

#### Backend (FastAPI):
```bash
python -m uvicorn dashboard.backend.app.main:app --reload --port 8000
```

#### Frontend (React + Vite):
```bash
cd frontend-design
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Execute the complete test suite (71 tests covering core logic and API endpoints):

```bash
# Set PYTHONPATH to src and run pytest
cmd.exe /c "set PYTHONPATH=src && python -m pytest tests dashboard/backend/tests"
```

Frontend type check & production build:
```bash
cd frontend-design
npm run build
```

---

## 📦 Docker Deployment

Build and spin up the complete stack using Docker Compose:

```bash
docker-compose up --build -d
```

---

## 🔒 Security & Admin Access

* **Public Recruiter View:** Visitors can inspect high-level Overview KPI statistics, Job listings, Company statuses, and Analytics.
* **Admin Access:** Accessing sensitive candidate draft emails, execution logs (`Runs`), or application records requires authenticating with the `DASHBOARD_API_TOKEN`.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
