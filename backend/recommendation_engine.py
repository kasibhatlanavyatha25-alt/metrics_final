from typing import Dict, List, Any, Optional

class RecommendationEngine:
    """
    Mutation-Aware Software Metric Recommendation Engine.
    Generates explainable, actionable recommendations with strict empirical evidence from Git AST evolution.
    """

    @classmethod
    def generate_recommendations(
        cls,
        classes: List[Dict[str, Any]],
        historical_class_map: Dict[str, List[Dict[str, Any]]], # class_name -> list of version metrics ordered by version
        mutations: List[Dict[str, Any]],
        risk_scores: List[Dict[str, Any]],
        esdi_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Build lookup for mutations by class and metric
        mutation_lookup: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for mut in mutations:
            c_name = mut.get("module_name")
            m_name = mut.get("metric_name", "").upper()
            if c_name not in mutation_lookup:
                mutation_lookup[c_name] = {}
            mutation_lookup[c_name][m_name] = mut

        risk_map = {r["class_name"]: r for r in risk_scores}

        for c in classes:
            c_name = c["class_name"]
            history = historical_class_map.get(c_name, [])
            c_muts = mutation_lookup.get(c_name, {})
            c_risk = risk_map.get(c_name, {})

            # 1. Cyclomatic Complexity (CC)
            cc = float(c.get("cyclomatic_complexity", 1))
            cc_mut = c_muts.get("CC") or c_muts.get("CYCLOMATIC_COMPLEXITY")
            cc_trend_values = [h.get("cyclomatic_complexity", 1) for h in history]
            cc_is_stable_high = len(cc_trend_values) >= 2 and all(v == cc_trend_values[0] for v in cc_trend_values) and cc > 10
            cc_trend_str = " → ".join(str(v) for v in cc_trend_values) if len(cc_trend_values) > 1 else str(cc)
            cc_pct_change = cc_mut["percentage_change"] if cc_mut else 0.0
            cc_mut_severity = cc_mut["severity"] if cc_mut else "HEALTHY"

            if cc > 10 or (cc_mut and cc_mut["is_deterioration"]):
                if cc > 18 or (cc_mut and cc_mut_severity == "CRITICAL"):
                    priority = "CRITICAL"
                elif cc > 12 or (cc_mut and cc_mut_severity == "RISKY"):
                    priority = "HIGH"
                else:
                    priority = "MEDIUM"

                if cc_is_stable_high:
                    reason = f"Persistent high complexity ({cc}) detected across all versions without architectural remediation."
                    obs_trend = "STABLE (PERSISTENT HIGH)"
                elif cc_pct_change > 0:
                    reason = f"Cyclomatic Complexity deteriorated by +{cc_pct_change}% ({cc_trend_str}), increasing branching execution paths and regression risk."
                    obs_trend = f"+{cc_pct_change}% ({cc_trend_str})"
                else:
                    reason = f"Cyclomatic Complexity stands at {cc}, exceeding normal maintainability threshold (CC <= 10)."
                    obs_trend = f"Current: {cc}"

                recommendations.append({
                    "priority": priority,
                    "module_name": c_name,
                    "metric_name": "Cyclomatic Complexity (CC)",
                    "current_value": cc,
                    "observed_trend": obs_trend,
                    "percentage_change": cc_pct_change if not cc_is_stable_high else 0.0,
                    "mutation_severity": cc_mut_severity if not cc_is_stable_high else "RISKY",
                    "target": "Target CC <= 10 per method/module.",
                    "reason": reason,
                    "recommended_action": "Refactor high-complexity methods using Extract Method or decomposition.",
                    "expected_benefit": "Reduces cognitive complexity, limits defect propagation, and simplifies unit test branch coverage.",
                    "evidence": f"Evolutionary trend: {cc_trend_str} across {len(history)} versions.",
                    "is_ml_derived": False
                })

            # 2. Coupling Between Objects (CBO)
            cbo = float(c.get("cbo", 0))
            cbo_mut = c_muts.get("CBO")
            cbo_trend_values = [h.get("cbo", 0) for h in history]
            cbo_is_stable_high = len(cbo_trend_values) >= 2 and all(v == cbo_trend_values[0] for v in cbo_trend_values) and cbo > 8
            cbo_trend_str = " → ".join(str(v) for v in cbo_trend_values) if len(cbo_trend_values) > 1 else str(cbo)
            cbo_pct_change = cbo_mut["percentage_change"] if cbo_mut else 0.0
            cbo_mut_severity = cbo_mut["severity"] if cbo_mut else "HEALTHY"

            if cbo > 7 or (cbo_mut and cbo_mut["is_deterioration"]):
                if cbo > 14 or (cbo_mut and cbo_mut_severity == "CRITICAL"):
                    priority = "CRITICAL"
                elif cbo > 9 or (cbo_mut and cbo_mut_severity == "RISKY"):
                    priority = "HIGH"
                else:
                    priority = "MEDIUM"

                if cbo_is_stable_high:
                    reason = f"Persistent tight coupling (CBO: {cbo}) detected across versions."
                    obs_trend = "STABLE (PERSISTENT HIGH)"
                elif cbo_pct_change > 0:
                    reason = f"Coupling Between Objects increased by +{cbo_pct_change}% ({cbo_trend_str}), creating tight dependency fan-out."
                    obs_trend = f"+{cbo_pct_change}% ({cbo_trend_str})"
                else:
                    reason = f"Coupling stands at {cbo} coupled types, exceeding standard tolerance (CBO <= 7)."
                    obs_trend = f"Current: {cbo}"

                recommendations.append({
                    "priority": priority,
                    "module_name": c_name,
                    "metric_name": "Coupling Between Objects (CBO)",
                    "current_value": cbo,
                    "observed_trend": obs_trend,
                    "percentage_change": cbo_pct_change if not cbo_is_stable_high else 0.0,
                    "mutation_severity": cbo_mut_severity if not cbo_is_stable_high else "RISKY",
                    "target": "Target CBO <= 7 by introducing loose coupling abstraction.",
                    "reason": reason,
                    "recommended_action": "Reduce excessive coupling by introducing interfaces, dependency inversion, or service boundaries.",
                    "expected_benefit": "Decouples component lifecycles, enables isolated unit testing, and prevents ripple effect breakage during refactoring.",
                    "evidence": f"Coupling evolution: {cbo_trend_str} across {len(history)} versions.",
                    "is_ml_derived": False
                })

            # 3. Weighted Methods per Class (WMC)
            wmc = float(c.get("wmc", 1))
            wmc_mut = c_muts.get("WMC")
            wmc_trend_values = [h.get("wmc", 1) for h in history]
            wmc_trend_str = " → ".join(str(v) for v in wmc_trend_values) if len(wmc_trend_values) > 1 else str(wmc)
            wmc_pct_change = wmc_mut["percentage_change"] if wmc_mut else 0.0

            if wmc > 20 or (wmc_mut and wmc_mut["is_deterioration"] and wmc_pct_change >= 20.0):
                priority = "CRITICAL" if wmc > 35 else ("HIGH" if wmc > 25 else "MEDIUM")
                recommendations.append({
                    "priority": priority,
                    "module_name": c_name,
                    "metric_name": "Weighted Methods per Class (WMC)",
                    "current_value": wmc,
                    "observed_trend": f"+{wmc_pct_change}% ({wmc_trend_str})" if wmc_pct_change > 0 else f"Current: {wmc}",
                    "percentage_change": wmc_pct_change,
                    "mutation_severity": "CRITICAL" if wmc > 35 else "RISKY",
                    "target": "Target WMC <= 20 per class.",
                    "reason": f"Accumulated method complexity (WMC: {wmc}) indicates God Class anti-pattern tendency.",
                    "recommended_action": "Split large classes or move responsibilities into focused components.",
                    "expected_benefit": "Restores Single Responsibility Principle and simplifies class maintenance.",
                    "evidence": f"WMC evolution: {wmc_trend_str}.",
                    "is_ml_derived": False
                })

            # 4. Lack of Cohesion of Methods (LCOM)
            lcom = float(c.get("lcom", 0.0))
            lcom_mut = c_muts.get("LCOM")
            if lcom > 0.65 or (lcom_mut and lcom_mut["is_deterioration"]):
                priority = "HIGH" if lcom > 0.80 else "MEDIUM"
                recommendations.append({
                    "priority": priority,
                    "module_name": c_name,
                    "metric_name": "Lack of Cohesion of Methods (LCOM)",
                    "current_value": lcom,
                    "observed_trend": f"LCOM: {lcom}",
                    "percentage_change": lcom_mut["percentage_change"] if lcom_mut else 0.0,
                    "mutation_severity": "RISKY",
                    "target": "Target LCOM <= 0.40.",
                    "reason": f"LCOM is {lcom}, indicating instance variables are accessed by disparate, uncoordinated methods.",
                    "recommended_action": "Improve cohesion by separating unrelated responsibilities.",
                    "expected_benefit": "Increases class cohesiveness and reduces scattered state management.",
                    "evidence": f"Cohesion metric LCOM: {lcom}.",
                    "is_ml_derived": False
                })

            # 5. Lines of Code (LOC) Bloat
            loc = float(c.get("loc", 0))
            loc_mut = c_muts.get("LOC")
            loc_pct_change = loc_mut["percentage_change"] if loc_mut else 0.0
            if loc > 350 or (loc_mut and loc_mut["is_deterioration"] and loc_pct_change >= 40.0):
                priority = "HIGH" if loc > 500 else "MEDIUM"
                recommendations.append({
                    "priority": priority,
                    "module_name": c_name,
                    "metric_name": "Lines of Code (LOC)",
                    "current_value": loc,
                    "observed_trend": f"+{loc_pct_change}%" if loc_pct_change > 0 else f"{loc} LOC",
                    "percentage_change": loc_pct_change,
                    "mutation_severity": "RISKY",
                    "target": "Target LOC <= 250 per source unit.",
                    "reason": f"Source unit has expanded to {loc} LOC (+{loc_pct_change}% growth), creating maintenance overhead.",
                    "recommended_action": "Investigate oversized modules and consider decomposition.",
                    "expected_benefit": "Improves readability and prevents modular monolithic decay.",
                    "evidence": f"File size: {loc} non-comment LOC.",
                    "is_ml_derived": False
                })

        priority_order = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
        return recommendations
