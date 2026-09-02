export default function Settings() {
  return (
    <div className="p-6 max-w-2xl space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[#0F172A]">Settings & Configuration</h2>
          <p className="text-xs text-[#64748B] mt-0.5">Agent environment parameters and API settings</p>
        </div>
        <span className="text-[11px] bg-[#EFF6FF] text-[#2563EB] font-medium px-2.5 py-1 rounded border border-[#BFDBFE]">
          Configured via Environment / GitHub Secrets
        </span>
      </div>

      {/* Settings Sections */}
      {[
        {
          title: "Agent Schedule",
          badge: "GitHub Actions Cron",
          fields: [
            { label: "Run Schedule", value: "Every 2 hours (08:00 - 22:00 PKT)" },
            { label: "Timezone", value: "Pakistan Standard Time (UTC+5)" },
          ],
        },
        {
          title: "Gemini AI Model",
          badge: "Active Secret: GEMINI_API_KEY",
          fields: [
            { label: "API Key", value: "•••••••••••••••• (Set in GitHub Secrets)" },
            { label: "Active Model", value: "gemini-2.5-flash (Fast & Cost Efficient)" },
          ],
        },
        {
          title: "Gmail Integration",
          badge: "OAuth 2.0 (Production)",
          fields: [
            { label: "Authentication Method", value: "OAuth 2.0 (token.json)" },
            { label: "Draft Action", value: "Automatically push drafts to Gmail inbox" },
          ],
        },
        {
          title: "Matching & Evaluation Criteria",
          badge: "Backend Config",
          fields: [
            { label: "Target Experience", value: "Entry-level & Junior (0-2 YOE)" },
            { label: "Match Threshold", value: "75% minimum relevance score" },
            { label: "Max Daily Applications", value: "5 drafts per day limit" },
          ],
        },
      ].map((section) => (
        <div key={section.title} className="bg-white border border-[#E2E8F0] rounded">
          <div className="px-4 py-3 border-b border-[#E2E8F0] flex items-center justify-between">
            <p className="text-sm font-semibold text-[#0F172A]">{section.title}</p>
            <span className="text-[10px] text-[#64748B] bg-[#F8FAFC] px-2 py-0.5 rounded border border-[#E2E8F0]">
              {section.badge}
            </span>
          </div>
          <div className="p-4 space-y-3">
            {section.fields.map((field) => (
              <div key={field.label} className="flex items-center justify-between text-xs">
                <label className="font-medium text-[#64748B]">{field.label}</label>
                <span className="font-medium text-[#0F172A] bg-[#F8FAFC] px-3 py-1.5 rounded border border-[#E2E8F0] min-w-[220px] text-right">
                  {field.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
