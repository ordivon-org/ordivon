from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.research.constraint_graph import (
    ConstraintGraphValidationError,
    compute_quantitative_headroom,
    load_constraint_graph,
    project_frontier,
    validate_constraint_graph_document,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/ai_infrastructure_constraint_graph_r1.json"


def test_graph_document_is_valid_and_research_only() -> None:
    doc = load_constraint_graph(CONFIG)
    validated = validate_constraint_graph_document(doc)

    assert validated["kind"] == "ordivon.capital.ai-infrastructure-constraint-graph"
    assert validated["truthRole"] == "RESEARCH_MODEL_NOT_PROVIDER_TRUTH_OR_INVESTMENT_AUTHORITY"
    assert validated["effectBoundary"]["externalFinancialWritesAllowed"] is False
    assert validated["effectBoundary"]["ownerRiskBudgetInferred"] is False
    assert validated["aggregationPolicy"]["aggregateScoreAllowed"] is False


def test_first_graph_is_the_frozen_seven_node_supply_chain() -> None:
    doc = load_constraint_graph(CONFIG)
    assert [row["nodeKey"] for row in doc["nodes"]] == [
        "accelerator-logic",
        "hbm",
        "advanced-packaging",
        "ai-data-center-it",
        "electricity-generation",
        "transformer-switchgear",
        "grid-interconnection-transmission",
    ]
    assert [(row["from"], row["to"]) for row in doc["edges"]] == [
        ("accelerator-logic", "hbm"),
        ("hbm", "advanced-packaging"),
        ("advanced-packaging", "ai-data-center-it"),
        ("ai-data-center-it", "electricity-generation"),
        ("electricity-generation", "transformer-switchgear"),
        ("transformer-switchgear", "grid-interconnection-transmission"),
    ]


def test_frontier_is_explicit_not_inferred_from_a_scalar_score() -> None:
    doc = load_constraint_graph(CONFIG)
    us = project_frontier(doc, "US")
    cn = project_frontier(doc, "CN")

    assert us["frontierNodeKeys"] == [
        "transformer-switchgear",
        "grid-interconnection-transmission",
    ]
    assert cn["frontierNodeKeys"] == [
        "accelerator-logic",
        "hbm",
    ]
    assert us["aggregateScore"] is None
    assert cn["aggregateScore"] is None


def test_every_current_frontier_claim_has_persistent_evidence_and_reopen_conditions() -> None:
    doc = load_constraint_graph(CONFIG)
    evidence_ids = {row["evidenceId"] for row in doc["evidence"]}
    for state in doc["jurisdictions"]:
        for claim in state["nodeStates"]:
            if claim["frontierRole"] == "CURRENT_FRONTIER":
                assert claim["evidenceIds"]
                assert set(claim["evidenceIds"]) <= evidence_ids
                assert claim["reopenConditions"]
                assert claim["currentness"]["observedAt"]


def test_quantitative_headroom_requires_same_unit_and_has_no_hidden_score() -> None:
    result = compute_quantitative_headroom(capacity=120.0, requirement=100.0, unit="GW")
    assert result == {
        "mode": "QUANTITATIVE",
        "unit": "GW",
        "capacity": 120.0,
        "requirement": 100.0,
        "headroomRatio": pytest.approx(0.2),
    }
    with pytest.raises(ConstraintGraphValidationError):
        compute_quantitative_headroom(capacity=120.0, requirement=0.0, unit="GW")


def test_source_identities_are_persistent_not_chat_citations() -> None:
    doc = json.loads(CONFIG.read_text())
    for row in doc["evidence"]:
        assert "turn" not in row["persistentIdentity"]
        assert row["canonicalUrl"].startswith("https://")


def test_scenarios_are_counterfactuals_not_forecasts_or_trade_actions() -> None:
    doc = load_constraint_graph(CONFIG)
    for row in doc["counterfactuals"]:
        assert row["truthRole"] == "ILLUSTRATIVE_COUNTERFACTUAL_NOT_FORECAST"
        assert row["candidateFrontierNodeKeys"]
        assert row["externalFinancialEffectAllowed"] is False


def test_graph_is_registered_as_research_only_validation_required() -> None:
    registry = json.loads((ROOT / "config/capital_lego_registry.json").read_text())
    row = next(
        item for item in registry["entries"]
        if item["legoId"] == "capital.research.ai-infrastructure-constraint-graph"
    )
    assert row["ownerDomain"] == "research"
    assert row["status"] == "VALIDATION_REQUIRED"
    assert row["effectClass"] == "NONE"
    assert row["authorityRequirement"] == "NONE"

    fmap = json.loads((ROOT / "planning/functional-lego-map-r1.json").read_text())
    assert fmap["moduleCoverage"]["src/ordivon_capital/research/constraint_graph.py"] == [
        "Validate", "Measure", "Model"
    ]


def test_graph_is_governed_but_not_promoted_to_decision_state_registry() -> None:
    inventory = json.loads((ROOT / "config/quantitative_component_inventory.json").read_text())
    component = next(
        item for item in inventory["components"]
        if item["id"] == "ai-infrastructure-constraint-graph-r1"
    )
    assert component["classification"] == "ANALYTICAL_HEURISTIC"
    assert component["sr26ModelStanding"] == "CLASSIFICATION_REVIEW"
    assert component["status"] == "RESEARCH_ONLY"
    assert component["validation"]["standing"] == "VALIDATION_REQUIRED"

    state_registry = json.loads((ROOT / "config/decision_state_claim_registry.json").read_text())
    assert all("infrastructure" not in item["claimKey"] for item in state_registry["claims"])


def test_external_owner_census_keeps_constraint_graph_as_thin_research_binding() -> None:
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    row = next(
        item for item in census["responsibilities"]
        if item["id"] == "research-ai-infrastructure-constraint-mapping"
    )
    assert row["sourcePatterns"] == [
        "src/ordivon_capital/research/constraint_graph.py",
        "src/ordivon_capital/research/constraint_measurements.py",
    ]
    assert row["localStanding"] == "RESEARCH_ONLY_VALIDATION_REQUIRED_THIN_BINDING"
    assert "do not own industrial capacity truth" in row["localResponsibility"]
    assert "ISO/IEC/IEEE 15288" in row["standardOwners"]
    assert "Berkeley Lab Queued Up" in row["providerOwners"]


def test_cn_transformer_is_candidate_tight_after_current_order_book_evidence() -> None:
    doc = load_constraint_graph(CONFIG)
    cn = next(row for row in doc["jurisdictions"] if row["jurisdiction"] == "CN")
    state = next(row for row in cn["nodeStates"] if row["nodeKey"] == "transformer-switchgear")
    assert cn["frontierNodeKeys"] == ["accelerator-logic", "hbm"]
    assert state["frontierRole"] == "CANDIDATE_FRONTIER"
    assert state["headroom"]["standing"] == "TIGHT"
    assert "ev-digitalchina-cn-transformer-orders-20260202" in state["evidenceIds"]
    assert any("2027" in condition for condition in state["reopenConditions"])
