"use client";
import { useEffect, useState, useCallback } from "react";
import { api, DashboardSummary, TrendPoint } from "@/lib/api";
import KpiBar from "@/components/KpiBar";
import RecoveryFeed from "@/components/RecoveryFeed";
import { RecoveryTrendChart, CategoryBreakdownChart, AttributionDonut } from "@/components/Charts";
import { RefreshCcw } from "lucide-react";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const load = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        api.getDashboardSummary(),
        api.getRecoveryTrend(7),
      ]);
      setSummary(s);
      setTrend(t);
      setLastRefresh(new Date());
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // Auto-refresh every 8 seconds for live feel
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-gray-400">
          <RefreshCcw size={18} className="animate-spin" />
          <span className="text-sm">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (!summary) return <p className="text-red-400 text-sm">Failed to connect to backend. Is the server running on :8000?</p>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Revenue Recovery Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">
            Autonomous AI engine · Real-time monitoring · Razorpay Buildathon 2025
          </p>
        </div>
        <div className="text-right">
          <button onClick={load} className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs text-gray-300 transition-colors">
            <RefreshCcw size={12} />
            Refresh
          </button>
          <p className="text-xs text-gray-600 mt-1">
            Last updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* Attribution formula callout */}
      <div className="bg-violet-900/20 border border-violet-500/30 rounded-xl px-5 py-3 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-violet-400 shrink-0" />
        <p className="text-xs text-violet-300">
          <span className="font-semibold">Holdout Attribution:</span>{" "}
          Net Agent Recovery = Total Recovered − (Control Rate × Treatment Total) ={" "}
          <span className="font-mono font-semibold">
            ₹{summary.net_agent_recovery.toLocaleString("en-IN")}
          </span>{" "}
          above organic baseline · 5% holdout group ({summary.holdout_count} events)
        </p>
      </div>

      {/* KPIs */}
      <KpiBar summary={summary} />

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <RecoveryTrendChart data={trend} />
        </div>
        <AttributionDonut summary={summary} />
      </div>

      {/* Category breakdown + feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <CategoryBreakdownChart breakdown={summary.category_breakdown} />
        </div>
        <div className="lg:col-span-2">
          <RecoveryFeed events={summary.recent_events} />
        </div>
      </div>
    </div>
  );
}
