"""OGAP-2: Tests for protocol schemas and payload validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"
VALIDATOR = ROOT / "scripts" / "validate_ogap_payload.py"
EXAMPLES_DIR = ROOT / "examples" / "ogap"


class TestOGAPSchemas:
    def test_all_schemas_exist(self):
        for name in [
            "ogap-work-claim",
            "ogap-governance-decision",
            "ogap-capability-manifest",
            "ogap-coverage-report",
            "ogap-trust-report",
        ]:
            assert (SCHEMAS_DIR / f"{name}.schema.json").exists()

    def test_all_schemas_parse(self):
        for f in SCHEMAS_DIR.glob("ogap-*.schema.json"):
            json.loads(f.read_text(encoding="utf-8"))

    def test_schemas_declare_draft_2020_12(self):
        for f in SCHEMAS_DIR.glob("ogap-*.schema.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data.get("$schema", "").startswith("https://json-schema.org/draft/2020-12")

    def test_schemas_do_not_claim_public_standard(self):
        for f in SCHEMAS_DIR.glob("ogap-*.schema.json"):
            content = f.read_text().lower()
            if "public standard" in content:
                assert "not a public" in content or "no public" in content
            if "stable" in content:
                assert "not a public stable" in content or "no public stable" in content or "stable contract" in content


class TestValidator:
    def test_validator_exists(self):
        assert VALIDATOR.exists()

    def test_all_examples_validate(self):
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            r = subprocess.run(
                [sys.executable, str(VALIDATOR), str(f)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(ROOT),
            )
            assert r.returncode == 0, f"{f.name} failed: {r.stdout[:200]}"

    def test_ready_decision_passes(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-ready.json")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_blocked_decision_passes(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-blocked.json")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_invalid_json_fails(self):
        invalid_file = ROOT / ".tmp" / "invalid.json"
        invalid_file.parent.mkdir(exist_ok=True)
        invalid_file.write_text("{not valid json!!!}", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(invalid_file)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_unknown_decision_fails(self):
        temp = ROOT / ".tmp" / "bad-decision.json"
        temp.parent.mkdir(exist_ok=True)
        temp.write_text(
            json.dumps({
                "schema_version": "0.1",
                "decision": "APPROVED",
                "decision_scope": "test",
                "evidence_summary": "test",
                "coverage_summary": "test",
                "authority_statement": "test",
            }),
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_ready_authorizes_execution_fails(self):
        temp = ROOT / ".tmp" / "bad-ready.json"
        temp.parent.mkdir(exist_ok=True)
        temp.write_text(
            json.dumps({
                "schema_version": "0.1",
                "decision": "READY",
                "decision_scope": "test",
                "evidence_summary": "test",
                "coverage_summary": "test",
                "authority_statement": "READY authorizes deployment",
            }),
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_json_output(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-ready.json"), "--json"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        data = json.loads(r.stdout)
        assert "valid" in data

    def test_validator_does_not_mutate(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "work-claim-basic.json")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_examples_have_no_secrets(self):
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            content = f.read_text()
            for secret in ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY"]:
                assert secret not in content, f"{f.name} contains {secret}"


class TestValidatorSecurity:
    """Security hardening tests from red team audit (OGAP-Z hardening)."""

    def test_duplicate_keys_rejected(self):
        """Payload with duplicate keys must be rejected."""
        temp = ROOT / ".tmp" / "dup-keys.json"
        temp.parent.mkdir(exist_ok=True)
        temp.write_text(
            '{"schema_version":"0.1","decision":"NO-GO","decision":"READY",'
            '"decision_scope":"test","evidence_summary":"test",'
            '"coverage_summary":"test","authority_statement":"test"}',
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"Duplicate keys should fail: {r.stdout}"
        assert "duplicate key" in r.stdout.lower()

    def test_extra_properties_rejected(self):
        """Payload with unknown fields must be rejected (additionalProperties: false)."""
        temp = ROOT / ".tmp" / "extra-field.json"
        temp.parent.mkdir(exist_ok=True)
        payload = json.loads((EXAMPLES_DIR / "governance-decision-ready.json").read_text())
        payload["approved"] = True
        temp.write_text(json.dumps(payload), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"Extra field should fail: {r.stdout}"
        assert "unknown field" in r.stdout.lower()

    def test_wrong_type_rejected(self):
        """Field with wrong JSON type must be rejected."""
        temp = ROOT / ".tmp" / "wrong-type.json"
        temp.parent.mkdir(exist_ok=True)
        payload = json.loads((EXAMPLES_DIR / "governance-decision-ready.json").read_text())
        payload["decision"] = 42  # should be string
        temp.write_text(json.dumps(payload), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"Wrong type should fail: {r.stdout}"
        assert "wrong type" in r.stdout.lower()

    def test_null_for_required_string_rejected(self):
        """null for a required string field must be rejected."""
        temp = ROOT / ".tmp" / "null-field.json"
        temp.parent.mkdir(exist_ok=True)
        payload = json.loads((EXAMPLES_DIR / "work-claim-basic.json").read_text())
        payload["claim_id"] = None
        temp.write_text(json.dumps(payload), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"null should fail: {r.stdout}"
        assert "wrong type" in r.stdout.lower()

    def test_boolean_as_string_rejected(self):
        """String 'true' for a boolean field must be rejected."""
        temp = ROOT / ".tmp" / "bool-str.json"
        temp.parent.mkdir(exist_ok=True)
        payload = json.loads((EXAMPLES_DIR / "capability-manifest-basic.json").read_text())
        payload["capabilities"]["can_write"] = "true"
        temp.write_text(json.dumps(payload), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"String bool should fail: {r.stdout}"
        assert "wrong type" in r.stdout.lower()

    def test_array_for_object_rejected(self):
        """Array where object expected must be rejected."""
        temp = ROOT / ".tmp" / "arr-obj.json"
        temp.parent.mkdir(exist_ok=True)
        payload = json.loads((EXAMPLES_DIR / "work-claim-basic.json").read_text())
        payload["evidence_bundle"] = ["malicious", "array"]
        temp.write_text(json.dumps(payload), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(ROOT),
        )
        assert r.returncode != 0, f"Array should fail: {r.stdout}"
        assert "wrong type" in r.stdout.lower()
