import { type Page } from "../App";

const pageTitles: Record<string, string> = {
  dashboard: "Dashboard",
  jobs: "Jobs",
  applications: "Applications",
  runs: "Runs",
  companies: "Companies",
  analytics: "Analytics",
  settings: "Settings",
  runDetail: "Run Details",
};

interface TopNavProps {
  currentPage: string;
}

export default function TopNav({ currentPage }: TopNavProps) {
  return (
    <header className="h-14 bg-white border-b border-[#E2E8F0] flex items-center justify-between px-6 sticky top-0 z-10">
      <h1 className="text-sm font-semibold text-[#0F172A]">{pageTitles[currentPage] ?? "Dashboard"}</h1>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#F8FAFC] border border-[#E2E8F0]">
          <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" />
          <span className="text-[11px] font-medium text-[#64748B]">Agent Online</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-[#2563EB] flex items-center justify-center text-white text-xs font-semibold shadow-sm">
          A
        </div>
      </div>
    </header>
  );
}
