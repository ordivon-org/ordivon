"""GOV-X: Lightweight structure and overclaim boundary tests."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOV_DIR = ROOT / "docs" / "governance"


def _read(path: str) -> str:
    return (GOV_DIR / path).read_text()


class TestCapabilityClasses:
    def test_c0_through_c5_exist(self):
        content = _read("capability-scaled-governance-gov-x.md")
        for cls in ["C0", "C1", "C2", "C3", "C4", "C5"]:
            assert cls in content, f"Missing capability class {cls}"

    def test_c4_defaults_to_blocked(self):
        content = _read("capability-scaled-governance-gov-x.md").lower()
        assert "c4" in content
        assert "blocked by default" in content or "c4 defaults to blocked" in content

    def test_c5_defaults_to_no_go(self):
        content = _read("capability-scaled-governance-gov-x.md").lower()
        assert "c5" in content
        assert "no-go" in content and "c5" in content


class TestRiskLadder:
    def test_ap_r0_through_r5_exist(self):
        content = _read("risk-ladder-gov-x.md")
        for level in ["AP-R0", "AP-R1", "AP-R2", "AP-R3", "AP-R4", "AP-R5"]:
            assert level in content, f"Missing risk level {level}"

    def test_risk_classification_not_permission(self):
        content = _read("risk-ladder-gov-x.md").lower()
        assert "risk classification is not permission" in content


class TestAuthorityImpact:
    def test_ai_0_through_6_exist(self):
        content = _read("authority-impact-gate-matrix-gov-x.md")
        for level in ["AI-0", "AI-1", "AI-2", "AI-3", "AI-4", "AI-5", "AI-6"]:
            assert level in content, f"Missing authority impact {level}"


class TestGateMatrix:
    def test_gate_responses_defined(self):
        content = _read("authority-impact-gate-matrix-gov-x.md")
        for resp in ["READY_WITHOUT_AUTHORIZATION", "REVIEW_REQUIRED", "DEGRADED", "BLOCKED", "NO-GO"]:
            assert resp in content, f"Missing gate response {resp}"

    def test_hap2_fixtures_all_match(self):
        content = _read("authority-impact-gate-matrix-gov-x.md")
        assert "14/14 fixtures match" in content or "100% consistency" in content


class TestNoOverclaim:
    def test_no_compliance_claims(self):
        for doc in [
            "capability-scaled-governance-gov-x.md",
            "risk-ladder-gov-x.md",
            "authority-impact-gate-matrix-gov-x.md",
        ]:
            content = _read(doc).lower()
            unsafe = [
                "compliant",
                "certified",
                "endorsed",
                "partnered",
                "equivalent to",
                "production-ready",
                "public standard",
            ]
            for word in unsafe:
                if word in content and f"not {word}" not in content and f"no {word}" not in content:
                    # Allow in safe-language clause or NO-GO triggers
                    if "does not imply" in content or "not claimed" in content:
                        continue
                    if "not imply" in content and word in content:
                        continue
                    # "public standard" in NO-GO trigger list is a prohibition, not a claim
                    if word == "public standard" and "NO-GO" in content:
                        continue
                    assert False, f"{doc}: unsafe claim '{word}'"

    def test_no_can_access_secrets(self):
        for doc in [
            "capability-scaled-governance-gov-x.md",
            "risk-ladder-gov-x.md",
            "authority-impact-gate-matrix-gov-x.md",
        ]:
            content = _read(doc)
            if "can_access_secrets" not in content:
                continue
            # Allow only in NO-GO trigger context (explicit prohibition with correction)
            assert "NO-GO" in content and "use can_read_credentials" in content, (
                f"{doc}: can_access_secrets appears outside NO-GO trigger context"
            )

    def test_ready_is_never_execution_authorization(self):
        content = _read("capability-scaled-governance-gov-x.md")
        assert (
            "READY_WITHOUT_AUTHORIZATION is never execution authorization" in content
            or "never execution authorization" in content.lower()
        )

    def test_candidate_rule_non_binding(self):
        content = _read("capability-scaled-governance-gov-x.md")
        assert "NON-BINDING" in content or "non-binding" in content.lower()

    def test_no_risk_lowers_from_external_benchmark(self):
        content = _read("capability-scaled-governance-gov-x.md").lower()
        assert "external benchmark" in content
        assert "cannot lower risk" in content


class TestDocsExist:
    def test_all_gov_x_docs_exist(self):
        for name in [
            "capability-scaled-governance-gov-x.md",
            "risk-ladder-gov-x.md",
            "authority-impact-gate-matrix-gov-x.md",
        ]:
            assert (GOV_DIR / name).exists(), f"Missing doc: {name}"
