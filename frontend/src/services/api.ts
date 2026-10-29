import {
  PipelineStatusResponse,
  DnaHistoryResponse,
  ClassMutationAnalysis,
  DependencyGraphResponse,
  EsdiResponse,
  RemediationResponse,
  CommitInfo,
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  async getPipelineStatus(): Promise<PipelineStatusResponse> {
    const res = await fetch(`${API_BASE}/pipeline`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getCommits(): Promise<CommitInfo[]> {
    const res = await fetch(`${API_BASE}/commits`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getDnaTrajectory(className: string = 'PaymentService'): Promise<DnaHistoryResponse> {
    const res = await fetch(`${API_BASE}/dna?class_name=${encodeURIComponent(className)}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getAllDna(): Promise<Record<string, DnaHistoryResponse['records']>> {
    const res = await fetch(`${API_BASE}/dna`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getMutations(commitSha?: string): Promise<Record<string, ClassMutationAnalysis>> {
    const url = commitSha ? `${API_BASE}/mutations?commit_sha=${commitSha}` : `${API_BASE}/mutations`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getDependencyGraph(): Promise<DependencyGraphResponse> {
    const res = await fetch(`${API_BASE}/dependency-graph`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async getEsdi(commitSha?: string): Promise<EsdiResponse> {
    const url = commitSha ? `${API_BASE}/esdi?commit_sha=${commitSha}` : `${API_BASE}/esdi`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async runMockAnalysis(): Promise<PipelineStatusResponse> {
    const res = await fetch(`${API_BASE}/analyze/mock-run`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },

  async applyRemediation(targetClass = 'PaymentService', targetMethod = 'processPayment', commitSha?: string): Promise<RemediationResponse> {
    const res = await fetch(`${API_BASE}/remediate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_class: targetClass,
        target_method: targetMethod,
        commit_sha: commitSha,
      }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return res.json();
  },
};
