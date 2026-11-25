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


def test_retired_carrier_consumers_bind_the_same_archived_subject():
    # A prose sentence is not a recovery contract. Cross-check the actual
    # structured source and recovery identities without asserting live restore.
    taxonomy = json.loads((ROOT / "config/capital_domain_taxonomy.json").read_text())
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    source = taxonomy["standaloneCarrierRetirement"]
    owner = census["standaloneCarrierRetirement"]
    identity = next(
        row for row in taxonomy["retiredCompatibilityIdentities"]
        if row["identity"] == source["path"]
    )
    surface = next(
        row for row in census["retiredCompatibilitySurfaces"]
        if row["id"] == "capital-standalone-source-carrier"
    )
    assert source["path"] == owner["path"] == identity["identity"] == surface["surface"]
    assert source["standing"] == owner["standing"] == "RETIRED_ARCHIVED"
    assert identity["standing"] == surface["standing"] == "RETIRED_ARCHIVED_SOURCE_COORDINATE"
    assert source["recovery"] == owner["recovery"] == identity["recovery"] == surface["recovery"]
    assert source["recovery"]["exactFullTreeRestoreValidated"] is True
