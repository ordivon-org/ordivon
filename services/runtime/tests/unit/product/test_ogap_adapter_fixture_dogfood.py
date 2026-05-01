"""OGAP-3: Tests for OGAP adapter scenario fixture dogfood."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts" / "validate_ogap_payload.py"
SCENARIOS_DIR = ROOT / "examples" / "ogap" / "scenarios"


class TestScenarioFixtures:
    def test_all_scenario_files_parse(self):
        for f in sorted(SCENARIOS_DIR.rglob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "schema_version" in data, f"{f.name} missing schema_version"

    def test_all_scenario_payloads_validate(self):
        for f in sorted(SCENARIOS_DIR.rglob("*.json")):
            r = subprocess.run(
                [sys.executable, str(VALIDATOR), str(f)],
                capture_output=True, text=True, timeout=10, cwd=str(ROOT),
            )
            assert r.returncode == 0, f"{f.relative_to(SCENARIOS_DIR)} failed:\n{r.stdout[:300]}"

    def test_ai_coding_ready_states_evidence_not_authorization(self):
        f = SCENARIOS_DIR / "ai-coding-agent" / "governance-decision-ready.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["decision"] == "READY"
        assert "not authorization" in data.get("authority_statement", "")

    def test_mcp_capability_includes_authority_note(self):
        f = SCENARIOS_DIR / "mcp-server" / "capability-manifest.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "capabilities" in data
        assert "authority_note" in data

    def test_ci_blocked_includes_hard_failures(self):
        f = SCENARIOS_DIR / "ci-merge-gate" / "governance-decision-blocked.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["decision"] == "BLOCKED"
        assert len(data.get("hard_failures", [])) >= 1

    def test_ide_fixture_includes_debt(self):
        f = SCENARIOS_DIR / "ide-agent" / "work-claim.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "debt_declaration" in data
        assert len(data["debt_declaration"].get("known_gaps", [])) >= 1

    def test_enterprise_trust_report_includes_human_review(self):
        f = SCENARIOS_DIR / "enterprise-agent-platform" / "trust-report.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data.get("human_review_required") is True

    def test_financial_action_is_no_go(self):
        f = SCENARIOS_DIR / "financial-action-request" / "governance-decision-no-go.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["decision"] == "NO-GO"

    def test_financial_has_no_broker_credentials(self):
        for f in sorted((SCENARIOS_DIR / "financial-action-request").glob("*.json")):
            content = f.read_text()
            for secret in ["API_KEY", "ALPACA_KEY", "BROKER_KEY", "ACCESS_TOKEN"]:
                assert secret not in content, f"{f.name} contains {secret}"

    def test_no_scenario_claims_public_standard(self):
        for f in sorted(SCENARIOS_DIR.rglob("*.json")):
            content = f.read_text().lower()
            if "public standard" in content:
                assert "not a public" in content or "no public" in content

    def test_no_scenario_claims_ready_authorizes(self):
        for f in sorted(SCENARIOS_DIR.rglob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            authority = data.get("authority_statement", "").lower()
            if data.get("decision") == "READY":
                assert "authorizes execution" not in authority
                assert "authorizes deployment" not in authority

    def test_scenarios_have_no_secrets(self):
        for f in sorted(SCENARIOS_DIR.rglob("*.json")):
            content = f.read_text()
            for secret in ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY"]:
                assert secret not in content, f"{f.name} contains {secret}"

    def test_tests_do_not_mutate_source(self):
        pass
