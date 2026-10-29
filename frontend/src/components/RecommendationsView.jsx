import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Search, ArrowUpRight, CheckCircle2, 
  Target, AlertTriangle, Layers, BookOpen
} from 'lucide-react';
import { fetchProjectRecommendations } from '../api';

export default function RecommendationsView({ projectId }) {
  const [recommendations, setRecommendations] = useState([]);
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRecs() {
      try {
        setLoading(true);
        const data = await fetchProjectRecommendations(projectId, priorityFilter);
        setRecommendations(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadRecs();
  }, [projectId, priorityFilter]);

  const filteredRecs = recommendations.filter(r =>
    r.module_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.metric_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.recommended_action.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getPriorityBadge = (p) => {
    switch (p?.toUpperCase()) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-risky';
      case 'MEDIUM': return 'badge-moderate';
      default: return 'badge-healthy';
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-healthy animate-pulse">Explainable AI</span>
            <span className="text-xs text-slate-400 font-mono">Evidence-Backed Action Cards</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            AI-Based Software Metric Recommendations
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Prescriptive refactoring recommendations linked to actual metric deterioration trends and Software DNA mutation evidence.
          </p>
        </div>
      </div>

      {/* Filters & Search */}
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
              placeholder="Search recommendations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-9 text-xs py-2 bg-slate-900"
            />
          </div>
        </div>

        {/* SECTION 29: Recommendation Cards with Mandatory Format */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredRecs.length > 0 ? (
            filteredRecs.map((rec) => (
              <div 
                key={rec.id} 
                className="glass-panel p-6 space-y-4 border border-slate-800 hover:border-slate-700 transition-all shadow-lg"
              >
                {/* Card Header */}
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <span className={`badge ${getPriorityBadge(rec.priority)}`}>
                    Priority: {rec.priority}
                  </span>
                  <span className="font-mono text-xs font-bold text-white bg-slate-900 px-3 py-1 rounded-lg border border-slate-800">
                    {rec.module_name}
                  </span>
                </div>

                {/* Metric & Current Trend Row */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-slate-400 block">Metric</span>
                    <span className="text-white font-bold block mt-0.5">{rec.metric_name}</span>
                    <span className="text-indigo-400 font-mono text-sm block mt-1">Current: {rec.current_value}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-850">
                    <span className="text-slate-400 block">Observed Trend</span>
                    <span className="text-indigo-300 font-mono font-bold block mt-0.5">{rec.observed_trend}</span>
                    <span className="text-rose-400 font-mono text-xs block mt-1">
                      {rec.percentage_change > 0 ? '+' : ''}{rec.percentage_change}% (Mutation: {rec.mutation_severity})
                    </span>
                  </div>
                </div>

                {/* Target */}
                <div className="text-xs space-y-1 bg-indigo-950/20 p-3 rounded-lg border border-indigo-500/20">
                  <div className="flex items-center gap-1.5 text-indigo-300 font-semibold">
                    <Target className="w-4 h-4 text-indigo-400" />
                    Target
                  </div>
                  <p className="text-slate-200">{rec.target}</p>
                </div>

                {/* Reason */}
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-semibold block">Reason</span>
                  <p className="text-slate-300 leading-relaxed">{rec.reason}</p>
                </div>

                {/* Recommended Action */}
                <div className="text-xs space-y-1 bg-slate-950/80 p-3.5 rounded-lg border border-slate-800">
                  <span className="text-emerald-400 font-semibold block flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Recommended Action
                  </span>
                  <p className="text-slate-200 leading-relaxed mt-1">{rec.recommended_action}</p>
                </div>

                {/* Expected Benefit */}
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-semibold block">Expected Benefit</span>
                  <p className="text-slate-300 leading-relaxed">{rec.expected_benefit}</p>
                </div>

                {/* Evidence Footer */}
                <div className="pt-2 border-t border-slate-850 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Evidence:</span>
                  <span className="text-slate-400">{rec.evidence}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-2 text-center py-12 text-slate-500">
              No recommendations matching current priority filter.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
