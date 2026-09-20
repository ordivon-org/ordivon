#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/standard-native-profile-projection-v1.schema.json"
RECEIPT = (
    ROOT / "evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json"
)


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    if (
        receipt.get("kind")
        != "ordivon.standard-native.enterprise-r2-cross-domain-dogfood"
    ):
        fail("wrong dogfood receipt kind")

    cases = receipt.get("cases", [])
    by_id = {case.get("caseId"): case for case in cases}
    if set(by_id) != {"research", "runtime", "game"} or len(cases) != 3:
        fail("dogfood must contain exactly research, runtime, and game")

    for case_id, case in by_id.items():
        errors = sorted(validator.iter_errors(case), key=lambda error: list(error.path))
        if errors:
            detail = "; ".join(
                f"{case_id}:{'.'.join(map(str, error.path)) or '$'}: {error.message}"
                for error in errors
            )
            fail(detail)
        req = case["requirementIdentity"]
        if req["count"] != len(req["uids"]):
            fail(f"{case_id}: requirement count does not match stable UID set")

    obs = receipt.get("observations", {})
    for key in (
        "allHaveExternalAuthorityDecisions",
        "allHaveStableRequirementIdentity",
        "allHaveExplicitClaimBoundary",
        "domainVerdictVocabulariesDistinct",
    ):
        if obs.get(key) is not True:
            fail(f"dogfood invariant false: {key}")
    if obs.get("universalVerdictNormalizationApplied") is not False:
        fail("universal verdict normalization must remain false")
    if obs.get("sharedVerdictStatuses") != ["PASS"]:
        fail(
            f"unexpected cross-domain verdict intersection: {obs.get('sharedVerdictStatuses')}"
        )

    union = set(obs.get("unionVerdictStatuses", []))
    expected_distinctive = {
        "EXTERNAL_ASSERTION_REQUIRED",
        "NOT_CLAIMED",
        "PINNED_NOT_LATEST",
        "DEFERRED_NOT_APPLICABLE_CURRENT_PHASE",
    }
    if not expected_distinctive.issubset(union):
        fail("dogfood lost distinctive domain verdict semantics")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.standard-native.enterprise-r2-acceptance",
        "standing": "PASS_CROSS_DOMAIN_DOGFOOD",
        "cases": [
            {
                "caseId": case_id,
                "authorities": len(by_id[case_id]["authorityDecisions"]),
                "requirements": by_id[case_id]["requirementIdentity"]["count"],
                "verdictStatuses": sorted(by_id[case_id]["verdict"]["summary"]),
            }
            for case_id in ("research", "runtime", "game")
        ],
        "sharedVerdictStatuses": obs["sharedVerdictStatuses"],
        "universalVerdictNormalizationApplied": False,
        "boundary": (
            "Acceptance proves the R2 projection/integration mechanics across three real "
            "domain profiles. It is not certification or domain semantic completion."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
