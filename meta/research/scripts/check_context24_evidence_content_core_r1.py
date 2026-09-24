#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
RECEIPT = META / "research/evidence/context24-evidence-content-core-r1.json"
BASELINE = META / "research/evidence/context24-evidence-content-baseline-r1.json"
IDENTITY_RECEIPT = META / "research/evidence/context24-identity-core-r1.json"


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


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def main() -> int:
    receipt = load(RECEIPT)
    baseline = load(BASELINE)
    identity_receipt = load(IDENTITY_RECEIPT)
    if receipt.get("status") != "MATERIALIZED_PARTIAL_GOLD_EVIDENCE_CONTENT_CORE_PASS":
        fail("Context24 content receipt standing drifted")
    if (
        receipt.get("parentAsset", {}).get("snapshotIdentity")
        != identity_receipt["snapshot"]["identity"]
    ):
        fail("Context24 content parent identity drifted")
    rights = receipt.get("rights", {})
    if rights.get("underlyingPaperMediaRights") != "NOT_INDEPENDENTLY_VERIFIED":
        fail("underlying-media rights boundary weakened")
    if rights.get("externalRedistribution") != "NOT_AUTHORIZED_BY_CATALOG":
        fail("external redistribution was silently authorized")
    if rights.get("commercialMediaReuse") != "NOT_AUTHORIZED_BY_CATALOG":
        fail("commercial media reuse was silently authorized")
    root = Path(receipt["snapshot"]["root"])
    required = [
        "raw/full_texts-2024-04-25-update.json",
        "raw/full_texts-test.json",
        "SNAPSHOT_MANIFEST_R1.json",
        "SCHEMA_CENSUS_R1.json",
        "NORMALIZATION_SUMMARY_R1.json",
        "ANALYTICAL_BUILD_RECEIPT_R1.json",
        "derived/jsonl/fulltexts.jsonl",
        "derived/jsonl/evidence_contents.jsonl",
        "derived/jsonl/claim_evidence_content_links.jsonl",
        "derived/jsonl/captions.jsonl",
        "derived/jsonl/unresolved_gold_links.jsonl",
        "derived/context24-evidence-content-core-r1.duckdb",
    ]
    for rel in required:
        if not (root / rel).is_file():
            fail(f"Context24 content file missing: {rel}")
    for rel, key in (
        ("SNAPSHOT_MANIFEST_R1.json", "manifestSha256"),
        ("SCHEMA_CENSUS_R1.json", "schemaCensusSha256"),
        ("NORMALIZATION_SUMMARY_R1.json", "normalizationSummarySha256"),
        ("ANALYTICAL_BUILD_RECEIPT_R1.json", "analyticalBuildReceiptSha256"),
    ):
        if sha256(root / rel) != receipt["snapshot"][key]:
            fail(f"Context24 content compact digest drifted: {rel}")
    census = load(root / "SCHEMA_CENSUS_R1.json")
    expected = {
        "task1TrainRows": 474,
        "task1GoldEvidenceLinks": 679,
        "exactGoldContentLinks": 256,
        "identityOnlyGoldLinks": 423,
        "uniqueContentImages": 223,
        "fulltextTrainCarrierKeys": 319,
        "fulltextTestCarrierKeys": 91,
        "normalizedFulltextRows": 410,
        "captionCarrierFiles": 32,
    }
    if (
        census.get("status")
        != "PASS_PARTIAL_GOLD_CONTENT_BINDING_WITH_FULLTEXT_COVERAGE"
    ):
        fail("Context24 content census standing drifted")
    for key, expected_value in expected.items():
        if census["counts"].get(key) != expected_value:
            fail(f"Context24 content census drift: {key}")
    if abs(float(census["coverage"]["goldContentLinkFraction"]) - 256 / 679) > 1e-15:
        fail("Context24 content coverage fraction drifted")
    manifest = load(root / "SNAPSHOT_MANIFEST_R1.json")
    if len(manifest.get("goldImageFiles", [])) != 223:
        fail("Context24 gold image manifest count drifted")
    for row in manifest["goldImageFiles"]:
        path = root / row["path"]
        if (
            not path.is_file()
            or sha256(path) != row["sha256"]
            or path.stat().st_size != row["bytes"]
        ):
            fail(f"Context24 gold image drift: {row['path']}")
    if len(manifest.get("captionFiles", [])) != 32:
        fail("Context24 caption manifest count drifted")
    for row in manifest["captionFiles"]:
        path = root / row["path"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            fail(f"Context24 caption drift: {row['path']}")
    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if analytical.get("counts") != {
        "captions": 32,
        "claim_evidence_content_links": 256,
        "evidence_contents": 223,
        "fulltexts": 410,
        "unresolved_gold_links": 423,
    }:
        fail("Context24 content analytical counts drifted")
    if analytical.get("referential", {}).get("orphanContentLinks") != 0:
        fail("Context24 content referential integrity failed")
    for row in analytical["files"]:
        if sha256(root / row["path"]) != row["sha256"]:
            fail(f"Context24 analytical product drift: {row['path']}")
    row_counts = {
        "fulltexts": count_jsonl(root / "derived/jsonl/fulltexts.jsonl"),
        "evidence_contents": count_jsonl(
            root / "derived/jsonl/evidence_contents.jsonl"
        ),
        "claim_evidence_content_links": count_jsonl(
            root / "derived/jsonl/claim_evidence_content_links.jsonl"
        ),
        "captions": count_jsonl(root / "derived/jsonl/captions.jsonl"),
        "unresolved_gold_links": count_jsonl(
            root / "derived/jsonl/unresolved_gold_links.jsonl"
        ),
    }
    if row_counts != analytical["counts"]:
        fail("Context24 content JSONL/analytical count mismatch")
    with (root / "derived/jsonl/claim_evidence_content_links.jsonl").open(
        encoding="utf-8"
    ) as fh:
        for line in fh:
            if line.strip() and not json.loads(line)["claim_instance_id"].startswith(
                "task1:train:"
            ):
                fail("withheld test gold leaked into content links")
    if baseline.get("sourceSnapshotIdentity") != receipt["snapshot"]["identity"]:
        fail("Context24 content baseline identity drifted")
    if baseline.get("counts", {}).get("identityOnlyGoldLinks") != 423:
        fail("Context24 unresolved identity-only ceiling drifted")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.context24-evidence-content-core-acceptance",
        "standing": "PASS_CONTEXT24_PARTIAL_EVIDENCE_CONTENT_CORE",
        "snapshotIdentity": receipt["snapshot"]["identity"],
        "goldEvidenceLinks": 679,
        "contentBoundGoldLinks": 256,
        "identityOnlyGoldLinks": 423,
        "uniqueContentImages": 223,
        "fulltextCoverage": {"task1Train": "229/229", "task1Test": "46/46"},
        "testGoldStanding": "WITHHELD_NOT_INFERRED",
        "truthBoundary": "Pass proves exact upstream content bytes and partial identity-to-content bindings only. It does not establish evidence adequacy, scientific truth, causal support, ClaimPermission, or media redistribution rights.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
