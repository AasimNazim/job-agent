Design a production-quality SaaS dashboard UI for an AI-powered autonomous job discovery and application platform.

Product name:
AI Job Agent

Product positioning:
AI-Powered Autonomous Job Discovery & Application Agent

The dashboard is for a user who wants to monitor an autonomous system that discovers jobs, evaluates them against multiple resumes, generates application drafts, finds recruiter emails, and creates Gmail drafts.

IMPORTANT:
This should look like a real modern SaaS product designed by a professional product/UI designer — NOT like a generic AI dashboard.

DESIGN STYLE

Create a clean, premium, modern B2B SaaS interface inspired by products such as Linear, Vercel, Stripe, Ramp, and modern analytics platforms.

Use a professional BLUE + WHITE visual identity.

Primary color:
- Professional deep blue: #2563EB

Supporting colors:
- Dark navy: #0F172A
- Blue: #3B82F6
- Light blue: #EFF6FF
- Background: #F8FAFC
- Card background: #FFFFFF
- Border: #E2E8F0
- Primary text: #0F172A
- Secondary text: #64748B
- Success: #16A34A
- Warning: #F59E0B
- Error: #DC2626

Use colors carefully. The interface should remain mostly white/light with blue used for primary actions, active navigation, charts, and important highlights.

TYPOGRAPHY

Use Inter or a similar modern SaaS font.

Typography hierarchy:
- Large dashboard numbers: bold
- Page headings: 24–30px
- Section headings: 16–18px
- Body text: 14–15px
- Secondary metadata: 12–13px

Use generous spacing and strong visual hierarchy.

LAYOUT

Desktop-first responsive SaaS dashboard.

Left sidebar:
- AI Job Agent logo
- Dashboard
- Jobs
- Applications
- Runs
- Companies
- Analytics
- Settings

Bottom of sidebar:
- User profile
- Account/settings

Top navigation:
- Page title
- Search
- Notifications
- User profile/avatar

MAIN DASHBOARD

Create a high-quality overview dashboard.

Top section:

"Good morning, Asim"
"Here's what your job agent discovered recently."

Include:
- Last successful run
- Run status
- Last run duration
- Jobs scanned

KPI cards:

1. Jobs Discovered
   Example: 357

2. Jobs Matched
   Example: 12

3. Applications Generated
   Example: 8

4. Recruiter Emails Verified
   Example: 5

5. Gmail Drafts Created
   Example: 5

Each card should contain:
- Large number
- Small descriptive label
- Percentage/change indicator where appropriate
- Small visual trend

MAIN ANALYTICS AREA

Create a large "Job Discovery Overview" chart.

Show:
- Jobs discovered over time
- Jobs matched
- Applications generated

Use a clean line/bar chart.

Add a time filter:
7 days / 30 days / 90 days

SECONDARY ANALYTICS

Create cards/charts for:

"Application Funnel"

Discovered
↓
Pre-filtered
↓
Evaluated
↓
Matched
↓
Draft Generated
↓
Gmail Draft

Show conversion percentages between stages.

"Top Companies"

Show companies scanned with:
- Company name
- Jobs found
- Matching jobs
- Applications

"Resume Performance"

Show which resume was selected most often:
- Software Engineering
- Data Science
- Bank IT
- Flutter
- Product Management

RUN MONITORING

Create a "Recent Agent Runs" section.

Each run should show:

Run ID
Date/time
Trigger: Scheduled / Manual
Jobs discovered
Jobs matched
Drafts generated
Recruiter emails verified
Duration
Status

Status badges:
- SUCCESS
- PARTIAL
- FAILED
- RUNNING

Use appropriate professional status colors.

RUN DETAILS PAGE

Create a detailed run page.

Header:
"Run Details"

Show:
- Run ID
- Started
- Completed
- Duration
- Trigger type
- Agent version
- Overall status

Metrics:
- Jobs discovered
- Jobs after pre-filter
- Jobs evaluated
- Gemini calls
- Gemini successes
- Gemini failures
- 429 retries
- Jobs matched
- Drafts generated
- Gmail drafts created
- Recruiter emails verified
- Recruiter emails not found
- Errors

Include an execution timeline showing:

Discovery
→ Deduplication
→ Pre-filter
→ AI Evaluation
→ Resume Selection
→ Draft Generation
→ Recruiter Discovery
→ Gmail Draft

JOB EXPLORER

Create a professional Jobs page.

Table columns:

Company
Job Title
Location
Match Score
Resume
Recruiter Email
Status
Discovered
Actions

Match score should be represented with a clean visual indicator.

Filters:
- Company
- Match score
- Status
- Resume
- Date
- Remote/On-site

Job detail drawer/page should show:
- Job title
- Company
- Location
- Match score
- Selected resume
- Recruiter email
- Email verification status
- Source
- Application status
- "Open Job" button

Do NOT expose sensitive resume text or raw ATS data.

APPLICATIONS PAGE

Create a polished application management page.

Each application should show:

Company
Position
Resume Used
Recruiter Email
Cover Letter Status
Gmail Draft Status
Created At
Action

Actions:
- View
- Open Gmail Draft
- Open Job

Use clear statuses.

COMPANIES PAGE

Show all monitored companies.

Columns:
Company
ATS
Jobs Found
Last Scan
Status
Matching Jobs

Use company logos where appropriate, but keep the interface clean.

SYSTEM / AGENT STATUS

Create a system monitoring page showing:

Agent Status:
RUNNING / IDLE / ERROR

Last successful run

Next scheduled run

Gemini status

Gmail status

Database status

ATS connection status

Show a clean system-health layout with green/yellow/red indicators.

IMPORTANT UX REQUIREMENTS

The dashboard must feel like a real SaaS product.

Avoid:
- Excessive gradients
- Huge AI illustrations
- Robot graphics
- Excessive glowing effects
- Neon colors
- Excessive rounded cards
- Fake AI terminology
- Unnecessary decorative elements

Prefer:
- Clean cards
- Subtle borders
- Small radius
- Strong typography
- Professional tables
- Useful charts
- Clear status badges
- Consistent spacing
- Minimal visual noise
- High information density without feeling crowded

DESIGN SYSTEM

Create reusable Figma components for:

- Sidebar
- Top navigation
- KPI cards
- Charts
- Tables
- Status badges
- Buttons
- Dropdowns
- Search
- Filters
- Modal
- Drawer
- Pagination
- Toast notifications
- Empty states
- Loading states
- Error states

Create variants for:
- Default
- Hover
- Active
- Disabled
- Loading
- Success
- Warning
- Error

RESPONSIVE DESIGN

Design:
1. Desktop dashboard
2. Tablet layout
3. Mobile layout

The mobile version should transform tables into cards and collapse the sidebar into a mobile navigation.

DESIGN GOAL

The final result should look like a dashboard that could realistically be launched as a commercial SaaS product.

It should communicate:
- Reliability
- Automation
- Intelligence
- Professionalism
- Trust
- Productivity

Do not make it look like a student project.

Create the complete Figma design with a consistent design system and reusable components.