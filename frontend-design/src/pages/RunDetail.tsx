import { useState, useEffect } from "react";
import { runsApi } from "../services/api/runsApi";
import type { AgentRun } from "../types/api";
import StatusBadge from "../components/StatusBadge";

const timelineStatusIcon = (status: string) => {
  if (status === "success") return (
    <div className="w-6 h-6 rounded-full bg-[#DCFCE7] flex items-center justify-center">
      <svg className="w-3 h-3 text-[#16A34A]" viewBox="0 0 12 12" fill="currentColor">
        <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
  if (status === "partial") return (
    <div className="w-6 h-6 rounded-full bg-[#FEF9C3] flex items-center justify-center">
      <svg className="w-3 h-3 text-[#CA8A04]" viewBox="0 0 12 12" fill="currentColor">
        <path d="M6 3v4M6 8.5v.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      </svg>
    </div>
  );
  return (
    <div className="w-6 h-6 rounded-full bg-[#FEE2E2] flex items-center justify-center">
      <svg className="w-3 h-3 text-[#DC2626]" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <path d="M3 3l6 6M9 3l-6 6" />
      </svg>
    </div>
  );
};

interface RunDetailProps {
  runUuid: string | null;
  onBack: () => void;
}

function formatDuration(seconds: number | null) {
  if (seconds === null || seconds === undefined) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

export default function RunDetail({ runUuid, onBack }: RunDetailProps) {
  const [run, setRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRunDetail = async () => {
    if (!runUuid) return;
    try {
      setLoading(true);
      setError(null);
      const res = await runsApi.getRunDetails(runUuid);
      setRun(res);
    } catch (err: any) {
      setError(err.message || "Unable to load run details. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (runUuid) {
      fetchRunDetail();
    }
  }, [runUuid]);

  if (!runUuid) {
    return (
      <div className="p-6 max-w-[1400px]">
        <div className="bg-white border border-[#E2E8F0] rounded p-6 text-center">
          <p className="text-sm font-medium text-[#0F172A]">No run selected</p>
          <button onClick={onBack} className="mt-4 px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading run details...</p>
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchRunDetail} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
          <button onClick={onBack} className="text-xs text-[#64748B] hover:text-[#0F172A] underline">
            Back to Runs
          </button>
        </div>
      </div>
    );
  }

  const metricGroups = [
    {
      label: "Discovery",
      items: [
        { label: "Jobs Discovered", value: run.jobsDiscovered ?? "—" },
        { label: "After Pre-filter", value: run.jobsAfterPrefilter ?? "—" },
        { label: "Jobs Evaluated", value: run.jobsEvaluated ?? "—" },
      ],
    },
    {
      label: "AI Evaluation",
      items: [
        { label: "Gemini Calls", value: run.llmCalls ?? "—" },
        { label: "Successes", value: run.llmSuccesses ?? "—", color: "#16A34A" },
        { label: "Failures", value: run.llmFailures ?? "—", color: "#DC2626" },
        { label: "429 Retries", value: run.rateLimitRetries ?? "—", color: "#F59E0B" },
      ],
    },
    {
      label: "Results",
      items: [
        { label: "Jobs Matched", value: run.jobsMatched ?? "—" },
        { label: "Drafts Generated", value: run.draftsCreated ?? "—" },
        { label: "Gmail Drafts", value: run.gmailDraftsCreated ?? "—" },
      ],
    },
    {
      label: "Recruiter",
      items: [
        { label: "Emails Verified", value: run.recruiterEmailsVerified ?? "—", color: "#16A34A" },
        { label: "Not Found", value: run.recruiterEmailsNotFound ?? "—", color: "#64748B" },
      ],
    },
  ];

  // Build a synthetic timeline from run data to match Figma's step visualization
  const runSucceeded = run.status === "SUCCEEDED" || run.status === "SUCCESS";
  const timeline = [
    { stage: "Discovery", status: run.jobsDiscovered ? "success" : "error", duration: "—" },
    { stage: "Pre-filter", status: run.jobsAfterPrefilter ? "success" : "partial", duration: "—" },
    { stage: "Evaluation", status: run.jobsEvaluated ? "success" : "partial", duration: "—" },
    { stage: "Matching", status: run.jobsMatched ? "success" : "partial", duration: "—" },
    { stage: "Drafting", status: run.draftsCreated ? "success" : "partial", duration: "—" },
    { stage: "Completed", status: runSucceeded ? "success" : "error", duration: formatDuration(run.durationSeconds) },
  ];

  return (
    <div className="p-6 max-w-[1400px] space-y-5">
      {/* Back */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-xs text-[#64748B] hover:text-[#0F172A] transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Runs
      </button>

      {/* Header card */}
      <div className="bg-white border border-[#E2E8F0] rounded p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs text-[#94A3B8] mb-1">Run ID</p>
            <p className="text-sm font-mono font-medium text-[#0F172A]">{run.runUuid}</p>
          </div>
          <StatusBadge status={run.status || "Unknown"} />
        </div>
        <div className="grid grid-cols-6 gap-4 text-xs">
          {[
            { label: "Started", value: run.startedAt ? new Date(run.startedAt).toLocaleString() : "—" },
            { label: "Completed", value: run.completedAt ? new Date(run.completedAt).toLocaleString() : "—" },
            { label: "Duration", value: formatDuration(run.durationSeconds) },
            { label: "Trigger", value: run.triggerType || "—" },
            { label: "Agent Version", value: run.agentVersion || "—" },
            { label: "Status", value: run.status || "—" },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-[#94A3B8] mb-0.5">{label}</p>
              <p className="font-medium text-[#0F172A]">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {run.failureSummary && (
        <div className="bg-[#FEF2F2] border border-[#FCA5A5] rounded p-4">
          <p className="text-xs font-semibold text-[#DC2626] uppercase tracking-wide mb-1">Failure Summary</p>
          <p className="text-sm text-[#991B1B]">{run.failureSummary}</p>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        {metricGroups.map((group) => (
          <div key={group.label} className="bg-white border border-[#E2E8F0] rounded p-4">
            <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wide mb-3">{group.label}</p>
            <div className="space-y-2.5">
              {group.items.map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-xs text-[#64748B]">{item.label}</span>
                  <span
                    className="text-sm font-bold tabular-nums"
                    style={{ color: item.color ?? "#0F172A" }}
                  >
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <div className="bg-white border border-[#E2E8F0] rounded p-5">
        <p className="text-sm font-semibold text-[#0F172A] mb-5">Execution Timeline</p>
        <div className="flex items-start gap-0">
          {timeline.map((step, i) => (
            <div key={step.stage} className="flex-1 flex flex-col items-center">
              <div className="flex items-center w-full">
                {i > 0 && (
                  <div className={`h-px flex-1 ${step.status === "success" ? "bg-[#16A34A]" : step.status === "partial" ? "bg-[#F59E0B]" : "bg-[#E2E8F0]"}`} />
                )}
                {timelineStatusIcon(step.status)}
                {i < timeline.length - 1 && (
                  <div className={`h-px flex-1 ${timeline[i + 1].status === "success" ? "bg-[#16A34A]" : "bg-[#E2E8F0]"}`} />
                )}
              </div>
              <div className="mt-2 text-center">
                <p className="text-[10px] font-medium text-[#0F172A] leading-tight">{step.stage}</p>
                <p className="text-[10px] text-[#94A3B8] mt-0.5 font-mono">{step.duration}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
