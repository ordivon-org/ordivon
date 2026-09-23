#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

META = Path(__file__).resolve().parents[2]
SCHEMA = META / "research/schemas/review-lifecycle-observation-v1.schema.json"
MAP = META / "research/data/review-lifecycle-evidence-map-r1.json"
ARIES = META / "research/evidence/aries-bounded-core-r1.json"
DISAPERE = META / "research/evidence/disapere-bounded-core-r1.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def digest_text(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value or "").encode()).hexdigest()


def read_first_jsonl(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    return value
    raise SystemExit(f"empty JSONL: {path}")


def rights(license_id: str, commercial: str) -> dict[str, str]:
    return {
        "licenseId": license_id,
        "commercialUseStanding": commercial,
        "redistributionStanding": "source_terms_apply",
    }


def main() -> int:
    schema = load(SCHEMA)
    mapping = load(MAP)
    aries_receipt = load(ARIES)
    disapere_receipt = load(DISAPERE)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    if mapping.get("truthRole") != "cross-corpus-interface-map-not-unified-scientific-truth":
        raise SystemExit("review-lifecycle map truth boundary drifted")
    if mapping.get("physicalPolicy") != "VIRTUAL_ADAPTER_ONLY_DO_NOT_MERGE_RAW_CORPUS_BYTES":
        raise SystemExit("raw corpus merge was silently authorized")
    if mapping.get("privacy", {}).get("reviewerProfiling") != "NOT_AUTHORIZED":
        raise SystemExit("reviewer profiling boundary drifted")

    assets = {row["assetId"]: row for row in mapping["assets"]}
    if set(assets) != {"aries-bounded-core-r1", "disapere-bounded-core-r1"}:
        raise SystemExit("unexpected R1 review-lifecycle assets")
    if assets["disapere-bounded-core-r1"]["commercialUseStanding"] != "blocked_by_source_license":
        raise SystemExit("DISAPERE commercial-use block missing")

    aries_root = Path(aries_receipt["snapshot"]["root"])
    disapere_root = Path(disapere_receipt["snapshot"]["root"])
    a_comment = read_first_jsonl(aries_root / "derived/jsonl/comments.jsonl")
    a_edit = read_first_jsonl(aries_root / "derived/jsonl/edits.jsonl")
    a_alignment = read_first_jsonl(aries_root / "derived/jsonl/alignments.jsonl")
    d_review = read_first_jsonl(disapere_root / "derived/jsonl/review_sentences.jsonl")
    d_response = read_first_jsonl(disapere_root / "derived/jsonl/rebuttal_sentences.jsonl")
    d_link = read_first_jsonl(disapere_root / "derived/jsonl/local_alignment_links.jsonl")

    aries_source = aries_receipt["snapshot"]["identity"]
    disapere_source = disapere_receipt["snapshot"]["identity"]
    aries_rights = rights("ODC-BY-1.0", "not_blocked_by_catalog")
    disapere_rights = rights("CC-BY-NC-4.0", "blocked_by_source_license")

    a_concern_id = f"aries:concern:{a_comment['doc_id']}:{a_comment['comment_id']}"
    a_revision_id = f"aries:revision:{a_edit['doc_id']}:{a_edit['edit_id']}"
    samples: list[dict[str, Any]] = [
        {
            "schemaVersion": 1,
            "observationId": a_concern_id,
            "kind": "concern",
            "source": {"assetId": "aries-bounded-core-r1", "snapshotIdentity": aries_source, "recordKey": f"{a_comment['doc_id']}:{a_comment['comment_id']}", "annotationOrigin": str(a_comment.get("annotation") or "upstream")},
            "rights": aries_rights,
            "authority": "evidence_only",
            "payload": {"contentDigest": digest_text(a_comment.get("comment")), "nativeLabels": {"annotation": a_comment.get("annotation")}},
        },
        {
            "schemaVersion": 1,
            "observationId": a_revision_id,
            "kind": "revision",
            "source": {"assetId": "aries-bounded-core-r1", "snapshotIdentity": aries_source, "recordKey": f"{a_edit['doc_id']}:{a_edit['edit_id']}", "annotationOrigin": "derived_identity"},
            "rights": aries_rights,
            "authority": "evidence_only",
            "payload": {"revisionId": a_edit["edit_id"], "representationStanding": "identity_only", "nativeLabels": {}},
        },
        {
            "schemaVersion": 1,
            "observationId": f"aries:edge:{a_alignment['doc_id']}:{a_alignment['comment_id']}:{a_alignment['edit_id']}:{a_alignment['split']}",
            "kind": "correspondence",
            "source": {"assetId": "aries-bounded-core-r1", "snapshotIdentity": aries_source, "recordKey": f"{a_alignment['doc_id']}:{a_alignment['comment_id']}:{a_alignment['edit_id']}:{a_alignment['split']}", "annotationOrigin": "manual" if a_alignment["split"] == "test" else "synthetic"},
            "rights": aries_rights,
            "authority": "evidence_only",
            "payload": {"fromObservationId": f"aries:concern:{a_alignment['doc_id']}:{a_alignment['comment_id']}", "toObservationId": f"aries:revision:{a_alignment['doc_id']}:{a_alignment['edit_id']}", "relationType": "corresponds_to_revision", "relationCeiling": "annotated_correspondence_not_causality", "nativeLabels": {"label": a_alignment["label"], "split": a_alignment["split"]}},
        },
    ]

    d_concern_id = f"disapere:concern:{d_review['pair_id']}:{d_review['sentence_index']}"
    d_response_id = f"disapere:response:{d_response['pair_id']}:{d_response['sentence_index']}"
    samples.extend([
        {
            "schemaVersion": 1,
            "observationId": d_concern_id,
            "kind": "concern",
            "source": {"assetId": "disapere-bounded-core-r1", "snapshotIdentity": disapere_source, "recordKey": f"{d_review['pair_id']}:{d_review['sentence_index']}", "annotationOrigin": "expert_annotation"},
            "rights": disapere_rights,
            "authority": "evidence_only",
            "payload": {"contentDigest": digest_text(d_review.get("text")), "nativeLabels": {key: d_review.get(key) for key in ("review_action", "fine_review_action", "aspect", "polarity")}},
        },
        {
            "schemaVersion": 1,
            "observationId": d_response_id,
            "kind": "response",
            "source": {"assetId": "disapere-bounded-core-r1", "snapshotIdentity": disapere_source, "recordKey": f"{d_response['pair_id']}:{d_response['sentence_index']}", "annotationOrigin": "expert_annotation"},
            "rights": disapere_rights,
            "authority": "evidence_only",
            "payload": {"contentDigest": digest_text(d_response.get("text")), "contextKind": d_response["alignment_kind"], "nativeLabels": {"rebuttal_stance": d_response.get("rebuttal_stance"), "rebuttal_action": d_response.get("rebuttal_action")}},
        },
        {
            "schemaVersion": 1,
            "observationId": f"disapere:edge:{d_link['pair_id']}:{d_link['rebuttal_sentence_index']}:{d_link['review_sentence_index']}",
            "kind": "correspondence",
            "source": {"assetId": "disapere-bounded-core-r1", "snapshotIdentity": disapere_source, "recordKey": f"{d_link['pair_id']}:{d_link['rebuttal_sentence_index']}:{d_link['review_sentence_index']}", "annotationOrigin": "expert_annotation"},
            "rights": disapere_rights,
            "authority": "evidence_only",
            "payload": {"fromObservationId": f"disapere:response:{d_link['pair_id']}:{d_link['rebuttal_sentence_index']}", "toObservationId": f"disapere:concern:{d_link['pair_id']}:{d_link['review_sentence_index']}", "relationType": "responds_to_explicit_local", "relationCeiling": "explicit_context_not_response_adequacy", "nativeLabels": {}},
        },
    ])

    errors: list[str] = []
    for sample in samples:
        for error in validator.iter_errors(sample):
            errors.append(f"{sample['observationId']}: {error.message}")
        serialized = json.dumps(sample, sort_keys=True)
        if '"reviewer"' in serialized or '"annotator"' in serialized:
            errors.append(f"identity field leaked: {sample['observationId']}")
    if errors:
        raise SystemExit("\n".join(errors))

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.review-lifecycle-schema-acceptance",
        "standing": "PASS_VIRTUAL_CROSS_CORPUS_INTERFACE",
        "validatedSampleCount": len(samples),
        "sourceAssets": sorted(assets),
        "sharedKinds": mapping["sharedKinds"],
        "physicalPolicy": mapping["physicalPolicy"],
        "reviewerProfiling": mapping["privacy"]["reviewerProfiling"],
        "disapereCommercialUse": assets["disapere-bounded-core-r1"]["commercialUseStanding"],
        "truthBoundary": "Schema validation proves interface compatibility only. It does not identify cross-corpus document identity, causal chains, response adequacy, revision quality, reviewer truth, or venue authority."
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
