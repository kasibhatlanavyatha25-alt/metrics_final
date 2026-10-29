from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class GateDecision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    CRITICAL_BLOCK = "CRITICAL BLOCK"


class BranchStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    QUARANTINED = "QUARANTINED"


class MetricVector(BaseModel):
    loc: int = Field(description="Lines of Code (non-empty, non-comment)")
    cc: int = Field(description="Max Method Cyclomatic Complexity")
    wmc: int = Field(description="Weighted Methods per Class (sum of method CC)")
    cbo: int = Field(description="Coupling Between Objects (unique external types)")
    lcom: float = Field(description="Lack of Cohesion in Methods (0.0 - 1.0)")


class DnaRecord(BaseModel):
    class_name: str
    package_name: str
    file_path: str
    commit_sha: str
    version_label: str
    metrics: MetricVector
    timestamp: str


class DnaHistoryResponse(BaseModel):
    class_name: str
    records: List[DnaRecord]
    latest_metrics: MetricVector


class MutationDimensionScore(BaseModel):
    magnitude: float
    persistence: float
    acceleration: float
    cooccurrence: float
    recency: float
    risk: float
    severity: str


class ClassMutationAnalysis(BaseModel):
    class_name: str
    commit_sha: str
    version_label: str
    metric_mutations: Dict[str, MutationDimensionScore]
    total_risk: float
    severe_mutations_count: int
    reasons: List[str]


class EsdiResponse(BaseModel):
    esdi: float
    aggregate_risk: float
    decision: GateDecision
    branch_status: BranchStatus
    affected_modules: List[str]
    mutation_count: int
    reasons: List[str]
    class_esdi: Dict[str, float]
    calibration_bias: float = 0.0


class DependencyGraphNode(BaseModel):
    id: str
    label: str
    package: str
    file_path: str
    commit_sha: str
    metrics: Optional[MetricVector] = None
    is_changed: bool = False


class DependencyGraphEdge(BaseModel):
    source: str
    target: str
    dependency_type: str
    introduced_commit: str
    active: bool = True
    is_new: bool = False


class DependencyGraphResponse(BaseModel):
    nodes: List[DependencyGraphNode]
    edges: List[DependencyGraphEdge]
    total_nodes: int
    total_edges: int


class CommitInfo(BaseModel):
    sha: str
    short_sha: str
    version_label: str
    message: str
    author: str
    timestamp: str
    changed_files: List[str]
    parent_sha: Optional[str] = None


class IncrementalStats(BaseModel):
    files_total: int
    files_changed: int
    files_parsed: int
    files_reused_from_cache: int
    cache_hit_rate: float


class RemediationRequest(BaseModel):
    target_class: str = "PaymentService"
    target_method: Optional[str] = "processPayment"
    commit_sha: Optional[str] = None


class RemediationResponse(BaseModel):
    id: str
    target_class: str
    target_method: str
    remediation_available: bool
    before_source: str
    after_source: str
    diff: str
    before_metrics: MetricVector
    after_metrics: MetricVector
    before_esdi: float
    after_esdi: float
    esdi_delta: float
    compilation_status: str
    test_status: str
    gate_before: str
    gate_after: str
    success: bool
    explanation: str


class PipelineStatusResponse(BaseModel):
    repository: str
    branch: str
    latest_commit: CommitInfo
    esdi: EsdiResponse
    incremental_stats: IncrementalStats
    active_remediation_available: bool
    all_commits: List[CommitInfo]


class GithubWebhookPayload(BaseModel):
    repository: Optional[Dict[str, Any]] = None
    ref: Optional[str] = None
    head_commit: Optional[Dict[str, Any]] = None
    commits: Optional[List[Dict[str, Any]]] = None
    pull_request: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    status: str
    engine: str
    version: str
    ast_engine: str
    graph_engine: str
    state_loaded: bool
    mock_repo_ready: bool


class RepositoryValidateRequest(BaseModel):
    repo_url: Optional[str] = Field(None, description="Public GitHub repository URL or local repository path")
    repository: Optional[str] = Field(None, description="Alternative field for repository URL")
    url: Optional[str] = Field(None, description="Alternative field for repository URL")

    @property
    def effective_url(self) -> str:
        return (self.repo_url or self.repository or self.url or "").strip()

