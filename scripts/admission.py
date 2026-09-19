#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from bound_refs import effect_authority_ref, occurrence_ref, provider_observation_ref
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"

class AdmissionError(ValueError):
    pass

def _schema(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text())

def _validate(name: str, value: object) -> None:
    validator = Draft202012Validator(_schema(name), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = ".".join(str(x) for x in first.absolute_path) or "$"
        raise AdmissionError(f"{name} validation failed at {path}: {first.message}")

def _instant(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise AdmissionError("timestamp must include timezone")
    return value.astimezone(UTC)

def _check_window(start: str, end: str, now: datetime, label: str) -> None:
    starts = _instant(start)
    ends = _instant(end)
    if ends <= starts:
        raise AdmissionError(f"{label} validity window is empty or reversed")
    if now < starts:
        raise AdmissionError(f"{label} is not yet valid")
    if now > ends:
        raise AdmissionError(f"{label} is expired")

def normalize(envelope: dict, now: datetime | None = None) -> dict:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    if set(envelope) != {"schemaVersion", "intent", "providerObservation", "effectAuthority"}:
        raise AdmissionError("admission envelope has unexpected or missing top-level fields")
    if envelope.get("schemaVersion") != 2:
        raise AdmissionError("admission envelope schemaVersion must be 2")
    intent = envelope["intent"]
    provider = envelope["providerObservation"]
    authority = envelope["effectAuthority"]
    _validate("distribution-intent.schema.json", intent)
    _validate("provider-observation.schema.json", provider)
    if authority is not None:
        _validate("effect-authority.schema.json", authority)
    computed_occurrence = occurrence_ref(intent)
    if intent["occurrenceRef"] != computed_occurrence:
        raise AdmissionError("occurrenceRef does not match exact intent")
    if provider["observationRef"] != provider_observation_ref(provider):
        raise AdmissionError("provider observation digest mismatch")
    bindings = {
        "occurrenceRef": intent["occurrenceRef"],
        "provider": intent["carrier"]["provider"],
        "accountRef": intent["carrier"]["accountRef"],
        "adapter": intent["carrier"]["adapter"],
        "effectName": intent["effect"]["name"],
    }
    for field, expected in bindings.items():
        if provider[field] != expected:
            raise AdmissionError(f"provider observation {field} is not bound to intent")
    _check_window(provider["observedAt"], provider["validUntil"], now, "provider observation")
    granted = False
    authority_ref = None
    if authority is not None:
        if authority["authorityRef"] != effect_authority_ref(authority):
            raise AdmissionError("effect authority digest mismatch")
        authority_bindings = {
            "occurrenceRef": intent["occurrenceRef"],
            "provider": intent["carrier"]["provider"],
            "accountRef": intent["carrier"]["accountRef"],
            "effectName": intent["effect"]["name"],
        }
        for field, expected in authority_bindings.items():
            if authority[field] != expected:
                raise AdmissionError(f"effect authority {field} is not bound to intent")
        _check_window(authority["issuedAt"], authority["validUntil"], now, "effect authority")
        granted = authority["decision"] == "grant"
        authority_ref = authority["authorityRef"]
    return {
        "schemaVersion": 2,
        "intent": {
            "intentId": intent["intentId"], "occurrenceRef": intent["occurrenceRef"],
            "provider": intent["carrier"]["provider"], "accountRef": intent["carrier"]["accountRef"],
            "adapter": intent["carrier"]["adapter"], "effectName": intent["effect"]["name"],
            "artifact": intent.get("artifact"),
        },
        "provider": {
            "observationRef": provider["observationRef"], "effectName": provider["effectName"],
            "effectMode": provider["effectMode"], "effectSupported": provider["effectSupported"],
            "executionMode": provider["executionMode"], "missingProviderRequirements": provider["missingProviderRequirements"],
            "missingInteractions": provider["missingInteractions"], "sourceKind": provider["sourceKind"],
            "sourceRef": provider["sourceRef"]
        },
        "authority": {"present": authority is not None, "authorityRef": authority_ref, "granted": granted},
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("normalize", "verify"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--now")
    args = parser.parse_args()
    try:
        envelope = json.loads(args.path.read_text())
        now = _instant(args.now) if args.now else None
        normalized = normalize(envelope, now)
    except (AdmissionError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ADMISSION_DENY: {exc}", file=sys.stderr)
        return 1
    if args.mode == "normalize":
        json.dump(normalized, sys.stdout, sort_keys=True, separators=(",", ":"))
        sys.stdout.write("\n")
    else:
        print("ADMISSION_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
