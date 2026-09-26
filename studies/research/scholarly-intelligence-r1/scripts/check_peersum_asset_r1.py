#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
STUDY = Path(__file__).resolve().parents[1]
RECEIPT = STUDY / "evidence/peersum-hf-bounded-core-r1.json"
BASELINE = STUDY / "evidence/peersum-meta-review-structure-baseline-r1.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def main() -> int:
    receipt = load(RECEIPT)
    baseline = load(BASELINE)
    root = Path(receipt["snapshot"]["root"])
    if receipt.get("status") != "MATERIALIZED_DIGEST_BOUND_ANALYTICAL_VIEWS_PASS":
        fail("PeerSum admission standing drifted")
    if receipt.get("truthRole") != "external-review-discussion-and-meta-review-physical-and-schema-evidence-not-reviewer-scientific-or-decision-truth":
        fail("PeerSum truth boundary drifted")
    if receipt.get("privacy", {}).get("reviewerProfilingAuthorized") is not False:
        fail("PeerSum reviewer profiling boundary weakened")
    if receipt.get("transport", {}).get("role") != "transport-only-not-authority":
        fail("PeerSum transport resolver was promoted to authority")
    source = receipt["source"]
    if source.get("licenseObserved") != "Apache-2.0":
        fail("PeerSum observed license drifted")
    raw = root / "raw/peersum_huggingface.jsonl"
    if raw.stat().st_size != 476238545:
        fail("PeerSum raw byte count drifted")
    if sha256(raw) != "sha256:ddd4766837f7d92913d1fa59cf2aabac18bf0313643f35e1c993d09c0ff938ab":
        fail("PeerSum raw carrier digest drifted")
    readme = root / "raw/README.md"
    if sha256(readme) != source["readmeSha256"]:
        fail("PeerSum README digest drifted")
    if "license: apache-2.0" not in readme.read_text(encoding="utf-8"):
        fail("PeerSum Apache-2.0 dataset-card marker missing")

    compact = {
        "SNAPSHOT_MANIFEST_R1.json": receipt["snapshot"]["manifestSha256"],
        "SCHEMA_CENSUS_R1.json": receipt["snapshot"]["schemaCensusSha256"],
        "NORMALIZATION_SUMMARY_R1.json": receipt["snapshot"]["normalizationSummarySha256"],
        "ANALYTICAL_BUILD_RECEIPT_R1.json": receipt["snapshot"]["analyticalBuildReceiptSha256"],
        "BASELINE_R1.json": receipt["snapshot"]["baselineSha256"],
        "REQUALIFICATION_R1.json": receipt["snapshot"]["requalificationSha256"],
    }
    for rel, expected in compact.items():
        if sha256(root / rel) != expected:
            fail(f"PeerSum compact receipt digest drift: {rel}")

    req = load(root / "REQUALIFICATION_R1.json")
    if req.get("status") != "PASS_ARTIFACT_BYTES_INDEPENDENTLY_REQUALIFIED":
        fail("PeerSum independent requalification standing drifted")
    materialization = req.get("materializationExecutionEvidence", {})
    if materialization.get("runtimeStanding") != "ORPHANED_RECONCILIATION_REQUIRED":
        fail("PeerSum original orphaned Runtime truth was overwritten")
    if materialization.get("semanticUse") != "NOT_USED_AS_SUCCESS_PROOF":
        fail("PeerSum orphaned Job was promoted to success proof")

    census = load(root / "SCHEMA_CENSUS_R1.json")
    if census.get("status") != "PASS":
        fail("PeerSum schema census not accepted")
    if census["counts"] != {
        "author_messages": 95943,
        "official_reviews": 79354,
        "public_messages": 2975,
        "reviews": 178272,
        "rows": 14993,
    }:
        fail("PeerSum census counts drifted")
    expected_zero = {
        "duplicatePaperIds", "duplicateReviewIdRows", "malformedListRows",
        "orphanReplyTargets", "papersWithReplyCycles",
        "parallelListLengthMismatchRows", "selfReplyEdges",
    }
    for key in expected_zero:
        if census["integrity"].get(key) != 0:
            fail(f"PeerSum integrity gate failed: {key}")
    if census["integrity"].get("nonemptyMetaReviews") != 14993:
        fail("PeerSum non-empty meta-review count drifted")
    current_splits = {"train": 11992, "val": 1496, "test": 1505}
    if census["splits"] != current_splits:
        fail("PeerSum current-carrier split drifted")

    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if analytical["counts"] != {"papers": 14993, "messages": 178272, "reply_edges": 178272}:
        fail("PeerSum analytical counts drifted")
    if any(value != 0 for value in analytical["referential"].values()):
        fail("PeerSum analytical referential integrity failed")
    for row in analytical["files"]:
        if sha256(root / row["path"]) != row["sha256"]:
            fail(f"PeerSum analytical product digest drift: {row['path']}")
    if analytical["thresholdCounts"] != {"spread_ge_3": 5320, "spread_ge_4": 2032, "spread_ge_5": 1175}:
        fail("PeerSum structural disagreement threshold counts drifted")

    expected_baseline_counts = {
        "papers": 14993, "messages": 178272, "officialReviewMessages": 79354,
        "authorMessages": 95943, "publicMessages": 2975, "nonemptyMetaReviews": 14993,
    }
    if baseline.get("sourceSnapshotIdentity") != receipt["snapshot"]["identity"]:
        fail("PeerSum baseline source identity drifted")
    if baseline.get("counts") != expected_baseline_counts:
        fail("PeerSum Git baseline counts drifted")
    if baseline.get("splitCountsCurrentCarrier") != current_splits:
        fail("PeerSum Git baseline current splits drifted")
    if baseline.get("historicalDocumentationSplitCounts") != {"train": 11995, "val": 1499, "test": 1499}:
        fail("PeerSum historical split witness drifted")
    if baseline.get("splitCountStanding") != "CURRENT_CARRIER_DIFFERS_FROM_HISTORICAL_DOCUMENTATION":
        fail("PeerSum release-drift boundary missing")
    if baseline["ratingSpreadProxy"]["definition"].find("not semantic conflict") < 0:
        fail("PeerSum structural-disagreement interpretation ceiling weakened")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.peersum-asset-acceptance",
        "standing": "PASS_DIGEST_BOUND_PEERSUM_ASSET",
        "snapshotIdentity": receipt["snapshot"]["identity"],
        "rawCarrierSha256": source["rawCarrierSha256"],
        "papers": 14993,
        "messages": 178272,
        "currentCarrierSplits": current_splits,
        "historicalDocumentationSplits": {"train": 11995, "val": 1499, "test": 1499},
        "originalMaterializationJob": "ORPHANED_RECONCILIATION_REQUIRED",
        "artifactRequalification": "PASS_ARTIFACT_BYTES_INDEPENDENTLY_REQUALIFIED",
        "truthBoundary": "Acceptance proves exact PeerSum artifact/schema/reply-graph bindings. It does not promote numeric rating spread to semantic disagreement, meta-review to truth, or acceptance metadata to a venue-independent quality target.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
