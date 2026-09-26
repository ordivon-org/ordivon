#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
SCHEMA = STUDY / "schemas/review-lifecycle-observation-v2.schema.json"
MAP = STUDY / "data/review-lifecycle-evidence-map-r2.json"
ARIES = STUDY / "evidence/aries-bounded-core-r1.json"
DISAPERE = STUDY / "evidence/disapere-bounded-core-r1.json"
PEERSUM = STUDY / "evidence/peersum-hf-bounded-core-r1.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def digest_text(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value or "").encode()).hexdigest()


def first_jsonl(path: Path, predicate: Any = None) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and (predicate is None or predicate(row)):
                return row
    raise SystemExit(f"no matching JSONL row: {path}")


def find_message(path: Path, paper_id: str, message_id: str) -> dict[str, Any]:
    return first_jsonl(path, lambda row: row.get("paper_id") == paper_id and row.get("message_id") == message_id)


def rights(license_id: str, commercial: str) -> dict[str, str]:
    return {"licenseId": license_id, "commercialUseStanding": commercial, "redistributionStanding": "source_terms_apply"}


def source(asset: str, snapshot: str, key: str, origin: str) -> dict[str, str]:
    return {"assetId": asset, "snapshotIdentity": snapshot, "recordKey": key, "annotationOrigin": origin}


def main() -> int:
    schema = load(SCHEMA)
    mapping = load(MAP)
    aries = load(ARIES)
    disapere = load(DISAPERE)
    peersum = load(PEERSUM)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    if mapping.get("inherits") != "review-lifecycle-evidence-map-r1":
        raise SystemExit("R2 must explicitly inherit R1")
    if mapping.get("physicalPolicy") != "VIRTUAL_ADAPTER_ONLY_DO_NOT_MERGE_RAW_CORPUS_BYTES":
        raise SystemExit("R2 raw corpus merge was silently authorized")
    if mapping.get("privacy", {}).get("reviewerProfiling") != "NOT_AUTHORIZED":
        raise SystemExit("R2 reviewer profiling boundary drifted")
    if mapping.get("decisionBoundary") != "ACCEPTANCE_METADATA_EXCLUDED_FROM_SHARED_LIFECYCLE_SEMANTICS":
        raise SystemExit("PeerSum acceptance metadata leaked into shared decision semantics")
    assets = {row["assetId"]: row for row in mapping["assets"]}
    if set(assets) != {"aries-bounded-core-r1", "disapere-bounded-core-r1", "peersum-hf-bounded-core-r1"}:
        raise SystemExit("unexpected R2 asset set")
    if assets["disapere-bounded-core-r1"]["commercialUseStanding"] != "blocked_by_source_license":
        raise SystemExit("DISAPERE commercial-use block missing in R2")

    samples: list[dict[str, Any]] = []
    # ARIES R1-compatible samples.
    ar = Path(aries["snapshot"]["root"]) / "derived/jsonl"
    ac = first_jsonl(ar / "comments.jsonl")
    ae = first_jsonl(ar / "edits.jsonl")
    aa = first_jsonl(ar / "alignments.jsonl")
    arights = rights("ODC-BY-1.0", "not_blocked_by_catalog")
    samples.extend([
        {"schemaVersion":2,"observationId":f"aries:concern:{ac['doc_id']}:{ac['comment_id']}","kind":"concern","source":source("aries-bounded-core-r1",aries["snapshot"]["identity"],f"{ac['doc_id']}:{ac['comment_id']}",str(ac.get("annotation") or "upstream")),"rights":arights,"authority":"evidence_only","payload":{"contentDigest":digest_text(ac.get("comment")),"nativeLabels":{"annotation":ac.get("annotation")}}},
        {"schemaVersion":2,"observationId":f"aries:revision:{ae['doc_id']}:{ae['edit_id']}","kind":"revision","source":source("aries-bounded-core-r1",aries["snapshot"]["identity"],f"{ae['doc_id']}:{ae['edit_id']}","derived_identity"),"rights":arights,"authority":"evidence_only","payload":{"revisionId":ae["edit_id"],"representationStanding":"identity_only","nativeLabels":{}}},
        {"schemaVersion":2,"observationId":f"aries:edge:{aa['doc_id']}:{aa['comment_id']}:{aa['edit_id']}:{aa['split']}","kind":"correspondence","source":source("aries-bounded-core-r1",aries["snapshot"]["identity"],f"{aa['doc_id']}:{aa['comment_id']}:{aa['edit_id']}:{aa['split']}","manual" if aa["split"]=="test" else "synthetic"),"rights":arights,"authority":"evidence_only","payload":{"fromObservationId":f"aries:concern:{aa['doc_id']}:{aa['comment_id']}","toObservationId":f"aries:revision:{aa['doc_id']}:{aa['edit_id']}","relationType":"corresponds_to_revision","relationCeiling":"annotated_correspondence_not_causality","nativeLabels":{"label":aa["label"],"split":aa["split"]}}}
    ])

    # DISAPERE R1-compatible samples.
    dr = Path(disapere["snapshot"]["root"]) / "derived/jsonl"
    dc = first_jsonl(dr / "review_sentences.jsonl")
    ds = first_jsonl(dr / "rebuttal_sentences.jsonl")
    dl = first_jsonl(dr / "local_alignment_links.jsonl")
    drights = rights("CC-BY-NC-4.0", "blocked_by_source_license")
    samples.extend([
        {"schemaVersion":2,"observationId":f"disapere:concern:{dc['pair_id']}:{dc['sentence_index']}","kind":"concern","source":source("disapere-bounded-core-r1",disapere["snapshot"]["identity"],f"{dc['pair_id']}:{dc['sentence_index']}","expert_annotation"),"rights":drights,"authority":"evidence_only","payload":{"contentDigest":digest_text(dc.get("text")),"nativeLabels":{key:dc.get(key) for key in ("review_action","fine_review_action","aspect","polarity")}}},
        {"schemaVersion":2,"observationId":f"disapere:response:{ds['pair_id']}:{ds['sentence_index']}","kind":"response","source":source("disapere-bounded-core-r1",disapere["snapshot"]["identity"],f"{ds['pair_id']}:{ds['sentence_index']}","expert_annotation"),"rights":drights,"authority":"evidence_only","payload":{"contentDigest":digest_text(ds.get("text")),"contextKind":ds["alignment_kind"],"nativeLabels":{"rebuttal_stance":ds.get("rebuttal_stance"),"rebuttal_action":ds.get("rebuttal_action")}}},
        {"schemaVersion":2,"observationId":f"disapere:edge:{dl['pair_id']}:{dl['rebuttal_sentence_index']}:{dl['review_sentence_index']}","kind":"correspondence","source":source("disapere-bounded-core-r1",disapere["snapshot"]["identity"],f"{dl['pair_id']}:{dl['rebuttal_sentence_index']}:{dl['review_sentence_index']}","expert_annotation"),"rights":drights,"authority":"evidence_only","payload":{"fromObservationId":f"disapere:response:{dl['pair_id']}:{dl['rebuttal_sentence_index']}","toObservationId":f"disapere:concern:{dl['pair_id']}:{dl['review_sentence_index']}","relationType":"responds_to_explicit_local","relationCeiling":"explicit_context_not_response_adequacy","nativeLabels":{}}}
    ])

    # PeerSum discussion + synthesis samples from exact normalized carrier.
    pr = Path(peersum["snapshot"]["root"]) / "derived/jsonl"
    edge = first_jsonl(pr / "reply_edges.jsonl", lambda row: row.get("parent_kind") == "message")
    child = find_message(pr / "messages.jsonl", edge["paper_id"], edge["child_message_id"])
    parent = find_message(pr / "messages.jsonl", edge["paper_id"], edge["parent_id"])
    paper = first_jsonl(pr / "papers.jsonl", lambda row: row.get("paper_id") == edge["paper_id"])
    prights = rights("Apache-2.0", "not_blocked_by_catalog")
    child_id=f"peersum:message:{child['paper_id']}:{child['message_id']}"
    parent_id=f"peersum:message:{parent['paper_id']}:{parent['message_id']}"
    synthesis_id=f"peersum:synthesis:{paper['paper_id']}:meta_review"
    for row, oid in ((child,child_id),(parent,parent_id)):
        samples.append({"schemaVersion":2,"observationId":oid,"kind":"discussion_message","source":source("peersum-hf-bounded-core-r1",peersum["snapshot"]["identity"],f"{row['paper_id']}:{row['message_id']}","upstream"),"rights":prights,"authority":"evidence_only","payload":{"contentDigest":digest_text(row.get("comment")),"role":row["writer_role"],"nativeLabels":{"rating":row["rating"],"confidence":row["confidence"],"parent_kind":row["parent_kind"]}}})
    samples.append({"schemaVersion":2,"observationId":synthesis_id,"kind":"synthesis","source":source("peersum-hf-bounded-core-r1",peersum["snapshot"]["identity"],f"{paper['paper_id']}:meta_review","upstream"),"rights":prights,"authority":"evidence_only","payload":{"contentDigest":digest_text(paper.get("meta_review")),"synthesisType":"meta_review","nativeLabels":{"split":paper["split"]}}})
    samples.extend([
        {"schemaVersion":2,"observationId":f"peersum:edge:reply:{edge['paper_id']}:{edge['child_message_id']}:{edge['parent_id']}","kind":"correspondence","source":source("peersum-hf-bounded-core-r1",peersum["snapshot"]["identity"],f"reply:{edge['paper_id']}:{edge['child_message_id']}:{edge['parent_id']}","upstream"),"rights":prights,"authority":"evidence_only","payload":{"fromObservationId":child_id,"toObservationId":parent_id,"relationType":"replies_to","relationCeiling":"conversation_topology_not_agreement_or_causality","nativeLabels":{}}},
        {"schemaVersion":2,"observationId":f"peersum:edge:source-set:{child['paper_id']}:{child['message_id']}","kind":"correspondence","source":source("peersum-hf-bounded-core-r1",peersum["snapshot"]["identity"],f"source-set:{child['paper_id']}:{child['message_id']}","upstream"),"rights":prights,"authority":"evidence_only","payload":{"fromObservationId":child_id,"toObservationId":synthesis_id,"relationType":"member_of_synthesis_source_set","relationCeiling":"source_set_membership_not_content_support_or_truth","nativeLabels":{}}}
    ])

    errors=[]
    for sample in samples:
        errors.extend(f"{sample['observationId']}: {err.message}" for err in validator.iter_errors(sample))
        serialized=json.dumps(sample,sort_keys=True)
        if 'paper_acceptance_native' in serialized:
            errors.append(f"acceptance metadata leaked: {sample['observationId']}")
        if '"reviewer"' in serialized or '"annotator"' in serialized:
            errors.append(f"human identity field leaked: {sample['observationId']}")
    if errors:
        raise SystemExit("\n".join(errors))
    result={"schemaVersion":2,"kind":"ordivon.research.review-lifecycle-schema-acceptance","standing":"PASS_VIRTUAL_CROSS_CORPUS_INTERFACE_R2","validatedSampleCount":len(samples),"sourceAssets":sorted(assets),"sharedKinds":mapping["sharedKinds"],"newR2Kinds":["discussion_message","synthesis"],"newR2Relations":["replies_to","member_of_synthesis_source_set"],"decisionBoundary":mapping["decisionBoundary"],"physicalPolicy":mapping["physicalPolicy"],"reviewerProfiling":mapping["privacy"]["reviewerProfiling"],"truthBoundary":"R2 validates typed interoperability and topology/source-set membership only. It does not infer semantic disagreement, source attribution inside a meta-review, synthesis correctness, venue-decision correctness, or cross-corpus causal chains."}
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
