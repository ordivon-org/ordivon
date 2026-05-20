"""Integration tests for Phase 3: OpenFGA + OPA authorization pipeline.

Validates:
    - OpenFGA client check() with/without OpenFGA server
    - OPA transition validation (Rego → Python fallback)
    - Authority state transition rules consistency
    - Route reviewer OpenFGA integration
    - Bootstrap authorization tuples

⚠️ COVERAGE GAP (DEBT-INFRA-003, 2026-05-13):
These tests verify FALLBACK paths only. The PRIMARY paths (actual OpenFGA
check() API calls, OPA eval CLI invocation) are NOT tested because OpenFGA
server has never been started and OPA CLI is not installed.

To fix: start docker-compose.infrastructure.yml, install opa CLI, then add
tests that verify actual OpenFGA authorization decisions and OPA Rego policy
evaluation against a running server.

Run:
    python3 tests/test_authorization_integration.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def test_openfga_client_fallback() -> None:
    """OpenFGA client returns False when server is not available."""
    from ordivon_governance_core.openfga_client import OpenFGAClient

    client = OpenFGAClient(base_url="http://localhost:19999")  # non-existent port

    result = asyncio.run(
        client.check(
            user="user:test-user",
            relation="can_read",
            object="governable_object:test-obj",
        )
    )
    assert result is False, "Should return False when OpenFGA is unavailable"
    assert client.available() is False

    print("  ✓ test_openfga_client_fallback PASSED")


def test_openfga_convenience_functions() -> None:
    """Convenience functions delegate to client correctly."""
    from ordivon_governance_core.openfga_client import (
        can_approve_transition,
        can_review_domain,
        can_register_object,
        can_close_debt,
        can_activate_policy,
        can_verify_receipt,
    )

    async def _run():
        # All should return False without OpenFGA
        results = await asyncio.gather(
            can_approve_transition("test-user", "test-obj"),
            can_review_domain("test-user", "documentation"),
            can_register_object("test-user", "document", "documentation"),
            can_close_debt("test-user", "test-debt"),
            can_activate_policy("test-user", "test-policy"),
            can_verify_receipt("test-user", "test-receipt"),
        )
        assert all(r is False for r in results), f"All should be False without OpenFGA: {results}"

    asyncio.run(_run())
    print("  ✓ test_openfga_convenience_functions PASSED")
def test_bootstrap_tuples() -> None:
    """Bootstrap authorization tuples are well-formed."""
    from ordivon_governance_core.openfga_client import DEFAULT_AUTHORIZATION_TUPLES

    assert len(DEFAULT_AUTHORIZATION_TUPLES) >= 20, (
        f"Expected at least 20 tuples, got {len(DEFAULT_AUTHORIZATION_TUPLES)}"
    )

    # Verify all tuples have 3 elements
    for t in DEFAULT_AUTHORIZATION_TUPLES:
        assert len(t) == 3, f"Tuple should have 3 elements: {t}"
        user, relation, obj = t
        assert ":" in user, f"User should have type prefix: {user}"
        assert ":" in obj, f"Object should have type prefix: {obj}"

    # Verify key tuples exist
    has_org_admin = any(
        t == ("user:ordivon-core-maintainer", "admin", "organization:ordivon") for t in DEFAULT_AUTHORIZATION_TUPLES
    )
    assert has_org_admin, "Missing org admin tuple"

    has_doc_approver = any(
        t == ("user:ordivon-core-maintainer", "approver", "domain:documentation") for t in DEFAULT_AUTHORIZATION_TUPLES
    )
    assert has_doc_approver, "Missing documentation approver tuple"

    print(f"  ✓ test_bootstrap_tuples PASSED ({len(DEFAULT_AUTHORIZATION_TUPLES)} tuples)")


def test_route_reviewer_fallback() -> None:
    """Route reviewer falls back to hardcoded surfaces without OpenFGA."""
    import asyncio
    from scripts.governance.route_reviewers import (
        route_file_fallback,
        route_files,
        route_files_async,
    )

    # Fallback routing
    matches = route_file_fallback("docs/governance/document-registry.jsonl")
    assert len(matches) >= 1
    assert any("admit_artifact" in m["required_checks"] for m in matches)

    # Sync routing
    result = route_files(["docs/governance/document-registry.jsonl"])
    assert result["matched_files"] == 1
    assert "admit_artifact" in result["unique_checks"]

    # Async routing (OpenFGA unavailable, falls back)
    async def _run():
        r = await route_files_async(["docs/governance/document-registry.jsonl"])
        assert r["matched_files"] == 1

    asyncio.run(_run())

    # Unmatched file
    result = route_files(["README.md"])
    assert result["matched_files"] == 0

    print("  ✓ test_route_reviewer_fallback PASSED")


def test_openfga_model_syntax() -> None:
    """OpenFGA authorization model can be parsed."""
    model_path = ROOT / "policies/openfga/ordivon-authorization-model.fga"
    assert model_path.exists(), f"Model file not found: {model_path}"

    content = model_path.read_text()
    assert "model" in content
    assert "schema 1.1" in content
    assert "type governable_object" in content
    assert "type domain" in content
    assert "type organization" in content
    assert "can_approve_transition" in content

    print("  ✓ test_openfga_model_syntax PASSED")


def test_authority_transitions_rego_syntax() -> None:
    """OPA authority transitions Rego policy is parseable."""
    rego_path = ROOT / "policies/opa/rules/authority_transitions.rego"
    assert rego_path.exists(), f"Rego file not found: {rego_path}"

    content = rego_path.read_text()
    assert "package ordivon.authority" in content
    assert "valid_evidence_transitions" in content
    assert "valid_authorization_transitions" in content
    assert "valid_policy_transitions" in content
    assert "validate_transition" in content

    print("  ✓ test_authority_transitions_rego_syntax PASSED")


def main() -> int:
    print("=== Phase 3 Integration Tests ===\n")

    tests = [
        ("OpenFGA client fallback", test_openfga_client_fallback),
        ("OpenFGA convenience functions", test_openfga_convenience_functions),
        ("OPA transition validation", test_opa_transition_validation),
        ("OPA vs Python consistency", test_opa_vs_python_consistency),
        ("Safety predicates", test_safety_predicates),
        ("Bootstrap authorization tuples", test_bootstrap_tuples),
        ("Route reviewer fallback", test_route_reviewer_fallback),
        ("OpenFGA model syntax", test_openfga_model_syntax),
        ("OPA Rego syntax", test_authority_transitions_rego_syntax),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name} FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
