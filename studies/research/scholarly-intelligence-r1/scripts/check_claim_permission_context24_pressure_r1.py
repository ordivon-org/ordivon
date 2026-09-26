#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
PLAN = STUDY / "pressure-tests/claim-permission-context24-r1.json"
RECEIPT = STUDY / "evidence/claim-permission-context24-pressure-r1.json"
IDENTITY_RECEIPT = STUDY / "evidence/context24-identity-core-r1.json"
CONTENT_RECEIPT = STUDY / "evidence/context24-evidence-content-core-r1.json"
IDENTITY_ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/context24/"
    "context24-identity-core-r1-20260923"
)
CONTENT_ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/context24/"
    "context24-evidence-content-core-r1-20260923"
)


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                fail(f"expected object at {path}:{line_number}")
            rows.append(value)
    return rows


def derive() -> dict[str, Any]:
    plan = load_json(PLAN)
    identity_receipt = load_json(IDENTITY_RECEIPT)
    content_receipt = load_json(CONTENT_RECEIPT)
    bindings = plan["sourceBindings"]
    if identity_receipt["snapshot"]["identity"] != bindings["identitySnapshot"]:
        fail("Context24 identity snapshot drifted")
    if content_receipt["snapshot"]["identity"] != bindings["contentSnapshot"]:
        fail("Context24 content snapshot drifted")

    claims = load_jsonl(IDENTITY_ROOT / "derived/jsonl/claims.jsonl")
    links = load_jsonl(IDENTITY_ROOT / "derived/jsonl/task1_evidence_links.jsonl")
    content_links = load_jsonl(
        CONTENT_ROOT / "derived/jsonl/claim_evidence_content_links.jsonl"
    )
    evidence_contents = load_jsonl(
        CONTENT_ROOT / "derived/jsonl/evidence_contents.jsonl"
    )
    unresolved = load_jsonl(CONTENT_ROOT / "derived/jsonl/unresolved_gold_links.jsonl")
    fulltexts = load_jsonl(CONTENT_ROOT / "derived/jsonl/fulltexts.jsonl")

    train_claims = [
        row
        for row in claims
        if row.get("task") == "task1" and row.get("split") == "train"
    ]
    train_claim_ids = {str(row["claim_instance_id"]) for row in train_claims}
    train_links = [
        row for row in links if str(row["claim_instance_id"]) in train_claim_ids
    ]
    bound_links = [
        row for row in content_links if str(row["claim_instance_id"]) in train_claim_ids
    ]

    total_by_claim: Counter[str] = Counter(
        str(row["claim_instance_id"]) for row in train_links
    )
    bound_by_claim: Counter[str] = Counter(
        str(row["claim_instance_id"]) for row in bound_links
    )
    all_content = sum(
        bound_by_claim[claim_id] == total for claim_id, total in total_by_claim.items()
    )
    zero_content = sum(bound_by_claim[claim_id] == 0 for claim_id in total_by_claim)
    partial_content = sum(
        0 < bound_by_claim[claim_id] < total
        for claim_id, total in total_by_claim.items()
    )
    any_content = sum(bound_by_claim[claim_id] > 0 for claim_id in total_by_claim)

    type_total = Counter(str(row["evidence_kind"]) for row in train_links)
    bound_keys = {
        (str(row["claim_instance_id"]), str(row["finding_id"])) for row in bound_links
    }
    type_bound: Counter[str] = Counter()
    for row in train_links:
        key = (str(row["claim_instance_id"]), str(row["evidence_label"]))
        if key in bound_keys:
            type_bound[str(row["evidence_kind"])] += 1

    multiplicity = Counter(total_by_claim.values())
    content_reuse = Counter(str(row["evidence_content_id"]) for row in bound_links)
    train_paper_claims = Counter(str(row["citekey"]) for row in train_claims)
    native_collision_groups = len(
        {
            str(row["native_id"])
            for row in train_claims
            if str(row.get("nativeIdCollisionClass")) != "none"
        }
    )

    fulltext_citekeys = {str(row["citekey"]) for row in fulltexts}
    train_citekeys = {str(row["citekey"]) for row in train_claims}
    test_citekeys = {
        str(row["citekey"])
        for row in claims
        if row.get("task") == "task1" and row.get("split") == "test"
    }

    counts = {
        "task1TrainClaims": len(train_claims),
        "task1GoldEvidenceLinks": len(train_links),
        "contentBoundGoldLinks": len(bound_links),
        "identityOnlyGoldLinks": len(unresolved),
        "uniqueContentObjects": len(evidence_contents),
        "claimsAllGoldContentBound": all_content,
        "claimsAnyGoldContentBound": any_content,
        "claimsIdentityOnly": zero_content,
        "claimsPartiallyContentBound": partial_content,
        "claimsWithMultipleGoldLinks": sum(
            value > 1 for value in total_by_claim.values()
        ),
        "maxGoldLinksPerClaim": max(total_by_claim.values()),
        "contentObjectsReusedAcrossLinks": sum(
            value > 1 for value in content_reuse.values()
        ),
        "maxLinksPerContentObject": max(content_reuse.values()),
        "task1TrainPapers": len(train_citekeys),
        "maxTask1TrainClaimsPerPaper": max(train_paper_claims.values()),
        "task1TrainPapersWithFulltext": len(train_citekeys & fulltext_citekeys),
        "task1TestPapers": len(test_citekeys),
        "task1TestPapersWithFulltext": len(test_citekeys & fulltext_citekeys),
        "trainingNativeIdCollisionGroups": native_collision_groups,
    }
    expected_counts = {
        "task1TrainClaims": 474,
        "task1GoldEvidenceLinks": 679,
        "contentBoundGoldLinks": 256,
        "identityOnlyGoldLinks": 423,
        "uniqueContentObjects": 223,
        "claimsAllGoldContentBound": 171,
        "claimsAnyGoldContentBound": 171,
        "claimsIdentityOnly": 303,
        "claimsPartiallyContentBound": 0,
        "claimsWithMultipleGoldLinks": 125,
        "maxGoldLinksPerClaim": 9,
        "contentObjectsReusedAcrossLinks": 28,
        "maxLinksPerContentObject": 6,
        "task1TrainPapers": 229,
        "maxTask1TrainClaimsPerPaper": 18,
        "task1TrainPapersWithFulltext": 229,
        "task1TestPapers": 46,
        "task1TestPapersWithFulltext": 46,
        "trainingNativeIdCollisionGroups": 19,
    }
    if counts != expected_counts:
        fail(f"Context24 pressure counts drifted: {counts!r}")

    evidence_type_coverage = {
        kind: {
            "total": type_total[kind],
            "contentBound": type_bound[kind],
            "identityOnly": type_total[kind] - type_bound[kind],
        }
        for kind in sorted(type_total)
    }
    if evidence_type_coverage != {
        "figure": {"total": 554, "contentBound": 212, "identityOnly": 342},
        "table": {"total": 125, "contentBound": 44, "identityOnly": 81},
    }:
        fail("Context24 evidence-kind pressure coverage drifted")

    multiplicity_histogram = {
        str(key): multiplicity[key] for key in sorted(multiplicity)
    }
    if multiplicity_histogram != {
        "1": 349,
        "2": 89,
        "3": 10,
        "4": 17,
        "5": 4,
        "6": 3,
        "7": 1,
        "9": 1,
    }:
        fail("Context24 gold-link multiplicity drifted")

    rights = content_receipt["rights"]
    if rights.get("underlyingPaperMediaRights") != "NOT_INDEPENDENTLY_VERIFIED":
        fail("Context24 underlying-media rights boundary drifted")
    if rights.get("externalRedistribution") != "NOT_AUTHORIZED_BY_CATALOG":
        fail("Context24 external redistribution was silently authorized")
    if rights.get("commercialMediaReuse") != "NOT_AUTHORIZED_BY_CATALOG":
        fail("Context24 commercial media reuse was silently authorized")

    dispositions = {
        row["id"]: row["requiredDisposition"] for row in plan["counterexamples"]
    }
    expected_dispositions = {
        "CP-CX1-content-byte-laundering": "REJECT_REPRESENTATION_TO_SUPPORT_AUTHORITY_TRANSFER",
        "CP-CX2-identity-only-erasure": "PRESERVE_EVIDENCE_IDENTITY_WITHOUT_INVENTING_CONTENT",
        "CP-CX3-link-count-strength": "REJECT_MULTIPLICITY_TO_STRENGTH_OR_INDEPENDENCE",
        "CP-CX4-content-reuse-independence": "REJECT_LINK_COUNT_AS_INDEPENDENT_EVIDENCE_COUNT",
        "CP-CX5-fulltext-method-adequacy": "REJECT_CONTENT_AVAILABILITY_TO_METHOD_AUTHORITY",
        "CP-CX6-withheld-test-gold": "KEEP_WITHHELD_GOLD_UNIDENTIFIED",
        "CP-CX7-rights-science-conflation": "KEEP_RIGHTS_AND_SCIENTIFIC_AUTHORITY_SEPARATE",
        "CP-CX8-native-id-authority": "KEEP_INSTANCE_IDENTITY_AND_COLLISION_EVIDENCE",
    }
    if dispositions != expected_dispositions:
        fail("ClaimPermission pressure dispositions drifted")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.research.claim-permission-context24-pressure-evidence",
        "id": "claim-permission-context24-pressure-r1",
        "standing": "PASS_STUDY_OWNED_CLAIM_PERMISSION_PRESSURE_R1",
        "truthRole": "pressure-test-not-scientific-truth-or-shared-policy",
        "sourceBindings": bindings,
        "population": "Context24 public Task1 train gold plus bound evidence-content/fulltext carriers",
        "counts": counts,
        "evidenceTypeCoverage": evidence_type_coverage,
        "goldLinkMultiplicityHistogram": multiplicity_histogram,
        "representationStrata": {
            "contentBoundAllGold": {
                "claims": all_content,
                "inspectionCeiling": "CONTENT_INSPECTABLE",
                "scientificClaimStrength": "OWNER_INFERENCE_REQUIRED",
            },
            "identityOnly": {
                "claims": zero_content,
                "inspectionCeiling": "EVIDENCE_IDENTITY_TRACEABLE",
                "scientificClaimStrength": "OWNER_INFERENCE_REQUIRED",
            },
            "partiallyContentBound": {
                "claims": partial_content,
                "inspectionCeiling": "MIXED_REPRESENTATION_IF_PRESENT",
                "scientificClaimStrength": "OWNER_INFERENCE_REQUIRED",
            },
        },
        "candidateEnvelope": {
            "truthPermission": "NOT_GRANTED",
            "causalPermission": "NOT_GRANTED",
            "generalizationPermission": "NOT_GRANTED",
            "claimStrengthPromotion": "NOT_GRANTED",
            "methodAdequacyPermission": "NOT_GRANTED",
            "sharedExecutablePolicy": "NOT_ADMITTED",
            "ownerRequiredBeforeScientificPermission": plan[
                "ownerRequiredBeforeScientificPermission"
            ],
        },
        "pressureResults": [
            {"id": key, "disposition": value, "standing": "PASS_FAIL_CLOSED"}
            for key, value in expected_dispositions.items()
        ],
        "rightsBoundary": {
            "datasetCardLicenseObserved": rights["datasetCardLicenseObserved"],
            "underlyingPaperMediaRights": rights["underlyingPaperMediaRights"],
            "externalRedistribution": rights["externalRedistribution"],
            "commercialMediaReuse": rights["commercialMediaReuse"],
        },
        "admission": {
            "target": plan["admissionTarget"],
            "verdict": "KEEP_STUDY_OWNED_PRESSURE_PROTOTYPE",
            "crossStudyPromotionEligible": False,
            "explicitlyNotAdmitted": plan["explicitlyNotAdmitted"],
        },
        "truthBoundary": (
            "This pressure evidence proves representation/authority separation on the bound "
            "Context24 assets. It does not judge whether any scientific claim is true, "
            "sufficiently supported, causal, generalizable, or publication-worthy."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    derived = derive()
    encoded = json.dumps(derived, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.write_receipt:
        RECEIPT.write_text(encoded, encoding="utf-8")
    else:
        if not RECEIPT.is_file():
            fail(f"pressure receipt missing: {RECEIPT}")
        recorded = load_json(RECEIPT)
        if recorded != derived:
            fail(
                "recorded ClaimPermission pressure receipt drifted from live derivation"
            )
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
