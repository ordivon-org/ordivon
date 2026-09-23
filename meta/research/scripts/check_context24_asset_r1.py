#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
RECEIPT = META / "research/evidence/context24-identity-core-r1.json"
BASELINE = META / "research/evidence/context24-claim-evidence-baseline-r1.json"


def fail(m: str) -> None:
    raise SystemExit(m)


def load(p: Path) -> dict[str, Any]:
    v = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v, dict):
        fail(f"expected object: {p}")
    return v


def sha(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    r = load(RECEIPT)
    b = load(BASELINE)
    root = Path(r["snapshot"]["root"])
    if r.get("status") != "MATERIALIZED_IDENTITY_CORE_ANALYTICAL_VIEWS_PASS":
        fail("Context24 admission standing drifted")
    if (
        r.get("truthRole")
        != "external-claim-grounding-annotation-evidence-not-scientific-truth"
    ):
        fail("Context24 truth boundary drifted")
    if r.get("transport", {}).get("role") != "transport-only-not-authority":
        fail("Context24 resolver promoted to authority")
    if (
        r.get("source", {}).get("repoCommit")
        != "457d3b5cb4bb8ade34e37458f4900c6eae0959bb"
    ):
        fail("Context24 repo commit drifted")
    if r.get("source", {}).get("licenseObserved") != "CC-BY-4.0":
        fail("Context24 license standing drifted")
    readme = root / "raw/README.md"
    if sha(readme) != r["source"][
        "readmeSha256"
    ] or "license: cc-by-4.0" not in readme.read_text(encoding="utf-8"):
        fail("Context24 README/license bytes drifted")
    compact = {
        "SNAPSHOT_MANIFEST_R1.json": r["snapshot"]["manifestSha256"],
        "SCHEMA_CENSUS_R1.json": r["snapshot"]["schemaCensusSha256"],
        "NORMALIZATION_SUMMARY_R1.json": r["snapshot"]["normalizationSummarySha256"],
        "ANALYTICAL_BUILD_RECEIPT_R1.json": r["snapshot"][
            "analyticalBuildReceiptSha256"
        ],
        "BASELINE_R1.json": r["snapshot"]["baselineSha256"],
    }
    for rel, expected in compact.items():
        if sha(root / rel) != expected:
            fail(f"Context24 compact digest drift: {rel}")
    m = load(root / "SNAPSHOT_MANIFEST_R1.json")
    if m["source"]["transportRole"] != "transport-only-not-authority":
        fail("Context24 manifest transport boundary drifted")
    for row in m["files"]:
        if (
            sha(root / row["path"]) != row["sha256"]
            or (root / row["path"]).stat().st_size != row["bytes"]
        ):
            fail(f"Context24 raw source drift: {row['path']}")
    c = load(root / "SCHEMA_CENSUS_R1.json")
    if (
        c.get("status")
        != "PASS_WITH_NATIVE_ID_COLLISIONS_PRESERVED_AND_TEST_GOLD_WITHHELD"
    ):
        fail("Context24 schema census standing drifted")
    expected_counts = {
        "task1TrainRows": 474,
        "task1TestRows": 111,
        "task1TotalRows": 585,
        "task1UniqueNativeIds": 566,
        "task1TrainingNativeIdCollisionGroups": 19,
        "task1TrainingExactUniqueRows": 463,
        "task1GoldEvidenceLinks": 679,
        "task1TrainPapers": 229,
        "task1TestPapers": 46,
        "task1CrossSplitPaperOverlap": 6,
        "task1CrossSplitExactClaimOverlap": 0,
        "task2TrainRows": 42,
        "task2TestRows": 109,
        "task2TotalRows": 151,
        "task2UniqueNativeIds": 151,
        "task2GoldMethodContextSnippets": 210,
        "task2ExactClaimsAlsoInTask1": 145,
        "task2NativeIdsNotInTask1": 5,
    }
    if c["counts"] != expected_counts:
        fail("Context24 census counts drifted")
    if c["nativeIdCollisionClasses"] != {
        "exact_duplicate_rows": 11,
        "same_claim_different_finding_set": 5,
        "same_claim_same_finding_set_different_order_or_serialization": 2,
        "same_native_id_different_claim_text": 1,
    }:
        fail("Context24 native-id collision taxonomy drifted")
    if any(c["integrity"].values()):
        fail("Context24 schema integrity gate failed")
    if c["evidenceKindCounts"] != {"figure": 554, "table": 125}:
        fail("Context24 evidence kind counts drifted")
    if "native id is source metadata, not a unique key" not in c["identityPolicy"]:
        fail("Context24 identity policy weakened")
    a = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if a["counts"] != {
        "claims": 736,
        "task1_evidence_links": 679,
        "task2_method_contexts": 210,
    }:
        fail("Context24 analytical counts drifted")
    if any(v != 0 for v in a["referential"].values()):
        fail("Context24 referential integrity failed")
    if a["goldAvailability"] != {
        "task1_test_withheld_challenge_test": 111,
        "task1_train_available": 474,
        "task2_test_withheld_challenge_test": 109,
        "task2_train_available": 42,
    }:
        fail("Context24 gold availability drifted")
    for row in a["files"]:
        if sha(root / row["path"]) != row["sha256"]:
            fail(f"Context24 analytical product drift: {row['path']}")
    if b.get("sourceSnapshotIdentity") != r["snapshot"]["identity"]:
        fail("Context24 baseline source identity drifted")
    if b.get("counts") != expected_counts:
        fail("Context24 Git baseline counts drifted")
    if b.get("evidenceKinds") != {"figure": 554, "table": 125}:
        fail("Context24 Git baseline evidence kinds drifted")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.context24-asset-acceptance",
        "standing": "PASS_CONTEXT24_IDENTITY_CORE",
        "snapshotIdentity": r["snapshot"]["identity"],
        "task1Rows": 585,
        "task1GoldEvidenceLinks": 679,
        "task2Rows": 151,
        "task2GoldMethodContextSnippets": 210,
        "nativeIdCollisionGroups": 19,
        "testGoldStanding": "WITHHELD_NOT_FABRICATED",
        "truthBoundary": "Acceptance proves exact claim/evidence-identity/method-context bindings and identity anomalies. It does not prove scientific truth, causal support, method adequacy, or hidden test gold.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
