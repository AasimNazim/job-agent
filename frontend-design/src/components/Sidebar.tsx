import { type Page } from "../App";

const navItems: { id: Page; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
  { id: "jobs", label: "Jobs", icon: "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
  { id: "applications", label: "Applications", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { id: "runs", label: "Runs", icon: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" },
  { id: "companies", label: "Companies", icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" },
  { id: "analytics", label: "Analytics", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { id: "settings", label: "Settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" },
];

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
  isAdmin: boolean;
  onOpenAdminModal: () => void;
  onLogoutAdmin: () => void;
}

export default function Sidebar({ currentPage, onNavigate, isAdmin, onOpenAdminModal, onLogoutAdmin }: SidebarProps) {
  return (
    <aside className="w-56 shrink-0 bg-white border-r border-[#E2E8F0] flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-[#E2E8F0]">
        <div className="w-7 h-7 bg-[#2563EB] rounded flex items-center justify-center">
          <svg viewBox="0 0 20 20" fill="white" className="w-4 h-4">
            <path d="M10 2a8 8 0 100 16A8 8 0 0010 2zm-1 11.5v-5l4 2.5-4 2.5z" />
          </svg>
        </div>
        <span className="text-sm font-semibold text-[#0F172A] tracking-tight">JobPilot AI</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const active = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm font-medium transition-colors ${
                active
                  ? "bg-[#EFF6FF] text-[#2563EB]"
                  : "text-[#64748B] hover:bg-[#F8FAFC] hover:text-[#0F172A]"
              }`}
            >
              <svg
                className={`w-4 h-4 shrink-0 ${active ? "text-[#2563EB]" : "text-[#94A3B8]"}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.75}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* User / Workspace Status */}
      <div className="border-t border-[#E2E8F0] p-3 space-y-2">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded bg-[#F8FAFC] border border-[#E2E8F0]">
          <div className="w-7 h-7 rounded-full bg-[#2563EB] flex items-center justify-center text-white text-xs font-semibold shrink-0">
            {isAdmin ? "A" : "R"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-[#0F172A] truncate">
              {isAdmin ? "Admin User" : "Public Guest"}
            </p>
            <p className={`text-[10px] font-medium truncate ${isAdmin ? "text-[#16A34A]" : "text-[#2563EB]"}`}>
              ● {isAdmin ? "Admin Workspace" : "Public Demo View"}
            </p>
          </div>
        </div>

        {isAdmin ? (
          <button
            onClick={onLogoutAdmin}
            className="w-full text-center text-xs font-medium text-[#DC2626] hover:underline py-1"
          >
            Exit Admin Access
          </button>
        ) : (
          <button
            onClick={onOpenAdminModal}
            className="w-full text-center text-xs font-medium text-[#2563EB] hover:underline py-1"
          >
            Admin Login
          </button>
        )}
      </div>
    </aside>
  );
}
