import React from 'react';
import { CommitInfo, IncrementalStats } from '../types';
import { GitCommit, FileCode, Cpu, CheckCircle2, History } from 'lucide-react';

interface CommitTimelineProps {
  commits: CommitInfo[];
  selectedCommitSha: string;
  onSelectCommit: (commit: CommitInfo) => void;
  stats?: IncrementalStats;
}

export const CommitTimeline: React.FC<CommitTimelineProps> = ({
  commits,
  selectedCommitSha,
  onSelectCommit,
  stats,
}) => {
  return (
    <div className="glass-card rounded-xl p-5 border border-slate-800">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-sky-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">
            Commit Evolution & Incremental AST Analysis
          </h2>
        </div>
        {stats && (
          <div className="flex items-center gap-3 text-xs font-mono text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <span>Total: <b className="text-white">{stats.files_total}</b></span>
            <span>Parsed: <b className="text-rose-400">{stats.files_parsed}</b></span>
            <span>Reused: <b className="text-emerald-400">{stats.files_reused_from_cache}</b></span>
            <span>Hit Rate: <b className="text-sky-400">{stats.cache_hit_rate}%</b></span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 mt-4">
        {commits.map((commit, idx) => {
          const isSelected = commit.sha === selectedCommitSha;
          const isV5 = commit.version_label === 'V5';

          return (
            <div
              key={commit.sha}
              onClick={() => onSelectCommit(commit)}
              className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                isSelected
                  ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md shadow-indigo-500/10'
                  : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-800/30'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                  isV5 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-slate-800 text-slate-300'
                }`}>
                  {commit.version_label}
                </span>
                <span className="text-[11px] font-mono text-slate-400">{commit.short_sha}</span>
              </div>

              <div className="text-xs text-slate-200 line-clamp-2 mt-1 leading-snug font-medium">
                {commit.message}
              </div>

              <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-800/60 pt-1.5">
                <span>{commit.changed_files.length} changed file{commit.changed_files.length !== 1 ? 's' : ''}</span>
                <span className="text-slate-500">{commit.timestamp.split(' ')[1] || ''}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
