from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from typing import Any


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _index(epoch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = epoch["nodes"]
    indexed = {node["id"]: node for node in nodes}
    if len(indexed) != len(nodes):
        raise ValueError("duplicate node id")
    return indexed


def _validate_epoch(epoch: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if epoch.get("schemaVersion") != 1 or epoch.get("kind") != "ordivon.dwc-defense-epoch":
        raise ValueError("unsupported defense epoch schema")
    nodes = _index(epoch)
    for node_id, node in nodes.items():
        if node.get("role") not in {"source", "derived"}:
            raise ValueError(f"node {node_id} has invalid role")
        owner_id = node.get("ownerId")
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError(f"node {node_id} ownerId must be explicit")
        digest = node.get("stateDigest")
        if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:"):
            raise ValueError(f"node {node_id} has invalid stateDigest")
        cost = node.get("revalidationCostUnits")
        if not isinstance(cost, int) or isinstance(cost, bool) or cost < 0:
            raise ValueError(f"node {node_id} has invalid revalidationCostUnits")

    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {node_id: 0 for node_id in nodes}
    for edge in epoch["edges"]:
        source, target = edge["from"], edge["to"]
        if source not in nodes or target not in nodes:
            raise ValueError(f"dangling dependency: {source}->{target}")
        if not isinstance(edge.get("invalidatesOnChange"), bool) or not isinstance(
            edge.get("temporalDependency"), bool
        ):
            raise ValueError(f"edge {source}->{target} dependency flags must be boolean")
        relation = edge.get("relation")
        if not isinstance(relation, str) or not relation.strip():
            raise ValueError(f"edge {source}->{target} relation must be explicit")
        if edge["invalidatesOnChange"]:
            if target not in adjacency[source]:
                adjacency[source].add(target)
                indegree[target] += 1

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in sorted(adjacency[source]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        raise ValueError("invalidation dependency graph is cyclic")
    return nodes


def _descendants(seeds: set[str], epoch: dict[str, Any]) -> set[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in epoch["edges"]:
        if edge["invalidatesOnChange"]:
            adjacency[edge["from"]].add(edge["to"])
    seen: set[str] = set()
    queue = deque(sorted(seeds))
    while queue:
        source = queue.popleft()
        for target in sorted(adjacency[source]):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def _delta(milestones: dict[str, Any], start: str, end: str) -> int | None:
    left = milestones.get(start)
    right = milestones.get(end)
    if left is None or right is None:
        return None
    if not isinstance(left, int) or isinstance(left, bool) or left < 0:
        raise ValueError(f"milestone {start} must be a non-negative integer or null")
    if not isinstance(right, int) or isinstance(right, bool) or right < 0:
        raise ValueError(f"milestone {end} must be a non-negative integer or null")
    if right < left:
        raise ValueError(f"milestone order invalid: {end} precedes {start}")
    return right - left


def _latency_projection(epoch: dict[str, Any]) -> dict[str, Any]:
    milestones = epoch.get("milestones", {})
    if not isinstance(milestones, dict):
        raise ValueError("milestones must be an object")
    allowed = {"T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "Tc", "Te", "Tr"}
    unknown_keys = set(milestones) - allowed
    if unknown_keys:
        raise ValueError(f"unknown milestone keys: {sorted(unknown_keys)}")
    for key, value in milestones.items():
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            raise ValueError(f"milestone {key} must be a non-negative integer or null")

    segment_pairs = [
        ("T0", "T1"),
        ("T1", "T2"),
        ("T2", "T3"),
        ("T3", "T4"),
        ("T4", "T5"),
        ("T5", "T6"),
        ("T6", "T7"),
    ]
    segments = {
        f"{start}->{end}": _delta(milestones, start, end)
        for start, end in segment_pairs
    }
    return {
        "milestones": {key: milestones.get(key) for key in sorted(allowed)},
        "segmentsMs": segments,
        "TTVPms": _delta(milestones, "T0", "T7"),
        "compromiseToEradicationMs": _delta(milestones, "Tc", "Te"),
        "compromiseToRecoveryMs": _delta(milestones, "Tc", "Tr"),
        "eradicationToRecoveryMs": _delta(milestones, "Te", "Tr"),
        "attackerTimingAssumed": False,
    }


def _critical_path(epoch: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stage_ids = sorted(
        node_id for node_id, node in nodes.items()
        if node.get("role") == "derived" and node.get("kind") == "stage"
    )
    stage_set = set(stage_ids)
    durations: dict[str, int] = {}
    unknown: list[str] = []
    for node_id in stage_ids:
        node = nodes[node_id]
        duration = node.get("durationMs")
        basis = node.get("durationBasis")
        if duration is None or basis is None:
            unknown.append(node_id)
            continue
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or duration < 0
            or basis not in {"OBSERVED", "POLICY_BUDGET"}
        ):
            raise ValueError(f"stage {node_id} has invalid explicit duration/basis")
        durations[node_id] = duration

    deadline = epoch.get("policyDeadline")
    deadline_value: int | None = None
    deadline_ref: str | None = None
    if deadline is not None:
        if not isinstance(deadline, dict):
            raise ValueError("policyDeadline must be an object or null")
        deadline_value = deadline.get("deadlineFromT0Ms")
        deadline_ref = deadline.get("sourceRef")
        if (
            not isinstance(deadline_value, int)
            or isinstance(deadline_value, bool)
            or deadline_value < 0
            or not isinstance(deadline_ref, str)
            or not deadline_ref
        ):
            raise ValueError("policyDeadline requires non-negative deadlineFromT0Ms and sourceRef")

    if unknown:
        return {
            "standing": "PARTIAL_UNKNOWN",
            "stageIds": [],
            "durationMs": None,
            "unknownDurationStageIds": unknown,
            "slackStanding": "UNKNOWN_DURATION",
            "slackMs": None,
            "deadlineFromT0Ms": deadline_value,
            "deadlineSourceRef": deadline_ref,
            "schedulerAuthorityEstablished": False,
        }

    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {node_id: 0 for node_id in stage_ids}
    for item in epoch["edges"]:
        if not item["temporalDependency"]:
            continue
        source, target = item["from"], item["to"]
        if source not in stage_set or target not in stage_set:
            raise ValueError(f"temporal dependency must connect stage nodes: {source}->{target}")
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        source = queue.popleft()
        order.append(source)
        for target in sorted(adjacency[source]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(order) != len(stage_ids):
        raise ValueError("temporal dependency graph is cyclic")

    distance = {node_id: durations[node_id] for node_id in stage_ids}
    parent: dict[str, str | None] = {node_id: None for node_id in stage_ids}
    for source in order:
        for target in sorted(adjacency[source]):
            candidate = distance[source] + durations[target]
            if candidate > distance[target] or (
                candidate == distance[target]
                and (parent[target] is None or source < parent[target])
            ):
                distance[target] = candidate
                parent[target] = source

    if not stage_ids:
        terminal = None
        path: list[str] = []
        duration_ms = 0
    else:
        terminal = min(
            stage_ids,
            key=lambda node_id: (-distance[node_id], node_id),
        )
        duration_ms = distance[terminal]
        path = []
        cursor: str | None = terminal
        while cursor is not None:
            path.append(cursor)
            cursor = parent[cursor]
        path.reverse()

    if deadline_value is None:
        slack_standing = "NO_POLICY_DEADLINE"
        slack_ms = None
    else:
        slack_standing = "KNOWN"
        slack_ms = deadline_value - duration_ms

    return {
        "standing": "KNOWN",
        "stageIds": path,
        "durationMs": duration_ms,
        "unknownDurationStageIds": [],
        "slackStanding": slack_standing,
        "slackMs": slack_ms,
        "deadlineFromT0Ms": deadline_value,
        "deadlineSourceRef": deadline_ref,
        "schedulerAuthorityEstablished": False,
    }


def project_epoch(previous_epoch: dict[str, Any] | None, current_epoch: dict[str, Any]) -> dict[str, Any]:
    previous = _validate_epoch(previous_epoch) if previous_epoch is not None else {}
    current = _validate_epoch(current_epoch)
    ids = set(previous) | set(current)
    changed = {
        node_id
        for node_id in ids
        if node_id not in previous
        or node_id not in current
        or (
            previous[node_id].get("stateDigest"),
            previous[node_id].get("standing"),
            previous[node_id].get("ownerId"),
            previous[node_id].get("role"),
            previous[node_id].get("kind"),
        )
        != (
            current[node_id].get("stateDigest"),
            current[node_id].get("standing"),
            current[node_id].get("ownerId"),
            current[node_id].get("role"),
            current[node_id].get("kind"),
        )
    }

    if previous_epoch is not None:
        previous_edges = {
            (item["from"], item["to"], item["relation"])
            for item in previous_epoch["edges"]
            if item["invalidatesOnChange"]
        }
        current_edges = {
            (item["from"], item["to"], item["relation"])
            for item in current_epoch["edges"]
            if item["invalidatesOnChange"]
        }
        for changed_edge in previous_edges ^ current_edges:
            target = changed_edge[1]
            if target in current:
                changed.add(target)

    impacted = _descendants(changed, current_epoch)
    impacted.update(
        node_id
        for node_id in changed
        if node_id in current and current[node_id]["role"] == "derived"
    )
    revalidation = sorted(
        node_id for node_id in impacted if node_id in current and current[node_id]["role"] == "derived"
    )
    all_derived = sorted(node_id for node_id, node in current.items() if node["role"] == "derived")
    selective_cost = sum(current[node_id]["revalidationCostUnits"] for node_id in revalidation)
    full_cost = sum(current[node_id]["revalidationCostUnits"] for node_id in all_derived)
    positive = {"VERIFIED", "SATISFIED", "COMPLETE", "PASS", "ADMISSIBLE", "CURRENT"}
    stale_risk = sorted(
        node_id
        for node_id in revalidation
        if node_id in previous and previous[node_id].get("standing") in positive
    )
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.dwc-temporal-invalidation-projection",
        "epochId": current_epoch["epochId"],
        "epochDigest": canonical_digest(current_epoch),
        "changedNodeIds": sorted(changed),
        "invalidatedNodeIds": revalidation,
        "revalidationNodeIds": revalidation,
        "unaffectedDerivedNodeIds": sorted(set(all_derived) - set(revalidation)),
        "staleSupportRiskNodeIds": stale_risk,
        "selectiveRevalidationCostUnits": selective_cost,
        "fullRecomputeCostUnits": full_cost,
        "costSavingsUnits": full_cost - selective_cost,
        "costSavingsRatio": (full_cost - selective_cost) / full_cost if full_cost else None,
        "latency": _latency_projection(current_epoch),
        "criticalPath": _critical_path(current_epoch, current),
        "schedulerAuthorityEstablished": False,
        "domainAcceptanceEstablished": False,
    }
    result["projectionDigest"] = canonical_digest(result)
    return result
