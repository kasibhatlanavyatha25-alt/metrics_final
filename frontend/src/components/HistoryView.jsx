import React, { useState, useEffect } from 'react';
import { 
  Layers, Trash2, ChevronRight, Activity, 
  GitBranch, Calendar, FileCode2
} from 'lucide-react';
import { fetchProjectsList, deleteProject } from '../api';

export default function HistoryView({ onSelectProject, activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await fetchProjectsList();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm(`Delete analysis record #${id}?`)) return;
    try {
      await deleteProject(id);
      loadProjects();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-moderate font-mono">SQLite Repository Store</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Analysis Run History & Analyzed Repositories
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Switch between previously analyzed software repositories or manage historical execution runs.
          </p>
        </div>
      </div>

      {/* Projects List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.length > 0 ? (
          projects.map((p) => {
            const isActive = p.id === activeProjectId;
            return (
              <div 
                key={p.id}
                onClick={() => onSelectProject(p.id)}
                className={`glass-panel p-5 space-y-4 cursor-pointer transition-all ${
                  isActive 
                    ? 'border-indigo-500 bg-indigo-950/30 shadow-lg shadow-indigo-500/20' 
                    : 'hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-base truncate">{p.name}</span>
                  <span className={`badge badge-${(p.status || 'healthy').toLowerCase()}`}>
                    {p.status || 'ANALYZED'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block">Health Score</span>
                    <span className="text-emerald-400 font-bold text-sm">{p.health_score || 0}/100</span>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 block">ESDI Risk</span>
                    <span className="text-amber-400 font-bold text-sm">{p.esdi_score || 0}/100</span>
                  </div>
                </div>

                <div className="text-xs text-slate-400 font-mono space-y-1">
                  <div>Versions: <span className="text-slate-200">{p.total_versions}</span> | Classes: <span className="text-slate-200">{p.total_classes}</span></div>
                  <div>Commits: <span className="text-slate-200">{p.total_commits?.toLocaleString()}</span></div>
                  <div className="text-[11px] text-slate-500">
                    Analyzed: {p.created_at ? new Date(p.created_at).toLocaleString() : 'N/A'}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-850 text-xs">
                  <button 
                    onClick={(e) => handleDelete(e, p.id)}
                    className="text-slate-500 hover:text-rose-400 p-1.5 rounded transition-colors"
                    title="Delete project record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <span className="text-indigo-400 font-semibold flex items-center gap-1">
                    {isActive ? 'Active Workspace' : 'Load Dashboard'} <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-3 text-center py-16 text-slate-500">
            No previous analysis runs found. Click "Analyze New Repository" to start.
          </div>
        )}
      </div>
    </div>
  );
}
