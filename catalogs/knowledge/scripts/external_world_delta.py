#!/usr/bin/env python3
"""Bounded external-world Claim/Evidence/Delta projection, not domain truth.

Reads an owner-review observation and emits an idempotent, non-authoritative
delta proposal. No network access, installation, database, or promotion.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

KIND = "ordivon.external-world-observation-r1"
STATES = {"ISSUER_REPORTED", "SINGLE_PARTY_CLAIM", "PRELIMINARY"}
ERROR = "UNVERIFIED_SOURCE_CONTENT"


def _day(value: object, field: str, errors: list[str]) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(field + ": expected ISO calendar day or null")
        return None
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError("non-canonical date")
        return parsed
    except ValueError:
        errors.append(field + ": invalid ISO calendar day")
        return None


def _number(value: object, field: str, errors: list[str]) -> Decimal | None:
    if not isinstance(value, str):
        errors.append(field + ": decimal must be a string")
        return None
    try:
        num = Decimal(value)
        if not num.is_finite():
            raise InvalidOperation
        return num
    except InvalidOperation:
        errors.append(field + ": invalid finite decimal")
        return None


def _source(source: object, field: str, errors: list[str]) -> date | None:
    if not isinstance(source, dict):
        errors.append(field + ": source evidence missing")
        return None
    url = source.get("url")
    if not isinstance(url, str):
        errors.append(field + ": source URL absent")
        return None
    p = urlparse(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        errors.append(field + ": HTTPS source URL required")
    if not source.get("publisher") or not source.get("supportScope"):
        errors.append(field + ": publisher and direct support scope required")
    return _day(source.get("publishedAt"), field + ".publishedAt", errors)


def examine(packet: object) -> tuple[list[str], dict | None]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be an object"], None
    if packet.get("kind") != KIND:
        errors.append("invalid kind")
    identity = packet.get("observationId")
    if not isinstance(identity, str) or not identity or len(identity) > 160:
        errors.append("observationId required (<=160 chars)")
    if packet.get("claimStatus") not in STATES:
        errors.append("claimStatus must preserve source/confirmation distinction")
    if packet.get("ownerVerdict") != "UNKNOWN" or packet.get("productionApplied") is not False:
        errors.append("catalog intake cannot issue owner acceptance or production effects")

    current = packet.get("current")
    baseline = packet.get("baseline")
    if not isinstance(current, dict) or not isinstance(baseline, dict):
        return errors + ["current and baseline must be objects"], None
    for key in ("subject", "predicate", "unit"):
        if not current.get(key) or current.get(key) != baseline.get(key):
            errors.append("missing or mismatched baseline/current " + key)
    value_kind = current.get("valueType", "numeric")
    if value_kind not in ("numeric", "state") or baseline.get("valueType", "numeric") != value_kind:
        errors.append("unsupported or mismatched valueType")
    if value_kind == "numeric":
        old = _number(baseline.get("value"), "baseline.value", errors)
        new = _number(current.get("value"), "current.value", errors)
        declared = _number(packet.get("declaredDelta"), "declaredDelta", errors)
    else:
        old = baseline.get("value")
        new = current.get("value")
        declared = None
        if not all(isinstance(v, str) and 0 < len(v) <= 200 for v in (old, new)):
            errors.append("state values must be short non-empty strings")
        if packet.get("declaredDelta") is not None:
            errors.append("state changes cannot assert arithmetic deltas")

    checked = _day(packet.get("checkedAt"), "checkedAt", errors)
    previous_at = _day(baseline.get("dataAsOf"), "baseline.dataAsOf", errors)
    event_at = _day(current.get("eventAt"), "current.eventAt", errors)
    reported_at = _day(current.get("reportedAt"), "current.reportedAt", errors)
    data_as_of = _day(current.get("dataAsOf"), "current.dataAsOf", errors)
    revised_at = _day(current.get("revisedAt"), "current.revisedAt", errors)
    if not (checked and reported_at and data_as_of and previous_at):
        errors.append("known checkedAt, reportedAt, current/baseline dataAsOf required")
    if previous_at and data_as_of and previous_at >= data_as_of:
        errors.append("baseline must precede current observation")
    if event_at and reported_at and event_at > reported_at:
        errors.append("eventAt cannot follow reportedAt")
    if reported_at and checked and reported_at > checked:
        errors.append("reportedAt exceeds checkedAt")
    if data_as_of and checked and data_as_of > checked:
        errors.append("dataAsOf exceeds checkedAt")
    if revised_at and checked and reported_at and not (reported_at <= revised_at <= checked):
        errors.append("revisedAt must lie between reportedAt and checkedAt")

    baseline_published = _source(baseline.get("evidence"), "baseline.evidence", errors)
    current_published = _source(current.get("evidence"), "current.evidence", errors)
    if checked and any(published and published > checked for published in
                       (baseline_published, current_published)):
        errors.append("evidence publication cannot follow checkedAt")
    if value_kind == "numeric" and old is not None and new is not None and declared is not None and new - old != declared:
        errors.append("declaredDelta does not equal current minus baseline")

    affected = packet.get("affectedConsumers")
    if not isinstance(affected, list):
        errors.append("affectedConsumers must be a list, empty if not proven")
    else:
        for item in affected:
            if not isinstance(item, dict) or not item.get("owner") or not item.get("consumerRef"):
                errors.append("consumer impact requires concrete owner and consumerRef")
            elif item.get("acceptance") not in ("UNKNOWN", "OWNER_REVIEW_REQUIRED"):
                errors.append("catalog cannot assert consumer acceptance")

    if errors:
        return errors, None
    assert old is not None and new is not None
    if value_kind == "numeric":
        assert declared is not None
    fingerprint = hashlib.sha256(json.dumps(packet, sort_keys=True, separators=(",", ":"),
                                            ensure_ascii=False).encode("utf-8")).hexdigest()
    projection = {
        "kind": "ordivon.external-world-delta-proposal-r1",
        "observationId": identity,
        "sourcePacketDigest": "sha256:" + fingerprint,
        "claimStatus": packet["claimStatus"],
        "subject": current["subject"],
        "predicate": current["predicate"],
        "baselineValue": str(old),
        "currentValue": str(new),
        "unit": current["unit"],
        "valueType": value_kind,
        "changeKind": ("NUMERIC_DIFFERENCE" if value_kind == "numeric" else
                       ("STATE_CHANGED" if old != new else "STATE_UNCHANGED")),
        "valueChange": str(new - old) if value_kind == "numeric" else None,
        "basisPointChange": (str((new - old) * 100)
                             if value_kind == "numeric" and current["unit"] == "percent" else None),
        "baselineDataAsOf": baseline["dataAsOf"],
        "currentDataAsOf": current["dataAsOf"],
        "eventAt": current.get("eventAt"),
        "reportedAt": current["reportedAt"],
        "checkedAt": packet["checkedAt"],
        "affectedConsumers": affected,
        "knowledgeVerdict": "OWNER_REVIEW_REQUIRED",
        "domainAcceptanceEstablished": False,
        "sourceContentVerifiedByThisProgram": False,
        "productionApplied": False,
        "nonClaim": "Metadata and typed comparison checked only; source contents and downstream domain truth require independent confirmation.",
    }
    return [], projection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path, help="Write a disposable projection (default stdout)")
    args = parser.parse_args()
    try:
        record = json.loads(args.packet.read_text(encoding="utf-8"))
        errors, projection = examine(record)
    except (OSError, ValueError) as exc:
        errors, projection = [str(exc)], None
    if errors:
        print(json.dumps({"standing": "REJECTED", "errors": errors}, indent=2))
        return 1
    payload = json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
