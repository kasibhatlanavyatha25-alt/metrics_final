import math
from typing import Dict, List, Any, Optional

CANONICAL_DNA_METRICS = ["loc", "cc", "wmc", "cbo", "lcom"]

DEFAULT_MUTATION_THRESHOLDS = {
    "risky_increase_pct": 15.0,
    "critical_increase_pct": 40.0,
    "loc_risky_pct": 25.0,
    "loc_critical_pct": 50.0,
}

class MutationAnalyzer:
    """
    Evaluates metric transitions V(t-1) -> V(t) using the 5-Dimensional Mutation Model:
    1. Magnitude: Normalized relative delta (m_t - m_{t-1}) / max(1, |m_{t-1}|)
    2. Persistence: Fraction of consecutive transitions where the metric deteriorated
    3. Acceleration: Second difference (delta_t - delta_{t-1}) normalized to 0-100
    4. Co-occurrence: Fraction of the 5 canonical DNA metrics deteriorating in the same transition
    5. Recency: Deterministic time/version distance decay factor (t / N * 100)
    """

    @staticmethod
    def calculate_magnitude(prev_val: float, curr_val: float) -> (float, float, float):
        delta = round(curr_val - prev_val, 4)
        safe_base = max(1.0, abs(prev_val))
        magnitude_ratio = delta / safe_base
        pct_change = round(magnitude_ratio * 100.0, 2)
        return delta, magnitude_ratio, pct_change

    @staticmethod
    def calculate_persistence(
        history_values: List[float],
        window_h: int = 5
    ) -> float:
        """
        P = (1 / min(len(history), H)) * sum(mu(u, k, t-h)) * 100.0
        If only 1 version transition exists, P = 100.0 if delta > 0 else 0.0. Never hardcode 50.0.
        """
        if len(history_values) < 2:
            return 0.0
        
        # Consider the recent window of transitions
        transitions = []
        for i in range(1, len(history_values)):
            is_deterioration = 1 if history_values[i] > history_values[i - 1] + 1e-4 else 0
            transitions.append(is_deterioration)
            
        recent_window = transitions[-window_h:]
        denom = min(len(transitions), window_h)
        if denom == 0:
            return 0.0
        persistence = (sum(recent_window) / float(denom)) * 100.0
        return round(min(100.0, max(0.0, persistence)), 2)

    @staticmethod
    def calculate_acceleration(
        prev_prev_val: Optional[float],
        prev_val: float,
        curr_val: float
    ) -> float:
        """
        A requires at least two consecutive deltas: delta_t and delta_{t-1}.
        If delta_{t-1} does not exist or history < 3 versions, Acceleration MUST BE 0.0.
        When delta_{t-1} exists:
          A_raw = max(0.0, (delta_t - delta_{t-1}) / max(delta_{t-1}, 1e-6))
          A = ((2.0 / (1.0 + exp(-A_raw))) - 1.0) * 100.0
        """
        if prev_prev_val is None:
            return 0.0
            
        delta_t = max(0.0, curr_val - prev_val)
        delta_prev = max(0.0, prev_val - prev_prev_val)
        
        if delta_prev > 1e-6:
            a_raw = max(0.0, (delta_t - delta_prev) / delta_prev)
        elif delta_t > 0:
            a_raw = max(0.0, delta_t / 1e-6)
        else:
            return 0.0
            
        a_raw_clipped = min(50.0, a_raw)
        accel_ratio = (2.0 / (1.0 + math.exp(-a_raw_clipped))) - 1.0
        return round(min(100.0, max(0.0, accel_ratio * 100.0)), 2)

    @staticmethod
    def calculate_co_occurrence(
        other_deteriorated_metrics_count: int,
        total_other_metrics: int = 4
    ) -> float:
        """
        C = (1 / (K - 1)) * sum_{j != k} mu(u, j, t) * 100.0
        Calculated strictly across the other 4 canonical metrics (K=5).
        If no other metric mutated in u, C must be 0.0. Never hardcode 50.0.
        """
        if total_other_metrics <= 0:
            return 0.0
        ratio = (other_deteriorated_metrics_count / float(total_other_metrics)) * 100.0
        return round(min(100.0, max(0.0, ratio)), 2)

    @staticmethod
    def calculate_recency(
        version_index: int,
        total_versions: int
    ) -> float:
        """
        Deterministic recency function based on version position:
        recency = (version_index / total_versions) * 100
        """
        if total_versions <= 1:
            return 100.0
        ratio = (version_index / float(total_versions)) * 100.0
        return round(min(100.0, max(0.0, ratio)), 2)

    @classmethod
    def evaluate_metric_mutation(
        cls,
        metric_name: str,
        prev_val: float,
        curr_val: float,
        module_name: str,
        history_values: Optional[List[float]] = None,
        prev_prev_val: Optional[float] = None,
        other_co_occurring_deteriorations: int = 0,
        co_occurring_deteriorations: Optional[int] = None,
        version_index: int = 1,
        total_versions: int = 1,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        cfg = thresholds or DEFAULT_MUTATION_THRESHOLDS
        delta, magnitude_ratio, pct_change = cls.calculate_magnitude(prev_val, curr_val)
        
        hist = history_values if history_values else [prev_val, curr_val]
        persistence = cls.calculate_persistence(hist)
        acceleration = cls.calculate_acceleration(prev_prev_val, prev_val, curr_val)
        
        coo_count = co_occurring_deteriorations if co_occurring_deteriorations is not None else other_co_occurring_deteriorations
        co_occurrence = cls.calculate_co_occurrence(coo_count, total_other_metrics=4)
        recency = cls.calculate_recency(version_index, total_versions)

        # Higher is worse for all 5 canonical DNA metrics (LOC, CC, WMC, CBO, LCOM)
        is_deterioration = delta > 1e-4

        # Composite mutation risk score (0 to 100)
        # Weights: W_dim = [0.25, 0.20, 0.20, 0.20, 0.15] -> [Magnitude, Persistence, Acceleration, Co-occurrence, Recency]
        mag_norm = min(100.0, max(0.0, pct_change))
        composite_score = (
            (mag_norm * 0.25) +
            (persistence * 0.20) +
            (acceleration * 0.20) +
            (co_occurrence * 0.20) +
            (recency * 0.15)
        ) if is_deterioration else 0.0

        composite_score = round(min(100.0, max(0.0, composite_score)), 2)

        # Severity classification
        if is_deterioration:
            is_loc = metric_name.lower() == "loc"
            crit_thresh = cfg["loc_critical_pct"] if is_loc else cfg["critical_increase_pct"]
            risk_thresh = cfg["loc_risky_pct"] if is_loc else cfg["risky_increase_pct"]

            if pct_change >= crit_thresh or composite_score >= 60.0:
                severity = "CRITICAL"
                reason = f"{metric_name} surged by +{pct_change}% ({prev_val} -> {curr_val}) with high mutation persistence ({persistence}%) and acceleration."
            elif pct_change >= risk_thresh or composite_score >= 35.0:
                severity = "RISKY"
                reason = f"{metric_name} increased by +{pct_change}% ({prev_val} -> {curr_val}) exceeding normal stability threshold."
            else:
                severity = "HEALTHY"
                reason = f"{metric_name} increased mildly by +{pct_change}% ({prev_val} -> {curr_val}) within acceptable tolerance."
        elif abs(delta) < 1e-4:
            severity = "HEALTHY"
            if curr_val > 15.0 and metric_name.lower() in ("cc", "cyclomatic_complexity", "wmc", "cbo"):
                reason = f"Stable but persistently high {metric_name} ({curr_val}) detected across versions."
            else:
                reason = f"{metric_name} remained stable ({prev_val} -> {curr_val})."
        else:
            severity = "HEALTHY"
            reason = f"{metric_name} improved (decreased by {abs(pct_change)}% from {prev_val} to {curr_val})."

        return {
            "target_type": "CLASS" if module_name != "Project" else "PROJECT",
            "module_name": module_name,
            "metric_name": metric_name.upper(),
            "previous_value": round(prev_val, 2),
            "current_value": round(curr_val, 2),
            "delta_value": delta,
            "percentage_change": pct_change,
            "is_deterioration": is_deterioration,
            "severity": severity,
            "magnitude": round(magnitude_ratio, 4),
            "persistence": persistence,
            "acceleration": acceleration,
            "co_occurrence": co_occurrence,
            "recency": recency,
            "composite_mutation_score": composite_score,
            "reason": reason,
            "is_combined": False,
            "combined_factors": None
        }

    @classmethod
    def analyze_class_mutations(
        cls,
        prev_classes: List[Dict[str, Any]],
        curr_classes: List[Dict[str, Any]],
        version_idx: int = 1,
        total_versions: int = 2
    ) -> List[Dict[str, Any]]:
        prev_map = {c["class_name"]: c for c in prev_classes}
        curr_map = {c["class_name"]: c for c in curr_classes}
        mutations = []
        metrics_to_check = ["loc", "wmc", "cbo", "lcom", "cyclomatic_complexity"]

        for c_name, curr_data in curr_map.items():
            prev_data = prev_map.get(c_name)
            if not prev_data:
                continue

            deteriorating_count = 0
            for m in metrics_to_check:
                p_v = float(prev_data.get(m, 0.0) or 0.0)
                c_v = float(curr_data.get(m, 0.0) or 0.0)
                if c_v > p_v + 1e-4:
                    deteriorating_count += 1

            for m in metrics_to_check:
                p_v = float(prev_data.get(m, 0.0) or 0.0)
                c_v = float(curr_data.get(m, 0.0) or 0.0)
                is_m_deteriorating = 1 if c_v > p_v + 1e-4 else 0
                other_deteriorating = max(0, deteriorating_count - is_m_deteriorating)
                eval_res = cls.evaluate_metric_mutation(
                    metric_name=m,
                    prev_val=p_v,
                    curr_val=c_v,
                    module_name=c_name,
                    history_values=[p_v, c_v],
                    co_occurring_deteriorations=other_deteriorating,
                    version_index=version_idx,
                    total_versions=total_versions
                )
                eval_res["target_type"] = "CLASS"
                eval_res["is_combined"] = False
                eval_res["combined_factors"] = None
                mutations.append(eval_res)

        return mutations

    @classmethod
    def analyze_project_dna_mutations(
        cls,
        prev_dna: Dict[str, Any],
        curr_dna: Dict[str, Any],
        version_idx: int = 1,
        total_versions: int = 2
    ) -> List[Dict[str, Any]]:
        mutations = []
        metrics_to_check = ["loc", "cc", "wmc", "cbo", "lcom"]

        deteriorating_count = 0
        for m in metrics_to_check:
            p_v = float(prev_dna.get(m, 0.0) or 0.0)
            c_v = float(curr_dna.get(m, 0.0) or 0.0)
            if c_v > p_v + 1e-4:
                deteriorating_count += 1

        for m in metrics_to_check:
            p_v = float(prev_dna.get(m, 0.0) or 0.0)
            c_v = float(curr_dna.get(m, 0.0) or 0.0)
            is_m_deteriorating = 1 if c_v > p_v + 1e-4 else 0
            other_deteriorating = max(0, deteriorating_count - is_m_deteriorating)
            eval_res = cls.evaluate_metric_mutation(
                metric_name=m,
                prev_val=p_v,
                curr_val=c_v,
                module_name="Project",
                history_values=[p_v, c_v],
                co_occurring_deteriorations=other_deteriorating,
                version_index=version_idx,
                total_versions=total_versions
            )
            eval_res["target_type"] = "PROJECT"
            eval_res["is_combined"] = False
            eval_res["combined_factors"] = None
            mutations.append(eval_res)

        return mutations

