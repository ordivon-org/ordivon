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
DISAPERE_RECEIPT = META / "research/evidence/disapere-bounded-core-r1.json"
DISAPERE_BASELINE = META / "research/evidence/disapere-review-rebuttal-baseline-r1.json"
PEERSUM_RECEIPT = META / "research/evidence/peersum-hf-bounded-core-r1.json"
PEERSUM_BASELINE = META / "research/evidence/peersum-meta-review-structure-baseline-r1.json"
CONTEXT24_RECEIPT = META / "research/evidence/context24-identity-core-r1.json"
CONTEXT24_BASELINE = META / "research/evidence/context24-claim-evidence-baseline-r1.json"
ARIES_RESPONSE_RECEIPT = META / "research/evidence/aries-review-response-core-r1.json"
ARIES_FORK_BASELINE = META / "research/evidence/aries-lifecycle-fork-baseline-r1.json"


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


def verify_disapere(asset: dict[str, Any], receipt: dict[str, Any]) -> dict[str, int]:
    expected_status = "MATERIALIZED_BOUNDED_CORE_ANALYTICAL_VIEWS_PASS_NONCOMMERCIAL"
    if receipt.get("status") != expected_status:
        fail("DISAPERE admission receipt is not admitted")
    if receipt.get("truthRole") != "external-review-discourse-physical-and-schema-evidence-not-reviewer-or-scientific-truth":
        fail("DISAPERE truth boundary drifted")
    if receipt.get("authority", {}).get("commercialProductOrServiceUse") != "NOT_AUTHORIZED_BY_CC_BY_NC_ADMISSION":
        fail("DISAPERE commercial-use gate was weakened")
    if receipt.get("privacy", {}).get("reviewerProfilingAuthorized") is not False:
        fail("DISAPERE reviewer-profiling boundary was weakened")
    root = Path(asset["rawExternalRoot"])
    if root != Path(receipt["snapshot"]["root"]):
        fail("DISAPERE catalog/receipt root mismatch")
    required = [
        "raw/DISAPERE-upstream.zip", "raw/LICENSE.md", "raw/README.md",
        "SNAPSHOT_MANIFEST_R1.json", "SCHEMA_CENSUS_R1.json",
        "NORMALIZATION_SUMMARY_R1.json", "ANALYTICAL_BUILD_RECEIPT_R1.json",
        "derived/jsonl/pairs.jsonl", "derived/jsonl/review_sentences.jsonl",
        "derived/jsonl/rebuttal_sentences.jsonl", "derived/jsonl/local_alignment_links.jsonl",
        "derived/parquet/pairs.parquet", "derived/parquet/review_sentences.parquet",
        "derived/parquet/rebuttal_sentences.parquet",
        "derived/parquet/local_alignment_links.parquet",
        "derived/disapere-bounded-r1.duckdb",
    ]
    for rel in required:
        if not (root / rel).is_file():
            fail(f"DISAPERE materialized file missing: {rel}")
    receipt_hashes = {
        "SNAPSHOT_MANIFEST_R1.json": receipt["snapshot"]["manifestSha256"],
        "SCHEMA_CENSUS_R1.json": receipt["snapshot"]["schemaCensusSha256"],
        "NORMALIZATION_SUMMARY_R1.json": receipt["snapshot"]["normalizationSummarySha256"],
        "ANALYTICAL_BUILD_RECEIPT_R1.json": receipt["snapshot"]["analyticalBuildReceiptSha256"],
    }
    for rel, expected in receipt_hashes.items():
        if sha256(root / rel) != expected:
            fail(f"DISAPERE compact receipt digest drift: {rel}")
    if sha256(root / "raw/LICENSE.md") != receipt["source"]["licenseFileSha256"]:
        fail("DISAPERE license bytes drifted")
    if sha256(root / "raw/DISAPERE-upstream.zip") != receipt["source"]["releaseZipSha256"]:
        fail("DISAPERE release ZIP bytes drifted")
    license_text = (root / "raw/LICENSE.md").read_text(encoding="utf-8")
    if "Attribution-NonCommercial 4.0 International" not in license_text:
        fail("DISAPERE CC BY-NC 4.0 marker missing")

    manifest = load(root / "SNAPSHOT_MANIFEST_R1.json")
    if manifest.get("sourceCommit") != "9adab87b997852c5447cfee6e3fd5bfad5e70311":
        fail("DISAPERE source commit drifted")
    if manifest.get("canonicalFileCount") != 509:
        fail("DISAPERE canonical file count drifted")

    census = load(root / "SCHEMA_CENSUS_R1.json")
    if census.get("status") != "PASS_SCHEMA_AND_LOCAL_ALIGNMENT_REFERENTIAL_INTEGRITY":
        fail("DISAPERE schema census not accepted")
    expected_census = {
        "pairFiles": 506, "reviewSentences": 9946, "rebuttalSentences": 11103,
        "localAlignmentLinks": 21675, "orphanLocalAlignmentLinks": 0,
        "duplicateReviewSentenceIdentities": 0,
    }
    for key, expected in expected_census.items():
        if census["counts"].get(key) != expected:
            fail(f"DISAPERE census drift: {key}")
    if "commercial product/service use is not authorized" not in census.get("licenseBoundary", ""):
        fail("DISAPERE license boundary missing commercial-use prohibition")

    analytical = load(root / "ANALYTICAL_BUILD_RECEIPT_R1.json")
    if analytical.get("counts") != {
        "pairs": 506, "review_sentences": 9946,
        "rebuttal_sentences": 11103, "local_alignment_links": 21675,
    }:
        fail("DISAPERE analytical counts drifted")
    if any(value != 0 for value in analytical.get("referential", {}).values()):
        fail("DISAPERE analytical referential integrity failed")
    for row in analytical["files"]:
        if sha256(root / row["path"]) != row["sha256"]:
            fail(f"DISAPERE analytical product digest drift: {row['path']}")

    forbidden = ('"reviewer":', '"annotator":')
    for rel in (
        "derived/jsonl/pairs.jsonl", "derived/jsonl/review_sentences.jsonl",
        "derived/jsonl/rebuttal_sentences.jsonl", "derived/jsonl/local_alignment_links.jsonl",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            fail(f"DISAPERE normalized identity field leaked: {rel}")
    if receipt["counts"] != asset["observedScale"]:
        fail("DISAPERE catalog observedScale differs from receipt")
    return receipt["counts"]


def main() -> int:
    catalog = load(CATALOG)
    plan = load(PLAN)
    sd1 = load(SD1)
    sd2 = load(SD2)
    aries_receipt = load(ARIES_RECEIPT)
    context24_transport = load(CONTEXT24_TRANSPORT)
    aries_baseline = load(ARIES_BASELINE)
    disapere_receipt = load(DISAPERE_RECEIPT)
    disapere_baseline = load(DISAPERE_BASELINE)
    peersum_receipt = load(PEERSUM_RECEIPT)
    peersum_baseline = load(PEERSUM_BASELINE)
    context24_receipt = load(CONTEXT24_RECEIPT)
    context24_baseline = load(CONTEXT24_BASELINE)
    aries_response_receipt = load(ARIES_RESPONSE_RECEIPT)
    aries_fork_baseline = load(ARIES_FORK_BASELINE)

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
    required_assets = {"emse-writing-benchmark-r16", "aries-bounded-core-r1", "aries-review-response-core-r1", "disapere-bounded-core-r1", "peersum-hf-bounded-core-r1", "context24-identity-core-r1"}
    if not required_assets.issubset(by_asset):
        fail(f"missing materialized assets: {sorted(required_assets - set(by_asset))}")
    if len(by_asset) != len(assets):
        fail("duplicate materialized asset ids")

    emse = verify_emse(by_asset["emse-writing-benchmark-r16"])
    aries = verify_aries(by_asset["aries-bounded-core-r1"], aries_receipt)
    disapere = verify_disapere(by_asset["disapere-bounded-core-r1"], disapere_receipt)

    if aries_response_receipt.get("status") != "MATERIALIZED_REVIEW_RESPONSE_CORE_ANALYTICAL_VIEWS_PASS":
        fail("ARIES response-core admission standing drifted")
    if aries_response_receipt.get("parentAsset", {}).get("snapshotIdentity") != aries_receipt["snapshot"]["identity"]:
        fail("ARIES response-core parent binding drifted")
    if aries_fork_baseline.get("sourceSnapshotIdentity") != aries_response_receipt["snapshot"]["identity"]:
        fail("ARIES lifecycle fork baseline identity drifted")
    if aries_fork_baseline.get("counts", {}).get("manualConcernsWithBothBranches") != 87:
        fail("ARIES lifecycle fork count drifted")

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

    if disapere_baseline.get("sourceSnapshotIdentity") != disapere_receipt["snapshot"]["identity"]:
        fail("DISAPERE baseline source identity drifted")
    if disapere_baseline.get("counts") != {
        "pairs": 506, "reviewSentences": 9946, "rebuttalSentences": 11103,
        "localAlignmentLinks": 21675, "locallyAlignedRebuttalSentences": 9416,
        "locallyTargetedReviewSentences": 4096, "requestLinkedRebuttalSentences": 5220,
    }:
        fail("DISAPERE baseline counts drifted")
    expected_coverage = {
        "allReviewSentences": (4096, 9946),
        "requestReviewSentences": (1441, 1971),
        "negativePolarityReviewSentences": (2004, 2927),
        "clarityReviewSentences": (600, 1102),
        "soundnessCorrectnessReviewSentences": (626, 953),
        "replicabilityReviewSentences": (214, 284),
    }
    for key, (targeted, total) in expected_coverage.items():
        row = disapere_baseline["explicitLocalAlignmentCoverage"][key]
        if row.get("targeted") != targeted or row.get("total") != total:
            fail(f"DISAPERE baseline coverage drift: {key}")
        if abs(float(row.get("fraction")) - targeted / total) > 1e-15:
            fail(f"DISAPERE baseline fraction drift: {key}")
    if disapere_baseline["distributions"]["requestLinkedRebuttalStance"] != {
        "concur": 3397, "dispute": 471, "nonarg": 1352
    }:
        fail("DISAPERE request-linked stance drifted")

    if peersum_receipt.get("status") != "MATERIALIZED_DIGEST_BOUND_ANALYTICAL_VIEWS_PASS":
        fail("PeerSum admission receipt standing drifted")
    if peersum_receipt.get("counts", {}).get("papers") != 14993:
        fail("PeerSum admission count drifted")
    if peersum_baseline.get("sourceSnapshotIdentity") != peersum_receipt["snapshot"]["identity"]:
        fail("PeerSum baseline source identity drifted")
    if peersum_baseline.get("splitCountStanding") != "CURRENT_CARRIER_DIFFERS_FROM_HISTORICAL_DOCUMENTATION":
        fail("PeerSum split drift boundary missing")

    if context24_receipt.get("status") != "MATERIALIZED_IDENTITY_CORE_ANALYTICAL_VIEWS_PASS":
        fail("Context24 admission receipt standing drifted")
    if context24_receipt.get("counts", {}).get("task1TotalRows") != 585:
        fail("Context24 admission count drifted")
    if context24_baseline.get("sourceSnapshotIdentity") != context24_receipt["snapshot"]["identity"]:
        fail("Context24 baseline source identity drifted")

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
    if aries_candidate.get("acquisitionState") != "MATERIALIZED_BOUNDED_CORE_PLUS_RESPONSE_CORE":
        fail("ARIES candidate/local asset state mismatch")
    if by_candidate["context24"].get("acquisitionState") != "MATERIALIZED_IDENTITY_CORE":
        fail("Context24 candidate/local asset state mismatch")
    if by_candidate["disapere"].get("acquisitionState") != "MATERIALIZED_BOUNDED_CORE_NONCOMMERCIAL":
        fail("DISAPERE candidate/local asset state mismatch")
    if by_candidate["peersum"].get("acquisitionState") != "MATERIALIZED_DIGEST_BOUND":
        fail("PeerSum candidate/local asset state mismatch")

    prohibited = " ".join(catalog.get("prohibitedInterpretations", [])).casefold()
    for token in ("acceptance", "reviewer truth", "redistribution"):
        if token not in prohibited:
            fail(f"missing prohibited interpretation token: {token}")

    by_wave = {row["id"]: row for row in plan.get("waves", [])}
    if by_wave.get("SD1", {}).get("standing") != "IN_PROGRESS_CONTEXT24_IDENTITY_CORE_MATERIALIZED_OTHER_LICENSE_BLOCKERS_REMAIN":
        fail("SD1 standing drifted")
    if by_wave.get("SD2", {}).get("standing") != "IN_PROGRESS_ARIES_RESPONSE_DISAPERE_PEERSUM_MATERIALIZED":
        fail("SD2 standing drifted")
    if by_wave.get("SD4", {}).get("standing") != "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST":
        fail("large scholarly fulltext acquisition was prematurely promoted")

    if sd1.get("standing") != "PARTIAL_READY_CONTEXT24_IDENTITY_CORE_MATERIALIZED":
        fail("SD1 readiness top-level standing drifted")
    sd1_by_id = {row["id"]: row for row in sd1.get("candidates", [])}
    if sd1_by_id.get("context24", {}).get("standing") != "MATERIALIZED_IDENTITY_CORE":
        fail("Context24 license-ready transport blocker missing")
    for blocked in ("scicite", "scidtb", "coresc-azii-chemistry"):
        if not str(sd1_by_id.get(blocked, {}).get("standing", "")).startswith("BLOCKED_"):
            fail(f"{blocked}: fail-closed license readiness lost")
    admission = sd1.get("admission", {})
    if admission.get("mayMaterializeNow") != []:
        fail("SD1 mayMaterializeNow must remain empty under current license gates")
    if admission.get("mayMaterializeWhenTransportAvailable") != []:
        fail("Context24 must no longer be transport-blocked after bounded materialization")
    if admission.get("materialized") != ["context24-identity-core-r1"]:
        fail("Context24 SD1 materialized binding missing")
    if admission.get("bulkDownloadAuthorized") is not False:
        fail("bulk download was silently authorized")
    if context24_transport.get("standing") != "BLOCKED_TRANSPORT_NOT_DATA_OR_LICENSE":
        fail("historical Context24 direct-transport evidence drifted")

    if sd2.get("standing") != "IN_PROGRESS_THREE_DATASETS_FOUR_REVIEW_LIFECYCLE_ASSETS_MATERIALIZED":
        fail("SD2 readiness standing drifted")
    sd2_by_id = {row["id"]: row for row in sd2.get("datasets", [])}
    expected_sd2 = {
        "aries": "MATERIALIZED_BOUNDED_CORE_PLUS_RESPONSE_CORE",
        "peersum": "MATERIALIZED_DIGEST_BOUND",
        "nlpeer-v2": "LICENSE_OBSERVED_ACCESS_RESTRICTED_LARGE_NOT_ACQUIRED",
        "peerread-v1": "PARTIAL_COMPONENT_LICENSE_CONSTRAINTS_REQUIRE_SECTION_LEVEL_BINDING",
        "disapere": "MATERIALIZED_BOUNDED_CORE_NONCOMMERCIAL",
    }
    for key, standing in expected_sd2.items():
        if sd2_by_id.get(key, {}).get("standing") != standing:
            fail(f"SD2 dataset standing drifted: {key}")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.scholarly-data-plane-r1-acceptance",
        "standing": "PASS_DATA_PLANE_WITH_CONTEXT24_ARIES_RESPONSE_DISAPERE_PEERSUM",
        "materializedLocalAssetCount": len(assets),
        "externalCandidateCount": len(candidates),
        "emse": emse,
        "aries": aries,
        "ariesResponse": aries_response_receipt["counts"],
        "ariesLifecycleFork": {"manualConcerns": 196, "withResponseContext": 196, "withPositiveRevision": 87, "withBothBranches": 87},
        "disapere": disapere,
        "peersum": peersum_receipt["counts"],
        "context24": context24_receipt["counts"],
        "context24HistoricalDirectTransport": context24_transport["standing"],
        "ariesManualBaseline": expected_baseline,
        "disapereCoverageBaseline": {key: {"targeted": value[0], "total": value[1]} for key, value in expected_coverage.items()},
        "nextWaves": ["Context24 evidence-content resolver", "PeerSum semantic-disagreement annotation", "ARIES response-to-revision identification"],
        "largeCorpusWave": "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST",
        "truthBoundary": (
            "Acceptance proves current local EMSE, Context24, ARIES core, ARIES review-response core, DISAPERE, and PeerSum physical/schema bindings, "
            "including exact analytical product digests, rights/provenance boundaries, and independent PeerSum artifact requalification. It does not turn dataset labels "
            "into reviewer/scientific truth, authorize manuscript or submission effects, or "
            "generalize dataset frequencies to scholarly populations."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
