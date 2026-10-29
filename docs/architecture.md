# Evolutionary Software DNA Quality Engine — Architecture Specification

**Project Title:** System and Method for Evolutionary Software Quality Assessment and Metric Recommendation Using Software DNA Mutation Analysis

---

## 1. System Overview

The Evolutionary Software DNA Quality Engine is an automated software quality control system designed for version-controlled repositories. It transitions static metric analysis into a dynamic, evolutionary assessment framework by modeling source code metrics as multidimensional "Software DNA" across commit timelines, characterizing metric changes through a 5-Dimensional Mutation Model, computing a composite Evolutionary Software DNA Index (ESDI), attributing risk hierarchically down to methods, and driving automated AST-based remediation with closed-loop validation.

```
Git Change Event
       │
       ▼
Changed-File Detection (Git Diff / History Extraction)
       │
       ▼
Incremental AST Parsing (Language Analyzers + AST Cache)
       │
       ▼
Structural Dependency Graph Update (NetworkX + PageRank Centrality)
       │
       ▼
Software Metric Extraction (LOC, CC, WMC, CBO, LCOM)
       │
       ▼
Evolutionary Software DNA Construction (V_t, E_t, M_t)
       │
       ▼
5D Mutation Detection (Δm_k >= δ_k)
 ├── Magnitude (M)
 ├── Persistence (P)
 ├── Acceleration (A)
 ├── Co-occurrence (C)
 └── Recency (R)
       │
       ▼
Evolutionary Software DNA Index (ESDI) & Source-Level Risk Attribution
       │
       ▼
CI/CD Quality Gate (PASS / WARN / BLOCK / CRITICAL BLOCK)
       │
       ▼
Controlled AST Remediation (Extract Method / Decomposition)
       │
       ▼
Compilation & Test Execution (Isolated Sandbox)
       │
       ▼
Metric Re-Extraction & ESDI Recalculation
       │
       ▼
Acceptance & Validated Evolutionary Baseline Update
```

---

## 2. Directory Structure

```
project-root/
│
├── backend/
│   ├── app/
│   │   ├── api/             # REST route handlers
│   │   ├── core/            # Core analysis engines (AST, Graph, DNA, Mutation, ESDI, Remediation)
│   │   ├── mock_repo/       # Deterministic multi-commit test repositories
│   │   ├── models/          # Pydantic schemas & state models
│   │   ├── storage/         # In-memory & persisted state cache
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # pytest test suite
│   ├── analyzer.py          # Repository multi-version analyzer pipeline
│   ├── database.py          # SQLite persistence layer
│   ├── models.py            # SQLAlchemy database models
│   ├── mutation_analyzer.py # 5D Mutation analyzer
│   ├── esdi_engine.py       # Canonical ESDI computation engine
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Views (DNA, Mutations, ESDI, Remediation, Graph)
│   │   ├── services/        # API client services
│   │   ├── types/           # TypeScript interfaces
│   │   ├── App.tsx          # Main React Application
│   │   └── main.tsx         # React DOM Entrypoint
│   └── package.json         # Frontend dependencies & Vite configuration
│
├── docs/                    # Mathematical models, architecture, and API specs
└── README.md                # Project documentation and reproducibility guide
```

---

## 3. Core Modules & Responsibilities

1. **Git Ingestion & Interceptor (`app/core/git_interceptor.py`, `repo_manager.py`)**:
   Tracks repository commits, detects file changes (additions, modifications, deletions, renames), and provides commit history timelines.

2. **Modular AST Parser & Incremental Engine (`app/core/incremental_ast.py`, `app/core/analyzer_adapters.py`)**:
   Pluggable parsers for Java, Python, and TypeScript. Maintains an AST cache to ensure unchanged files reuse cached ASTs without redundant re-parsing.

3. **Structural Dependency Graph (`app/core/dependency_graph.py`)**:
   Constructs structural graph $G_t = (V_t, E_t)$ capturing method calls, class inheritance, and module imports using NetworkX. Computes PageRank and degree centralities such that $\sum \alpha(u) = 1$.

4. **Software Metric Engine (`app/core/metrics_engine.py`, `ck_extractor.py`)**:
   Extracts standard object-oriented metrics: Lines of Code (LOC), Cyclomatic Complexity (CC), Weighted Methods per Class (WMC), Coupling Between Objects (CBO), and Lack of Cohesion of Methods (LCOM).

5. **Evolutionary DNA Engine (`app/core/dna_engine.py`)**:
   Represents snapshot states $D_t = (V_t, E_t, M_t)$ indexed across historical commits.

6. **5D Mutation Engine (`app/core/mutation_detector.py`, `mutation_analyzer.py`)**:
   Characterizes metric mutations across Magnitude, Persistence, Acceleration, Co-occurrence, and Recency.

7. **ESDI & Risk Engine (`app/core/esdi_calculator.py`, `esdi_engine.py`)**:
   Computes composite ESDI score and attributes risk hierarchically to repository, module, file, class, method, and metric.

8. **CI/CD Quality Gate (`app/core/cicd_gate.py`)**:
   Evaluates pull requests and commits against policy thresholds to issue PASS, WARN, BLOCK, or CRITICAL BLOCK decisions.

9. **Controlled Remediation & Verification (`app/core/remediation_engine.py`, `app/core/verification_engine.py`)**:
   Performs targeted AST refactoring (e.g., Extract Method) in an isolated sandbox, compiles, runs tests, re-extracts metrics, recalculates ESDI, and rolls back if validation conditions are not met.
