import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import TopNav from "./components/TopNav";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import Applications from "./pages/Applications";
import Runs from "./pages/Runs";
import RunDetail from "./pages/RunDetail";
import Companies from "./pages/Companies";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

export type Page = "dashboard" | "jobs" | "applications" | "runs" | "companies" | "analytics" | "settings" | "runDetail";

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(() => {
    return !!localStorage.getItem("dashboard_token");
  });
  const [showAdminModal, setShowAdminModal] = useState<boolean>(false);

  useEffect(() => {
    const handleAuthError = () => {
      // Wipes admin token on 401 but stays on public recruiter dashboard
      localStorage.removeItem("dashboard_token");
      setIsAdmin(false);
    };

    window.addEventListener("auth_error", handleAuthError);
    return () => window.removeEventListener("auth_error", handleAuthError);
  }, []);

  function navigate(p: Page) {
    setPage(p);
  }

  function handleViewRunDetail(runUuid: string) {
    setSelectedRunId(runUuid);
    navigate("runDetail");
  }

  function handleLogoutAdmin() {
    localStorage.removeItem("dashboard_token");
    setIsAdmin(false);
  }

  const restrictedPages: Page[] = ["applications", "runs", "runDetail", "settings"];

  function renderPage() {
    // If attempting to view restricted page without Admin token, show Admin Access Required screen
    if (!isAdmin && restrictedPages.includes(page)) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
          <div className="w-12 h-12 bg-[#EFF6FF] text-[#2563EB] rounded-full flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-[#0F172A] mb-1">Admin Access Required</h2>
          <p className="text-sm text-[#64748B] max-w-md mb-6">
            Detailed candidate applications, execution runs, and system settings are restricted to maintain SaaS privacy. Public recruiters can freely view Dashboard, Jobs, Companies, and Analytics.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => navigate("dashboard")}
              className="px-4 py-2 bg-white border border-[#E2E8F0] rounded-md text-sm font-medium text-[#0F172A] hover:bg-[#F8FAFC]"
            >
              Back to Dashboard
            </button>
            <button
              onClick={() => setShowAdminModal(true)}
              className="px-4 py-2 bg-[#2563EB] text-white rounded-md text-sm font-medium hover:bg-[#1D4ED8]"
            >
              Authenticate as Admin
            </button>
          </div>
        </div>
      );
    }

    switch (page) {
      case "dashboard":
        return <Dashboard onNavigate={navigate} isAdmin={isAdmin} />;
      case "jobs":
        return <Jobs />;
      case "applications":
        return <Applications />;
      case "runs":
        return <Runs onViewDetail={handleViewRunDetail} />;
      case "runDetail":
        return <RunDetail runUuid={selectedRunId} onBack={() => { setSelectedRunId(null); navigate("runs"); }} />;
      case "companies":
        return <Companies />;
      case "analytics":
        return <Analytics />;
      case "settings":
        return <Settings />;
      default:
        return <Dashboard onNavigate={navigate} isAdmin={isAdmin} />;
    }
  }

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">
      <Sidebar
        currentPage={page}
        onNavigate={navigate}
        isAdmin={isAdmin}
        onOpenAdminModal={() => setShowAdminModal(true)}
        onLogoutAdmin={handleLogoutAdmin}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNav currentPage={page} />
        <main className="flex-1 overflow-y-auto">
          {renderPage()}
        </main>
      </div>

      {showAdminModal && (
        <Login
          onLogin={() => {
            setIsAdmin(true);
            setShowAdminModal(false);
          }}
          onClose={() => setShowAdminModal(false)}
        />
      )}
    </div>
  );
}
