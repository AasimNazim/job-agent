import { useState, useEffect } from "react";
import { applicationsApi } from "../services/api/applicationsApi";
import type { Application } from "../types/api";
import StatusBadge from "../components/StatusBadge";

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await applicationsApi.getApplications();
      setApplications(res.items);
    } catch (err: any) {
      setError(err.message || "Unable to load applications. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading applications...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchApplications} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1400px]">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-[#0F172A]">Applications</h2>
        <p className="text-xs text-[#64748B] mt-0.5">{applications.length} applications generated</p>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded">
        {applications.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center">
            <svg className="w-12 h-12 text-[#94A3B8] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-sm font-medium text-[#0F172A]">No applications yet</p>
            <p className="text-xs text-[#64748B] mt-1">When the agent discovers a strong match, drafts will appear here.</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F0]">
                {["Company", "Position", "Resume Used", "Recruiter Email", "Cover Letter", "Gmail Draft", "Created", "Actions"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[#64748B] font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => (
                <tr key={app.id} className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors">
                  <td className="px-4 py-3 font-medium text-[#0F172A]">{app.companyName || "—"}</td>
                  <td className="px-4 py-3 text-[#0F172A] max-w-[200px] truncate">{app.jobTitle || "—"}</td>
                  <td className="px-4 py-3 text-[#64748B]">{app.resume || "—"}</td>
                  <td className="px-4 py-3 text-[#64748B]">{app.recruiterEmail || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={app.status || "Unknown"} /></td>
                  <td className="px-4 py-3"><StatusBadge status={app.gmailDraftCreated ? "Created" : "Pending"} /></td>
                  <td className="px-4 py-3 text-[#94A3B8]">{app.createdAt ? new Date(app.createdAt).toLocaleDateString() : "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button className="text-[#2563EB] hover:text-[#1D4ED8] font-medium transition-colors">View</button>
                      {app.gmailDraftCreated && (
                        <button className="flex items-center gap-1 text-[#64748B] hover:text-[#0F172A] font-medium transition-colors">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          Gmail
                        </button>
                      )}
                      <button className="flex items-center gap-1 text-[#64748B] hover:text-[#0F172A] font-medium transition-colors">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Job
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
