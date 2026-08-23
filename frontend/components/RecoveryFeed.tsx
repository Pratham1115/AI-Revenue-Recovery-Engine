import { RecoveryEvent } from "@/lib/api";
import { CategoryBadge, StatusBadge } from "@/components/Badges";
import { formatDistanceToNow } from "@/lib/utils";

interface Props { events: RecoveryEvent[] }

export default function RecoveryFeed({ events }: Props) {
  if (events.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
        <p className="text-gray-500 text-sm">No events yet — use the Simulator to fire some!</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Live Recovery Feed</h3>
        <span className="text-xs text-gray-500">{events.length} recent events</span>
      </div>
      <div className="divide-y divide-gray-800">
        {events.map((event) => (
          <div key={event.recovery_id} className="px-5 py-3.5 hover:bg-gray-800/50 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <CategoryBadge category={event.failure_category} />
                  <StatusBadge status={event.status} />
                </div>
                <div className="mt-1.5 flex items-center gap-3 text-xs text-gray-400">
                  <span className="font-mono truncate max-w-[140px]">{event.original_charge_id}</span>
                  <span>·</span>
                  <span>{event.customer_name || event.customer_email || "Unknown"}</span>
                  {event.amount && (
                    <>
                      <span>·</span>
                      <span className="text-gray-300 font-medium">
                        ₹{event.amount.toLocaleString("en-IN")}
                      </span>
                    </>
                  )}
                </div>
                {/* Last intervention */}
                {Array.isArray(event.intervention_trail) && event.intervention_trail.length > 0 && (
                  <p className="mt-1 text-xs text-gray-500 truncate">
                    {(() => {
                      const last = event.intervention_trail[event.intervention_trail.length - 1];
                      return `${last.channel ?? ""} · ${(last.message_preview ?? "").substring(0, 60)}...`;
                    })()}
                  </p>
                )}
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-gray-500">{formatDistanceToNow(event.created_at)}</p>
                {event.settlement_amount && (
                  <p className="text-xs text-green-400 font-medium mt-0.5">
                    Recovered ₹{event.settlement_amount.toLocaleString("en-IN")}
                  </p>
                )}
                {event.churn_risk_score > 0.7 && !event.settlement_amount && (
                  <p className="text-xs text-red-400 mt-0.5">High churn risk</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
