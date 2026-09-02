import { useState } from "react";

interface LoginProps {
  onLogin: () => void;
  onClose?: () => void;
}

export default function Login({ onLogin, onClose }: LoginProps) {
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setError("Please enter a valid token.");
      return;
    }
    
    // Save to local storage
    localStorage.setItem("dashboard_token", token.trim());
    setError(null);
    onLogin();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white p-8 rounded-lg shadow-lg border border-[#E2E8F0] max-w-md w-full relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
        <h2 className="text-xl font-semibold text-[#0F172A] mb-2">Admin Token Authentication</h2>
        <p className="text-sm text-[#64748B] mb-6">
          Enter your secret Admin API token to access internal system logs, raw runs, and settings.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="token" className="block text-sm font-medium text-[#0F172A] mb-1">
              Admin API Token
            </label>
            <input
              type="password"
              id="token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full px-3 py-2 border border-[#E2E8F0] rounded-md focus:outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
              placeholder="Enter Admin token..."
            />
          </div>
          
          {error && <p className="text-sm text-[#DC2626]">{error}</p>}
          
          <div className="space-y-2 pt-2">
            <button
              type="submit"
              className="w-full bg-[#2563EB] text-white py-2 px-4 rounded-md font-medium hover:bg-[#1D4ED8] transition-colors"
            >
              Authenticate Admin
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="w-full bg-white text-[#64748B] py-2 px-4 rounded-md font-medium border border-[#E2E8F0] hover:bg-[#F8FAFC] transition-colors"
              >
                Return to Public View
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
