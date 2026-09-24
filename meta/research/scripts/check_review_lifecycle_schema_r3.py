#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

META = Path(__file__).resolve().parents[2]
SCHEMA = META / "research/schemas/review-lifecycle-observation-v3.schema.json"
MAP = META / "research/data/review-lifecycle-evidence-map-r3.json"
ARIES = META / "research/evidence/aries-bounded-core-r1.json"
RESP = META / "research/evidence/aries-review-response-core-r1.json"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def digest(v):
    return "sha256:" + hashlib.sha256(str(v or "").encode()).hexdigest()


def rows(p):
    with p.open(encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def rights():
    return {
        "licenseId": "ODC-BY-1.0",
        "commercialUseStanding": "not_blocked_by_catalog",
        "redistributionStanding": "source_terms_apply",
    }


def main():
    schema = load(SCHEMA)
    mapping = load(MAP)
    a = load(ARIES)
    r = load(RESP)
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    if (
        mapping.get("truthRole")
        != "cross-corpus-interface-map-not-unified-scientific-truth"
    ):
        raise SystemExit("truth role drifted")
    if (
        "response -> revision semantic or causal linkage despite same-paper lifecycle identity"
        not in mapping["composition"]["notYetIdentified"]
    ):
        raise SystemExit("response-revision gap silently closed")
    root = Path(r["snapshot"]["root"])
    parent = Path(a["snapshot"]["root"])
    fork = next(
        x
        for x in rows(root / "derived/jsonl/lifecycle_forks.jsonl")
        if x["has_both_branches"]
    )
    doc = str(fork["doc_id"])
    cid = int(fork["comment_id"])
    rid = str(fork["review_id"])
    c = {
        (str(x["doc_id"]), int(x["comment_id"])): x
        for x in rows(parent / "derived/jsonl/comments.jsonl")
    }[(doc, cid)]
    rv = {
        str(x["review_id"]): x
        for x in rows(root / "derived/jsonl/official_reviews.jsonl")
    }[rid]
    resp = next(
        x
        for x in rows(root / "derived/jsonl/author_responses.jsonl")
        if str(x["root_review_id"]) == rid and x["direct_to_review"]
    )
    al = next(
        x
        for x in rows(parent / "derived/jsonl/alignments.jsonl")
        if str(x["doc_id"]) == doc
        and int(x["comment_id"]) == cid
        and int(x["label"]) == 1
    )
    ed = {
        (str(x["doc_id"]), int(x["edit_id"])): x
        for x in rows(parent / "derived/jsonl/edits.jsonl")
    }[(doc, int(al["edit_id"]))]
    sid = r["snapshot"]["identity"]
    psid = a["snapshot"]["identity"]
    R = rights()
    concern = f"aries:concern:{doc}:{cid}"
    review = f"aries:review:{rid}"
    response = f"aries:response:{resp['response_id']}"
    revision = f"aries:revision:{doc}:{ed['edit_id']}"
    samples = [
        {
            "schemaVersion": 3,
            "observationId": concern,
            "kind": "concern",
            "source": {
                "assetId": "aries-bounded-core-r1",
                "snapshotIdentity": psid,
                "recordKey": f"{doc}:{cid}",
                "annotationOrigin": "manual",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(c.get("comment")),
                "nativeLabels": {"annotation": "manual"},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": review,
            "kind": "discussion_message",
            "source": {
                "assetId": "aries-review-response-core-r1",
                "snapshotIdentity": sid,
                "recordKey": rid,
                "annotationOrigin": "upstream",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(rv.get("review_text")),
                "role": "official_review",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": response,
            "kind": "response",
            "source": {
                "assetId": "aries-review-response-core-r1",
                "snapshotIdentity": sid,
                "recordKey": str(resp["response_id"]),
                "annotationOrigin": "upstream",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "contentDigest": digest(resp.get("response_text")),
                "contextKind": "review_thread",
                "nativeLabels": {"direct_to_review": True},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": revision,
            "kind": "revision",
            "source": {
                "assetId": "aries-bounded-core-r1",
                "snapshotIdentity": psid,
                "recordKey": f"{doc}:{ed['edit_id']}",
                "annotationOrigin": "derived_identity",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "revisionId": ed["edit_id"],
                "representationStanding": "identity_only",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": f"aries:source-review-edge:{doc}:{cid}:{rid}",
            "kind": "correspondence",
            "source": {
                "assetId": "aries-review-response-core-r1",
                "snapshotIdentity": sid,
                "recordKey": f"{doc}:{cid}:{rid}",
                "annotationOrigin": "upstream",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": concern,
                "toObservationId": review,
                "relationType": "source_review_for_concern",
                "relationCeiling": "source_review_identity_not_span_alignment_or_resolution",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": f"aries:reply-edge:{resp['response_id']}:{rid}",
            "kind": "correspondence",
            "source": {
                "assetId": "aries-review-response-core-r1",
                "snapshotIdentity": sid,
                "recordKey": f"{resp['response_id']}:{rid}",
                "annotationOrigin": "upstream",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": response,
                "toObservationId": review,
                "relationType": "replies_to",
                "relationCeiling": "conversation_topology_not_agreement_or_causality",
                "nativeLabels": {},
            },
        },
        {
            "schemaVersion": 3,
            "observationId": f"aries:revision-edge:{doc}:{cid}:{ed['edit_id']}",
            "kind": "correspondence",
            "source": {
                "assetId": "aries-bounded-core-r1",
                "snapshotIdentity": psid,
                "recordKey": f"{doc}:{cid}:{ed['edit_id']}",
                "annotationOrigin": "manual",
            },
            "rights": R,
            "authority": "evidence_only",
            "payload": {
                "fromObservationId": concern,
                "toObservationId": revision,
                "relationType": "corresponds_to_revision",
                "relationCeiling": "annotated_correspondence_not_causality",
                "nativeLabels": {"split": "test", "label": 1},
            },
        },
    ]
    errors = [
        f"{s['observationId']}: {e.message}" for s in samples for e in v.iter_errors(s)
    ]
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        json.dumps(
            {
                "schemaVersion": 3,
                "kind": "ordivon.research.review-lifecycle-schema-acceptance",
                "standing": "PASS_SAME_AUTHORITY_ARIES_LIFECYCLE_FORK_R3",
                "validatedSampleCount": len(samples),
                "sourceAssets": [
                    "aries-bounded-core-r1",
                    "aries-review-response-core-r1",
                    "disapere-bounded-core-r1",
                    "peersum-hf-bounded-core-r1",
                ],
                "newR3Relations": ["source_review_for_concern"],
                "sameAuthorityFork": {
                    "manualConcerns": 196,
                    "withReviewResponseContext": 196,
                    "withPositiveRevisionCorrespondence": 87,
                    "withBothBranches": 87,
                },
                "unresolved": "Response->Revision semantic/causal linkage remains NOT_IDENTIFIED",
                "truthBoundary": "R3 proves exact concern source-review identity, reply topology, and separate revision correspondence under ARIES. It does not prove concern-specific response adequacy or a Response->Revision semantic/causal edge.",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
