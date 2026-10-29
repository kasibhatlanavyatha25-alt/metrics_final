import logging
from typing import Dict, List, Optional, Any
from app.models.schemas import (
    CommitInfo,
    DnaRecord,
    ClassMutationAnalysis,
    EsdiResponse,
    DependencyGraphResponse,
    IncrementalStats,
    RemediationResponse,
)

logger = logging.getLogger("software_dna.state")


class StateStore:
    """
    Central in-memory state repository for the Evolutionary Software DNA engine.
    Maintains historical DNA trajectories, commits, mutation matrices, graph snapshots,
    and CI/CD gate states.
    """

    def __init__(self):
        self.repository_name: str = "Evolutionary Payment System"
        self.branch: str = "feature/payment-processing"
        self.repo_path: str = ""
        self.commits: List[CommitInfo] = []
        
        # class_name -> List[DnaRecord] in chronological order
        self.dna_history: Dict[str, List[DnaRecord]] = {}
        
        # commit_sha -> Dict[class_name, ClassMutationAnalysis]
        self.mutation_history: Dict[str, Dict[str, ClassMutationAnalysis]] = {}
        
        # commit_sha -> EsdiResponse
        self.esdi_history: Dict[str, EsdiResponse] = {}
        
        # commit_sha -> IncrementalStats
        self.incremental_stats: Dict[str, IncrementalStats] = {}
        
        # Latest dependency graph
        self.current_graph: Optional[DependencyGraphResponse] = None
        
        # remediation_id -> RemediationResponse
        self.remediations: Dict[str, RemediationResponse] = {}

    def reset(self) -> None:
        self.commits.clear()
        self.dna_history.clear()
        self.mutation_history.clear()
        self.esdi_history.clear()
        self.incremental_stats.clear()
        self.current_graph = None
        self.remediations.clear()
        logger.info("[StateStore] State reset completed.")

    def add_commit(self, commit: CommitInfo) -> None:
        # Avoid duplicate commits
        for idx, c in enumerate(self.commits):
            if c.sha == commit.sha:
                self.commits[idx] = commit
                return
        self.commits.append(commit)

    def record_dna(self, record: DnaRecord) -> None:
        if record.class_name not in self.dna_history:
            self.dna_history[record.class_name] = []
        # Update or append
        existing = self.dna_history[record.class_name]
        for idx, item in enumerate(existing):
            if item.commit_sha == record.commit_sha:
                existing[idx] = record
                return
        existing.append(record)
        logger.info(f"[DNA] Class {record.class_name} @ {record.version_label}: LOC={record.metrics.loc}, CC={record.metrics.cc}, WMC={record.metrics.wmc}, CBO={record.metrics.cbo}, LCOM={record.metrics.lcom:.2f}")

    def get_dna_history(self, class_name: str) -> List[DnaRecord]:
        return self.dna_history.get(class_name, [])

    def record_mutations(self, commit_sha: str, class_name: str, analysis: ClassMutationAnalysis) -> None:
        if commit_sha not in self.mutation_history:
            self.mutation_history[commit_sha] = {}
        self.mutation_history[commit_sha][class_name] = analysis

    def record_esdi(self, commit_sha: str, esdi: EsdiResponse) -> None:
        self.esdi_history[commit_sha] = esdi

    def record_stats(self, commit_sha: str, stats: IncrementalStats) -> None:
        self.incremental_stats[commit_sha] = stats

    def get_latest_commit(self) -> Optional[CommitInfo]:
        return self.commits[-1] if self.commits else None

    def get_latest_esdi(self) -> Optional[EsdiResponse]:
        if not self.commits:
            return None
        latest_sha = self.commits[-1].sha
        return self.esdi_history.get(latest_sha)

    def get_latest_mutations(self) -> Dict[str, ClassMutationAnalysis]:
        if not self.commits:
            return {}
        latest_sha = self.commits[-1].sha
        return self.mutation_history.get(latest_sha, {})


# Global singleton instance
state_store = StateStore()
