import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, ArrowRight, Wrench, CheckCircle } from 'lucide-react';
import { EsdiResponse } from '../types';

interface PipelineStatusProps {
  esdi: EsdiResponse;
  onOpenRemediation: () => void;
}

export const PipelineStatus: React.FC<PipelineStatusProps> = ({ esdi, onOpenRemediation }) => {
  const isBlocked = esdi.decision === 'BLOCK' || esdi.decision === 'CRITICAL BLOCK';

  return (
    <div className="glass-card rounded-xl p-5 border border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            {isBlocked ? (
              <ShieldAlert className="w-5 h-5 text-rose-400" />
            ) : esdi.decision === 'WARN' ? (
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            )}
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">CI/CD Gate Evaluation</h2>
          </div>
          <span
            className={`px-2.5 py-1 text-xs font-bold rounded border font-mono ${
              isBlocked
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : esdi.decision === 'WARN'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
            }`}
          >
            {esdi.decision}
          </span>
        </div>

        {/* Reasons list */}
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gate Decision Rationale:</div>
          <ul className="space-y-1.5">
            {esdi.reasons.slice(0, 4).map((reason, idx) => (
              <li key={idx} className="text-xs text-slate-300 flex items-start gap-2 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${isBlocked ? 'bg-rose-400' : 'bg-emerald-400'}`} />
                <span className="font-mono">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Affected modules and Remediation action */}
      <div className="mt-5 pt-3 border-t border-slate-800/80">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-slate-400">
            Affected Hotspots: <span className="text-rose-400 font-mono font-semibold">{esdi.affected_modules.join(', ') || 'None'}</span>
          </div>

          {isBlocked && (
            <button
              onClick={onOpenRemediation}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-rose-500/20"
            >
              <Wrench className="w-3.5 h-3.5" />
              Automated AST Remediation
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
