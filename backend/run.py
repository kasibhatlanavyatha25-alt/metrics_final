import argparse
import sys
import uvicorn
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.mock_repo.generator import generate_mock_repository, MOCK_REPO_DIR
from app.core.git_interceptor import GitInterceptor
from app.core.cicd_gate import CICDGateEngine
from app.core.remediation_engine import RemediationEngine
from app.core.verification_engine import VerificationEngine
from app.storage.state_store import state_store


def run_self_test() -> bool:
    print("=" * 60)
    print("STARTING EVOLUTIONARY SOFTWARE DNA ENGINE SELF TEST")
    print("=" * 60)

    try:
        # 1. Generate mock repository
        print("\n[STEP 1] Generating 5-commit mock Git repository...")
        generate_mock_repository(MOCK_REPO_DIR)
        print("Mock repository created successfully at:", MOCK_REPO_DIR)

        # 2. Run sequential analysis V1 -> V5
        print("\n[STEP 2] Running incremental AST analysis & DNA tracking across V1..V5...")
        engine = CICDGateEngine()
        status_res = engine.run_full_repository_analysis(str(MOCK_REPO_DIR))

        commits = state_store.commits
        print(f"Processed {len(commits)} commits:")
        for c in commits:
            esdi = state_store.esdi_history.get(c.sha)
            esdi_val = esdi.esdi if esdi else 0.0
            gate = esdi.decision.value if esdi else "N/A"
            print(f"  - {c.version_label} [{c.short_sha}]: ESDI={esdi_val:.1f} -> Gate: {gate} | Msg: {c.message[:45]}...")

        # 3. Verify V1 vs V5 evolutionary risk
        v1_sha = commits[0].sha
        v5_sha = commits[-1].sha
        v1_esdi = state_store.esdi_history[v1_sha].esdi
        v5_esdi = state_store.esdi_history[v5_sha].esdi
        v5_gate = state_store.esdi_history[v5_sha].decision.value

        print(f"\n[STEP 3] Validating Risk Progression: V1 ESDI = {v1_esdi:.1f}, V5 ESDI = {v5_esdi:.1f}")
        assert v5_esdi > v1_esdi, f"Expected V5 ESDI > V1 ESDI, but got V5={v5_esdi}, V1={v1_esdi}"
        print(f"  [OK] V5 risk ({v5_esdi:.1f}) is higher than V1 baseline ({v1_esdi:.1f})")

        # 4. Verify V5 results in BLOCK or CRITICAL BLOCK
        print(f"\n[STEP 4] Checking V5 Gate Decision: {v5_gate}")
        assert v5_gate in ("BLOCK", "CRITICAL BLOCK"), f"Expected V5 gate BLOCK or CRITICAL BLOCK, got {v5_gate}"
        print(f"  [OK] V5 produced expected gate decision: {v5_gate}")

        # 5. Execute Automated Remediation
        print("\n[STEP 5] Triggering Automated AST Extract Method Remediation on PaymentService...")
        file_path = "src/main/java/com/evolutionary/payment/PaymentService.java"
        git_tool = GitInterceptor(str(MOCK_REPO_DIR))
        v5_source = git_tool.get_file_content_at_commit(file_path, v5_sha)

        rem_engine = RemediationEngine()
        available, rem_source, diff, expl = rem_engine.generate_remediation(
            v5_source, "PaymentService", "processPayment"
        )
        assert available, "Remediation was not available for high complexity PaymentService"
        print("  [OK] Extract Method remediation generated with unified diff.")

        # 6. Validate compilation and recalculate ESDI
        print("\n[STEP 6] Running Verification Loop & Recalculating ESDI...")
        ver_engine = VerificationEngine()
        ver_result = ver_engine.verify_remediation(
            target_class="PaymentService",
            target_method="processPayment",
            before_source=v5_source,
            after_source=rem_source,
            diff=diff,
            explanation=expl,
            commit_sha=v5_sha,
        )

        print(f"  - Compilation Status: {ver_result.compilation_status}")
        print(f"  - Test Status: {ver_result.test_status}")
        print(f"  - Before ESDI: {ver_result.before_esdi:.1f} ({ver_result.gate_before})")
        print(f"  - After ESDI:  {ver_result.after_esdi:.1f} ({ver_result.gate_after})")
        print(f"  - ESDI Delta:   -{ver_result.esdi_delta:.1f}")

        assert ver_result.after_esdi < ver_result.before_esdi, (
            f"Expected after ESDI ({ver_result.after_esdi}) < before ESDI ({ver_result.before_esdi})"
        )
        assert ver_result.success, "Remediation verification did not succeed"
        print("  [OK] Remediated ESDI improved and satisfies quality gate.")

        print("\n" + "=" * 60)
        print("SELF TEST PASSED")
        print("=" * 60)
        return True

    except Exception as ex:
        print("\n" + "=" * 60)
        print(f"SELF TEST FAILED: {ex}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Evolutionary Software DNA Quality Engine")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind backend server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--self-test", action="store_true", help="Run automated self-test verification")
    parser.add_argument("--gen-mock", action="store_true", help="Generate mock Git repository and exit")

    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if args.gen_mock:
        generate_mock_repository(MOCK_REPO_DIR)
        print("Mock repository generated.")
        sys.exit(0)

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
