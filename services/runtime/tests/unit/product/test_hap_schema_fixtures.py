"""HAP-1: Tests for HAP schema fixtures — structural and semantic validation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = ROOT / "examples" / "hap"
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"


class TestHAPFixtureStructure:
    def test_all_basic_fixtures_exist(self):
        for name in [
            "harness-adapter-manifest.json",
            "harness-task-request.json",
            "harness-execution-receipt.json",
        ]:
            path = EXAMPLES_DIR / "basic" / name
            assert path.exists(), f"Missing fixture: {path}"

    def test_all_scenario_dirs_have_manifest(self):
        for scenario_dir in (EXAMPLES_DIR / "scenarios").iterdir():
            if scenario_dir.is_dir():
                manifest = scenario_dir / "harness-adapter-manifest.json"
                assert manifest.exists(), f"Missing manifest in {scenario_dir.name}"

    def test_all_scenario_dirs_have_task_request(self):
        for scenario_dir in (EXAMPLES_DIR / "scenarios").iterdir():
            if scenario_dir.is_dir():
                task_req = scenario_dir / "harness-task-request.json"
                assert task_req.exists(), f"Missing task request in {scenario_dir.name}"

    def test_all_fixtures_are_valid_json(self):
        for f in EXAMPLES_DIR.glob("**/*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{f.relative_to(ROOT)}: not a JSON object"

    def test_all_manifests_have_schema_version(self):
        for f in EXAMPLES_DIR.glob("**/harness-adapter-manifest.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("schema_version") == "0.1", f"{f.relative_to(ROOT)}: missing or wrong schema_version"

    def test_all_task_requests_have_schema_version(self):
        for f in EXAMPLES_DIR.glob("**/harness-task-request.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("schema_version") == "0.1", f"{f.relative_to(ROOT)}: missing or wrong schema_version"

    def test_all_receipts_have_schema_version(self):
        for f in EXAMPLES_DIR.glob("**/harness-execution-receipt.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("schema_version") == "0.1", f"{f.relative_to(ROOT)}: missing or wrong schema_version"


class TestHAPFixtureSemantics:
    def test_no_manifest_claims_authorization(self):
        """No harness manifest should claim it authorizes action."""
        for f in EXAMPLES_DIR.glob("**/harness-adapter-manifest.json"):
            content = f.read_text().lower()
            assert "authorizes action" not in content, f"{f.relative_to(ROOT)}: claims authorization"
            assert "authorizes execution" not in content, f"{f.relative_to(ROOT)}: claims execution authorization"

    def test_no_task_request_claims_approval(self):
        """No task request should claim it is approved."""
        for f in EXAMPLES_DIR.glob("**/harness-task-request.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            auth = data.get("authority_statement", "").lower()
            assert "not" in auth or "does not" in auth, f"{f.relative_to(ROOT)}: authority_statement must be a denial"

    def test_all_manifests_declare_capability_not_authorization(self):
        for f in EXAMPLES_DIR.glob("**/harness-adapter-manifest.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            caps = data.get("capabilities", {})
            auth = caps.get("authority_statement", "")
            assert "can_x does not imply may_x" in auth.lower() or "not authorization" in auth.lower(), (
                f"{f.relative_to(ROOT)}: capabilities missing authority disclaimer"
            )

    def test_no_fixture_uses_can_access_secrets(self):
        for f in EXAMPLES_DIR.glob("**/*.json"):
            content = f.read_text()
            assert "can_access_secrets" not in content, f"{f.relative_to(ROOT)}: uses forbidden 'can_access_secrets'"

    def test_credential_read_blocked_scenario_has_correct_capability(self):
        path = EXAMPLES_DIR / "scenarios" / "credential-read-blocked" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        assert data["capabilities"]["can_read_credentials"] is True, (
            "credential-read-blocked scenario must declare can_read_credentials=True (as capability)"
        )
        assert data["declared_boundaries"]["credential_access_blocked"] is True, (
            "credential-read-blocked scenario must block credential access at boundary"
        )

    def test_five_scenarios_exist(self):
        scenarios = [d.name for d in (EXAMPLES_DIR / "scenarios").iterdir() if d.is_dir()]
        assert "read-only-review" in scenarios
        assert "workspace-patch-proposal" in scenarios
        assert "shell-risk-blocked" in scenarios
        assert "credential-read-blocked" in scenarios
        assert "external-side-effect-blocked" in scenarios

    def test_external_side_effect_blocked_has_correct_semantics(self):
        path = EXAMPLES_DIR / "scenarios" / "external-side-effect-blocked" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        assert data["capabilities"]["can_call_external_api"] is True, "Must declare capability"
        assert data["declared_boundaries"]["external_api_blocked"] is True, "Must block external API at boundary"

    def test_shell_risk_blocked_has_shell_in_forbidden(self):
        path = EXAMPLES_DIR / "scenarios" / "shell-risk-blocked" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        assert "run_shell" in data["declared_boundaries"]["forbidden_actions"], (
            "shell execution must be in forbidden_actions"
        )
        assert data["declared_boundaries"]["shell_blocked"] is True, "shell_blocked must be True"

    def test_workspace_patch_proposal_requires_review(self):
        path = EXAMPLES_DIR / "scenarios" / "workspace-patch-proposal" / "harness-task-request.json"
        data = json.loads(path.read_text())
        assert "apply_patch" in data["boundary_declaration"]["requires_review_for"], (
            "patch proposal must require review"
        )
        assert "proposed" in data["authority_statement"].lower() or "not applied" in data["authority_statement"], (
            "patch must be described as proposed, not applied"
        )
