import React from 'react';
import { ClassMutationAnalysis, MetricVector } from '../types';
import { Layers, TrendingUp, Zap, Clock, ShieldAlert } from 'lucide-react';

interface MutationMatrixProps {
  mutationAnalysis?: ClassMutationAnalysis;
  currentMetrics?: MetricVector;
  className?: string;
}

export const MutationMatrix: React.FC<MutationMatrixProps> = ({
  mutationAnalysis,
  currentMetrics,
  className = 'PaymentService',
}) => {
  const mutations = mutationAnalysis?.metric_mutations || {};

  const getMetricCurrentVal = (mKey: string): string => {
    if (!currentMetrics) return '-';
    switch (mKey.toLowerCase()) {
      case 'loc': return String(currentMetrics.loc);
      case 'cc': return String(currentMetrics.cc);
      case 'wmc': return String(currentMetrics.wmc);
      case 'cbo': return String(currentMetrics.cbo);
      case 'lcom': return currentMetrics.lcom.toFixed(2);
      default: return '-';
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/50 glow-danger';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/50';
      case 'MEDIUM':
        return 'bg-sky-500/20 text-sky-300 border-sky-500/50';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50';
    }
  };

  return (
    <div className="glass-card rounded-xl p-5 border border-slate-800">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-sky-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Five-Dimensional Mutation Matrix
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Module: <span className="text-indigo-400 font-bold">{className}</span> ({mutationAnalysis?.version_label || 'V5'})
        </span>
      </div>

      <div className="overflow-x-auto mt-4">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px] bg-slate-900/50">
              <th className="py-2.5 px-3">Metric</th>
              <th className="py-2.5 px-3">Current Val</th>
              <th className="py-2.5 px-3">Magnitude</th>
              <th className="py-2.5 px-3">Persistence</th>
              <th className="py-2.5 px-3">Acceleration</th>
              <th className="py-2.5 px-3">Co-occur</th>
              <th className="py-2.5 px-3">Recency</th>
              <th className="py-2.5 px-3">Risk Score</th>
              <th className="py-2.5 px-3 text-right">Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {Object.entries(mutations).map(([mKey, score]) => {
              const currentVal = getMetricCurrentVal(mKey);
              return (
                <tr key={mKey} className="hover:bg-slate-800/30 transition">
                  <td className="py-2.5 px-3 font-bold text-white uppercase">{mKey}</td>
                  <td className="py-2.5 px-3 text-sky-300 font-semibold">{currentVal}</td>
                  <td className="py-2.5 px-3 text-slate-300">{score.magnitude.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-300">{score.persistence.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-300">{score.acceleration.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-300">{score.cooccurrence.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-300">{score.recency.toFixed(2)}</td>
                  <td className="py-2.5 px-3">
                    <span className="font-bold text-white">{score.risk.toFixed(2)}</span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${getSeverityBadge(score.severity)}`}>
                      {score.severity}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
