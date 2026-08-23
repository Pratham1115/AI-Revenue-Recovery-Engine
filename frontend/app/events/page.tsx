"use client";
import { useEffect, useState, useCallback } from "react";
import { api, RecoveryEvent } from "@/lib/api";
import { CategoryBadge, StatusBadge } from "@/components/Badges";
import { RefreshCcw, Activity } from "lucide-react";
import { formatDistanceToNow } from "@/lib/utils";

export default function EventsPage() {
  const [events, setEvents] = useState<RecoveryEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const evts = await api.getEvents({ limit: 50 });
      setEvents(evts);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity size={22} className="text-violet-400" /> Live Event Feed
          </h1>
          <p className="text-sm text-gray-400 mt-1">Auto-refreshes every 5 seconds · Latest 50 events</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 hover:bg-gray-700 transition-colors">
          <RefreshCcw size={12} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <div className="space-y-3">
        {loading && events.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500 text-sm">
            Loading events...
          </div>
        ) : events.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
            <p className="text-gray-500 text-sm">No events yet. Head to the <strong className="text-violet-400">Simulator</strong> to fire some!</p>
          </div>
        ) : events.map((event) => (
          <div key={event.recovery_id} className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <CategoryBadge category={event.failure_category} />
                  <StatusBadge status={event.status} />
                  <span className="text-xs text-gray-500">{formatDistanceToNow(event.created_at)}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-xs">
                  <Field label="Charge ID" value={event.original_charge_id.substring(0, 18)} mono />
                  <Field label="Customer" value={event.customer_name || event.customer_email || "—"} />
                  <Field label="Amount" value={event.amount ? `₹${event.amount.toLocaleString("en-IN")}` : "—"} />
                  <Field label="Error Code" value={event.raw_error_code || "—"} mono />
                  <Field label="LTV" value={`₹${event.customer_ltv.toLocaleString("en-IN")}`} />
                  <Field label="Churn Risk" value={`${(event.churn_risk_score * 100).toFixed(0)}%`}
                    highlight={event.churn_risk_score > 0.7 ? "red" : event.churn_risk_score > 0.4 ? "yellow" : "green"} />
                  <Field label="Touchpoints" value={String(event.touchpoint_count)} />
                  <Field label="Attribution" value={event.attribution_status.replace("_", " ")} />
                </div>
              </div>
              {/* Retry schedule pill */}
              {Array.isArray(event.retry_schedule) && event.retry_schedule.length > 0 && (
                <div className="shrink-0 bg-violet-900/20 border border-violet-500/30 rounded-lg px-3 py-2 text-xs text-right">
                  <p className="text-violet-300 font-medium">Next Retry</p>
                  <p className="text-gray-300 mt-0.5">
                    {new Date(event.retry_schedule[0].scheduled_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                  </p>
                  <p className="text-violet-400 font-semibold">
                    {Math.round((event.retry_schedule[0].confidence_score ?? 0) * 100)}% confidence
                  </p>
                </div>
              )}
              {event.settlement_amount && (
                <div className="shrink-0 bg-green-900/20 border border-green-500/30 rounded-lg px-3 py-2 text-xs text-right">
                  <p className="text-green-300 font-medium">Recovered</p>
                  <p className="text-green-400 font-bold text-base mt-0.5">₹{event.settlement_amount.toLocaleString("en-IN")}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Field({ label, value, mono, highlight }: {
  label: string; value: string; mono?: boolean; highlight?: "red" | "yellow" | "green";
}) {
  const valueClass = highlight === "red" ? "text-red-400" : highlight === "yellow" ? "text-yellow-400" : highlight === "green" ? "text-green-400" : "text-gray-300";
  return (
    <div>
      <span className="text-gray-500">{label}: </span>
      <span className={`${mono ? "font-mono" : ""} ${valueClass}`}>{value}</span>
    </div>
  );
}
