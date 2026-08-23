"use client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { TrendPoint, DashboardSummary } from "@/lib/api";

// ── Recovery Trend Bar Chart ───────────────────────────────────────────────

export function RecoveryTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Recovery Trend (7 Days)</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 11 }} />
          <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
            labelStyle={{ color: "#f9fafb" }}
            itemStyle={{ color: "#d1d5db" }}
          />
          <Bar dataKey="total" name="Total Events" fill="#374151" radius={[4, 4, 0, 0]} />
          <Bar dataKey="recovered" name="Recovered" fill="#7c3aed" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Category Breakdown Bar Chart ───────────────────────────────────────────

const CATEGORY_COLORS: Record<string, string> = {
  SOFT_DECLINE: "#eab308",
  HARD_DECLINE: "#ef4444",
  CREDENTIAL_EXPIRY: "#f97316",
  MANDATE_FAILURE: "#a855f7",
  CART_ABANDONED: "#3b82f6",
  B2B_OVERDUE: "#ec4899",
  UNKNOWN: "#6b7280",
};

export function CategoryBreakdownChart({ breakdown }: { breakdown: Record<string, number> }) {
  const data = Object.entries(breakdown).map(([key, value]) => ({
    name: key.replace("_", " "),
    value,
    key,
  }));

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Events by Category</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="name" tick={{ fill: "#6b7280", fontSize: 10 }} angle={-20} textAnchor="end" />
          <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
            labelStyle={{ color: "#f9fafb" }}
          />
          <Bar dataKey="value" name="Events" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.key} fill={CATEGORY_COLORS[entry.key] ?? "#6b7280"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Attribution Donut Chart ────────────────────────────────────────────────

const ATTR_COLORS: Record<string, string> = {
  AGENT_DRIVEN: "#22c55e",
  ORGANIC_BASELINE: "#6b7280",
  HOLDOUT: "#475569",
  PENDING: "#eab308",
};

export function AttributionDonut({ summary }: { summary: DashboardSummary }) {
  const data = [
    { name: "Agent Driven", value: summary.agent_driven_count, key: "AGENT_DRIVEN" },
    { name: "Organic Baseline", value: summary.organic_count, key: "ORGANIC_BASELINE" },
    { name: "Holdout", value: summary.holdout_count, key: "HOLDOUT" },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-center justify-center h-64">
        <p className="text-gray-500 text-sm">No attribution data yet</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-white mb-1">Attribution Split</h3>
      <p className="text-xs text-gray-500 mb-4">Agent-driven vs organic baseline (5% holdout)</p>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
            {data.map((entry) => (
              <Cell key={entry.key} fill={ATTR_COLORS[entry.key] ?? "#6b7280"} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
            formatter={(value, name) => [value, name]}
          />
          <Legend formatter={(value) => <span className="text-xs text-gray-400">{value}</span>} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
