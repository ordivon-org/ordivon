#!/usr/bin/env python3
"""Validate PGI ExtendedMindTool records."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "tool_id",
    "tool_class",
    "cognitive_role",
    "data_boundary",
    "failure_modes",
    "governance_surface",
    "human_retains",
    "replacement_claim_present",
    "authority_boundary",
]

VALID_CLASSES = {
    "ai_assistant",
    "ci",
    "editor",
    "git",
    "knowledge_base",
    "notebook",
    "terminal",
    "validator",
}
VALID_SURFACES = {"claim", "decision", "evidence", "memory", "review", "rule", "tooling"}
REPLACE_RE = re.compile(r"replaces\s+judgment|decides\s+for\s+the\s+human|source\s+of\s+truth\s+by\s+itself", re.I)


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

    if payload.get("object_type") != "PGIExtendedMindTool":
        errors.append("object_type must be PGIExtendedMindTool")
    if payload.get("tool_class") not in VALID_CLASSES:
        errors.append(f"tool_class must be one of {sorted(VALID_CLASSES)}")
    if payload.get("governance_surface") not in VALID_SURFACES:
        errors.append(f"governance_surface must be one of {sorted(VALID_SURFACES)}")

    for key in ("tool_id", "cognitive_role", "data_boundary", "human_retains", "authority_boundary"):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")
    if not _list_of_strings(payload.get("failure_modes")):
        errors.append("failure_modes must be a non-empty list of strings")
    if not isinstance(payload.get("replacement_claim_present"), bool):
        errors.append("replacement_claim_present must be boolean")

    combined = " ".join(
        [str(payload.get("cognitive_role", "")), str(payload.get("human_retains", ""))]
        + list(payload.get("failure_modes", []))
    )
    if payload.get("replacement_claim_present") is not False:
        errors.append("replacement_claim_present must remain false")
    if REPLACE_RE.search(combined):
        errors.append("tool map must not claim the tool replaces human judgment or source-of-truth review")

    data_boundary = str(payload.get("data_boundary", "")).lower()
    if "privacy" not in data_boundary and "local" not in data_boundary and "redacted" not in data_boundary:
        errors.append("data_boundary must state privacy, local, or redacted handling")

    human = str(payload.get("human_retains", "")).lower()
    if "judgment" not in human or "decision" not in human:
        errors.append("human_retains must preserve human judgment and decision responsibility")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "tool is not authority" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and tool is not authority")

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
        print("Usage: python scripts/validate_pgi_extended_mind_tool.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-extended-mind-tool-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
