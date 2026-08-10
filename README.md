# Autonomous Personal Entry-Level Job Agent

This project is an autonomous cloud-based personal entry-level job discovery and application-drafting agent.

## Current Phase: Phase 1 (Foundation)

Phase 1 establishes the core repository structure, database layer, configuration layer, and testing framework.

### Setup Instructions

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Copy `.env.example` to `.env` and fill in your variables.
4. Run the application:
   ```bash
   python -m job_agent
   ```
5. Run tests:
   ```bash
   pytest
   ```

### Architecture Overview

The system is built with a clean, extensible architecture in mind, using SQLAlchemy for the database (ready for future PostgreSQL migration) and Pydantic for configuration management.
