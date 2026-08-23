"use client";
import { useState } from "react";
import { api, SimulateResult } from "@/lib/api";
import { CategoryBadge, StatusBadge, AttributionBadge } from "@/components/Badges";
import { Zap, Play, RefreshCcw, CheckCircle } from "lucide-react";

const SCENARIOS = [
  { key: "soft_decline",    label: "Soft Decline",       desc: "Insufficient Funds",       color: "border-yellow-500/40 hover:border-yellow-400/70", icon: "💳" },
  { key: "hard_decline",    label: "Hard Decline",        desc: "Card Blocked / Do Not Honor", color: "border-red-500/40 hover:border-red-400/70",    icon: "🚫" },
  { key: "expired_card",    label: "Expired Card",        desc: "Credential Expiry",        color: "border-orange-500/40 hover:border-orange-400/70", icon: "⏰" },
  { key: "mandate_failure", label: "Mandate Failure",     desc: "UPI Autopay / e-Mandate",  color: "border-purple-500/40 hover:border-purple-400/70", icon: "📱" },
  { key: "cart_abandoned",  label: "Cart Abandoned",      desc: "High-Intent Checkout",     color: "border-blue-500/40 hover:border-blue-400/70",     icon: "🛒" },
  { key: "b2b_overdue",     label: "B2B Overdue",         desc: "Net-30 Invoice Aging",     color: "border-pink-500/40 hover:border-pink-400/70",     icon: "📄" },
];

const AMOUNTS = [499, 999, 2499, 4999, 9999, 24999];

export default function SimulatorPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [amount, setAmount] = useState(4999);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulateResult | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState<{ fired: number } | null>(null);
  const [recovering, setRecovering] = useState(false);
  const [recovered, setRecovered] = useState(false);

  const fire = async () => {
    if (!selected) return;
    setLoading(true);
    setResult(null);
    setRecovered(false);
    try {
      const r = await api.simulateEvent({ scenario: selected, amount });
      setResult(r);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fireRecovery = async () => {
    if (!result) return;
    setRecovering(true);
    try {
      await api.simulateRecovery(result.recovery_id);
      setRecovered(true);
    } finally {
      setRecovering(false);
    }
  };

  const fireBulk = async () => {
    setBulkLoading(true);
    setBulkResult(null);
    try {
      const r = await api.simulateBulk(25);
      setBulkResult({ fired: r.fired });
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Event Simulator</h1>
        <p className="text-sm text-gray-400 mt-1">Fire synthetic Razorpay payment failure events to demo the full recovery pipeline</p>
      </div>

      {/* Scenario grid */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Select Scenario</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {SCENARIOS.map((s) => (
            <button key={s.key}
              onClick={() => setSelected(s.key)}
              className={`text-left p-4 rounded-xl border bg-gray-900 transition-all ${s.color} ${selected === s.key ? "ring-2 ring-violet-500 border-violet-500" : ""}`}>
              <p className="text-xl mb-2">{s.icon}</p>
              <p className="text-sm font-semibold text-white">{s.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{s.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Amount selector */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Amount</p>
        <div className="flex gap-2 flex-wrap">
          {AMOUNTS.map((a) => (
            <button key={a}
              onClick={() => setAmount(a)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${amount === a ? "bg-violet-600 border-violet-500 text-white" : "bg-gray-900 border-gray-700 text-gray-300 hover:border-gray-500"}`}>
              ₹{a.toLocaleString("en-IN")}
            </button>
          ))}
        </div>
      </div>

      {/* Fire button */}
      <div className="flex items-center gap-3">
        <button onClick={fire} disabled={!selected || loading}
          className="flex items-center gap-2 px-6 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold text-white transition-colors">
          {loading ? <RefreshCcw size={16} className="animate-spin" /> : <Zap size={16} />}
          {loading ? "Processing..." : "Fire Event"}
        </button>
        <button onClick={fireBulk} disabled={bulkLoading}
          className="flex items-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl text-sm text-gray-300 transition-colors disabled:opacity-50">
          {bulkLoading ? <RefreshCcw size={14} className="animate-spin" /> : <Play size={14} />}
          Bulk Seed (25 events)
        </button>
        {bulkResult && (
          <span className="text-sm text-green-400">✓ Seeded {bulkResult.fired} events</span>
        )}
      </div>

      {/* Result panel */}
      {result && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <p className="text-sm font-semibold text-white">Pipeline Result</p>
              <CategoryBadge category={result.failure_category} />
              <StatusBadge status={result.status} />
              <AttributionBadge status={result.attribution_status} />
            </div>
            {!recovered && result.status !== "HOLDOUT" && (
              <button onClick={fireRecovery} disabled={recovering}
                className="flex items-center gap-2 px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded-lg text-xs text-white transition-colors">
                {recovering ? <RefreshCcw size={12} className="animate-spin" /> : <CheckCircle size={12} />}
                Simulate Recovery
              </button>
            )}
            {recovered && <span className="text-xs text-green-400 font-medium">✓ Marked as Recovered</span>}
          </div>
          <div className="p-5 grid grid-cols-2 gap-5 text-sm">
            {/* Left: details */}
            <div className="space-y-3">
              <Row label="Recovery ID" value={<span className="font-mono text-xs">{result.recovery_id}</span>} />
              <Row label="Charge ID" value={<span className="font-mono text-xs">{result.charge_id}</span>} />
              <Row label="Customer LTV" value={`₹${result.customer_ltv.toLocaleString("en-IN")}`} />
              <Row label="Churn Risk" value={
                <span className={result.churn_risk_score > 0.7 ? "text-red-400" : "text-green-400"}>
                  {(result.churn_risk_score * 100).toFixed(1)}%
                </span>
              } />
            </div>
            {/* Right: retry schedule */}
            <div>
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">ML Retry Schedule</p>
              {Array.isArray(result.retry_schedule) && result.retry_schedule.length > 0 ? (
                <div className="space-y-2">
                  {result.retry_schedule.map((slot, i) => (
                    <div key={i} className="bg-gray-800 rounded-lg px-3 py-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-300">{new Date(slot.scheduled_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                        <span className="text-violet-400 font-semibold">{(slot.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                      <p className="text-gray-500 mt-0.5">{slot.window_label}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-xs">No retry scheduled (hard decline or non-retriable)</p>
              )}
            </div>
          </div>
          {/* Intervention trail */}
          {Array.isArray(result.intervention_trail) && result.intervention_trail.length > 0 && (
            <div className="border-t border-gray-800 px-5 py-4">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Intervention Trail</p>
              <div className="space-y-2">
                  {result.intervention_trail.map((item, i) => (
                    <div key={i} className="flex gap-3 text-xs">
                      <span className="text-gray-500 shrink-0 font-mono">{new Date(item.timestamp + "Z").toLocaleTimeString()}</span>
                      <span className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-300 shrink-0">{item.channel}</span>
                      <span className="text-gray-400 truncate">{item.message_preview}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-gray-400 text-xs">{label}</span>
      <span className="text-white text-xs text-right">{value}</span>
    </div>
  );
}
