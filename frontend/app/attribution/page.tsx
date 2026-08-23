"use client";
import { useEffect, useState } from "react";
import { api, RecoveryEvent } from "@/lib/api";
import { CategoryBadge, StatusBadge, AttributionBadge } from "@/components/Badges";
import { RefreshCcw, Search } from "lucide-react";
import { formatDistanceToNow } from "@/lib/utils";

const STATUSES = ["", "RECOVERED", "INTERVENTION_SENT", "TRIAGED", "CIRCUIT_BROKEN", "HOLDOUT"];
const CATEGORIES = ["", "SOFT_DECLINE", "HARD_DECLINE", "CREDENTIAL_EXPIRY", "MANDATE_FAILURE", "CART_ABANDONED", "B2B_OVERDUE"];

export default function AttributionPage() {
  const [events, setEvents] = useState<RecoveryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [stats, setStats] = useState<Record<string, number>>({});

  const load = async () => {
    setLoading(true);
    try {
      const [evts, attrStats] = await Promise.all([
        api.getEvents({ limit: 100, status: status || undefined, category: category || undefined }),
        api.getAttributionStats(),
      ]);
      setEvents(evts);
      setStats(attrStats);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [status, category]);

  const filtered = events.filter((e) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      e.recovery_id.includes(q) ||
      e.original_charge_id.includes(q) ||
      (e.customer_email ?? "").toLowerCase().includes(q) ||
      (e.customer_name ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Attribution Ledger</h1>
        <p className="text-sm text-gray-400 mt-1">Immutable recovery record — every intervention tracked and attributed</p>
      </div>

      {/* Attribution summary cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { key: "AGENT_DRIVEN", label: "Agent Driven", color: "text-green-400 border-green-500/30 bg-green-500/10" },
          { key: "ORGANIC_BASELINE", label: "Organic Baseline", color: "text-gray-300 border-gray-500/30 bg-gray-500/10" },
          { key: "HOLDOUT", label: "Holdout (Control)", color: "text-slate-300 border-slate-500/30 bg-slate-500/10" },
          { key: "PENDING", label: "Pending", color: "text-yellow-300 border-yellow-500/30 bg-yellow-500/10" },
        ].map(({ key, label, color }) => (
          <div key={key} className={`rounded-xl border p-4 ${color}`}>
            <p className="text-xs font-medium opacity-70 uppercase tracking-wide">{label}</p>
            <p className="text-2xl font-bold mt-1">{stats[key] ?? 0}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID, email, customer..."
            className="w-full pl-9 pr-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-500" />
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-violet-500">
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-violet-500">
          <option value="">All Categories</option>
          {CATEGORIES.filter(Boolean).map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
        </select>
        <button onClick={load}
          className="flex items-center gap-2 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300 hover:bg-gray-700 transition-colors">
          <RefreshCcw size={13} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-left">
                <th className="px-4 py-3 font-medium">Recovery ID</th>
                <th className="px-4 py-3 font-medium">Charge ID</th>
                <th className="px-4 py-3 font-medium">Customer</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Attribution</th>
                <th className="px-4 py-3 font-medium">Settlement</th>
                <th className="px-4 py-3 font-medium">Age</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {loading ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">No events found</td></tr>
              ) : (
                filtered.map((e) => (
                  <tr key={e.recovery_id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-400 max-w-[120px]">
                      <span className="truncate block" title={e.recovery_id}>{e.recovery_id.substring(0, 12)}...</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-400">
                      <span className="truncate block max-w-[120px]" title={e.original_charge_id}>{e.original_charge_id.substring(0, 14)}...</span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      <div>{e.customer_name ?? "—"}</div>
                      <div className="text-gray-500 truncate max-w-[120px]">{e.customer_email}</div>
                    </td>
                    <td className="px-4 py-3"><CategoryBadge category={e.failure_category} /></td>
                    <td className="px-4 py-3 text-gray-300">
                      {e.amount ? `₹${e.amount.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                    <td className="px-4 py-3"><AttributionBadge status={e.attribution_status} /></td>
                    <td className="px-4 py-3 text-green-400 font-medium">
                      {e.settlement_amount ? `₹${e.settlement_amount.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDistanceToNow(e.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-gray-800 text-xs text-gray-500">
          Showing {filtered.length} of {events.length} events
        </div>
      </div>
    </div>
  );
}
