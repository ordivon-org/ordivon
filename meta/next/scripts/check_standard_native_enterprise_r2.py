#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/standard-native-profile-projection-v1.schema.json"
RECEIPT = ROOT / "evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json"
DOC = ROOT / "docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md"
README = ROOT / "README.md"
VERIFY = ROOT / "verification/README.md"


def fail(message: str) -> None:
    raise SystemExit(message)


def structural_validate(case: dict) -> None:
    required = {"schemaVersion", "kind", "caseId", "domain", "source", "subject", "authorityDecisions", "requirementIdentity", "verdict", "claimBoundary"}
    missing = required - set(case)
    if missing:
        fail(f"{case.get('caseId','?')}: missing projection fields {sorted(missing)}")
    if case["schemaVersion"] != 1 or case["kind"] != "ordivon.standard-native.profile-projection":
        fail(f"{case['caseId']}: wrong projection identity")
    if not case["authorityDecisions"]:
        fail(f"{case['caseId']}: no authority decisions")
    for row in case["authorityDecisions"]:
        if row.get("disposition") not in {"BOUND", "EXCLUDED", "DEFERRED"}:
            fail(f"{case['caseId']}: invalid authority disposition")
        if not row.get("id"):
            fail(f"{case['caseId']}: authority without id")
    req = case["requirementIdentity"]
    if req["count"] < 1 or req["count"] != len(req["uids"]) or len(set(req["uids"])) != len(req["uids"]):
        fail(f"{case['caseId']}: unstable requirement identity")
    if case["verdict"].get("owner") != "domain" or not case["verdict"].get("summary"):
        fail(f"{case['caseId']}: verdict ownership/summary invalid")
    if not case["claimBoundary"].strip():
        fail(f"{case['caseId']}: empty claim boundary")
    for key in ("profile", "report", "requirements"):
        ident = case["source"][key]
        if not ident["sha256"].startswith("sha256:") or len(ident["sha256"]) != 71:
            fail(f"{case['caseId']}: bad {key} digest")
        if len(ident["lastCommit"]) != 40:
            fail(f"{case['caseId']}: bad {key} commit")


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    verify = VERIFY.read_text(encoding="utf-8")

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("projection schema is not JSON Schema 2020-12")
    if schema.get("$id") != "urn:ordivon:schema:standard-native-profile-projection:v1":
        fail("projection schema identity mismatch")
    if receipt.get("kind") != "ordivon.standard-native.enterprise-r2-cross-domain-dogfood":
        fail("wrong dogfood receipt kind")
    cases = receipt.get("cases", [])
    if [c.get("caseId") for c in cases] != ["research", "runtime", "game"]:
        fail("dogfood must contain research, runtime, game in that order")
    for case in cases:
        structural_validate(case)

    obs = receipt.get("observations", {})
    for key in ("allHaveExternalAuthorityDecisions", "allHaveStableRequirementIdentity", "allHaveExplicitClaimBoundary", "domainVerdictVocabulariesDistinct"):
        if obs.get(key) is not True:
            fail(f"dogfood invariant false: {key}")
    if obs.get("universalVerdictNormalizationApplied") is not False:
        fail("universal verdict normalization must remain false")
    if obs.get("sharedVerdictStatuses") != ["PASS"]:
        fail(f"unexpected cross-domain verdict intersection: {obs.get('sharedVerdictStatuses')}")

    union = set(obs.get("unionVerdictStatuses", []))
    expected_distinctive = {"EXTERNAL_ASSERTION_REQUIRED", "NOT_CLAIMED", "PINNED_NOT_LATEST", "DEFERRED_NOT_APPLICABLE_CURRENT_PHASE"}
    if not expected_distinctive.issubset(union):
        fail("dogfood lost distinctive domain verdict semantics")

    required_doc_phrases = [
        "Domain-owned verdict",
        "Orthogonal dimensions, not one traffic light",
        "Prepare",
        "Connect",
        "Integrate",
        "BPMN 2.0.2",
        "CMMN 1.1",
        "DMN 1.5",
        "Historical evidence is append/supersede, not rewrite",
        "does **not** define one global status enum",
    ]
    for phrase in required_doc_phrases:
        if phrase not in doc:
            fail(f"R2 doc missing: {phrase}")
    if "STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md" not in readme:
        fail("README does not route to R2")
    if "domain-owned verdict vocabulary" not in verify:
        fail("verification README does not preserve domain verdict ownership")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.standard-native.enterprise-r2-acceptance",
        "standing": "PASS_CROSS_DOMAIN_DOGFOOD",
        "cases": [
            {
                "caseId": c["caseId"],
                "authorities": len(c["authorityDecisions"]),
                "requirements": c["requirementIdentity"]["count"],
                "verdictStatuses": sorted(c["verdict"]["summary"]),
            }
            for c in cases
        ],
        "sharedVerdictStatuses": obs["sharedVerdictStatuses"],
        "universalVerdictNormalizationApplied": False,
        "boundary": "Acceptance proves the R2 projection/integration mechanics across three real domain profiles. It is not certification or domain semantic completion."
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
