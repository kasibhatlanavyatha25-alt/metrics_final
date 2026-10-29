import React from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck } from 'lucide-react';
import { GateDecision } from '../types';

interface EsdiGaugeProps {
  score: number;
  decision: GateDecision;
  aggregateRisk: number;
}

export const EsdiGauge: React.FC<EsdiGaugeProps> = ({ score, decision, aggregateRisk }) => {
  // Angle calculations for 180-degree semi-circle gauge (from -90 to +90 deg or 0 to 180)
  const clampedScore = Math.min(100, Math.max(0, score));
  const rotationDeg = (clampedScore / 100) * 180 - 90;

  const getColorInfo = () => {
    if (clampedScore >= 90) {
      return {
        color: '#f43f5e', // rose-500
        glow: 'glow-danger',
        label: 'CRITICAL BLOCK',
        desc: 'Severe DNA mutations detected',
        icon: <ShieldAlert className="w-5 h-5 text-rose-400" />,
      };
    } else if (clampedScore >= 75) {
      return {
        color: '#f43f5e',
        glow: 'glow-danger',
        label: 'BLOCK',
        desc: 'Evolutionary debt threshold exceeded',
        icon: <ShieldAlert className="w-5 h-5 text-rose-400" />,
      };
    } else if (clampedScore >= 50) {
      return {
        color: '#f59e0b', // amber-500
        glow: 'glow-warning',
        label: 'WARN',
        desc: 'Accelerating degradation observed',
        icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
      };
    } else {
      return {
        color: '#10b981', // emerald-500
        glow: 'glow-success',
        label: 'PASS',
        desc: 'Software DNA within healthy bounds',
        icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />,
      };
    }
  };

  const info = getColorInfo();

  return (
    <div className={`glass-card rounded-xl p-5 border flex flex-col items-center justify-between ${info.glow}`}>
      <div className="w-full flex items-center justify-between border-b border-slate-800/80 pb-3">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evolutionary Software DNA Index</h2>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
          5D Sigmoid Model
        </span>
      </div>

      {/* SVG Radial Gauge */}
      <div className="relative w-48 h-28 my-2 flex items-center justify-center">
        <svg viewBox="0 0 100 55" className="w-full h-full overflow-visible">
          {/* Background Arc */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#1e293b"
            strokeWidth="8"
            strokeLinecap="round"
          />

          {/* Color Gradient Segments */}
          {/* PASS: 0 - 50 */}
          <path
            d="M 10 50 A 40 40 0 0 1 50 10"
            fill="none"
            stroke="#10b981"
            strokeWidth="8"
            strokeDasharray="62.8 125.6"
            strokeOpacity="0.8"
          />
          {/* WARN: 50 - 75 */}
          <path
            d="M 50 10 A 40 40 0 0 1 78.28 21.72"
            fill="none"
            stroke="#f59e0b"
            strokeWidth="8"
            strokeDasharray="31.4 125.6"
            strokeOpacity="0.8"
          />
          {/* BLOCK: 75 - 100 */}
          <path
            d="M 78.28 21.72 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#f43f5e"
            strokeWidth="8"
            strokeDasharray="31.4 125.6"
            strokeOpacity="0.8"
          />

          {/* Indicator Needle */}
          <g transform={`rotate(${rotationDeg} 50 50)`} className="transition-transform duration-700 ease-out">
            <line x1="50" y1="50" x2="50" y2="14" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="50" cy="50" r="4" fill="#6366f1" stroke="#ffffff" strokeWidth="1.5" />
          </g>
        </svg>

        {/* Score in Center */}
        <div className="absolute bottom-0 text-center">
          <div className="text-3xl font-black font-mono tracking-tight text-white">{score.toFixed(1)}</div>
          <span className="text-[10px] text-slate-400 font-medium">ESDI Score</span>
        </div>
      </div>

      {/* Decision Status Pill */}
      <div className="w-full bg-slate-900/80 rounded-lg p-3 border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {info.icon}
          <div>
            <div className="text-xs font-bold text-white tracking-wide">{info.label}</div>
            <div className="text-[11px] text-slate-400">{info.desc}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-slate-500 uppercase">Agg. Risk</div>
          <div className="text-xs font-mono font-bold text-sky-400">{aggregateRisk.toFixed(3)}</div>
        </div>
      </div>
    </div>
  );
};
