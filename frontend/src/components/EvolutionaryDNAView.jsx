import React, { useState, useEffect } from 'react';
import { 
  Dna, Layers, ArrowRight, ShieldCheck, Activity, 
  GitCommit, Clock, BarChart2, Info
} from 'lucide-react';
import { fetchProjectDNA } from '../api';

export default function EvolutionaryDNAView({ projectId }) {
  const [dnaList, setDnaList] = useState([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDNA() {
      try {
        setLoading(true);
        const data = await fetchProjectDNA(projectId);
        setDnaList(data);
        if (data.length > 0) {
          setSelectedIdx(data.length - 1);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadDNA();
  }, [projectId]);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading Evolutionary Software DNA...</div>;
  if (!dnaList || dnaList.length === 0) return <div className="p-8 text-center text-slate-400">No DNA profiles available.</div>;

  const currentDNA = dnaList[selectedIdx] || dnaList[0];

  const geneSpecs = [
    { key: "loc", label: "Lines of Code (LOC)", desc: "System volume & module size (θ=50.0, γ=0.05)", unit: "LOC", color: "#a78bfa" },
    { key: "cc", label: "Cyclomatic Complexity (CC)", desc: "McCabe linear independent decision paths (θ=10.0, γ=0.25)", unit: "Decision Paths", color: "#818cf8" },
    { key: "wmc", label: "Weighted Methods per Class (WMC)", desc: "Sum of cyclomatic complexity of declared methods (θ=20.0, γ=0.15)", unit: "Sum of CC", color: "#38bdf8" },
    { key: "cbo", label: "Coupling Between Objects (CBO)", desc: "Unique external classes / types coupled (θ=5.0, γ=0.30)", unit: "Coupled Types", color: "#f43f5e" },
    { key: "lcom", label: "Lack of Cohesion of Methods (LCOM)", desc: "Henderson-Sellers lack of cohesion (0.0=cohesive, 1.0=defect, θ=0.5, γ=2.0)", unit: "LCOM (0.0-1.0)", color: "#34d399" },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-moderate">Patent Analytical Construct (IDF-B)</span>
            <span className="text-xs text-slate-400 font-mono">Software DNA: D_t = (V_t, E_t, M_t)</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <Dna className="w-5 h-5 text-indigo-400" />
            Evolutionary Software DNA Profile & Historical Timeline
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Software DNA consists strictly of the 5 canonical structural metrics: LOC, CC, WMC, CBO, and LCOM across version snapshots.
          </p>
        </div>
      </div>

      {/* SECTION 2: Evolutionary Timeline (V1 -> V2 -> V3 -> Current) */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          Evolutionary DNA Timeline (Select Snapshot)
        </h2>

        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {dnaList.map((dna, idx) => {
            const isSelected = idx === selectedIdx;
            const isLatest = idx === dnaList.length - 1;
            return (
              <React.Fragment key={idx}>
                <button 
                  onClick={() => setSelectedIdx(idx)}
                  className={`p-4 rounded-xl border text-left min-w-[160px] transition-all cursor-pointer ${
                    isSelected 
                      ? 'bg-indigo-950/60 border-indigo-500 shadow-lg shadow-indigo-500/20 text-white' 
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-mono font-bold text-indigo-300">{dna.version_tag}</span>
                    {isLatest && <span className="badge badge-healthy text-[9px]">LATEST</span>}
                  </div>
                  <div className="text-xs text-slate-400 font-mono">
                    {dna.commit_date ? new Date(dna.commit_date).toLocaleDateString() : 'Snapshot'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-2 font-mono">
                    LOC: <span className="text-purple-400 font-semibold">{dna.loc}</span> | CC: <span className="text-indigo-400 font-semibold">{dna.cc}</span>
                  </div>
                </button>

                {idx < dnaList.length - 1 && (
                  <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* DNA Profile Breakdown for Selected Version */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {geneSpecs.map((g) => {
          const val = currentDNA[g.key] ?? 0;
          return (
            <div key={g.key} className="glass-panel p-5 space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">{g.label}</span>
                <span className="text-xs font-mono text-slate-400">{g.unit}</span>
              </div>
              <div className="text-3xl font-extrabold font-mono text-white" style={{ color: g.color }}>
                {typeof val === 'number' ? (val % 1 !== 0 ? val.toFixed(2) : val.toLocaleString()) : val}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {g.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* 5 Canonical DNA Metrics Across History */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-indigo-400" />
          Evolutionary DNA Metric Matrix Across History
        </h2>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Version</th>
                <th>LOC (Lines)</th>
                <th>CC (Cyclomatic Complexity)</th>
                <th>WMC (Weighted Methods)</th>
                <th>CBO (Coupling)</th>
                <th>LCOM (Lack of Cohesion)</th>
              </tr>
            </thead>
            <tbody>
              {dnaList.map((dna, idx) => (
                <tr key={idx} className={idx === selectedIdx ? 'bg-indigo-950/40 font-bold' : ''}>
                  <td className="font-mono text-indigo-300">{dna.version_tag}</td>
                  <td className="font-mono">{dna.loc?.toLocaleString()}</td>
                  <td className="font-mono text-indigo-400">{dna.cc}</td>
                  <td className="font-mono text-cyan-400">{dna.wmc}</td>
                  <td className="font-mono text-rose-400">{dna.cbo}</td>
                  <td className="font-mono text-emerald-400">{typeof dna.lcom === 'number' ? dna.lcom.toFixed(2) : dna.lcom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
