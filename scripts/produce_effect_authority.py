#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from bound_refs import effect_authority_ref, occurrence_ref
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
APPROVAL_SCHEMA = json.loads((ROOT / "contracts/effect-approval.schema.json").read_text())


class AuthorityProducerError(ValueError):
    pass


def _instant(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise AuthorityProducerError("timestamp must include timezone")
    return value.astimezone(UTC)


def _bound_input(relative: str) -> Path:
    root_text = os.environ.get("ORDIVON_INPUT_ROOT")
    if not root_text:
        raise AuthorityProducerError("ORDIVON_INPUT_ROOT is required; approval must arrive through Runtime execBound")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise AuthorityProducerError("approval path must be a normal relative path")
    path = Path(root_text).joinpath(*rel.parts)
    if not path.is_file() or path.is_symlink():
        raise AuthorityProducerError("approval input must be one regular Runtime-bound file")
    return path


def produce(intent: dict, approval: dict, *, now: datetime) -> dict:
    errors = sorted(
        Draft202012Validator(APPROVAL_SCHEMA, format_checker=FormatChecker()).iter_errors(approval),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        raise AuthorityProducerError(f"approval schema invalid: {errors[0].message}")
    actual_occurrence = occurrence_ref(intent)
    if intent.get("occurrenceRef") != actual_occurrence:
        raise AuthorityProducerError("intent occurrenceRef mismatch")
    if approval["occurrenceRef"] != actual_occurrence:
        raise AuthorityProducerError("approval is not bound to this exact occurrence")
    issued = _instant(approval["issuedAt"])
    expires = _instant(approval["validUntil"])
    if expires <= issued or now < issued or now > expires:
        raise AuthorityProducerError("approval is outside its validity window")
    authority = {
        "schemaVersion": 2,
        "authorityRef": "sha256:" + "0" * 64,
        "occurrenceRef": actual_occurrence,
        "principalRef": approval["principalRef"],
        "provider": intent["carrier"]["provider"],
        "accountRef": intent["carrier"]["accountRef"],
        "effectName": intent["effect"]["name"],
        "decision": approval["decision"],
        "issuedAt": approval["issuedAt"],
        "validUntil": approval["validUntil"],
        "sourceRef": f"approval:{approval['approvalId']}:{approval['sourceRef']}",
    }
    authority["authorityRef"] = effect_authority_ref(authority)
    return authority


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--approval-input", required=True)
    parser.add_argument("--now")
    args = parser.parse_args()
    try:
        intent = json.loads(args.intent.read_text())
        if "intent" in intent:
            intent = intent["intent"]
        approval = json.loads(_bound_input(args.approval_input).read_text())
        now = _instant(args.now) if args.now else datetime.now(UTC)
        authority = produce(intent, approval, now=now)
    except (AuthorityProducerError, KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
        print(f"EFFECT_AUTHORITY_DENY: {exc}", file=sys.stderr)
        return 1
    json.dump(authority, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
