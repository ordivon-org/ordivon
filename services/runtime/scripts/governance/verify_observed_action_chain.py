#!/usr/bin/env python3
"""Verify sealed AOS ObservedAction hash chains.

This verifier is read-only. A PASS means the supplied observation files are
internally sealed and chain-continuous; it is evidence, not authorization.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

import observe_action


ROOT = Path(__file__).resolve().parents[2]
OBS_SCHEMA = ROOT / "schemas/governance/observed-action.schema.json"
TRUSTED_SYSTEM_PRODUCERS = {
    "scripts/governance/observe_action.py",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def schema_errors(obj: dict) -> list[str]:
    schema = load_json(OBS_SCHEMA)
    validator = Draft202012Validator(schema)
    return [err.message for err in sorted(validator.iter_errors(obj), key=lambda e: e.path)]


def observation_trust_errors(obj: dict) -> list[str]:
    errors: list[str] = []
    if obj.get("origin") != "SYSTEM_OBSERVED":
        errors.append(f"origin_not_system_observed:{obj.get('origin')}")
    if obj.get("created_by") not in TRUSTED_SYSTEM_PRODUCERS:
        errors.append(f"created_by_not_trusted_system:{obj.get('created_by')}")
    if obj.get("source_identity") not in TRUSTED_SYSTEM_PRODUCERS:
        errors.append(f"source_identity_not_trusted_system:{obj.get('source_identity')}")

    collector = (obj.get("provenance") or {}).get("collector")
    if collector not in TRUSTED_SYSTEM_PRODUCERS:
        errors.append(f"collector_not_trusted_system:{collector}")

    for source in obj.get("observation_sources", []):
        lowered = str(source).lower()
        if "ai_written" in lowered or "ai self-report" in lowered or "llm self-report" in lowered:
            errors.append(f"observation_source_untrusted:{source}")
    return errors


def verify_observation(obj: dict) -> list[str]:
    errors = schema_errors(obj)
    errors.extend(observation_trust_errors(obj))

    expected = observe_action.compute_event_hash(obj)
    if obj.get("event_hash") != expected:
        errors.append(f"event_hash_mismatch:expected={expected}:observed={obj.get('event_hash')}")
    return errors


def verify_chain(observations: list[tuple[Path, dict]]) -> list[dict]:
    findings: list[dict] = []
    ordered = sorted(observations, key=lambda item: item[1].get("observed_sequence", 0))
    previous_hash = observe_action.GENESIS_EVENT_HASH
    previous_sequence = 0

    for path, obj in ordered:
        errors = verify_observation(obj)
        sequence = obj.get("observed_sequence")
        if sequence != previous_sequence + 1:
            errors.append(f"observed_sequence_gap:expected={previous_sequence + 1}:observed={sequence}")
        if obj.get("prev_event_hash") != previous_hash:
            errors.append(f"prev_event_hash_mismatch:expected={previous_hash}:observed={obj.get('prev_event_hash')}")

        if errors:
            findings.append({
                "path": str(path),
                "event_id": obj.get("event_id"),
                "event_hash": obj.get("event_hash"),
                "errors": sorted(set(errors)),
            })

        previous_hash = obj.get("event_hash", "")
        previous_sequence = sequence if isinstance(sequence, int) else previous_sequence

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify sealed AOS ObservedAction hash chain")
    parser.add_argument("observed_actions", nargs="+", help="ObservedAction JSON file(s) to verify")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    observations = [(Path(path), load_json(Path(path))) for path in args.observed_actions]
    findings = verify_chain(observations)
    result = {
        "tool": "verify_observed_action_chain",
        "status": "PASS" if not findings else "FAIL",
        "checked_count": len(observations),
        "findings": findings,
        "not_claimed": [
            "Hash-chain verification is evidence, not authorization.",
            "PASS does not authorize merge, deploy, release, policy activation, broker writes, live trading, or external action.",
            "The v0.3-A seal is deterministic hashing, not cryptographic signing or transparency-log attestation.",
        ],
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif findings:
        print(f"FAIL: {len(findings)} observed action file(s) failed seal verification")
        for item in findings:
            print(f"  {item['path']}: {', '.join(item['errors'])}")
    else:
        print(f"PASS: {len(observations)} observed action file(s) verified")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
