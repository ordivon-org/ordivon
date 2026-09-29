from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConstraintGraphValidationError(ValueError):
    """Validation failure for the bounded AI-infrastructure constraint graph."""


EXPECTED_NODE_ORDER = [
    "accelerator-logic",
    "hbm",
    "advanced-packaging",
    "ai-data-center-it",
    "electricity-generation",
    "transformer-switchgear",
    "grid-interconnection-transmission",
]
EXPECTED_EDGES = list(zip(EXPECTED_NODE_ORDER, EXPECTED_NODE_ORDER[1:]))
FRONTIER_ROLES = {"CURRENT_FRONTIER", "CANDIDATE_FRONTIER", "NOT_FRONTIER", "UNKNOWN"}
CONSTRAINT_CLASSES = {
    "DIGITAL_TECHNICAL",
    "CYBER_PHYSICAL",
    "INDUSTRIAL_THROUGHPUT",
    "INFRASTRUCTURE_INSTITUTIONAL",
}
CLOCKS = {
    "COGNITION_SEARCH",
    "VERIFICATION_QUALIFICATION",
    "MANUFACTURING_RAMP",
    "INFRASTRUCTURE_INSTITUTION",
}
CONFIDENCE = {"HIGH", "MODERATE", "LOW"}
HEADROOM_STANDINGS = {"AMPLE", "ADEQUATE", "TIGHT", "BINDING", "MIXED", "UNKNOWN"}
AI_LEVERAGE = {"HIGH", "MEDIUM", "LOW"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConstraintGraphValidationError(message)


def _nonempty_string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    _require(isinstance(value, list) and len(value) >= min_items, f"{label} must be an array")
    for index, item in enumerate(value):
        _nonempty_string(item, f"{label}[{index}]")
    return value


def compute_quantitative_headroom(*, capacity: float, requirement: float, unit: str) -> dict[str, Any]:
    _require(isinstance(capacity, (int, float)) and not isinstance(capacity, bool), "capacity must be numeric")
    _require(isinstance(requirement, (int, float)) and not isinstance(requirement, bool), "requirement must be numeric")
    _require(requirement > 0, "requirement must be > 0")
    _require(capacity >= 0, "capacity must be >= 0")
    _nonempty_string(unit, "unit")
    return {
        "mode": "QUANTITATIVE",
        "unit": unit,
        "capacity": float(capacity),
        "requirement": float(requirement),
        "headroomRatio": float(capacity) / float(requirement) - 1.0,
    }


def _validate_headroom(raw: Any, label: str) -> None:
    _require(isinstance(raw, dict), f"{label} must be an object")
    mode = raw.get("mode")
    _require(mode in {"QUALITATIVE", "QUANTITATIVE"}, f"{label}.mode mismatch")
    if mode == "QUALITATIVE":
        _require(set(raw) == {"mode", "standing", "reason"}, f"{label} qualitative keys mismatch")
        _require(raw["standing"] in HEADROOM_STANDINGS, f"{label}.standing mismatch")
        _nonempty_string(raw["reason"], f"{label}.reason")
        return
    _require(
        set(raw) == {"mode", "unit", "capacity", "requirement", "headroomRatio"},
        f"{label} quantitative keys mismatch",
    )
    expected = compute_quantitative_headroom(
        capacity=raw["capacity"], requirement=raw["requirement"], unit=raw["unit"]
    )
    _require(abs(raw["headroomRatio"] - expected["headroomRatio"]) < 1e-12, f"{label}.headroomRatio mismatch")


def validate_constraint_graph_document(doc: Any) -> dict[str, Any]:
    _require(isinstance(doc, dict), "constraint graph must be an object")
    required = {
        "schemaVersion",
        "kind",
        "truthRole",
        "asOfDate",
        "methodContract",
        "principles",
        "aggregationPolicy",
        "effectBoundary",
        "methodOwners",
        "evidence",
        "nodes",
        "edges",
        "jurisdictions",
        "counterfactuals",
    }
    _require(set(doc) == required, "constraint graph root keys mismatch")
    _require(doc["schemaVersion"] == 1, "schemaVersion must equal 1")
    _require(doc["kind"] == "ordivon.capital.ai-infrastructure-constraint-graph", "kind mismatch")
    _require(
        doc["truthRole"] == "RESEARCH_MODEL_NOT_PROVIDER_TRUTH_OR_INVESTMENT_AUTHORITY",
        "truthRole mismatch",
    )
    _nonempty_string(doc["asOfDate"], "asOfDate")

    method = doc["methodContract"]
    _require(isinstance(method, dict), "methodContract must be an object")
    _require(method.get("name") == "Recursive LEGO Calculus R2.1", "methodContract.name mismatch")
    digest = _nonempty_string(method.get("instructionDigest"), "methodContract.instructionDigest")
    _require(digest.startswith("sha256:") and len(digest) == 71, "methodContract digest must be sha256")

    _string_list(doc["principles"], "principles", min_items=4)
    aggregation = doc["aggregationPolicy"]
    _require(isinstance(aggregation, dict), "aggregationPolicy must be an object")
    _require(aggregation.get("aggregateScoreAllowed") is False, "aggregate score must remain forbidden")
    _require(aggregation.get("frontierSelection") == "EXPLICIT_EVIDENCE_BOUNDED_JUDGMENT", "frontier policy mismatch")

    effect = doc["effectBoundary"]
    _require(isinstance(effect, dict), "effectBoundary must be an object")
    _require(effect.get("externalFinancialWritesAllowed") is False, "financial writes must remain closed")
    _require(effect.get("ownerRiskBudgetInferred") is False, "owner risk budget must not be inferred")
    _require(effect.get("investmentRecommendationAuthority") is False, "research graph must not mint recommendation authority")

    owners = doc["methodOwners"]
    _require(isinstance(owners, list) and owners, "methodOwners must be non-empty")
    for index, row in enumerate(owners):
        _require(isinstance(row, dict), f"methodOwners[{index}] must be an object")
        _nonempty_string(row.get("owner"), f"methodOwners[{index}].owner")
        _nonempty_string(row.get("role"), f"methodOwners[{index}].role")
        _nonempty_string(row.get("canonicalUrl"), f"methodOwners[{index}].canonicalUrl")

    evidence_rows = doc["evidence"]
    _require(isinstance(evidence_rows, list) and evidence_rows, "evidence must be non-empty")
    evidence_ids: set[str] = set()
    for index, row in enumerate(evidence_rows):
        label = f"evidence[{index}]"
        _require(isinstance(row, dict), f"{label} must be an object")
        evidence_id = _nonempty_string(row.get("evidenceId"), f"{label}.evidenceId")
        _require(evidence_id not in evidence_ids, f"duplicate evidenceId {evidence_id}")
        evidence_ids.add(evidence_id)
        persistent = _nonempty_string(row.get("persistentIdentity"), f"{label}.persistentIdentity")
        _require("turn" not in persistent, f"{label} must not persist chat citation identities")
        canonical_url = _nonempty_string(row.get("canonicalUrl"), f"{label}.canonicalUrl")
        _require(canonical_url.startswith("https://"), f"{label}.canonicalUrl must be https")
        _nonempty_string(row.get("sourceClass"), f"{label}.sourceClass")
        _nonempty_string(row.get("claimBoundary"), f"{label}.claimBoundary")
        _nonempty_string(row.get("observedAt"), f"{label}.observedAt")

    nodes = doc["nodes"]
    _require(isinstance(nodes, list), "nodes must be an array")
    node_keys = [row.get("nodeKey") for row in nodes]
    _require(node_keys == EXPECTED_NODE_ORDER, "R1 node order drifted")
    for index, row in enumerate(nodes):
        label = f"nodes[{index}]"
        _require(isinstance(row, dict), f"{label} must be an object")
        _nonempty_string(row.get("label"), f"{label}.label")
        _require(row.get("constraintClass") in CONSTRAINT_CLASSES, f"{label}.constraintClass mismatch")
        _require(row.get("primaryClock") in CLOCKS, f"{label}.primaryClock mismatch")
        leverage = row.get("aiLeverage")
        _require(isinstance(leverage, dict), f"{label}.aiLeverage must be an object")
        _require(leverage.get("standing") in AI_LEVERAGE, f"{label}.aiLeverage.standing mismatch")
        _string_list(leverage.get("mechanisms"), f"{label}.aiLeverage.mechanisms", min_items=1)
        _string_list(leverage.get("ceilings"), f"{label}.aiLeverage.ceilings", min_items=1)
        _require(leverage.get("analyticConfidence") in CONFIDENCE, f"{label}.aiLeverage.analyticConfidence mismatch")
        refs = _string_list(leverage.get("evidenceIds"), f"{label}.aiLeverage.evidenceIds", min_items=1)
        _require(set(refs) <= evidence_ids, f"{label}.aiLeverage unknown evidence")
        readiness = row.get("readiness")
        _require(isinstance(readiness, dict), f"{label}.readiness must be an object")
        _require(readiness.get("mode") == "PORTFOLIO_LAYER_NOT_SINGLE_TECHNOLOGY", f"{label}.readiness mode mismatch")
        _require(readiness.get("trl") is None and readiness.get("mrl") is None, f"{label} must not invent aggregate TRL/MRL")
        _nonempty_string(readiness.get("reason"), f"{label}.readiness.reason")

    edges = doc["edges"]
    _require(isinstance(edges, list), "edges must be an array")
    edge_pairs = [(row.get("from"), row.get("to")) for row in edges]
    _require(edge_pairs == EXPECTED_EDGES, "R1 edge chain drifted")
    for index, row in enumerate(edges):
        _nonempty_string(row.get("relation"), f"edges[{index}].relation")
        _nonempty_string(row.get("assumption"), f"edges[{index}].assumption")

    jurisdictions = doc["jurisdictions"]
    _require(isinstance(jurisdictions, list) and jurisdictions, "jurisdictions must be non-empty")
    seen_jurisdictions: set[str] = set()
    for index, jurisdiction in enumerate(jurisdictions):
        label = f"jurisdictions[{index}]"
        _require(isinstance(jurisdiction, dict), f"{label} must be an object")
        code = _nonempty_string(jurisdiction.get("jurisdiction"), f"{label}.jurisdiction")
        _require(code not in seen_jurisdictions, f"duplicate jurisdiction {code}")
        seen_jurisdictions.add(code)
        _require(jurisdiction.get("aggregateScore") is None, f"{label}.aggregateScore must remain null")
        frontier_keys = _string_list(jurisdiction.get("frontierNodeKeys"), f"{label}.frontierNodeKeys")
        _require(set(frontier_keys) <= set(EXPECTED_NODE_ORDER), f"{label} unknown frontier node")
        states = jurisdiction.get("nodeStates")
        _require(isinstance(states, list), f"{label}.nodeStates must be an array")
        _require([row.get("nodeKey") for row in states] == EXPECTED_NODE_ORDER, f"{label} nodeStates must cover exact R1 chain")
        current_frontier: list[str] = []
        for state_index, state in enumerate(states):
            state_label = f"{label}.nodeStates[{state_index}]"
            role = state.get("frontierRole")
            _require(role in FRONTIER_ROLES, f"{state_label}.frontierRole mismatch")
            if role == "CURRENT_FRONTIER":
                current_frontier.append(state["nodeKey"])
            _validate_headroom(state.get("headroom"), f"{state_label}.headroom")
            _require(state.get("analyticConfidence") in CONFIDENCE, f"{state_label}.analyticConfidence mismatch")
            refs = _string_list(state.get("evidenceIds"), f"{state_label}.evidenceIds", min_items=1)
            _require(set(refs) <= evidence_ids, f"{state_label} unknown evidence")
            contrary = _string_list(state.get("contraryEvidenceIds"), f"{state_label}.contraryEvidenceIds")
            _require(set(contrary) <= evidence_ids, f"{state_label} unknown contrary evidence")
            _string_list(state.get("assumptions"), f"{state_label}.assumptions")
            _string_list(state.get("reopenConditions"), f"{state_label}.reopenConditions", min_items=1)
            currentness = state.get("currentness")
            _require(isinstance(currentness, dict), f"{state_label}.currentness must be object")
            _nonempty_string(currentness.get("observedAt"), f"{state_label}.currentness.observedAt")
            _require("expiresAt" in currentness, f"{state_label}.currentness.expiresAt missing")
            observations = state.get("quantitativeObservations")
            _require(isinstance(observations, list), f"{state_label}.quantitativeObservations must be array")
            for obs_index, observation in enumerate(observations):
                obs_label = f"{state_label}.quantitativeObservations[{obs_index}]"
                _require(isinstance(observation, dict), f"{obs_label} must be object")
                _nonempty_string(observation.get("metric"), f"{obs_label}.metric")
                _require(isinstance(observation.get("value"), (int, float)) and not isinstance(observation.get("value"), bool), f"{obs_label}.value numeric")
                _nonempty_string(observation.get("unit"), f"{obs_label}.unit")
                _nonempty_string(observation.get("scope"), f"{obs_label}.scope")
                obs_refs = _string_list(observation.get("evidenceIds"), f"{obs_label}.evidenceIds", min_items=1)
                _require(set(obs_refs) <= evidence_ids, f"{obs_label} unknown evidence")
        _require(frontier_keys == current_frontier, f"{label}.frontierNodeKeys must equal explicit CURRENT_FRONTIER states")

    counterfactuals = doc["counterfactuals"]
    _require(isinstance(counterfactuals, list) and counterfactuals, "counterfactuals must be non-empty")
    for index, row in enumerate(counterfactuals):
        label = f"counterfactuals[{index}]"
        _require(isinstance(row, dict), f"{label} must be an object")
        _require(row.get("truthRole") == "ILLUSTRATIVE_COUNTERFACTUAL_NOT_FORECAST", f"{label}.truthRole mismatch")
        _require(row.get("externalFinancialEffectAllowed") is False, f"{label} must not allow financial effect")
        demand = row.get("demandMultiplier")
        efficiency = row.get("algorithmicEfficiencyMultiplier")
        requirement = row.get("effectiveComputeRequirementMultiplier")
        for name, value in (("demandMultiplier", demand), ("algorithmicEfficiencyMultiplier", efficiency), ("effectiveComputeRequirementMultiplier", requirement)):
            _require(isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0, f"{label}.{name} must be > 0")
        _require(abs(requirement - demand / efficiency) < 1e-12, f"{label} multiplier bridge mismatch")
        candidate = _string_list(row.get("candidateFrontierNodeKeys"), f"{label}.candidateFrontierNodeKeys", min_items=1)
        _require(set(candidate) <= set(EXPECTED_NODE_ORDER), f"{label} unknown candidate frontier")
        _string_list(row.get("assumptions"), f"{label}.assumptions", min_items=1)
        _string_list(row.get("falsifiers"), f"{label}.falsifiers", min_items=1)

    return doc


def load_constraint_graph(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text())
    return validate_constraint_graph_document(raw)


def project_frontier(doc: dict[str, Any], jurisdiction: str) -> dict[str, Any]:
    validate_constraint_graph_document(doc)
    for row in doc["jurisdictions"]:
        if row["jurisdiction"] == jurisdiction:
            return {
                "jurisdiction": jurisdiction,
                "asOfDate": doc["asOfDate"],
                "frontierNodeKeys": list(row["frontierNodeKeys"]),
                "aggregateScore": None,
                "truthRole": doc["truthRole"],
            }
    raise ConstraintGraphValidationError(f"unknown jurisdiction: {jurisdiction}")
