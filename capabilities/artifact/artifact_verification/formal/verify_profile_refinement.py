"""Bounded executable source refinement of production Profile v1 to v2.

For each of the eight real production Profiles, enumerate a Cartesian 2^7
product of independent agreement/disagreement dimensions. Cross-check the
production evaluator with an independent Boolean oracle. The scope is only
shared Profile identity, family, construction, primary output and target facts,
not equality of all policy/evidence semantics or arbitrary JSON structures.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifact_core.json_validation import load_json  # noqa: E402
from artifact_core.profile_refinement import assess_v1_v2_refinement  # noqa: E402

ART = ROOT / "artifact-delivery"
PROFILES = (
    "document-r1",
    "pdf-accessible-r1",
    "pdf-fixed-r1",
    "pdu-sdu-presentation-r1",
    "presentation-local-development-r1",
    "presentation-ultrawide-34x10-r1",
    "spreadsheet-r1",
    "web-r1",
)
AXES = (
    "id",
    "classification.family",
    "construction.authorityMode",
    "outputs.format",
    "outputs.purpose",
    "outputs.required",
    "targetAuthorities.primary.required",
)


def disagree(doc: dict, axis: str) -> None:
    if axis == "id":
        doc["id"] = "unrelated-production-profile"
    elif axis == "classification.family":
        doc["classification"]["family"] = "still-image"
    elif axis == "construction.authorityMode":
        source = doc["construction"]["authorityMode"]
        doc["construction"]["authorityMode"] = (
            "source-authored" if source == "generated-managed" else "generated-managed"
        )
    elif axis == "outputs.format":
        doc["outputs"][0]["format"]["name"] = "not-the-original-format"
    elif axis == "outputs.purpose":
        doc["outputs"][0]["purpose"] = "not-the-original-purpose"
    elif axis == "outputs.required":
        doc["outputs"][0]["required"] = not doc["outputs"][0]["required"]
    elif axis == "targetAuthorities.primary.required":
        doc["targetAuthorities"][0]["required"] = not doc["targetAuthorities"][0]["required"]
    else:
        raise AssertionError(f"unmodeled axis: {axis}")


def main() -> None:
    total = 0
    for profile_id in PROFILES:
        source = load_json(ART / "examples" / f"{profile_id}.json")
        canonical = load_json(
            ART / "shadow-v2/examples" / f"{profile_id}-v2.json"
        )
        for vector in itertools.product((False, True), repeat=len(AXES)):
            candidate = json.loads(json.dumps(canonical))
            for axis, mutated in zip(AXES, vector, strict=True):
                if mutated:
                    disagree(candidate, axis)
            actual = assess_v1_v2_refinement(source, candidate)
            # Independent abstract oracle: baseline Profile agrees by
            # construction; each axis modifies a disjoint agreed fact.
            expected_complete = not any(vector)
            if actual["complete"] is not expected_complete:
                raise AssertionError((profile_id, vector, actual))
            if actual["status"] != ("PASS" if expected_complete else "FAIL"):
                raise AssertionError((profile_id, vector, actual))
            total += 1
    assert total == 1024
    print(json.dumps({
        "method": "exhaustive finite Boolean crosswalk model with independent oracle",
        "productionProfiles": len(PROFILES),
        "refinementAxes": AXES,
        "statesChecked": total,
        "counterexamples": 0,
        "sourceSha256": hashlib.sha256(
            (ROOT / "artifact_core/profile_refinement.py").read_bytes()
        ).hexdigest(),
        "nonClaims": (
            "not arbitrary JSON equivalence, full v1/v2 policy equivalence, "
            "runtime provider correctness, source path continuity or consumer acceptance"
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
