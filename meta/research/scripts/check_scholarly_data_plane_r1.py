#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

META = Path(__file__).resolve().parents[2]
CATALOG = META / "research/data/scholarly-data-catalog-r1.json"
PLAN = META / "research/data/scholarly-data-acquisition-plan-r1.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected object: {path}")
    return value


def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def main() -> int:
    catalog = load(CATALOG)
    plan = load(PLAN)

    if catalog.get("truthRole") != "data-asset-catalog-not-scientific-truth":
        fail("catalog authority boundary drifted")
    storage = catalog.get("storagePolicy", {})
    if storage.get("rawExternalBytes") != "OUTSIDE_GIT":
        fail("raw external corpus bytes must remain outside Git")
    if storage.get("sharedPostgresStanding") != "NOT_JUSTIFIED_YET":
        fail("shared PostgreSQL was silently promoted")

    assets = catalog.get("materializedLocalAssets")
    if not isinstance(assets, list) or len(assets) != 1:
        fail("R1 expects exactly one registered materialized external writing corpus")
    local = assets[0]
    if local.get("id") != "emse-writing-benchmark-r16":
        fail("unexpected R1 materialized asset")
    repo = Path(local["sourceRepo"])
    if not repo.is_dir():
        fail(f"local corpus owner repo missing: {repo}")
    resolved = {key: repo / value for key, value in local["paths"].items()}
    for key, path in resolved.items():
        if not path.is_file():
            fail(f"registered local corpus file missing: {key}: {path}")

    summary = load(resolved["samplingSummary"])
    grammar = load(resolved["sectionGrammar"])
    comparison = load(resolved["currentComparison"])
    observed = local["observedScale"]
    checks = {
        "publisherOriginalPaperFrame": summary["publisherOriginalPaperFrameCount"],
        "stratifiedBaselineAssignment": summary["baseline"]["n"],
        "focusedTopicOversampleAssignment": summary["focusedTopicOversample"]["n"],
        "uniqueAcquisitionTargets": summary["uniqueAcquisitionTargets"],
        "validatedFulltexts": summary["validCleanTargetPdfs"],
        "publisherFinalFulltexts": summary["validPublisherVersionPdfs"],
        "externalPdfFiles": summary["externalPdfFilesTotal"],
        "externalPdfBytes": summary["externalPdfBytesTotal"],
        "accessibleRandomBaselineFulltexts": comparison["cleanBaselineFulltextComparison"]["bodyWordsBeforeReferences"]["baselineFulltextN"],
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

    candidates = catalog.get("externalCandidates")
    if not isinstance(candidates, list) or len(candidates) < 10:
        fail("external candidate coverage is unexpectedly small")
    ids = [row.get("id") for row in candidates]
    if len(ids) != len(set(ids)):
        fail("duplicate external dataset ids")
    required = {
        "s2orc-2020", "peerread-v1", "nlpeer", "disapere", "aries",
        "coresc-azii-chemistry", "scidtb", "scicite", "peersum",
        "context24", "openreview-api"
    }
    if not required.issubset(ids):
        fail(f"missing required candidates: {sorted(required - set(ids))}")
    for row in candidates:
        if not row.get("sourceUrl"):
            fail(f"{row.get('id')}: sourceUrl missing")
        if row.get("acquisitionState") == "MATERIALIZED_EXTERNAL_CORPUS":
            fail(f"{row.get('id')}: external candidate falsely marked materialized")
        license_standing = str(row.get("licenseStanding", ""))
        if not license_standing or ("VERIFY" not in license_standing and "MUST_BE_BOUND" not in license_standing):
            fail(f"{row.get('id')}: license/access standing is not fail-closed")

    prohibited = " ".join(catalog.get("prohibitedInterpretations", [])).casefold()
    for token in ("acceptance", "reviewer truth", "redistribution"):
        if token not in prohibited:
            fail(f"missing prohibited interpretation token: {token}")

    by_id = {row["id"]: row for row in plan.get("waves", [])}
    if by_id.get("SD1", {}).get("standing") != "NEXT":
        fail("small labeled corpora must remain the next acquisition wave")
    if by_id.get("SD4", {}).get("standing") != "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST":
        fail("large scholarly fulltext acquisition was prematurely promoted")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research.scholarly-data-plane-r1-acceptance",
        "standing": "PASS_CATALOG_AND_LOCAL_EMSE_BINDING",
        "materializedLocalAssetCount": 1,
        "externalCandidateCount": len(candidates),
        "emse": checks,
        "nextWave": "SD1",
        "largeCorpusWave": "DEFERRED_UNTIL_QUERY_JUSTIFIES_COST",
        "truthBoundary": "Acceptance proves catalog structure and current local EMSE corpus bindings. It does not prove external candidate licenses, downloadability, scientific truth, or cross-domain representativeness."
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
