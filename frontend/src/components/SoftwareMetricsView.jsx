import React, { useState, useEffect } from 'react';
import { 
  FileCode2, Search, ArrowUpDown, ChevronDown, 
  BarChart3, Activity, Layers, Download
} from 'lucide-react';
import { fetchProjectMetrics, fetchProjectVersions } from '../api';

export default function SoftwareMetricsView({ projectId }) {
  const [versions, setVersions] = useState([]);
  const [selectedVersionId, setSelectedVersionId] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('cyclomatic_complexity');
  const [sortAsc, setSortAsc] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const vers = await fetchProjectVersions(projectId);
        setVersions(vers);
        const initialVerId = vers.length > 0 ? vers[vers.length - 1].id : null;
        setSelectedVersionId(initialVerId);

        if (initialVerId) {
          const data = await fetchProjectMetrics(projectId, initialVerId);
          setMetricsData(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  const handleVersionChange = async (verId) => {
    setSelectedVersionId(verId);
    setLoading(true);
    try {
      const data = await fetchProjectMetrics(projectId, verId);
      setMetricsData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const classes = metricsData?.class_metrics || [];
  const filteredClasses = classes
    .filter(c => c.class_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                 c.package_name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const valA = a[sortField] ?? 0;
      const valB = b[sortField] ?? 0;
      return sortAsc ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
    });

  const pm = metricsData?.project_metric;
  const history = metricsData?.historical_summary || [];

  return (
    <div className="space-y-8 pb-12">
      {/* Header & Controls */}
      <div className="glass-panel p-6 border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileCode2 className="w-5 h-5 text-indigo-400" />
            Software Metrics Extraction & Source Explorer
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Unified Software Quality Metrics (LOC, Complexity, Coupling, Cohesion) extracted at source unit, module, and project levels.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-400">Snapshot Version:</span>
          <select 
            value={selectedVersionId || ''} 
            onChange={(e) => handleVersionChange(Number(e.target.value))}
            className="form-input text-xs py-2 px-3 bg-slate-900 border-slate-700 text-white font-mono cursor-pointer"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.version_tag} ({new Date(v.commit_date).toLocaleDateString()})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Project-Level Metric Aggregations */}
      {pm && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Total LOC</span>
            <span className="text-lg font-bold font-mono text-cyan-400">{pm.total_loc?.toLocaleString()}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Avg Complexity (CC)</span>
            <span className="text-lg font-bold font-mono text-indigo-400">{pm.avg_complexity}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Avg WMC</span>
            <span className="text-lg font-bold font-mono text-indigo-400">{pm.avg_wmc}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Avg CBO (Coupling)</span>
            <span className="text-lg font-bold font-mono text-amber-400">{pm.avg_cbo}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Avg RFC</span>
            <span className="text-lg font-bold font-mono text-amber-400">{pm.avg_rfc}</span>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Avg LCOM (Cohesion)</span>
            <span className="text-lg font-bold font-mono text-rose-400">{pm.avg_lcom}</span>
          </div>
        </div>
      )}

      {/* SECTION 3: Metric Evolution Charts (Multi-Version Historical Trends) */}
      {history.length > 1 && (
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-indigo-400" />
            Metric Evolution Across Versions (Historical Trajectory)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Complexity Trend */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400 font-semibold block">Complexity (CC) vs Version</span>
              <div className="flex items-end justify-between h-24 gap-2 pt-4">
                {history.map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-indigo-300">{h.avg_complexity}</span>
                    <div 
                      className="w-full bg-indigo-500 rounded-t"
                      style={{ height: `${Math.min(100, Math.max(10, (h.avg_complexity / 20) * 100))}%` }}
                    />
                    <span className="text-[9px] font-mono text-slate-500 truncate w-full text-center">{h.version_tag}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CBO Trend */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400 font-semibold block">Coupling (CBO) vs Version</span>
              <div className="flex items-end justify-between h-24 gap-2 pt-4">
                {history.map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-cyan-300">{h.avg_cbo}</span>
                    <div 
                      className="w-full bg-cyan-500 rounded-t"
                      style={{ height: `${Math.min(100, Math.max(10, (h.avg_cbo / 15) * 100))}%` }}
                    />
                    <span className="text-[9px] font-mono text-slate-500 truncate w-full text-center">{h.version_tag}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* LCOM Trend */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400 font-semibold block">Lack of Cohesion (LCOM) vs Version</span>
              <div className="flex items-end justify-between h-24 gap-2 pt-4">
                {history.map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-rose-300">{h.avg_lcom}</span>
                    <div 
                      className="w-full bg-rose-500 rounded-t"
                      style={{ height: `${Math.min(100, Math.max(10, h.avg_lcom * 100))}%` }}
                    />
                    <span className="text-[9px] font-mono text-slate-500 truncate w-full text-center">{h.version_tag}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* LOC Trend */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
              <span className="text-xs text-slate-400 font-semibold block">Lines of Code (LOC) vs Version</span>
              <div className="flex items-end justify-between h-24 gap-2 pt-4">
                {history.map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-emerald-300">{h.total_loc}</span>
                    <div 
                      className="w-full bg-emerald-500 rounded-t"
                      style={{ height: `${Math.min(100, Math.max(10, (h.total_loc / (history[history.length-1].total_loc * 1.2)) * 100))}%` }}
                    />
                    <span className="text-[9px] font-mono text-slate-500 truncate w-full text-center">{h.version_tag}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Class / Source Unit Metrics Table */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input 
              type="text"
              placeholder="Search source units, classes, or modules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-9 text-xs py-2 bg-slate-900"
            />
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing {filteredClasses.length} of {classes.length} source units
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('class_name')} className="cursor-pointer hover:text-white">
                  Source Unit / Module {sortField === 'class_name' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('loc')} className="cursor-pointer hover:text-white text-right">
                  LOC {sortField === 'loc' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('cyclomatic_complexity')} className="cursor-pointer hover:text-white text-right">
                  Complexity {sortField === 'cyclomatic_complexity' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('wmc')} className="cursor-pointer hover:text-white text-right">
                  WMC {sortField === 'wmc' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('cbo')} className="cursor-pointer hover:text-white text-right">
                  CBO {sortField === 'cbo' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('rfc')} className="cursor-pointer hover:text-white text-right">
                  RFC {sortField === 'rfc' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('lcom')} className="cursor-pointer hover:text-white text-right">
                  LCOM {sortField === 'lcom' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('dit')} className="cursor-pointer hover:text-white text-right">
                  DIT {sortField === 'dit' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('noc')} className="cursor-pointer hover:text-white text-right">
                  NOC {sortField === 'noc' && (sortAsc ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('num_methods')} className="cursor-pointer hover:text-white text-right">
                  Methods / Funcs {sortField === 'num_methods' && (sortAsc ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredClasses.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className="font-mono font-semibold text-white block">{c.class_name}</span>
                    <span className="text-[11px] text-slate-500 font-mono block">{c.package_name}</span>
                  </td>
                  <td className="font-mono text-right text-slate-300">{c.loc}</td>
                  <td className="font-mono text-right font-bold text-indigo-300">{c.cyclomatic_complexity}</td>
                  <td className="font-mono text-right text-slate-300">{c.wmc}</td>
                  <td className="font-mono text-right font-bold text-amber-300">{c.cbo}</td>
                  <td className="font-mono text-right text-slate-300">{c.rfc}</td>
                  <td className="font-mono text-right font-bold text-rose-300">{c.lcom}</td>
                  <td className="font-mono text-right text-slate-400">{c.dit}</td>
                  <td className="font-mono text-right text-slate-400">{c.noc}</td>
                  <td className="font-mono text-right text-slate-400">{c.num_methods}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
