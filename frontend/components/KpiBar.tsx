import { DashboardSummary } from "@/lib/api";
import { TrendingUp, RefreshCcw, Users, IndianRupee } from "lucide-react";

interface Props { summary: DashboardSummary }

function KpiCard({ title, value, sub, icon: Icon, accent }: {
  title: string; value: string; sub: string;
  icon: React.ElementType; accent: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start gap-4">
      <div className={`p-2.5 rounded-lg ${accent}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{title}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
        <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
      </div>
    </div>
  );
}

export default function KpiBar({ summary }: Props) {
  const fmt = (n: number) =>
    n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : n >= 1000 ? `₹${(n / 1000).toFixed(1)}K` : `₹${n.toFixed(0)}`;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard
        title="Total Recovered"
        value={fmt(summary.total_amount_recovered)}
        sub={`${summary.total_recovered} of ${summary.total_events} events`}
        icon={IndianRupee}
        accent="bg-green-600"
      />
      <KpiCard
        title="Gross Recovery Rate"
        value={`${summary.gross_recovery_rate}%`}
        sub="Target ≥ 42% on soft declines"
        icon={TrendingUp}
        accent="bg-violet-600"
      />
      <KpiCard
        title="Active Interventions"
        value={String(summary.active_interventions)}
        sub="Events in pipeline"
        icon={RefreshCcw}
        accent="bg-blue-600"
      />
      <KpiCard
        title="Net Agent Recovery"
        value={fmt(summary.net_agent_recovery)}
        sub="Above organic baseline"
        icon={Users}
        accent="bg-indigo-600"
      />
    </div>
  );
}
