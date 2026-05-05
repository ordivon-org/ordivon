#!/usr/bin/env python3
"""Validate PGI ExternalizationAlignment payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "alignment_id",
    "external_wedge",
    "internal_root_preserved",
    "external_claim",
    "casebook_refs",
    "schema_public_claim",
    "adapter_public_claim",
    "release_claim",
    "trust_boundary",
    "companion_boundary",
    "authority_boundary",
]

VALID_WEDGES = {"alpha_0_agent_work_trust_audit", "verify_cli", "casebook_demo", "none"}
FORBIDDEN_CLAIMS_RE = re.compile(r"public\s+standard|platform\s+launched|sdk\s+available|mcp\s+server|adapter\s+released", re.I)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_of_strings(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIExternalizationAlignment":
        errors.append("object_type must be PGIExternalizationAlignment")
    if payload.get("external_wedge") not in VALID_WEDGES:
        errors.append(f"external_wedge must be one of {sorted(VALID_WEDGES)}")
    if payload.get("internal_root_preserved") is not True:
        errors.append("internal_root_preserved must be true")

    for key in (
        "alignment_id",
        "external_claim",
        "trust_boundary",
        "companion_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")
    if not _list_of_strings(payload.get("casebook_refs")):
        errors.append("casebook_refs must be a non-empty list of strings")

    for key in ("schema_public_claim", "adapter_public_claim", "release_claim"):
        if not isinstance(payload.get(key), bool):
            errors.append(f"{key} must be boolean")
        if payload.get(key) is not False:
            errors.append(f"{key} must remain false in PGI-3.08")

    combined = " ".join(
        str(payload.get(key, ""))
        for key in ("external_claim", "trust_boundary", "companion_boundary", "authority_boundary")
    )
    if FORBIDDEN_CLAIMS_RE.search(combined):
        errors.append("externalization alignment must not claim public standard/platform/SDK/MCP/adapter release")

    claim = str(payload.get("external_claim", "")).lower()
    if "trust audit" not in claim and "governed work" not in claim:
        errors.append("external_claim must stay anchored to trust audit or governed work")

    companion = str(payload.get("companion_boundary", "")).lower()
    if "companion governance" not in companion or "commercialization is externalization" not in companion:
        errors.append("companion_boundary must preserve companion governance root and commercialization-as-externalization")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not release approval" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not release approval")

    return errors


def validate_file(path: Path) -> tuple[bool, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"invalid JSON: {e}"]
    errors = validate_payload(payload)
    return not errors, errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: python scripts/validate_pgi_externalization_alignment.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-externalization-alignment-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
