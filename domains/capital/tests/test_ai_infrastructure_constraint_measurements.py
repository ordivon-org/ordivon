from __future__ import annotations

import json
from pathlib import Path

import pytest

from ordivon_capital.research.constraint_measurements import (
    ConstraintMeasurementValidationError,
    evaluate_headroom_pair,
    load_constraint_measurements,
    prioritized_fill_queue,
    validate_constraint_measurements_document,
)

ROOT = Path(__file__).resolve().parents[1]
MEASUREMENTS = ROOT / "config/ai_infrastructure_constraint_measurements_r1.json"
GRAPH = ROOT / "config/ai_infrastructure_constraint_graph_r1.json"


def test_measurement_document_is_research_only_and_binds_exact_graph() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    validated = validate_constraint_measurements_document(doc, graph_path=GRAPH)
    assert validated["kind"] == "ordivon.capital.ai-infrastructure-constraint-measurements"
    assert validated["truthRole"] == "MEASUREMENT_BINDING_NOT_PROVIDER_TRUTH_OR_HEADROOM_BY_DEFAULT"
    assert validated["effectBoundary"]["externalFinancialWritesAllowed"] is False
    assert validated["effectBoundary"]["decisionStateRegistryMutationIncluded"] is False


def test_fill_queue_is_frontier_first_not_database_completeness_first() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    queue = prioritized_fill_queue(doc)
    assert [(row["jurisdiction"], row["nodeKey"]) for row in queue[:4]] == [
        ("CN", "accelerator-logic"),
        ("CN", "hbm"),
        ("US", "transformer-switchgear"),
        ("US", "grid-interconnection-transmission"),
    ]
    assert all(row["priority"] == "P0_CURRENT_FRONTIER" for row in queue[:4])


def test_headroom_admission_requires_same_unit_scope_time_and_independent_requirement() -> None:
    admitted = evaluate_headroom_pair(
        capacity={"value": 120.0, "unit": "GW", "scope": "X", "timeBasis": "2026YE"},
        requirement={
            "value": 100.0,
            "unit": "GW",
            "scope": "X",
            "timeBasis": "2026YE",
            "independentOfCapacityModel": True,
        },
    )
    assert admitted["standing"] == "ADMITTED"
    assert admitted["headroomRatio"] == pytest.approx(0.2)

    endogenous = evaluate_headroom_pair(
        capacity={"value": 240_000.0, "unit": "accelerator_units", "scope": "Huawei-950DT", "timeBasis": "2026"},
        requirement={
            "value": 320_000.0,
            "unit": "accelerator_units",
            "scope": "Huawei-950DT",
            "timeBasis": "2026",
            "independentOfCapacityModel": False,
        },
    )
    assert endogenous == {"standing": "BLOCKED_ENDOGENOUS_REQUIREMENT", "headroomRatio": None}


def test_china_hbm_records_bom_and_model_without_faking_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "CN" and item["nodeKey"] == "hbm"
    )
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["huawei-950dt-memory-variants-gb"]["values"] == [96.0, 144.0]
    assert metrics["epoch-domestic-hbm-supported-950dt-units"]["value"] == 240_000.0
    assert metrics["epoch-domestic-hbm-supported-950dt-pb-96gb"]["value"] == pytest.approx(23.04)
    assert metrics["epoch-modeled-total-950dt-hbm-units"]["value"] == 320_000.0
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"
    assert row["headroomAdmission"]["headroomRatio"] is None
    assert "qualified" in row["headroomAdmission"]["resolutionRequirement"].lower()


def test_china_accelerator_has_directional_excess_demand_but_no_numeric_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "CN" and item["nodeKey"] == "accelerator-logic"
    )
    assert row["demandSupplySignal"] == "INDEPENDENT_CUSTOMER_DEMAND_LOWER_BOUND_PLUS_PROVIDER_EXCESS_DEMAND"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_us_transformer_lead_time_is_not_miscast_as_capacity_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "US" and item["nodeKey"] == "transformer-switchgear"
    )
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["reported-high-voltage-transformer-lead-time-weeks-up-to"]["value"] == 160.0
    assert row["headroomAdmission"]["standing"] == "BLOCKED_TIME_BASIS_MISMATCH"


def test_us_generation_queue_is_explicitly_rejected_as_load_headroom_denominator() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "US" and item["nodeKey"] == "grid-interconnection-transmission"
    )
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"
    assert "generation" in row["headroomAdmission"]["reason"].lower()
    assert "load" in row["headroomAdmission"]["reason"].lower()


def test_no_turn_citations_and_no_trade_authority() -> None:
    doc = json.loads(MEASUREMENTS.read_text())
    for evidence in doc["evidence"]:
        assert "turn" not in evidence["persistentIdentity"]
    assert doc["effectBoundary"] == {
        "externalFinancialWritesAllowed": False,
        "ownerRiskBudgetInferred": False,
        "investmentRecommendationAuthority": False,
        "decisionStateRegistryMutationIncluded": False,
    }


def test_invalid_graph_digest_fails_closed(tmp_path: Path) -> None:
    graph = tmp_path / "graph.json"
    graph.write_text(GRAPH.read_text() + " ")
    with pytest.raises(ConstraintMeasurementValidationError):
        load_constraint_measurements(MEASUREMENTS, graph_path=graph)


def test_measurement_lego_is_registered_without_new_authority() -> None:
    registry = json.loads((ROOT / "config/capital_lego_registry.json").read_text())
    row = next(item for item in registry["entries"] if item["legoId"] == "capital.research.ai-infrastructure-constraint-measurements")
    assert row["ownerDomain"] == "research"
    assert row["status"] == "ACTIVE"
    assert row["functionalRoles"] == ["Validate", "Measure"]
    assert row["effectClass"] == "NONE"
    assert row["authorityRequirement"] == "NONE"

    fmap = json.loads((ROOT / "planning/functional-lego-map-r1.json").read_text())
    assert fmap["moduleCoverage"]["src/ordivon_capital/research/constraint_measurements.py"] == ["Validate", "Measure"]


def test_measurement_control_is_non_model_and_research_only() -> None:
    inventory = json.loads((ROOT / "config/quantitative_component_inventory.json").read_text())
    row = next(item for item in inventory["components"] if item["id"] == "ai-infrastructure-constraint-measurements-r1")
    assert row["classification"] == "CONTROL"
    assert row["sr26ModelStanding"] == "NON_MODEL"
    assert row["status"] == "RESEARCH_ONLY"
    assert row["validation"]["standing"] == "DEVELOPMENT_TESTED"


def test_measurement_and_graph_share_one_external_owner_responsibility() -> None:
    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    row = next(item for item in census["responsibilities"] if item["id"] == "research-ai-infrastructure-constraint-mapping")
    assert "src/ordivon_capital/research/constraint_graph.py" in row["sourcePatterns"]
    assert "src/ordivon_capital/research/constraint_measurements.py" in row["sourcePatterns"]
    assert "independent requirement denominator" in row["localResponsibility"]


def test_independent_deepseek_demand_narrows_cn_accelerator_gap_without_overclaiming() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "CN" and item["nodeKey"] == "accelerator-logic"
    )
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["deepseek-reported-950dt-demand-lower-bound-units"]["value"] == 160_000.0
    assert metrics["deepseek-reported-950dt-demand-lower-bound-units"]["standing"] == "OBSERVED"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"
    assert "950DT" in row["headroomAdmission"]["reason"]


def test_deepseek_order_creates_independent_hbm_demand_lower_bound_but_not_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "CN" and item["nodeKey"] == "hbm"
    )
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["deepseek-950dt-hbm-demand-lower-bound-pb-144gb"]["value"] == pytest.approx(23.04)
    assert metrics["domestic-model-vs-deepseek-memory-capacity-equivalent-ratio"]["value"] == pytest.approx(1.0)
    assert "NOT_HEADROOM" in metrics["domestic-model-vs-deepseek-memory-capacity-equivalent-ratio"]["claimBoundary"]
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"
    assert row["headroomAdmission"]["headroomRatio"] is None


def test_us_lpt_scenario_coverage_is_computable_but_not_current_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == "US" and item["nodeKey"] == "transformer-switchgear"
    )
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["nlr-us-lpt-availability-2025-low"]["value"] == 825.0
    assert metrics["nlr-us-lpt-availability-2025-high"]["value"] == 1400.0
    assert metrics["nlr-us-lpt-ac-scenario-annual-demand"]["value"] == 1510.0
    assert metrics["nlr-us-lpt-mt-scenario-annual-demand"]["value"] == 1370.0
    assert metrics["nlr-us-lpt-2025-scenario-coverage-low"]["value"] == pytest.approx(825.0 / 1510.0)
    assert metrics["nlr-us-lpt-2025-scenario-coverage-high"]["value"] == pytest.approx(1400.0 / 1370.0)
    assert row["headroomAdmission"]["standing"] == "BLOCKED_TIME_BASIS_MISMATCH"
    assert "average" in row["headroomAdmission"]["reason"].lower()


def test_scenario_coverage_interval_is_deterministic_and_not_headroom() -> None:
    from ordivon_capital.research.constraint_measurements import compute_coverage_interval

    result = compute_coverage_interval(
        supply_low=825.0,
        supply_high=1400.0,
        requirement_low=1370.0,
        requirement_high=1510.0,
    )
    assert result == {
        "coverageRatioLow": pytest.approx(825.0 / 1510.0),
        "coverageRatioHigh": pytest.approx(1400.0 / 1370.0),
    }
    with pytest.raises(ConstraintMeasurementValidationError):
        compute_coverage_interval(
            supply_low=1400.0,
            supply_high=825.0,
            requirement_low=1370.0,
            requirement_high=1510.0,
        )
