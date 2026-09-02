from datetime import datetime, timezone, timedelta

from sqlalchemy import func, inspect, text, case
from types import SimpleNamespace
from sqlalchemy.orm import Session

from job_agent.models.application import Application
from job_agent.models.company import Company
from job_agent.models.job import Job
from job_agent.models.candidate import Resume
from job_agent.models.notification import JobRun


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _parse_dt(val) -> datetime | None:
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except ValueError:
                return None
        return val

    @staticmethod
    def _duration_seconds(run: JobRun | None) -> float | None:
        if not run or not run.started_at or not run.completed_at:
            return None
        started = DashboardService._parse_dt(run.started_at)
        completed = DashboardService._parse_dt(run.completed_at)
        if not started or not completed:
            return None
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)
        return (completed - started).total_seconds()

    def _run_columns(self) -> set[str]:
        return {column["name"] for column in inspect(self.db.bind).get_columns("job_runs")}

    def _run_query(self):
        columns = self._run_columns()
        names = [
            "id", "run_uuid", "trigger_type", "status", "started_at", "completed_at",
            "finished_at", "agent_version", "companies_scanned", "jobs_discovered",
            "new_jobs", "duplicate_jobs", "jobs_prefiltered", "jobs_evaluated",
            "jobs_matched", "jobs_ignored", "applications_generated", "drafts_created",
            "gmail_drafts_created", "recruiter_emails_verified", "recruiter_emails_not_found",
            "llm_calls", "llm_successes", "llm_failures", "rate_limit_retries",
            "error_count", "failure_summary",
        ]
        expressions = [name if name in columns else f"NULL AS {name}" for name in names]
        return text(f"SELECT {', '.join(expressions)} FROM job_runs")

    def _run_objects(self) -> list[SimpleNamespace]:
        rows = self.db.execute(self._run_query()).mappings().all()
        objects = []
        for row in rows:
            values = dict(row)
            values["started_at"] = self._parse_dt(values.get("started_at"))
            values["completed_at"] = self._parse_dt(values.get("completed_at")) or self._parse_dt(values.get("finished_at"))
            values["finished_at"] = self._parse_dt(values.get("finished_at"))
            objects.append(SimpleNamespace(**values))
        return objects

    def latest_run(self) -> JobRun | None:
        runs = sorted(self._run_objects(), key=lambda run: (run.started_at or datetime.min, run.id or 0), reverse=True)
        return runs[0] if runs else None

    def overview(self) -> dict:
        latest = self.latest_run()
        successful = max(
            (run for run in self._run_objects() if run.status == "SUCCEEDED"),
            key=lambda run: (run.completed_at or datetime.min, run.id or 0),
            default=None,
        )
        current_jobs = self.db.query(func.count(Job.id)).scalar()
        current_matched = self.db.query(func.count(Job.id)).filter(Job.status == "MATCHED").scalar()
        current_rejected = self.db.query(func.count(Job.id)).filter(Job.status == "IGNORED").scalar()
        current_applications = self.db.query(func.count(Application.id)).scalar()

        if latest is None:
            run_metrics = {field: None for field in (
                "jobs_discovered", "companies_scanned", "duplicate_jobs_removed",
                "llm_calls", "llm_successes", "llm_failures", "rate_limit_retries",
                "recruiter_emails_verified", "recruiter_emails_not_found",
            )}
            last_status = last_started = last_duration = None
        else:
            run_metrics = {
                "jobs_discovered": latest.jobs_discovered,
                "companies_scanned": latest.companies_scanned,
                "duplicate_jobs_removed": latest.duplicate_jobs,
                "llm_calls": latest.llm_calls,
                "llm_successes": latest.llm_successes,
                "llm_failures": latest.llm_failures,
                "rate_limit_retries": latest.rate_limit_retries,
                "recruiter_emails_verified": latest.recruiter_emails_verified,
                "recruiter_emails_not_found": latest.recruiter_emails_not_found,
            }
            last_status = latest.status
            last_started = latest.started_at
            last_duration = self._duration_seconds(latest)

        return {
            **run_metrics,
            "jobs_matched": current_matched,
            "jobs_rejected": current_rejected,
            "applications_generated": current_applications,
            "last_run_status": last_status,
            "last_run_started_at": last_started,
            "last_successful_run": successful.completed_at if successful else None,
            "last_run_duration_seconds": last_duration,
        }

    def companies(self) -> tuple[list[dict], int]:
        company_stats = self.db.query(
            Job.company_name,
            func.count(Job.id).label("total_jobs"),
            func.sum(case((Job.status.in_(["MATCHED", "DRAFT_CREATED"]), 1), else_=0)).label("matching_jobs"),
            func.max(Job.last_seen_at).label("last_scan")
        ).group_by(Job.company_name).all()
        
        stat_map = {stat.company_name: stat for stat in company_stats}
        companies = self.db.query(Company).all()
        total = len(companies)
        
        results = []
        for c in companies:
            stats = stat_map.get(c.name)
            jobs_found = stats.total_jobs if stats else 0
            matching_jobs = stats.matching_jobs if stats else 0
            last_scan = stats.last_scan if stats else None
            
            scan_status = "Active" if c.enabled else "Disabled"
            monitoring_status = "Enabled" if c.enabled else "Disabled"
            
            results.append({
                "id": c.id,
                "name": c.name,
                "ats": c.platform,
                "jobs_found": jobs_found,
                "matching_jobs": matching_jobs,
                "last_scan": last_scan,
                "scan_status": scan_status,
                "monitoring_status": monitoring_status
            })
            
        return results, total

    def analytics(self, date_range: str) -> dict:
        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(date_range, 7)
        range_start = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 1. Timeline
        timeline_query = self.db.query(
            func.date(JobRun.started_at).label("date"),
            func.sum(JobRun.jobs_discovered).label("discovered"),
            func.sum(JobRun.new_jobs).label("matched"),
            func.sum(JobRun.drafts_created).label("applied")
        ).filter(JobRun.started_at >= range_start).group_by(func.date(JobRun.started_at)).all()
        
        timeline_dict = {row.date: row for row in timeline_query if row.date}
        timeline = []
        for i in range(days + 1):
            d = (range_start + timedelta(days=i)).strftime("%Y-%m-%d")
            row = timeline_dict.get(d)
            if row:
                timeline.append({
                    "date": d[-5:], # e.g. "08-20"
                    "discovered": row.discovered or 0,
                    "matched": row.matched or 0,
                    "applied": row.applied or 0
                })
            else:
                timeline.append({
                    "date": d[-5:],
                    "discovered": 0,
                    "matched": 0,
                    "applied": 0
                })
        
        # 2. Funnel
        funnel_stats = self.db.query(
            func.sum(JobRun.jobs_discovered).label("discovered"),
            func.sum(JobRun.new_jobs).label("prefiltered"),
            func.sum(JobRun.new_jobs).label("evaluated"),
            func.sum(JobRun.new_jobs).label("matched"),
            func.sum(JobRun.drafts_created).label("draft_generated"),
            func.sum(JobRun.drafts_created).label("gmail_draft")
        ).filter(JobRun.started_at >= range_start).first()
        
        disc = funnel_stats.discovered or 0
        def pct(count): return int(round(count / disc * 100)) if disc > 0 else 0
        
        funnel = [
            {"stage": "Discovered", "count": disc, "pct": 100 if disc > 0 else 0},
            {"stage": "Pre-filtered", "count": funnel_stats.prefiltered or 0, "pct": pct(funnel_stats.prefiltered or 0)},
            {"stage": "Evaluated", "count": funnel_stats.evaluated or 0, "pct": pct(funnel_stats.evaluated or 0)},
            {"stage": "Matched", "count": funnel_stats.matched or 0, "pct": pct(funnel_stats.matched or 0)},
            {"stage": "Draft Generated", "count": funnel_stats.draft_generated or 0, "pct": pct(funnel_stats.draft_generated or 0)},
            {"stage": "Gmail Draft", "count": funnel_stats.gmail_draft or 0, "pct": pct(funnel_stats.gmail_draft or 0)},
        ]
        
        # 3. Top Companies
        # Note: Match date assumes matches happened in the same run as discovery (Job.first_seen_at) 
        # since Job does not store matched_at.
        company_stats = self.db.query(
            Job.company_name,
            func.count(Job.id).label("total_jobs"),
            func.sum(case((Job.status.in_(["MATCHED", "DRAFT_CREATED"]), 1), else_=0)).label("matching_jobs")
        ).filter(Job.first_seen_at >= range_start).group_by(Job.company_name).all()
        
        app_stats = self.db.query(
            Job.company_name,
            func.count(Application.id).label("apps")
        ).join(Job, Application.job_id == Job.id).filter(Application.created_at >= range_start).group_by(Job.company_name).all()
        app_map = {row.company_name: row.apps for row in app_stats}
        
        companies = self.db.query(Company.name, Company.platform).all()
        ats_map = {c.name: c.platform for c in companies}
        
        top_companies = []
        for stat in company_stats:
            cname = stat.company_name
            top_companies.append({
                "name": cname,
                "ats": ats_map.get(cname, "Unknown").capitalize(),
                "jobs_found": stat.total_jobs or 0,
                "matching_jobs": stat.matching_jobs or 0,
                "applications": app_map.get(cname, 0)
            })
            
        top_companies.sort(key=lambda x: (x["matching_jobs"], x["jobs_found"]), reverse=True)
        top_companies = top_companies[:10]
        
        # 4. Resume Performance
        resume_stats = self.db.query(
            Resume.filename.label("name"),
            func.count(Application.id).label("selected")
        ).join(Application, Resume.id == Application.resume_id).filter(Application.created_at >= range_start).group_by(Resume.id).all()
        
        resume_performance = [
            {"name": r.name, "selected": r.selected or 0} for r in resume_stats
        ]
        resume_performance.sort(key=lambda x: x["selected"], reverse=True)
        
        return {
            "timeline": timeline,
            "funnel": funnel,
            "top_companies": top_companies,
            "resume_performance": resume_performance
        }

    def runs(self, page: int, page_size: int) -> tuple[list[JobRun], int]:
        items = sorted(self._run_objects(), key=lambda run: (run.started_at or datetime.min, run.id or 0), reverse=True)
        total = len(items)
        items = items[(page - 1) * page_size:page * page_size]
        return items, total

    def run_by_uuid(self, run_uuid: str) -> JobRun | None:
        return next((run for run in self._run_objects() if run.run_uuid == run_uuid), None)

    def jobs(self, page: int, page_size: int, status: str | None, company: str | None, min_score: float | None) -> tuple[list[Job], int]:
        query = self.db.query(Job)
        if status:
            query = query.filter(Job.status == status)
        if company:
            query = query.filter(Job.company_name == company)
        if min_score is not None:
            query = query.filter(Job.match_confidence >= min_score)
        query = query.order_by(Job.first_seen_at.desc(), Job.id.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def applications(self, page: int, page_size: int) -> tuple[list[tuple[Application, Job | None, Resume | None]], int]:
        query = self.db.query(Application, Job, Resume).outerjoin(Job, Application.job_id == Job.id).outerjoin(Resume, Application.resume_id == Resume.id)
        query = query.order_by(Application.created_at.desc(), Application.id.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def system_status(self) -> dict:
        latest = self.latest_run()
        successful = max(
            (run for run in self._run_objects() if run.status == "SUCCEEDED"),
            key=lambda run: (run.completed_at or datetime.min, run.id or 0),
            default=None,
        )
        return {
            "api_status": "healthy",
            "database_status": "connected",
            "agent_last_run": latest.started_at if latest else None,
            "agent_last_success": successful.completed_at if successful else None,
            "agent_version": latest.agent_version if latest else None,
            "companies_configured": self.db.query(func.count(Company.id)).scalar(),
            "database_jobs": self.db.query(func.count(Job.id)).scalar(),
            "database_applications": self.db.query(func.count(Application.id)).scalar(),
        }
