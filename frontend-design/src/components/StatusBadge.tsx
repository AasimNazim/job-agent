const configs = {
  SUCCEEDED: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  SUCCESS: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  PARTIAL: { bg: "bg-[#FEF9C3]", text: "text-[#CA8A04]", dot: "bg-[#F59E0B]" },
  FAILED: { bg: "bg-[#FEE2E2]", text: "text-[#DC2626]", dot: "bg-[#DC2626]" },
  RUNNING: { bg: "bg-[#DBEAFE]", text: "text-[#2563EB]", dot: "bg-[#2563EB]" },
  Active: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  Disabled: { bg: "bg-[#F1F5F9]", text: "text-[#64748B]", dot: "bg-[#94A3B8]" },
  Paused: { bg: "bg-[#F1F5F9]", text: "text-[#64748B]", dot: "bg-[#94A3B8]" },
  Error: { bg: "bg-[#FEE2E2]", text: "text-[#DC2626]", dot: "bg-[#DC2626]" },
  Generated: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  DRAFT_CREATED: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  DRAFT_SAVED: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  Created: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  Pending: { bg: "bg-[#FEF9C3]", text: "text-[#CA8A04]", dot: "bg-[#F59E0B]" },
  Draft: { bg: "bg-[#FEF9C3]", text: "text-[#CA8A04]", dot: "bg-[#F59E0B]" },
  Matched: { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  Evaluated: { bg: "bg-[#DBEAFE]", text: "text-[#2563EB]", dot: "bg-[#2563EB]" },
  "Draft Saved": { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  "Draft Generated": { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
  "Gmail Draft": { bg: "bg-[#DCFCE7]", text: "text-[#16A34A]", dot: "bg-[#16A34A]" },
} as const;

interface StatusBadgeProps {
  status: string;
  pulse?: boolean;
}

export default function StatusBadge({ status, pulse = false }: StatusBadgeProps) {
  const cfg = configs[status as keyof typeof configs] ?? { bg: "bg-[#F1F5F9]", text: "text-[#64748B]", dot: "bg-[#94A3B8]" };
  const label = status === "DRAFT_SAVED" || status === "DRAFT_CREATED" ? "Draft Saved" : status;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium ${cfg.bg} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${pulse && status === "RUNNING" ? "animate-pulse" : ""}`} />
      {label}
    </span>
  );
}
