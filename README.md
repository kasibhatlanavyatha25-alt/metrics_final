# Evolutionary Software DNA Quality Engine

A production-style implementation of **"System and Method for Evolutionary Software Quality Assessment and Metric Recommendation Using Software DNA Mutation Analysis"**.

This platform delivers an automated, mathematically rigorous quality control gate for continuous integration (CI/CD) pipelines. Unlike static linters that compute point-in-time scores, this engine models software metrics as an evolving multi-generational genome, detects five-dimensional metric mutations, computes the **Evolutionary Software DNA Index (ESDI)**, enforces gating decisions, and provides automated, verified AST-level remediation.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────────────────┐
                        │             Git Commit / PR Event               │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │        Git Interceptor & Diff Detection         │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │            Incremental AST Engine               │
                        │    (Reuses Unchanged Nodes via AST Cache)       │
                        └──────────┬───────────────────────────┬──────────┘
                                   │                           │
                                   ▼                           ▼
        ┌────────────────────────────────────┐       ┌────────────────────────────────────┐
        │    NetworkX Dependency Graph       │       │       Raw Metric Vector Extractor  │
        │   (Node & Edge Delta Updates)      │       │     [LOC, CC, WMC, CBO, LCOM]      │
        └────────────────────────────────────┘       └─────────────────┬──────────────────┘
                                                                       │
                                                                       ▼
                                                     ┌────────────────────────────────────┐
                                                     │     Evolutionary Software DNA      │
                                                     │         Trajectory Store           │
                                                     └─────────────────┬──────────────────┘
                                                                       │
                                                                       ▼
                                                     ┌────────────────────────────────────┐
                                                     │   5D DNA Mutation Engine           │
                                                     │   (Mag, Pers, Acc, Cooc, Rec)      │
                                                     └─────────────────┬──────────────────┘
                                                                       │
                                                                       ▼
                                                     ┌────────────────────────────────────┐
                                                     │        ESDI Risk Aggregator        │
                                                     │     (Calibrated Sigmoid Model)     │
                                                     └─────────────────┬──────────────────┘
                                                                       │
                                                                       ▼
                                                     ┌────────────────────────────────────┐
                                                     │      CI/CD Quality Gate Policy     │
                                                     │  PASS / WARN / BLOCK / QUARANTINE  │
                                                     └─────────────────┬──────────────────┘
                                                                       │
                                                     ┌─────────────────┴──────────────────┐
                                                     │  If BLOCKED:                       │
                                                     │  Automated AST Remediation &       │
                                                     │  Compilation/Test Verification     │
                                                     └────────────────────────────────────┘
```

---

## Core Analytical Components

### 1. Software DNA Representation
For every Java class $c$ at commit version $t$, the system computes an empirical 5-tuple metric vector:
$$M(c, t) = [\text{LOC}, \text{CC}, \text{WMC}, \text{CBO}, \text{LCOM}]$$

- **LOC (Lines of Code)**: Non-empty, non-comment lines extracted directly from raw source.
- **CC (Cyclomatic Complexity)**: Method-level McCabe complexity:
  $$\text{CC}(\text{method}) = 1 + \sum \text{decision constructs}$$
  (Counts `if`, `for`, `while`, `do`, `case`, `catch`, ternary `? :`, and boolean `&&`/`||` operators).
- **WMC (Weighted Methods per Class)**: $\sum_{m \in \text{methods}} \text{CC}(m)$.
- **CBO (Coupling Between Objects)**: Count of unique external classes/types referenced in imports, field declarations, method signatures, return types, and `new` object creators (excluding primitives and `java.lang.*`).
- **LCOM (Henderson-Sellers Lack of Cohesion in Methods)**:
  $$\text{LCOM}^* = \frac{\frac{1}{a} \sum_{j=1}^a \mu(A_j) - m}{1 - m}$$
  where $m$ is method count, $a$ is field count, and $\mu(A_j)$ is method access count per field.

---

### 2. Incremental AST Engine & Cache
The engine does not naively re-parse the entire codebase.
1. Inspects Git diffs using `GitPython` to identify modified `.java` files.
2. Checks in-memory AST cache keyed by `(repository, file_path, commit_sha)`.
3. Parses only modified/added files using `javalang`.
4. Reuses cached AST trees for unchanged files, computing real-time cache statistics (`files_total`, `files_changed`, `files_parsed`, `files_reused_from_cache`, `cache_hit_rate`).

---

### 3. Class Dependency Graph
Maintains an incremental `networkx.DiGraph` representing classes as nodes and references (inheritance, implementation, field dependency, parameter dependency, object instantiation) as directed edges. When a class changes, old outgoing edges are removed and rebuilt without disturbing unchanged graph topology.

---

### 4. Five-Dimensional Mutation Engine
For every metric $m \in \{\text{LOC}, \text{CC}, \text{WMC}, \text{CBO}, \text{LCOM}\}$:

1. **Magnitude ($\text{Mag}$)**:
   $$\text{Mag}(m, t) = \frac{m_t - m_{t-1}}{\max(1, |m_{t-1}|)}$$
2. **Persistence ($P$)**:
   $$P(m) = \frac{\text{consecutive deteriorating transitions}}{\text{total transitions in rolling window}}$$
3. **Acceleration ($A$)**:
   $$A_{\text{raw}} = (m_t - m_{t-1}) - (m_{t-1} - m_{t-2})$$
   Normalized relative to prior velocity.
4. **Co-occurrence ($C$)**:
   $$C(u, k, t) = \frac{\sum_{j \ne k} \mu(u, j, t)}{K - 1}$$
   Where $K=5$ is the total number of tracked metrics ($\text{LOC}, \text{CC}, \text{WMC}, \text{CBO}, \text{LCOM}$), the evaluated metric $k$ is excluded ($j \ne k$), and the denominator is $K-1=4$. Discrete co-occurrence values are $C \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$.
5. **Recency ($R$)**:
   $$R = \exp(-\lambda \cdot \text{age})$$

Dimensional risk per metric:
$$\text{risk}_m = w_{\text{mag}} \cdot \text{Mag}_{\text{norm}} + w_{\text{pers}} \cdot P + w_{\text{acc}} \cdot A_{\text{norm}} + w_{\text{cooc}} \cdot C + w_{\text{rec}} \cdot R$$

---

### 5. Evolutionary Software DNA Index (ESDI)
The system aggregates weighted metric risks:
$$\text{AggregateRisk} = \sum_{m} w_m \cdot \text{risk}_m$$

The final index is computed via a calibrated sigmoid function:
$$\text{ESDI} = 100 \cdot \frac{1}{1 + \exp(-k \cdot (\text{AggregateRisk} - \text{bias}))}$$

### CI/CD Gate Policy:
- **PASS**: $\text{ESDI} < 50$ (Normal pipeline execution)
- **WARN**: $50 \le \text{ESDI} < 75$ (Build alert / review requested)
- **BLOCK**: $75 \le \text{ESDI} < 90$ (Merge blocked due to high degradation)
- **CRITICAL BLOCK**: $\text{ESDI} \ge 90$ (Branch marked **QUARANTINED**)

---

### 6. Automated AST Remediation & Verification Loop
For monolithic methods exceeding architectural thresholds ($\text{CC} > 15$, $\text{LOC} > 40$):
1. Safely applies AST **Extract Method** refactoring to isolate validation, security checks, routing, and lifecycle execution.
2. Generates a standard unified diff.
3. Compiles the remediated code (`javac` if available, or verified AST syntax/symbol pass).
4. Executes unit tests.
5. Recomputes AST, metrics, DNA trajectory, and recalculates $\text{ESDI}_{\text{after}}$.
6. Re-evaluates the CI/CD gate: the remediation is accepted only if $\text{ESDI}_{\text{after}} < \text{ESDI}_{\text{before}}$ and compilation/tests succeed.

---

## Mock Repository Evolution (V1 - V5)

The included generator creates an authentic local Git repository (`data/generated/mock_repo`) across 5 real commits:
- **V1 (`feat: initial clean architecture`)**: Modular `PaymentService` ($\text{CC}=5, \text{WMC}=6, \text{CBO}=6, \text{LCOM}=0.0$). $\text{ESDI} \approx 31.4$ (PASS).
- **V2 (`feat: validation checks`)**: Comprehensive request validations added ($\text{CC}=10, \text{WMC}=11$).
- **V3 (`refactor: retry and fraud checks`)**: Retries, backoff, and fraud detection debt added ($\text{CC}=18, \text{WMC}=19$).
- **V4 (`feat: multi-channel payment routing`)**: Nested switch statements and external adapters ($\text{CC}=38, \text{WMC}=39$).
- **V5 (`feat: critical PR #142`)**: Monolithic method with high CC, CBO, and LCOM degradation ($\text{CC}=54, \text{WMC}=55$). $\text{ESDI} \approx 78.5$ (**BLOCK**).

Applying AST remediation on V5 reduces ESDI from **78.5 (BLOCK)** to **63.2 (WARN)** with verified test execution.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health status |
| `GET` | `/api/v1/status` | System status & AST engine metadata |
| `GET` | `/api/v1/repository` | Repository stats & cache hit rates |
| `GET` | `/api/v1/commits` | Ordered commit history with changed files |
| `GET` | `/api/v1/dna` | DNA trajectories for specific or all classes |
| `GET` | `/api/v1/mutations` | 5D mutation breakdown per class |
| `GET` | `/api/v1/dependency-graph` | NetworkX class dependency graph topology |
| `GET` | `/api/v1/esdi` | Current system ESDI score & gate decision |
| `GET` | `/api/v1/pipeline` | Complete consolidated pipeline overview |
| `POST` | `/api/v1/analyze/mock-run` | Triggers 5-commit mock repository simulation |
| `POST` | `/api/v1/webhook/github` | Ingests GitHub push/PR webhooks |
| `POST` | `/api/v1/remediate` | Executes Extract Method remediation & verification |
| `GET` | `/api/v1/remediation/{id}` | Fetches remediation result by ID |

---

## Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Git**

### Installation & Quick Start

1. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Install frontend dependencies:**
   ```bash
   cd frontend && npm install && cd ..
   ```

3. **Run automated self-test:**
   ```bash
   python backend/run.py --self-test
   ```

4. **Start backend & frontend servers:**
   - On Linux / macOS / Git Bash:
     ```bash
     bash scripts/start.sh
     ```
   - On Windows (PowerShell):
     ```powershell
     # Terminal 1: Backend
     python backend/run.py --port 8000

     # Terminal 2: Frontend
     cd frontend; npm run dev
     ```

- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running Automated Tests

```bash
# Run backend pytest suite
python -m pytest backend/tests -v

# Run self-test verification
python backend/run.py --self-test
```

---

## Patent-Oriented Technical Contribution & Limitations

1. **Decision Signal**: ESDI is an empirical quality gate signal capturing architectural velocity, not merely a static score.
2. **Controlled Remediation**: Automated refactoring is strictly scoped to high-complexity structural targets (e.g. Extract Method) and requires automated verification before deployment. The system does not claim arbitrary Java code synthesis.
3. **Incremental Performance**: The AST cache and dependency graph prune unchanged subtrees to ensure $O(\Delta \text{files})$ execution time suitable for CI/CD webhooks.
