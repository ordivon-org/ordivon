from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel: str):
    return json.loads((ROOT / rel).read_text())

def test_current_truth_projection_matches_canonical_authorities():
    truth = load("planning/current-truth-r1.json")
    production = load("contracts/production-authorization.json")
    execution = load("config/execution_policy.json")
    risk = load("config/portfolio_risk_budget.json")
    private = load("config/private_reality_policy.json")
    protocol = load("config/protocol_identity_migration_v2.json")
    accounting = load("config/accounting_substrate.json")
    taxonomy = load("config/capital_domain_taxonomy.json")

    assert truth["truthRole"] == "REBUILDABLE_PROJECTION_NOT_AUTHORITY"
    assert truth["domainOwners"] == list(taxonomy["domains"])
    assert truth["protocol"]["schemaVersion"] == protocol["schemaVersion"] == 2
    assert truth["protocol"]["standing"] == protocol["standing"]
    assert truth["execution"]["currentLane"] == execution["currentLane"] == "NON_LIVE"
    assert truth["productionAuthorization"]["state"] == production["state"] == "BLOCK_NOT_GRANTED"
    assert truth["productionAuthorization"]["externalFinancialWriteAllowed"] is production["externalFinancialWriteAllowed"] is False
    assert truth["portfolioRiskBudget"]["standing"] == risk["standing"] == "UNSET"
    assert truth["portfolioRiskBudget"]["owner"] == risk["owner"] == "OWNER_PRINCIPAL"
    assert truth["privateReality"]["privateAccountDataAdmission"] == private["privateAccountDataAdmission"] == "NOT_ADMITTED"
    assert truth["privateReality"]["privateAccountDataAllowed"] is private["privateAccountDataAllowed"] is False
    assert truth["accounting"]["standing"] == accounting["standing"]

def test_current_architecture_separates_history_from_present_truth():
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text()
    current = (ROOT / "docs/CURRENT_STATE.md").read_text()
    history = (ROOT / "docs/history/ARCHITECTURE_PROGRESSION_THROUGH_20260921.md").read_text()
    assert "## Current progression" not in architecture
    assert "## Current standing projection" in architecture
    assert "outside the 1000 ms gate" not in architecture
    assert "outside the 1000 ms gate" in history
    assert "BLOCK_NOT_GRANTED" in current
    assert "UNSET" in current
    assert "NOT_ADMITTED" in current
    assert "Historical/provenance only" in history
