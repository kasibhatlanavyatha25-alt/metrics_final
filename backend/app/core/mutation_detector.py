import logging
import math
from typing import Dict, List, Optional, Tuple
from app.models.schemas import (
    DnaRecord,
    MetricVector,
    MutationDimensionScore,
    ClassMutationAnalysis,
)
from app.core.formal_dna_engine import (
    CANONICAL_METRICS,
    NUM_CANONICAL_METRICS,
    W_DIM,
    OMEGA_MAP,
    DEFAULT_NORMALIZATION_PARAMS,
    DEFAULT_MUTATION_DELTA,
    DEFAULT_PERSISTENCE_WINDOW,
    DEFAULT_RECENCY_LAMBDA,
    sigmoid_normalize_metric,
    compute_mutation_activation,
    compute_5d_vector,
    FiveDimensionalVector,
    compute_node_risk,
)

logger = logging.getLogger("software_dna.mutation_detector")

# Formal Dimension Weights: W_dim = [0.25, 0.20, 0.20, 0.20, 0.15]
DIM_WEIGHTS = {
    "magnitude": W_DIM[0],
    "persistence": W_DIM[1],
    "acceleration": W_DIM[2],
    "cooccurrence": W_DIM[3],
    "recency": W_DIM[4],
}

TRACKED_METRICS = CANONICAL_METRICS


class MutationDetector:
    """
    Evaluates 5-dimensional software DNA mutations according to formal mathematical constraints:
    
    1. Metric Normalization: m̃_k(u,t) = 1 / (1 + exp(-γ_k * (m_k(u,t) - θ_k^(0))))
    2. Mutation Activation: μ(u,k,t) = 1 if (m̃_k(u,t) - m̃_k(u,t-1)) >= δ_k
    3. 5D Vector Components:
       - Magnitude: M = min(1.0, Δm̃_k / max(σ_k, 1e-6))
       - Persistence: P = (1/H) * Σ_{h=0}^{H-1} μ(u,k,t-h) (Default window H = 5)
       - Acceleration: A = 2 / (1 + exp(-A_raw)) - 1, where A_raw = max(0.0, (Δm_t - Δm_{t-1}) / max(Δm_{t-1}, 1e-6))
       - Co-occurrence: C = (1 / (K-1)) * Σ_{j!=k} μ(u,j,t)
       - Recency: R = exp(-λ * (t_current - t_version_epoch_in_days)) (Default λ = 0.05)
    4. Node Evolutionary Risk: R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t))
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        recency_lambda: float = DEFAULT_RECENCY_LAMBDA,
        delta_threshold: float = DEFAULT_MUTATION_DELTA,
        persistence_window: int = DEFAULT_PERSISTENCE_WINDOW
    ):
        self.weights = weights or DIM_WEIGHTS
        self.recency_lambda = recency_lambda
        self.delta_threshold = delta_threshold
        self.persistence_window = persistence_window

    def analyze_class_mutations(
        self,
        class_name: str,
        history: List[DnaRecord],
    ) -> ClassMutationAnalysis:
        """
        Analyzes 5D mutations for a class given its historical trajectory.
        """
        if not history:
            return self._empty_analysis(class_name, "N/A", "V0")

        latest_record = history[-1]
        commit_sha = latest_record.commit_sha
        version_label = latest_record.version_label

        if len(history) == 1:
            # First commit: baseline, zero mutation risk
            return self._baseline_analysis(class_name, commit_sha, version_label, latest_record.metrics)

        # 1. Extract raw metric series across all history
        raw_series: Dict[str, List[float]] = {
            "loc": [float(r.metrics.loc) for r in history],
            "cc": [float(r.metrics.cc) for r in history],
            "wmc": [float(r.metrics.wmc) for r in history],
            "cbo": [float(r.metrics.cbo) for r in history],
            "lcom": [float(r.metrics.lcom) for r in history],
        }

        # 2. Compute normalized metric series: m̃_k(u,t) = 1 / (1 + exp(-γ_k * (m_k(u,t) - θ_k)))
        norm_series: Dict[str, List[float]] = {}
        for m_name in TRACKED_METRICS:
            norm_series[m_name] = [
                sigmoid_normalize_metric(val, m_name)
                for val in raw_series[m_name]
            ]

        # 3. Compute mutation activations μ(u,k,t) across transitions
        activation_series: Dict[str, List[int]] = {m: [] for m in TRACKED_METRICS}
        num_records = len(history)
        for t_idx in range(1, num_records):
            for m_name in TRACKED_METRICS:
                curr_n = norm_series[m_name][t_idx]
                prev_n = norm_series[m_name][t_idx - 1]
                curr_r = raw_series[m_name][t_idx]
                prev_r = raw_series[m_name][t_idx - 1]
                raw_rel_delta = (curr_r - prev_r) / max(1.0, prev_r) if (curr_r > prev_r) else 0.0
                mu_val = 1 if ((curr_n - prev_n) >= self.delta_threshold or raw_rel_delta >= self.delta_threshold) else 0
                activation_series[m_name].append(mu_val)

        # Current activations at latest transition t
        current_activations: Dict[str, int] = {
            m_name: activation_series[m_name][-1] if activation_series[m_name] else 0
            for m_name in TRACKED_METRICS
        }

        # 4. Compute 5D Vector Components for each metric
        phi_vectors: Dict[str, FiveDimensionalVector] = {}
        dimension_scores: Dict[str, MutationDimensionScore] = {}
        reasons: List[str] = []

        for m_name in TRACKED_METRICS:
            phi_k = compute_5d_vector(
                metric_name=m_name,
                raw_history=raw_series[m_name],
                norm_history=norm_series[m_name],
                activations_history=activation_series[m_name],
                all_current_activations=current_activations,
                version_epoch_days=0.0,
                current_epoch_days=0.0,
                window_h=self.persistence_window,
                lambda_recency=self.recency_lambda,
            )
            phi_vectors[m_name] = phi_k

            # Dot product with dimensional weights: W_dim · Φ(u,k,t)
            w_list = [
                self.weights.get("magnitude", W_DIM[0]),
                self.weights.get("persistence", W_DIM[1]),
                self.weights.get("acceleration", W_DIM[2]),
                self.weights.get("cooccurrence", W_DIM[3]),
                self.weights.get("recency", W_DIM[4]),
            ]
            metric_risk = round(phi_k.dot_product(w_list), 3)

            # Severity classification
            if metric_risk >= 0.75:
                severity = "CRITICAL"
                reasons.append(f"Critical {m_name.upper()} mutation (Risk: {metric_risk:.2f}, Mag: {phi_k.magnitude:.2f}, Acc: {phi_k.acceleration:.2f})")
            elif metric_risk >= 0.55:
                severity = "HIGH"
                reasons.append(f"High {m_name.upper()} deterioration (Persistence: {phi_k.persistence:.2f})")
            elif metric_risk >= 0.35:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            dimension_scores[m_name] = MutationDimensionScore(
                magnitude=phi_k.magnitude,
                persistence=phi_k.persistence,
                acceleration=phi_k.acceleration,
                cooccurrence=phi_k.co_occurrence,
                recency=phi_k.recency,
                risk=metric_risk,
                severity=severity,
            )

        # 5. Compute Node Evolutionary Risk R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t))
        # If no metric active (μ=0), use unweighted baseline mean for total_risk representation
        active_risk = compute_node_risk(
            phi_vectors=phi_vectors,
            activations=current_activations,
            require_activation=True
        )
        total_class_risk = sum(score.risk for score in dimension_scores.values()) / len(dimension_scores)
        severe_count = sum(1 for s in dimension_scores.values() if s.severity in ("HIGH", "CRITICAL"))

        active_count = sum(current_activations.values())
        if active_count >= 3:
            reasons.append(f"Multi-metric co-occurring mutation ({active_count}/{len(TRACKED_METRICS)} activated simultaneously)")

        logger.info(f"[MUTATION] {class_name} @ {version_label}: Total Risk={total_class_risk:.3f}, Active Risk={active_risk:.3f}, Severe Mutations={severe_count}")

        return ClassMutationAnalysis(
            class_name=class_name,
            commit_sha=commit_sha,
            version_label=version_label,
            metric_mutations=dimension_scores,
            total_risk=round(total_class_risk, 3),
            severe_mutations_count=severe_count,
            reasons=reasons,
        )

    def _baseline_analysis(
        self,
        class_name: str,
        commit_sha: str,
        version_label: str,
        metrics: MetricVector,
    ) -> ClassMutationAnalysis:
        scores: Dict[str, MutationDimensionScore] = {}
        for m in TRACKED_METRICS:
            scores[m] = MutationDimensionScore(
                magnitude=0.0,
                persistence=0.0,
                acceleration=0.0,
                cooccurrence=0.0,
                recency=1.0,
                risk=0.15,
                severity="LOW",
            )
        return ClassMutationAnalysis(
            class_name=class_name,
            commit_sha=commit_sha,
            version_label=version_label,
            metric_mutations=scores,
            total_risk=0.15,
            severe_mutations_count=0,
            reasons=["Initial baseline version established"],
        )

    def _empty_analysis(self, class_name: str, commit_sha: str, version_label: str) -> ClassMutationAnalysis:
        return ClassMutationAnalysis(
            class_name=class_name,
            commit_sha=commit_sha,
            version_label=version_label,
            metric_mutations={},
            total_risk=0.0,
            severe_mutations_count=0,
            reasons=["No DNA history found"],
        )
