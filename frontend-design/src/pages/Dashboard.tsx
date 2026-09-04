import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import StatusBadge from "../components/StatusBadge";
import { type Page } from "../App";
import { dashboardApi } from "../services/api/dashboardApi";
import { runsApi } from "../services/api/runsApi";
import { analyticsApi } from "../services/api/analyticsApi";
import type { DashboardOverview, AgentRun, AnalyticsResponse } from "../types/api";

type TimeRange = "7d" | "30d" | "90d";

const resumeColors = ["#2563EB", "#3B82F6", "#93C5FD", "#BFDBFE", "#DBEAFE"];

function formatDuration(seconds: number | null) {
  if (seconds === null || seconds === undefined) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

function MiniSparkline({ data }: { data: number[] }) {
  if (!data || data.length < 2) return <div className="w-14 h-6" />;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 56, h = 24;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
      <polyline points={points} fill="none" stroke="#3B82F6" strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function KpiCard({ label, value, change, trend }: { label: string; value: number | null; change?: number; trend?: number[] }) {
  const positive = change !== undefined ? change >= 0 : true;
  return (
    <div className="bg-white border border-[#E2E8F0] rounded p-4 flex flex-col gap-3">
      <p className="text-xs text-[#64748B] font-medium">{label}</p>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold text-[#0F172A] leading-none tabular-nums">
          {value !== null && value !== undefined ? value.toLocaleString() : "—"}
        </span>
        <MiniSparkline data={trend ?? [0, 0]} />
      </div>
      {change !== undefined ? (
        <div className={`flex items-center gap-1 text-xs font-medium ${positive ? "text-[#16A34A]" : "text-[#DC2626]"}`}>
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
            {positive
              ? <path d="M6 2l4 4H7v4H5V6H2l4-4z" />
              : <path d="M6 10L2 6h3V2h2v4h3L6 10z" />}
          </svg>
          {Math.abs(change)}% vs last period
        </div>
      ) : (
        <div className="flex items-center gap-1 text-[10px] font-medium text-[#94A3B8]">
          Overall total
        </div>
      )}
    </div>
  );
}

interface DashboardProps {
  onNavigate: (page: Page) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");

  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [recentRuns, setRecentRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [analyticsData, setAnalyticsData] = useState<AnalyticsResponse | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewData, runsData] = await Promise.all([
        dashboardApi.getOverview(),
        runsApi.getRuns(1, 5)
      ]);
      setOverview(overviewData);
      setRecentRuns(runsData.items);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalyticsData = async () => {
    try {
      setAnalyticsLoading(true);
      setAnalyticsError(null);
      const data = await analyticsApi.getAnalytics(timeRange);
      setAnalyticsData(data);
    } catch (err: any) {
      setAnalyticsError(err.message || "Failed to load analytics");
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchDashboardData} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const latestRunDuration = recentRuns.length > 0 ? recentRuns[0].durationSeconds : null;
  const latestRunScanned = recentRuns.length > 0 ? recentRuns[0].jobsDiscovered : null;

  // Build sparkline trends from timeline data
  const discoveredTrend = analyticsData?.timeline?.map(t => t.discovered) ?? [0, 0];
  const matchedTrend = analyticsData?.timeline?.map(t => t.matched) ?? [0, 0];
  const appliedTrend = analyticsData?.timeline?.map(t => t.applied) ?? [0, 0];

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[#0F172A]">Good morning, Asim</h2>
          <p className="text-sm text-[#64748B] mt-0.5">Here's what your job agent discovered recently.</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-[#64748B]">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${overview?.lastRunStatus === "SUCCEEDED" ? "bg-[#16A34A]" : overview?.lastRunStatus === "FAILED" ? "bg-[#DC2626]" : "bg-[#64748B]"}`} />
            Last run: <span className="font-medium text-[#0F172A]">{overview?.lastRunStartedAt ? new Date(overview.lastRunStartedAt).toLocaleString() : "Never"}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Duration: <span className="font-medium text-[#0F172A]">{formatDuration(latestRunDuration)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Scanned: <span className="font-medium text-[#0F172A]">{latestRunScanned ?? "—"} jobs</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-5 gap-4">
        <KpiCard label="Jobs Discovered" value={overview?.jobsDiscovered ?? null} trend={discoveredTrend} />
        <KpiCard label="LLM Calls" value={overview?.llmCalls ?? null} trend={matchedTrend} />
        <KpiCard label="Jobs Matched" value={overview?.jobsMatched ?? null} trend={matchedTrend} />
        <KpiCard label="Applications Generated" value={overview?.applicationsGenerated ?? null} trend={appliedTrend} />
        <KpiCard label="Verified Emails" value={overview?.recruiterEmailsVerified ?? null} trend={appliedTrend} />
      </div>

      {/* Main chart + funnel row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Discovery chart */}
        <div className="col-span-2 bg-white border border-[#E2E8F0] rounded p-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm font-semibold text-[#0F172A]">Job Discovery Overview</p>
              <p className="text-xs text-[#64748B] mt-0.5">Discoveries, matches, and applications over time</p>
            </div>
            <div className="flex items-center gap-1 p-0.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded">
              {(["7d", "30d", "90d"] as TimeRange[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTimeRange(t)}
                  className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                    timeRange === t
                      ? "bg-white text-[#2563EB] shadow-sm border border-[#E2E8F0]"
                      : "text-[#64748B] hover:text-[#0F172A]"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          {analyticsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <div className="w-6 h-6 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
            </div>
          ) : analyticsError || !analyticsData?.timeline?.length ? (
            <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">
              {analyticsError ?? "No data for this time period."}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={analyticsData.timeline} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94A3B8" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#94A3B8" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 4, fontSize: 12 }}
                  cursor={{ fill: "#F8FAFC" }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
                <Bar dataKey="discovered" name="Discovered" fill="#DBEAFE" radius={[2, 2, 0, 0]} />
                <Bar dataKey="matched" name="Matched" fill="#3B82F6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="applied" name="Applied" fill="#2563EB" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Application Funnel */}
        <div className="bg-white border border-[#E2E8F0] rounded p-4">
          <p className="text-sm font-semibold text-[#0F172A] mb-4">Application Funnel</p>
          {analyticsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <div className="w-6 h-6 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
            </div>
          ) : analyticsError || !analyticsData?.funnel?.length ? (
            <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">
              {analyticsError ?? "No funnel data."}
            </div>
          ) : (
            <div className="space-y-1">
              {analyticsData.funnel.map((row, i) => (
                <div key={row.stage}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-[#64748B]">{row.stage}</span>
                    <span className="text-xs font-medium text-[#0F172A] tabular-nums">{row.count.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 bg-[#F1F5F9] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${row.pct}%`,
                        background: `hsl(${220 - i * 10}, ${70 - i * 5}%, ${45 + i * 5}%)`,
                      }}
                    />
                  </div>
                  {i < analyticsData.funnel.length - 1 && (
                    <div className="flex items-center gap-1 mt-1 mb-2 ml-1">
                      <svg className="w-2.5 h-2.5 text-[#94A3B8]" viewBox="0 0 10 10" fill="currentColor">
                        <path d="M5 1v8M2 6l3 3 3-3" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                      </svg>
                      <span className="text-[10px] text-[#94A3B8]">{analyticsData.funnel[i + 1].pct}% conversion</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Top Companies */}
        <div className="col-span-2 bg-white border border-[#E2E8F0] rounded">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#E2E8F0]">
            <p className="text-sm font-semibold text-[#0F172A]">Top Companies</p>
            <button onClick={() => onNavigate("companies")} className="text-xs text-[#2563EB] hover:text-[#1D4ED8] font-medium transition-colors">
              View all
            </button>
          </div>
          {analyticsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <div className="w-6 h-6 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
            </div>
          ) : !analyticsData?.topCompanies?.length ? (
            <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">
              No companies data yet.
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F0]">
                  <th className="text-left px-4 py-2.5 text-[#64748B] font-medium">Company</th>
                  <th className="text-right px-4 py-2.5 text-[#64748B] font-medium">Jobs Found</th>
                  <th className="text-right px-4 py-2.5 text-[#64748B] font-medium">Matching</th>
                  <th className="text-right px-4 py-2.5 text-[#64748B] font-medium">Applications</th>
                </tr>
              </thead>
              <tbody>
                {analyticsData.topCompanies.map((c) => (
                  <tr key={c.name} className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors">
                    <td className="px-4 py-2.5 font-medium text-[#0F172A]">{c.name}</td>
                    <td className="px-4 py-2.5 text-right text-[#64748B] tabular-nums">{c.jobsFound}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      <span className={c.matchingJobs > 0 ? "text-[#2563EB] font-medium" : "text-[#94A3B8]"}>{c.matchingJobs}</span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-[#64748B] tabular-nums">{c.applications}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Resume Performance */}
        <div className="bg-white border border-[#E2E8F0] rounded">
          <div className="px-4 py-3 border-b border-[#E2E8F0]">
            <p className="text-sm font-semibold text-[#0F172A]">Resume Performance</p>
          </div>
          {analyticsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <div className="w-6 h-6 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
            </div>
          ) : !analyticsData?.resumePerformance?.length ? (
            <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">
              No resume data yet.
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {analyticsData.resumePerformance.map((r, i) => {
                const maxSelected = Math.max(...analyticsData.resumePerformance.map((rp) => rp.selected)) || 1;
                return (
                  <div key={r.name}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-[#0F172A] truncate max-w-[180px]">{r.name.replace(/\.pdf$/i, "").replace(/_/g, " ")}</span>
                      <span className="text-xs font-medium text-[#64748B] tabular-nums">{r.selected}×</span>
                    </div>
                    <div className="h-1.5 bg-[#F1F5F9] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${(r.selected / maxSelected) * 100}%`, background: resumeColors[i % resumeColors.length] }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Runs */}
      <div className="bg-white border border-[#E2E8F0] rounded">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#E2E8F0]">
          <p className="text-sm font-semibold text-[#0F172A]">Recent Agent Runs</p>
          <button onClick={() => onNavigate("runs")} className="text-xs text-[#2563EB] hover:text-[#1D4ED8] font-medium transition-colors">
            View all
          </button>
        </div>
        {recentRuns.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center">
            <p className="text-sm font-medium text-[#0F172A]">No runs found</p>
            <p className="text-xs text-[#64748B] mt-1">The agent has not executed any runs yet.</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F0]">
                {["Run ID", "Date / Time", "Trigger", "Discovered", "Pre-filtered", "Evaluated", "Matched", "Drafts", "Verified", "Duration", "Status"].map((h) => (
                  <th key={h} className="text-left px-4 py-2.5 text-[#64748B] font-medium first:w-44">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((run) => (
                <tr key={run.runUuid || Math.random()} className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors">
                  <td className="px-4 py-2.5 font-mono text-[10px] text-[#2563EB]">{run.runUuid?.split('-')[0] || "—"}</td>
                  <td className="px-4 py-2.5 text-[#64748B]">{run.startedAt ? new Date(run.startedAt).toLocaleString() : "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                      run.triggerType?.toLowerCase() === "manual"
                        ? "bg-[#FEF9C3] text-[#CA8A04]"
                        : "bg-[#F1F5F9] text-[#64748B]"
                    }`}>
                      {run.triggerType || "Unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.jobsDiscovered ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.jobsAfterPrefilter ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.jobsEvaluated ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.jobsMatched ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.draftsCreated ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#0F172A] tabular-nums">{run.recruiterEmailsVerified ?? "—"}</td>
                  <td className="px-4 py-2.5 text-[#64748B] font-mono text-[10px]">{formatDuration(run.durationSeconds)}</td>
                  <td className="px-4 py-2.5"><StatusBadge status={run.status || "Unknown"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
