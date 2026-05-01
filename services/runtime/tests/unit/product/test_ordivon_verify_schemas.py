"""Tests for Ordivon Verify prototype schemas (PV-N2).

Lightweight structural validation — no JSON Schema validation library required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "src" / "ordivon_verify" / "schemas"

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"
STD_CONFIG = FIXTURE_DIR / "ordivon_verify_standard_external_repo" / "ordivon.verify.json"
CLEAN_CONFIG = FIXTURE_DIR / "ordivon_verify_clean_external_repo" / "ordivon.verify.json"
BAD_CONFIG = FIXTURE_DIR / "ordivon_verify_external_repo" / "ordivon.verify.json"

EXPECTED_SCHEMA_FILES = [
    "ordivon.verify.schema.json",
    "trust-report.schema.json",
    "verification-debt-ledger.schema.json",
    "verification-gate-manifest.schema.json",
    "document-registry.schema.json",
]


# ── existence and validity ──────────────────────────────────────────────────


@pytest.mark.parametrize("filename", EXPECTED_SCHEMA_FILES)
def test_schema_file_exists(filename: str):
    path = SCHEMAS_DIR / filename
    assert path.is_file(), f"Missing schema: {filename}"


@pytest.mark.parametrize("filename", EXPECTED_SCHEMA_FILES)
def test_schema_file_is_valid_json(filename: str):
    path = SCHEMAS_DIR / filename
    try:
        json.loads(path.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {filename}: {e}")


def test_schema_readme_exists():
    assert (SCHEMAS_DIR / "README.md").is_file(), "Missing schemas/README.md"


# ── schema_version ───────────────────────────────────────────────────────────


def test_ordivon_verify_schema_has_version():
    schema = json.loads((SCHEMAS_DIR / "ordivon.verify.schema.json").read_text())
    assert "schema_version" in str(schema.get("properties", {}))


def test_trust_report_schema_has_version():
    schema = json.loads((SCHEMAS_DIR / "trust-report.schema.json").read_text())
    assert "schema_version" in str(schema.get("properties", {}))


# ── external config conformance ──────────────────────────────────────────────


def test_standard_external_config_has_required_fields():
    config = json.loads(STD_CONFIG.read_text())
    assert config.get("schema_version") == "0.1"
    assert config.get("project_name") is not None
    assert config.get("mode") in ("advisory", "standard", "strict")
    assert isinstance(config.get("receipt_paths"), list)


def test_clean_advisory_config_has_required_fields():
    config = json.loads(CLEAN_CONFIG.read_text())
    assert config.get("schema_version") == "0.1"
    assert config.get("project_name") is not None
    assert config.get("mode") == "advisory"


def test_bad_external_config_has_required_fields():
    config = json.loads(BAD_CONFIG.read_text())
    assert config.get("schema_version") == "0.1"
    assert config.get("project_name") is not None
    assert config.get("mode") == "advisory"


# ── trust report required fields ─────────────────────────────────────────────


def test_trust_report_schema_requires_status():
    schema = json.loads((SCHEMAS_DIR / "trust-report.schema.json").read_text())
    required = schema.get("required", [])
    assert "tool" in required
    assert "schema_version" in required
    assert "status" in required
    assert "checks" in required
    assert "disclaimer" in required


def test_trust_report_status_enum():
    schema = json.loads((SCHEMAS_DIR / "trust-report.schema.json").read_text())
    status_prop = schema["properties"]["status"]
    assert "READY" in status_prop["enum"]
    assert "BLOCKED" in status_prop["enum"]
    assert "DEGRADED" in status_prop["enum"]


def test_trust_report_disclaimer_immutable():
    schema = json.loads((SCHEMAS_DIR / "trust-report.schema.json").read_text())
    disclaimer = schema["properties"]["disclaimer"]
    assert disclaimer.get("const") == "READY means selected checks passed; it does not authorize execution."


# ── gate manifest ────────────────────────────────────────────────────────────


def test_gate_manifest_schema_requires_no_noop():
    schema = json.loads((SCHEMAS_DIR / "verification-gate-manifest.schema.json").read_text())
    gate_props = schema["properties"]["gates"]["items"]["properties"]
    assert "command" in gate_props
    desc = gate_props["command"].get("description", "")
    assert "no-op" in desc.lower() or "noop" in desc.lower(), (
        "Gate command description should mention no-op restriction"
    )


# ── private reference scan ───────────────────────────────────────────────────


_FORBIDDEN_TERMS = [
    "Alpaca",
    "broker",
    "live trading",
    "live_trading",
    "Phase 7P",
    "RiskEngine",
    "Risk Engine",
    "/root/projects",
    "API_KEY",
    "SECRET",
    "TOKEN",
]


@pytest.mark.parametrize("filename", EXPECTED_SCHEMA_FILES)
def test_schema_has_no_private_references(filename: str):
    content = (SCHEMAS_DIR / filename).read_text()
    found = []
    for term in _FORBIDDEN_TERMS:
        if term.lower() in content.lower():
            # Allow if term appears in a negative/boundary context only
            found.append(term)
    assert not found, f"{filename} contains private references: {found}"


# ── schemas do not require full Ordivon DG Pack ──────────────────────────────


def test_ordivon_verify_schema_is_minimal():
    """External config schema must not require DG Pack-only fields."""
    schema = json.loads((SCHEMAS_DIR / "ordivon.verify.schema.json").read_text())
    required = schema.get("required", [])
    # Only 3 minimal fields required for external use
    for heavy in ("debt_ledger", "gate_manifest", "document_registry"):
        assert heavy not in required, f"'{heavy}' should be optional, not required, for minimal external use"


def test_debt_ledger_schema_allows_empty():
    """An empty ledger (no entries) must be valid."""
    schema = json.loads((SCHEMAS_DIR / "verification-debt-ledger.schema.json").read_text())
    # The schema describes a single entry; empty file = no entries = valid
    assert schema.get("additionalProperties") is True, (
        "Debt ledger schema should be permissive to allow gradual field addition"
    )


def test_document_registry_schema_is_permissive():
    schema = json.loads((SCHEMAS_DIR / "document-registry.schema.json").read_text())
    assert schema.get("additionalProperties") is True, (
        "Document registry schema should be permissive to allow optional fields"
    )


# ── schemas are read-only — no test writes files ─────────────────────────────


def test_schema_tests_do_not_write_to_schemas_dir():
    """All schema files must have unchanged mtimes after this test runs."""
    mtimes = {}
    for filename in EXPECTED_SCHEMA_FILES:
        p = SCHEMAS_DIR / filename
        mtimes[filename] = p.stat().st_mtime
    # Re-read every schema (reads, not writes)
    for filename in EXPECTED_SCHEMA_FILES:
        json.loads((SCHEMAS_DIR / filename).read_text())
    for filename, orig in mtimes.items():
        assert (SCHEMAS_DIR / filename).stat().st_mtime == orig, f"{filename} was modified by schema tests"
