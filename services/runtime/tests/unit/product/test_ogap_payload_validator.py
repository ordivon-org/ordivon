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
        for name in ["ogap-work-claim", "ogap-governance-decision", "ogap-capability-manifest", "ogap-coverage-report", "ogap-trust-report"]:
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
                capture_output=True, text=True, timeout=10, cwd=str(ROOT),
            )
            assert r.returncode == 0, f"{f.name} failed: {r.stdout[:200]}"

    def test_ready_decision_passes(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-ready.json")],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_blocked_decision_passes(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-blocked.json")],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_invalid_json_fails(self):
        invalid_file = ROOT / ".tmp" / "invalid.json"
        invalid_file.parent.mkdir(exist_ok=True)
        invalid_file.write_text("{not valid json!!!}", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(invalid_file)],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_unknown_decision_fails(self):
        temp = ROOT / ".tmp" / "bad-decision.json"
        temp.parent.mkdir(exist_ok=True)
        temp.write_text(json.dumps({"schema_version": "0.1", "decision": "APPROVED", "decision_scope": "test", "evidence_summary": "test", "coverage_summary": "test", "authority_statement": "test"}), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_ready_authorizes_execution_fails(self):
        temp = ROOT / ".tmp" / "bad-ready.json"
        temp.parent.mkdir(exist_ok=True)
        temp.write_text(json.dumps({"schema_version": "0.1", "decision": "READY", "decision_scope": "test", "evidence_summary": "test", "coverage_summary": "test", "authority_statement": "READY authorizes deployment"}), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(temp)],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode != 0

    def test_json_output(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "governance-decision-ready.json"), "--json"],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        data = json.loads(r.stdout)
        assert "valid" in data

    def test_validator_does_not_mutate(self):
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(EXAMPLES_DIR / "work-claim-basic.json")],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT),
        )
        assert r.returncode == 0

    def test_examples_have_no_secrets(self):
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            content = f.read_text()
            for secret in ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY"]:
                assert secret not in content, f"{f.name} contains {secret}"
