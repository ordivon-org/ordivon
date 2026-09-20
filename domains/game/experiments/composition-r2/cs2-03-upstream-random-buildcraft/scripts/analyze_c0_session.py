#!/usr/bin/env python3
"""Validate one exported CS2-03 Human C0 session.

This script intentionally does not estimate a condition effect. C0 is an apparatus
canary only; ratings and strategy text are preserved but never promoted to a
mechanism claim here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DESIGN = json.loads((HERE / "design.json").read_text())
PROTOCOL = json.loads((HERE / "human" / "c0-protocol-r1.json").read_text())


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_json", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    session = json.loads(args.session_json.read_text())
    defects: list[str] = []

    if not isinstance(session.get("sessionId"), str) or not session["sessionId"]:
        defects.append("missing_session_id")
    schedule = session.get("schedule")
    if schedule not in DESIGN["schedules"]:
        defects.append("unknown_schedule")
    runs = session.get("runs")
    if not isinstance(runs, list) or len(runs) != 4:
        defects.append("run_count_not_4")
        runs = runs if isinstance(runs, list) else []

    expected_conditions = DESIGN["schedules"].get(schedule, [])
    observed_conditions = []
    for i, run in enumerate(runs):
        observed_conditions.append(run.get("condition"))
        if i < len(expected_conditions) and run.get("condition") != expected_conditions[i]:
            defects.append(f"run_{i+1}_condition_schedule_mismatch")
        expected_seq = DESIGN["humanSequences"][i] if i < len(DESIGN["humanSequences"]) else None
        if expected_seq is not None and run.get("sequence") != expected_seq:
            defects.append(f"run_{i+1}_sequence_mismatch")
        rounds = run.get("rounds")
        if not isinstance(rounds, list) or len(rounds) != 4:
            defects.append(f"run_{i+1}_round_count_not_4")
            continue
        for j, rec in enumerate(rounds):
            if rec.get("round") != j + 1:
                defects.append(f"run_{i+1}_round_{j+1}_index_mismatch")
            cond = run.get("condition")
            should_visible = cond == "UPSTREAM"
            if rec.get("encounterVisibleBeforeChoice") is not should_visible:
                defects.append(f"run_{i+1}_round_{j+1}_visibility_flag_mismatch")
            offer = DESIGN["offers"][j]
            if rec.get("offer") != offer:
                defects.append(f"run_{i+1}_round_{j+1}_offer_mismatch")
            if rec.get("choice") not in offer:
                defects.append(f"run_{i+1}_round_{j+1}_illegal_choice")
        survey = run.get("survey")
        if not isinstance(survey, dict):
            defects.append(f"run_{i+1}_missing_survey")
        else:
            for key in ["choiceAttribution", "adaptation", "causalUnderstanding", "voluntaryRetry"]:
                value = survey.get(key)
                if not isinstance(value, (int, float)) or not (1 <= value <= 7):
                    defects.append(f"run_{i+1}_{key}_invalid")
            if not isinstance(survey.get("strategyRevision"), str):
                defects.append(f"run_{i+1}_strategyRevision_missing")

    if sorted(observed_conditions) != ["DOWNSTREAM", "DOWNSTREAM", "UPSTREAM", "UPSTREAM"]:
        defects.append("conditions_not_two_each")
    if not session.get("startedAt") or not session.get("finishedAt"):
        defects.append("missing_session_timestamps")

    structural_complete = not defects
    receipt = {
        "schemaVersion": 1,
        "kind": "cs2-03-human-c0-session-validation",
        "protocol": PROTOCOL["id"],
        "candidate": PROTOCOL["candidate"],
        "sessionId": session.get("sessionId"),
        "schedule": schedule,
        "sourceSession": str(args.session_json),
        "sourceSessionDigest": sha256(args.session_json),
        "apparatusStructureComplete": structural_complete,
        "structuralDefects": defects,
        "c0Standing": "STRUCTURALLY_ADMISSIBLE_AWAITING_HUMAN_APPARATUS_NOTES" if structural_complete else "FAIL_SESSION_OR_APPARATUS_STRUCTURE",
        "humanMechanismStanding": "UNASSESSED_C0_ONLY",
        "conditionEffectStanding": "NOT_ASSESSED_AT_C0",
        "productStanding": "NOT_AUTHORIZED",
        "g0": False,
        "boundary": "This validator checks session completeness and experimental-condition integrity only. It does not interpret ratings, text, fun, strategy value, or condition superiority."
    }
    out = args.out or args.session_json.with_name(args.session_json.stem + "-c0-validation.json")
    out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    raise SystemExit(0 if structural_complete else 2)


if __name__ == "__main__":
    main()
