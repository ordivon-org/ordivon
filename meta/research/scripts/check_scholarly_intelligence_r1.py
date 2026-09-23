#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

META = Path(__file__).resolve().parents[2]
SCHEMA = META / "research/schemas/scholarly-intelligence-profile-v1.schema.json"
PROFILE = META / "research/profiles/paper1-standard-native-r2-dogfood-r1.json"
DOGFOOD = META / "next/evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json"

EXPECTED_AXES = {
    "requirements",
    "evidence",
    "inference",
    "claims",
    "argument",
    "venue",
    "review",
    "publication",
    "learning",
}
EXPECTED_REF_ROLES = {"requirements", "claims", "evidence", "concerns", "resolutions"}


def fail(message: str) -> None:
    raise SystemExit(message)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path}")
    return value


def main() -> int:
    schema = load(SCHEMA)
    profile = load(PROFILE)
    dogfood = load(DOGFOOD)

    Draft202012Validator.check_schema(schema)
    validation_errors = sorted(
        Draft202012Validator(schema).iter_errors(profile),
        key=lambda error: list(error.path),
    )
    if validation_errors:
        detail = "; ".join(
            f"{'.'.join(map(str, error.path)) or '$'}: {error.message}"
            for error in validation_errors
        )
        fail(f"profile schema validation failed: {detail}")

    if schema.get("$id") != "urn:ordivon:research:scholarly-intelligence-profile:v1":
        fail("unexpected schema identity")
    if profile.get("kind") != "ordivon.research.scholarly-intelligence-profile":
        fail("wrong profile kind")
    if profile.get("truthRole") != "non-authoritative-study-projection":
        fail("shared Research profile must remain non-authoritative")

    study = profile.get("studyAuthority", {})
    revision = study.get("sourceRevision")
    if not isinstance(revision, str) or len(revision) != 40:
        fail("study authority must bind exact 40-hex revision")
    try:
        int(revision, 16)
    except ValueError as exc:
        raise SystemExit("study sourceRevision is not hexadecimal") from exc

    binding = profile.get("standardNativeBinding")
    if not isinstance(binding, dict):
        fail("R1 dogfood must bind the accepted Standard-Native projection")
    if binding.get("sourceDigest") != sha256(DOGFOOD):
        fail("Standard-Native dogfood digest drifted")

    cases = {
        case.get("caseId"): case
        for case in dogfood.get("cases", [])
        if isinstance(case, dict)
    }
    research_case = cases.get(binding.get("caseId"))
    if research_case is None:
        fail("bound Standard-Native case not found")
    if research_case.get("domain") != "research":
        fail("bound Standard-Native case is not Research")
    if research_case.get("source", {}).get("headRevision") != revision:
        fail("Study revision differs from accepted Research dogfood revision")

    axes = profile.get("stateAxes", {})
    if set(axes) != EXPECTED_AXES:
        fail(f"state-axis set differs: {sorted(axes)}")
    for axis, value in axes.items():
        if not isinstance(value, dict):
            fail(f"state axis {axis} is not an object")
        if not value.get("owner"):
            fail(f"state axis {axis} has no owner")
        if not value.get("state"):
            fail(f"state axis {axis} has no owner-native state")
        if not isinstance(value.get("evidenceRefs"), list):
            fail(f"state axis {axis} evidenceRefs must be a list")

    refs = profile.get("semanticRefs", {})
    if set(refs) != EXPECTED_REF_ROLES:
        fail(f"semantic reference roles differ: {sorted(refs)}")
    for role, items in refs.items():
        if not isinstance(items, list):
            fail(f"{role} references must be a list")
        for item in items:
            if not isinstance(item, dict) or not item.get("owner") or not item.get("id"):
                fail(f"{role} reference lacks owner/id")

    non_claims = profile.get("nonClaims", [])
    if not isinstance(non_claims, list) or len(non_claims) < 3:
        fail("profile requires explicit non-claims")
    joined = " ".join(non_claims).casefold()
    for token in ("not current", "does not establish", "does not reinterpret"):
        if token not in joined:
            fail(f"missing authority-boundary non-claim: {token}")

    forbidden_top_level = {
        "manuscript",
        "dataset",
        "scores",
        "modelFits",
        "reviewText",
        "decision",
        "acceptanceProbability",
    }
    leaked = forbidden_top_level.intersection(profile)
    if leaked:
        fail(f"Study payload/decision leaked into shared projection: {sorted(leaked)}")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.scholarly-intelligence-r1-acceptance",
        "standing": "PASS_PROFILE_ONLY_DOGFOOD",
        "profileId": profile["profileId"],
        "studyRevision": revision,
        "standardNativeDigest": binding["sourceDigest"],
        "stateAxisCount": len(axes),
        "semanticReferenceRoles": sorted(refs),
        "truthRole": profile["truthRole"],
        "boundary": (
            "Acceptance proves a non-authoritative machine-readable Research projection "
            "over an already accepted historical Paper1 Standard-Native dogfood object. "
            "It does not establish current Paper1 scientific, review, publication, or "
            "submission standing."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
