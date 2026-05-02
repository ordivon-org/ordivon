"""HAP-1: Tests for HAP schemas and payload validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"
VALIDATOR = ROOT / "scripts" / "validate_hap_payload.py"
EXAMPLES_DIR = ROOT / "examples" / "hap"


class TestHAPSchemas:
    def test_all_hap_schemas_exist(self):
        for name in [
            "hap-adapter-manifest",
            "hap-task-request",
            "hap-execution-receipt",
        ]:
            path = SCHEMAS_DIR / f"{name}.schema.json"
            assert path.exists(), f"Missing schema: {path}"

    def test_all_hap_schemas_parse(self):
        for f in SCHEMAS_DIR.glob("hap-*.schema.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert isinstance(data, dict)

    def test_hap_schemas_declare_draft_2020_12(self):
        for f in SCHEMAS_DIR.glob("hap-*.schema.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("$schema", "").startswith("https://json-schema.org/draft/2020-12"), (
                f"{f.name} missing draft 2020-12 $schema"
            )

    def test_hap_schemas_declare_prototype_maturity(self):
        for f in SCHEMAS_DIR.glob("hap-*.schema.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("_maturity") == "prototype", f"{f.name} missing _maturity: prototype"

    def test_hap_schemas_do_not_claim_public_standard(self):
        for f in SCHEMAS_DIR.glob("hap-*.schema.json"):
            content = f.read_text().lower()
            assert "public standard" not in content, f"{f.name} claims 'public standard'"
            assert "stable contract" not in content or "not a public stable contract" in content, (
                f"{f.name} has unqualified 'stable contract'"
            )

    def test_hap_schemas_do_not_use_can_access_secrets(self):
        """can_access_secrets must not be reintroduced — use can_read_credentials."""
        for f in SCHEMAS_DIR.glob("hap-*.schema.json"):
            content = f.read_text()
            assert "can_access_secrets" not in content, (
                f"{f.name} uses forbidden 'can_access_secrets' — use 'can_read_credentials'"
            )


class TestHAPValidator:
    def test_validator_exists(self):
        assert VALIDATOR.exists(), f"Validator not found: {VALIDATOR}"

    def test_basic_adapter_manifest_validates(self):
        r = _validate("basic/harness-adapter-manifest.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_basic_task_request_validates(self):
        r = _validate("basic/harness-task-request.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_basic_execution_receipt_validates(self):
        r = _validate("basic/harness-execution-receipt.json")
        assert r.returncode == 0, f"FAIL: {r.stdout}"

    def test_all_scenario_fixtures_validate(self):
        failures = []
        for scenario_dir in sorted((EXAMPLES_DIR / "scenarios").iterdir()):
            if not scenario_dir.is_dir():
                continue
            for f in sorted(scenario_dir.glob("*.json")):
                # Pass path relative to EXAMPLES_DIR
                rel = str(f.relative_to(EXAMPLES_DIR))
                r = _validate(rel)
                if r.returncode != 0:
                    failures.append(f"{f.name}: {r.stdout.strip()}")
        assert not failures, f"Scenario fixture failures: {failures}"

    def test_adapter_manifest_missing_required_fails(self):
        r = _validate_string('{"schema_version": "0.1", "adapter_id": "x"}')
        assert r.returncode != 0, "Should fail on missing required fields"

    def test_task_request_missing_boundary_fails(self):
        r = _validate_string(
            '{"schema_version": "0.1", "request_id": "x", "adapter_id": "y", '
            '"task_type": "z", "description": "d", "requested_capabilities": []}'
        )
        assert r.returncode != 0, "Should fail on missing boundary_declaration"

    def test_execution_receipt_missing_evidence_fails(self):
        r = _validate_string(
            '{"schema_version": "0.1", "receipt_id": "x", "request_id": "y", '
            '"plan_id": "p", "commands_run": [], "files_changed": [], '
            '"passed_checks": [], "failed_checks": []}'
        )
        assert r.returncode != 0, "Should fail on missing evidence_bundle"

    def test_capability_declares_authority_statement(self):
        """All valid manifests must include the authority disclaimer in capabilities."""
        r = _validate("basic/harness-adapter-manifest.json")
        assert r.returncode == 0
        payload = json.loads((EXAMPLES_DIR / "basic/harness-adapter-manifest.json").read_text())
        stmt = payload["capabilities"].get("authority_statement", "").lower()
        assert (
            "not authorization" in stmt
            or "does not authorize" in stmt
            or "not imply" in stmt
            or "does not imply" in stmt
        )

    def test_manifest_blocked_credentials_do_not_leak(self):
        """Credential access blocked manifests must have credential_access_blocked=True."""
        for scenario in ["read-only-review", "credential-read-blocked"]:
            manifest_path = EXAMPLES_DIR / "scenarios" / scenario / "harness-adapter-manifest.json"
            data = json.loads(manifest_path.read_text())
            boundaries = data.get("declared_boundaries", {})
            assert boundaries.get("credential_access_blocked") is True, (
                f"{scenario}: credential_access_blocked must be True"
            )

    def test_shell_blocked_scenarios_enforce_boundary(self):
        """Shell-blocked scenarios must have shell_blocked=True."""
        path = EXAMPLES_DIR / "scenarios" / "shell-risk-blocked" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        assert data["declared_boundaries"]["shell_blocked"] is True

    def test_external_api_blocked_scenarios_enforce_boundary(self):
        """External API blocked scenarios must have external_api_blocked=True."""
        path = EXAMPLES_DIR / "scenarios" / "external-side-effect-blocked" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        assert data["declared_boundaries"]["external_api_blocked"] is True

    def test_read_only_scenario_has_no_destructive_capabilities(self):
        """Read-only scenario must have all destructive capabilities set to False."""
        path = EXAMPLES_DIR / "scenarios" / "read-only-review" / "harness-adapter-manifest.json"
        data = json.loads(path.read_text())
        caps = data["capabilities"]
        assert caps["can_write_files"] is False
        assert caps["can_run_shell"] is False
        assert caps["can_read_credentials"] is False
        assert caps["can_call_external_api"] is False

    def test_capability_not_authorization_language_present(self):
        """All manifests must include 'Capability declaration is not authorization' or equivalent."""
        for f in EXAMPLES_DIR.glob("**/*.json"):
            if "harness-adapter-manifest" in str(f):
                data = json.loads(f.read_text())
                auth = data.get("authority_statement", "")
                assert "not authorization" in auth.lower() or "does not authorize" in auth.lower(), (
                    f"{f.relative_to(ROOT)}: missing authority disclaimer"
                )

    def test_ready_means_evidence_not_authorization(self):
        """Any READY status must have disclaimer that it does not authorize execution."""
        path = EXAMPLES_DIR / "basic/harness-execution-receipt.json"
        data = json.loads(path.read_text())
        if data.get("result_summary", {}).get("status") == "READY":
            ra = data["result_summary"].get("authority_statement", "").lower()
            assert "does not authorize" in ra or "not authorization" in ra, (
                "READY result_summary missing authorization disclaimer"
            )


class TestHAPDocs:
    def test_architecture_doc_exists(self):
        path = ROOT / "docs" / "architecture" / "harness-adapter-protocol-hap-1.md"
        assert path.exists(), f"Missing HAP architecture doc: {path}"

    def test_runtime_doc_exists(self):
        path = ROOT / "docs" / "runtime" / "hap-foundation-hap-1.md"
        assert path.exists(), f"Missing HAP runtime doc: {path}"

    def test_stage_notes_exist(self):
        path = ROOT / "docs" / "product" / "harness-adapter-protocol-stage-notes-hap-1.md"
        assert path.exists(), f"Missing HAP stage notes: {path}"

    def test_architecture_doc_disclaims_public_standard(self):
        content = (ROOT / "docs" / "architecture" / "harness-adapter-protocol-hap-1.md").read_text()
        assert "Not a public standard" in content

    def test_architecture_doc_disclaims_live_api(self):
        content = (ROOT / "docs" / "architecture" / "harness-adapter-protocol-hap-1.md").read_text()
        assert "live API" in content.lower() or "No live API" in content

    def test_architecture_doc_uses_can_read_credentials(self):
        content = (ROOT / "docs" / "architecture" / "harness-adapter-protocol-hap-1.md").read_text()
        assert "can_read_credentials" in content
        assert "can_access_secrets" not in content, "HAP docs must not reintroduce can_access_secrets"

    def test_ogap_is_closed_in_runtime_doc(self):
        content = (ROOT / "docs" / "runtime" / "hap-foundation-hap-1.md").read_text()
        assert "OGAP-1" in content or "OGAP" in content

    def test_capability_not_authorization_in_arch_doc(self):
        content = (ROOT / "docs" / "architecture" / "harness-adapter-protocol-hap-1.md").read_text()
        assert (
            "Capability declaration is not authorization" in content
            or "capability is not authorization" in content.lower()
        )


def _validate(relative_path: str) -> subprocess.CompletedProcess:
    payload = EXAMPLES_DIR / relative_path
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(payload)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(ROOT),
    )


def _validate_string(json_str: str) -> subprocess.CompletedProcess:
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_str)
        f.flush()
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), f.name],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
    Path(f.name).unlink(missing_ok=True)
    return r
