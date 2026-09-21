from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = "/root/projects/ordivon-market-capital-next"


def test_legacy_physical_source_coordinate_is_retired_not_retained():
    taxonomy = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())
    retained = {row["identity"] for row in taxonomy["retainedCompatibilityIdentities"]}
    assert LEGACY_PATH not in retained
    retired = {row["identity"]: row for row in taxonomy["retiredCompatibilityIdentities"]}
    row = retired[LEGACY_PATH]
    assert row["standing"] == "RETIRED_ARCHIVED_SOURCE_COORDINATE"
    assert row["recovery"]["exactFullTreeRestoreValidated"] is True


def test_standalone_retirement_recovery_is_hash_bound():
    taxonomy = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())
    row = taxonomy["standaloneCarrierRetirement"]
    assert row["standing"] == "RETIRED_ARCHIVED"
    assert row["physicalPathPresent"] is False
    assert row["currentSourceOfTruth"] == "monorepo:domains/capital"
    assert row["lastQualifiedExternalSourceRevision"] == "71bf084cc140a210a5ec0ce736afeb82ed03ae69"
    recovery = row["recovery"]
    for key in (
        "allRefsBundleSha256",
        "gitDirectoryTarSha256",
        "ignoredNonVenvPayloadTarSha256",
        "sndkResidualTarSha256",
    ):
        assert recovery[key].startswith("sha256:")
    assert recovery["refs"] == 50
    assert recovery["commits"] == 94
    assert recovery["unreachableObjectsPreserved"] == 30
    assert recovery["ignoredNonVenvFilesPreserved"] == 322
    assert recovery["excludedRegenerablePayload"] == [".venv"]


def test_owner_census_has_no_retained_physical_repo_contract():
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    retained = {row["id"] for row in census["retainedCompatibilityContracts"]}
    assert "historical-physical-repo-source-coordinate" not in retained
    retired = {row["id"]: row for row in census["retiredCompatibilitySurfaces"]}
    row = retired["capital-standalone-source-carrier"]
    assert row["standing"] == "RETIRED_ARCHIVED_SOURCE_COORDINATE"
    assert row["researchProvenanceRule"].startswith("frozen Research/Paper1 records")


def test_current_docs_do_not_claim_physical_carrier_is_retained():
    census_doc = (ROOT / "docs/ORDIVON_CAPITAL_EXTERNAL_OWNER_CENSUS_R1.md").read_text()
    taxonomy_doc = (ROOT / "docs/CAPITAL_DOMAIN_TAXONOMY_ACCEPTANCE_20260921.md").read_text()
    assert "is retained because frozen Research/Paper1" not in census_doc
    assert "Physical rename is therefore blocked" not in census_doc
    assert "standalone repository path used by research provenance remain explicit provenance identities" not in taxonomy_doc
    assert "physical standalone carrier is retired" in census_doc
