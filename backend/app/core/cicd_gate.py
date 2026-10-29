import logging
from typing import Dict, List, Optional
from app.models.schemas import (
    CommitInfo,
    PipelineStatusResponse,
    EsdiResponse,
    IncrementalStats,
)
from app.core.git_interceptor import GitInterceptor
from app.core.incremental_ast import IncrementalASTEngine
from app.core.dependency_graph import DependencyGraphEngine
from app.core.dna_engine import EvolutionaryDNAEngine
from app.core.mutation_detector import MutationDetector
from app.core.esdi_calculator import ESDICalculator
from app.storage.state_store import state_store, StateStore

logger = logging.getLogger("software_dna.gate")


class CICDGateEngine:
    """
    Coordinates the full evolutionary quality pipeline:
    Git Event -> Changed Files -> Incremental AST -> Dependency Graph ->
    Metrics -> DNA History -> 5D Mutations -> ESDI -> CI/CD Gate Decision.
    """

    def __init__(
        self,
        git_interceptor: Optional[GitInterceptor] = None,
        ast_engine: Optional[IncrementalASTEngine] = None,
        graph_engine: Optional[DependencyGraphEngine] = None,
        dna_engine: Optional[EvolutionaryDNAEngine] = None,
        mutation_detector: Optional[MutationDetector] = None,
        esdi_calculator: Optional[ESDICalculator] = None,
        store: Optional[StateStore] = None,
    ):
        self.git = git_interceptor or GitInterceptor()
        self.ast_engine = ast_engine or IncrementalASTEngine()
        self.graph_engine = graph_engine or DependencyGraphEngine()
        self.dna_engine = dna_engine or EvolutionaryDNAEngine()
        self.mutation_detector = mutation_detector or MutationDetector()
        self.esdi_calc = esdi_calculator or ESDICalculator()
        self.store = store or state_store

    def run_full_repository_analysis(self, repo_path: str) -> PipelineStatusResponse:
        """
        Executes sequential analysis across all commits in the repository.
        """
        self.git.set_repo_path(repo_path)
        self.store.reset()
        self.store.repo_path = repo_path

        commits = self.git.get_commit_history()
        logger.info(f"[CICD Gate] Starting incremental analysis for {len(commits)} commits...")

        last_esdi: Optional[EsdiResponse] = None
        last_stats: Optional[IncrementalStats] = None

        for commit in commits:
            self.store.add_commit(commit)
            last_esdi, last_stats = self.analyze_commit_event(commit)

        latest_commit = commits[-1] if commits else CommitInfo(
            sha="0000000",
            short_sha="0000000",
            version_label="V0",
            message="No commits",
            author="N/A",
            timestamp="N/A",
            changed_files=[],
        )

        return PipelineStatusResponse(
            repository=self.store.repository_name,
            branch=self.store.branch,
            latest_commit=latest_commit,
            esdi=last_esdi or self.esdi_calc.calculate_system_esdi({}),
            incremental_stats=last_stats or IncrementalStats(
                files_total=0,
                files_changed=0,
                files_parsed=0,
                files_reused_from_cache=0,
                cache_hit_rate=0.0,
            ),
            active_remediation_available=(last_esdi.esdi >= 75.0 if last_esdi else False),
            all_commits=commits,
        )

    def analyze_commit_event(self, commit: CommitInfo) -> tuple[EsdiResponse, IncrementalStats]:
        """Processes a single commit event in the pipeline."""
        commit_sha = commit.sha
        v_label = commit.version_label

        # 1. Incremental AST analysis
        ast_map, metrics_map, stats, changed_files = self.ast_engine.analyze_commit(
            self.git, commit_sha, self.store.repository_name
        )
        self.store.record_stats(commit_sha, stats)

        # 2. Dependency Graph update
        graph_response = self.graph_engine.update_graph(
            ast_map, metrics_map, changed_files, commit_sha, v_label
        )
        self.store.current_graph = graph_response

        # 3. Update Software DNA records
        for class_name, m_vector in metrics_map.items():
            # Find file path
            f_path = ""
            for path, tree in ast_map.items():
                if tree and any(getattr(t, "name", "") == class_name for t in getattr(tree, "types", [])):
                    f_path = path
                    break

            self.dna_engine.record_class_dna(
                class_name=class_name,
                package_name="com.evolutionary.payment",
                file_path=f_path,
                commit_sha=commit_sha,
                version_label=v_label,
                metrics=m_vector,
                timestamp=commit.timestamp,
            )

        # 4. Detect 5D Mutations per class
        class_analyses: Dict[str, Any] = {}
        for class_name in metrics_map.keys():
            history = self.store.get_dna_history(class_name)
            analysis = self.mutation_detector.analyze_class_mutations(class_name, history)
            self.store.record_mutations(commit_sha, class_name, analysis)
            class_analyses[class_name] = analysis

        # 5. Calculate ESDI & CI/CD Gate
        esdi_response = self.esdi_calc.calculate_system_esdi(class_analyses)
        self.store.record_esdi(commit_sha, esdi_response)

        logger.info(
            f"[CI/CD] Commit {commit.short_sha} ({v_label}) -> ESDI: {esdi_response.esdi} | "
            f"Gate: {esdi_response.decision.value} | Status: {esdi_response.branch_status.value}"
        )

        return esdi_response, stats
