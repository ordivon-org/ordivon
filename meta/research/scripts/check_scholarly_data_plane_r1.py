#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
CATALOG = META / "research/data/scholarly-data-catalog-r1.json"
PLAN = META / "research/data/scholarly-data-acquisition-plan-r1.json"
SD1 = META / "research/data/sd1-acquisition-readiness-r1.json"
SD2 = META / "research/data/sd2-review-lifecycle-readiness-r1.json"
ARIES_RECEIPT = META / "research/evidence/aries-bounded-core-r1.json"
CONTEXT24_TRANSPORT = META / "research/evidence/context24-transport-blocker-r1.json"
ARIES_BASELINE = META / "research/evidence/aries-review-revision-baseline-r1.json"


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


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def verify_emse(asset: dict[str, Any]) -> dict[str, int]:
    repo = Path(asset["sourceRepo"])
    if not repo.is_dir():
        fail(f"EMSE corpus owner repo missing: {repo}")
    resolved = {key: repo / value for key, value in asset["paths"].items()}
    for key, path in resolved.items():
        if not path.is_file():
            fail(f"registered EMSE corpus file missing: {key}: {path}")

    summary = load(resolved["samplingSummary"])
    grammar = load(resolved["sectionGrammar"])
    comparison = load(resolved["currentComparison"])
    observed = asset["observedScale"]
    checks = {
        "publisherOriginalPaperFrame": summary["publisherOriginalPaperFrameCount"],
        "stratifiedBaselineAssignment": summary["baseline"]["n"],
        "focusedTopicOversampleAssignment": summary["focusedTopicOversample"]["n"],
        "uniqueAcquisitionTargets": summary["uniqueAcquisitionTargets"],
        "validatedFulltexts": summary["validCleanTargetPdfs"],
        "publisherFinalFulltexts": summary["validPublisherVersionPdfs"],
        "externalPdfFiles": summary["externalPdfFilesTotal"],
        "externalPdfBytes": summary["externalPdfBytesTotal"],
        "accessibleRandomBaselineFulltexts": comparison[
            "cleanBaselineFulltextComparison"
        ]["bodyWordsBeforeReferences"]["baselineFulltextN"],
    }
    for key, actual in checks.items():
        expected = observed[key]
        if actual != expected:
            fail(f"EMSE catalog drift {key}: expected {expected!r}, got {actual!r}")
    if grammar["cleanBaselineFulltextN"] != observed["accessibleRandomBaselineFulltexts"]:
        fail("EMSE grammar baseline cardinality drifted")
    if count_csv_rows(resolved["fulltextMetrics"]) != observed["validatedFulltexts"]:
        fail("EMSE fulltext metrics row count drifted")
    if count_csv_rows(resolved["acquisitionManifest"]) != observed["validatedFulltexts"]:
        fail("EMSE acquisition manifest row count drifted")
    return checks


def verify_aries(asset: dict[str, Any], receipt: dict[str, Any]) -> dict[str, int]:
    if receipt.get("status") != "MATERIALIZED_BOUNDED_CORE_ANALYTICAL_VIEWS_PASS":
        fail("ARIES admission receipt is not admitted")
    if receipt.get("truthRole") != "external-dataset-physical-and-schema-evidence-not-reviewer-or-scientific-truth":
        fail("ARIES truth boundary drifted")
    root = Path(asset["rawExternalRoot"])
    if root != Path(receipt["snapshot"]["root"]):
        fail("ARIES catalog/receipt root mismatch")

    required = [
        "raw/LICENSE",
        "raw/edit_labels_dev.jsonl",
        "raw/edit_labels_test.jsonl",
        "raw/paper_edits.jsonl",
        "raw/review_comments.jsonl",
        "SNAPSHOT_MANIFEST_R1.json",
        "SCHEMA_CENSUS_R1.json",
        "NORMALIZATION_SUMMARY_R1.json",
        "ANALYTICAL_BUILD_RECEIPT_R1.json",
        "derived/parquet/comments.parquet",
        "derived/parquet/edits.parquet",
        "derived/parquet/alignments.parquet",
        "derived/aries-bounded-core-r1.duckdb",
    ]
    for rel in required:
        if not (root / rel).is_file():
            fail(f"ARIES materialized file missing: {rel}")

    receipt_hashes = {
        "SNAPSHOT_MANIFEST_R1.json": receipt["snapshot"]["rawManifestSha256"],
        "SCHEMA_CENSUS_R1.json": receipt["snapshot"]["schemaCensusSha256"],
        "NORMALIZATION_SUMMARY_R1.json": receipt["snapshot"]["normalizationSummarySha256"],
        "ANALYTICAL_BUILD_RECEIPT_R1.json": receipt["snapshot"]["analyticalBuildReceiptSha256"],
    }
    for rel, expected in receipt_hashes.items():
        actual = sha256(root / rel)
        if actual != expected:
            fail(f"ARIES compact receipt digest drift {rel}: {actual} != {expected}")
    if sha256(root / "raw/LICENSE") != receipt["source"]["licenseFileSha256"]:
        fail("ARIES license bytes drifted")

    census = load(root / "SCHEMA_CENSUS_R1.json")
    if census.get("status") != "PASS_SCHEMA_AND_REFERENTIAL_CENSUS":
        fail("ARIES schema census not accepted")
    expected_census = {
        "reviewCommentRows": 4088,
        "uniqueReviewCommentIdentities": 4088,
        "paperEditDocuments": 1720,
        "editUnits": 213955,
        "devLabelRows": 542,
        "testLabelRows": 196,
    }
    for key, expected in expected_census.items():
        if census["counts"].get(key) != expected:
            fail(f"ARIES census drift {key}")
    for split in ("dev", "test"):
        part = census["annotation"][split]
        rows = part["rows"]
        for key in (
            "commentIdentityResolvableRows",
            "allPositiveEditIdsResolvableRows",
            "allNegativeEditIdsResolvableRows",
        ):
            if part[key] != rows:
                fail(f"ARIES {split} referential check failed: {key}")

    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    expected_counts = {
        "comments": 4088,
        "edits": 213955,
        "alignments": 25462,
        "positiveAlignments": 724,
        "negativeAlignments": 24738,
        "manualTestComments": 196,
    }
    for key, expected in expected_counts.items():
        if analytical["counts"].get(key) != expected:
            fail(f"ARIES analytical count drift {key}")
    if analytical["referential"] != {
        "orphanAlignmentComments": 0,
        "orphanAlignmentEdits": 0,
    }:
        fail("ARIES analytical referential integrity failed")
    for row in analytical["files"]:
        p = root / row["path"]
        if sha256(p) != row["sha256"]:
            fail(f"ARIES analytical product digest drift: {row['path']}")

    if receipt["counts"] != asset["observedScale"]:
        fail("ARIES catalog observedScale differs from admission receipt")
    if receipt["source"].get("licenseObserved") != "ODC-BY-1.0":
        fail("ARIES observed license standing drifted")
    return receipt["counts"]


def main() -> int:
    catalog = load(CATALOG)
    plan = load(PLAN)
    sd1 = load(SD1)
    sd2 = load(SD2)
    aries_receipt = load(ARIES_RECEIPT)
    context24_transport = load(CONTEXT24_TRANSPORT)
    aries_baseline = load(ARIES_BASELINE)

    if catalog.get("truthRole") != "data-asset-catalog-not-scientific-truth":
        fail("catalog authority boundary drifted")
    storage = catalog.get("storagePolicy", {})
    if storage.get("rawExternalBytes") != "OUTSIDE_GIT":
        fail("raw external corpus bytes must remain outside Git")
    if storage.get("sharedPostgresStanding") != "NOT_JUSTIFIED_YET":
        fail("shared PostgreSQL was silently promoted")

    assets = catalog.get("materializedLocalAssets")
    if not isinstance(assets, list):
        fail("materializedLocalAssets must be a list")
    by_asset = {row.get("id"): row for row in assets}
    required_assets = {"emse-writing-benchmark-r16", "aries-bounded-core-r1"}
    if not required_assets.issubset(by_asset):
        fail(f"missing materialized assets: {sorted(required_assets - set(by_asset))}")
    if len(by_asset) != len(assets):
        fail("duplicate materialized asset ids")

    emse = verify_emse(by_asset["emse-writing-benchmark-r16"])
    aries = verify_aries(by_asset["aries-bounded-core-r1"], aries_receipt)

    if aries_baseline.get("sourceSnapshotIdentity") != aries_receipt["snapshot"]["identity"]:
        fail("ARIES baseline source identity drifted")
    baseline_counts = aries_baseline.get("counts", {})
    expected_baseline = {
        "manualTestComments": 196,
        "commentsWithPositiveEditAlignment": 87,
        "commentsWithoutPositiveEditAlignment": 109,
        "positiveEditLinks": 182,
        "negativeEditLinks": 24738,
        "distinctDocumentsInManualTest": 42,
    }
    for key, expected in expected_baseline.items():
        if baseline_counts.get(key) != expected:
            fail(f"ARIES manual baseline drift: {key}")
    rate = aries_baseline.get("rates", {}).get("commentsWithPositiveEditAlignment")
    if abs(float(rate) - (87 / 196)) > 1e-15:
        fail("ARIES manual baseline positive-alignment rate drifted")
    if aries_baseline.get("provenance", {}).get("testAnnotation") != "manual":
        fail("ARIES manual baseline provenance drifted")

    candidates = catalog.get("externalCandidates")
    if not isinstance(candidates, list) or len(candidates) < 10:
        fail("external candidate coverage is unexpectedly small")
    by_candidate = {row.get("id"): row for row in candidates}
    required = {
        "s2orc-2020", "peerread-v1", "nlpeer", "disapere", "aries",
        "coresc-azii-chemistry", "scidtb", "scicite", "peersum",
        "context24", "openreview-api",
    }
    if not required.issubset(by_candidate):
        fail(f"missing required candidates: {sorted(required - set(by_candidate))}")
    if len(by_candidate) != len(candidates):
        fail("duplicate external candidate ids")
    for row in candidates:
        if not row.get("sourceUrl"):
            fail(f"{row.get('id')}: sourceUrl missing")
        standing = str(row.get("licenseStanding", ""))
        if not standing or not any(token in standing for token in ("VERIFY", "MUST_BE_BOUND", "OBSERVED")):
            fail(f"{row.get('id')}: license/access standing is not explicit")
    aries_candidate = by_candidate["aries"]
    if aries_candidate.get("acquisitionState") != "MATERIALIZED_BOUNDED_CORE":
        fail("ARIES candidate/local asset state mismatch")
    if by_candidate["context24"].get("acquisitionState") != "READY_LICENSE_VERIFIED_TRANSPORT_BLOCKED":
        fail("Context24 transport-blocked state missing")

    prohibited = " ".join(catalog.get("prohibitedInterpretations", [])).casefold()
    for token in ("acceptance", "reviewer truth", "redistribution"):
        if token not in prohibited:
            fail(f"missing prohibited interpretation token: {token}")

    by_wave = {row["id"]: row for row in plan.get("waves", [])}
    if by_wave.get("SD1", {}).get("standing") != "PARTIAL_READY_TRANSPORT_BLOCKED_FOR_CONTEXT24":
        fail("SD1 standing drifted")
    if by_wave.get("SD2", {}).get("standing") != "IN_PROGRESS_ARIES_BOUNDED_CORE_MATERIALIZED":
        fail("SD2 standing drifted")
    if by_wave.get("SD4", {}).get("standing") != "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST":
        fail("large scholarly fulltext acquisition was prematurely promoted")

    if sd1.get("standing") != "PARTIAL_READY":
        fail("SD1 readiness top-level standing drifted")
    sd1_by_id = {row["id"]: row for row in sd1.get("candidates", [])}
    if sd1_by_id.get("context24", {}).get("standing") != "READY_LICENSE_VERIFIED_TRANSPORT_BLOCKED_HF_DIRECT":
        fail("Context24 license-ready transport blocker missing")
    for blocked in ("scicite", "scidtb", "coresc-azii-chemistry"):
        if not str(sd1_by_id.get(blocked, {}).get("standing", "")).startswith("BLOCKED_"):
            fail(f"{blocked}: fail-closed license readiness lost")
    admission = sd1.get("admission", {})
    if admission.get("mayMaterializeNow") != []:
        fail("SD1 mayMaterializeNow must remain empty under current transport")
    if admission.get("bulkDownloadAuthorized") is not False:
        fail("bulk download was silently authorized")
    if context24_transport.get("standing") != "BLOCKED_TRANSPORT_NOT_DATA_OR_LICENSE":
        fail("Context24 transport evidence standing drifted")

    if sd2.get("standing") != "IN_PROGRESS_FIRST_ASSET_MATERIALIZED":
        fail("SD2 readiness standing drifted")
    sd2_by_id = {row["id"]: row for row in sd2.get("datasets", [])}
    expected_sd2 = {
        "aries": "MATERIALIZED_BOUNDED_CORE",
        "peersum": "READY_LICENSE_OBSERVED_NOT_ACQUIRED",
        "nlpeer-v2": "LICENSE_OBSERVED_ACCESS_RESTRICTED_LARGE_NOT_ACQUIRED",
        "peerread-v1": "PARTIAL_COMPONENT_LICENSE_CONSTRAINTS_REQUIRE_SECTION_LEVEL_BINDING",
        "disapere": "RELEASE_LICENSE_NOT_YET_BOUND",
    }
    for key, standing in expected_sd2.items():
        if sd2_by_id.get(key, {}).get("standing") != standing:
            fail(f"SD2 dataset standing drifted: {key}")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.scholarly-data-plane-r1-acceptance",
        "standing": "PASS_DATA_PLANE_WITH_ARIES_BOUNDED_CORE",
        "materializedLocalAssetCount": len(assets),
        "externalCandidateCount": len(candidates),
        "emse": emse,
        "aries": aries,
        "context24Transport": context24_transport["standing"],
        "ariesManualBaseline": expected_baseline,
        "nextWaves": ["SD1 transport recovery", "SD2 lifecycle expansion"],
        "largeCorpusWave": "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST",
        "truthBoundary": (
            "Acceptance proves current local EMSE and ARIES physical/schema bindings, "
            "including exact ARIES analytical product digests. It does not turn dataset labels "
            "into reviewer/scientific truth, authorize manuscript or submission effects, or "
            "generalize dataset frequencies to scholarly populations."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
