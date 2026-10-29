"""
Formal Mathematical Framework for Evolutionary Software DNA Engine.

Implements exact mathematical formulations for:
1. Software DNA Attributed Graph: D_t = (V_t, E_t, M_t)
2. Metric Normalization via Sigmoid: m̃_k(u,t) = 1 / (1 + exp(-γ_k * (m_k(u,t) - θ_k^(0))))
3. Mutation Activation: μ(u,k,t) = 1 if (m̃_k(u,t) - m̃_k(u,t-1)) >= δ_k
4. 5D Vector Components Φ(u,k,t) = [M, P, A, C, R]
5. ESDI & Centrality Aggregation: R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t)), ESDI(t) = Σ_u α(u) * R(u,t)
6. Python AST & LibCST Parser + NetworkX DiGraph representation.
"""

import ast
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
import networkx as nx

try:
    import libcst as cst
except ImportError:
    cst = None

logger = logging.getLogger("software_dna.formal_engine")

# ============================================================================
# 1. FORMAL CONFIGURATION & DEFAULT WEIGHTS
# ============================================================================

# Metric order for vector representation: [LOC, CC, WMC, CBO, LCOM]
CANONICAL_METRICS = ["loc", "cc", "wmc", "cbo", "lcom"]
NUM_CANONICAL_METRICS = len(CANONICAL_METRICS)  # K = 5

# 2. Metric Normalization Sigmoid Parameters: θ_k (midpoint), γ_k (steepness)
DEFAULT_NORMALIZATION_PARAMS: Dict[str, Dict[str, float]] = {
    "loc":  {"theta": 50.0, "gamma": 0.05, "sigma": 0.20},
    "cc":   {"theta": 10.0, "gamma": 0.25, "sigma": 0.20},
    "wmc":  {"theta": 20.0, "gamma": 0.15, "sigma": 0.20},
    "cbo":  {"theta": 5.0,  "gamma": 0.30, "sigma": 0.20},
    "lcom": {"theta": 0.5,  "gamma": 2.0,  "sigma": 0.20},
}

# 3. Mutation Activation Threshold: δ_k = 0.05 across all metrics
DEFAULT_MUTATION_DELTA = 0.05

# 4. 5D Mutation Dimension Parameters
DEFAULT_PERSISTENCE_WINDOW = 5  # H = 5
DEFAULT_RECENCY_LAMBDA = 0.05   # λ = 0.05

# 5. Weights
# W_dim = [0.25, 0.20, 0.20, 0.20, 0.15] -> [M, P, A, C, R]
W_DIM = [0.25, 0.20, 0.20, 0.20, 0.15]

# ω = [0.15, 0.25, 0.20, 0.20, 0.20] -> [LOC, CC, WMC, CBO, LCOM]
OMEGA_WEIGHTS = [0.15, 0.25, 0.20, 0.20, 0.20]
OMEGA_MAP = dict(zip(CANONICAL_METRICS, OMEGA_WEIGHTS))


# ============================================================================
# 2. MATHEMATICAL NORMALIZATION & 5D VECTOR COMPUTATIONS
# ============================================================================

def sigmoid_normalize_metric(
    raw_value: float,
    metric_name: str,
    theta: Optional[float] = None,
    gamma: Optional[float] = None
) -> float:
    """
    Computes Sigmoid Normalization:
    m̃_k(u,t) = 1 / (1 + exp(-γ_k * (m_k(u,t) - θ_k^(0))))
    """
    params = DEFAULT_NORMALIZATION_PARAMS.get(metric_name.lower(), {"theta": 10.0, "gamma": 0.25})
    th = theta if theta is not None else params["theta"]
    ga = gamma if gamma is not None else params["gamma"]

    z = -ga * (float(raw_value) - th)
    # Clip z to prevent float overflow in exp
    z_clipped = max(-50.0, min(50.0, z))
    return 1.0 / (1.0 + math.exp(z_clipped))


def compute_normalized_metric_vector(raw_metrics: Dict[str, float]) -> List[float]:
    """
    Transforms raw metrics [LOC, CC, WMC, CBO, LCOM] into normalized vector m̃.
    """
    return [
        sigmoid_normalize_metric(raw_metrics.get(k, 0.0), k)
        for k in CANONICAL_METRICS
    ]


def compute_mutation_activation(
    curr_norm: float,
    prev_norm: float,
    delta: float = DEFAULT_MUTATION_DELTA
) -> int:
    """
    Computes Mutation Activation:
    μ(u,k,t) = 1 if (m̃_k(u,t) - m̃_k(u,t-1)) >= δ_k else 0
    """
    return 1 if (curr_norm - prev_norm) >= delta else 0


@dataclass
class FiveDimensionalVector:
    """
    5D Mutation Vector Φ(u, k, t) = [M, P, A, C, R]
    """
    magnitude: float       # M
    persistence: float     # P
    acceleration: float    # A
    co_occurrence: float   # C
    recency: float         # R

    def to_list(self) -> List[float]:
        return [self.magnitude, self.persistence, self.acceleration, self.co_occurrence, self.recency]

    def dot_product(self, weights: Optional[List[float]] = None) -> float:
        w = weights or W_DIM
        return (
            self.magnitude * w[0] +
            self.persistence * w[1] +
            self.acceleration * w[2] +
            self.co_occurrence * w[3] +
            self.recency * w[4]
        )


def compute_5d_vector(
    metric_name: str,
    raw_history: List[float],
    norm_history: List[float],
    activations_history: List[int],
    all_current_activations: Dict[str, int],
    version_epoch_days: float = 0.0,
    current_epoch_days: float = 0.0,
    window_h: int = DEFAULT_PERSISTENCE_WINDOW,
    lambda_recency: float = DEFAULT_RECENCY_LAMBDA,
    sigma_k: Optional[float] = None
) -> FiveDimensionalVector:
    """
    Computes the 5D Mutation Vector Φ(u, k, t):
    
    1. Magnitude: M = min(1.0, Δm̃_k / max(σ_k, 1e-6))
    2. Persistence: P = (1/H) * Σ_{h=0}^{H-1} μ(u,k,t-h)
    3. Acceleration: A = 2 / (1 + exp(-A_raw)) - 1, where A_raw = max(0.0, (Δm_t - Δm_{t-1}) / max(Δm_{t-1}, 1e-6))
    4. Co-occurrence: C = (1 / (K-1)) * Σ_{j!=k} μ(u,j,t)
    5. Recency: R = exp(-λ * (t_current - t_version_epoch_in_days))
    """
    params = DEFAULT_NORMALIZATION_PARAMS.get(metric_name.lower(), {"sigma": 0.20})
    sig = sigma_k if sigma_k is not None else params.get("sigma", 0.20)

    # 1. Magnitude: M = min(1.0, Δm̃_k / max(σ_k, 1e-6))
    if len(norm_history) >= 2:
        delta_m_tilde = max(0.0, norm_history[-1] - norm_history[-2])
    else:
        delta_m_tilde = 0.0
    
    if len(raw_history) >= 2 and raw_history[-2] > 0:
        raw_rel = max(0.0, (raw_history[-1] - raw_history[-2]) / max(1.0, raw_history[-2]))
    else:
        raw_rel = 0.0

    magnitude = min(1.0, max(delta_m_tilde / max(sig, 1e-6), raw_rel))

    # 2. Persistence: P = (1/H) * Σ_{h=0}^{H-1} μ(u,k,t-h)
    if activations_history:
        recent_activations = activations_history[-window_h:]
        persistence = sum(recent_activations) / float(window_h)
        persistence = min(1.0, max(0.0, persistence))
    else:
        persistence = 0.0

    # 3. Acceleration: A = 2 / (1 + exp(-A_raw)) - 1
    # where A_raw = max(0.0, (Δm_t - Δm_{t-1}) / max(Δm_{t-1}, 1e-6))
    if len(raw_history) >= 3:
        delta_m_t = max(0.0, raw_history[-1] - raw_history[-2])
        delta_m_prev = max(0.0, raw_history[-2] - raw_history[-3])
        if delta_m_prev > 1e-6:
            a_raw = max(0.0, (delta_m_t - delta_m_prev) / delta_m_prev)
        else:
            a_raw = max(0.0, delta_m_t / 1e-6) if delta_m_t > 0 else 0.0
        a_raw_clipped = min(50.0, a_raw)
        acceleration = (2.0 / (1.0 + math.exp(-a_raw_clipped))) - 1.0
        acceleration = min(1.0, max(0.0, acceleration))
    elif len(raw_history) == 2:
        delta_m_t = max(0.0, raw_history[-1] - raw_history[-2])
        a_raw = min(50.0, delta_m_t)
        acceleration = (2.0 / (1.0 + math.exp(-a_raw))) - 1.0
        acceleration = min(1.0, max(0.0, acceleration))
    else:
        acceleration = 0.0

    # 4. Co-occurrence: C = (1 / (K-1)) * Σ_{j!=k} μ(u,j,t)
    other_activations_sum = sum(
        act for other_k, act in all_current_activations.items()
        if other_k != metric_name
    )
    k_minus_1 = max(1, NUM_CANONICAL_METRICS - 1)  # K-1 = 4
    co_occurrence = min(1.0, max(0.0, other_activations_sum / float(k_minus_1)))

    # 5. Recency: R = exp(-λ * (t_current - t_version_epoch_in_days))
    time_diff_days = max(0.0, current_epoch_days - version_epoch_days)
    recency = math.exp(-lambda_recency * time_diff_days)
    recency = min(1.0, max(0.0, recency))

    return FiveDimensionalVector(
        magnitude=round(magnitude, 4),
        persistence=round(persistence, 4),
        acceleration=round(acceleration, 4),
        co_occurrence=round(co_occurrence, 4),
        recency=round(recency, 4),
    )


# ============================================================================
# 3. ESDI & PAGERANK CENTRALITY AGGREGATION
# ============================================================================

def compute_node_risk(
    phi_vectors: Dict[str, FiveDimensionalVector],
    activations: Dict[str, int],
    omega_weights: Optional[Dict[str, float]] = None,
    w_dim: Optional[List[float]] = None,
    require_activation: bool = True
) -> float:
    """
    Computes Node Evolutionary Risk:
    R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t))
    """
    weights = omega_weights or OMEGA_MAP
    w = w_dim or W_DIM
    node_risk = 0.0

    for k in CANONICAL_METRICS:
        omega_k = weights.get(k, 0.20)
        phi_k = phi_vectors.get(k, FiveDimensionalVector(0.0, 0.0, 0.0, 0.0, 0.0))
        mu_k = activations.get(k, 1 if not require_activation else 0)

        # Dot product: W_dim · Φ(u,k,t)
        dot_score = phi_k.dot_product(w)
        node_risk += omega_k * mu_k * dot_score

    return node_risk


def compute_pagerank_centrality(graph: nx.DiGraph) -> Dict[str, float]:
    """
    Computes normalized PageRank centrality α(u) for all nodes u in graph:
    Σ_u α(u) = 1.0
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: 1.0}

    try:
        # Compute PageRank with standard damping factor 0.85
        pr = nx.pagerank(graph, alpha=0.85, max_iter=100)
    except Exception as ex:
        logger.warning(f"PageRank computation fallback to uniform: {ex}")
        pr = {u: 1.0 / float(n) for u in nodes}

    total_pr = sum(pr.values())
    if total_pr > 0:
        normalized_pr = {u: val / total_pr for u, val in pr.items()}
    else:
        normalized_pr = {u: 1.0 / float(n) for u in nodes}

    return normalized_pr


def compute_esdi_index(
    node_risks: Dict[str, float],
    graph: Optional[nx.DiGraph] = None,
    centrality_map: Optional[Dict[str, float]] = None
) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    """
    Computes Evolutionary Software DNA Index:
    ESDI(t) = Σ_u α(u) * R(u,t)
    where α(u) is NetworkX PageRank normalized such that Σ α(u) = 1.0.
    
    Returns: (esdi_score, node_risks, pagerank_alphas)
    """
    if not node_risks:
        return 0.0, {}, {}

    if centrality_map is not None:
        alphas = centrality_map
    elif graph is not None and graph.number_of_nodes() > 0:
        alphas = compute_pagerank_centrality(graph)
    else:
        # Uniform centrality if no graph provided
        n = len(node_risks)
        uniform_val = 1.0 / float(n)
        alphas = {u: uniform_val for u in node_risks}

    # Ensure all nodes in node_risks have an alpha
    for u in node_risks:
        if u not in alphas:
            alphas[u] = 0.0

    # Re-normalize alphas to sum to 1.0
    total_alpha = sum(alphas.get(u, 0.0) for u in node_risks)
    if total_alpha > 0:
        normalized_alphas = {u: alphas.get(u, 0.0) / total_alpha for u in node_risks}
    else:
        n = len(node_risks)
        normalized_alphas = {u: 1.0 / float(n) for u in node_risks}

    # Compute ESDI(t) = Σ_u α(u) * R(u,t)
    esdi_t = sum(normalized_alphas[u] * node_risks[u] for u in node_risks)

    return esdi_t, node_risks, normalized_alphas


# ============================================================================
# 4. SOFTWARE DNA ATTRIBUTED GRAPH: D_t = (V_t, E_t, M_t)
# ============================================================================

@dataclass
class SoftwareDnaAttributedGraph:
    """
    Software DNA Attributed Graph:
    D_t = (V_t, E_t, M_t)
    where:
      - V_t are AST nodes (modules, classes, functions)
      - E_t are dependency edges
      - M_t is the N x K normalized metric matrix
    """
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    metric_matrix: Dict[str, List[float]] = field(default_factory=dict)  # u -> [m̃_loc, m̃_cc, m̃_wmc, m̃_cbo, m̃_lcom]
    raw_metric_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    commit_sha: str = "HEAD"
    version_label: str = "t"

    def add_node_with_metrics(
        self,
        node_id: str,
        node_type: str,
        raw_metrics: Dict[str, float],
        file_path: str = "",
        package: str = "root"
    ):
        """Adds AST node u to V_t with raw and normalized metrics in M_t."""
        norm_vector = compute_normalized_metric_vector(raw_metrics)
        self.metric_matrix[node_id] = norm_vector
        self.raw_metric_matrix[node_id] = raw_metrics

        self.graph.add_node(
            node_id,
            node_type=node_type,
            file_path=file_path,
            package=package,
            raw_metrics=raw_metrics,
            normalized_metrics=norm_vector,
        )

    def add_dependency_edge(self, source: str, target: str, dependency_type: str = "reference"):
        """Adds dependency edge (u, v) to E_t."""
        if self.graph.has_node(source) and self.graph.has_node(target):
            self.graph.add_edge(source, target, dependency_type=dependency_type)

    def get_matrix_n_x_k(self) -> Tuple[List[str], List[List[float]]]:
        """Returns ordered node IDs and the N x K normalized metric matrix M_t."""
        node_order = list(self.graph.nodes())
        matrix = [self.metric_matrix.get(u, [0.0] * NUM_CANONICAL_METRICS) for u in node_order]
        return node_order, matrix


# ============================================================================
# 5. PYTHON AST & LIBCST PARSER
# ============================================================================

class PythonAstLibCstParser:
    """
    Reference Python Parser utilizing both Python standard `ast` module and `libcst`.
    Extracts AST nodes V_t (modules, classes, functions), dependency edges E_t,
    and calculates [LOC, CC, WMC, CBO, LCOM].
    """

    @staticmethod
    def calculate_python_loc(source_code: str) -> int:
        """Counts non-empty, non-comment lines of Python code."""
        lines = source_code.splitlines()
        loc = 0
        in_multiline_str = False
        quote_char = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if in_multiline_str:
                if quote_char and quote_char in line:
                    in_multiline_str = False
                    quote_char = None
                continue

            if line.startswith('"""') or line.startswith("'''"):
                q = line[:3]
                if line.count(q) < 2:
                    in_multiline_str = True
                    quote_char = q
                continue

            if line.startswith("#"):
                continue

            loc += 1

        return max(1, loc)

    @classmethod
    def calculate_function_cyclomatic_complexity(cls, func_node: Any) -> int:
        """
        CC(func) = 1 + number of branching decision points.
        """
        cc = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.IfExp, ast.Assert)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                cc += max(1, len(node.values) - 1)
            elif hasattr(ast, 'Match') and isinstance(node, ast.Match):
                cc += len(getattr(node, 'cases', []))
        return cc

    @classmethod
    def parse_python_file(
        cls,
        source_code: str,
        file_path: str = ""
    ) -> Tuple[Optional[ast.AST], Optional[Any], Dict[str, Dict[str, float]], List[Tuple[str, str, str]]]:
        """
        Parses a Python file using standard `ast` and optionally `libcst`.
        
        Returns:
            - standard_ast: ast.Module
            - cst_tree: libcst.Module (if libcst is available)
            - metrics_map: Dict[node_name, {"loc": ..., "cc": ..., "wmc": ..., "cbo": ..., "lcom": ...}]
            - dependencies: List[Tuple[source_node, target_node, dep_type]]
        """
        total_loc = cls.calculate_python_loc(source_code)
        metrics_map: Dict[str, Dict[str, float]] = {}
        dependencies: List[Tuple[str, str, str]] = []

        # 1. Parse standard AST
        try:
            tree = ast.parse(source_code)
        except Exception as e:
            logger.debug(f"Standard AST parse failed for {file_path}: {e}")
            tree = None

        # 2. Parse LibCST if available
        cst_tree = None
        if cst is not None:
            try:
                cst_tree = cst.parse_module(source_code)
            except Exception as e:
                logger.debug(f"LibCST parse failed for {file_path}: {e}")
                cst_tree = None

        if tree is None:
            mod_name = file_path or "Module"
            metrics_map[mod_name] = {"loc": float(total_loc), "cc": 1.0, "wmc": 1.0, "cbo": 0.0, "lcom": 0.0}
            return None, cst_tree, metrics_map, dependencies

        # Collect top-level imports for CBO
        imported_modules: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        # Find classes and standalone functions
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        top_functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        if not classes:
            # Standalone module / script
            mod_name = file_path or "Module"
            if top_functions:
                ccs = [cls.calculate_function_cyclomatic_complexity(f) for f in top_functions]
                max_cc = max(ccs)
                wmc = sum(ccs)
            else:
                top_cc = 1
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                        top_cc += 1
                max_cc = top_cc
                wmc = top_cc

            metrics_map[mod_name] = {
                "loc": float(total_loc),
                "cc": float(max_cc),
                "wmc": float(wmc),
                "cbo": float(len(imported_modules)),
                "lcom": 0.0,
            }

            for imp in imported_modules:
                dependencies.append((mod_name, imp, "import"))

            return tree, cst_tree, metrics_map, dependencies

        # Process each class
        for cls_node in classes:
            cls_name = cls_node.name
            methods = [n for n in cls_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

            if methods:
                ccs = [cls.calculate_function_cyclomatic_complexity(m) for m in methods]
                max_cc = max(ccs)
                wmc = sum(ccs)
            else:
                max_cc = 1
                wmc = 1

            # Coupling Between Objects (CBO)
            coupled_types: Set[str] = set(imported_modules)
            for base in cls_node.bases:
                if isinstance(base, ast.Name):
                    coupled_types.add(base.id)
                    dependencies.append((cls_name, base.id, "inheritance"))

            for sub_node in ast.walk(cls_node):
                if isinstance(sub_node, ast.Call) and isinstance(sub_node.func, ast.Name):
                    if sub_node.func.id != cls_name:
                        coupled_types.add(sub_node.func.id)
                        dependencies.append((cls_name, sub_node.func.id, "instantiation"))

            # Lack of Cohesion of Methods (LCOM - Henderson-Sellers formula)
            fields: Set[str] = set()
            method_field_access: Dict[str, Set[str]] = {}

            for m in methods:
                method_field_access[m.name] = set()
                for node in ast.walk(m):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
                        fields.add(node.attr)
                        method_field_access[m.name].add(node.attr)

            m_count = len(methods)
            a_count = len(fields)
            if m_count <= 1 or a_count == 0:
                lcom = 0.0
            else:
                avg_access = sum(len(accs) for accs in method_field_access.values()) / float(a_count)
                raw_lcom = (avg_access - m_count) / (1.0 - m_count)
                lcom = round(max(0.0, min(1.0, float(raw_lcom))), 4)

            metrics_map[cls_name] = {
                "loc": float(total_loc),
                "cc": float(max_cc),
                "wmc": float(wmc),
                "cbo": float(len(coupled_types)),
                "lcom": float(lcom),
            }

        return tree, cst_tree, metrics_map, dependencies
