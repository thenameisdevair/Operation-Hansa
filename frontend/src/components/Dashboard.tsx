import { useEffect, useState } from "react";
import { DollarSign, CheckCircle, Layers, TrendingUp, Cpu } from "lucide-react";
import type { Stats } from "../types";

const CATEGORY_COLORS: Record<string, string> = {
  research: "bg-blue-500",
  writing: "bg-purple-500",
  coding: "bg-yellow-500",
  marketing: "bg-pink-500",
};

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}

function StatCard({ icon, label, value, sub, accent = "text-hansa-400" }: StatCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start gap-4">
      <div className={`mt-0.5 ${accent}`}>{icon}</div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
        <p className={`text-2xl font-bold ${accent}`}>{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const load = () =>
      fetch("/api/stats")
        .then((r) => r.json())
        .then(setStats)
        .catch(() => null);
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  if (!stats) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl h-24" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Layers size={20} />}
          label="Tasks Completed"
          value={stats.total_tasks}
          sub="all time"
        />
        <StatCard
          icon={<DollarSign size={20} />}
          label="USDC Earned"
          value={`$${stats.total_usdc_earned}`}
          sub="quality-passed tasks"
          accent="text-green-400"
        />
        <StatCard
          icon={<TrendingUp size={20} />}
          label="Success Rate"
          value={`${stats.success_rate}%`}
          sub="QC pass rate"
          accent="text-blue-400"
        />
        <StatCard
          icon={<Cpu size={20} />}
          label="Agent ID"
          value={stats.agent_id.split("-").slice(-2).join("-")}
          sub="via TokenRouter"
          accent="text-purple-400"
        />
      </div>

      {Object.keys(stats.categories).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Task Breakdown</p>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(stats.categories).map(([cat, count]) => (
              <div key={cat} className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${CATEGORY_COLORS[cat] ?? "bg-gray-500"}`} />
                <span className="text-sm text-gray-300 capitalize">{cat}</span>
                <span className="text-sm font-bold text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
