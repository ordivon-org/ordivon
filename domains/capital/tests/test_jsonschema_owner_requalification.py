from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ordivon_capital.research.quantitative_inventory_validation import (
    QuantitativeInventoryValidationError,
    assert_quantitative_inventory_schema_identity,
    validate_quantitative_component_inventory_document,
)
from ordivon_capital.risk.risk_budget_validation import (
    RiskBudgetValidationError,
    assert_risk_budget_schema_identity,
    validate_registered_risk_budget_document,
)

ROOT = Path(__file__).resolve().parents[1]


def _risk() -> dict:
    return json.loads((ROOT / "config/portfolio_risk_budget.json").read_text())


def _inventory() -> dict:
    return json.loads((ROOT / "config/quantitative_component_inventory.json").read_text())


def test_current_documents_pass_domain_local_exact_contract_validators():
    validate_registered_risk_budget_document(_risk())
    validate_quantitative_component_inventory_document(_inventory())
    assert_risk_budget_schema_identity(ROOT / "contracts/portfolio-risk-budget-v2.schema.json")
    assert_quantitative_inventory_schema_identity(
        ROOT / "schema/quantitative_component_inventory.schema.json"
    )


def test_risk_budget_validator_fails_closed_on_contract_boundaries():
    base = _risk()

    extra = copy.deepcopy(base)
    extra["extra"] = True
    with pytest.raises(RiskBudgetValidationError):
        validate_registered_risk_budget_document(extra)

    active_missing = copy.deepcopy(base)
    active_missing["standing"] = "ACTIVE"
    with pytest.raises(RiskBudgetValidationError):
        validate_registered_risk_budget_document(active_missing)

    bad_bool = copy.deepcopy(base)
    bad_bool["standing"] = "ACTIVE"
    for key in bad_bool["limits"]:
        bad_bool["limits"][key] = 1
    bad_bool["limits"]["maxGrossToEquity"] = True
    with pytest.raises(RiskBudgetValidationError):
        validate_registered_risk_budget_document(bad_bool)


def test_quantitative_inventory_validator_fails_closed_on_contract_boundaries():
    base = _inventory()

    bad_id = copy.deepcopy(base)
    bad_id["components"][0]["id"] = "Bad ID"
    with pytest.raises(QuantitativeInventoryValidationError):
        validate_quantitative_component_inventory_document(bad_id)

    extra = copy.deepcopy(base)
    extra["components"][0]["extra"] = True
    with pytest.raises(QuantitativeInventoryValidationError):
        validate_quantitative_component_inventory_document(extra)

    retired = copy.deepcopy(base)
    retired["components"][0]["status"] = "RETIRED"
    retired["components"][0].pop("retirementReason", None)
    with pytest.raises(QuantitativeInventoryValidationError):
        validate_quantitative_component_inventory_document(retired)


def test_schema_identity_drift_requires_requalification(tmp_path: Path):
    risk_schema = ROOT / "contracts/portfolio-risk-budget-v2.schema.json"
    changed_risk = tmp_path / "risk.schema.json"
    changed_risk.write_text(risk_schema.read_text() + "\n")
    with pytest.raises(RiskBudgetValidationError, match="requalification required"):
        assert_risk_budget_schema_identity(changed_risk)

    inventory_schema = ROOT / "schema/quantitative_component_inventory.schema.json"
    changed_inventory = tmp_path / "inventory.schema.json"
    changed_inventory.write_text(inventory_schema.read_text() + "\n")
    with pytest.raises(
        QuantitativeInventoryValidationError,
        match="requalification required",
    ):
        assert_quantitative_inventory_schema_identity(changed_inventory)


def test_jsonschema_is_not_a_current_runtime_dependency():
    pyproject = (ROOT / "pyproject.toml").read_text()
    capability_check = (ROOT / "scripts/check-capabilities").read_text()
    current_source = "\n".join(
        path.read_text()
        for path in (ROOT / "src/ordivon_capital").rglob("*.py")
    )
    assert "jsonschema" not in pyproject
    assert "jsonschema" not in capability_check
    assert "jsonschema" not in current_source


def test_r18_frozen_evidence_supports_candidate_demotion():
    evidence = json.loads(
        (ROOT / "tools/jsonschema_4_26_0/qualification-r18.json").read_text()
    )
    assert evidence["standing"] == "PASS_LOCAL_BOUNDED_VALIDATORS_PREFERRED"
    assert evidence["differential"]["totalCases"] == 6000
    assert evidence["differential"]["mismatches"] == 0
    assert evidence["differential"]["canonicalImplementationReplay"] == (
        "PASS_ZERO_MISMATCH_6000"
    )
    assert evidence["canonicalLocalImplementation"]["schemaIdentityBinding"] == (
        "SHA256_FAIL_CLOSED"
    )
    assert evidence["externalDependencyClosure"]["bytes"] == 1874489


def test_owner_census_demotes_jsonschema_to_candidate():
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    owners = {row["id"]: row for row in census["standardsAndOwners"]}
    row = owners["json-schema-validation"]
    assert row["ownerClass"] == "IMPLEMENTATION_CANDIDATE"
    assert row["currentStanding"] == "R18_LOCAL_BOUNDED_VALIDATORS_PREFERRED"

    quals = {row["contractId"]: row for row in census["comparativeQualifications"]}
    q = quals["json-schema-draft-2020-12-validation"]
    assert q["externalOwnerAdmitted"] is False
    assert q["standing"] == "LOCAL_BOUNDED_DOCUMENT_VALIDATORS_PREFERRED"
    assert q["evidence"]["differentialCases"] == 6000
    assert q["evidence"]["differentialMismatches"] == 0
