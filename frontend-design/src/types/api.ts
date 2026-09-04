// Raw Backend API Response Types (snake_case)
export interface RawPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RawOverviewResponse {
  jobs_discovered: number | null;
  companies_scanned: number | null;
  jobs_matched: number | null;
  jobs_rejected: number | null;
  applications_generated: number | null;
  duplicate_jobs_removed: number | null;
  llm_calls: number | null;
  llm_successes: number | null;
  llm_failures: number | null;
  rate_limit_retries: number | null;
  recruiter_emails_verified: number | null;
  recruiter_emails_not_found: number | null;
  last_run_status: str | null;
  last_run_started_at: string | null;
  last_successful_run: string | null;
  last_run_duration_seconds: number | null;
}

export interface RawJobResponse {
  id: number;
  company_name: string;
  title: string;
  status: string | null;
  match_confidence: number | null;
  selected_resume: string | null;
  url: string;
  source: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface RawApplicationResponse {
  id: number;
  job_id: number;
  company_name: string | null;
  job_title: string | null;
  status: string | null;
  resume: string | null;
  recruiter_email_status: string | null;
  recruiter_email: string | null;
  recruiter_email_source: string | null;
  gmail_draft_created: boolean;
  created_at: string | null;
}

export interface RawRunResponse {
  run_uuid: string | null;
  trigger_type: string | null;
  status: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  agent_version: string | null;
  jobs_discovered: number | null;
  jobs_after_prefilter: number | null;
  jobs_evaluated: number | null;
  jobs_matched: number | null;
  applications_generated: number | null;
  drafts_created: number | null;
  gmail_drafts_created: number | null;
  recruiter_emails_verified: number | null;
  recruiter_emails_not_found: number | null;
  llm_calls: number | null;
  llm_successes: number | null;
  llm_failures: number | null;
  rate_limit_retries: number | null;
  failure_summary: string | null;
}

export interface RawSystemStatusResponse {
  api_status: string;
  database_status: string;
  agent_last_run: string | null;
  agent_last_success: string | null;
  agent_version: string | null;
  companies_configured: number | null;
  database_jobs: number | null;
  database_applications: number | null;
}


// Frontend Types (camelCase)
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DashboardOverview {
  jobsDiscovered: number | null;
  companiesScanned: number | null;
  jobsMatched: number | null;
  jobsRejected: number | null;
  applicationsGenerated: number | null;
  duplicateJobsRemoved: number | null;
  llmCalls: number | null;
  llmSuccesses: number | null;
  llmFailures: number | null;
  rateLimitRetries: number | null;
  recruiterEmailsVerified: number | null;
  recruiterEmailsNotFound: number | null;
  lastRunStatus: string | null;
  lastRunStartedAt: string | null;
  lastSuccessfulRun: string | null;
  lastRunDurationSeconds: number | null;
}

export interface Job {
  id: number;
  companyName: string;
  title: string;
  status: string | null;
  matchConfidence: number | null;
  selectedResume: string | null;
  url: string;
  source: string;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface Application {
  id: number;
  jobId: number;
  companyName: string | null;
  jobTitle: string | null;
  status: string | null;
  resume: string | null;
  recruiterEmailStatus: string | null;
  recruiterEmail: string | null;
  recruiterEmailSource: string | null;
  gmailDraftCreated: boolean;
  createdAt: string | null;
}

export interface AgentRun {
  runUuid: string | null;
  triggerType: string | null;
  status: string | null;
  startedAt: string | null;
  completedAt: string | null;
  durationSeconds: number | null;
  agentVersion: string | null;
  jobsDiscovered: number | null;
  jobsAfterPrefilter: number | null;
  jobsEvaluated: number | null;
  jobsMatched: number | null;
  applicationsGenerated: number | null;
  draftsCreated: number | null;
  gmailDraftsCreated: number | null;
  recruiterEmailsVerified: number | null;
  recruiterEmailsNotFound: number | null;
  llmCalls: number | null;
  llmSuccesses: number | null;
  llmFailures: number | null;
  rateLimitRetries: number | null;
  failureSummary: string | null;
}

export interface CompanyDashboard {
  id: number;
  name: string;
  ats: string;
  jobsFound: number;
  matchingJobs: number;
  lastScan: string | null;
  scanStatus: string;
  monitoringStatus: string;
}

export interface CompaniesResponse extends PaginatedResponse<CompanyDashboard> {}

// ------------------------------------------------------------------
// ANALYTICS
// ------------------------------------------------------------------

export interface AnalyticsTimelineItem {
  date: string;
  discovered: number;
  matched: number;
  applied: number;
}

export interface AnalyticsFunnelItem {
  stage: string;
  count: number;
  pct: number;
}

export interface AnalyticsCompany {
  name: string;
  ats: string;
  jobsFound: number;
  matchingJobs: number;
  applications: number;
}

export interface AnalyticsResumePerformance {
  name: string;
  selected: number;
}

export interface AnalyticsResponse {
  timeline: AnalyticsTimelineItem[];
  funnel: AnalyticsFunnelItem[];
  topCompanies: AnalyticsCompany[];
  resumePerformance: AnalyticsResumePerformance[];
}

export interface SystemHealth {
  apiStatus: string;
  databaseStatus: string;
  agentLastRun: string | null;
  agentLastSuccess: string | null;
  agentVersion: string | null;
  companiesConfigured: number | null;
  databaseJobs: number | null;
  databaseApplications: number | null;
}
