import pytest
from app.models.schemas import ClassMutationAnalysis, MutationDimensionScore, GateDecision
from app.core.esdi_calculator import ESDICalculator


def test_esdi_calculation_low_risk():
    calculator = ESDICalculator()
    low_scores = {
        m: MutationDimensionScore(
            magnitude=0.05,
            persistence=0.1,
            acceleration=0.05,
            cooccurrence=0.1,
            recency=1.0,
            risk=0.20,
            severity="LOW",
        )
        for m in ["cc", "wmc", "cbo", "lcom", "loc"]
    }
    analysis = ClassMutationAnalysis(
        class_name="PaymentService",
        commit_sha="c1",
        version_label="V1",
        metric_mutations=low_scores,
        total_risk=0.20,
        severe_mutations_count=0,
        reasons=[],
    )

    esdi_resp = calculator.calculate_system_esdi({"PaymentService": analysis})
    assert esdi_resp.esdi < 50.0
    assert esdi_resp.decision == GateDecision.PASS


def test_esdi_calculation_high_risk_block():
    calculator = ESDICalculator()
    high_scores = {
        m: MutationDimensionScore(
            magnitude=0.85,
            persistence=0.90,
            acceleration=0.80,
            cooccurrence=0.80,
            recency=1.0,
            risk=0.85,
            severity="CRITICAL",
        )
        for m in ["cc", "wmc", "cbo", "lcom", "loc"]
    }
    analysis = ClassMutationAnalysis(
        class_name="PaymentService",
        commit_sha="c5",
        version_label="V5",
        metric_mutations=high_scores,
        total_risk=0.85,
        severe_mutations_count=5,
        reasons=["Critical CC mutation", "High CBO"],
    )

    esdi_resp = calculator.calculate_system_esdi({"PaymentService": analysis})
    assert esdi_resp.esdi >= 75.0
    assert esdi_resp.decision in (GateDecision.BLOCK, GateDecision.CRITICAL_BLOCK)
