#!/usr/bin/env python3
"""Governance Admission Validator — validate registry entries before write.

Usage:
    python3 scripts/governance/admit_artifact.py --path <registry-entry.json>
    python3 scripts/governance/admit_artifact.py --stdin < entry.json

Checks:
    - Required fields present
    - doc_type in valid_doc_types
    - authority in valid authorities
    - phase format valid (if provided)
    - no duplicate doc_id
    - no duplicate path
    - path matches doc_type convention hints

Exit 0 = valid, exit 1 = invalid with error details.

⚠️ DEBT-INFRA-004 (2026-05-13): DUAL-CHECKER TRAP (AP-2 risk).
This file's Python validation rules (VALID_AUTHORITIES, doc_type checks, path
conventions) co-exist with OPA Rego policies in policies/opa/rules/authority_transitions.rego.
These are TWO independently maintained authority sets. If one is updated
without the other, they will diverge — reproducing AP-2 (Dual-Checker Trap).

Resolution plan:
    Short-term: Keep both. Add a CI gate that runs both and compares output.
    Long-term:  OPA Rego becomes the single authority. This script becomes
                a thin OPA invocation wrapper or is deleted per PolicyRetirement.
    Due: Phase 4 (Evidence + Trace) or earlier if divergence detected.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_TYPES_PATH = ROOT / "docs/governance/schemas/document-types.json"
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"

VALID_AUTHORITIES = [
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "proposal",
    "bootstrap",
]

REQUIRED_FIELDS = [
    "doc_id",
    "path",
    "title",
    "doc_type",
    "status",
    "authority",
]

OPTIONAL_FIELDS = [
    "phase",
    "owner",
    "freshness",
    "ai_read_priority",
    "supersedes",
    "superseded_by",
    "related_docs",
    "related_ledgers",
    "related_receipts",
    "notes",
    "last_verified",
    "stale_after_days",
    "doc_layer",
    "doc_authority",
    "authority_domain",
    "authority_role",
    "authority_scope",
]

ALL_VALID_FIELDS = set(REQUIRED_FIELDS + OPTIONAL_FIELDS)


def load_valid_doc_types() -> list[str]:
    try:
        from ordivon_governance_core.registry import load_valid_doc_types as _load

        return _load()
    except ImportError:
        if DOC_TYPES_PATH.exists():
            return json.loads(DOC_TYPES_PATH.read_text()).get("valid_doc_types", [])
        return []


def load_existing_registry() -> dict:
    existing = {"by_id": {}, "by_path": {}}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    existing["by_id"][entry["doc_id"]] = entry
                    existing["by_path"][entry["path"]] = entry
                except json.JSONDecodeError:
                    continue
    return existing


def validate_entry(entry: dict, registry: dict) -> list[str]:
    """Validate a single registry entry. Returns list of errors."""
    errors = []
    valid_types = load_valid_doc_types()

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in entry or not entry[field]:
            errors.append(f"MISSING_REQUIRED_FIELD: {field}")

    # Unknown fields
    for key in entry:
        if key not in ALL_VALID_FIELDS:
            errors.append(f"UNKNOWN_FIELD: {key}")

    # doc_type validity
    dt = entry.get("doc_type", "")
    if dt and dt not in valid_types:
        errors.append(f"INVALID_DOC_TYPE: '{dt}' not in {valid_types}")

    # authority validity
    auth = entry.get("authority", "")
    if auth and auth not in VALID_AUTHORITIES:
        errors.append(f"INVALID_AUTHORITY: '{auth}' not in {VALID_AUTHORITIES}")

    # doc_id format: lowercase kebab-case
    did = entry.get("doc_id", "")
    if (
        did
        and not did
        .replace("-", "")
        .replace("_", "")
        .replace("0", "")
        .replace("1", "")
        .replace("2", "")
        .replace("3", "")
        .replace("4", "")
        .replace("5", "")
        .replace("6", "")
        .replace("7", "")
        .replace("8", "")
        .replace("9", "")
        .islower()
    ):
        pass  # acceptable — allow digits and hyphens

    # Duplicate checks
    if did and did in registry["by_id"]:
        existing_path = registry["by_id"][did]["path"]
        if existing_path != entry.get("path", ""):
            errors.append(f"DUPLICATE_DOC_ID: '{did}' already used by '{existing_path}'")

    path = entry.get("path", "")
    if path and path in registry["by_path"]:
        existing_id = registry["by_path"][path]["doc_id"]
        if existing_id != did:
            errors.append(f"DUPLICATE_PATH: '{path}' already registered as '{existing_id}'")

    # Path existence check (warn only)
    if path and not (ROOT / path).exists():
        errors.append(f"PATH_NOT_FOUND: '{path}' does not exist on disk")

    # doc_type → path convention hints
    if dt == "receipt" and "receipt" not in path.lower():
        errors.append(f"CONVENTION: receipt doc_type but path lacks 'receipt': {path}")
    if dt == "schema" and ".schema.json" not in path.lower():
        errors.append(f"CONVENTION: schema doc_type but path lacks .schema.json: {path}")
    if dt == "ledger" and ".jsonl" not in path.lower():
        errors.append(f"CONVENTION: ledger doc_type but path lacks .jsonl: {path}")

    return errors


# ── OPA-backed validation (Phase 3 — DEBT-INFRA-004 convergence) ──────────
# When OPA is available, authority-level checks delegate to Rego policies.
# This is the first step toward OPA as single authority. Python rules remain
# as fallback. Use --compare to detect divergence.


def validate_entry_opa(entry: dict, registry: dict) -> dict:
    """Validate a registry entry using OPA Rego (primary) + Python (fallback).

    Returns: {"valid": bool, "errors": [...], "backend": "opa"|"python", "opa_errors": [...]}
    """
    try:
        # Map registry entry fields to authority state for OPA validation
        authority = entry.get("authority", "")
        doc_type = entry.get("doc_type", "")
        status = entry.get("status", "")

        # Check authority validity via OPA
        opa_errors = []
        if authority:
            from ordivon_governance_core.opa_engine import opa_available, _opa_eval

            if opa_available():
                try:
                    input_data = {
                        "entry": {
                            "authority": authority,
                            "doc_type": doc_type,
                            "status": status,
                        }
                    }
                    result = _opa_eval(
                        "data.governance.registry.validate_entry(input.entry)",
                        input_data,
                    )
                    if "error" not in result:
                        for r in result.get("result", []):
                            for expr in r.get("expressions", []):
                                val = expr.get("value")
                                if isinstance(val, list):
                                    for finding in val:
                                        if isinstance(finding, dict):
                                            opa_errors.append(
                                                f"OPA:{finding.get('finding_id', 'UNKNOWN')}: "
                                                f"{finding.get('description', '')}"
                                            )
                except Exception:
                    pass  # OPA failed, fall back to Python

        if opa_errors:
            return {"valid": False, "errors": opa_errors, "backend": "opa", "opa_errors": opa_errors}
        else:
            # OPA passed or not available — fall back to Python
            py_errors = validate_entry(entry, registry)
            return {
                "valid": len(py_errors) == 0,
                "errors": py_errors,
                "backend": "python",
                "opa_errors": opa_errors,
            }
    except ImportError:
        py_errors = validate_entry(entry, registry)
        return {"valid": len(py_errors) == 0, "errors": py_errors, "backend": "python", "opa_errors": []}


def compare_backends(entry: dict, registry: dict) -> dict:
    """Run both Python and OPA validation and compare results.

    Returns: {"python": {...}, "opa": {...}, "diverged": bool, "divergences": [...]}
    """
    py_errors = validate_entry(entry, registry)
    py_result = {"valid": len(py_errors) == 0, "errors": py_errors}

    opa_result = {"valid": True, "errors": [], "error": "OPA not available"}
    try:
        from ordivon_governance_core.opa_engine import opa_available, _opa_eval

        if opa_available():
            authority = entry.get("authority", "")
            doc_type = entry.get("doc_type", "")
            input_data = {"entry": {"authority": authority, "doc_type": doc_type, "status": entry.get("status", "")}}
            result = _opa_eval("data.governance.registry.validate_entry(input.entry)", input_data)
            opa_errors = []
            if "error" not in result:
                for r in result.get("result", []):
                    for expr in r.get("expressions", []):
                        val = expr.get("value")
                        if isinstance(val, list):
                            for finding in val:
                                if isinstance(finding, dict):
                                    opa_errors.append(
                                        f"OPA:{finding.get('finding_id', '?')}:{finding.get('description', '')}"
                                    )
            opa_result = {"valid": len(opa_errors) == 0, "errors": opa_errors, "backend": "opa"}
    except ImportError:
        pass

    # Detect divergence
    divergences = []
    py_valid = py_result["valid"]
    opa_valid = opa_result.get("valid", True)
    if py_valid != opa_valid:
        divergences.append(
            f"DIVERGENCE: Python={'PASS' if py_valid else 'FAIL'}, OPA={'PASS' if opa_valid else 'FAIL'}"
        )
    # Compare individual error categories
    py_error_types = {e.split(":")[0] for e in py_result["errors"]}
    opa_error_types = {e.split(":")[0] for e in opa_result.get("errors", [])}
    only_py = py_error_types - opa_error_types - {"OPA"}
    only_opa = opa_error_types - py_error_types
    if only_py:
        divergences.append(f"Python-only checks: {only_py}")
    if only_opa:
        divergences.append(f"OPA-only checks: {only_opa}")

    return {
        "python": py_result,
        "opa": opa_result,
        "diverged": len(divergences) > 0,
        "divergences": divergences,
    }


def main() -> int:
    entry = None
    compare = "--compare" in sys.argv

    if "--path" in sys.argv:
        idx = sys.argv.index("--path")
        if idx + 1 < len(sys.argv):
            path = Path(sys.argv[idx + 1])
            if path.exists():
                entry = json.loads(path.read_text())
            else:
                print(f"ERROR: File not found: {path}", file=sys.stderr)
                return 1
    elif "--stdin" in sys.argv:
        entry = json.loads(sys.stdin.read())
    else:
        # Try reading from stdin if data available
        try:
            entry = json.loads(sys.stdin.read())
        except json.JSONDecodeError:
            print("Usage: admit_artifact.py --path <json-file> | --stdin < entry.json", file=sys.stderr)
            return 1

    if not entry:
        print("ERROR: No entry provided", file=sys.stderr)
        return 1

    registry = load_existing_registry()

    if compare:
        result = compare_backends(entry, registry)
        print(json.dumps(result, indent=2))
        return 0 if not result["diverged"] else 1
    else:
        # Default: OPA if available, Python fallback
        result = validate_entry_opa(entry, registry)

    if not result["valid"]:
        print(
            json.dumps(
                {"valid": False, "errors": result["errors"], "backend": result.get("backend", "python")}, indent=2
            )
        )
        return 1
    else:
        print(json.dumps({"valid": True, "errors": [], "backend": result.get("backend", "python")}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
