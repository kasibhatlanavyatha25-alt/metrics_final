import math
from typing import Dict, List, Any, Optional

# Formal Metric Weights: ω = [0.15, 0.25, 0.20, 0.20, 0.20] for [LOC, CC, WMC, CBO, LCOM]
DEFAULT_DNA_METRIC_WEIGHTS = {
    "loc": 0.15,
    "cc": 0.25,
    "wmc": 0.20,
    "cbo": 0.20,
    "lcom": 0.20,
}

# Formal Dimension Weights: W_dim = [0.25, 0.20, 0.20, 0.20, 0.15] for [M, P, A, C, R]
DEFAULT_MUTATION_DIMENSION_WEIGHTS = {
    "magnitude": 0.25,
    "persistence": 0.20,
    "acceleration": 0.20,
    "co_occurrence": 0.20,
    "recency": 0.15,
}

CI_CD_GATE_THRESHOLDS = {
    "PASS": (0.0, 49.99),
    "WARN": (50.0, 74.99),
    "BLOCK": (75.0, 89.99),
    "CRITICAL_BLOCK": (90.0, 100.0)
}

class ESDIEngine:
    """
    Computes the Evolutionary Software DNA Index (ESDI).
    
    ESDI = 0.50 * (DNA Metric Risk) + 0.50 * (Mutation Dimension Risk)
    
    DNA Metric Risk (Weights):
      - CC:   0.25
      - WMC:  0.20
      - CBO:  0.25
      - LCOM: 0.20
      - LOC:  0.10
      
    Mutation Dimension Risk (Weights):
      - Magnitude:     0.30
      - Persistence:   0.20
      - Acceleration:  0.20
      - Co-occurrence: 0.15
      - Recency:       0.15
      
    CI/CD Gate:
      - ESDI < 50        => PASS
      - 50 <= ESDI < 75  => WARN
      - 75 <= ESDI < 90  => BLOCK
      - ESDI >= 90       => CRITICAL BLOCK / QUARANTINE
    """

    @staticmethod
    def normalize_cc_risk(avg_cc: float) -> float:
        # CC > 15 is industry standard high risk threshold
        return round(min(100.0, max(0.0, (avg_cc / 15.0) * 100.0)), 2)

    @staticmethod
    def normalize_wmc_risk(avg_wmc: float) -> float:
        # WMC > 30 is industry standard high risk threshold
        return round(min(100.0, max(0.0, (avg_wmc / 30.0) * 100.0)), 2)

    @staticmethod
    def normalize_cbo_risk(avg_cbo: float) -> float:
        # CBO > 14 is industry standard high coupling threshold
        return round(min(100.0, max(0.0, (avg_cbo / 14.0) * 100.0)), 2)

    @staticmethod
    def normalize_lcom_risk(avg_lcom: float) -> float:
        # LCOM is 0.0 to 1.0 (Lack of cohesion). Direct percentage
        return round(min(100.0, max(0.0, avg_lcom * 100.0)), 2)

    @staticmethod
    def normalize_loc_risk(total_loc: float, avg_loc: float) -> float:
        # Normalizes scale & module bloat risk
        loc_score = (avg_loc / 300.0) * 60.0 + min(40.0, (total_loc / 25000.0) * 40.0)
        return round(min(100.0, max(0.0, loc_score)), 2)

    @classmethod
    def determine_status(
        cls,
        esdi_score: float,
        max_unit_risk: float = 0.0,
        critical_units: Optional[List[str]] = None
    ) -> str:
        """
        Enforces Section 7.1.E, Equation 15 of IDF-B:
        1. CRITICAL BLOCK: ESDI >= 80.0 OR max_u R(u,t) >= 90.0
        2. BLOCK: (65.0 <= ESDI < 80.0) OR (80.0 <= max_u R(u,t) < 90.0)
        3. WARN: (35.0 <= ESDI < 65.0 AND max_u R < 80.0) OR (50.0 <= max_u R < 80.0)
        4. PASS: ESDI < 35.0 AND max_u R(u,t) < 50.0
        """
        if esdi_score >= 80.0 or max_unit_risk >= 90.0:
            return "CRITICAL BLOCK"
        elif (65.0 <= esdi_score < 80.0) or (80.0 <= max_unit_risk < 90.0):
            return "BLOCK"
        elif (35.0 <= esdi_score < 65.0) or (50.0 <= max_unit_risk < 80.0):
            return "WARN"
        else:
            return "PASS"

    @classmethod
    def calculate_esdi(
        cls,
        dna_snapshot: Dict[str, Any],
        project_metric: Dict[str, Any],
        mutation_records: Optional[List[Dict[str, Any]]] = None,
        custom_metric_weights: Optional[Dict[str, float]] = None,
        custom_mutation_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        m_weights = custom_metric_weights or DEFAULT_DNA_METRIC_WEIGHTS.copy()
        mut_weights = custom_mutation_weights or DEFAULT_MUTATION_DIMENSION_WEIGHTS.copy()

        # 1. Calculate DNA Metric Risk Scores (0 - 100)
        loc_val = float(dna_snapshot.get("loc", project_metric.get("total_loc", 0.0)))
        avg_loc_val = float(project_metric.get("avg_loc", loc_val / max(1, project_metric.get("total_classes", 1))))
        cc_val = float(dna_snapshot.get("cc", project_metric.get("avg_complexity", 1.0)))
        wmc_val = float(dna_snapshot.get("wmc", project_metric.get("avg_wmc", 1.0)))
        cbo_val = float(dna_snapshot.get("cbo", project_metric.get("avg_cbo", 0.0)))
        lcom_val = float(dna_snapshot.get("lcom", project_metric.get("avg_lcom", 0.0)))

        loc_risk = cls.normalize_loc_risk(loc_val, avg_loc_val)
        cc_risk = cls.normalize_cc_risk(cc_val)
        wmc_risk = cls.normalize_wmc_risk(wmc_val)
        cbo_risk = cls.normalize_cbo_risk(cbo_val)
        lcom_risk = cls.normalize_lcom_risk(lcom_val)

        # Weighted DNA Metric Risk
        metric_risk = (
            (loc_risk * m_weights.get("loc", 0.10)) +
            (cc_risk * m_weights.get("cc", 0.25)) +
            (wmc_risk * m_weights.get("wmc", 0.20)) +
            (cbo_risk * m_weights.get("cbo", 0.25)) +
            (lcom_risk * m_weights.get("lcom", 0.20))
        )
        metric_risk = round(min(100.0, max(0.0, metric_risk)), 2)

        # 2. Calculate 5D Mutation Dimension Risk Scores (0 - 100)
        has_mutations = mutation_records is not None and len(mutation_records) > 0
        if has_mutations:
            avg_mag = sum(min(100.0, max(0.0, m.get("magnitude", 0.0) * 100.0)) for m in mutation_records) / len(mutation_records)
            avg_pers = sum(m.get("persistence", 0.0) for m in mutation_records) / len(mutation_records)
            avg_accel = sum(m.get("acceleration", 50.0) for m in mutation_records) / len(mutation_records)
            avg_coo = sum(m.get("co_occurrence", 0.0) for m in mutation_records) / len(mutation_records)
            avg_rec = sum(m.get("recency", 50.0) for m in mutation_records) / len(mutation_records)

            mag_risk = round(min(100.0, max(0.0, avg_mag)), 2)
            pers_risk = round(min(100.0, max(0.0, avg_pers)), 2)
            accel_risk = round(min(100.0, max(0.0, avg_accel)), 2)
            coo_risk = round(min(100.0, max(0.0, avg_coo)), 2)
            rec_risk = round(min(100.0, max(0.0, avg_rec)), 2)

            mutation_risk = (
                (mag_risk * mut_weights.get("magnitude", 0.30)) +
                (pers_risk * mut_weights.get("persistence", 0.20)) +
                (accel_risk * mut_weights.get("acceleration", 0.20)) +
                (coo_risk * mut_weights.get("co_occurrence", 0.15)) +
                (rec_risk * mut_weights.get("recency", 0.15))
            )
            mutation_risk = round(min(100.0, max(0.0, mutation_risk)), 2)
            
            # Combine Metric Risk and Mutation Risk equally (50% baseline metrics, 50% evolutionary mutations)
            final_esdi = round(0.50 * metric_risk + 0.50 * mutation_risk, 2)
            policy = "Canonical Mutation-Aware ESDI (50% DNA Metrics + 50% 5D Mutation Dimensions)"
        else:
            mag_risk = pers_risk = accel_risk = coo_risk = rec_risk = 0.0
            mutation_risk = 0.0
            final_esdi = metric_risk
            policy = "Baseline Version Snapshot (DNA Metric Risk Model)"

        final_esdi = round(min(100.0, max(0.0, final_esdi)), 2)
        health_score = round(max(0.0, min(100.0, 100.0 - final_esdi)), 2)
        status = cls.determine_status(final_esdi)

        explanation = (
            f"ESDI Score is {final_esdi}/100 ({status}). "
            f"DNA Metric Risk: {metric_risk}/100 (CC: {cc_risk}, WMC: {wmc_risk}, CBO: {cbo_risk}, LCOM: {lcom_risk}, LOC: {loc_risk}). "
            f"5D Mutation Risk: {mutation_risk}/100 (Magnitude: {mag_risk}, Persistence: {pers_risk}, Acceleration: {accel_risk}, Co-occurrence: {coo_risk}, Recency: {rec_risk})."
        )

        return {
            "esdi_score": final_esdi,
            "health_score": health_score,
            "status": status,
            # DNA Metric Risk Components
            "metric_risk": metric_risk,
            "loc_risk": loc_risk,
            "cc_risk": cc_risk,
            "wmc_risk": wmc_risk,
            "cbo_risk": cbo_risk,
            "lcom_risk": lcom_risk,
            # 5D Mutation Risk Components
            "mutation_risk": mutation_risk,
            "magnitude_risk": mag_risk,
            "persistence_risk": pers_risk,
            "acceleration_risk": accel_risk,
            "co_occurrence_risk": coo_risk,
            "recency_risk": rec_risk,
            # Weights & Explanation
            "metric_weights": m_weights,
            "mutation_weights": mut_weights,
            "weights_used": {"dna_metrics": m_weights, "mutation_dimensions": mut_weights},
            "calculation_policy": policy,
            "explanation": explanation,
            # Legacy compatibility mappings
            "complexity_risk": cc_risk,
            "coupling_risk": cbo_risk,
            "maintainability_risk": round(100.0 - lcom_risk, 2),
            "churn_risk": mag_risk,
            "activity_risk": rec_risk,
            "defect_risk": None,
            "weighted_complexity": round(cc_risk * m_weights.get("cc", 0.25), 2),
            "weighted_coupling": round(cbo_risk * m_weights.get("cbo", 0.25), 2),
            "weighted_maintainability": round(lcom_risk * m_weights.get("lcom", 0.20), 2),
            "weighted_churn": round(mag_risk * mut_weights.get("magnitude", 0.30), 2),
            "weighted_activity": round(rec_risk * mut_weights.get("recency", 0.15), 2),
            "weighted_defect": None
        }

DEFAULT_ESDI_WEIGHTS = {
    "dna_metrics": DEFAULT_DNA_METRIC_WEIGHTS,
    "mutation_dimensions": DEFAULT_MUTATION_DIMENSION_WEIGHTS
}
