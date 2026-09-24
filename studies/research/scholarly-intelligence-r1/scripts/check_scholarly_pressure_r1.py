#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
PLAN = STUDY / "pressure-tests/axis-authority-isolation-r1.json"
PROFILES = STUDY / "profiles"
SCHEMA = REPO_ROOT / "profiles/research/scholarly-intelligence/scholarly-intelligence-profile-v1.schema.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected object: {path}")
    return value


def run_bytes(*args: str) -> bytes:
    cp = subprocess.run(args, capture_output=True, check=False)
    if cp.returncode:
        fail(
            f"command failed ({cp.returncode}): {' '.join(args)}\n"
            + cp.stderr.decode("utf-8", errors="replace")
        )
    return cp.stdout


def sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def get_path(value: Any, dotted: str) -> Any:
    current = value
    for token in dotted.split("."):
        if not isinstance(current, dict) or token not in current:
            fail(f"missing assertion path {dotted}")
        current = current[token]
    return current


def evaluate(actual: Any, op: str, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "contains":
        return isinstance(actual, str) and str(expected) in actual
    if op == "contains_item":
        return isinstance(actual, list) and expected in actual
    if op == "gt":
        return isinstance(actual, (int, float)) and actual > expected
    fail(f"unsupported op: {op}")


def semantic_ref_index(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for items in profile["semanticRefs"].values():
        for item in items:
            out[item["id"]] = item
    return out


def evidence_json(
    profile: dict[str, Any],
    ref: dict[str, Any],
    cache: dict[tuple[str, str, str], dict[str, Any]],
) -> dict[str, Any]:
    authority = profile["studyAuthority"]
    repo = authority["sourceRepo"]
    revision = authority["sourceRevision"]
    location = ref.get("location")
    digest = ref.get("digest")
    if not location or not digest:
        fail(f"{profile['profileId']} ref {ref['id']} lacks location/digest")
    key = (repo, revision, location)
    if key in cache:
        return cache[key]
    raw = run_bytes("git", "-C", repo, "show", f"{revision}:{location}")
    if sha256(raw) != digest:
        fail(f"digest mismatch for {profile['profileId']}:{ref['id']}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"non-JSON pressure evidence {profile['profileId']}:{ref['id']}: {exc}")
    if not isinstance(value, dict):
        fail(f"pressure evidence root is not object: {profile['profileId']}:{ref['id']}")
    cache[key] = value
    return value


def counterexample_pressure(schema: dict[str, Any]) -> dict[str, Any]:
    root_props = set(schema.get("properties", {}))
    defs = schema.get("$defs", {})
    opaque_props = set(defs.get("opaqueRef", {}).get("properties", {}))
    state_schema = defs.get("stateAxis", {}).get("properties", {}).get("state", {})
    checks = {
        "noScientificPayloadAtRoot": not bool(
            root_props
            & {
                "estimand",
                "pValue",
                "effectSize",
                "uncertainty",
                "eligibilityDecision",
                "reviewText",
                "acceptanceProbability",
                "experimentAuthorized",
            }
        ),
        "opaqueRefRemainsThin": opaque_props == {"owner", "id", "location", "digest"},
        "ownerNativeStateNotNormalizedEnum": (
            state_schema.get("type") == "string" and "enum" not in state_schema
        ),
        "noGlobalScientificEdgeOntology": "relations" not in root_props
        and "coordinationLinks" not in root_props,
        "emptyRoleListsAllowed": "minItems"
        not in defs.get("refList", {}),
    }
    failed = sorted(key for key, value in checks.items() if not value)
    return {
        "standing": "PASS_COUNTEREXAMPLE_PRESSURE_FOR_PROFILE_ONLY"
        if not failed
        else "FAIL_COUNTEREXAMPLE_PRESSURE",
        "checks": checks,
        "failed": failed,
    }


def main() -> int:
    plan = load(PLAN)
    schema = load(SCHEMA)
    cache: dict[tuple[str, str, str], dict[str, Any]] = {}
    rows = []
    owners: set[str] = set()
    repos: set[str] = set()

    for case in plan["studies"]:
        profile_path = PROFILES / f"{case['profileId']}.json"
        profile = load(profile_path)
        authority = profile["studyAuthority"]
        owners.add(authority["owner"])
        repos.add(authority["sourceRepo"])
        refs = semantic_ref_index(profile)
        assertion_rows = []
        for assertion in case["assertions"]:
            ref_id = assertion["evidenceRef"]
            ref = refs.get(ref_id)
            if ref is None:
                fail(f"{case['profileId']}: pressure evidence ref not projected: {ref_id}")
            evidence = evidence_json(profile, ref, cache)
            actual = get_path(evidence, assertion["path"])
            passed = evaluate(actual, assertion["op"], assertion["expected"])
            assertion_rows.append(
                {
                    "evidenceRef": ref_id,
                    "path": assertion["path"],
                    "op": assertion["op"],
                    "expected": assertion["expected"],
                    "actual": actual,
                    "passed": passed,
                }
            )
            if not passed:
                fail(
                    f"{case['profileId']} pressure assertion failed: "
                    f"{assertion['path']} {assertion['op']} {assertion['expected']!r}, "
                    f"got {actual!r}"
                )
        rows.append(
            {
                "profileId": case["profileId"],
                "studyLabel": case["studyLabel"],
                "assertionCount": len(assertion_rows),
                "assertionsPassed": sum(r["passed"] for r in assertion_rows),
                "actionBoundary": case["actionBoundary"],
                "nextActionClass": case["nextActionClass"],
                "supportsCandidateRule": True,
                "assertions": assertion_rows,
            }
        )

    cx = counterexample_pressure(schema)
    if cx["standing"] != "PASS_COUNTEREXAMPLE_PRESSURE_FOR_PROFILE_ONLY":
        fail("counterexample pressure failed")

    shared_rule_supported = (
        len(rows) >= 3
        and len(owners) >= 3
        and len(repos) >= 2
        and all(row["supportsCandidateRule"] for row in rows)
    )
    external_substitution = (
        plan["externalSubstitutionAssessment"]["status"] == "PASS_FOR_THIN_PROFILE_ONLY"
    )
    admission = (
        "ADMIT_THIN_PROFILE_PROTOCOL"
        if shared_rule_supported and external_substitution
        else "PENDING_MORE_EVIDENCE"
    )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.cross-study-pressure-test-result",
        "planId": plan["id"],
        "candidateRule": plan["candidateRule"],
        "standing": "PASS_CROSS_STUDY_PRESSURE_R1",
        "independentStudyOwnerCount": len(owners),
        "distinctSourceRepoCount": len(repos),
        "studies": rows,
        "externalSubstitutionAssessment": plan["externalSubstitutionAssessment"],
        "counterexamplePressure": cx,
        "admission": {
            "target": plan["admissionTarget"],
            "verdict": admission,
            "explicitlyNotAdmitted": plan["explicitlyNotAdmitted"],
        },
        "truthBoundary": (
            "The admission verdict applies only to the thin non-authoritative projection "
            "protocol. Study scientific semantics and action authority remain external."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
