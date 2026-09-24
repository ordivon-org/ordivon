#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
RECEIPT = META / "research/evidence/aries-semantic-content-core-r1.json"
BASELINE = META / "research/evidence/aries-response-revision-candidate-space-r1.json"
CATALOG = META / "research/data/scholarly-data-catalog-r1.json"

EXPECTED_ROOT = Path(
    "/root/projects/ordivon-corpora/scholarly-data/aries/"
    "aries-semantic-content-core-r1-20260924"
)
EXPECTED_IDENTITY = (
    "sha256:aee4b640155c01f8c0e1f677494356f87944671e4a5c7079de8c86ee11fb0848"
)
EXPECTED_SOURCE_SHA = (
    "sha256:c0b5c50afde1a819788bc679b3751167c65ea3b5bc283c30f2b069d21c7b201c"
)
EXPECTED_RELATION = "NO_GOLD_RESPONSE_EDIT_RELATION_IN_SOURCE_ASSETS"
EXPECTED_CEILING = "CANDIDATE_RESPONSE_EDIT_PAIR_NOT_GOLD_NOT_CAUSAL"
EXPECTED_COUNTS = {
    "selectedDocuments": 36,
    "requestedPdfIdentities": 72,
    "extractedPdfIdentities": 72,
    "paragraphs": 8518,
    "semanticEdits": 4718,
    "positiveEditLinkRows": 182,
    "uniquePositiveEdits": 131,
    "responseRevisionCandidateRows": 248,
    "candidateConcernGroups": 87,
    "candidateDocuments": 36,
    "uniqueResponsesInCandidateSpace": 49,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                fail(f"expected JSON object at {path}:{line_number}")
            yield value


def main() -> int:
    receipt = load(RECEIPT)
    baseline = load(BASELINE)
    catalog = load(CATALOG)
    if receipt.get("status") != "MATERIALIZED_BOUNDED_SEMANTIC_CONTENT_CORE_PASS":
        fail("ARIES semantic-content admission standing drifted")
    if (
        receipt.get("truthRole")
        != "external-paper-text-and-candidate-space-evidence-not-response-revision-gold"
    ):
        fail("ARIES semantic-content truth boundary drifted")
    if receipt.get("relationStanding") != EXPECTED_RELATION:
        fail("ARIES response->revision relation was silently promoted")
    if (
        receipt.get("annotationReadiness")
        != "READY_FOR_INDEPENDENT_SEMANTIC_ANNOTATION"
    ):
        fail("ARIES semantic annotation readiness drifted")
    if (
        receipt.get("modelTrainingStanding")
        != "NOT_AUTHORIZED_WITHOUT_SEPARATELY_VALIDATED_RESPONSE_EDIT_RELATION"
    ):
        fail("ARIES model-training gate was weakened")

    root = Path(receipt["snapshot"]["root"])
    if root != EXPECTED_ROOT or not root.is_dir():
        fail("ARIES semantic-content root drifted")
    if receipt["snapshot"]["identity"] != EXPECTED_IDENTITY:
        fail("ARIES semantic-content snapshot identity drifted")
    if receipt["source"]["bytes"] != 93627656:
        fail("ARIES S2ORC carrier size drifted")
    if receipt["source"]["sha256"] != EXPECTED_SOURCE_SHA:
        fail("ARIES S2ORC source digest declaration drifted")
    if (root / "raw/s2orc.tar.gz").stat().st_size != 93627656:
        fail("ARIES S2ORC local carrier size drifted")
    if sha256(root / "raw/s2orc.tar.gz") != EXPECTED_SOURCE_SHA:
        fail("ARIES S2ORC local carrier bytes drifted")
    if sha256(root / "raw/LICENSE") != receipt["source"]["licenseFileSha256"]:
        fail("ARIES semantic-content license bytes drifted")

    compact = {
        "SNAPSHOT_MANIFEST_R1.json": "snapshotManifestSha256",
        "SELECTION_MANIFEST_R1.json": "selectionManifestSha256",
        "EXTRACTION_MANIFEST_R1.json": "extractionManifestSha256",
        "SCHEMA_CENSUS_R1.json": "schemaCensusSha256",
        "NORMALIZATION_SUMMARY_R1.json": "normalizationSummarySha256",
        "ANALYTICAL_BUILD_RECEIPT_R1.json": "analyticalBuildReceiptSha256",
        "CANDIDATE_SPACE_BASELINE_R1.json": "candidateSpaceBaselineSha256",
    }
    for rel, key in compact.items():
        if sha256(root / rel) != receipt["snapshot"][key]:
            fail(f"ARIES semantic-content compact digest drift: {rel}")

    manifest = load(root / "SNAPSHOT_MANIFEST_R1.json")
    if manifest.get("canonicalFileCount") != 72:
        fail("ARIES selected S2ORC file count drifted")
    if (
        manifest.get("physicalPolicy")
        != "RAW_UPSTREAM_CARRIER_OUTSIDE_GIT_SELECTED_PDF_JSON_ONLY_NORMALIZED"
    ):
        fail("ARIES semantic-content physical policy drifted")
    rights = manifest.get("rights", {})
    expected_rights = {
        "datasetLicenseObserved": "ODC-BY-1.0",
        "underlyingPaperTextRights": "NOT_INDEPENDENTLY_VERIFIED",
        "externalTextRedistribution": "NOT_AUTHORIZED_BY_CATALOG",
        "commercialPaperTextReuse": "NOT_AUTHORIZED_BY_CATALOG",
    }
    if rights != expected_rights or receipt.get("rights") != expected_rights:
        fail("ARIES paper-text rights boundary drifted")
    for row in manifest.get("canonicalFiles", []):
        path = root / row["path"]
        if (
            not path.is_file()
            or path.stat().st_size != row["bytes"]
            or sha256(path) != row["sha256"]
        ):
            fail(f"ARIES selected S2ORC file drifted: {row.get('path')}")

    selection = load(root / "SELECTION_MANIFEST_R1.json")
    extraction = load(root / "EXTRACTION_MANIFEST_R1.json")
    if selection.get("documentCount") != 36:
        fail("ARIES semantic-content document selection drifted")
    if (
        extraction.get("requestedPdfIdentities") != 72
        or extraction.get("extractedPdfIdentities") != 72
    ):
        fail("ARIES semantic-content extraction cardinality drifted")
    if extraction.get("missingPdfIdentities") != []:
        fail("ARIES semantic-content extraction is incomplete")

    census = load(root / "SCHEMA_CENSUS_R1.json")
    if census.get("status") != "PASS_BOUNDED_SEMANTIC_CONTENT_AND_CANDIDATE_SPACE":
        fail("ARIES semantic-content schema census not accepted")
    if (
        census.get("counts") != EXPECTED_COUNTS
        or receipt.get("counts") != EXPECTED_COUNTS
    ):
        fail("ARIES semantic-content exact counts drifted")
    if census.get("relationStanding") != EXPECTED_RELATION:
        fail("ARIES semantic-content census relation standing drifted")
    if census.get("indexIntegrity") != {
        "missingPdfPairs": 0,
        "sourceOutOfBounds": 0,
        "targetOutOfBounds": 0,
    }:
        fail("ARIES semantic-content edit-index integrity failed")
    if any(census.get("textIntegrity", {}).values()):
        fail("ARIES semantic-content text/candidate integrity failed")
    ambiguity = census["candidateAmbiguity"]
    if (
        ambiguity.get("singleCandidateConcerns") != 34
        or ambiguity.get("ambiguousConcerns") != 53
    ):
        fail("ARIES candidate ambiguity counts drifted")
    if ambiguity.get("totalCandidatePairs") != 248:
        fail("ARIES candidate-pair count drifted")
    reuse = ambiguity.get("responseReuse", {})
    if (
        reuse.get("responses") != 49
        or reuse.get("reusedAcrossConcerns") != 31
        or reuse.get("maxConcernsPerResponse") != 5
    ):
        fail("ARIES response-reuse pressure evidence drifted")

    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if analytical.get("counts") != {
        "paragraphs": 8518,
        "semantic_edits": 4718,
        "positive_edit_texts": 182,
        "response_revision_candidates": 248,
    }:
        fail("ARIES semantic analytical counts drifted")
    if any(analytical.get("integrity", {}).values()):
        fail("ARIES semantic analytical integrity failed")
    for row in analytical.get("files", []):
        if sha256(root / row["path"]) != row["sha256"]:
            fail(f"ARIES semantic analytical product drifted: {row['path']}")

    candidate_path = root / "derived/jsonl/response_revision_candidates.jsonl"
    seen: set[str] = set()
    candidate_count = 0
    for row in iter_jsonl(candidate_path):
        candidate_count += 1
        pair_id = row.get("candidate_pair_id")
        if not isinstance(pair_id, str) or pair_id in seen:
            fail("ARIES semantic candidate id missing or duplicated")
        seen.add(pair_id)
        if row.get("relation_ceiling") != EXPECTED_CEILING:
            fail("ARIES candidate row silently promoted beyond candidate relation")
        if not str(row.get("response_text") or "").strip():
            fail("ARIES semantic candidate lacks response text")
        if not (
            str(row.get("source_text") or "").strip()
            or str(row.get("target_text") or "").strip()
        ):
            fail("ARIES semantic candidate lacks revision text")
    if candidate_count != 248:
        fail("ARIES semantic candidate JSONL cardinality drifted")

    external_baseline = load(root / "CANDIDATE_SPACE_BASELINE_R1.json")
    if external_baseline.get("sourceSnapshotIdentity") != EXPECTED_IDENTITY:
        fail("ARIES external candidate baseline source identity drifted")
    if (
        external_baseline.get("annotationReadiness")
        != "READY_FOR_INDEPENDENT_SEMANTIC_ANNOTATION"
    ):
        fail("ARIES external annotation readiness drifted")
    if (
        external_baseline.get("modelTrainingStanding")
        != "NOT_AUTHORIZED_WITHOUT_SEPARATELY_VALIDATED_RESPONSE_EDIT_RELATION"
    ):
        fail("ARIES external model-training gate drifted")
    if (
        baseline.get("sourceSnapshotIdentity") != EXPECTED_IDENTITY
        or baseline.get("relationStanding") != EXPECTED_RELATION
    ):
        fail("ARIES Git candidate baseline drifted")
    serialized_baseline = json.dumps(baseline, sort_keys=True)
    for forbidden in ('"response_text"', '"source_text"', '"target_text"'):
        if forbidden in serialized_baseline:
            fail("raw paper/response text leaked into compact Git baseline")

    assets = {row.get("id"): row for row in catalog.get("materializedLocalAssets", [])}
    asset = assets.get("aries-semantic-content-core-r1")
    if not asset or asset.get("status") != "MATERIALIZED_BOUNDED_SEMANTIC_CONTENT":
        fail("ARIES semantic-content catalog admission missing")
    if (
        asset.get("rawExternalRoot") != str(EXPECTED_ROOT)
        or asset.get("observedScale") != EXPECTED_COUNTS
    ):
        fail("ARIES semantic-content catalog binding drifted")
    if (
        asset.get("reuseStanding")
        != "ADMIT_INTERNAL_SEMANTIC_ANNOTATION_NO_EXTERNAL_PAPER_TEXT_REDISTRIBUTION"
    ):
        fail("ARIES semantic-content reuse boundary drifted")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.aries-semantic-content-core-acceptance",
        "standing": "PASS_ARIES_SEMANTIC_CONTENT_CANDIDATE_SUBSTRATE_R1",
        "sourceSnapshotIdentity": EXPECTED_IDENTITY,
        "counts": EXPECTED_COUNTS,
        "relationStanding": EXPECTED_RELATION,
        "annotationReadiness": "READY_FOR_INDEPENDENT_SEMANTIC_ANNOTATION",
        "modelTrainingStanding": "NOT_AUTHORIZED_WITHOUT_SEPARATELY_VALIDATED_RESPONSE_EDIT_RELATION",
        "rights": expected_rights,
        "truthBoundary": "Acceptance proves bounded text-bearing candidate substrate integrity only; response-to-revision semantic correspondence, adequacy, and causality remain unidentified.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
