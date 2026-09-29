from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ConstraintMeasurementValidationError(ValueError):
    """Validation failure for AI-infrastructure constraint measurements."""


MEASUREMENT_STANDINGS = {"OBSERVED", "MODELED", "DERIVED", "UNKNOWN"}
HEADROOM_STANDINGS = {
    "ADMITTED",
    "BLOCKED_ENDOGENOUS_REQUIREMENT",
    "BLOCKED_REQUIREMENT_UNKNOWN",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_UNIT_MISMATCH",
    "BLOCKED_TIME_BASIS_MISMATCH",
}
PRIORITIES = {"P0_CURRENT_FRONTIER", "P1_CANDIDATE_FRONTIER", "P2_MONITOR"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConstraintMeasurementValidationError(message)


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be a non-empty string")
    return value


def _strings(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    _require(isinstance(value, list) and len(value) >= min_items, f"{label} must be an array")
    for index, item in enumerate(value):
        _string(item, f"{label}[{index}]")
    return value


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def compute_coverage_interval(
    *,
    supply_low: float,
    supply_high: float,
    requirement_low: float,
    requirement_high: float,
) -> dict[str, float]:
    """Compute a bounded supply/requirement coverage interval; this is not headroom admission."""
    values = {
        "supply_low": supply_low,
        "supply_high": supply_high,
        "requirement_low": requirement_low,
        "requirement_high": requirement_high,
    }
    for label, value in values.items():
        _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label} numeric")
        _require(value > 0, f"{label} must be > 0")
    _require(supply_low <= supply_high, "supply_low must be <= supply_high")
    _require(requirement_low <= requirement_high, "requirement_low must be <= requirement_high")
    return {
        "coverageRatioLow": float(supply_low) / float(requirement_high),
        "coverageRatioHigh": float(supply_high) / float(requirement_low),
    }


def evaluate_headroom_pair(
    *, capacity: dict[str, Any], requirement: dict[str, Any]
) -> dict[str, Any]:
    """Admit a headroom ratio only when the bridge to the problem quantity is valid."""
    for label, row in (("capacity", capacity), ("requirement", requirement)):
        _require(isinstance(row, dict), f"{label} must be an object")
        value = row.get("value")
        _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label}.value numeric")
        _require(value >= 0, f"{label}.value must be >= 0")
        _string(row.get("unit"), f"{label}.unit")
        _string(row.get("scope"), f"{label}.scope")
        _string(row.get("timeBasis"), f"{label}.timeBasis")
    _require(requirement["value"] > 0, "requirement.value must be > 0")
    if requirement.get("independentOfCapacityModel") is not True:
        return {"standing": "BLOCKED_ENDOGENOUS_REQUIREMENT", "headroomRatio": None}
    if capacity["unit"] != requirement["unit"]:
        return {"standing": "BLOCKED_UNIT_MISMATCH", "headroomRatio": None}
    if capacity["scope"] != requirement["scope"]:
        return {"standing": "BLOCKED_SCOPE_MISMATCH", "headroomRatio": None}
    if capacity["timeBasis"] != requirement["timeBasis"]:
        return {"standing": "BLOCKED_TIME_BASIS_MISMATCH", "headroomRatio": None}
    return {
        "standing": "ADMITTED",
        "headroomRatio": float(capacity["value"]) / float(requirement["value"]) - 1.0,
    }


def _validate_measurement(row: dict[str, Any], label: str, evidence_ids: set[str]) -> None:
    _string(row.get("metricKey"), f"{label}.metricKey")
    _require(row.get("standing") in MEASUREMENT_STANDINGS, f"{label}.standing mismatch")
    has_value = "value" in row
    has_values = "values" in row
    _require(has_value ^ has_values, f"{label} must have exactly one of value/values")
    if has_value:
        value = row["value"]
        _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label}.value numeric")
    else:
        values = row["values"]
        _require(isinstance(values, list) and values, f"{label}.values non-empty array")
        for index, value in enumerate(values):
            _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{label}.values[{index}] numeric")
    _string(row.get("unit"), f"{label}.unit")
    _string(row.get("scope"), f"{label}.scope")
    _string(row.get("timeBasis"), f"{label}.timeBasis")
    refs = _strings(row.get("evidenceIds"), f"{label}.evidenceIds", min_items=1)
    _require(set(refs) <= evidence_ids, f"{label} has unknown evidenceIds")
    _string(row.get("claimBoundary"), f"{label}.claimBoundary")


def validate_constraint_measurements_document(
    doc: Any, *, graph_path: Path
) -> dict[str, Any]:
    _require(isinstance(doc, dict), "measurement document must be an object")
    required = {
        "schemaVersion",
        "kind",
        "truthRole",
        "asOfDate",
        "graphBinding",
        "principles",
        "effectBoundary",
        "evidence",
        "fillQueue",
        "nodeMeasurements",
    }
    _require(set(doc) == required, "measurement document root keys mismatch")
    _require(doc["schemaVersion"] == 1, "schemaVersion must equal 1")
    _require(
        doc["kind"] == "ordivon.capital.ai-infrastructure-constraint-measurements",
        "kind mismatch",
    )
    _require(
        doc["truthRole"] == "MEASUREMENT_BINDING_NOT_PROVIDER_TRUTH_OR_HEADROOM_BY_DEFAULT",
        "truthRole mismatch",
    )
    _string(doc["asOfDate"], "asOfDate")

    binding = doc["graphBinding"]
    _require(isinstance(binding, dict), "graphBinding must be object")
    _require(binding.get("relativePath") == "config/ai_infrastructure_constraint_graph_r1.json", "graph path mismatch")
    _require(binding.get("expectedDigest") == _digest(graph_path), "graph digest mismatch")

    _strings(doc["principles"], "principles", min_items=4)
    effect = doc["effectBoundary"]
    _require(
        effect
        == {
            "externalFinancialWritesAllowed": False,
            "ownerRiskBudgetInferred": False,
            "investmentRecommendationAuthority": False,
            "decisionStateRegistryMutationIncluded": False,
        },
        "effect boundary mismatch",
    )

    evidence = doc["evidence"]
    _require(isinstance(evidence, list) and evidence, "evidence must be non-empty")
    evidence_ids: set[str] = set()
    for index, row in enumerate(evidence):
        label = f"evidence[{index}]"
        _require(isinstance(row, dict), f"{label} must be object")
        evidence_id = _string(row.get("evidenceId"), f"{label}.evidenceId")
        _require(evidence_id not in evidence_ids, f"duplicate evidenceId: {evidence_id}")
        evidence_ids.add(evidence_id)
        persistent = _string(row.get("persistentIdentity"), f"{label}.persistentIdentity")
        _require("turn" not in persistent, f"{label} must not persist chat citation identity")
        url = _string(row.get("canonicalUrl"), f"{label}.canonicalUrl")
        _require(url.startswith("https://"), f"{label}.canonicalUrl must be https")
        _string(row.get("sourceClass"), f"{label}.sourceClass")
        _string(row.get("claimBoundary"), f"{label}.claimBoundary")
        _string(row.get("observedAt"), f"{label}.observedAt")

    queue = doc["fillQueue"]
    _require(isinstance(queue, list) and queue, "fillQueue must be non-empty")
    seen_pairs: set[tuple[str, str]] = set()
    for index, row in enumerate(queue):
        label = f"fillQueue[{index}]"
        _require(isinstance(row, dict), f"{label} must be object")
        jurisdiction = _string(row.get("jurisdiction"), f"{label}.jurisdiction")
        node = _string(row.get("nodeKey"), f"{label}.nodeKey")
        pair = (jurisdiction, node)
        _require(pair not in seen_pairs, f"duplicate fillQueue pair {pair}")
        seen_pairs.add(pair)
        _require(row.get("priority") in PRIORITIES, f"{label}.priority mismatch")
        _string(row.get("reason"), f"{label}.reason")
        _strings(row.get("requiredMeasurements"), f"{label}.requiredMeasurements", min_items=1)

    node_rows = doc["nodeMeasurements"]
    _require(isinstance(node_rows, list) and node_rows, "nodeMeasurements must be non-empty")
    for index, row in enumerate(node_rows):
        label = f"nodeMeasurements[{index}]"
        _require(isinstance(row, dict), f"{label} must be object")
        _string(row.get("jurisdiction"), f"{label}.jurisdiction")
        _string(row.get("nodeKey"), f"{label}.nodeKey")
        _string(row.get("demandSupplySignal"), f"{label}.demandSupplySignal")
        measurements = row.get("measurements")
        _require(isinstance(measurements, list) and measurements, f"{label}.measurements non-empty")
        for measurement_index, measurement in enumerate(measurements):
            _validate_measurement(measurement, f"{label}.measurements[{measurement_index}]", evidence_ids)
        admission = row.get("headroomAdmission")
        _require(isinstance(admission, dict), f"{label}.headroomAdmission must be object")
        _require(admission.get("standing") in HEADROOM_STANDINGS, f"{label}.headroomAdmission standing mismatch")
        _require(admission.get("headroomRatio") is None or isinstance(admission.get("headroomRatio"), (int, float)), f"{label}.headroomAdmission ratio mismatch")
        _string(admission.get("reason"), f"{label}.headroomAdmission.reason")
        _string(admission.get("resolutionRequirement"), f"{label}.headroomAdmission.resolutionRequirement")
        _strings(row.get("nextObservations"), f"{label}.nextObservations", min_items=1)
    return doc


def load_constraint_measurements(path: Path, *, graph_path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text())
    return validate_constraint_measurements_document(raw, graph_path=graph_path)


def prioritized_fill_queue(doc: dict[str, Any]) -> list[dict[str, Any]]:
    priority_order = {"P0_CURRENT_FRONTIER": 0, "P1_CANDIDATE_FRONTIER": 1, "P2_MONITOR": 2}
    return sorted(doc["fillQueue"], key=lambda row: (priority_order[row["priority"]], row["order"]))
