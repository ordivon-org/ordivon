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


def _measurement_row(doc: dict, jurisdiction: str, node_key: str) -> dict:
    return next(
        item for item in doc["nodeMeasurements"]
        if item["jurisdiction"] == jurisdiction and item["nodeKey"] == node_key
    )


def test_cn_advanced_packaging_preserves_currentness_gap_instead_of_promoting_historical_utilization() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "CN", "advanced-packaging")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["sjsemi-chiplet-multichip-utilization-2025h1"]["value"] == pytest.approx(63.42)
    assert metrics["sjsemi-chiplet-multichip-revenue-growth-2026h1"]["value"] == pytest.approx(2.61)
    assert row["demandSupplySignal"] == "PACKAGING_CAPABILITY_REAL_CURRENT_BINDING_STATUS_UNRESOLVED_UPSTREAM_INPUT_TIGHTNESS"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_TIME_BASIS_MISMATCH"
    assert "2026" in row["headroomAdmission"]["resolutionRequirement"]


def test_us_hbm_is_global_allocation_scarcity_not_us_specific_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "US", "hbm")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["trendforce-hbm-share-dram-wafer-input-2026ye"]["value"] == pytest.approx(22.0)
    assert metrics["trendforce-dram-sufficiency-2026-low"]["value"] == pytest.approx(-2.0)
    assert metrics["trendforce-dram-sufficiency-2026-high"]["value"] == pytest.approx(-1.0)
    assert row["demandSupplySignal"] == "GLOBAL_HBM_TIGHT_US_ECOSYSTEM_ALLOCATION_HEADROOM_UNKNOWN"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_us_advanced_packaging_records_global_gap_without_pretending_us_domestic_capacity() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "US", "advanced-packaging")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["trendforce-cowos-gap-mid-2026"]["value"] == pytest.approx(20.0)
    assert metrics["trendforce-cowos-gap-end-2026"]["value"] == pytest.approx(10.0)
    assert metrics["trendforce-tsmc-cowos-capacity-2026-low"]["value"] == pytest.approx(120.0)
    assert metrics["trendforce-tsmc-cowos-capacity-2026-high"]["value"] == pytest.approx(140.0)
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"
    assert "allocation" in row["headroomAdmission"]["resolutionRequirement"].lower()


def test_us_ai_ready_dc_distinguishes_market_scarcity_from_ai_specific_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "US", "ai-data-center-it")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["cbre-primary-market-inventory-h1-2026"]["value"] == pytest.approx(10903.0)
    assert metrics["cbre-primary-market-vacancy-h1-2026"]["value"] == pytest.approx(1.4)
    assert metrics["cbre-primary-market-under-construction-h1-2026"]["value"] == pytest.approx(7481.1)
    assert metrics["cbre-primary-market-preleased-share-h1-2026"]["value"] == pytest.approx(80.4)
    assert row["demandSupplySignal"] == "MARKET_CAPACITY_SCARCE_POWER_DELIVERY_AND_AI_SPECIFIC_SCOPE_NOT_SEPARATED"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_us_generation_keeps_national_nameplate_separate_from_local_firm_ai_power() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "US", "electricity-generation")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["eia-planned-utility-scale-additions-2026"]["value"] == pytest.approx(86.0)
    assert metrics["eia-realized-utility-scale-additions-2025"]["value"] == pytest.approx(53.0)
    assert metrics["eia-us-load-growth-2026"]["value"] == pytest.approx(1.9)
    assert metrics["eia-us-load-growth-2027"]["value"] == pytest.approx(2.5)
    assert row["demandSupplySignal"] == "NATIONAL_ADDITIONS_STRONG_LOCAL_FIRM_DELIVERABILITY_MIXED"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_p1_nodes_remain_non_headroom_until_scope_bridge_is_closed() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    pairs = [
        ("CN", "advanced-packaging"),
        ("US", "hbm"),
        ("US", "advanced-packaging"),
        ("US", "ai-data-center-it"),
        ("US", "electricity-generation"),
    ]
    for jurisdiction, node_key in pairs:
        row = _measurement_row(doc, jurisdiction, node_key)
        assert row["headroomAdmission"]["headroomRatio"] is None
        assert row["headroomAdmission"]["standing"] != "ADMITTED"


def test_cn_ai_dc_monitor_tracks_scale_and_load_growth_without_ai_only_headroom() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "CN", "ai-data-center-it")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["cn-standard-racks-june-2026"]["value"] == pytest.approx(15.56)
    assert metrics["cn-intelligent-compute-fp16-june-2026"]["value"] == pytest.approx(2185.0)
    assert metrics["cn-internet-data-services-electricity-jan-aug-2026"]["value"] == pytest.approx(69.5)
    assert metrics["cn-internet-data-services-electricity-yoy-jan-aug-2026"]["value"] == pytest.approx(42.5)
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_cn_generation_monitor_preserves_nameplate_peak_and_firm_capacity_distinction() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "CN", "electricity-generation")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["cn-installed-generation-july-2026"]["value"] == pytest.approx(4.08)
    assert metrics["cn-new-generation-jan-july-2026"]["value"] == pytest.approx(194.0)
    assert metrics["cn-system-peak-load-august-2026"]["value"] == pytest.approx(1.56)
    assert row["demandSupplySignal"] == "NATIONAL_SUPPLY_SCALE_LARGE_PEAKS_ABSORBED_LOCAL_FIRM_POWER_STILL_SITE_SPECIFIC"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_cn_transformer_monitor_detects_tight_orders_despite_export_strength() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "CN", "transformer-switchgear")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["cn-transformer-export-value-2026h1"]["value"] == pytest.approx(39.792)
    assert metrics["cn-transformer-export-value-yoy-2026h1"]["value"] == pytest.approx(26.78)
    assert metrics["cn-gt10mva-liquid-transformer-export-growth-2026h1"]["value"] == pytest.approx(50.0)
    assert row["demandSupplySignal"] == "STRONG_MANUFACTURING_AND_EXPORTS_BUT_ORDER_BOOKS_TIGHT_DATA_CENTER_DELIVERIES_EXTEND_TO_2027"
    assert row["headroomAdmission"]["standing"] == "BLOCKED_REQUIREMENT_UNKNOWN"
    assert "2027" in row["headroomAdmission"]["reason"]


def test_cn_grid_monitor_records_large_transfer_system_without_local_site_inference() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    row = _measurement_row(doc, "CN", "grid-interconnection-transmission")
    metrics = {item["metricKey"]: item for item in row["measurements"]}
    assert metrics["cn-operating-uhv-corridors-summer-2026"]["value"] == pytest.approx(46.0)
    assert metrics["cn-west-east-transfer-capability-summer-2026"]["value"] == pytest.approx(340.0)
    assert row["headroomAdmission"]["standing"] == "BLOCKED_SCOPE_MISMATCH"


def test_every_fill_queue_pair_now_has_a_measurement_state() -> None:
    doc = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    measured = {(row["jurisdiction"], row["nodeKey"]) for row in doc["nodeMeasurements"]}
    queued = {(row["jurisdiction"], row["nodeKey"]) for row in doc["fillQueue"]}
    assert queued <= measured
