import { useState, useEffect } from "react";
import StatusBadge from "../components/StatusBadge";
import { companiesApi } from "../services/api/companiesApi";
import type { CompanyDashboard } from "../types/api";

const companyInitials: Record<string, string> = {
  Stripe: "S",
  Vercel: "V",
  Linear: "L",
  Notion: "N",
  Figma: "F",
  Loom: "Lo",
  Retool: "R",
  Planetscale: "PS",
  Raycast: "Rc",
  Resend: "Re",
};

const companyColors: Record<string, string> = {
  Stripe: "#635BFF",
  Vercel: "#000000",
  Linear: "#5E6AD2",
  Notion: "#000000",
  Figma: "#F24E1E",
  Loom: "#625DF5",
  Retool: "#FF4F00",
  Planetscale: "#000000",
  Raycast: "#FF6363",
  Resend: "#000000",
};

export default function Companies() {
  const [data, setData] = useState<CompanyDashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await companiesApi.getCompanies(1, 100);
      setData(res.items);
    } catch (err: any) {
      setError(err.message || "Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  if (loading) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin"></div>
          <p className="text-sm text-[#64748B]">Loading companies...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1400px] flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-4 bg-white border border-[#E2E8F0] rounded p-6">
          <p className="text-sm font-medium text-[#DC2626]">{error}</p>
          <button onClick={fetchCompanies} className="px-4 py-2 bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#0F172A] text-xs font-medium rounded transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1400px]">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-[#0F172A]">Companies</h2>
        <p className="text-xs text-[#64748B] mt-0.5">{data.length} companies monitored</p>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded">
        {data.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center">
            <p className="text-sm font-medium text-[#0F172A]">No companies found</p>
            <p className="text-xs text-[#64748B] mt-1">Configure companies in your backend to see them here.</p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#E2E8F0]">
                {["Company", "ATS", "Jobs Found", "Last Scan", "Status", "Matching Jobs"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[#64748B] font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((c) => (
                <tr key={c.name} className="border-b border-[#F1F5F9] hover:bg-[#FAFAFA] transition-colors cursor-pointer">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center text-white text-[10px] font-bold shrink-0"
                        style={{ background: companyColors[c.name] ?? "#64748B" }}
                      >
                        {companyInitials[c.name] ?? c.name[0]}
                      </div>
                      <span className="font-medium text-[#0F172A]">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[#64748B]">{c.ats}</td>
                  <td className="px-4 py-3 text-[#0F172A] tabular-nums font-medium">{c.jobsFound}</td>
                  <td className="px-4 py-3 text-[#94A3B8]">{c.lastScan ? new Date(c.lastScan).toLocaleString() : "Never"}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.scanStatus} /></td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-semibold tabular-nums ${c.matchingJobs > 0 ? "text-[#2563EB]" : "text-[#94A3B8]"}`}>
                      {c.matchingJobs}
                    </span>
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
