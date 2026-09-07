#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASELINE = "8ebc23144ed5b49d685cc32ac11428bbddf64d2f"
ROOT = Path(__file__).resolve().parents[1]
F22 = ROOT / "contracts" / "F22_TELEMETRY_EVIDENCE_CONTRACT_R1.json"
F24 = ROOT / "contracts" / "F24_PLAYER_EVIDENCE_CONTRACT_R1.json"
REQUIRED_HUMAN_UNKNOWN = {
    "fun",
    "immersion",
    "believability",
    "detectability",
    "cueUsefulness",
    "fairness",
    "comprehension",
}
REQUIRED_EVENTS = {
    "session_started",
    "cue_exposed",
    "creature_state_changed",
    "evade_started",
    "reacquisition_opportunity",
    "observe_action_started",
    "observation_committed",
    "success_consequence",
}
FORBIDDEN_IDENTIFIER_KEYS = {
    "participantName",
    "realName",
    "email",
    "phone",
    "address",
    "ipAddress",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contracts() -> list[str]:
    errors: list[str] = []
    f22 = load(F22)
    f24 = load(F24)
    if f22.get("baseline") != BASELINE or f24.get("baseline") != BASELINE:
        errors.append("baseline_mismatch")
    events = {row["id"] for row in f22.get("eventTypes", [])}
    missing_events = REQUIRED_EVENTS - events
    if missing_events:
        errors.append(f"missing_required_events:{sorted(missing_events)}")
    envelope_required = set(f22.get("eventEnvelope", {}).get("required", []))
    for field in ["runId", "sequence", "monotonicTimeMs", "sourceRevision", "buildId", "conditionId", "accessibilityConditionId", "sourceFront", "producerSemanticId"]:
        if field not in envelope_required:
            errors.append(f"missing_envelope_field:{field}")
    claims = f22.get("humanClaims", {})
    if set(claims) != REQUIRED_HUMAN_UNKNOWN or any(value != "UNKNOWN" for value in claims.values()):
        errors.append("f22_human_claim_guard_failed")
    f24_claims = f24.get("humanClaimsBeforeExecution", {})
    if set(f24_claims) != REQUIRED_HUMAN_UNKNOWN or any(value != "UNKNOWN" for value in f24_claims.values()):
        errors.append("f24_human_claim_guard_failed")
    if not f24.get("claimSpecificQuestions"):
        errors.append("missing_claim_specific_questions")
    if not f24.get("conditionFreeze", {}).get("mustRecordBeforeExposure"):
        errors.append("missing_condition_freeze")
    if not f24.get("decisionRules"):
        errors.append("missing_decision_rules")
    prohibited = set(f22.get("privacyAndHumanBoundary", {}).get("prohibitedExamples", []))
    if not FORBIDDEN_IDENTIFIER_KEYS.issubset(prohibited):
        errors.append("privacy_guard_missing_keys")
    for binding in f22.get("upstreamBindings", []):
        if binding.get("producer") in {"A01/F01", "A02/F02"} and not binding.get("revalidated"):
            errors.append(f"unrevalidated_upstream:{binding.get('producer')}")
    return errors


def validate_evidence(event_path: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    manifest = load(manifest_path)
    raw_digest = sha256(event_path)
    if manifest.get("eventFileSha256") != raw_digest:
        errors.append("manifest_digest_mismatch")
    rows = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if manifest.get("eventCount") != len(rows):
        errors.append("manifest_event_count_mismatch")
    previous_time = -1
    frozen = None
    for idx, row in enumerate(rows, 1):
        if row.get("sequence") != idx:
            errors.append(f"sequence_gap:{idx}")
        if row.get("eventId") != f"{row.get('runId')}:{idx}":
            errors.append(f"event_id_mismatch:{idx}")
        if row.get("monotonicTimeMs", -1) < previous_time:
            errors.append(f"monotonic_regression:{idx}")
        previous_time = row.get("monotonicTimeMs", previous_time)
        current_frozen = tuple(row.get(key) for key in ["runId", "sourceRevision", "buildId", "conditionId", "accessibilityConditionId"])
        if frozen is None:
            frozen = current_frozen
        elif frozen != current_frozen:
            errors.append(f"frozen_condition_drift:{idx}")
        encoded = json.dumps(row, sort_keys=True)
        for key in FORBIDDEN_IDENTIFIER_KEYS:
            if f'"{key}"' in encoded:
                errors.append(f"forbidden_identifier:{key}:{idx}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    errors = validate_contracts()
    if bool(args.events) != bool(args.manifest):
        errors.append("events_and_manifest_must_be_supplied_together")
    if args.events and args.manifest:
        errors.extend(validate_evidence(args.events, args.manifest))
    if errors:
        print("VEILWILD_A21_EVIDENCE_CONTRACT_FAIL")
        for error in errors:
            print(error)
        return 1
    print("VEILWILD_A21_EVIDENCE_CONTRACT_VALID")
    print(f"f22_sha256={sha256(F22)}")
    print(f"f24_sha256={sha256(F24)}")
    if args.events and args.manifest:
        print(f"events_sha256={sha256(args.events)}")
        print(f"manifest_sha256={sha256(args.manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
