#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/ENTERPRISE_OPERATING_MODEL_R1.md"
COMPOSITION = ROOT / "compositions/enterprise-work-to-outcome-r1.md"
RECEIPT = ROOT / "evidence/acceptance/enterprise-operating-model-r1-dogfood-20260914.json"
R2_ACCEPT = ROOT / "evidence/acceptance/standard-native-enterprise-r2-acceptance-20260914.json"
R2_SCHEMA = ROOT / "evidence/acceptance/standard-native-enterprise-r2-schema-validation-20260914.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    doc = DOC.read_text(encoding="utf-8")
    composition = COMPOSITION.read_text(encoding="utf-8")
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    r2_accept = json.loads(R2_ACCEPT.read_text(encoding="utf-8"))
    r2_schema = json.loads(R2_SCHEMA.read_text(encoding="utf-8"))

    if receipt.get("standing") != "PASS_BOUNDED_INTERNAL_DOGFOOD":
        fail("dogfood standing is not accepted")
    if receipt["work"].get("externalCustomer") is not False or receipt["work"].get("businessTransaction") is not False:
        fail("internal dogfood must not be laundered into customer/business evidence")
    if receipt["work"].get("acceptedCommit") != "a0d73b08702b507b801bb4c124acc2733b97bb4b":
        fail("dogfood accepted commit mismatch")
    if r2_accept.get("standing") != "PASS_CROSS_DOMAIN_DOGFOOD":
        fail("underlying Standard-Native R2 semantic acceptance missing")
    if r2_schema.get("standing") != "PASS" or "check-jsonschema" not in r2_schema.get("validator", ""):
        fail("underlying mature schema validation missing")

    activations = {x["provider"]: x["status"] for x in receipt["providerActivation"]}
    required = {
        "git-ordivon-next": "ACTIVATED",
        "strictdoc-0.29.0": "ACTIVATED",
        "check-jsonschema-0.38.0": "ACTIVATED",
        "ordivon-runtime": "ACTIVATED",
        "erpnext": "AVAILABLE_NOT_ACTIVATED",
        "plane-openproject": "NOT_ACTIVATED",
        "flowable-bpmn-cmmn-dmn": "MATERIALIZED_NOT_ACTIVATED",
        "temporal": "NOT_ACTIVATED",
        "n8n": "AVAILABLE_NOT_ACTIVATED",
    }
    for provider, expected in required.items():
        if activations.get(provider) != expected:
            fail(f"provider activation mismatch: {provider} -> {activations.get(provider)!r}, expected {expected!r}")

    applied = {x["id"]: x["disposition"] for x in receipt["externalManagementGuidance"]}
    for standard in ("iso-integrated-management-systems-guide-2026", "iso-10005-2018", "iso-21502-2020", "iso-10006-2017", "iso-31000-2018"):
        if not applied.get(standard, "").startswith("APPLIED"):
            fail(f"management guidance not applied: {standard}")
    if applied.get("iso-19011-2026") != "NOT_ACTIVATED_NO_AUDIT_OBJECTIVE":
        fail("audit guidance was incorrectly treated as an audit")
    if applied.get("iso-9001-2026") != "UNDER_PUBLICATION_NOT_YET_TREATED_AS_PUBLISHED":
        fail("ISO 9001:2026 currentness boundary lost")

    if receipt["qualityPlan"].get("result") != "ACCEPTED" or len(receipt["qualityPlan"].get("acceptanceCriteria", [])) < 8:
        fail("bounded quality plan acceptance is incomplete")
    if any(row.get("standing") != "TREATED" for row in receipt.get("risksAndTreatments", [])):
        fail("one or more admitted dogfood risks lack a treatment standing")

    required_doc = [
        "Prepare -> Connect -> Integrate",
        "ISO 10005:2018",
        "ISO 21502:2020",
        "ISO 31000:2018",
        "ISO 19011:2026",
        "ISO 9001:2026 — UNDER PUBLICATION",
        "Dormant is not deficient.",
        "Universal front door",
        "Universal unlimited contract",
        "Provider activation economics",
        "R1 dogfood — Standard-Native Enterprise Environment R2",
    ]
    for phrase in required_doc:
        if phrase not in doc:
            fail(f"operating model missing: {phrase}")
    if "Provider success is evidence only for that provider's responsibility" not in composition:
        fail("composition lost provider/domain evidence boundary")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.enterprise-operating-model-r1-acceptance",
        "standing": "PASS_REAL_INTERNAL_WORK_DOGFOOD",
        "work": receipt["work"]["name"],
        "qualityPlanCriteria": len(receipt["qualityPlan"]["acceptanceCriteria"]),
        "risksTreated": len(receipt["risksAndTreatments"]),
        "activatedProviders": sorted(k for k, v in activations.items() if v == "ACTIVATED"),
        "dormantProvidersPreserved": sorted(k for k, v in activations.items() if "NOT_ACTIVATED" in v),
        "boundary": "Acceptance proves a bounded operating-model composition over a real internal improvement project. It does not prove ISO certification, external customer acceptance, or universal provider applicability."
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
