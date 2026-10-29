import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Search, Filter, AlertCircle, CheckCircle2, 
  ArrowUpRight, ArrowDownRight, Layers, Sparkles
} from 'lucide-react';
import { fetchProjectMutations } from '../api';

export default function DNAMutationView({ projectId }) {
  const [mutations, setMutations] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMutations() {
      try {
        setLoading(true);
        const data = await fetchProjectMutations(projectId, severityFilter);
        setMutations(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadMutations();
  }, [projectId, severityFilter]);

  const filteredMutations = mutations.filter(m => 
    m.module_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.metric_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.reason.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const criticalCount = mutations.filter(m => m.severity === 'CRITICAL').length;
  const riskyCount = mutations.filter(m => m.severity === 'RISKY').length;
  const healthyCount = mutations.filter(m => m.severity === 'HEALTHY').length;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-critical animate-pulse">DNA Mutation Engine</span>
            <span className="text-xs text-slate-400 font-mono">Differential Metric Analysis</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Software DNA Mutation Report
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Detects significant evolutionary shifts (Deltas & % Changes) in metrics across consecutive versions and classifies severity.
          </p>
        </div>

        {/* Severity Count Summary Badges */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="px-3 py-2 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300">
            <span className="font-bold">{criticalCount}</span> Critical
          </div>
          <div className="px-3 py-2 rounded-lg bg-amber-950/40 border border-amber-800 text-amber-300">
            <span className="font-bold">{riskyCount}</span> Risky
          </div>
          <div className="px-3 py-2 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300">
            <span className="font-bold">{healthyCount}</span> Healthy
          </div>
        </div>
      </div>

      {/* Filter Toolbar & Search */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          {/* Severity Filters */}
          <div className="flex items-center gap-2">
            {['ALL', 'CRITICAL', 'RISKY', 'HEALTHY'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                  severityFilter === sev
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input 
              type="text"
              placeholder="Search module, metric, or reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-9 text-xs py-2 bg-slate-900"
            />
          </div>
        </div>

        {/* Mutation Table */}
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Version</th>
                <th>Source Unit / Module</th>
                <th>Metric</th>
                <th className="text-right">Previous</th>
                <th className="text-right">Current</th>
                <th className="text-right">Change %</th>
                <th>Severity</th>
                <th>Mutation Rationale & Evidence</th>
              </tr>
            </thead>
            <tbody>
              {filteredMutations.length > 0 ? (
                filteredMutations.map((m) => (
                  <tr key={m.id}>
                    <td className="font-mono font-bold text-indigo-300">{m.version_tag}</td>
                    <td className="font-mono font-semibold text-white">
                      {m.module_name}
                      {m.is_combined && <span className="badge badge-critical ml-2 text-[9px]">COMBINED</span>}
                    </td>
                    <td className="text-xs text-slate-300 font-medium">{m.metric_name}</td>
                    <td className="font-mono text-right text-slate-400">{m.previous_value}</td>
                    <td className="font-mono text-right font-bold text-white">{m.current_value}</td>
                    <td className="font-mono text-right font-semibold">
                      <span className={`flex items-center justify-end gap-0.5 ${
                        m.is_deterioration ? 'text-rose-400' : 'text-emerald-400'
                      }`}>
                        {m.percentage_change > 0 ? '+' : ''}{m.percentage_change}%
                        {m.percentage_change > 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        m.severity === 'CRITICAL' ? 'badge-critical' :
                        m.severity === 'RISKY' ? 'badge-risky' : 'badge-healthy'
                      }`}>
                        {m.severity}
                      </span>
                    </td>
                    <td className="text-xs text-slate-300 max-w-md leading-relaxed">
                      {m.reason}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-slate-500">
                    No mutations matching current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
