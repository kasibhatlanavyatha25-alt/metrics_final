import React, { useEffect, useState, useRef } from 'react';
import { 
  CheckCircle2, Circle, Loader2, AlertTriangle, Terminal, 
  ArrowRight, ShieldCheck, Cpu, GitCommit, Dna, FileSpreadsheet, Sparkles
} from 'lucide-react';
import { fetchAnalysisStatus } from '../api';

const STAGE_LABELS = [
  "Repository validation",
  "Multi-language source detection",
  "Git history extraction",
  "Version identification",
  "Version checkout",
  "Unified metric extraction",
  "Historical dataset construction",
  "Evolutionary DNA generation",
  "Mutation analysis",
  "ESDI calculation",
  "Module risk analysis",
  "Recommendation generation",
  "Future prediction",
  "Report generation & persistence"
];

export default function ProgressView({ projectId, onComplete, onCancel }) {
  const [statusData, setStatusData] = useState(null);
  const [error, setError] = useState(null);
  const logEndRef = useRef(null);

  useEffect(() => {
    let interval = null;

    const checkStatus = async () => {
      try {
        const data = await fetchAnalysisStatus(projectId);
        setStatusData(data);

        if (data.status === 'COMPLETED') {
          clearInterval(interval);
          setTimeout(() => {
            onComplete(projectId);
          }, 1200);
        } else if (data.status === 'FAILED') {
          clearInterval(interval);
          setError(data.error_message || 'Analysis run failed.');
        }
      } catch (err) {
        console.error('Error fetching progress:', err);
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 1500);

    return () => clearInterval(interval);
  }, [projectId, onComplete]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [statusData?.logs]);

  const currentStageIdx = statusData?.stage_index || 1;
  const isFinished = statusData?.status === 'COMPLETED';

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* Header */}
      <div className="glass-panel p-6 border-indigo-500/30 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="badge badge-moderate animate-pulse">Live Pipeline Execution</span>
            <span className="text-xs text-slate-400 font-mono">Project ID: #{projectId}</span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Analyzing: <span className="text-indigo-400">{statusData?.project_name || 'Git Repository'}</span>
          </h1>
          <p className="text-xs text-slate-400">
            Running 14-stage empirical extraction and Evolutionary DNA pipeline on actual source AST & Git commits.
          </p>
        </div>

        <div className="text-right">
          <div className="text-3xl font-extrabold font-mono text-indigo-400">
            {Math.min(100, Math.round((currentStageIdx / 14) * 100))}%
          </div>
          <span className="text-xs text-slate-400">Stage {currentStageIdx} of 14</span>
        </div>
      </div>

      {/* Progress Stepper */}
      <div className="glass-panel p-6 space-y-4">
        <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          Pipeline Stages (14 Real Stages)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {STAGE_LABELS.map((stageName, idx) => {
            const stageNum = idx + 1;
            const isCompleted = stageNum < currentStageIdx || isFinished;
            const isCurrent = stageNum === currentStageIdx && !isFinished;

            return (
              <div 
                key={idx}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                  isCompleted 
                    ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300' 
                    : isCurrent 
                      ? 'bg-indigo-950/40 border-indigo-500/50 text-indigo-200 shadow-md shadow-indigo-500/10' 
                      : 'bg-slate-900/40 border-slate-800/60 text-slate-500'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-slate-600 shrink-0" />
                )}
                
                <span className="text-xs font-mono font-semibold opacity-70 w-5">
                  {stageNum.toString().padStart(2, '0')}
                </span>
                
                <span className={`text-xs font-medium truncate ${isCurrent ? 'font-bold text-white' : ''}`}>
                  {stageName}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Terminal Log Stream */}
      <div className="glass-panel p-6 space-y-3 bg-slate-950/90 border-slate-800">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
            <Terminal className="w-4 h-4 text-emerald-400" />
            Backend Execution Console Output
          </div>
          <span className="text-xs text-slate-500 font-mono">Real-time Stream</span>
        </div>

        <div className="h-48 overflow-y-auto font-mono text-xs text-slate-300 space-y-1.5 p-3 rounded-lg bg-black/50 border border-slate-900">
          {statusData?.logs && statusData.logs.length > 0 ? (
            statusData.logs.map((log, i) => (
              <div key={i} className="leading-relaxed">
                <span className="text-emerald-400">{">"}</span> {log}
              </div>
            ))
          ) : (
            <div className="text-slate-500 italic">Initializing analysis pipeline...</div>
          )}
          <div ref={logEndRef} />
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-200 space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
            Analysis Failed
          </div>
          <p className="text-xs">{error}</p>
          <button onClick={onCancel} className="btn-secondary text-xs mt-2 px-3 py-1.5">
            Return to Home
          </button>
        </div>
      )}
    </div>
  );
}
