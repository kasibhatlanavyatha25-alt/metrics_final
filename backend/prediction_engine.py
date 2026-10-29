import numpy as np
from typing import Dict, List, Any, Optional

class QualityPredictionEngine:
    """
    Experimental Future Quality & Evolutionary Risk Forecasting Engine.
    Strictly reports limitations when historical observations are limited.
    """

    @classmethod
    def predict_future_quality(
        cls,
        version_history: List[Dict[str, Any]], # List of version records with esdi, health_score, dna
        gate_decision: Optional[str] = None,
        max_unit_risk: Optional[float] = None
    ) -> Dict[str, Any]:
        num_versions = len(version_history)
        
        if num_versions < 2:
            return {
                "is_data_sufficient": False,
                "current_health": version_history[0]["health_score"] if version_history else 0.0,
                "predicted_health": None,
                "predicted_esdi": None,
                "trend_direction": "INSUFFICIENT_DATA",
                "confidence_score": None,
                "forecast_type": "Experimental Forecast (Insufficient Data)",
                "status_message": "Experimental forecast unavailable: at least 2 historical versions are required for preliminary trend extrapolation.",
                "main_factors": [],
                "forecast_points": []
            }

        # Extract historical time-series
        version_tags = [v["version_tag"] for v in version_history]
        health_series = [float(v["health_score"]) for v in version_history]
        esdi_series = [float(v["esdi_score"]) for v in version_history]
        cc_series = [float(v.get("cc", v.get("complexity_gene", 1.0))) for v in version_history]
        cbo_series = [float(v.get("cbo", v.get("coupling_gene", 1.0))) for v in version_history]
        loc_series = [float(v.get("loc", v.get("size_gene", 100.0))) for v in version_history]

        current_health = health_series[-1]
        current_esdi = esdi_series[-1]

        x = np.arange(num_versions)
        
        # Fit Linear Trend Regression on Health & ESDI Scores
        health_slope, health_intercept = np.polyfit(x, health_series, 1)
        esdi_slope, esdi_intercept = np.polyfit(x, esdi_series, 1)
        cc_slope, _ = np.polyfit(x, cc_series, 1)
        cbo_slope, _ = np.polyfit(x, cbo_series, 1)
        loc_slope, _ = np.polyfit(x, loc_series, 1)

        # Predict for next version (index = num_versions)
        next_x = num_versions
        predicted_health = round(max(0.0, min(100.0, float(health_slope * next_x + health_intercept))), 2)
        predicted_esdi = round(max(0.0, min(100.0, float(esdi_slope * next_x + esdi_intercept))), 2)

        # Calculate Confidence Score based on number of observations & R^2 fit (Never hard-coded)
        y_pred = health_slope * x + health_intercept
        ss_tot = np.sum((health_series - np.mean(health_series)) ** 2)
        ss_res = np.sum((health_series - y_pred) ** 2)
        r2 = max(0.0, 1.0 - (ss_res / (ss_tot + 1e-6))) if ss_tot > 1e-4 else 0.50
        
        # Confidence scales strictly with sample size (N versions) and statistical fit
        sample_weight = min(1.0, num_versions / 10.0) # 3 versions = 0.3, 5 versions = 0.5, 10 versions = 1.0
        confidence_score = round(max(0.15, min(0.85, (r2 * 0.4 + sample_weight * 0.6))), 2)

        # Determine Trend Direction & Gate Awareness per Patent Specification IDF-B
        health_diff = predicted_health - current_health
        is_quarantined = (
            (gate_decision and "CRITICAL" in str(gate_decision).upper()) or
            (max_unit_risk is not None and max_unit_risk >= 90.0)
        )
        is_blocked = (
            (gate_decision and "BLOCK" in str(gate_decision).upper() and not is_quarantined) or
            (max_unit_risk is not None and 80.0 <= max_unit_risk < 90.0)
        )

        if is_quarantined:
            trend_direction = "QUARANTINED"
            status_msg = "Repository is currently under CI/CD quarantine due to severe localized mutations (Risk >= 90). Downstream health projection is suspended until remediation is validated."
        elif is_blocked:
            trend_direction = "BLOCKED / AT RISK"
            status_msg = "Repository is currently under CI/CD build block due to elevated architectural risk (80 <= Risk < 90). Downstream health projection is suspended until remediation is validated."
        elif gate_decision == "WARN" or (max_unit_risk is not None and max_unit_risk >= 50.0):
            if health_diff > 2.0:
                trend_direction = "WARN (CONDITIONAL)"
                status_msg = f"Experimental Forecast ({num_versions} versions, confidence: {int(confidence_score * 100)}%): Metric trend shows positive slope, but gate warning is active. Proceed with caution."
            elif health_diff < -2.0:
                trend_direction = "DECLINING"
                status_msg = f"Experimental Forecast ({num_versions} versions, confidence: {int(confidence_score * 100)}%): Trend regression suggests next-version health will move from {current_health} to {predicted_health} (DECLINING)."
            else:
                trend_direction = "STABLE"
                status_msg = f"Experimental Forecast ({num_versions} versions, confidence: {int(confidence_score * 100)}%): Trend regression suggests health stability ({current_health} -> {predicted_health})."
        else: # gate_decision == PASS or unconstrained
            if health_diff > 2.0:
                trend_direction = "IMPROVING"
            elif health_diff < -2.0:
                trend_direction = "DECLINING"
            else:
                trend_direction = "STABLE"
            status_msg = (
                f"Experimental Forecast (Limited historical data: {num_versions} versions, confidence: {int(confidence_score * 100)}%): "
                f"Trend regression suggests next-version health will move from {current_health} to {predicted_health} ({trend_direction})."
            )

        # Primary driving factors
        main_factors = []
        if cc_slope > 0.3:
            main_factors.append("Cyclomatic Complexity has an upward trajectory across recent versions.")
        elif cc_slope < -0.3:
            main_factors.append("Cyclomatic Complexity has been actively reduced in recent commits.")

        if cbo_slope > 0.3:
            main_factors.append("Coupling between objects (CBO) has been steadily increasing.")
        elif cbo_slope < -0.3:
            main_factors.append("Coupling has decreased, reflecting improved component modularity.")

        if loc_slope > 100:
            main_factors.append("Lines of Code (LOC) show rapid expansion.")

        if is_quarantined:
            main_factors.insert(0, "CRITICAL: Localized high-risk unit breaches safety ceiling (max unit risk >= 90.0).")
        elif is_blocked:
            main_factors.insert(0, "WARNING: Elevated architectural degradation breaches threshold (80.0 <= risk < 90.0).")

        if not main_factors:
            main_factors.append("Metric trajectories indicate stable equilibrium across current history.")

        # Build chart forecast points
        forecast_points = []
        for i, v_tag in enumerate(version_tags):
            forecast_points.append({
                "version": v_tag,
                "is_prediction": False,
                "health_score": health_series[i],
                "esdi_score": esdi_series[i]
            })

        forecast_points.append({
            "version": f"V{num_versions + 1} (Forecast)",
            "is_prediction": True,
            "health_score": predicted_health,
            "esdi_score": predicted_esdi
        })

        return {
            "is_data_sufficient": num_versions >= 3,
            "forecast_type": f"Experimental Forecast ({num_versions} versions)",
            "current_health": current_health,
            "predicted_health": predicted_health,
            "predicted_esdi": predicted_esdi,
            "trend_direction": trend_direction,
            "confidence_score": confidence_score,
            "confidence_pct": int(confidence_score * 100),
            "status_message": status_msg,
            "main_factors": main_factors,
            "forecast_points": forecast_points,
            "gate_decision": gate_decision,
            "is_quarantined": is_quarantined,
            "is_blocked": is_blocked
        }
