"""Bounded, executable refinement check for Artifact required-evidence promotion.

SPEC: successful profile evidence iff every *declared* claim has an explicit
PASS and matching independent native status witness. The claim record itself
is never a native witness.

MODEL: full Cartesian product of six abstract claim states over the real
FLAC/WAVE/PNG required-evidence key sets (7/5/4 claims respectively).

REFINEMENT: execute the production assess_required_evidence implementation
on every generated model state and compare its complete/status projection with
the separately written specification oracle. No external validators or I/O
effects are included. This is exhaustive only for the finite abstraction, NOT
a universal proof of arbitrary JSON, native decoders or deployed behavior.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifact_verification.claim_coverage import assess_required_evidence  # noqa: E402

PROFILES = (
    "audio-flac-pcm16-r1",
    "audio-wave-pcm16-r1",
    "still-image-png-srgb-r1",
)
STATES = ("MISSING", "UNKNOWN", "FAIL", "PASS", "SELF", "MISMATCH")


def make_native(names: list[str], states: tuple[str, ...]) -> dict:
    """One concrete representative per abstract claim state."""
    observed: dict[str, dict[str, str]] = {}
    claims: dict[str, dict] = {}
    for name, state in zip(names, states, strict=True):
        if state == "MISSING":
            continue
        if state == "UNKNOWN":
            claims[name] = {"status": "NOT_EVALUATED", "nativePointers": []}
            continue
        if state == "FAIL":
            status = "FAIL"
            observed[name] = {"status": status}
            claims[name] = {
                "status": status,
                "nativePointers": [f"/observed/{name}"],
            }
            continue
        if state == "PASS":
            observed[name] = {"status": "PASS"}
            claims[name] = {
                "status": "PASS",
                "nativePointers": [f"/observed/{name}"],
            }
            continue
        if state == "SELF":
            claims[name] = {
                "status": "PASS",
                "nativePointers": [f"/claimResults/{name}"],
            }
            continue
        if state == "MISMATCH":
            observed[name] = {"status": "FAIL"}
            claims[name] = {
                "status": "PASS",
                "nativePointers": [f"/observed/{name}"],
            }
            continue
        raise AssertionError(f"unmodeled state: {state}")
    return {"status": "PASS", "claimResults": claims, "observed": observed}


def check_profile(profile_id: str) -> dict:
    profile_path = (
        ROOT / "artifact-delivery/shadow-v2/examples" / (profile_id + "-v2.json")
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    names = sorted(profile["requiredEvidence"])
    checked = 0
    accepted = 0
    for vector in itertools.product(STATES, repeat=len(names)):
        native = make_native(names, vector)
        result = assess_required_evidence(profile, native)
        spec_accept = all(state == "PASS" for state in vector)
        if result["complete"] != spec_accept:
            raise AssertionError(
                f"refinement violation {profile_id} {dict(zip(names, vector, strict=True))}: "
                f"spec_accept={spec_accept}, implementation={result}"
            )
        if (result["status"] == "COMPLETE") != spec_accept:
            raise AssertionError(
                f"status refinement violation {profile_id}: {vector}: {result}"
            )
        if sorted(result["expectedClaims"]) != names:
            raise AssertionError("canonical profile claim-set drift")
        if spec_accept:
            accepted += 1
        checked += 1

    # Non-vacuity: exactly one all-PASS model state is accepted.
    assert accepted == 1, (profile_id, accepted)

    # Schema narrowing/unknown must never accidentally establish success.
    good = make_native(names, ("PASS",) * len(names))
    good["claimResults"]["undeclared"] = {
        "status": "PASS",
        "nativePointers": ["/observed/" + names[0]],
    }
    assert not assess_required_evidence(profile, good)["complete"]
    assert not assess_required_evidence(profile, {"status": "PASS"})["complete"]
    assert not assess_required_evidence({"requiredEvidence": {}}, good)["complete"]

    return {
        "profileId": profile_id,
        "abstractStates": list(STATES),
        "requiredClaims": names,
        "modelStatesExhaustivelyChecked": checked,
        "acceptedStates": accepted,
        "profileSha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    path = ROOT / "artifact_verification/claim_coverage.py"
    rows = [check_profile(profile_id) for profile_id in PROFILES]
    summary = {
        "method": "exhaustive finite abstract state model + source refinement",
        "sourceSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "scope": (
            "Explicit claim status and independent native pointer consistency "
            "in six representative states per required claim; not proof of "
            "arbitrary inputs, target applications, or native validators"
        ),
        "totalStates": sum(row["modelStatesExhaustivelyChecked"] for row in rows),
        "counterexamples": 0,
        "models": rows,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    assert summary["totalStates"] > 100000, "vacuous state-space reduction"


if __name__ == "__main__":
    main()
