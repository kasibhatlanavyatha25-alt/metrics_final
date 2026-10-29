import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Any

# Ensure backend root and workspace root are on sys.path for direct module resolution
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_backend_dir.parent) not in sys.path:
    sys.path.insert(0, str(_backend_dir.parent))


from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models.schemas import (
    SystemStatusResponse,
    CommitInfo,
    DnaRecord,
    DnaHistoryResponse,
    ClassMutationAnalysis,
    EsdiResponse,
    DependencyGraphResponse,
    PipelineStatusResponse,
    RemediationRequest,
    RemediationResponse,
    GithubWebhookPayload,
    RepositoryValidateRequest,
)
from app.git.repository_service import validate_repository_input
from app.mock_repo.generator import generate_mock_repository, MOCK_REPO_DIR

from app.storage.state_store import state_store
from app.storage.cache import ast_cache
from app.core.git_interceptor import GitInterceptor
from app.core.incremental_ast import IncrementalASTEngine
from app.core.dependency_graph import DependencyGraphEngine
from app.core.dna_engine import EvolutionaryDNAEngine
from app.core.mutation_detector import MutationDetector
from app.core.esdi_calculator import ESDICalculator
from app.core.cicd_gate import CICDGateEngine
from app.core.remediation_engine import RemediationEngine
from app.core.verification_engine import VerificationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("software_dna.api")

# Core Engine Singletons
git_interceptor = GitInterceptor()
ast_engine = IncrementalASTEngine(cache=ast_cache)
graph_engine = DependencyGraphEngine()
dna_engine = EvolutionaryDNAEngine(store=state_store)
mutation_detector = MutationDetector()
esdi_calculator = ESDICalculator()
cicd_gate_engine = CICDGateEngine(
    git_interceptor=git_interceptor,
    ast_engine=ast_engine,
    graph_engine=graph_engine,
    dna_engine=dna_engine,
    mutation_detector=mutation_detector,
    esdi_calculator=esdi_calculator,
    store=state_store,
)
remediation_engine = RemediationEngine()
verification_engine = VerificationEngine(
    dna_engine=dna_engine,
    mutation_detector=mutation_detector,
    esdi_calculator=esdi_calculator,
    store=state_store,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Evolutionary Software DNA Quality Engine...")
    # Initialize mock repository if needed and execute initial run
    try:
        if not (MOCK_REPO_DIR / ".git").exists():
            logger.info(f"Generating mock Git repository at {MOCK_REPO_DIR}...")
            generate_mock_repository(MOCK_REPO_DIR)
        
        logger.info(f"Analyzing mock repository at {MOCK_REPO_DIR}...")
        cicd_gate_engine.run_full_repository_analysis(str(MOCK_REPO_DIR))
        logger.info("Initial repository analysis completed successfully.")
    except Exception as ex:
        logger.error(f"Startup initialization error: {ex}", exc_info=True)
    yield
    logger.info("Shutting down Evolutionary Software DNA Quality Engine.")


app = FastAPI(
    title="Evolutionary Software DNA Quality Engine API",
    description="Incremental AST & DNA Mutation-driven CI/CD Quality Gate & Automated Remediation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["System"])
async def get_health():
    return {"status": "ok", "timestamp": "2026-09-07T10:00:00Z"}


@app.get("/api/v1/status", response_model=SystemStatusResponse, tags=["System"])
async def get_status():
    return SystemStatusResponse(
        status="active",
        engine="Evolutionary Software DNA Mutation Engine",
        version="1.0.0",
        ast_engine="Incremental AST Engine (javalang)",
        graph_engine="NetworkX Class Dependency Graph",
        state_loaded=bool(state_store.commits),
        mock_repo_ready=(MOCK_REPO_DIR / ".git").exists(),
    )


@app.get("/api/v1/repository", tags=["Repository"])
async def get_repository():
    return {
        "repository_name": state_store.repository_name,
        "branch": state_store.branch,
        "path": str(state_store.repo_path or MOCK_REPO_DIR),
        "total_commits": len(state_store.commits),
        "total_classes": len(state_store.dna_history),
        "ast_cache_stats": ast_cache.get_stats(),
    }


@app.post("/api/projects/validate", tags=["Repository"])
@app.post("/api/v1/projects/validate", tags=["Repository"])
@app.post("/api/v1/repository/validate", tags=["Repository"])
async def validate_repository(payload: RepositoryValidateRequest):
    return validate_repository_input(payload.effective_url)


@app.get("/api/v1/commits", response_model=List[CommitInfo], tags=["Repository"])

async def get_commits():
    return state_store.commits


@app.get("/api/v1/dna", tags=["DNA"])
async def get_dna(class_name: Optional[str] = None):
    if class_name:
        trajectory = dna_engine.get_trajectory(class_name)
        if not trajectory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No DNA trajectory found for class '{class_name}'",
            )
        return trajectory
    return dna_engine.get_all_trajectories()


@app.get("/api/v1/mutations", tags=["Mutations"])
async def get_mutations(commit_sha: Optional[str] = None, class_name: Optional[str] = None):
    if commit_sha:
        mutations = state_store.mutation_history.get(commit_sha, {})
        if class_name:
            if class_name not in mutations:
                raise HTTPException(status_code=404, detail=f"No mutation data for {class_name}")
            return mutations[class_name]
        return mutations
    
    # Return latest mutations
    latest = state_store.get_latest_mutations()
    if class_name:
        if class_name not in latest:
            raise HTTPException(status_code=404, detail=f"No mutation data for {class_name}")
        return latest[class_name]
    return latest


@app.get("/api/v1/dependency-graph", response_model=DependencyGraphResponse, tags=["Graph"])
async def get_dependency_graph():
    if not state_store.current_graph:
        return DependencyGraphResponse(nodes=[], edges=[], total_nodes=0, total_edges=0)
    return state_store.current_graph


@app.get("/api/v1/esdi", response_model=EsdiResponse, tags=["ESDI"])
async def get_esdi(commit_sha: Optional[str] = None):
    if commit_sha:
        res = state_store.esdi_history.get(commit_sha)
        if not res:
            raise HTTPException(status_code=404, detail=f"No ESDI score computed for commit {commit_sha}")
        return res
    latest_esdi = state_store.get_latest_esdi()
    if not latest_esdi:
        raise HTTPException(status_code=404, detail="No ESDI analysis available yet")
    return latest_esdi


@app.get("/api/v1/pipeline", response_model=PipelineStatusResponse, tags=["Pipeline"])
async def get_pipeline_status():
    latest_commit = state_store.get_latest_commit()
    latest_esdi = state_store.get_latest_esdi()
    latest_stats = (
        state_store.incremental_stats.get(latest_commit.sha)
        if latest_commit
        else None
    )

    if not latest_commit or not latest_esdi:
        # Run mock analysis
        status_resp = cicd_gate_engine.run_full_repository_analysis(str(MOCK_REPO_DIR))
        return status_resp

    return PipelineStatusResponse(
        repository=state_store.repository_name,
        branch=state_store.branch,
        latest_commit=latest_commit,
        esdi=latest_esdi,
        incremental_stats=latest_stats or IncrementalStats(
            files_total=len(state_store.dna_history),
            files_changed=len(latest_commit.changed_files),
            files_parsed=len(latest_commit.changed_files),
            files_reused_from_cache=max(0, len(state_store.dna_history) - len(latest_commit.changed_files)),
            cache_hit_rate=ast_cache.hit_rate,
        ),
        active_remediation_available=(latest_esdi.esdi >= 75.0),
        all_commits=state_store.commits,
    )


@app.post("/api/v1/analyze/mock-run", response_model=PipelineStatusResponse, tags=["Analysis"])
async def run_mock_analysis():
    """Triggers generation and incremental re-analysis of the 5-commit mock repository."""
    generate_mock_repository(MOCK_REPO_DIR)
    ast_cache.clear()
    pipeline_res = cicd_gate_engine.run_full_repository_analysis(str(MOCK_REPO_DIR))
    return pipeline_res


@app.post("/api/v1/webhook/github", tags=["Webhook"])
async def github_webhook(payload: GithubWebhookPayload):
    """
    Receives GitHub push / PR webhook payloads.
    Resolves repository, identifies changed files, runs incremental AST analysis.
    """
    logger.info(f"[Webhook] Received GitHub webhook event: ref={payload.ref}")
    
    # Run analysis on local mock repository for demonstration
    pipeline_res = cicd_gate_engine.run_full_repository_analysis(str(MOCK_REPO_DIR))
    
    return {
        "status": "processed",
        "repository": payload.repository.get("name", "PaymentSystem") if payload.repository else "PaymentSystem",
        "decision": pipeline_res.esdi.decision.value,
        "esdi": pipeline_res.esdi.esdi,
        "affected_modules": pipeline_res.esdi.affected_modules,
        "mutation_count": pipeline_res.esdi.mutation_count,
        "reasons": pipeline_res.esdi.reasons,
    }


@app.post("/api/v1/remediate", response_model=RemediationResponse, tags=["Remediation"])
async def apply_remediation(req: RemediationRequest):
    """
    Analyzes and applies automated Extract Method remediation to high-complexity class.
    Compiles, tests, recalculates DNA and ESDI, and returns unified diff.
    """
    target_class = req.target_class or "PaymentService"
    target_method = req.target_method or "processPayment"

    # Read latest file content for target class
    file_path = f"src/main/java/com/evolutionary/payment/{target_class}.java"
    latest_commit = state_store.get_latest_commit()
    commit_sha = req.commit_sha or (latest_commit.sha if latest_commit else "HEAD")

    source_content = git_interceptor.get_file_content_at_commit(file_path, commit_sha)
    if not source_content:
        disk_path = MOCK_REPO_DIR / file_path
        if disk_path.exists():
            source_content = disk_path.read_text(encoding="utf-8")

    if not source_content:
        raise HTTPException(
            status_code=404,
            detail=f"Source file for class {target_class} not found at {file_path}",
        )

    # 1. Generate remediation
    available, remediated_source, unified_diff, explanation = remediation_engine.generate_remediation(
        source_content, target_class, target_method
    )

    if not available:
        return RemediationResponse(
            id="none",
            target_class=target_class,
            target_method=target_method,
            remediation_available=False,
            before_source=source_content,
            after_source=source_content,
            diff="",
            before_metrics=MetricVector(loc=0, cc=0, wmc=0, cbo=0, lcom=0.0),
            after_metrics=MetricVector(loc=0, cc=0, wmc=0, cbo=0, lcom=0.0),
            before_esdi=0.0,
            after_esdi=0.0,
            esdi_delta=0.0,
            compilation_status="SKIPPED",
            test_status="SKIPPED",
            gate_before="N/A",
            gate_after="N/A",
            success=False,
            explanation="No high complexity target found exceeding refactoring thresholds.",
        )

    # 2. Run Verification Loop
    verification_result = verification_engine.verify_remediation(
        target_class=target_class,
        target_method=target_method,
        before_source=source_content,
        after_source=remediated_source,
        diff=unified_diff,
        explanation=explanation,
        commit_sha=commit_sha,
    )

    return verification_result


@app.get("/api/v1/remediation/{remediation_id}", response_model=RemediationResponse, tags=["Remediation"])
async def get_remediation_by_id(remediation_id: str):
    res = state_store.remediations.get(remediation_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Remediation with ID '{remediation_id}' not found")
    return res


# Mount legacy research routes (/api/projects, /api/health, etc.)
try:
    from backend.main import app as legacy_research_app
    app.include_router(legacy_research_app.router)
    logger.info("Successfully mounted legacy research routes.")
except Exception as ex:
    logger.warning(f"Could not mount legacy research routes: {ex}")

