import clsx from "clsx";

const CATEGORY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  SOFT_DECLINE:      { label: "Soft Decline",      color: "text-yellow-300", bg: "bg-yellow-500/15 border-yellow-500/30" },
  HARD_DECLINE:      { label: "Hard Decline",      color: "text-red-300",    bg: "bg-red-500/15 border-red-500/30" },
  CREDENTIAL_EXPIRY: { label: "Credential Expiry", color: "text-orange-300", bg: "bg-orange-500/15 border-orange-500/30" },
  MANDATE_FAILURE:   { label: "Mandate Failure",   color: "text-purple-300", bg: "bg-purple-500/15 border-purple-500/30" },
  CART_ABANDONED:    { label: "Cart Abandoned",     color: "text-blue-300",   bg: "bg-blue-500/15 border-blue-500/30" },
  B2B_OVERDUE:       { label: "B2B Overdue",        color: "text-pink-300",   bg: "bg-pink-500/15 border-pink-500/30" },
  UNKNOWN:           { label: "Unknown",            color: "text-gray-300",   bg: "bg-gray-500/15 border-gray-500/30" },
};

const STATUS_CONFIG: Record<string, { label: string; dot: string }> = {
  DETECTED:               { label: "Detected",      dot: "bg-gray-400" },
  TRIAGED:                { label: "Triaged",        dot: "bg-blue-400" },
  INTERVENTION_SCHEDULED: { label: "Scheduled",     dot: "bg-yellow-400" },
  INTERVENTION_SENT:      { label: "Sent",           dot: "bg-violet-400" },
  RECOVERED:              { label: "Recovered",      dot: "bg-green-400" },
  FAILED:                 { label: "Failed",         dot: "bg-red-400" },
  LAPSED:                 { label: "Lapsed",         dot: "bg-gray-500" },
  CIRCUIT_BROKEN:         { label: "Circuit Broken", dot: "bg-red-600" },
  HOLDOUT:                { label: "Holdout",        dot: "bg-gray-400" },
};

export function CategoryBadge({ category }: { category: string }) {
  const cfg = CATEGORY_CONFIG[category] ?? CATEGORY_CONFIG.UNKNOWN;
  return (
    <span className={clsx("inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border", cfg.bg, cfg.color)}>
      {cfg.label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, dot: "bg-gray-400" };
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-gray-300">
      <span className={clsx("w-1.5 h-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}

export function AttributionBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    AGENT_DRIVEN:      "bg-green-500/15 border-green-500/30 text-green-300",
    ORGANIC_BASELINE:  "bg-gray-500/15 border-gray-500/30 text-gray-300",
    HOLDOUT:           "bg-slate-500/15 border-slate-500/30 text-slate-300",
    PENDING:           "bg-yellow-500/15 border-yellow-500/30 text-yellow-300",
  };
  return (
    <span className={clsx("inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border", map[status] ?? map.PENDING)}>
      {status.replace("_", " ")}
    </span>
  );
}
