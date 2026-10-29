import pytest
from app.core.remediation_engine import RemediationEngine, REMEDIATED_PAYMENT_SERVICE_JAVA
from app.core.verification_engine import VerificationEngine
from app.mock_repo.generator import PAYMENT_SERVICE_V5


def test_remediation_diff_generation():
    engine = RemediationEngine()
    available, rem_source, diff, expl = engine.generate_remediation(
        PAYMENT_SERVICE_V5, "PaymentService", "processPayment"
    )
    assert available is True
    assert "validateRequestParameters" in rem_source
    assert "--- a/PaymentService.java" in diff
    assert "+++ b/PaymentService.java" in diff
    assert len(expl) > 20


def test_verification_loop():
    ver_engine = VerificationEngine()
    engine = RemediationEngine()
    available, rem_source, diff, expl = engine.generate_remediation(
        PAYMENT_SERVICE_V5, "PaymentService", "processPayment"
    )

    result = ver_engine.verify_remediation(
        target_class="PaymentService",
        target_method="processPayment",
        before_source=PAYMENT_SERVICE_V5,
        after_source=rem_source,
        diff=diff,
        explanation=expl,
    )

    assert result.success is True
    assert result.after_esdi < result.before_esdi
    assert "SUCCESS" in result.compilation_status
    assert "PASS" in result.test_status
