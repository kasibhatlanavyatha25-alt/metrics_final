# API Specification

The Evolutionary Software DNA Quality Engine provides REST endpoints for continuous integration, real-time repository analysis, DNA tracking, mutation risk attribution, and automated AST remediation.

Base URL: `http://localhost:8000/api/v1`

---

## 1. System Endpoints

### `GET /api/v1/health`
Returns service health status.
- **Response:** `{"status": "ok", "timestamp": "2026-09-07T10:00:00Z"}`

### `GET /api/v1/status`
Returns runtime engine configurations and initialized adapters.
- **Response:**
```json
{
  "status": "active",
  "engine": "Evolutionary Software DNA Mutation Engine",
  "version": "1.0.0",
  "ast_engine": "Incremental AST Engine (javalang/ast)",
  "graph_engine": "NetworkX Class Dependency Graph",
  "state_loaded": true,
  "mock_repo_ready": true
}
```

---

## 2. Repository & Analysis Endpoints

### `GET /api/v1/repository`
Returns summary statistics of the active repository.

### `GET /api/v1/commits`
Returns the historical list of commits ingested into the engine.

### `POST /api/v1/analyze/mock-run`
Executes a fresh multi-commit incremental analysis run over the test repository.

### `GET /api/v1/pipeline`
Returns current pipeline status, latest commit metrics, and cache statistics.

---

## 3. DNA & Mutation Endpoints

### `GET /api/v1/dna`
- **Query Params:** `class_name` (optional)
- Returns time-series DNA trajectories across commits.

### `GET /api/v1/mutations`
- **Query Params:** `commit_sha` (optional), `class_name` (optional)
- Returns 5D mutation vectors $\Phi = [M, P, A, C, R]^T$ for all detected mutations.

### `GET /api/v1/dependency-graph`
Returns structural dependency graph nodes, edges, and centrality weights.

### `GET /api/v1/esdi`
- **Query Params:** `commit_sha` (optional)
- Returns ESDI score, CI/CD gate decision, and risk breakdown.

---

## 4. Remediation Endpoints

### `POST /api/v1/remediate`
Triggers AST-based Extract Method remediation on a high-risk target.
- **Request Body:**
```json
{
  "target_class": "PaymentService",
  "target_method": "processPayment",
  "commit_sha": "HEAD"
}
```
- **Response:** Before/after source, unified diff, compilation status, test status, before/after ESDI score, and validation outcome.
