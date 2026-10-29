import logging
import math
from typing import Dict, List, Optional
import networkx as nx
from app.models.schemas import (
    ClassMutationAnalysis,
    EsdiResponse,
    GateDecision,
    BranchStatus,
)
from app.core.formal_dna_engine import (
    OMEGA_MAP,
    compute_pagerank_centrality,
    compute_esdi_index,
)

logger = logging.getLogger("software_dna.esdi")

# Formal Metric weights: ω = [0.15, 0.25, 0.20, 0.20, 0.20] for [LOC, CC, WMC, CBO, LCOM]
DEFAULT_METRIC_WEIGHTS = OMEGA_MAP.copy()


class ESDICalculator:
    """
    Calculates the Evolutionary Software DNA Index (ESDI) by mathematically
    aggregating 5D mutation risks through PageRank centrality and metric weights:
    
    R(u,t) = Σ_k ω_k * μ(u,k,t) * (W_dim · Φ(u,k,t))
    ESDI(t) = Σ_u α(u) * R(u,t)
    where α(u) is NetworkX PageRank normalized such that Σ α(u) = 1.0.
    """

    def __init__(
        self,
        metric_weights: Optional[Dict[str, float]] = None,
        calibration_bias: float = 0.35,
        steepness: float = 6.0,
    ):
        self.metric_weights = metric_weights or DEFAULT_METRIC_WEIGHTS
        self.calibration_bias = calibration_bias
        self.steepness = steepness

    def calculate_class_esdi(self, analysis: ClassMutationAnalysis) -> float:
        """
        Computes ESDI for an individual class from its 5D mutation scores:
        R(u, t) scaled to [0, 100].
        """
        if not analysis.metric_mutations:
            return 0.0

        # Weighted aggregate risk across metrics: Σ_k ω_k * R_k(u)
        weighted_risk = 0.0
        total_w = 0.0
        for m_name, weight in self.metric_weights.items():
            dim_score = analysis.metric_mutations.get(m_name)
            m_risk = dim_score.risk if dim_score else 0.0
            weighted_risk += weight * m_risk
            total_w += weight

        if total_w > 0:
            weighted_risk = weighted_risk / total_w

        # Apply calibrated sigmoid scaling for class ESDI score (0 - 100)
        logit = self.steepness * (weighted_risk - self.calibration_bias)
        sigmoid_val = 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, logit))))
        esdi_score = round(100.0 * sigmoid_val, 1)

        return esdi_score

    def calculate_system_esdi(
        self,
        class_analyses: Dict[str, ClassMutationAnalysis],
        graph: Optional[nx.DiGraph] = None,
    ) -> EsdiResponse:
        """
        Calculates system-wide aggregate ESDI using PageRank centrality α(u):
        ESDI(t) = Σ_u α(u) * R(u,t)
        
        Determines CI/CD gate status and explanations.
        """
        if not class_analyses:
            return EsdiResponse(
                esdi=0.0,
                aggregate_risk=0.0,
                decision=GateDecision.PASS,
                branch_status=BranchStatus.NORMAL,
                affected_modules=[],
                mutation_count=0,
                reasons=["No active modules analyzed"],
                class_esdi={},
                calibration_bias=self.calibration_bias,
            )

        class_esdis: Dict[str, float] = {}
        node_risks: Dict[str, float] = {}
        all_reasons: List[str] = []
        affected_modules: List[str] = []
        total_severe_mutations = 0

        # Compute ESDI per class
        for c_name, analysis in class_analyses.items():
            c_score = self.calculate_class_esdi(analysis)
            class_esdis[c_name] = c_score
            node_risks[c_name] = analysis.total_risk
            total_severe_mutations += analysis.severe_mutations_count

            if c_score >= 50.0:
                affected_modules.append(c_name)
                for r in analysis.reasons:
                    all_reasons.append(f"[{c_name}] {r}")

        # Compute PageRank-weighted ESDI: ESDI(t) = Σ_u α(u) * R(u,t)
        if graph is not None and graph.number_of_nodes() > 0:
            esdi_raw, _, alphas = compute_esdi_index(class_esdis, graph=graph)
            # Weighted average ESDI across graph
            system_esdi = round(esdi_raw, 1)
        else:
            # When individual hotspot classes are severely mutated, system ESDI reflects the maximum hotspot
            max_class_score = max(class_esdis.values()) if class_esdis else 0.0
            avg_class_score = sum(class_esdis.values()) / len(class_esdis) if class_esdis else 0.0
            system_esdi = max_class_score if max_class_score >= 50.0 else round(avg_class_score, 1)

        # Peak Unit Evolutionary Risk: max_u R(u,t)
        max_unit_risk = max(class_esdis.values()) if class_esdis else 0.0
        critical_units = [u for u, score in class_esdis.items() if score >= 90.0]
        blocked_units = [u for u, score in class_esdis.items() if 80.0 <= score < 90.0]
        warn_units = [u for u, score in class_esdis.items() if 50.0 <= score < 80.0]

        aggregate_risk = round(sum(a.total_risk for a in class_analyses.values()) / len(class_analyses), 3)

        # Enforce Section 7.1.E, Equation 15 of IDF-B:
        # 1. CRITICAL BLOCK: ESDI(t) >= 80.0 OR max_u R(u, t) >= 90.0
        # 2. BLOCK: (65.0 <= ESDI(t) < 80.0) OR (80.0 <= max_u R(u, t) < 90.0)
        # 3. WARN: (35.0 <= ESDI(t) < 65.0 AND max_u R < 80.0) OR (50.0 <= max_u R < 80.0)
        # 4. PASS: (ESDI(t) < 35.0) AND (max_u R(u, t) < 50.0)
        if system_esdi >= 80.0 or max_unit_risk >= 90.0:
            decision = GateDecision.CRITICAL_BLOCK
            branch_status = BranchStatus.QUARANTINED
            culprit = f" [{critical_units[0]} risk = {class_esdis[critical_units[0]]:.1f}/100 >= 90.0]" if critical_units else f" [ESDI = {system_esdi:.1f} >= 80.0]"
            all_reasons.insert(0, f"CRITICAL RISK: Severe evolutionary DNA mutations detected.{culprit} Branch quarantined.")
        elif (65.0 <= system_esdi < 80.0) or (80.0 <= max_unit_risk < 90.0):
            decision = GateDecision.BLOCK
            branch_status = BranchStatus.BLOCKED
            culprit = f" [{blocked_units[0]} risk = {class_esdis[blocked_units[0]]:.1f}/100 >= 80.0]" if blocked_units else f" [ESDI = {system_esdi:.1f} >= 65.0]"
            all_reasons.insert(0, f"HIGH RISK: Architectural degradation thresholds breached.{culprit} Build blocked.")
        elif (35.0 <= system_esdi < 65.0) or (50.0 <= max_unit_risk < 80.0):
            decision = GateDecision.WARN
            branch_status = BranchStatus.WARNING
            culprit = f" [{warn_units[0]} risk = {class_esdis[warn_units[0]]:.1f}/100 >= 50.0]" if warn_units else f" [ESDI = {system_esdi:.1f} >= 35.0]"
            all_reasons.insert(0, f"MODERATE RISK: Moderate mutation detected.{culprit} Review recommended.")
        else:
            decision = GateDecision.PASS
            branch_status = BranchStatus.NORMAL
            all_reasons = [f"Evolutionary software DNA stable within healthy boundaries (ESDI={system_esdi:.1f}, Max Unit Risk={max_unit_risk:.1f})."]

        logger.info(f"[ESDI] System ESDI: {system_esdi} | Max Unit Risk: {max_unit_risk} | Decision: {decision.value} | Status: {branch_status.value}")

        return EsdiResponse(
            esdi=system_esdi,
            aggregate_risk=aggregate_risk,
            decision=decision,
            branch_status=branch_status,
            affected_modules=affected_modules,
            mutation_count=total_severe_mutations,
            reasons=all_reasons,
            class_esdi=class_esdis,
            calibration_bias=self.calibration_bias,
        )
