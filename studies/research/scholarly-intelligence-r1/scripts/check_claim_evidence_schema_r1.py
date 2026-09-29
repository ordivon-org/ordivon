#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
SCHEMA = STUDY / "schemas/claim-evidence-observation-v1.schema.json"
MAP = STUDY / "data/claim-evidence-map-r1.json"
RECEIPT = STUDY / "evidence/context24-identity-core-r1.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value or "").encode()).hexdigest()


def first_jsonl(path: Path, predicate: Any = None) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and (predicate is None or predicate(row)):
                return row
    raise SystemExit(f"no matching row: {path}")


def src(snapshot: str, key: str, origin: str, gold: str) -> dict[str, str]:
    return {
        "assetId": "context24-identity-core-r1",
        "snapshotIdentity": snapshot,
        "recordKey": key,
        "annotationOrigin": origin,
        "goldAvailability": gold,
    }


def rights() -> dict[str, str]:
    return {"licenseId": "CC-BY-4.0", "redistributionStanding": "source_terms_apply"}


def claim_observation(row: dict[str, Any], snapshot: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "observationId": f"context24:claim:{row['claim_instance_id']}",
        "kind": "claim",
        "source": src(
            snapshot, row["claim_instance_id"], "source_claim", row["gold_availability"]
        ),
        "rights": rights(),
        "authority": "evidence_only",
        "payload": {
            "contentDigest": digest(row["claim"]),
            "nativeId": row["native_id"],
            "citekey": row["citekey"],
            "dataset": row["dataset"],
            "identityStanding": "source_coordinate_authority_native_id_nonunique",
            "nativeLabels": {
                "task": row["task"],
                "split": row["split"],
                "nativeIdMultiplicity": row["nativeIdMultiplicity"],
                "nativeIdCollisionClass": row["nativeIdCollisionClass"],
            },
        },
    }


def main() -> int:
    schema = load(SCHEMA)
    mapping = load(MAP)
    receipt = load(RECEIPT)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    if mapping.get("truthRole") != "claim-grounding-interface-not-scientific-truth":
        raise SystemExit("claim-evidence truth boundary drifted")
    if (
        mapping.get("goldPolicy", {}).get("challengeTest")
        != "withheld_do_not_infer_or_fabricate"
    ):
        raise SystemExit("test-gold boundary drifted")
    if mapping.get("contentExpansion") != {
        "figureTablePixels": "NOT_BOUND_R1",
        "captions": "NOT_BOUND_R1",
        "fullText": "NOT_BOUND_R1",
        "silverCorpus": "NOT_BOUND_R1",
    }:
        raise SystemExit("R1 content expansion silently promoted")
    root = Path(receipt["snapshot"]["root"]) / "derived/jsonl"
    snapshot = receipt["snapshot"]["identity"]
    e = first_jsonl(root / "task1_evidence_links.jsonl")
    c1 = first_jsonl(
        root / "claims.jsonl",
        lambda r: r["claim_instance_id"] == e["claim_instance_id"],
    )
    m = first_jsonl(root / "task2_method_contexts.jsonl")
    c2 = first_jsonl(
        root / "claims.jsonl",
        lambda r: r["claim_instance_id"] == m["claim_instance_id"],
    )
    test = first_jsonl(
        root / "claims.jsonl", lambda r: r["task"] == "task1" and r["split"] == "test"
    )
    collision = first_jsonl(
        root / "claims.jsonl", lambda r: r["nativeIdCollisionClass"] != "none"
    )
    c1id = f"context24:claim:{c1['claim_instance_id']}"
    evid = f"context24:evidence:{e['citekey']}:{e['evidence_label']}"
    c2id = f"context24:claim:{c2['claim_instance_id']}"
    mid = f"context24:method-context:{m['claim_instance_id']}:{m['context_index']}"
    samples = [
        claim_observation(c1, snapshot),
        claim_observation(c2, snapshot),
        claim_observation(test, snapshot),
        claim_observation(collision, snapshot),
        {
            "schemaVersion": 1,
            "observationId": evid,
            "kind": "evidence_identity",
            "source": src(
                snapshot,
                f"{e['citekey']}:{e['evidence_label']}",
                "derived_identity",
                "available",
            ),
            "rights": rights(),
            "authority": "evidence_only",
            "payload": {
                "evidenceLabel": e["evidence_label"],
                "evidenceKind": e["evidence_kind"],
                "representationStanding": "identity_only",
                "nativeLabels": {"dataset": e["dataset"]},
            },
        },
        {
            "schemaVersion": 1,
            "observationId": f"context24:edge:evidence:{e['claim_instance_id']}:{e['evidence_index']}",
            "kind": "correspondence",
            "source": src(
                snapshot,
                f"{e['claim_instance_id']}:{e['evidence_index']}",
                "gold_annotation",
                "available",
            ),
            "rights": rights(),
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": c1id,
                "toObservationId": evid,
                "relationType": "annotated_supporting_evidence_identity",
                "relationCeiling": "annotation_not_scientific_truth_or_causality",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 1,
            "observationId": mid,
            "kind": "method_context",
            "source": src(
                snapshot,
                f"{m['claim_instance_id']}:{m['context_index']}",
                "gold_annotation",
                "available",
            ),
            "rights": rights(),
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(m["context_text"]),
                "representationStanding": "content_bound",
                "nativeLabels": {"citekey": m["citekey"], "dataset": m["dataset"]},
            },
        },
        {
            "schemaVersion": 1,
            "observationId": f"context24:edge:method:{m['claim_instance_id']}:{m['context_index']}",
            "kind": "correspondence",
            "source": src(
                snapshot,
                f"{m['claim_instance_id']}:{m['context_index']}",
                "gold_annotation",
                "available",
            ),
            "rights": rights(),
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": c2id,
                "toObservationId": mid,
                "relationType": "annotated_method_context",
                "relationCeiling": "method_context_annotation_not_claim_validity",
                "nativeLabels": {},
            },
        },
    ]
    errors = []
    for sample in samples:
        errors.extend(
            f"{sample['observationId']}: {err.message}"
            for err in validator.iter_errors(sample)
        )
    if errors:
        raise SystemExit("\n".join(errors))
    if test["gold_availability"] != "withheld_challenge_test":
        raise SystemExit("test sample unexpectedly has public gold")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.claim-evidence-schema-acceptance",
        "standing": "PASS_CLAIM_EVIDENCE_INTERFACE_R1",
        "validatedSampleCount": len(samples),
        "sourceAsset": "context24-identity-core-r1",
        "sharedKinds": mapping["sharedKinds"],
        "testGoldStanding": "WITHHELD_NOT_FABRICATED",
        "evidenceRepresentationStanding": "IDENTITY_ONLY_R1",
        "truthBoundary": "Interface validation proves typed annotation interoperability only. It does not establish scientific truth, causal support, evidential sufficiency, method adequacy, or hidden challenge-test labels.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
