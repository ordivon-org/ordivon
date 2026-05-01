#!/usr/bin/env python3
"""OGAP-2: Ordivon Governance Adapter Protocol — Payload Validator.

Validates OGAP JSON payloads against draft v0 schemas and safety invariants.

Usage:
    uv run python scripts/validate_ogap_payload.py <file.json>
    uv run python scripts/validate_ogap_payload.py <file.json> --json

Does not call network APIs, mutate files, or authorize action.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "src" / "ordivon_verify" / "schemas"

VALID_DECISIONS = {"READY", "DEGRADED", "BLOCKED", "HOLD", "REJECT", "NO-GO"}


def load_schema(schema_name: str) -> dict | None:
    path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(payload: dict, schema: dict) -> list[str]:
    """Structural validation against JSON Schema. Returns list of errors."""
    errors = []
    required = schema.get("required", [])

    for field in required:
        if field not in payload:
            errors.append(f"missing required field: {field}")
        elif isinstance(payload.get(field), str) and not payload[field].strip():
            errors.append(f"required field is empty: {field}")

    # Enum validation for decision
    props = schema.get("properties", {})
    for prop_name, prop_schema in props.items():
        if "enum" in prop_schema and prop_name in payload:
            value = payload[prop_name]
            if value not in prop_schema["enum"]:
                errors.append(
                    f"invalid {prop_name}: '{value}' (allowed: {prop_schema['enum']})"
                )

    return errors


def safety_checks(payload: dict, schema_name: str) -> list[str]:
    """Safety invariants beyond structural validation."""
    errors = []

    # GovernanceDecision: authority_statement must not claim READY authorizes execution
    if schema_name in ("ogap-governance-decision", "ogap-trust-report"):
        decision = payload.get("decision", "").upper()
        authority = payload.get("authority_statement", "").lower()

        if decision == "READY":
            dangerous = ["authorizes execution", "authorizes deployment", "approves deployment", "approves release", "approves merge", "approved to"]
            for phrase in dangerous:
                if phrase in authority:
                    errors.append(
                        f"READY-authorizes-execution: authority_statement contains '{phrase}' — READY is evidence, not authorization"
                    )

    # CapabilityManifest: must have authority_note
    if schema_name == "ogap-capability-manifest":
        if "authority_note" not in payload:
            errors.append("CapabilityManifest missing authority_note — must state can_X != may_X")

    return errors


def infer_schema(payload: dict) -> str | None:
    """Infer schema name from payload shape."""
    # WorkClaim has claim_id + evidence_bundle
    if "evidence_bundle" in payload and "claim_id" in payload and "coverage_report" in payload:
        return "ogap-work-claim"
    # GovernanceDecision / TrustReport both have "decision"
    if "decision" in payload:
        if "report_id" in payload and "debt_summary" in payload:
            return "ogap-trust-report"
        if "decision_id" in payload or "decision_scope" in payload:
            return "ogap-governance-decision"
    # CapabilityManifest has capabilities + adapter_id
    if "capabilities" in payload and "adapter_id" in payload:
        return "ogap-capability-manifest"
    # CoverageReport has claimed_universe + discovery_method
    if "claimed_universe" in payload and "discovery_method" in payload:
        return "ogap-coverage-report"
    return None


def main() -> int:
    json_output = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]
    schema_override = None

    # Parse --schema flag
    if "--schema" in args:
        idx = args.index("--schema")
        if idx + 1 < len(args):
            schema_override = args[idx + 1]
            args.pop(idx)  # --schema
            args.pop(idx)  # its value

    if not args:
        print("Usage: validate_ogap_payload.py <file.json> [--schema ogap-work-claim] [--json]")
        return 1

    path = Path(args[0])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1

    # Parse payload
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
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
    all_errors = errors + safety_errors

    if json_output:
        print(json.dumps({
            "valid": len(all_errors) == 0,
            "schema": schema_name,
            "file": str(path),
            "errors": all_errors,
            "warnings": [],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"📋 Schema:  {schema_name}")
        print(f"📄 File:    {path.name}")
        if not errors:
            print(f"✅ Schema:  PASS ({len(schema.get('required', []))} required fields)")
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
