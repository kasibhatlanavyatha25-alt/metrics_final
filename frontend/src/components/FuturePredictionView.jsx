import React, { useState, useEffect } from 'react';
import { 
  Sparkles, TrendingUp, TrendingDown, AlertCircle, 
  HelpCircle, ShieldCheck, Activity, LineChart
} from 'lucide-react';
import { fetchProjectPrediction } from '../api';

export default function FuturePredictionView({ projectId }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPrediction() {
      try {
        setLoading(true);
        const data = await fetchProjectPrediction(projectId);
        setPrediction(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadPrediction();
  }, [projectId]);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading quality trajectory prediction...</div>;
  if (!prediction) return <div className="p-8 text-center text-slate-400">No prediction data available.</div>;

  const { current_health, predicted_health, trend_direction, confidence_score, is_data_sufficient, status_message, main_factors, forecast_points } = prediction;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-moderate">Predictive Modeling</span>
            <span className="text-xs text-slate-400 font-mono">Statistical Trend Extrapolation</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            Future Software Quality & Risk Prediction
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Forecasts next-version architectural quality and risk using empirical time-series trends across historical versions.
          </p>
        </div>
      </div>

      {/* Main Prediction KPI Card */}
      {(() => {
        const isQuarantined = trend_direction === 'QUARANTINED' || prediction?.is_quarantined;
        const isBlocked = trend_direction === 'BLOCKED / AT RISK' || prediction?.is_blocked;

        return (
          <>
            {isQuarantined && (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/50 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-rose-300">CI/CD Gate Quarantine Active</h3>
                  <p className="text-xs text-rose-200/90 leading-relaxed">
                    Repository is currently under CI/CD quarantine due to severe localized mutations (Risk &ge; 90). Downstream health projection is suspended until remediation is validated.
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Current Quality */}
              <div className="glass-panel p-6 space-y-2 border-emerald-500/30 bg-emerald-950/10">
                <span className="text-xs font-semibold text-emerald-400 block">Current Software Quality</span>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold font-mono text-emerald-300">{current_health}</span>
                  <span className="text-slate-400 text-sm">/ 100 Health</span>
                </div>
                <span className="text-xs text-slate-400 block">Latest Analyzed Version</span>
              </div>

              {/* Predicted Quality */}
              <div className={`glass-panel p-6 space-y-2 ${isQuarantined || isBlocked ? 'border-rose-500/30 bg-rose-950/10' : 'border-indigo-500/30 bg-indigo-950/10'}`}>
                <span className="text-xs font-semibold text-indigo-300 block">Predicted Next-Version Quality</span>
                <div className="flex items-baseline gap-2">
                  <span className={`text-4xl font-extrabold font-mono ${
                    isQuarantined || isBlocked ? 'text-rose-400' :
                    predicted_health >= current_health ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {isQuarantined ? 'SUSPENDED' : (predicted_health !== null ? `${predicted_health}` : 'N/A')}
                  </span>
                  {!isQuarantined && <span className="text-slate-400 text-sm">/ 100 Health</span>}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`badge ${
                    isQuarantined || isBlocked ? 'badge-critical bg-rose-950/80 text-rose-300 border-rose-500/50' :
                    trend_direction === 'IMPROVING' ? 'badge-healthy' :
                    trend_direction === 'DECLINING' ? 'badge-critical' : 'badge-moderate'
                  }`}>
                    Trend: {trend_direction}
                  </span>
                </div>
              </div>

              {/* Confidence & Empirical Limitations */}
              <div className="glass-panel p-6 space-y-2">
                <span className="text-xs font-semibold text-slate-300 block">Confidence & Limitations</span>
                <div className="text-2xl font-bold font-mono text-cyan-400">
                  {confidence_score && !isQuarantined ? `${(confidence_score * 100).toFixed(0)}%` : (isQuarantined ? '0% (Suspended)' : 'N/A')}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  * Prediction is a statistical trend estimate based on historical regression fit, subject to active gate status.
                </p>
              </div>
            </div>
          </>
        );
      })()}

      {/* Main Driving Factors */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          Primary Factors Driving Quality Trajectory
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {main_factors && main_factors.length > 0 ? (
            main_factors.map((factor, idx) => (
              <div key={idx} className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center gap-3 text-xs text-slate-200">
                <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0" />
                <span>{factor}</span>
              </div>
            ))
          ) : (
            <div className="text-xs text-slate-400 italic">No significant trend anomalies detected.</div>
          )}
        </div>

        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-850 text-xs text-slate-300 space-y-1">
          <span className="font-semibold text-slate-200">Summary Forecast Status:</span>
          <p className="leading-relaxed text-slate-400">{status_message}</p>
        </div>
      </div>

      {/* Time-Series Forecast Timeline Chart */}
      {forecast_points && forecast_points.length > 0 && (
        <div className="glass-panel p-6 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <LineChart className="w-4 h-4 text-indigo-400" />
            Software Health Trajectory & Next-Version Forecast
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {forecast_points.map((pt, idx) => (
              <div 
                key={idx}
                className={`p-4 rounded-xl border space-y-2 font-mono ${
                  pt.is_prediction 
                    ? 'bg-indigo-950/40 border-indigo-500/60 shadow-lg shadow-indigo-500/20' 
                    : 'bg-slate-900/70 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className={pt.is_prediction ? 'text-indigo-300 font-bold' : 'text-slate-400 font-medium'}>
                    {pt.version}
                  </span>
                  {pt.is_prediction && <span className="badge badge-moderate text-[9px]">FORECAST</span>}
                </div>

                <div className="text-xl font-bold text-emerald-400">
                  {pt.health_score} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                </div>

                {pt.confidence_lower !== undefined && (
                  <span className="text-[10px] text-slate-400 block">
                    Range: {pt.confidence_lower} – {pt.confidence_upper}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
