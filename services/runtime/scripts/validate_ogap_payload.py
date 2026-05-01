#!/usr/bin/env python3
"""OGAP-2: Ordivon Governance Adapter Protocol — Payload Validator.

Validates OGAP JSON payloads against draft v0 schemas and safety invariants.
Uses jsonschema library for full Draft 2020-12 compliance (types, formats,
patterns, enum, nested validation, additionalProperties).

Usage:
    uv run python scripts/validate_ogap_payload.py <file.json>
    uv run python scripts/validate_ogap_payload.py <file.json> --json

Does not call network APIs, mutate files, or authorize action.
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"

VALID_DECISIONS = {"READY", "DEGRADED", "BLOCKED", "HOLD", "REJECT", "NO-GO"}


# ═══════════════════════════════════════════════════════════════════════
# Custom format checkers for OGAP-specific semantics
# ═══════════════════════════════════════════════════════════════════════

_ogap_format_checker = jsonschema.FormatChecker()


@_ogap_format_checker.checks("ogap-decision", ValueError)
def _check_ogap_decision(instance):
    if not isinstance(instance, str):
        return True  # type checker handles this
    if instance not in VALID_DECISIONS:
        raise ValueError(f"'{instance}' is not a valid OGAP decision (allowed: {sorted(VALID_DECISIONS)})")
    return True


@_ogap_format_checker.checks("ogap-schema-version", ValueError)
def _check_schema_version(instance):
    if not isinstance(instance, str):
        return True
    import re

    if not re.match(r"^0\.\d+$", instance):
        raise ValueError(f"'{instance}' is not a valid OGAP schema version (expected '0.N' prototype format)")
    return True


# ═══════════════════════════════════════════════════════════════════════
# JSON parsing with duplicate key detection
# ═══════════════════════════════════════════════════════════════════════


def load_payload_with_dup_check(path: Path) -> tuple[dict, list[str]]:
    """Load JSON payload, detecting duplicate keys.

    Returns (payload, dup_errors).
    """
    dup_errors: list[str] = []

    def _dup_hook(pairs):
        result = OrderedDict()
        for key, value in pairs:
            if key in result:
                dup_errors.append(f"duplicate key: '{key}' (overwrites previous value)")
            result[key] = value
        return result

    raw_text = path.read_text(encoding="utf-8")
    payload = json.loads(raw_text, object_pairs_hook=_dup_hook)
    return payload, dup_errors


# ═══════════════════════════════════════════════════════════════════════
# Schema validation (jsonschema-backed)
# ═══════════════════════════════════════════════════════════════════════


def validate_against_schema(payload: dict, schema: dict) -> list[str]:
    """Validate payload against JSON Schema using jsonschema library.

    Returns human-readable error strings. Zero-length list = valid.
    """
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=_ogap_format_checker,
    )

    for err in validator.iter_errors(payload):
        path = "/".join(str(p) for p in err.absolute_path) if err.absolute_path else "(root)"
        errors.append(f"{path}: {err.message}")

    return errors


# ═══════════════════════════════════════════════════════════════════════
# OGAP-specific safety checks (beyond JSON Schema)
# ═══════════════════════════════════════════════════════════════════════


def safety_checks(payload: dict, schema_name: str) -> list[str]:
    """Safety invariants beyond structural validation."""
    errors = []

    # GovernanceDecision / TrustReport: authority_statement must not claim
    # READY authorizes execution
    if schema_name in ("ogap-governance-decision", "ogap-trust-report"):
        decision = payload.get("decision", "")
        decision = str(decision).upper() if not isinstance(decision, str) else decision.upper()
        authority = str(payload.get("authority_statement", "")).lower()

        if decision == "READY":
            dangerous = [
                "authorizes execution",
                "authorizes deployment",
                "approves deployment",
                "approves release",
                "approves merge",
                "approved to",
            ]
            for phrase in dangerous:
                if phrase in authority:
                    errors.append(
                        f"READY-authorizes-execution: authority_statement "
                        f"contains '{phrase}' — READY is evidence, not authorization"
                    )

    # CapabilityManifest: must have authority_note
    if schema_name == "ogap-capability-manifest":
        if "authority_note" not in payload:
            errors.append("CapabilityManifest missing authority_note — must state can_X != may_X")

    return errors


# ═══════════════════════════════════════════════════════════════════════
# Schema inference and CLI
# ═══════════════════════════════════════════════════════════════════════


def load_schema(schema_name: str) -> dict | None:
    path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def infer_schema(payload: dict) -> str | None:
    """Infer schema name from payload shape."""
    if "evidence_bundle" in payload and "claim_id" in payload and "coverage_report" in payload:
        return "ogap-work-claim"
    if "decision" in payload:
        if "report_id" in payload and "debt_summary" in payload:
            return "ogap-trust-report"
        if "decision_id" in payload or "decision_scope" in payload:
            return "ogap-governance-decision"
    if "capabilities" in payload and "adapter_id" in payload:
        return "ogap-capability-manifest"
    if "claimed_universe" in payload and "discovery_method" in payload:
        return "ogap-coverage-report"
    return None


def main() -> int:
    json_output = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]
    schema_override = None

    if "--schema" in args:
        idx = args.index("--schema")
        if idx + 1 < len(args):
            schema_override = args[idx + 1]
            args.pop(idx)
            args.pop(idx)

    if not args:
        print("Usage: validate_ogap_payload.py <file.json> [--schema ogap-work-claim] [--json]")
        return 1

    path = Path(args[0])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1

    # Parse with duplicate key detection
    try:
        payload, dup_errors = load_payload_with_dup_check(path)
    except json.JSONDecodeError as e:
        if json_output:
            print(json.dumps({"valid": False, "errors": [f"invalid JSON: {e}"]}))
        else:
            print(f"❌ Invalid JSON: {e}")
        return 1

    # Infer schema
    schema_name = schema_override or infer_schema(payload)
    if not schema_name:
        msg = "Could not infer OGAP object type — use --schema flag"
        if json_output:
            print(json.dumps({"valid": False, "errors": [msg]}))
        else:
            print(f"❌ {msg}")
        return 1

    schema = load_schema(schema_name)
    if not schema:
        msg = f"Schema not found: {schema_name}"
        if json_output:
            print(json.dumps({"valid": False, "errors": [msg]}))
        else:
            print(f"❌ {msg}")
        return 1

    # Validate
    errors = validate_against_schema(payload, schema)
    safety_errors = safety_checks(payload, schema_name)
    all_errors = dup_errors + errors + safety_errors

    if json_output:
        print(
            json.dumps(
                {
                    "valid": len(all_errors) == 0,
                    "schema": schema_name,
                    "file": str(path),
                    "errors": all_errors,
                    "warnings": [],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"📋 Schema:  {schema_name}")
        print(f"📄 File:    {path.name}")
        for de in dup_errors:
            print(f"  🔑 {de}")
        if not errors:
            req_count = len(schema.get("required", []))
            print(f"✅ Schema:  PASS ({req_count} required fields)")
        else:
            for e in errors:
                print(f"  ❌ {e}")
        if safety_errors:
            for se in safety_errors:
                print(f"  ⚠️  {se}")
        if not all_errors:
            print("✅ All checks pass.")
        else:
            print(f"❌ {len(all_errors)} validation issue(s).")

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
