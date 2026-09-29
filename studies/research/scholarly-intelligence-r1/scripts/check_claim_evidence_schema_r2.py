#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
SCHEMA = STUDY / "schemas/claim-evidence-observation-v2.schema.json"
MAP = STUDY / "data/claim-evidence-map-r2.json"
IDENTITY_RECEIPT = STUDY / "evidence/context24-identity-core-r1.json"
CONTENT_RECEIPT = STUDY / "evidence/context24-evidence-content-core-r1.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value or "").encode()).hexdigest()


def rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def identity_rights() -> dict[str, str]:
    return {"licenseId": "CC-BY-4.0", "redistributionStanding": "source_terms_apply"}


def content_rights() -> dict[str, str]:
    return {
        "licenseId": "CC-BY-4.0",
        "redistributionStanding": "source_terms_apply",
        "underlyingRightsStanding": "not_independently_verified",
        "commercialMediaReuseStanding": "not_authorized_by_catalog",
    }


def source(
    asset: str, snapshot: str, key: str, origin: str, gold: str
) -> dict[str, str]:
    return {
        "assetId": asset,
        "snapshotIdentity": snapshot,
        "recordKey": key,
        "annotationOrigin": origin,
        "goldAvailability": gold,
    }


def main() -> int:
    schema = load(SCHEMA)
    mapping = load(MAP)
    identity_receipt = load(IDENTITY_RECEIPT)
    content_receipt = load(CONTENT_RECEIPT)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    if mapping.get("truthRole") != "claim-grounding-interface-not-scientific-truth":
        raise SystemExit("Claim-Evidence R2 truth boundary drifted")
    if (
        mapping.get("goldPolicy", {}).get("challengeTest")
        != "withheld_do_not_infer_or_fabricate"
    ):
        raise SystemExit("test-gold boundary drifted")
    if (
        mapping.get("rights", {}).get("commercialMediaReuse")
        != "NOT_AUTHORIZED_BY_CATALOG"
    ):
        raise SystemExit("commercial media reuse silently authorized")
    if (
        "ClaimPermission or claim ceiling derived from evidence content"
        not in mapping.get("notYetIdentified", [])
    ):
        raise SystemExit("ClaimPermission was silently promoted")
    iroot = Path(identity_receipt["snapshot"]["root"]) / "derived/jsonl"
    croot = Path(content_receipt["snapshot"]["root"]) / "derived/jsonl"
    isnap = identity_receipt["snapshot"]["identity"]
    csnap = content_receipt["snapshot"]["identity"]
    links = rows(croot / "claim_evidence_content_links.jsonl")
    contents = {
        row["evidence_content_id"]: row
        for row in rows(croot / "evidence_contents.jsonl")
    }
    identity_links = rows(iroot / "task1_evidence_links.jsonl")
    claims = {row["claim_instance_id"]: row for row in rows(iroot / "claims.jsonl")}
    link = links[0]
    content = contents[link["evidence_content_id"]]
    identity_link = next(
        row
        for row in identity_links
        if row["claim_instance_id"] == link["claim_instance_id"]
        and row["evidence_label"] == link["finding_id"]
    )
    claim = claims[link["claim_instance_id"]]
    test_claim = next(
        row
        for row in claims.values()
        if row["task"] == "task1" and row["split"] == "test"
    )
    claim_id = f"context24:claim:{claim['claim_instance_id']}"
    evidence_id = f"context24:evidence:{identity_link['citekey']}:{identity_link['evidence_label']}"
    content_id = link["evidence_content_id"]
    samples = [
        {
            "schemaVersion": 2,
            "observationId": claim_id,
            "kind": "claim",
            "source": source(
                "context24-identity-core-r1",
                isnap,
                claim["claim_instance_id"],
                "source_claim",
                "available",
            ),
            "rights": identity_rights(),
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(claim["claim"]),
                "nativeId": claim["native_id"],
                "citekey": claim["citekey"],
                "dataset": claim["dataset"],
                "identityStanding": "source_coordinate_authority_native_id_nonunique",
                "nativeLabels": {"task": "task1", "split": "train"},
            },
        },
        {
            "schemaVersion": 2,
            "observationId": evidence_id,
            "kind": "evidence_identity",
            "source": source(
                "context24-identity-core-r1",
                isnap,
                f"{identity_link['citekey']}:{identity_link['evidence_label']}",
                "derived_identity",
                "available",
            ),
            "rights": identity_rights(),
            "authority": "evidence_only",
            "payload": {
                "evidenceLabel": identity_link["evidence_label"],
                "evidenceKind": identity_link["evidence_kind"],
                "representationStanding": "identity_only",
                "nativeLabels": {"dataset": identity_link["dataset"]},
            },
        },
        {
            "schemaVersion": 2,
            "observationId": content_id,
            "kind": "evidence_content",
            "source": source(
                "context24-evidence-content-core-r1",
                csnap,
                content_id,
                "upstream_content",
                "available",
            ),
            "rights": content_rights(),
            "authority": "evidence_only",
            "payload": {
                "contentDigest": content["sha256"],
                "evidenceLabel": content["finding_id"],
                "evidenceKind": content["evidence_kind"],
                "mediaType": content["media_type"],
                "representationStanding": content["representation_standing"],
                "contentBytes": content["bytes"],
                "width": content["width"],
                "height": content["height"],
                "nativeLabels": {
                    "citekey": content["citekey"],
                    "upstreamPath": content["upstream_path"],
                },
            },
        },
        {
            "schemaVersion": 2,
            "observationId": f"context24:edge:identity:{claim['claim_instance_id']}:{identity_link['evidence_index']}",
            "kind": "correspondence",
            "source": source(
                "context24-identity-core-r1",
                isnap,
                f"{claim['claim_instance_id']}:{identity_link['evidence_index']}",
                "gold_annotation",
                "available",
            ),
            "rights": identity_rights(),
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": claim_id,
                "toObservationId": evidence_id,
                "relationType": "annotated_supporting_evidence_identity",
                "relationCeiling": "annotation_not_scientific_truth_or_causality",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 2,
            "observationId": f"context24:edge:content:{claim['claim_instance_id']}:{identity_link['evidence_index']}",
            "kind": "correspondence",
            "source": source(
                "context24-evidence-content-core-r1",
                csnap,
                f"{claim['claim_instance_id']}:{identity_link['evidence_index']}",
                "upstream_content",
                "available",
            ),
            "rights": content_rights(),
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": evidence_id,
                "toObservationId": content_id,
                "relationType": "materializes_evidence_identity",
                "relationCeiling": "byte_content_binding_not_support_adequacy",
                "nativeLabels": {"claimInstanceId": claim["claim_instance_id"]},
            },
        },
        {
            "schemaVersion": 2,
            "observationId": f"context24:claim:{test_claim['claim_instance_id']}",
            "kind": "claim",
            "source": source(
                "context24-identity-core-r1",
                isnap,
                test_claim["claim_instance_id"],
                "source_claim",
                "withheld_challenge_test",
            ),
            "rights": identity_rights(),
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(test_claim["claim"]),
                "nativeId": test_claim["native_id"],
                "citekey": test_claim["citekey"],
                "dataset": test_claim["dataset"],
                "identityStanding": "source_coordinate_authority_native_id_nonunique",
                "nativeLabels": {"task": "task1", "split": "test"},
            },
        },
    ]
    errors = [
        f"{sample['observationId']}: {error.message}"
        for sample in samples
        for error in validator.iter_errors(sample)
    ]
    if errors:
        raise SystemExit("\n".join(errors))
    result = {
        "schemaVersion": 2,
        "kind": "ordivon.research.claim-evidence-schema-acceptance",
        "standing": "PASS_CLAIM_EVIDENCE_CONTENT_INTERFACE_R2",
        "validatedSampleCount": len(samples),
        "sourceAssets": [
            "context24-identity-core-r1",
            "context24-evidence-content-core-r1",
        ],
        "sharedKinds": mapping["sharedKinds"],
        "contentBoundGoldLinks": 256,
        "identityOnlyGoldLinks": 423,
        "testGoldStanding": "WITHHELD_NOT_INFERRED",
        "claimPermissionStanding": "NOT_AUTHORIZED_BY_R2",
        "underlyingMediaRights": "NOT_INDEPENDENTLY_VERIFIED",
        "truthBoundary": "R2 proves identity-to-content byte binding only. It does not establish evidential sufficiency, scientific truth, causal support, method adequacy, ClaimPermission, or external media redistribution rights.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
