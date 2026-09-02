import { useState, useEffect } from "react";
import { jobsApi } from "../services/api/jobsApi";
import type { Job } from "../types/api";
import StatusBadge from "../components/StatusBadge";

function MatchScore({ score }: { score: number | null }) {
  if (score === null || score === undefined) return <span className="text-xs text-[#94A3B8]">—</span>;
  const color = score >= 85 ? "#16A34A" : score >= 70 ? "#2563EB" : "#F59E0B";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-[#F1F5F9] rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-xs font-medium tabular-nums" style={{ color }}>{score}%</span>
    </div>
  );
}

interface JobDrawerProps {
  job: Job;
  onClose: () => void;
}

function JobDrawer({ job, onClose }: JobDrawerProps) {
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/20" onClick={onClose} />
      <div className="w-96 bg-white border-l border-[#E2E8F0] h-full overflow-y-auto shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E8F0]">
          <p className="text-sm font-semibold text-[#0F172A]">Job Details</p>
          <button onClick={onClose} className="p-1 rounded hover:bg-[#F8FAFC] text-[#64748B] transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-5 space-y-5">
          <div>
            <p className="text-base font-semibold text-[#0F172A]">{job.title}</p>
            <p className="text-sm text-[#64748B] mt-1">{job.companyName}</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {[
              { label: "Source", value: job.source },
              { label: "Created At", value: job.createdAt ? new Date(job.createdAt).toLocaleDateString() : "—" },
              { label: "Status", value: <StatusBadge status={job.status || "Unknown"} /> },
            ].map(({ label, value }) => (
              <div key={label} className="bg-[#F8FAFC] rounded p-3 border border-[#E2E8F0]">
                <p className="text-[#94A3B8] mb-1">{label}</p>
                <div className="font-medium text-[#0F172A]">{value}</div>
              </div>
            ))}
          </div>
          <div className="bg-[#F8FAFC] rounded p-3 border border-[#E2E8F0]">
            <p className="text-xs text-[#94A3B8] mb-2">Match Score</p>
            <MatchScore score={job.matchConfidence} />
          </div>
          <div className="bg-[#F8FAFC] rounded p-3 border border-[#E2E8F0]">
            <p className="text-xs text-[#94A3B8] mb-1">Resume Selected</p>
            <p className="text-xs font-medium text-[#0F172A]">{job.selectedResume || "—"}</p>
          </div>
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#2563EB] text-white text-xs font-medium rounded hover:bg-[#1D4ED8] transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Open Job Posting
          </a>
        </div>
      </div>
    </div>
  );
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [filterStatus, setFilterStatus] = useState("All");
  const [filterResume, setFilterResume] = useState("All");

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await jobsApi.getJobs();
      setJobs(res.items);
    } catch (err: any) {
      setError(err.message || "Unable to load jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const statuses = ["All", ...Array.from(new Set(jobs.map((j) => j.status).filter(Boolean) as string[]))];
  const resumes = ["All", ...Array.from(new Set(jobs.map((j) => j.selectedResume).filter(Boolean) as string[]))];

  const filtered = jobs.filter((j) => {
    if (filterStatus !== "All" && j.status !== filterStatus) return false;
    if (filterResume !== "All" && j.selectedResume !== filterResume) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading jobs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchJobs} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-semibold text-[#0F172A]">Jobs</h2>
          <p className="text-xs text-[#64748B] mt-0.5">{filtered.length} jobs found</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs border border-[#E2E8F0] rounded px-2.5 py-1.5 bg-white text-[#0F172A] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
          >
            {statuses.map((s) => <option key={s}>{s}</option>)}
          </select>
          <select
            value={filterResume}
            onChange={(e) => setFilterResume(e.target.value)}
            className="text-xs border border-[#E2E8F0] rounded px-2.5 py-1.5 bg-white text-[#0F172A] focus:outline-none focus:ring-1 focus:ring-[#2563EB]"
          >
            {resumes.map((r) => <option key={r}>{r}</option>)}
          </select>
        </div>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded">
        {filtered.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center">
            <svg className="w-12 h-12 text-[#94A3B8] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p className="text-sm font-medium text-[#0F172A]">No jobs found</p>
            <p className="text-xs text-[#64748B] mt-1">Try adjusting your filters or wait for the next agent run.</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F0]">
                {["Company", "Job Title", "Source", "Match Score", "Resume", "Status", "Discovered", ""].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[#64748B] font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((job) => (
                <tr
                  key={job.id}
                  className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors cursor-pointer"
                  onClick={() => setSelectedJob(job)}
                >
                  <td className="px-4 py-3 font-medium text-[#0F172A]">{job.companyName}</td>
                  <td className="px-4 py-3 text-[#0F172A] max-w-[200px] truncate">{job.title}</td>
                  <td className="px-4 py-3 text-[#64748B]">{job.source}</td>
                  <td className="px-4 py-3"><MatchScore score={job.matchConfidence} /></td>
                  <td className="px-4 py-3 text-[#64748B]">{job.selectedResume || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={job.status || "Unknown"} /></td>
                  <td className="px-4 py-3 text-[#94A3B8]">{job.createdAt ? new Date(job.createdAt).toLocaleDateString() : "—"}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={(e) => { e.stopPropagation(); setSelectedJob(job); }}
                      className="text-[#2563EB] hover:text-[#1D4ED8] font-medium transition-colors"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedJob && <JobDrawer job={selectedJob} onClose={() => setSelectedJob(null)} />}
    </div>
  );
}
