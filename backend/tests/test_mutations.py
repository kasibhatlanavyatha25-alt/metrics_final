import pytest
from app.models.schemas import DnaRecord, MetricVector
from app.core.mutation_detector import MutationDetector


def test_baseline_mutation_detection():
    detector = MutationDetector()
    record1 = DnaRecord(
        class_name="PaymentService",
        package_name="com.test",
        file_path="PaymentService.java",
        commit_sha="c1",
        version_label="V1",
        metrics=MetricVector(loc=60, cc=5, wmc=5, cbo=3, lcom=0.20),
        timestamp="2026-09-07 10:00:00",
    )
    analysis = detector.analyze_class_mutations("PaymentService", [record1])
    assert analysis.class_name == "PaymentService"
    assert analysis.severe_mutations_count == 0
    assert analysis.total_risk < 0.3


def test_5d_mutation_progression():
    detector = MutationDetector()
    records = [
        DnaRecord(
            class_name="PaymentService",
            package_name="com.test",
            file_path="PaymentService.java",
            commit_sha="c1",
            version_label="V1",
            metrics=MetricVector(loc=60, cc=5, wmc=5, cbo=3, lcom=0.20),
            timestamp="2026-09-07 10:00:00",
        ),
        DnaRecord(
            class_name="PaymentService",
            package_name="com.test",
            file_path="PaymentService.java",
            commit_sha="c2",
            version_label="V2",
            metrics=MetricVector(loc=110, cc=8, wmc=8, cbo=4, lcom=0.30),
            timestamp="2026-09-07 10:05:00",
        ),
        DnaRecord(
            class_name="PaymentService",
            package_name="com.test",
            file_path="PaymentService.java",
            commit_sha="c3",
            version_label="V3",
            metrics=MetricVector(loc=180, cc=14, wmc=14, cbo=7, lcom=0.45),
            timestamp="2026-09-07 10:10:00",
        ),
        DnaRecord(
            class_name="PaymentService",
            package_name="com.test",
            file_path="PaymentService.java",
            commit_sha="c4",
            version_label="V4",
            metrics=MetricVector(loc=320, cc=24, wmc=24, cbo=12, lcom=0.60),
            timestamp="2026-09-07 10:15:00",
        ),
        DnaRecord(
            class_name="PaymentService",
            package_name="com.test",
            file_path="PaymentService.java",
            commit_sha="c5",
            version_label="V5",
            metrics=MetricVector(loc=390, cc=31, wmc=31, cbo=15, lcom=0.72),
            timestamp="2026-09-07 10:20:00",
        ),
    ]

    analysis = detector.analyze_class_mutations("PaymentService", records)
    assert analysis.total_risk > 0.4
    assert "cc" in analysis.metric_mutations
    assert analysis.metric_mutations["cc"].persistence > 0.5
    assert analysis.metric_mutations["cc"].recency == 1.0
    assert analysis.metric_mutations["wmc"].magnitude > 0.5
