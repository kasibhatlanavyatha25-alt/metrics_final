import React from 'react';
import { GitBranch, GitCommit, Dna, Play, RefreshCw, ShieldAlert, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { PipelineStatusResponse } from '../types';

interface HeaderProps {
  pipeline: PipelineStatusResponse | null;
  loading: boolean;
  onRefresh: () => void;
  onRunMock: () => void;
  onOpenRemediation: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  pipeline,
  loading,
  onRefresh,
  onRunMock,
  onOpenRemediation,
}) => {
  const decision = pipeline?.esdi.decision || 'PASS';

  const getGateBadge = () => {
    switch (decision) {
      case 'CRITICAL BLOCK':
        return {
          bg: 'bg-rose-500/20 text-rose-300 border-rose-500/40 glow-danger',
          icon: <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />,
          label: 'CRITICAL QUARANTINE',
        };
      case 'BLOCK':
        return {
          bg: 'bg-rose-500/20 text-rose-300 border-rose-500/40 glow-danger',
          icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
          label: 'PIPELINE BLOCKED',
        };
      case 'WARN':
        return {
          bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40 glow-warning',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          label: 'GATE WARNING',
        };
      default:
        return {
          bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 glow-success',
          icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
          label: 'PIPELINE PASSED',
        };
    }
  };

  const badge = getGateBadge();

  return (
    <header className="border-b border-slate-800 bg-[#090e17]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        {/* Brand & Repo Info */}
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-sky-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-[#090e17] rounded-[10px] flex items-center justify-center">
              <Dna className="w-6 h-6 text-sky-400 animate-pulse-glow" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Software DNA Quality Engine
              </h1>
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border flex items-center gap-1.5 ${badge.bg}`}>
                {badge.icon}
                {badge.label}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-slate-400">
              <span className="flex items-center gap-1 font-mono text-slate-300">
                <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
                {pipeline?.branch || 'feature/payment-processing'}
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1 font-mono text-slate-400">
                <GitCommit className="w-3.5 h-3.5 text-sky-400" />
                Commit: <span className="text-sky-300 font-semibold">{pipeline?.latest_commit.short_sha || 'df905d0'}</span> ({pipeline?.latest_commit.version_label || 'V5'})
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400 truncate max-w-xs">{pipeline?.latest_commit.message || 'Latest PR changes'}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 self-end md:self-auto">
          {pipeline?.active_remediation_available && (
            <button
              onClick={onOpenRemediation}
              className="px-4 py-2 text-xs font-bold rounded-lg bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 text-white shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2 animate-bounce"
            >
              <ShieldAlert className="w-4 h-4" />
              Analyze Remediation
            </button>
          )}

          <button
            onClick={onRunMock}
            disabled={loading}
            className="px-3.5 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-2"
            title="Re-run 5-commit evolutionary simulation"
          >
            <Play className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
            Re-run 5 Commits
          </button>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh state"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
