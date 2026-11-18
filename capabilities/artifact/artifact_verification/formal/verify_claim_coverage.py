"""Bounded, executable refinement check for Artifact required-evidence promotion.

SPEC: successful profile evidence iff every mandatory (required=True) claim
has an explicit PASS and matching native status witness. Optional claims do not
strengthen the mandatory gate; malformed/all-optional declarations fail closed.
The claim record itself is never a native witness.

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
from artifact_verification.claim_coverage import (  # noqa: E402
    assess_required_evidence,
    assess_required_statuses,
)

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

    # Optional declarations must not strengthen required gates. Missing and
    # failing optional observations are still visible in native raw evidence.
    mixed = {"requiredEvidence": {
        "mandatory": {"required": True}, "optional": {"required": False}
    }}
    mixed_native = {
        "status": "PASS",
        "observed": {"mandatory": {"status": "PASS"}},
        "claimResults": {"mandatory": {
            "status": "PASS", "nativePointers": ["/observed/mandatory"]
        }},
    }
    assessed = assess_required_evidence(mixed, mixed_native)
    assert assessed["complete"] and assessed["expectedClaims"] == ["mandatory"]
    mixed_native["claimResults"]["optional"] = {"status": "FAIL"}
    assert assess_required_evidence(mixed, mixed_native)["complete"]
    mixed_native["claimResults"]["undeclared"] = {"status": "PASS"}
    assert not assess_required_evidence(mixed, mixed_native)["complete"]
    assert not assess_required_evidence(
        {"requiredEvidence": {"mandatory": {"required": "yes"}}}, mixed_native
    )["complete"]
    assert not assess_required_evidence(
        {"requiredEvidence": {"optional": {"required": False}}}, mixed_native
    )["complete"]

    return {
        "profileId": profile_id,
        "abstractStates": list(STATES),
        "requiredClaims": names,
        "modelStatesExhaustivelyChecked": checked,
        "acceptedStates": accepted,
        "profileSha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
    }



def check_shared_standing() -> dict:
    """Bounded refinement for the v1/v2 shared decision, independent of native I/O.

    Exhausts all 5² combinations of required status representatives and both
    independent-evidence dispositions. This is a finite abstraction, not a
    theorem about arbitrary provider results or consumer readback.
    """
    required = {"decoded", "readback"}
    states = ("MISSING", "PASS", "FAIL", "NOT_EVALUATED", "INVALID")
    checked = 0
    for pair in itertools.product(states, repeat=2):
        for invalid_witness in (False, True):
            observed = {
                key: value
                for key, value in zip(sorted(required), pair, strict=True)
                if value != "MISSING"
            }
            issues = ("native witness mismatch",) if invalid_witness else ()
            result = assess_required_statuses(required, observed, issues=issues)
            # Independent oracle: contradictory observations cannot count
            # as verified failures; only valid, explicit FAIL is falsification.
            if invalid_witness:
                expected = "UNKNOWN"
            elif "FAIL" in pair:
                expected = "FAIL"
            elif pair == ("PASS", "PASS"):
                expected = "PASS"
            else:
                expected = "UNKNOWN"
            if result["verificationStatus"] != expected:
                raise AssertionError(
                    f"shared-standing status refinement failed: {pair} {issues}: {result}"
                )
            if result["complete"] != (expected == "PASS"):
                raise AssertionError(
                    f"shared-standing completion refinement failed: {pair}: {result}"
                )
            if result["consumerAcceptance"] != "EXTERNAL_NOT_EVALUATED":
                raise AssertionError("shared Standing illegally promotes consumer acceptance")
            checked += 1

    if assess_required_statuses(set(), {})["complete"]:
        raise AssertionError("empty requirements yielded vacuous completeness")
    assert checked == 50

    # Source-bound two-claim abstraction: a native result may reuse one
    # specifically declared multi-claim witness, but neither generic status
    # nor another claim's matching PASS certifies this claim.
    binding_profile = {
        "requiredEvidence": {"alpha": {"required": True}, "beta": {"required": True}}
    }
    binding_modes = ("named", "generic", "multi", "other")
    binding_checked = 0
    for alpha_mode, beta_mode in itertools.product(binding_modes, repeat=2):
        observation = {
            "alpha": {"status": "PASS"},
            "beta": {"status": "PASS"},
            "aggregate": {"status": "PASS"},
            "multi": {"status": "PASS", "supportsClaims": ["alpha", "beta"]},
        }
        claim_results = {}
        for name, mode in (("alpha", alpha_mode), ("beta", beta_mode)):
            if mode == "named":
                pointer = f"/observations/{name}"
            elif mode == "generic":
                pointer = "/observations/aggregate"
            elif mode == "multi":
                pointer = "/observations/multi"
            else:
                pointer = f"/observations/{'beta' if name == 'alpha' else 'alpha'}"
            claim_results[name] = {
                "status": "PASS",
                "nativePointers": [pointer],
            }
        candidate = {
            "status": "PASS",
            "observations": observation,
            "claimResults": claim_results,
        }
        actual = assess_required_evidence(binding_profile, candidate)
        oracle = all(
            mode in {"named", "multi"} for mode in (alpha_mode, beta_mode)
        )
        if actual["complete"] != oracle:
            raise AssertionError(
                f"claim-specific witness refinement violated: "
                f"{alpha_mode}/{beta_mode} actual={actual} expected={oracle}"
            )
        binding_checked += 1
    assert binding_checked == 16
    return {
        "method": "finite Cartesian abstraction + production-source refinement",
        "abstractStates": list(states),
        "abstractCasesChecked": checked,
        "claimBindingCasesChecked": binding_checked,
        "counterexamples": 0,
        "nonClaims": [
            "not proof of native result honesty or pointer identity",
            "not proof of target application or domain acceptance",
        ],
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
        "sharedStandingModel": check_shared_standing(),
        "models": rows,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    assert summary["totalStates"] > 100000, "vacuous state-space reduction"


if __name__ == "__main__":
    main()
