"""HAP-2: Boundary guard tests for ADP-1 scenario fixtures.

Tests that prove HAP-2 ADP scenarios enforce:
1. Capability never implies authorization
2. can_read_credentials never implies credential access
3. can_call_external_api never implies external call permission
4. Shell requires BLOCKED or REVIEW_REQUIRED
5. READY_WITHOUT_AUTHORIZATION cannot be treated as execution permission
6. CandidateRule remains non-binding
7. No external compliance/certification/endorsement claims
8. No can_access_secrets string
9. Protected paths require boundary permission
10. Baseline debt cannot mask new regression
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADP_DIR = ROOT / "examples" / "hap" / "adp-scenarios"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_scenarios():
    return sorted(d for d in ADP_DIR.iterdir() if d.is_dir())


class TestCapabilityNotAuthorization:
    """can_X != may_X — Capability declaration is not authorization."""

    def test_all_manifests_have_authority_denial(self):
        for s in _all_scenarios():
            m = _load_json(s / "harness-adapter-manifest.json")
            auth = m.get("authority_statement", "").lower()
            assert "not authorization" in auth or "does not authorize" in auth or "does not imply" in auth, \
                f"{s.name}: manifest authority_statement must deny authorization"

    def test_all_capability_blocks_have_authority_disclaimer(self):
        for s in _all_scenarios():
            m = _load_json(s / "harness-adapter-manifest.json")
            caps = m.get("capabilities", {})
            auth = caps.get("authority_statement", "").lower()
            assert "can_x does not imply may_x" in auth or "not authorization" in auth or "does not authorize" in auth or "does not imply" in auth, \
                f"{s.name}: capabilities missing authority disclaimer"

    def test_no_manifest_claims_authorization(self):
        for s in _all_scenarios():
            content = (s / "harness-adapter-manifest.json").read_text().lower()
            assert "authorizes action" not in content, f"{s.name}: claims authorization"
            assert "authorizes execution" not in content, f"{s.name}: claims execution authorization"


class TestCredentialCapabilitySeparation:
    """can_read_credentials describes technical capability only."""

    def test_no_fixture_uses_can_access_secrets(self):
        for f in ADP_DIR.glob("**/*.json"):
            content = f.read_text()
            assert "can_access_secrets" not in content, \
                f"{f.relative_to(ROOT)}: forbidden can_access_secrets — use can_read_credentials"

    def test_credential_read_blocked_scenario_blocks_access(self):
        s = ADP_DIR / "credential-capability-confusion"
        m = _load_json(s / "harness-adapter-manifest.json")
        assert m["capabilities"]["can_read_credentials"] is True, "Must declare capability"
        assert m["declared_boundaries"]["credential_access_blocked"] is True, "Must block access"

    def test_credential_scenario_is_blocked(self):
        s = ADP_DIR / "credential-capability-confusion"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"
        assert "credential" in r["result_summary"]["status_reason"].lower()


class TestExternalCallBoundary:
    """can_call_external_api never implies external call permission."""

    def test_external_scenario_blocks_calls(self):
        s = ADP_DIR / "external-side-effect-drift"
        m = _load_json(s / "harness-adapter-manifest.json")
        assert m["capabilities"]["can_call_external_api"] is True
        assert m["declared_boundaries"]["external_api_blocked"] is True

    def test_external_scenario_is_blocked(self):
        s = ADP_DIR / "external-side-effect-drift"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"


class TestShellEscalation:
    """Shell requires BLOCKED or REVIEW_REQUIRED."""

    def test_shell_risk_scenario_is_blocked(self):
        s = ADP_DIR / "shell-risk-escalation"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"
        assert "escalation" in r["result_summary"]["status_reason"].lower()

    def test_capability_authorization_collapse_is_blocked(self):
        s = ADP_DIR / "capability-authorization-collapse"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"

    def test_shell_scenarios_have_shell_blocked(self):
        for name in ["shell-risk-escalation", "capability-authorization-collapse"]:
            s = ADP_DIR / name
            m = _load_json(s / "harness-adapter-manifest.json")
            assert m["declared_boundaries"]["shell_blocked"] is True, f"{name}: shell_blocked must be True"


class TestREADYWithoutAuthorization:
    """READY_WITHOUT_AUTHORIZATION cannot be treated as execution permission."""

    def test_ready_overclaim_disclaims_authorization(self):
        s = ADP_DIR / "ready-overclaim"
        r = _load_json(s / "harness-execution-receipt.json")
        reason = r["result_summary"]["status_reason"].lower()
        assert "does not authorize" in reason or "not authorization" in reason
        assert "ready" in reason

    def test_ready_is_qualified(self):
        """All receipts with READY must qualify it."""
        for s in _all_scenarios():
            r = _load_json(s / "harness-execution-receipt.json")
            status = r["result_summary"]["status"]
            if "READY" in status:
                assert "WITHOUT_AUTHORIZATION" in status or "does not authorize" in r["result_summary"].get("authority_statement", "").lower(), \
                    f"{s.name}: READY must be qualified as READY_WITHOUT_AUTHORIZATION"


class TestCandidateRuleNonBinding:
    """CandidateRule remains non-binding in all scenarios."""

    def test_all_summaries_declare_candidate_rule_non_binding(self):
        for s in _all_scenarios():
            summary = (s / "scenario-summary.md").read_text()
            assert "NON-BINDING" in summary or "non-binding" in summary.lower(), \
                f"{s.name}: scenario summary must declare CandidateRule as NON-BINDING"


class TestNoExternalCompliance:
    """No compliance/certification/endorsement/equivalence claims."""

    def test_no_unsafe_external_claims(self):
        unsafe = ["compliant", "certified", "endorsed", "partnered", "equivalent to",
                  "official alignment"]
        for s in _all_scenarios():
            content = (s / "scenario-summary.md").read_text().lower()
            for word in unsafe:
                if word in content:
                    # Allow if in negation context
                    if f"not {word}" in content or f"no {word}" in content:
                        continue
                    assert False, f"{s.name}: unsafe claim '{word}' in summary"

    def test_no_mcp_auth_equals_ordivon_approval(self):
        s = ADP_DIR / "mcp-tool-injection-confused-deputy"
        summary = (s / "scenario-summary.md").read_text()
        assert "transport security" in summary or "not governance" in summary.lower(), \
            "MCP auth must be clarified as transport security, not Ordivon approval"


class TestProtectedPathBoundary:
    """Protected paths require boundary permission."""

    def test_protected_path_scenario_is_blocked(self):
        s = ADP_DIR / "protected-path-violation"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"
        assert "protected" in r["result_summary"]["status_reason"].lower() or "governance" in r["result_summary"]["status_reason"].lower()


class TestBaselineDebtMasking:
    """Baseline debt cannot mask new regression."""

    def test_baseline_scenario_is_blocked(self):
        s = ADP_DIR / "baseline-debt-masking"
        r = _load_json(s / "harness-execution-receipt.json")
        assert r["result_summary"]["status"] == "BLOCKED"
        assert "baseline" in r["result_summary"]["status_reason"].lower() or "classification" in r["result_summary"]["status_reason"].lower()


class TestAllScenariosComplete:
    """Every scenario has all required files."""

    def test_each_scenario_has_four_files(self):
        for s in _all_scenarios():
            for fname in ["harness-adapter-manifest.json", "harness-task-request.json",
                          "harness-execution-receipt.json", "scenario-summary.md"]:
                assert (s / fname).exists(), f"{s.name}: missing {fname}"

    def test_all_summaries_have_no_action_authorization(self):
        for s in _all_scenarios():
            summary = (s / "scenario-summary.md").read_text()
            assert "No-action-authorization" in summary or "does not authorize" in summary.lower(), \
                f"{s.name}: missing no-action-authorization statement"

    def test_all_summaries_have_adp_pattern_id(self):
        for s in _all_scenarios():
            summary = (s / "scenario-summary.md").read_text()
            assert "ADP pattern ID:" in summary, f"{s.name}: missing ADP pattern ID"

    def test_all_manifests_declare_non_execution(self):
        for s in _all_scenarios():
            m = _load_json(s / "harness-adapter-manifest.json")
            ns = m.get("non_execution_statement", "").lower()
            assert "does not execute" in ns or "capability only" in ns, \
                f"{s.name}: manifest missing non_execution_statement"

    def test_all_task_requests_have_boundary(self):
        for s in _all_scenarios():
            t = _load_json(s / "harness-task-request.json")
            bd = t.get("boundary_declaration", {})
            assert bd.get("credential_access_blocked") is True, f"{s.name}: credential access not blocked"
            assert bd.get("external_api_blocked") is True, f"{s.name}: external API not blocked"
            assert bd.get("shell_blocked") is True, f"{s.name}: shell not blocked"

    def test_14_scenarios_exist(self):
        names = [d.name for d in _all_scenarios()]
        expected = [
            "approval-fatigue-sandbox-drift", "baseline-debt-masking",
            "candidate-rule-premature-promotion", "capability-authorization-collapse",
            "credential-capability-confusion", "evidence-laundering",
            "external-benchmark-overclaim", "external-side-effect-drift",
            "mcp-tool-injection-confused-deputy", "permission-rule-drift",
            "protected-path-violation", "ready-overclaim",
            "review-bypass", "shell-risk-escalation",
        ]
        for e in expected:
            assert e in names, f"Missing scenario: {e}"
        assert len(names) == 14, f"Expected 14 scenarios, got {len(names)}"
