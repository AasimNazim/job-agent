import { useState, useEffect } from "react";
import { runsApi } from "../services/api/runsApi";
import type { AgentRun } from "../types/api";
import StatusBadge from "../components/StatusBadge";

interface RunsProps {
  onViewDetail: (runUuid: string) => void;
}

function formatDuration(seconds: number | null) {
  if (seconds === null || seconds === undefined) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

export default function Runs({ onViewDetail }: RunsProps) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await runsApi.getRuns();
      setRuns(res.items);
    } catch (err: any) {
      setError(err.message || "Unable to load runs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading runs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchRuns} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1400px]">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-[#0F172A]">Agent Runs</h2>
        <p className="text-xs text-[#64748B] mt-0.5">History of all agent executions</p>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded">
        {runs.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center">
            <svg className="w-12 h-12 text-[#94A3B8] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium text-[#0F172A]">No runs found</p>
            <p className="text-xs text-[#64748B] mt-1">The agent has not executed any runs yet.</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F0]">
                {["Run ID", "Date / Time", "Trigger", "Discovered", "Matched", "Drafts", "Verified", "Duration", "Status", ""].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[#64748B] font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.runUuid || Math.random()} className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors">
                  <td className="px-4 py-3 font-mono text-[10px] text-[#2563EB]">{run.runUuid?.split('-')[0] || "—"}</td>
                  <td className="px-4 py-3 text-[#64748B]">{run.startedAt ? new Date(run.startedAt).toLocaleString() : "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                      run.triggerType?.toLowerCase() === "manual"
                        ? "bg-[#FEF9C3] text-[#CA8A04]"
                        : "bg-[#F1F5F9] text-[#64748B]"
                    }`}>
                      {run.triggerType || "Unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[#0F172A] tabular-nums">{run.jobsDiscovered ?? "—"}</td>
                  <td className="px-4 py-3 text-[#0F172A] tabular-nums">{run.jobsMatched ?? "—"}</td>
                  <td className="px-4 py-3 text-[#0F172A] tabular-nums">{run.draftsCreated ?? "—"}</td>
                  <td className="px-4 py-3 text-[#0F172A] tabular-nums">{run.recruiterEmailsVerified ?? "—"}</td>
                  <td className="px-4 py-3 text-[#64748B] font-mono text-[10px]">{formatDuration(run.durationSeconds)}</td>
                  <td className="px-4 py-3"><StatusBadge status={run.status || "Unknown"} /></td>
                  <td className="px-4 py-3">
                    {run.runUuid && (
                      <button
                        onClick={() => onViewDetail(run.runUuid as string)}
                        className="text-[#2563EB] hover:text-[#1D4ED8] font-medium transition-colors"
                      >
                        Details
                      </button>
                    )}
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
