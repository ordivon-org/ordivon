from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft201909Validator, Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "data-products/experimental-episode-corpus-r1"
EVIDENCE = ROOT / "evidence/data-products/experimental-episode-analysis-r1"
FEDERATION = ROOT / "evidence/data-lifecycle/data-products-r2"
STANDARDS = ROOT / "evidence/data-lifecycle/github-pilot-r1/standards"
ARTIFACT_ROOT = ROOT.parents[1] / "capabilities/artifact"


def load(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_episode_product_binds_replay_manifest_and_contract() -> None:
    product = load(PRODUCT / "odps.json")
    contract = load(PRODUCT / "odcs.json")
    acceptance = load(PRODUCT / "acceptance.json")
    manifest = ROOT / "evidence/experimental-episode/corpus-r1/manifest.json"

    assert product["apiVersion"] == "v1.1.0"
    assert product["kind"] == "DataProduct"
    assert product["id"] == acceptance["productId"]
    assert product["version"] == acceptance["productVersion"] == "1.0.0"
    assert contract["apiVersion"] == "v3.2.0"
    assert contract["kind"] == "DataContract"
    assert contract["id"] == acceptance["contractId"]
    assert {port["contractId"] for port in product["outputPorts"]} == {contract["id"]}
    assert sha256(manifest) == acceptance["corpusManifestSha256"]
    assert acceptance["standing"] == (
        "PASS_ODPS_1_1_ODCS_3_2_ARTIFACT_INDEX_OPENLINEAGE_PROV"
    )


def test_episode_odcs_validates_against_frozen_official_schema() -> None:
    schema = load(STANDARDS / "odcs-json-schema-v3.2.0.json")
    contract = load(PRODUCT / "odcs.json")
    Draft201909Validator.check_schema(schema)
    errors = sorted(
        Draft201909Validator(schema).iter_errors(contract),
        key=lambda error: list(error.path),
    )
    assert errors == []


def test_artifact_contract_remains_artifact_owned_and_digest_bound() -> None:
    contract = load(PRODUCT / "artifact-dataset-contract.json")
    schema = load(
        ARTIFACT_ROOT
        / "artifact-delivery/shadow-contracts/dataset-contract-v1.schema.json"
    )
    Draft202012Validator(schema).validate(contract)
    acceptance = load(PRODUCT / "acceptance.json")
    verification = load(EVIDENCE / "artifact-index-verification.json")
    assert verification["status"] == "PASS"
    assert verification["readerAgreement"]["exactCanonicalRowsMatch"] is True
    assert verification["keyIntegrity"]["duplicateKeyObserved"] is False
    assert verification["rowBounds"]["pyarrowRowCount"] == 10007
    assert (
        verification["artifact"]["sha256"] == acceptance["qualifiedParquetIndexSha256"]
    )
    assert (
        sha256(PRODUCT / "artifact-dataset-contract.json")
        == acceptance["artifactDatasetContractSha256"]
    )


def test_openlineage_events_validate_and_bind_analysis() -> None:
    root_schema = load(STANDARDS / "OpenLineage-2.0.2.json")
    run_schema = {
        "$schema": root_schema["$schema"],
        "$id": root_schema["$id"] + "#run-event-local-validation",
        "$ref": "#/$defs/RunEvent",
        "$defs": root_schema["$defs"],
    }
    validator = Draft202012Validator(run_schema, format_checker=FormatChecker())
    events = load(EVIDENCE / "openlineage.json")
    assert [event["eventType"] for event in events] == ["START", "COMPLETE"]
    for event in events:
        assert list(validator.iter_errors(event)) == []

    receipt = load(EVIDENCE / "receipt.json")
    assert receipt["openLineageRunId"] == events[0]["run"]["runId"]
    assert events[0]["run"]["runId"] == events[1]["run"]["runId"]
    assert receipt["corpusManifestSha256"] in events[0]["inputs"][0]["name"]
    assert receipt["systemAnalysisSha256"] in events[1]["outputs"][0]["name"]
    assert receipt["authorityTransfer"] is False


def test_federation_r2_adds_product_without_rewriting_r1() -> None:
    r1 = load(ROOT / "evidence/data-lifecycle/data-products-r1/acceptance.json")
    r2 = load(FEDERATION / "acceptance.json")
    catalog = load(FEDERATION / "federated-catalog.dcat.jsonld")
    assert r1["standing"] == "PASS_TWO_DOMAIN_ODPS_ODCS_DCAT_PROV"
    assert r2["standing"] == "PASS_THREE_PRODUCT_ODPS_ODCS_DCAT_PROV_OPENLINEAGE"
    assert len(catalog["dcat:dataset"]) == 3
    assert sum(len(item["dcat:distribution"]) for item in catalog["dcat:dataset"]) == 4
    ids = {item["dct:identifier"] for item in catalog["dcat:dataset"]}
    assert "4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b" in ids


def test_product_governance_and_claim_boundaries_fail_closed() -> None:
    product = load(PRODUCT / "odps.json")
    acceptance = load(PRODUCT / "acceptance.json")
    policy = load(PRODUCT / "governance-policy.odrl.jsonld")
    custom = {item["property"]: item["value"] for item in product["customProperties"]}

    assert {item["action"] for item in policy["prohibition"]} == {
        "distribute",
        "grantUse",
        "delete",
    }
    assert custom["redistributionStatus"] == "NOT_AUTHORIZED_BY_PRODUCT_METADATA"
    assert custom["retentionScheduleStatus"] == "UNASSIGNED"
    assert "license" not in json.dumps(product).lower()
    assert "does not transfer" in acceptance["claimBoundary"].lower()
    assert product["team"]["customProperties"][0]["value"] == (
        "PRODUCT_METADATA_AND_ANALYTICAL_LIFECYCLE_NOT_OWNER_NATIVE_TRUTH"
    )
