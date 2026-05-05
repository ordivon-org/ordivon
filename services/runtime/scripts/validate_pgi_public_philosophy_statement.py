#!/usr/bin/env python3
"""Validate PGI PublicPhilosophyStatement payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "object_type",
    "schema_version",
    "statement_id",
    "surface",
    "statement",
    "personal_origin_disclosed",
    "evidence_boundary",
    "not_advice_boundary",
    "commercialization_boundary",
    "anti_cult_boundary",
    "authority_boundary",
]

VALID_SURFACES = {"about", "blog", "docs", "pitch", "readme", "talk", "website"}
GUARANTEE_RE = re.compile(
    r"guaranteed\s+success|follow\s+this\s+and\s+you\s+will|cure\s+anxiety|financial\s+freedom\s+guaranteed|"
    r"ultimate\s+truth|only\s+way\s+to\s+live",
    re.I,
)


def _nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if payload.get("object_type") != "PGIPublicPhilosophyStatement":
        errors.append("object_type must be PGIPublicPhilosophyStatement")
    if payload.get("surface") not in VALID_SURFACES:
        errors.append(f"surface must be one of {sorted(VALID_SURFACES)}")
    if payload.get("personal_origin_disclosed") is not True:
        errors.append("personal_origin_disclosed must be true")

    for key in (
        "statement_id",
        "statement",
        "evidence_boundary",
        "not_advice_boundary",
        "commercialization_boundary",
        "anti_cult_boundary",
        "authority_boundary",
    ):
        if not _nonempty(payload.get(key)):
            errors.append(f"{key} must be a non-empty string")

    statement = str(payload.get("statement", ""))
    if GUARANTEE_RE.search(statement):
        errors.append("statement must not contain success/therapy/finance/ultimate-truth guarantees")

    evidence = str(payload.get("evidence_boundary", "")).lower()
    if "casebook" not in evidence and "evidence" not in evidence:
        errors.append("evidence_boundary must anchor public philosophy to casebook/evidence")

    advice = str(payload.get("not_advice_boundary", "")).lower()
    for phrase in ("not therapy", "not financial advice", "not life advice"):
        if phrase not in advice:
            errors.append(f"not_advice_boundary must include '{phrase}'")

    commerce = str(payload.get("commercialization_boundary", "")).lower()
    if "externalization" not in commerce or "not origin" not in commerce:
        errors.append("commercialization_boundary must state commercialization is externalization and not origin")

    anti_cult = str(payload.get("anti_cult_boundary", "")).lower()
    if "not a belief system" not in anti_cult and "not a cult" not in anti_cult:
        errors.append("anti_cult_boundary must state this is not a belief system/cult")

    boundary = str(payload.get("authority_boundary", "")).lower()
    if "does not authorize" not in boundary or "not a universal doctrine" not in boundary:
        errors.append("authority_boundary must state this does not authorize action and is not a universal doctrine")

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
        print("Usage: python scripts/validate_pgi_public_philosophy_statement.py <payload.json> [...]")
        return 2
    failed = False
    results = []
    for raw in args:
        path = Path(raw)
        ok, errors = validate_file(path)
        failed = failed or not ok
        results.append({"path": str(path), "valid": ok, "errors": errors})
    print(json.dumps({"tool": "pgi-public-philosophy-statement-validator", "results": results}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
