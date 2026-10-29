import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { DnaRecord } from '../types';
import { Activity } from 'lucide-react';

interface DnaTrajectoryViewerProps {
  trajectory: DnaRecord[];
  className?: string;
}

export const DnaTrajectoryViewer: React.FC<DnaTrajectoryViewerProps> = ({
  trajectory,
  className = 'PaymentService',
}) => {
  const [activeMetrics, setActiveMetrics] = useState({
    loc: true,
    cc: true,
    wmc: true,
    cbo: true,
    lcom: true,
  });

  const toggleMetric = (key: keyof typeof activeMetrics) => {
    setActiveMetrics((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Prepare chart data
  const chartData = trajectory.map((r) => ({
    version: r.version_label,
    loc: r.metrics.loc,
    cc: r.metrics.cc,
    wmc: r.metrics.wmc,
    cbo: r.metrics.cbo,
    lcom: Number((r.metrics.lcom * 100).toFixed(1)), // Scale LCOM to 0-100 for visual comparison
    rawLcom: r.metrics.lcom,
    shortSha: r.commit_sha.slice(0, 7),
  }));

  return (
    <div className="glass-card rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Evolutionary Software DNA Trajectory
            </h2>
            <div className="text-xs text-slate-400 font-mono">
              Target Class: <span className="text-sky-300 font-bold">{className}</span>
            </div>
          </div>
        </div>

        {/* Metric Series Toggles */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => toggleMetric('loc')}
            className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition ${
              activeMetrics.loc
                ? 'bg-slate-700 text-slate-200 border-slate-500'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            LOC
          </button>
          <button
            onClick={() => toggleMetric('cc')}
            className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition ${
              activeMetrics.cc
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/50'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            CC
          </button>
          <button
            onClick={() => toggleMetric('wmc')}
            className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition ${
              activeMetrics.wmc
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            WMC
          </button>
          <button
            onClick={() => toggleMetric('cbo')}
            className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition ${
              activeMetrics.cbo
                ? 'bg-sky-500/20 text-sky-300 border-sky-500/50'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            CBO
          </button>
          <button
            onClick={() => toggleMetric('lcom')}
            className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition ${
              activeMetrics.lcom
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/50'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            LCOM (x100)
          </button>
        </div>
      </div>

      {/* Recharts Line Chart */}
      <div className="h-64 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="version" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
                fontFamily: 'monospace',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />

            {activeMetrics.loc && (
              <Line type="monotone" dataKey="loc" stroke="#94a3b8" strokeWidth={2} dot={{ r: 4 }} name="LOC" />
            )}
            {activeMetrics.cc && (
              <Line type="monotone" dataKey="cc" stroke="#f43f5e" strokeWidth={3} dot={{ r: 5 }} name="CC (Cyclomatic Complexity)" />
            )}
            {activeMetrics.wmc && (
              <Line type="monotone" dataKey="wmc" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} name="WMC" />
            )}
            {activeMetrics.cbo && (
              <Line type="monotone" dataKey="cbo" stroke="#38bdf8" strokeWidth={2} dot={{ r: 4 }} name="CBO (Coupling)" />
            )}
            {activeMetrics.lcom && (
              <Line type="monotone" dataKey="lcom" stroke="#c084fc" strokeWidth={2} dot={{ r: 4 }} name="LCOM (x100)" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
