#!/usr/bin/env python3
"""Validate AOS AIActionDeclaration objects."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/governance/ai-action-declaration.schema.json"
RULES_PATH = ROOT / "docs/governance/schemas/action-conformance-rules.json"

REQUIRED_BOUNDARY_PHRASES = (
    "not authorization",
    "does not prove correctness",
    "does not permit scope expansion",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_known_actions() -> set[str]:
    if not RULES_PATH.exists():
        return set()
    rules = load_json(RULES_PATH)
    return set((rules.get("action_types") or {}).keys())


def validate(filepath: Path) -> tuple[bool, list[str], list[str]]:
    obj = load_json(filepath)
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = [f"SCHEMA: {err.message}" for err in sorted(validator.iter_errors(obj), key=lambda e: e.path)]
    warnings: list[str] = []

    if obj.get("object_kind") != "AIActionDeclaration":
        errors.append(f"INVALID_OBJECT_KIND: {obj.get('object_kind')}")

    for path in obj.get("declared_scope", []):
        if path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"INVALID_DECLARED_SCOPE_PATH: {path}")

    boundary_text = " ".join(obj.get("not_claimed", [])).lower()
    for phrase in REQUIRED_BOUNDARY_PHRASES:
        if phrase not in boundary_text:
            errors.append(f"NOT_CLAIMED_MUST_STATE: {phrase}")

    known_actions = load_known_actions()
    declared_action = obj.get("declared_action")
    if known_actions and declared_action not in known_actions:
        warnings.append(f"REVIEW_REQUIRED: declared_action not in action registry: {declared_action}")

    return len(errors) == 0, errors, warnings


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate-ai-action-declaration.py <object.aos.json>", file=sys.stderr)
        sys.exit(1)

    ok, errors, warnings = validate(Path(sys.argv[1]))
    for warning in warnings:
        print(f"  ! {warning}")
    if ok:
        print("✓ AI action declaration valid")
        sys.exit(0)
    for error in errors:
        print(f"  ✗ {error}")
    sys.exit(1)


if __name__ == "__main__":
    main()
