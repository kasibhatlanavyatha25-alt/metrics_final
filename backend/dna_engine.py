import math
from typing import Dict, List, Any, Optional

class EvolutionaryDNAEngine:
    """
    Constructs the Evolutionary Software DNA profile across version snapshots.
    
    The Canonical Software DNA vector consists of precisely 5 core metrics:
    DNA = [LOC, CC, WMC, CBO, LCOM]
    
    1. LOC:  Lines of Code (System scale / volume)
    2. CC:   Cyclomatic Complexity (McCabe decision complexity)
    3. WMC:  Weighted Methods per Class (Chidamber & Kemerer OO method complexity)
    4. CBO:  Coupling Between Objects (Inter-class architectural coupling)
    5. LCOM: Lack of Cohesion of Methods (Henderson-Sellers / CK cohesion defect)
    """

    @staticmethod
    def generate_dna_snapshot(
        project_metric: Dict[str, Any],
        evolution_metric: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        total_loc = float(project_metric.get("total_loc", 0.0))
        avg_complexity = float(project_metric.get("avg_complexity", 1.0))
        avg_wmc = float(project_metric.get("avg_wmc", 1.0))
        avg_cbo = float(project_metric.get("avg_cbo", 0.0))
        avg_lcom = float(project_metric.get("avg_lcom", 0.0))

        # 5 Canonical Software DNA Metrics
        loc_val = round(total_loc, 2)
        cc_val = round(avg_complexity, 2)
        wmc_val = round(avg_wmc, 2)
        cbo_val = round(avg_cbo, 2)
        lcom_val = round(max(0.0, min(1.0, avg_lcom)), 4)

        dna_vector = [loc_val, cc_val, wmc_val, cbo_val, lcom_val]

        gene_breakdown = {
            "loc": {
                "name": "Lines of Code (LOC)",
                "value": loc_val,
                "unit": "Lines",
                "description": "Total executable source volume across all modules."
            },
            "cc": {
                "name": "Cyclomatic Complexity (CC)",
                "value": cc_val,
                "unit": "McCabe CC",
                "description": "Average independent linear execution paths per method/module."
            },
            "wmc": {
                "name": "Weighted Methods per Class (WMC)",
                "value": wmc_val,
                "unit": "Sum of CC",
                "description": "Sum of cyclomatic complexities of all declared methods per class."
            },
            "cbo": {
                "name": "Coupling Between Objects (CBO)",
                "value": cbo_val,
                "unit": "Coupled Types",
                "description": "Number of external classes or modules to which a class is coupled."
            },
            "lcom": {
                "name": "Lack of Cohesion of Methods (LCOM)",
                "value": lcom_val,
                "unit": "LCOM (0.0-1.0)",
                "description": "Measure of method dissimilarity based on instance variable access."
            }
        }

        normalized_vector = [
            round(1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, -0.05 * (loc_val - 50.0))))), 4),
            round(1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, -0.25 * (cc_val - 10.0))))), 4),
            round(1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, -0.15 * (wmc_val - 20.0))))), 4),
            round(1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, -0.30 * (cbo_val - 5.0))))), 4),
            round(1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, -2.0 * (lcom_val - 0.5))))), 4),
        ]

        return {
            "loc": loc_val,
            "cc": cc_val,
            "wmc": wmc_val,
            "cbo": cbo_val,
            "lcom": lcom_val,
            "dna_vector": dna_vector,
            "normalized_dna_vector": normalized_vector,
            "gene_breakdown": gene_breakdown,
        }
