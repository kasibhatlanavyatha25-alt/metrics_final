import math
import pytest
import networkx as nx
from app.core.formal_dna_engine import (
    CANONICAL_METRICS,
    NUM_CANONICAL_METRICS,
    W_DIM,
    OMEGA_WEIGHTS,
    OMEGA_MAP,
    DEFAULT_NORMALIZATION_PARAMS,
    DEFAULT_MUTATION_DELTA,
    DEFAULT_PERSISTENCE_WINDOW,
    DEFAULT_RECENCY_LAMBDA,
    sigmoid_normalize_metric,
    compute_normalized_metric_vector,
    compute_mutation_activation,
    compute_5d_vector,
    FiveDimensionalVector,
    compute_node_risk,
    compute_pagerank_centrality,
    compute_esdi_index,
    SoftwareDnaAttributedGraph,
    PythonAstLibCstParser,
)


def test_formal_metric_normalization():
    """
    Validates exact Sigmoid Metric Normalization formula:
    m̃_k(u,t) = 1 / (1 + exp(-γ_k * (m_k(u,t) - θ_k^(0))))
    """
    # At raw == theta, sigmoid value MUST be exactly 0.5
    assert pytest.approx(sigmoid_normalize_metric(50.0, "loc"), rel=1e-5) == 0.5
    assert pytest.approx(sigmoid_normalize_metric(10.0, "cc"), rel=1e-5) == 0.5
    assert pytest.approx(sigmoid_normalize_metric(20.0, "wmc"), rel=1e-5) == 0.5
    assert pytest.approx(sigmoid_normalize_metric(5.0, "cbo"), rel=1e-5) == 0.5
    assert pytest.approx(sigmoid_normalize_metric(0.5, "lcom"), rel=1e-5) == 0.5

    # Test values above theta (should be > 0.5)
    loc_norm = sigmoid_normalize_metric(100.0, "loc")
    expected_loc = 1.0 / (1.0 + math.exp(-0.05 * (100.0 - 50.0)))
    assert pytest.approx(loc_norm, rel=1e-5) == expected_loc

    cc_norm = sigmoid_normalize_metric(20.0, "cc")
    expected_cc = 1.0 / (1.0 + math.exp(-0.25 * (20.0 - 10.0)))
    assert pytest.approx(cc_norm, rel=1e-5) == expected_cc

    # Test full vector
    raw = {"loc": 50.0, "cc": 10.0, "wmc": 20.0, "cbo": 5.0, "lcom": 0.5}
    vec = compute_normalized_metric_vector(raw)
    assert len(vec) == 5
    assert all(pytest.approx(v, rel=1e-5) == 0.5 for v in vec)


def test_formal_mutation_activation():
    """
    Validates Mutation Activation:
    μ(u,k,t) = 1 if (m̃_k(u,t) - m̃_k(u,t-1)) >= δ_k (Default δ_k = 0.05)
    """
    # Exactly at delta: active
    assert compute_mutation_activation(0.55, 0.50, delta=0.05) == 1
    # Above delta: active
    assert compute_mutation_activation(0.60, 0.50, delta=0.05) == 1
    # Below delta: inactive
    assert compute_mutation_activation(0.54, 0.50, delta=0.05) == 0
    # Negative transition (improvement): inactive
    assert compute_mutation_activation(0.40, 0.50, delta=0.05) == 0


def test_formal_5d_vector_components():
    """
    Validates 5D Vector Components Φ(u, k, t) = [M, P, A, C, R]
    1. Magnitude: M = min(1.0, Δm̃_k / max(σ_k, 1e-6))
    2. Persistence: P = (1/H) * Σ_{h=0}^{H-1} μ(u,k,t-h) (Default window H = 5)
    3. Acceleration: A = 2 / (1 + exp(-A_raw)) - 1, where A_raw = max(0.0, (Δm_t - Δm_{t-1}) / max(Δm_{t-1}, 1e-6))
    4. Co-occurrence: C = (1 / (K-1)) * Σ_{j!=k} μ(u,j,t)
    5. Recency: R = exp(-λ * (t_current - t_version_epoch_in_days)) (Default λ = 0.05)
    """
    raw_history = [5.0, 10.0, 20.0]  # Δm_t-1 = 5, Δm_t = 10 => A_raw = (10 - 5) / 5 = 1.0
    norm_history = [0.20, 0.50, 0.70]  # Δm̃_k = 0.20 => M = 0.20 / 0.20 = 1.0
    activations_history = [1, 1, 1]
    current_activations = {"loc": 1, "cc": 1, "wmc": 1, "cbo": 0, "lcom": 0}

    phi = compute_5d_vector(
        metric_name="cc",
        raw_history=raw_history,
        norm_history=norm_history,
        activations_history=activations_history,
        all_current_activations=current_activations,
        version_epoch_days=0.0,
        current_epoch_days=0.0,
        window_h=5,
        lambda_recency=0.05,
    )

    # 1. Magnitude: M = min(1.0, 0.20 / 0.20) = 1.0
    assert phi.magnitude == 1.0

    # 2. Persistence: 3 activations in window of 5 => 3/5 = 0.60
    assert pytest.approx(phi.persistence, rel=1e-3) == 0.60

    # 3. Acceleration: A_raw = 1.0 => A = 2 / (1 + exp(-1.0)) - 1 ≈ 0.4621
    expected_a = (2.0 / (1.0 + math.exp(-1.0))) - 1.0
    assert pytest.approx(phi.acceleration, rel=1e-3) == expected_a

    # 4. Co-occurrence: 2 other active metrics out of 4 => 2/4 = 0.50
    assert pytest.approx(phi.co_occurrence, rel=1e-3) == 0.50

    # 5. Recency: exp(-0.05 * 0) = 1.0
    assert phi.recency == 1.0

    # W_dim dot product: [0.25, 0.20, 0.20, 0.20, 0.15]
    expected_dot = (
        1.0 * 0.25 +
        0.60 * 0.20 +
        expected_a * 0.20 +
        0.50 * 0.20 +
        1.0 * 0.15
    )
    assert pytest.approx(phi.dot_product(W_DIM), rel=1e-3) == expected_dot


def test_formal_esdi_and_pagerank_aggregation():
    """
    Validates ESDI & Centrality Aggregation:
    W_dim = [0.25, 0.20, 0.20, 0.20, 0.15]
    ω = [0.15, 0.25, 0.20, 0.20, 0.20]
    R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t))
    ESDI(t) = Σ_u α(u) * R(u,t)
    where α(u) is NetworkX PageRank normalized such that Σ α(u) = 1.0.
    """
    # 1. Create dependency graph: A -> B -> C
    graph = nx.DiGraph()
    graph.add_edge("ClassA", "ClassB")
    graph.add_edge("ClassB", "ClassC")
    graph.add_edge("ClassC", "ClassA")

    alphas = compute_pagerank_centrality(graph)
    assert len(alphas) == 3
    assert pytest.approx(sum(alphas.values()), rel=1e-5) == 1.0

    # 2. Node Evolutionary Risks
    node_risks = {
        "ClassA": 0.80,
        "ClassB": 0.40,
        "ClassC": 0.20,
    }

    esdi_t, risks, norm_alphas = compute_esdi_index(node_risks, graph=graph)
    expected_esdi = sum(norm_alphas[u] * node_risks[u] for u in node_risks)
    assert pytest.approx(esdi_t, rel=1e-5) == expected_esdi
    assert 0.0 <= esdi_t <= 1.0


def test_software_dna_attributed_graph():
    """
    Validates Software DNA Attributed Graph D_t = (V_t, E_t, M_t)
    """
    dna_graph = SoftwareDnaAttributedGraph(commit_sha="c123", version_label="v1")
    dna_graph.add_node_with_metrics(
        node_id="ServiceA",
        node_type="class",
        raw_metrics={"loc": 100.0, "cc": 15.0, "wmc": 30.0, "cbo": 8.0, "lcom": 0.6},
        file_path="service_a.py",
        package="services"
    )
    dna_graph.add_node_with_metrics(
        node_id="RepositoryB",
        node_type="class",
        raw_metrics={"loc": 50.0, "cc": 5.0, "wmc": 10.0, "cbo": 2.0, "lcom": 0.1},
        file_path="repo_b.py",
        package="db"
    )
    dna_graph.add_dependency_edge("ServiceA", "RepositoryB", "dependency")

    assert dna_graph.graph.number_of_nodes() == 2
    assert dna_graph.graph.number_of_edges() == 1

    node_order, matrix = dna_graph.get_matrix_n_x_k()
    assert len(node_order) == 2
    assert len(matrix) == 2
    assert len(matrix[0]) == 5  # 5 canonical metrics
    assert len(matrix[1]) == 5


def test_python_ast_libcst_parser():
    """
    Validates Reference Python parser utilizing Python standard ast and libcst.
    """
    code = """
import os
import sys

class AccountService:
    def __init__(self, balance: float):
        self.balance = balance
        self.transactions = []

    def deposit(self, amount: float) -> bool:
        if amount > 0:
            self.balance += amount
            self.transactions.append(amount)
            return True
        return False

    def withdraw(self, amount: float) -> bool:
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self.transactions.append(-amount)
            return True
        return False
"""
    ast_tree, cst_tree, metrics_map, deps = PythonAstLibCstParser.parse_python_file(code, "account_service.py")
    assert ast_tree is not None
    assert "AccountService" in metrics_map

    m = metrics_map["AccountService"]
    assert m["loc"] > 10
    assert m["cc"] >= 2  # Has if branches
    assert m["wmc"] >= 3 # Multiple methods
    assert m["cbo"] >= 2 # os, sys
    assert 0.0 <= m["lcom"] <= 1.0
