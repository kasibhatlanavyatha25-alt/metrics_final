export interface MetricVector {
  loc: number;
  cc: number;
  wmc: number;
  cbo: number;
  lcom: number;
}

export interface DnaRecord {
  class_name: string;
  package_name: string;
  file_path: string;
  commit_sha: string;
  version_label: string;
  metrics: MetricVector;
  timestamp: string;
}

export interface DnaHistoryResponse {
  class_name: string;
  records: DnaRecord[];
  latest_metrics: MetricVector;
}

export interface MutationDimensionScore {
  magnitude: number;
  persistence: number;
  acceleration: number;
  cooccurrence: number;
  recency: number;
  risk: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface ClassMutationAnalysis {
  class_name: string;
  commit_sha: string;
  version_label: string;
  metric_mutations: Record<string, MutationDimensionScore>;
  total_risk: number;
  severe_mutations_count: number;
  reasons: string[];
}

export type GateDecision = 'PASS' | 'WARN' | 'BLOCK' | 'CRITICAL BLOCK';
export type BranchStatus = 'NORMAL' | 'WARNING' | 'BLOCKED' | 'QUARANTINED';

export interface EsdiResponse {
  esdi: number;
  aggregate_risk: number;
  decision: GateDecision;
  branch_status: BranchStatus;
  affected_modules: string[];
  mutation_count: number;
  reasons: string[];
  class_esdi: Record<string, number>;
  calibration_bias: number;
}

export interface DependencyGraphNode {
  id: string;
  label: string;
  package: string;
  file_path: string;
  commit_sha: string;
  metrics?: MetricVector;
  is_changed: boolean;
}

export interface DependencyGraphEdge {
  source: string;
  target: string;
  dependency_type: string;
  introduced_commit: string;
  active: boolean;
  is_new: boolean;
}

export interface DependencyGraphResponse {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  total_nodes: number;
  total_edges: number;
}

export interface CommitInfo {
  sha: string;
  short_sha: string;
  version_label: string;
  message: string;
  author: string;
  timestamp: string;
  changed_files: string[];
  parent_sha?: string;
}

export interface IncrementalStats {
  files_total: number;
  files_changed: number;
  files_parsed: number;
  files_reused_from_cache: number;
  cache_hit_rate: number;
}

export interface RemediationResponse {
  id: string;
  target_class: string;
  target_method: string;
  remediation_available: boolean;
  before_source: string;
  after_source: string;
  diff: string;
  before_metrics: MetricVector;
  after_metrics: MetricVector;
  before_esdi: number;
  after_esdi: number;
  esdi_delta: number;
  compilation_status: string;
  test_status: string;
  gate_before: string;
  gate_after: string;
  success: boolean;
  explanation: string;
}

export interface PipelineStatusResponse {
  repository: string;
  branch: string;
  latest_commit: CommitInfo;
  esdi: EsdiResponse;
  incremental_stats: IncrementalStats;
  active_remediation_available: boolean;
  all_commits: CommitInfo[];
}
