from __future__ import annotations

import json
from pathlib import Path

from ordivon_capital.research.constraint_graph import load_constraint_graph
from ordivon_capital.research.constraint_measurements import load_constraint_measurements
from ordivon_capital.research.constraint_observatory import (
    evaluate_reentry_candidate,
    load_constraint_observatory,
    prioritized_watch_specs,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "config/ai_infrastructure_constraint_graph_r1.json"
MEASUREMENTS = ROOT / "config/ai_infrastructure_constraint_measurements_r1.json"
OBSERVATORY = ROOT / "config/ai_infrastructure_constraint_observatory_r1.json"


def _docs() -> tuple[dict, dict, dict]:
    graph = load_constraint_graph(GRAPH)
    measurements = load_constraint_measurements(MEASUREMENTS, graph_path=GRAPH)
    observatory = load_constraint_observatory(
        OBSERVATORY,
        graph_path=GRAPH,
        measurements_path=MEASUREMENTS,
    )
    return graph, measurements, observatory


def _candidate(
    *,
    watch_key: str,
    observed_at: str = "2026-09-30",
    source_class: str = "PRIMARY_PROVIDER_OR_COMPANY",
    source_standing: str = "CALLER_QUALIFIED",
    material_delta: bool = True,
    gap_ids: list[str] | None = None,
    graph_trigger_ids: list[str] | None = None,
) -> dict:
    return {
        "watchKey": watch_key,
        "persistentIdentity": "url:https://example.com/exact-evidence-object",
        "canonicalUrl": "https://example.com/exact-evidence-object",
        "sourceClass": source_class,
        "sourceStanding": source_standing,
        "observedAt": observed_at,
        "materialDelta": material_delta,
        "gapIds": gap_ids or [],
        "graphTriggerIds": graph_trigger_ids or [],
    }


def test_observatory_binds_exact_graph_measurements_and_covers_queue_once() -> None:
    graph, measurements, observatory = _docs()
    assert observatory["kind"] == "ordivon.capital.ai-infrastructure-constraint-observatory"
    assert observatory["truthRole"] == "REENTRY_CONTROL_NOT_PROVIDER_TRUTH_OR_SCHEDULER"
    watches = observatory["watchSpecs"]
    queue_pairs = {(row["jurisdiction"], row["nodeKey"]) for row in measurements["fillQueue"]}
    watch_pairs = {(row["jurisdiction"], row["nodeKey"]) for row in watches}
    assert len(watches) == 13
    assert len(watch_pairs) == 13
    assert watch_pairs == queue_pairs
    assert graph["asOfDate"] == "2026-09-29"


def test_observatory_is_read_only_control_not_fetcher_scheduler_or_graph_writer() -> None:
    _, _, observatory = _docs()
    assert observatory["effectBoundary"] == {
        "networkFetchIncluded": False,
        "schedulerAuthority": False,
        "providerTruthAuthority": False,
        "graphMutationIncluded": False,
        "measurementMutationIncluded": False,
        "decisionStateRegistryMutationIncluded": False,
        "investmentRecommendationAuthority": False,
        "ownerRiskBudgetInferred": False,
        "externalFinancialWritesAllowed": False,
    }


def test_watch_plan_preserves_fill_priority_and_exact_next_observations() -> None:
    _, measurements, observatory = _docs()
    ordered = prioritized_watch_specs(observatory)
    assert [(row["jurisdiction"], row["nodeKey"]) for row in ordered[:4]] == [
        ("CN", "accelerator-logic"),
        ("CN", "hbm"),
        ("US", "transformer-switchgear"),
        ("US", "grid-interconnection-transmission"),
    ]
    measurement_rows = {
        (row["jurisdiction"], row["nodeKey"]): row
        for row in measurements["nodeMeasurements"]
    }
    for watch in ordered:
        pair = (watch["jurisdiction"], watch["nodeKey"])
        assert watch["nextObservations"] == measurement_rows[pair]["nextObservations"]


def test_stale_candidate_does_not_reopen_anything() -> None:
    graph, _, observatory = _docs()
    result = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="CN:hbm",
            observed_at="2026-09-29",
            gap_ids=["QUALIFIED_FINISHED_SUPPLY"],
        ),
        graph_doc=graph,
    )
    assert result["standing"] == "NO_REENTRY"
    assert result["reasonCode"] == "NOT_NEWER_THAN_CURRENT_STATE"
    assert result["measurementReentryRequired"] is False
    assert result["graphReentryRequired"] is False


def test_unqualified_or_wrong_source_class_cannot_reopen() -> None:
    graph, _, observatory = _docs()
    unqualified = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="CN:hbm",
            source_standing="UNQUALIFIED",
            gap_ids=["QUALIFIED_FINISHED_SUPPLY"],
        ),
        graph_doc=graph,
    )
    assert unqualified["reasonCode"] == "SOURCE_NOT_CALLER_QUALIFIED"

    wrong_class = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="CN:hbm",
            source_class="SOCIAL_MEDIA_RUMOR",
            gap_ids=["QUALIFIED_FINISHED_SUPPLY"],
        ),
        graph_doc=graph,
    )
    assert wrong_class["reasonCode"] == "SOURCE_CLASS_NOT_ADMITTED_FOR_WATCH"


def test_matching_gap_evidence_reopens_measurement_only_without_certifying_headroom() -> None:
    graph, _, observatory = _docs()
    result = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="CN:hbm",
            gap_ids=["QUALIFIED_FINISHED_SUPPLY", "DELIVERY_STATUS"],
        ),
        graph_doc=graph,
    )
    assert result["standing"] == "REENTER_MEASUREMENT"
    assert result["reasonCode"] == "MATERIAL_GAP_EVIDENCE"
    assert result["measurementReentryRequired"] is True
    assert result["graphReentryRequired"] is False
    assert result["recomputeJurisdictionFrontier"] is False
    assert result["matchedGapIds"] == ["QUALIFIED_FINISHED_SUPPLY", "DELIVERY_STATUS"]
    assert result["headroomAdmitted"] is False


def test_candidate_schedule_blocker_reopens_graph_and_measurement() -> None:
    graph, _, observatory = _docs()
    result = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="CN:transformer-switchgear",
            gap_ids=["BACKLOG"],
            graph_trigger_ids=["CANDIDATE_REPEATED_SCHEDULE_BLOCKER"],
        ),
        graph_doc=graph,
    )
    assert result["standing"] == "REENTER_GRAPH_AND_MEASUREMENT"
    assert result["reasonCode"] == "MATERIAL_GRAPH_TRIGGER"
    assert result["measurementReentryRequired"] is True
    assert result["graphReentryRequired"] is True
    assert result["recomputeJurisdictionFrontier"] is True
    assert result["affectedJurisdiction"] == "CN"
    assert result["affectedNodeKeys"] == ["transformer-switchgear"]
    assert result["graphMutationAllowed"] is False


def test_irrelevant_or_nonmaterial_candidate_does_not_reopen() -> None:
    graph, _, observatory = _docs()
    irrelevant = evaluate_reentry_candidate(
        observatory,
        _candidate(watch_key="US:hbm", gap_ids=["LOCAL_WEATHER"]),
        graph_doc=graph,
    )
    assert irrelevant["standing"] == "NO_REENTRY"
    assert irrelevant["reasonCode"] == "NO_MATCHED_REENTRY_CONDITION"

    nonmaterial = evaluate_reentry_candidate(
        observatory,
        _candidate(
            watch_key="US:hbm",
            material_delta=False,
            gap_ids=["PLATFORM_ALLOCATION"],
        ),
        graph_doc=graph,
    )
    assert nonmaterial["reasonCode"] == "NO_MATERIAL_DELTA"


def test_observatory_is_registered_as_non_model_read_only_reentry_control() -> None:
    registry = json.loads((ROOT / "config/capital_lego_registry.json").read_text())
    row = next(
        item for item in registry["entries"]
        if item["legoId"] == "capital.research.ai-infrastructure-constraint-observatory"
    )
    assert row["ownerDomain"] == "research"
    assert row["functionalRoles"] == ["Validate", "Reconcile"]
    assert row["authorityRequirement"] == "NONE"
    assert row["effectClass"] == "NONE"
    assert row["sideEffects"] == []
    assert "provider truth" in " ".join(row["prohibitedUses"]).lower()
    assert "scheduler" in " ".join(row["prohibitedUses"]).lower()

    fmap = json.loads((ROOT / "planning/functional-lego-map-r1.json").read_text())
    assert fmap["moduleCoverage"]["src/ordivon_capital/research/constraint_observatory.py"] == [
        "Validate",
        "Reconcile",
    ]

    inventory = json.loads((ROOT / "config/quantitative_component_inventory.json").read_text())
    component = next(
        item for item in inventory["components"]
        if item["id"] == "ai-infrastructure-constraint-observatory-r1"
    )
    assert component["classification"] == "CONTROL"
    assert component["sr26ModelStanding"] == "NON_MODEL"
    assert component["status"] == "RESEARCH_ONLY"

    census = json.loads((ROOT / "config/external_owner_census.json").read_text())
    responsibility = next(
        item for item in census["responsibilities"]
        if item["id"] == "research-ai-infrastructure-constraint-mapping"
    )
    assert "src/ordivon_capital/research/constraint_observatory.py" in responsibility["sourcePatterns"]
    assert "does not own scheduling" in responsibility["localResponsibility"]


def test_observatory_has_draft_2020_12_schema_carrier_without_runtime_jsonschema_dependency() -> None:
    schema_path = ROOT / "schema/ai-infrastructure-constraint-observatory-r1.schema.json"
    schema = json.loads(schema_path.read_text())
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "ordivon.capital.schema.ai-infrastructure-constraint-observatory-r1"
    assert schema["properties"]["kind"]["const"] == "ordivon.capital.ai-infrastructure-constraint-observatory"
    assert schema["additionalProperties"] is False

    registry = json.loads((ROOT / "config/capital_lego_registry.json").read_text())
    row = next(
        item for item in registry["entries"]
        if item["legoId"] == "capital.research.ai-infrastructure-constraint-observatory"
    )
    assert "schema/ai-infrastructure-constraint-observatory-r1.schema.json" in row["inputContracts"]
    assert "jsonschema" not in (ROOT / "pyproject.toml").read_text().lower()
