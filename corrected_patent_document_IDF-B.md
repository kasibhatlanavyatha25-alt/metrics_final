# Invention Disclosure Format (IDF)-B

**Document No.:** 02-IPR-R003 | **Issue No/Date:** 2/01.02.2024 | **Amd. No/Date:** 0/00.00.0000

---

## Title of the invention: System and Method for Evolutionary Software Quality Assessment and Metric Recommendation Using Software DNA Mutation Analysis

### Field /Area of invention: The present invention relates to the field of Software Engineering, Software Quality Assurance, Software Evolution Analysis, Static Program Analysis, Software Metrics, Version-Controlled Software Analysis and Continuous Integration/Continuous Deployment (CI/CD). More particularly, the invention provides a system and method for analyzing the evolution of software quality across successive versions of a software repository. The system extracts structural and software-quality metrics from source code, models the metric state of software as an Evolutionary Software DNA representation, detects significant changes in these metric states as software metric mutations, evaluates the evolutionary risk associated with such mutations using an Evolutionary Software DNA Index (ESDI), identifies the source units and quality metrics contributing to the risk, and generates prioritized metric-specific recommendations. The system operates on version-controlled software repositories and supports multiple programming languages through modular Abstract Syntax Tree (AST) parsing mechanisms.

### Prior Patents and Publications from literature (provide a table summarizing the prior art)

### Summary and background of the invention (Address the gap / Novelty)

Gap in Existing Solutions:

The major gaps addressed by the invention are:

Isolated Snapshot Analysis vs. Unified Evolutionary State: Existing quality assessment tools evaluate isolated static code snapshots rather than modeling an evolving quality trajectory across revisions.

Absence of a Formal Software DNA Representation: Prior art lacks a formal mathematical graph-and-tensor representation capturing structural dependencies and localized metric profiles simultaneously across commits.

Crude Delta Metrics: A raw percentage change in a metric does not indicate whether code degradation is an isolated event or systemic decay. Existing tools do not combine magnitude, persistence, acceleration, co-occurrence, and recency into a unified mutation vector.

Lack of Topological Risk Attribution: Standard analyzers output flat issue lists rather than mapping risk to precise source units weighted by architectural centrality.

Absence of Closed-Loop Remediation Verification: Traditional linters and analyzers stop at issuing advisory recommendations. Existing tools do not execute an automated code transformation, compile, run test suites, reconstruct software DNA, and re-evaluate index thresholds before accepting refactored code.

Novelty and Inventive Step:

The invention introduces the following technical aspects:

Attributed Graph Software DNA Representation: Modeling source repositories across revisions as time-indexed hierarchical property graphs coupled with normalized metric tensors.

Five-Dimensional (5D) Mutation Vector Analysis: A multi-factor mutation engine that quantifies changes using Magnitude (), Persistence (), Acceleration (), Co-occurrence (), and Recency ().

Evolutionary Software DNA Index (ESDI): A graph-centrality-weighted risk index aggregating multi-dimensional mutations across the repository.

Hierarchical Source-Level Attribution: Exact mathematical risk attribution pinpointing the contributing files, classes, methods, and metric vectors.

Closed-Loop CI/CD Validation Pipeline: An automated remediation subsystem that transforms source code, builds and tests the program, extracts updated metrics, reconstructs the Software DNA, and recalculates ESDI to verify risk reduction before pipeline integration.

### Objective(s) of Invention

The primary objectives of the present invention are:

To provide continuous evolutionary assessment of software quality across successive versions of a version-controlled repository.

To represent software quality states as an attributed property graph and metric tensor (Evolutionary Software DNA).

To detect significant metric transitions between successive software versions as metric mutations.

To characterize detected mutations using magnitude, persistence, acceleration, co-occurrence, and recency.

To calculate an Evolutionary Software DNA Index (ESDI) representing aggregate evolutionary quality risk.

To attribute quality risk hierarchically to specific methods, classes, files, and metric dimensions.

To provide automated CI/CD gating decisions categorized into PASS, WARN, BLOCK, and CRITICAL BLOCK.

To execute closed-loop automated remediation, ensuring that candidate fixes are compiled, tested, re-profiled into reconstructed DNA, and verified for ESDI improvement before committing.

### Working principle of the invention (in brief)

The invention analyzes the evolution of software quality across successive versions of a version-controlled software repository. It extracts software-quality metrics from source code, represents the quality state of each version as Evolutionary Software DNA, detects significant metric changes as mutations, and evaluates their evolutionary risk using the Evolutionary Software DNA Index (ESDI). The system operates across the following six computational stages:

Version Ingestion & Parsing: A commit/tag comparator identifies the differences between versions  and  of the Git/VCS repository; a changed-file filter isolates the delta, and a modular, per-language AST parser converts the changed source into an Abstract Syntax Tree.

Extraction & Software DNA Modeling: A structural dependency graph  is built and the metric extraction engine computes LOC, CC, WMC, CBO and LCOM. The metrics are sigmoid-normalized into

and organized into the Software DNA state .

Mutation Detection & 5D Vector Engine: Metric differentials between successive DNA states are passed through a threshold	gate;	each	detected	mutation		is	characterized	by	the	five-dimensional	vector

.

ESDI Computation & Risk Attribution: A unit risk engine computes , a global evaluator computes  using structural centrality, and an attribution matrix engine ranks units and attributes the top drivers to specific (file, class, method, metric) combinations.

CI/CD Gateway & Decision Matrix:  and the unit-level peak risk are evaluated to produce a PASS, WARN, BLOCK or CRITICAL BLOCK decision.

Closed-Loop Remediation & Re-Verification: When the gate fails, a recommendation engine maps the metric mutation and AST context to a refactoring recipe, which is applied as an automated code transformation. The candidate is compiled and tested; if both succeed, the software DNA is reconstructed and  is recalculated. The revision is accepted only if ; otherwise the modifications are rolled back and the integration remains blocked.

### Description of the invention in detail (Include drawing and or photograph as needed)

The invention is a software-centric computational architecture for evolutionary assessment of software quality and metric recommendation. It is described below through its formal data structures and mathematical formulations, remediation rules, system architecture, algorithm, and an experimental case study.

### Formal Mathematical Formulations & Data Structures

Evolutionary Software DNA Data Structure

Software DNA at version  is formally defined as a time-indexed attributed hierarchical property graph:

(1)

is the set of software structural units (functions, methods, classes, modules) at commit/tag version .

represents structural dependencies (method calls, class inheritance, module imports).

​

the metric matrix where row  corresponds to unit  and column  corresponds to normalized metric (such as LOC, CC, WMC, CBO, and LCOM).

The localized metric state of unit  at version  is represented by the vector: Normalized metrics use a logistic sigmoidal function:

where  represents the baseline median threshold for metric  and  is the scaling factor.

Metric Mutation Condition

A metric change for unit  on metric  between versions  and  triggers an active mutation flag according to:

where  is the mutation sensitivity threshold for metric .

The Five Mutation Dimensions:

When , the mutation is mapped to a 5D vector:

Magnitude (): Normalizes the raw metric increase relative to historical variability:

where	is the historical standard deviation of changes for metric .

(2)

(3)

(4)

(5)

(6)

Persistence (): Measures the frequency of metric violations over a sliding historical window of size :

Acceleration (): Computes the second-order discrete rate of degradation across versions , , :

Co-occurrence (): Evaluates multi-metric architectural breakdown across other metrics within the same unit :

Where C(u, k, t) is the co-occurrence score for metric k, source unit u, and version t; K = 5 is the total number of tracked canonical metrics (LOC, CC, WMC, CBO, LCOM); μ(u, j, t) ∈ {0, 1} is the binary mutation indicator for metric j; the metric currently undergoing evaluation (k) is excluded from the numerator summation (j ≠ k); and the normalization denominator is K - 1 = 4. For binary mutation indicators, valid co-occurrence values are strictly discrete: C ∈ {0.00, 0.25, 0.50, 0.75, 1.00}, representing zero, one, two, three, or four other mutated metrics, respectively.

Recency (): Applies an exponential decay weight prioritizing current degradations over historical regressions:

Evolutionary Software DNA Index (ESDI)

(7)

(8)

(9)

(10)

(11)

The aggregate mutation score for unit  on metric  uses dimension weights  (where

):

(12)

The total unit-level evolutionary risk  aggregates across all metrics with importance weights :

(13)

The system-level  computes the graph-weighted risk across all units		, where  represents the structural centrality (e.g., PageRank or Degree Centrality) of unit  in dependency graph	:

(14)

### CI/CD Gate Threshold Mapping

CI/CD decisions are determined via global  and unit-level peak risk :

(15)

### Recommendation Rules & Remediation Mappings

Detected mutations are mapped to metric-specific remediation recipes according to the unit risk level, the dominant metric mutation, and the structural AST pattern detected:

### Complete System Architecture & Operational Workflow

System Architecture Diagram — Evolutionary software quality assessment pipeline (Stages 1–6).

### Algorithmic Pseudocode

Algorithm: Evolutionary Mutation Analysis and Closed-Loop Remediation Gate Input:

Repo: Git Repository

Commit_Prev (t-1), Commit_Curr (t)

Thresholds: δ (Mutation Delta), τ_warn, τ_block (CI/CD Gates) Weights: W_dim = [w_M, w_P, w_A, w_C, w_R], ω = [ω_1, ..., ω_K]

Output:

Gate_Decision ∈ {PASS, WARN, BLOCK, CRITICAL_BLOCK}

Verified_Repo_State

1:  Changed_Files ← GitDiff(Repo, Commit_Prev, Commit_Curr)

2: AST_Prev ← ParseAbstractSyntaxTree(Changed_Files, Commit_Prev) 3: AST_Curr ← ParseAbstractSyntaxTree(Changed_Files, Commit_Curr) 4: Dep_Graph_Curr ← BuildStructuralDependencyGraph(AST_Curr)

5:

6:	for each unit u in ExtractedUnits(AST_Curr) do 7:		m_curr ← ExtractSoftwareMetrics(AST_Curr, u) 8:		m_prev ← ExtractSoftwareMetrics(AST_Prev, u) 9:		m_norm_curr ← SigmoidNormalize(m_curr)

10:	m_norm_prev ← SigmoidNormalize(m_prev) 11:

12:	Unit_Risk[u] ← 0.0

13:	for each metric k in {LOC, CC, WMC, CBO, LCOM} do 14:		Δm_k ← m_norm_curr[k] - m_norm_prev[k]

15:	if Δm_k ≥ δ[k] then

16:	μ[u, k, t] ← 1

17:	Φ[u, k, t] ← ComputeFiveDimensionalVector(u, k, Δm_k, Repo.History) 18:	Score_k ← DotProduct(W_dim, Φ[u, k, t])

19:		Unit_Risk[u] ← Unit_Risk[u] + (ω[k] * Score_k) 20:	else

21:	μ[u, k, t] ← 0

22:	end if

23:	end for

24:	end for

25:

26:	Centrality_Vector α ← ComputePageRank(Dep_Graph_Curr) 27:	ESDI_t ← ∑_{u} (α[u] * Unit_Risk[u])

28:

29:	if ESDI_t < τ_warn and Max(Unit_Risk) < 0.50 then 30:		return PASS, Commit_Curr

31:	else if ESDI_t < τ_block and Max(Unit_Risk) < 0.80 then 32:		EmitAdvisoryWarning(Unit_Risk)

33:		return WARN, Commit_Curr 34:	end if

35:

36:	/* Gating Failed: Trigger Closed-Loop Remediation Subsystem */ 37:	Target_Unit ← ArgMax(Unit_Risk)

38:	Refactor_Recipe ← MatchTransformationRule(Target_Unit, AST_Curr)

39:	AST_Candidate ← ApplyASTTransformation(AST_Curr, Target_Unit, Refactor_Recipe) 40:

41:	Build_Status ← CompileSourceTree(AST_Candidate)

42:	Test_Status ← ExecuteRegressionTestSuite(AST_Candidate) 43:

44:	if Build_Status == SUCCESS and Test_Status == ALL_PASSED then

45:	m_remediated ← ExtractSoftwareMetrics(AST_Candidate, Target_Unit) 46:	ESDI_Remediated ← RecomputeESDI(m_remediated, Dep_Graph_Curr) 47:

48:	if ESDI_Remediated < ESDI_t then

49:	AutoCommitTransformation(Repo, AST_Candidate) 50:	return PASS, AST_Candidate

51:	end if

52:	end if

53:

54:	RollbackModifications(Repo)

55:	if ESDI_t ≥ 0.80 then

56:		return CRITICAL_BLOCK, Commit_Curr 57:	else

58:		return BLOCK, Commit_Curr 59:	end if

### Substantive Figure Data & Illustrative Case Study [Illustrative example — not experimental data]

Expected Results of the Invention [Illustrative example — not experimental data]. Below are illustrative data models and structural descriptions corresponding to Expected Output Figures 1 through 4 (illustrative calculations, not experimental measurements).

#### Expected Output Figure 1 — Version-wise Evolutionary Software DNA

Depicts the longitudinal metric evolution of core system components across successive release tags (v1.0 through v1.4).

#### Expected Output Figure 2 — Software Metric Mutation Result

Visualizes the 5-dimensional mutation vectors  for units that exceeded sensitivity thresholds at commit release v1.3.

Table 3: Detected metric mutation profiling table (commit v1.3) [Illustrative example — not experimental data]. Scores are evaluated with equal dimension weights W_dim = [0.20, 0.20, 0.20, 0.20, 0.20] and normalized using the five-metric co-occurrence denominator K - 1 = 4.

#### Expected Output Figure 3 — Evolutionary Software DNA Index (ESDI)

Traces the repository-wide index  across successive versions relative to the CI/CD deployment thresholds.

At v1.3 the index reaches 0.768 (BLOCK); after validated remediation the index falls to 0.284 at v1.4 (PASS region). Values for v1.0 and v1.1 are shown approximately.

#### Expected Output Figure 4 — Source-Level Evolutionary Risk Attribution

Hierarchical breakdown of system risk showing the concentration of degradation in core modules.

### What is Technology readiness level of your invention? (Tick the appropriate TRL)

Current Validated Readiness: TRL 3 (Experimental Proof of Concept)

Evidence: Algorithmic formulation validated across multi-commit repository histories using synthetic and benchmark datasets; proven automated execution of the 5-dimensional mutation engine and closed-loop test/ESDI recalculation loop.

Target Milestone: TRL 5 (Integrated System Validation in Relevant Environment)

Roadmap: Embedding native GitHub Actions and GitLab CI runner plugins executing containerized AST parsing, dependency mapping, and automated pull-request refactoring transformations in live team environments.

----------------------END OF THE DOCUMENT-----------------------------



## Tables in Document

### Table 0

| Invention Disclosure Format (IDF)-B | Document No. | 02-IPR-R003 |
| --- | --- | --- |
| Invention Disclosure Format (IDF)-B | Issue No/Date | 2/01.02.2024 |
| Invention Disclosure Format (IDF)-B | Amd. No/Date | 0/00.00.0000 |


### Table 1

| Patent/Paper Title | Patent Number | Description/Key Features | Technical Limitations Addressed by the Present Invention | Link |
| --- | --- | --- | --- | --- |
| Methods and systems for generating software quality index | WO2009089294A2 | Generates a software-quality index using source-code metrics, static-analysis violations, fault-prone files, and source-control information. | Computes snapshot quality scores without modeling temporal persistence, acceleration, or multi-metric co-occurrence. Lacks automated closed-loop remediation validation. | https://patents.google.com/ patent/WO2009089294A2/en |
| Technologies for code failure proneness estimation | US8332822B2 | Estimates failure proneness using code metrics, code churn, and historical commit information. | Uses basic statistical churn counts without an attributed structural graph DNA representation or unit-level topological risk weighting. | https://patents.google.com/ patent/US8332822B2/en |
| Analysis of source code changes | US8984485B2 | Employs an AST to evaluate source-code modifications between software versions to determine their effects on code quality. | Focuses on delta changes between two points in time without characterizing evolutionary multi-commit mutation vectors or recalculating closed-loop post-fix impact. | https://patents.google.com/ patent/US8984485B2/en |
| Software intelligence as-a-service | US11947956B2 | Uses software functional building blocks and a software genome representation to identify issues. | Treats “genome” as static functional blocks rather than a time-indexed property graph with 5D mutation dynamics. Does not support automated verification-based CI/CD gating. | https://patents.google.com/ patent/US11947956B2/en |
| Systems and methods for software quality prediction | US11334351B1 | Uses source structure, commit history, and file relationships to identify hotspots. | Produces risk forecasts without isolating specific metric mutation dimensions or running verification pipelines before integration. | https://patents.google.com/ patent/US11334351B1/en |
| Process metric element evaluation method for evolution software | CN112416789A | Evaluates process metrics during software evolution across historical software versions. | Limited to process metric evaluation without closed-loop AST refactoring or composite topological index calculation. | https://patents.google.com/ patent/CN112416789A/en |
| System and method for identifying viable refactorings of program code using a comprehensive test suite | US7669188B2 | Identifies and applies possible refactorings and uses test validation to assess program validity. | Refactorings are test-suite driven without measuring multi-dimensional evolutionary metric mutations or verifying whether refactoring reduces repository-wide evolutionary rot. | https://patents.google.com/ patent/US7669188B2/en |
| Software quality detection method and system, and storage medium | WO2025107406A1 | Employs AST-based control flow and call-graph analysis alongside multiple software metrics. | Evaluates code quality at isolated points in time without an evolutionary software DNA state machine or closed-loop CI/CD remediation gating. | https://patents.google.com/ patent/WO2025107406A1/en |


### Table 2

| Unit Risk Level | Dominant Metric Mutation | Structural AST Pattern Detected | Remediation Recipe / Automated Transformation |
| --- | --- | --- | --- |
|  | Cyclomatic Complexity (CC) | Control flow nesting depth  (nested if /for /switch ) | Extract Method & Guard Clause Injection: Split inner branches into helper functions; replace nested conditional trees with return guard clauses. |
|  | WMC & LCOM | Disjoint clusters of method-field access within a single class | Extract Class Refactoring: Segregate unshared fields and associated methods into a dedicated delegate class; inject delegate via composition. |
|  | Coupling Between Objects (CBO) | High in-degree foreign class instantiations | Dependency Inversion: Introduce abstract interfaces; replace concrete calls with interface parameter passing and factory instantiation. |
|  | LOC & WMC | Monolithic method containing multiple execution stages | Decompose Monolith / Pipeline Pattern: Convert sequential execution blocks into chained command classes or handler pipeline delegates. |


### Table 3

| Unit ID () | Metric () |  | Magnitude () | Persistence () | Acceleration () | Co-occurrence () | Recency () | Score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OrderProcessingService | CC (Complexity) | +7 | 0.85 | 0.75 | 0.82 | 0.50 | 1.00 | 0.784 |
| OrderProcessingService | CBO (Coupling) | +5 | 0.72 | 0.50 | 0.60 | 0.50 | 1.00 | 0.664 |
| UserAuthManager | LOC (Size) | +32 | 0.41 | 0.25 | 0.10 | 0.25 | 1.00 | 0.402 |
| PaymentGatewayAdapter | LCOM (Cohesion) | +0.14 | 0.38 | 0.00 | 0.00 | 0.00 | 1.00 | 0.276 |


### Table 4

| Invention Disclosure Format (IDF)-B | Document No. | 02-IPR-R003 |
| --- | --- | --- |
| Invention Disclosure Format (IDF)-B | Issue No/Date | 2/01.02.2024 |
| Invention Disclosure Format (IDF)-B | Amd. No/Date | 0/00.00.0000 |


### Table 5

| Research | Research | Research | Development | Development | Development | Deployment | Deployment | Deployment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRL 1 | TRL 2 | TRL 3 | TRL 4 | TRL 5 | TRL 6 | TRL 7 | TRL 8 | TRL 9 |
| Basic Principles | Technology | Experimental | Technology | Technology | Technology | System | System | Actual system |
| observed | concept | proof of concept | validated in a | validated in a | demonstrated in | prototype | complete and | proven in an |
|  | formulated |  | lab | relevant | a relevant | demonstration in | qualified | operational |
|  |  |  |  | environment | environment | an operational |  | environment |
|  |  |  |  | (industrially | (industrially | environment |  | (competitive |
|  |  |  |  | relevant in case | relevant in case |  |  | manufacturing |
|  |  |  |  | of key enabling | of key enabling |  |  | in case of key |
|  |  |  |  | technologies) | technologies) |  |  | enabling |
|  |  |  |  |  |  |  |  | technologies, or |
|  |  |  |  |  |  |  |  | in space) |
| Yes | Yes | Yes |  |  |  |  |  |  |


