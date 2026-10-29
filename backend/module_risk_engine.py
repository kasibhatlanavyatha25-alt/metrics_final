import math
from typing import Dict, List, Any, Optional

class ModuleRiskEngine:
    """
    Computes Module-Level Evolutionary Risk Scores (0-100), prioritizes source units,
    and isolates module-level risk from project-level ESDI.
    
    A project can have moderate overall risk while individual modules exhibit critical evolutionary risk.
    """

    @classmethod
    def evaluate_class_risk(
        cls,
        current_class: Dict[str, Any],
        historical_class_metrics: List[Dict[str, Any]],
        class_mutations: List[Dict[str, Any]],
        project_esdi: float
    ) -> Dict[str, Any]:
        c_name = current_class["class_name"]
        loc = float(current_class.get("loc", 0))
        wmc = float(current_class.get("wmc", 0))
        cbo = float(current_class.get("cbo", 0))
        rfc = float(current_class.get("rfc", 0))
        lcom = float(current_class.get("lcom", 0.0))
        cc = float(current_class.get("cyclomatic_complexity", 1))

        # Risk components (normalized 0-100)
        cc_risk = min(100.0, (cc / 15.0) * 100.0)
        wmc_risk = min(100.0, (wmc / 30.0) * 100.0)
        cbo_risk = min(100.0, (cbo / 14.0) * 100.0)
        lcom_risk = min(100.0, lcom * 100.0)
        loc_risk = min(100.0, (loc / 350.0) * 100.0)

        # Base structural risk score based on canonical weights
        base_risk = (cc_risk * 0.35) + (cbo_risk * 0.25) + (wmc_risk * 0.20) + (lcom_risk * 0.10) + (loc_risk * 0.10)

        # Mutation penalty adjustment
        recent_mutation_severity = "HEALTHY"
        has_critical_mutation = False
        has_risky_mutation = False

        for mut in class_mutations:
            if mut.get("module_name") == c_name:
                sev = mut.get("severity")
                if sev == "CRITICAL":
                    has_critical_mutation = True
                    recent_mutation_severity = "CRITICAL"
                elif sev == "RISKY" and not has_critical_mutation:
                    has_risky_mutation = True
                    recent_mutation_severity = "RISKY"

        mutation_bonus = 0.0
        if has_critical_mutation:
            mutation_bonus = 20.0
        elif has_risky_mutation:
            mutation_bonus = 10.0

        final_risk = round(min(100.0, max(0.0, base_risk + mutation_bonus)), 2)

        # Determine Priority
        if final_risk >= 75.0 or has_critical_mutation:
            priority = "CRITICAL"
        elif final_risk >= 50.0:
            priority = "HIGH"
        elif final_risk >= 25.0:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Identify primary risk factors
        primary_factors = []
        top_risk_metric = "Cyclomatic Complexity"
        max_factor_risk = cc_risk

        if cbo_risk > max_factor_risk:
            max_factor_risk = cbo_risk
            top_risk_metric = "Coupling (CBO)"
        if wmc_risk > max_factor_risk:
            max_factor_risk = wmc_risk
            top_risk_metric = "Weighted Methods (WMC)"
        if lcom_risk > max_factor_risk:
            max_factor_risk = lcom_risk
            top_risk_metric = "Lack of Cohesion (LCOM)"
        if loc_risk > max_factor_risk:
            max_factor_risk = loc_risk
            top_risk_metric = "Lines of Code (LOC)"

        if cc > 10:
            primary_factors.append({
                "metric": "Complexity",
                "value": cc,
                "detail": f"Cyclomatic Complexity is {cc} (decision density high)."
            })
        if cbo > 7:
            primary_factors.append({
                "metric": "Coupling",
                "value": cbo,
                "detail": f"Coupled to {cbo} external types (architectural fan-out)."
            })
        if wmc > 20:
            primary_factors.append({
                "metric": "WMC",
                "value": wmc,
                "detail": f"Accumulated method complexity is {wmc}."
            })
        if lcom > 0.6:
            primary_factors.append({
                "metric": "LCOM",
                "value": lcom,
                "detail": f"Cohesion defect index is {lcom}."
            })
        if loc > 300:
            primary_factors.append({
                "metric": "Size",
                "value": loc,
                "detail": f"File size has expanded to {loc} LOC."
            })

        if not primary_factors:
            primary_factors.append({
                "metric": "Baseline",
                "value": cc,
                "detail": "Metric parameters within stable boundaries."
            })

        explanation = (
            f"Module '{c_name}' evaluated at {final_risk}/100 ({priority}). "
            f"Primary driver: {top_risk_metric}. Recent Mutation: {recent_mutation_severity}."
        )

        return {
            "class_name": c_name,
            "package_name": current_class.get("package_name", "(default)"),
            "risk_score": final_risk,
            "priority": priority,
            "level_type": "MODULE-LEVEL EVOLUTIONARY RISK",
            "top_risk_metric": top_risk_metric,
            "primary_factors": primary_factors,
            "recent_mutation_severity": recent_mutation_severity,
            "complexity_risk": round(cc_risk, 2),
            "coupling_risk": round(cbo_risk, 2),
            "wmc_risk": round(wmc_risk, 2),
            "lcom_risk": round(lcom_risk, 2),
            "size_risk": round(loc_risk, 2),
            "explanation": explanation,
            "esdi_contribution": round((final_risk / 100.0) * (loc / max(100.0, float(current_class.get("total_loc", loc)))), 2)
        }

    @classmethod
    def analyze_all_modules(
        cls,
        classes: List[Dict[str, Any]],
        historical_class_map: Dict[str, List[Dict[str, Any]]],
        mutations: List[Dict[str, Any]],
        project_esdi: float
    ) -> List[Dict[str, Any]]:
        results = []
        for c in classes:
            c_name = c["class_name"]
            history = historical_class_map.get(c_name, [])
            c_muts = [m for m in mutations if m.get("module_name") == c_name]
            score_dict = cls.evaluate_class_risk(c, history, c_muts, project_esdi)
            results.append(score_dict)

        # Sort descending by risk score
        results.sort(key=lambda x: x["risk_score"], reverse=True)
        return results
