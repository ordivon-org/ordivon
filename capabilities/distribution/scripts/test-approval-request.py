#!/usr/bin/env python
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from bound_refs import effect_payload_ref, occurrence_ref
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
REQUEST_SCHEMA = json.loads((ROOT / "contracts/effect-approval-request.schema.json").read_text())
AUTHORITY_SCHEMA = json.loads((ROOT / "contracts/effect-authority.schema.json").read_text())
INTENT = json.loads((ROOT / "evidence/r3-github-create-issue-intent.json").read_text())
REQUEST = json.loads((ROOT / "evidence/r4-github-create-issue-approval-request.json").read_text())


def main() -> int:
    errors = list(Draft202012Validator(REQUEST_SCHEMA, format_checker=FormatChecker()).iter_errors(REQUEST))
    if errors:
        raise AssertionError(errors[0].message)
    if REQUEST["occurrenceRef"] != occurrence_ref(INTENT):
        raise AssertionError("approval request occurrence mismatch")
    if REQUEST["effectPayloadRef"] != effect_payload_ref(INTENT):
        raise AssertionError("approval request payload mismatch")
    if not list(Draft202012Validator(AUTHORITY_SCHEMA, format_checker=FormatChecker()).iter_errors(REQUEST)):
        raise AssertionError("approval request must never validate as effect authority")
    swapped = deepcopy(INTENT)
    swapped["effect"]["payload"]["title"] += " changed"
    swapped["occurrenceRef"] = occurrence_ref(swapped)
    if occurrence_ref(swapped) == REQUEST["occurrenceRef"]:
        raise AssertionError("payload swap did not change occurrence")
    if effect_payload_ref(swapped) == REQUEST["effectPayloadRef"]:
        raise AssertionError("payload swap did not change payload ref")
    print("PASS exact approval request binds occurrence and payload")
    print("PASS approval request is structurally non-authoritative")
    print("PASS payload mutation invalidates approval request identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
