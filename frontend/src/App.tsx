import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import {
  PipelineStatusResponse,
  DnaHistoryResponse,
  ClassMutationAnalysis,
  DependencyGraphResponse,
  RemediationResponse,
  CommitInfo,
} from './types';
import { Header } from './components/Header';
import { DashboardOverview } from './components/DashboardOverview';
import { RemediationPreview } from './components/RemediationPreview';
import { Loader2, AlertCircle } from 'lucide-react';

export function App() {
  const [pipeline, setPipeline] = useState<PipelineStatusResponse | null>(null);
  const [dnaHistory, setDnaHistory] = useState<DnaHistoryResponse | null>(null);
  const [mutations, setMutations] = useState<Record<string, ClassMutationAnalysis>>({});
  const [graph, setGraph] = useState<DependencyGraphResponse | null>(null);
  const [selectedCommit, setSelectedCommit] = useState<CommitInfo | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Remediation Modal State
  const [isRemediationOpen, setIsRemediationOpen] = useState<boolean>(false);
  const [remediationData, setRemediationData] = useState<RemediationResponse | null>(null);
  const [remediationLoading, setRemediationLoading] = useState<boolean>(false);

  const loadData = async (commitSha?: string) => {
    try {
      setLoading(true);
      setError(null);

      const [pipeRes, dnaRes, mutRes, graphRes] = await Promise.all([
        api.getPipelineStatus(),
        api.getDnaTrajectory('PaymentService'),
        api.getMutations(commitSha),
        api.getDependencyGraph(),
      ]);

      setPipeline(pipeRes);
      setDnaHistory(dnaRes);
      setMutations(mutRes);
      setGraph(graphRes);

      if (!selectedCommit && pipeRes.latest_commit) {
        setSelectedCommit(pipeRes.latest_commit);
      }
    } catch (err: any) {
      console.error('Failed to load engine data:', err);
      setError(err.message || 'Failed to connect to Evolutionary DNA Engine backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectCommit = async (commit: CommitInfo) => {
    setSelectedCommit(commit);
    try {
      const mutRes = await api.getMutations(commit.sha);
      setMutations(mutRes);
    } catch (err) {
      console.error('Error fetching commit mutations:', err);
    }
  };

  const handleRunMock = async () => {
    try {
      setLoading(true);
      const res = await api.runMockAnalysis();
      setPipeline(res);
      setSelectedCommit(res.latest_commit);
      await loadData(res.latest_commit.sha);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenRemediation = async () => {
    setIsRemediationOpen(true);
    try {
      setRemediationLoading(true);
      const rem = await api.applyRemediation('PaymentService', 'processPayment');
      setRemediationData(rem);
    } catch (err: any) {
      console.error('Failed to analyze remediation:', err);
    } finally {
      setRemediationLoading(false);
    }
  };

  const handleApplyRemediation = async () => {
    setIsRemediationOpen(false);
    await loadData();
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col font-sans">
      <Header
        pipeline={pipeline}
        loading={loading}
        onRefresh={() => loadData()}
        onRunMock={handleRunMock}
        onOpenRemediation={handleOpenRemediation}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6">
        {loading && !pipeline ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            <span className="text-sm font-mono">Running Incremental AST & Software DNA Engine...</span>
          </div>
        ) : error ? (
          <div className="p-6 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-start gap-3">
            <AlertCircle className="w-6 h-6 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <h3 className="font-bold text-sm">Engine Communication Error</h3>
              <p className="text-xs mt-1 text-rose-300/80">{error}</p>
              <button
                onClick={() => loadData()}
                className="mt-3 px-3 py-1.5 text-xs bg-rose-800/60 hover:bg-rose-700/80 rounded border border-rose-600 transition"
              >
                Retry Connection
              </button>
            </div>
          </div>
        ) : pipeline ? (
          <DashboardOverview
            pipeline={pipeline}
            dnaHistory={dnaHistory}
            mutations={mutations}
            graph={graph}
            selectedCommit={selectedCommit}
            onSelectCommit={handleSelectCommit}
            onOpenRemediation={handleOpenRemediation}
          />
        ) : null}
      </main>

      <RemediationPreview
        isOpen={isRemediationOpen}
        onClose={() => setIsRemediationOpen(false)}
        remediation={remediationData}
        loading={remediationLoading}
        onApply={handleApplyRemediation}
      />
    </div>
  );
}

export default App;
