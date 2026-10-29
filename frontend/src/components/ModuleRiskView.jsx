import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Search, Filter, HelpCircle, 
  ChevronRight, AlertTriangle, X, Dna, Activity
} from 'lucide-react';
import { fetchProjectRisks } from '../api';

export default function ModuleRiskView({ projectId }) {
  const [risks, setRisks] = useState([]);
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModule, setSelectedModule] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRisks() {
      try {
        setLoading(true);
        const data = await fetchProjectRisks(projectId, priorityFilter);
        setRisks(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadRisks();
  }, [projectId, priorityFilter]);

  const filteredRisks = risks.filter(r => 
    r.class_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (r.package_name && r.package_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    r.top_risk_metric.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-critical">Module Risk Engine</span>
            <span className="text-xs text-slate-400 font-mono">Source-Level Risk Synthesis</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Module / Source Unit Risk Analysis
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluates individual source units and modules based on complexity, coupling, cohesion, code size, mutations, and ESDI contribution.
          </p>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                  priorityFilter === p
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                    : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input 
              type="text"
              placeholder="Search source unit, module, or metric..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-9 text-xs py-2 bg-slate-900"
            />
          </div>
        </div>

        {/* Risk Table */}
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Source Unit / Module</th>
                <th>Risk Score</th>
                <th>Priority</th>
                <th>Top Risk Metric</th>
                <th>Mutation Severity</th>
                <th>ESDI Contribution</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRisks.length > 0 ? (
                filteredRisks.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span className="font-mono font-bold text-white block">{r.class_name}</span>
                      <span className="text-[11px] text-slate-500 font-mono block">{r.package_name}</span>
                    </td>
                    <td className="font-mono text-base font-bold text-amber-400">
                      {r.risk_score} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                    </td>
                    <td>
                      <span className={`badge ${
                        r.priority === 'CRITICAL' ? 'badge-critical' :
                        r.priority === 'HIGH' ? 'badge-risky' :
                        r.priority === 'MEDIUM' ? 'badge-moderate' : 'badge-healthy'
                      }`}>
                        {r.priority}
                      </span>
                    </td>
                    <td className="text-xs text-slate-300 font-medium">{r.top_risk_metric}</td>
                    <td>
                      <span className={`badge ${
                        r.recent_mutation_severity === 'CRITICAL' ? 'badge-critical' :
                        r.recent_mutation_severity === 'RISKY' ? 'badge-risky' : 'badge-healthy'
                      }`}>
                        {r.recent_mutation_severity || 'HEALTHY'}
                      </span>
                    </td>
                    <td className="font-mono text-xs text-indigo-300">
                      +{r.esdi_contribution}%
                    </td>
                    <td>
                      <button 
                        onClick={() => setSelectedModule(r)}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1 cursor-pointer"
                      >
                        <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
                        Why High Risk?
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-slate-500">
                    No source units matching current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* WHY-EXPLAINER MODAL (Explainability Drawer) */}
      {selectedModule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-xl glass-panel-glow bg-slate-900 border border-slate-700 p-6 md:p-8 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`badge ${
                    selectedModule.priority === 'CRITICAL' ? 'badge-critical' :
                    selectedModule.priority === 'HIGH' ? 'badge-risky' : 'badge-moderate'
                  }`}>
                    {selectedModule.priority} PRIORITY
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Risk: {selectedModule.risk_score}/100</span>
                </div>
                <h2 className="text-lg font-bold text-white font-mono">{selectedModule.class_name}</h2>
              </div>
              <button 
                onClick={() => setSelectedModule(null)}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Why Question & Evidence */}
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-2">
                <span className="font-bold text-indigo-300 uppercase tracking-wider block">
                  Why is this module classified as {selectedModule.priority} risk?
                </span>
                <p className="text-slate-200 leading-relaxed text-sm">
                  {selectedModule.explanation}
                </p>
              </div>

              {/* Primary Factors Checklist */}
              {selectedModule.primary_factors && selectedModule.primary_factors.length > 0 && (
                <div className="space-y-2">
                  <span className="font-bold text-slate-300 uppercase tracking-wider block">
                    Empirical Contributing Factors
                  </span>
                  <div className="space-y-2">
                    {selectedModule.primary_factors.map((f, i) => (
                      <div key={i} className="p-3 rounded-lg bg-slate-950/80 border border-slate-850 flex items-start gap-2.5">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold text-white block">{f.metric}: {f.value}</span>
                          <span className="text-slate-400 leading-relaxed block mt-0.5">{f.detail}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button 
                onClick={() => setSelectedModule(null)}
                className="btn-primary text-xs px-4 py-2"
              >
                Close Explainer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
