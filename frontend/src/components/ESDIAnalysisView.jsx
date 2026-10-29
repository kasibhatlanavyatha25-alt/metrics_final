import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Sliders, RefreshCw, Layers, 
  HelpCircle, Info, Sparkles, Activity
} from 'lucide-react';
import { fetchProjectESDI, simulateESDI } from '../api';

export default function ESDIAnalysisView({ projectId }) {
  const [esdiData, setEsdiData] = useState(null);
  const [weights, setWeights] = useState({
    complexity: 0.25,
    coupling: 0.20,
    maintainability: 0.20,
    churn: 0.15,
    activity: 0.10,
    defect: 0.10
  });
  const [simulationResult, setSimulationResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadESDI() {
      try {
        setLoading(true);
        const data = await fetchProjectESDI(projectId);
        setEsdiData(data);
        if (data.latest?.weights_used) {
          setWeights({
            complexity: data.latest.weights_used.complexity ?? 0.25,
            coupling: data.latest.weights_used.coupling ?? 0.20,
            maintainability: data.latest.weights_used.maintainability ?? 0.20,
            churn: data.latest.weights_used.churn ?? 0.15,
            activity: data.latest.weights_used.activity ?? 0.10,
            defect: data.latest.weights_used.defect ?? 0.10
          });
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadESDI();
  }, [projectId]);

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const res = await simulateESDI(projectId, weights);
      setSimulationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading ESDI analysis...</div>;
  if (!esdiData || !esdiData.latest) return <div className="p-8 text-center text-slate-400">No ESDI data found.</div>;

  const latest = esdiData.latest;
  const activeESDI = simulationResult ? simulationResult.esdi_score : latest.esdi_score;
  const activeHealth = simulationResult ? simulationResult.health_score : latest.health_score;
  const activeStatus = simulationResult ? simulationResult.status : latest.status;
  const activeExplanation = simulationResult ? simulationResult.explanation : latest.explanation;

  const getStatusBadge = (st) => {
    switch (st?.toUpperCase()) {
      case 'CRITICAL': return 'badge-critical';
      case 'RISKY': return 'badge-risky';
      case 'MODERATE': return 'badge-moderate';
      default: return 'badge-healthy';
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-moderate">Empirical Risk Metric</span>
            <span className="text-xs text-slate-400 font-mono">0–100 Normalized Scale</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            Evolutionary Software DNA Index (ESDI)
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Summarizes overall evolutionary software risk based on historical multi-version metric trajectory.
          </p>
        </div>
      </div>

      {/* Main ESDI & Health Dual Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* ESDI Risk */}
        <div className="glass-panel p-6 space-y-4 border-amber-500/30 bg-amber-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">ESDI Risk Score</span>
            <span className={`badge ${getStatusBadge(activeStatus)}`}>{activeStatus} DNA</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-extrabold font-mono text-amber-400">{activeESDI}</span>
            <span className="text-slate-400 text-base">/ 100 Risk</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-900/80 p-3 rounded-lg border border-slate-800">
            "{activeExplanation}"
          </p>
        </div>

        {/* Health Score */}
        <div className="glass-panel p-6 space-y-4 border-emerald-500/30 bg-emerald-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Software Health Score</span>
            <span className="badge badge-healthy">Quality Indicator</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-extrabold font-mono text-emerald-400">{activeHealth}</span>
            <span className="text-slate-400 text-base">/ 100 Quality</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-3 rounded-lg border border-slate-800">
            Formulation: <span className="font-mono text-emerald-300 font-semibold">Health Score = 100 - ESDI</span>. Distinctly represents software architecture health.
          </p>
        </div>
      </div>

      {/* SECTION 4: Component Breakdown & Historical Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Normalized Component Breakdown */}
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Normalized Component Breakdown (Raw & Weighted)
          </h2>

          <div className="space-y-3 font-mono text-xs">
            {[
              { 
                name: "Complexity Risk (CC)", 
                raw: latest.cc_risk ?? latest.complexity_risk, 
                weighted: latest.weighted_cc ?? latest.weighted_complexity, 
                weight: latest.weights_used?.cc ?? 0.25 
              },
              { 
                name: "Coupling Risk (CBO)", 
                raw: latest.cbo_risk ?? latest.coupling_risk, 
                weighted: latest.weighted_cbo ?? latest.weighted_coupling, 
                weight: latest.weights_used?.cbo ?? 0.20 
              },
              { 
                name: "Class Complexity Risk (WMC)", 
                raw: latest.wmc_risk ?? 0, 
                weighted: latest.weighted_wmc ?? 0, 
                weight: latest.weights_used?.wmc ?? 0.20 
              },
              { 
                name: "Cohesion Defect Risk (LCOM)", 
                raw: latest.lcom_risk ?? 0, 
                weighted: latest.weighted_lcom ?? 0, 
                weight: latest.weights_used?.lcom ?? 0.20 
              },
              { 
                name: "Size / Volume Risk (LOC)", 
                raw: latest.loc_risk ?? 0, 
                weighted: latest.weighted_loc ?? 0, 
                weight: latest.weights_used?.loc ?? 0.15 
              }
            ].map((comp, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-slate-300 font-semibold block">{comp.name}</span>
                  <span className="text-[11px] text-slate-500 font-normal">Weight: {((comp.weight || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="text-right">
                  <span className="text-indigo-400 font-bold block">{typeof comp.raw === 'number' ? `${comp.raw.toFixed(1)} / 100` : comp.raw}</span>
                  <span className="text-[11px] text-slate-400 font-normal">Contribution: +{typeof comp.weighted === 'number' ? comp.weighted.toFixed(2) : comp.weighted}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 italic bg-slate-950/60 p-3 rounded-lg border border-slate-850">
            Policy: {latest.calculation_policy || "Canonical 5D Structural DNA Normalization"}
          </div>
        </div>

        {/* Historical ESDI Timeline */}
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Historical ESDI Evolution Across Versions
          </h2>

          <div className="space-y-3">
            {esdiData.timeline && esdiData.timeline.map((item, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-mono font-bold text-indigo-300 text-sm">{item.version_tag}</span>
                  <span className="text-xs text-slate-500 font-mono block">
                    {item.commit_date ? new Date(item.commit_date).toLocaleDateString() : 'Historical Version'}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right font-mono text-xs">
                    <span className="text-amber-400 font-bold block">ESDI: {item.esdi_score}/100</span>
                    <span className="text-emerald-400 block">Health: {item.health_score}/100</span>
                  </div>
                  <span className={`badge ${getStatusBadge(item.status)}`}>{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Interactive Research Weight Simulator */}
      <div className="glass-panel p-6 space-y-5 border-indigo-500/40 bg-indigo-950/10">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-400" />
              Interactive Research Weight Simulator
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Experiment with alternative research hypotheses by recalculating ESDI and Health Scores with custom weights.
            </p>
          </div>
          <button 
            onClick={handleSimulate}
            disabled={isSimulating}
            className="btn-primary text-xs px-4 py-2 cursor-pointer shadow-indigo-500/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
            Run Simulation
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.keys(weights).map((k) => (
            <div key={k} className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between font-semibold">
                <span className="capitalize text-slate-300">{k}</span>
                <span className="text-indigo-400 font-mono">{(weights[k] * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range"
                min="0"
                max="0.50"
                step="0.05"
                value={weights[k]}
                onChange={(e) => setWeights({ ...weights, [k]: parseFloat(e.target.value) })}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>
          ))}
        </div>

        {simulationResult && (
          <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/40 flex items-center justify-between text-xs font-mono">
            <span className="text-indigo-300">
              Simulated Result: ESDI = <b className="text-amber-400 text-sm">{simulationResult.esdi_score}/100</b>, Health = <b className="text-emerald-400 text-sm">{simulationResult.health_score}/100</b> ({simulationResult.status})
            </span>
            <button 
              onClick={() => setSimulationResult(null)}
              className="text-slate-400 hover:text-white underline cursor-pointer"
            >
              Reset to Base
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
