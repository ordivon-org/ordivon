"""Finite abstract refinement for native result identity.

Three states per native fact: exact, contradictory, or not evaluated.
All Cartesian combinations are executed against the production predicate.
The independent oracle defines strict and legacy promotion semantics.
This does not constitute a proof about arbitrary JSON or external tools.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifact_verification.native_identity import assess_native_identity  # noqa: E402

STATES = ("MATCH", "MISMATCH", "UNKNOWN")
PROFILE = "audio-wave-pcm16-r1"
SUBJECT = "a" * 64
CONTRACT = "b" * 64
SIZE = 987


def _value(state: str, expected: object) -> object | None:
    if state == "UNKNOWN":
        return None
    if state == "MISMATCH":
        return 16 if isinstance(expected, int) else "not-the-expected-value"
    return expected


def check_model(include_contract: bool, strict: bool) -> int:
    names = ("profileId", "artifact.sha256", "artifact.size")
    if include_contract:
        names += ("contract.sha256",)
    count = 0
    for vector in itertools.product(STATES, repeat=len(names)):
        abstract = dict(zip(names, vector, strict=True))
        native = {
            "status": "PASS",
            "profileId": _value(abstract["profileId"], PROFILE),
            "artifact": {
                "sha256": _value(abstract["artifact.sha256"], SUBJECT),
                "size": _value(abstract["artifact.size"], SIZE),
            },
        }
        if include_contract:
            native["contract"] = {
                "sha256": _value(abstract["contract.sha256"], CONTRACT)
            }
        result = assess_native_identity(
            native,
            profile_id=PROFILE,
            subject_sha256=SUBJECT,
            subject_size=SIZE,
            contract_sha256=CONTRACT if include_contract else None,
            require_complete=strict,
        )
        # Independent specification: any contradiction fails; absent fields
        # stay unknown for legacy, but strict qualification needs full witness.
        contradiction = "MISMATCH" in vector
        unknown = "UNKNOWN" in vector
        expected_reject = contradiction or (strict and unknown)
        expected_complete = not contradiction and not unknown
        if result["rejected"] != expected_reject:
            raise AssertionError((include_contract, strict, abstract, result))
        if result["complete"] != expected_complete:
            raise AssertionError((include_contract, strict, abstract, result))
        if (result["status"] == "COMPLETE") != expected_complete:
            raise AssertionError((include_contract, strict, abstract, result))
        count += 1
    return count


def main() -> None:
    variants = [
        (with_contract, strict)
        for with_contract in (False, True)
        for strict in (False, True)
    ]
    counts = [
        {"contractRequired": with_contract, "strict": strict,
         "states": check_model(with_contract, strict)}
        for with_contract, strict in variants
    ]
    summary = {
        "method": "finite Cartesian state abstraction + production-source refinement",
        "sourceSha256": hashlib.sha256(
            (ROOT / "artifact_verification/native_identity.py").read_bytes()
        ).hexdigest(),
        "states": sum(row["states"] for row in counts),
        "counterexamples": 0,
        "variants": counts,
        "nonClaims": [
            "not exhaustive over arbitrary JSON values or nested objects",
            "not a theorem about native verifier honesty or filesystem effects",
            "not production service or domain-consumer acceptance",
        ],
    }
    assert summary["states"] == 216
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
