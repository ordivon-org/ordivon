from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


class ConstraintObservatoryValidationError(ValueError):
    """Validation failure for the bounded AI-infrastructure re-entry control."""


PRIORITIES = {"P0_CURRENT_FRONTIER", "P1_CANDIDATE_FRONTIER", "P2_MONITOR"}
PRIORITY_ORDER = {"P0_CURRENT_FRONTIER": 0, "P1_CANDIDATE_FRONTIER": 1, "P2_MONITOR": 2}
SOURCE_STANDINGS = {"CALLER_QUALIFIED", "UNQUALIFIED"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConstraintObservatoryValidationError(message)


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be a non-empty string")
    return value


def _strings(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    _require(isinstance(value, list) and len(value) >= min_items, f"{label} must be an array")
    for index, item in enumerate(value):
        _string(item, f"{label}[{index}]")
    _require(len(set(value)) == len(value), f"{label} must not contain duplicates")
    return value


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _iso_date(value: Any, label: str) -> date:
    raw = _string(value, label)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ConstraintObservatoryValidationError(f"{label} must be ISO YYYY-MM-DD") from exc


def validate_constraint_observatory_document(
    doc: Any,
    *,
    graph_path: Path,
    measurements_path: Path,
) -> dict[str, Any]:
    _require(isinstance(doc, dict), "observatory document must be an object")
    required = {
        "schemaVersion", "kind", "truthRole", "asOfDate", "graphBinding",
        "measurementBinding", "principles", "effectBoundary",
        "sourceQualificationContract", "gapVocabulary", "graphTriggerVocabulary",
        "watchSpecs",
    }
    _require(set(doc) == required, "observatory root keys mismatch")
    _require(doc["schemaVersion"] == 1, "schemaVersion must equal 1")
    _require(doc["kind"] == "ordivon.capital.ai-infrastructure-constraint-observatory", "kind mismatch")
    _require(doc["truthRole"] == "REENTRY_CONTROL_NOT_PROVIDER_TRUTH_OR_SCHEDULER", "truthRole mismatch")
    _iso_date(doc["asOfDate"], "asOfDate")

    _require(doc["graphBinding"] == {
        "relativePath": "config/ai_infrastructure_constraint_graph_r1.json",
        "expectedDigest": _digest(graph_path),
    }, "graph binding mismatch")
    _require(doc["measurementBinding"] == {
        "relativePath": "config/ai_infrastructure_constraint_measurements_r1.json",
        "expectedDigest": _digest(measurements_path),
    }, "measurement binding mismatch")
    _strings(doc["principles"], "principles", min_items=5)
    _require(doc["effectBoundary"] == {
        "networkFetchIncluded": False,
        "schedulerAuthority": False,
        "providerTruthAuthority": False,
        "graphMutationIncluded": False,
        "measurementMutationIncluded": False,
        "decisionStateRegistryMutationIncluded": False,
        "investmentRecommendationAuthority": False,
        "ownerRiskBudgetInferred": False,
        "externalFinancialWritesAllowed": False,
    }, "effectBoundary mismatch")

    qualification = doc["sourceQualificationContract"]
    _require(isinstance(qualification, dict), "sourceQualificationContract must be object")
    _require(qualification.get("requiredStanding") == "CALLER_QUALIFIED", "source qualification standing mismatch")
    _require(qualification.get("observatoryMayQualifySource") is False, "observatory must not qualify source truth")
    _string(qualification.get("reason"), "sourceQualificationContract.reason")

    gap_vocab = set(_strings(doc["gapVocabulary"], "gapVocabulary", min_items=1))
    trigger_vocab = set(_strings(doc["graphTriggerVocabulary"], "graphTriggerVocabulary", min_items=1))
    graph_doc = json.loads(graph_path.read_text())
    measurement_doc = json.loads(measurements_path.read_text())
    queue_rows = {(r["jurisdiction"], r["nodeKey"]): r for r in measurement_doc["fillQueue"]}
    measurement_rows = {(r["jurisdiction"], r["nodeKey"]): r for r in measurement_doc["nodeMeasurements"]}
    graph_pairs = {(j["jurisdiction"], s["nodeKey"]) for j in graph_doc["jurisdictions"] for s in j["nodeStates"]}

    watches = doc["watchSpecs"]
    _require(isinstance(watches, list) and watches, "watchSpecs must be non-empty")
    seen_watch_keys: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for index, watch in enumerate(watches):
        label = f"watchSpecs[{index}]"
        _require(isinstance(watch, dict), f"{label} must be object")
        _require(set(watch) == {
            "watchKey", "jurisdiction", "nodeKey", "priority", "order",
            "naturalOwners", "acceptedSourceClasses", "requiredGapIds",
            "graphReentryTriggerIds", "nextObservations",
        }, f"{label} keys mismatch")
        watch_key = _string(watch["watchKey"], f"{label}.watchKey")
        jurisdiction = _string(watch["jurisdiction"], f"{label}.jurisdiction")
        node_key = _string(watch["nodeKey"], f"{label}.nodeKey")
        pair = (jurisdiction, node_key)
        _require(watch_key == f"{jurisdiction}:{node_key}", f"{label}.watchKey mismatch")
        _require(watch_key not in seen_watch_keys, f"duplicate watchKey {watch_key}")
        _require(pair not in seen_pairs, f"duplicate watch pair {pair}")
        seen_watch_keys.add(watch_key); seen_pairs.add(pair)
        _require(pair in graph_pairs and pair in queue_rows and pair in measurement_rows, f"{label} pair not bound")
        queue = queue_rows[pair]
        _require(watch["priority"] in PRIORITIES and watch["priority"] == queue["priority"], f"{label}.priority drifted")
        _require(isinstance(watch["order"], int) and not isinstance(watch["order"], bool), f"{label}.order integer")
        _require(watch["order"] == queue["order"], f"{label}.order drifted")
        _strings(watch["naturalOwners"], f"{label}.naturalOwners", min_items=1)
        _strings(watch["acceptedSourceClasses"], f"{label}.acceptedSourceClasses", min_items=1)
        gaps = _strings(watch["requiredGapIds"], f"{label}.requiredGapIds", min_items=1)
        _require(set(gaps) <= gap_vocab, f"{label} unknown requiredGapIds")
        triggers = _strings(watch["graphReentryTriggerIds"], f"{label}.graphReentryTriggerIds", min_items=1)
        _require(set(triggers) <= trigger_vocab, f"{label} unknown graph trigger")
        _require(watch["nextObservations"] == measurement_rows[pair]["nextObservations"], f"{label}.nextObservations drifted")
    _require(seen_pairs == set(queue_rows), "watchSpecs must exactly cover fillQueue pairs")
    return doc


def load_constraint_observatory(path: Path, *, graph_path: Path, measurements_path: Path) -> dict[str, Any]:
    return validate_constraint_observatory_document(json.loads(path.read_text()), graph_path=graph_path, measurements_path=measurements_path)


def prioritized_watch_specs(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(doc["watchSpecs"], key=lambda r: (PRIORITY_ORDER[r["priority"]], r["order"], r["watchKey"]))


def _no_reentry(*, watch: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "standing": "NO_REENTRY", "reasonCode": reason, "watchKey": watch["watchKey"],
        "affectedJurisdiction": watch["jurisdiction"], "affectedNodeKeys": [watch["nodeKey"]],
        "matchedGapIds": [], "matchedGraphTriggerIds": [],
        "measurementReentryRequired": False, "graphReentryRequired": False,
        "recomputeJurisdictionFrontier": False, "headroomAdmitted": False,
        "graphMutationAllowed": False,
    }


def evaluate_reentry_candidate(doc: dict[str, Any], candidate: Any, *, graph_doc: dict[str, Any]) -> dict[str, Any]:
    """Route one already-qualified candidate to the smallest research re-entry."""
    _require(isinstance(candidate, dict), "candidate must be object")
    _require(set(candidate) == {
        "watchKey", "persistentIdentity", "canonicalUrl", "sourceClass",
        "sourceStanding", "observedAt", "materialDelta", "gapIds", "graphTriggerIds",
    }, "candidate keys mismatch")
    watch_key = _string(candidate["watchKey"], "candidate.watchKey")
    watches = {r["watchKey"]: r for r in doc["watchSpecs"]}
    _require(watch_key in watches, "candidate.watchKey unknown")
    watch = watches[watch_key]
    persistent = _string(candidate["persistentIdentity"], "candidate.persistentIdentity")
    _require("turn" not in persistent, "candidate must not use chat citation identity")
    url = _string(candidate["canonicalUrl"], "candidate.canonicalUrl")
    _require(url.startswith("https://"), "candidate.canonicalUrl must be https")
    source_class = _string(candidate["sourceClass"], "candidate.sourceClass")
    source_standing = _string(candidate["sourceStanding"], "candidate.sourceStanding")
    _require(source_standing in SOURCE_STANDINGS, "candidate.sourceStanding mismatch")
    observed_at = _iso_date(candidate["observedAt"], "candidate.observedAt")
    _require(isinstance(candidate["materialDelta"], bool), "candidate.materialDelta must be bool")
    gap_ids = _strings(candidate["gapIds"], "candidate.gapIds")
    trigger_ids = _strings(candidate["graphTriggerIds"], "candidate.graphTriggerIds")

    if source_standing != doc["sourceQualificationContract"]["requiredStanding"]:
        return _no_reentry(watch=watch, reason="SOURCE_NOT_CALLER_QUALIFIED")
    if source_class not in watch["acceptedSourceClasses"]:
        return _no_reentry(watch=watch, reason="SOURCE_CLASS_NOT_ADMITTED_FOR_WATCH")
    if not candidate["materialDelta"]:
        return _no_reentry(watch=watch, reason="NO_MATERIAL_DELTA")

    jurisdiction = next(r for r in graph_doc["jurisdictions"] if r["jurisdiction"] == watch["jurisdiction"])
    state = next(r for r in jurisdiction["nodeStates"] if r["nodeKey"] == watch["nodeKey"])
    current_observed_at = _iso_date(state["currentness"]["observedAt"], "graph state currentness.observedAt")
    if observed_at <= current_observed_at:
        return _no_reentry(watch=watch, reason="NOT_NEWER_THAN_CURRENT_STATE")

    matched_gaps = [x for x in gap_ids if x in watch["requiredGapIds"]]
    matched_triggers = [x for x in trigger_ids if x in watch["graphReentryTriggerIds"]]
    base = {
        "watchKey": watch_key, "affectedJurisdiction": watch["jurisdiction"],
        "affectedNodeKeys": [watch["nodeKey"]], "matchedGapIds": matched_gaps,
        "matchedGraphTriggerIds": matched_triggers, "headroomAdmitted": False,
        "graphMutationAllowed": False,
    }
    if matched_triggers:
        return {**base, "standing": "REENTER_GRAPH_AND_MEASUREMENT", "reasonCode": "MATERIAL_GRAPH_TRIGGER",
                "measurementReentryRequired": True, "graphReentryRequired": True,
                "recomputeJurisdictionFrontier": True}
    if matched_gaps:
        return {**base, "standing": "REENTER_MEASUREMENT", "reasonCode": "MATERIAL_GAP_EVIDENCE",
                "measurementReentryRequired": True, "graphReentryRequired": False,
                "recomputeJurisdictionFrontier": False}
    return _no_reentry(watch=watch, reason="NO_MATCHED_REENTRY_CONDITION")
