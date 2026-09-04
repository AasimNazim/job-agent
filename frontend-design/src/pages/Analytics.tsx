import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import { useState, useEffect } from "react";
import { analyticsApi } from "../services/api/analyticsApi";
import { dashboardApi } from "../services/api/dashboardApi";
import type { AnalyticsResponse, SystemHealth } from "../types/api";

const COLORS = ["#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE"];

export default function Analytics() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    analyticsApi.getAnalytics("30d")
      .then(setAnalyticsData)
      .catch((err: any) => setError(err.message || "Failed to load analytics"))
      .finally(() => setLoading(false));

    dashboardApi.getSystemHealth()
      .then(setSystemHealth)
      .catch(() => {/* silent */});
  }, []);

  const healthItems = [
    { label: "Agent Status", value: systemHealth?.agentLastRun ? "Active" : "IDLE", status: systemHealth?.apiStatus === "healthy" ? "ok" : "warn" },
    { label: "API Status", value: systemHealth?.apiStatus ?? "Unknown", status: systemHealth?.apiStatus === "healthy" ? "ok" : "error" },
    { label: "Database", value: systemHealth?.databaseStatus ?? "Unknown", status: systemHealth?.databaseStatus === "healthy" ? "ok" : "error" },
    { label: "Agent Version", value: systemHealth?.agentVersion ?? "—", status: "ok" },
    { label: "Companies Configured", value: systemHealth?.companiesConfigured != null ? String(systemHealth.companiesConfigured) : "—", status: "ok" },
    { label: "Last Successful Run", value: systemHealth?.agentLastSuccess ? new Date(systemHealth.agentLastSuccess).toLocaleString() : "Never", status: systemHealth?.agentLastSuccess ? "ok" : "warn" },
    { label: "Total Jobs in DB", value: systemHealth?.databaseJobs != null ? String(systemHealth.databaseJobs) : "—", status: "ok" },
    { label: "Total Applications", value: systemHealth?.databaseApplications != null ? String(systemHealth.databaseApplications) : "—", status: "ok" },
  ];

  return (
    <div className="p-6 max-w-[1400px] space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-[#0F172A]">Analytics</h2>
        <p className="text-xs text-[#64748B] mt-0.5">Performance metrics and system health</p>
      </div>

      {/* System Health */}
      <div className="bg-white border border-[#E2E8F0] rounded">
        <div className="px-4 py-3 border-b border-[#E2E8F0]">
          <p className="text-sm font-semibold text-[#0F172A]">System Status</p>
        </div>
        <div className="grid grid-cols-4 divide-x divide-[#F1F5F9]">
          {healthItems.map((item) => (
            <div key={item.label} className="px-4 py-3 flex items-center gap-2.5">
              <div
                className={`w-2 h-2 rounded-full shrink-0 ${
                  item.status === "ok" ? "bg-[#16A34A]" : item.status === "warn" ? "bg-[#F59E0B]" : "bg-[#DC2626]"
                }`}
              />
              <div>
                <p className="text-[10px] text-[#94A3B8]">{item.label}</p>
                <p className="text-xs font-medium text-[#0F172A]">{item.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
        </div>
      ) : error ? (
        <div className="flex justify-center items-center h-64 text-[#DC2626]">{error}</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4">
            {/* Trend area chart */}
            <div className="bg-white border border-[#E2E8F0] rounded p-4">
              <p className="text-sm font-semibold text-[#0F172A] mb-1">Discovery Trend (30 days)</p>
              <p className="text-xs text-[#64748B] mb-4">Jobs discovered per day</p>
              {!analyticsData?.timeline?.length ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">No data available.</div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={analyticsData.timeline}>
                    <defs>
                      <linearGradient id="colorDiscovered" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563EB" stopOpacity={0.12} />
                        <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94A3B8" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#94A3B8" }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 4, fontSize: 12 }} />
                    <Area type="monotone" dataKey="discovered" name="Discovered" stroke="#2563EB" strokeWidth={2} fill="url(#colorDiscovered)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Resume pie chart */}
            <div className="bg-white border border-[#E2E8F0] rounded p-4">
              <p className="text-sm font-semibold text-[#0F172A] mb-1">Resume Selection</p>
              <p className="text-xs text-[#64748B] mb-4">Which resume the agent picks most</p>
              {!analyticsData?.resumePerformance?.filter(r => r.selected > 0).length ? (
                <div className="flex items-center justify-center h-[200px] text-sm text-[#94A3B8]">
                  No resume data available.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={analyticsData.resumePerformance
                        .filter((r) => r.selected > 0)
                        .map((r) => ({ ...r, name: r.name.replace(/\.pdf$/i, "").replace(/_/g, " ") }))
                      }
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={3}
                      dataKey="selected"
                      nameKey="name"
                    >
                      {analyticsData.resumePerformance.filter((r) => r.selected > 0).map((entry, index) => (
                        <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Legend
                      wrapperStyle={{ fontSize: 11, paddingTop: 10 }}
                      formatter={(value: string) => (value.length > 20 ? `${value.substring(0, 18)}...` : value)}
                    />
                    <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 4, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Funnel bar chart */}
          <div className="bg-white border border-[#E2E8F0] rounded p-4">
            <p className="text-sm font-semibold text-[#0F172A] mb-1">Application Funnel</p>
            <p className="text-xs text-[#64748B] mb-4">Conversion at each stage of the pipeline</p>
            {!analyticsData?.funnel?.length ? (
              <div className="flex items-center justify-center h-[180px] text-sm text-[#94A3B8]">No funnel data available.</div>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={analyticsData.funnel} layout="vertical" barSize={16}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "#94A3B8" }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="stage" type="category" tick={{ fontSize: 11, fill: "#64748B" }} axisLine={false} tickLine={false} width={100} />
                  <Tooltip contentStyle={{ background: "#fff", border: "1px solid #E2E8F0", borderRadius: 4, fontSize: 12 }} />
                  <Bar dataKey="count" name="Count" radius={[0, 2, 2, 0]}>
                    {analyticsData.funnel.map((_, i) => (
                      <Cell key={i} fill={`hsl(${220 - i * 8}, ${72 - i * 6}%, ${45 + i * 5}%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  );
}
