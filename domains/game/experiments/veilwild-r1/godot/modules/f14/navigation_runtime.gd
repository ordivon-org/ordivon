class_name VeilwildNavigationRuntime
extends Node3D

## Resolves F13 semantic navigation actions into F14-owned legal world targets.
## It does not choose behavior state, threat thresholds, Human-visible cue meaning,
## or environment source geometry.

@export_range(0.01, 2.0, 0.01) var endpoint_tolerance_m: float = 0.35
@export_range(0.0, 20.0, 0.1) var min_evade_separation_gain_m: float = 1.0

signal intent_resolved(action: StringName, affordance_id: StringName, target_position_m: Vector3)
signal intent_rejected(action: StringName, reason: StringName)

func behavior_affordance_snapshot(navigation_map: RID, creature_position_m: Vector3, threat_position_m: Vector3) -> Dictionary:
    var candidates := collect_affordance_snapshots(navigation_map, creature_position_m, threat_position_m)
    var conceal := select_candidate_from_snapshots(&"SEEK_OR_MAINTAIN_CONCEALMENT", candidates, min_evade_separation_gain_m)
    var evade := select_candidate_from_snapshots(&"EVADE_FROM_THREAT", candidates, min_evade_separation_gain_m)
    return {
        "concealment_available": not conceal.is_empty(),
        "concealment_quality": float(conceal.get("concealmentSuitability", 0.0)),
        "escape_available": not evade.is_empty(),
        "selected_concealment_affordance_id": String(conceal.get("affordanceId", "")),
        "selected_escape_affordance_id": String(evade.get("affordanceId", "")),
        "navigation_map_iteration": NavigationServer3D.map_get_iteration_id(navigation_map) if navigation_map.is_valid() else 0,
    }

func resolve_nav_intent(nav_intent: Dictionary, navigation_map: RID, creature_position_m: Vector3, threat_position_m: Vector3) -> Dictionary:
    var action := StringName(String(nav_intent.get("action", "NONE")))
    if action in [&"NONE", &"FACE_THREAT", &"HOLD_POSITION", &"HOLD_OR_SLOW_REPOSITION"]:
        return {"accepted": true, "action": action, "locomotionRequired": false, "reason": &"NO_TRANSLATIONAL_TARGET"}
    if action not in [&"SEEK_OR_MAINTAIN_CONCEALMENT", &"EVADE_FROM_THREAT"]:
        intent_rejected.emit(action, &"UNKNOWN_F13_NAV_ACTION")
        return {"accepted": false, "action": action, "reason": &"UNKNOWN_F13_NAV_ACTION"}
    if not navigation_map.is_valid() or NavigationServer3D.map_get_iteration_id(navigation_map) == 0:
        intent_rejected.emit(action, &"NAVIGATION_MAP_UNSYNCHRONIZED")
        return {"accepted": false, "action": action, "reason": &"NAVIGATION_MAP_UNSYNCHRONIZED"}

    var candidates := collect_affordance_snapshots(navigation_map, creature_position_m, threat_position_m)
    var selected := select_candidate_from_snapshots(action, candidates, min_evade_separation_gain_m)
    if selected.is_empty():
        intent_rejected.emit(action, &"NO_REACHABLE_AFFORDANCE")
        return {"accepted": false, "action": action, "reason": &"NO_REACHABLE_AFFORDANCE"}

    var affordance_id := StringName(String(selected["affordanceId"]))
    var target: Vector3 = selected["navigationAnchorM"]
    intent_resolved.emit(action, affordance_id, target)
    return {
        "accepted": true,
        "action": action,
        "locomotionRequired": true,
        "affordanceId": affordance_id,
        "targetPositionM": target,
        "pathLengthM": float(selected["pathLengthM"]),
        "concealmentSuitability": float(selected["concealmentSuitability"]),
        "threatSeparationGainM": float(selected["threatSeparationGainM"]),
        "environmentRevision": String(selected["environmentRevision"]),
        "reason": &"F14_REACHABLE_AFFORDANCE_SELECTED",
    }

func collect_affordance_snapshots(navigation_map: RID, creature_position_m: Vector3, threat_position_m: Vector3) -> Array[Dictionary]:
    var snapshots: Array[Dictionary] = []
    if not navigation_map.is_valid() or NavigationServer3D.map_get_iteration_id(navigation_map) == 0:
        return snapshots
    for node in get_tree().get_nodes_in_group("veilwild_concealment_affordance"):
        if not node.has_method("validate_contract") or not node.has_method("contract_snapshot"):
            continue
        var errors: PackedStringArray = node.call("validate_contract")
        if not errors.is_empty():
            continue
        var snapshot: Dictionary = node.call("contract_snapshot")
        var anchor_value: Variant = snapshot.get("navigationAnchorM", null)
        if not (anchor_value is Vector3):
            continue
        var anchor: Vector3 = anchor_value
        var path := NavigationServer3D.map_get_path(navigation_map, creature_position_m, anchor, true)
        var reachable := path.size() >= 2 and path[path.size() - 1].distance_to(anchor) <= endpoint_tolerance_m
        snapshot["reachable"] = reachable
        snapshot["pathLengthM"] = _path_length(path) if reachable else INF
        snapshot["threatSeparationGainM"] = anchor.distance_to(threat_position_m) - creature_position_m.distance_to(threat_position_m)
        snapshots.append(snapshot)
    return snapshots

static func select_candidate_from_snapshots(action: StringName, candidates: Array[Dictionary], min_evade_gain_m: float) -> Dictionary:
    var selected: Dictionary = {}
    for candidate in candidates:
        if not bool(candidate.get("reachable", false)) or not bool(candidate.get("traversalEligible", false)):
            continue
        if action == &"EVADE_FROM_THREAT":
            if not bool(candidate.get("evasionEligible", false)):
                continue
            if float(candidate.get("threatSeparationGainM", -INF)) < min_evade_gain_m:
                continue
        elif action != &"SEEK_OR_MAINTAIN_CONCEALMENT":
            continue
        if selected.is_empty() or _candidate_precedes(action, candidate, selected):
            selected = candidate.duplicate(true)
    return selected

static func _candidate_precedes(action: StringName, candidate: Dictionary, incumbent: Dictionary) -> bool:
    if action == &"EVADE_FROM_THREAT":
        var gain := float(candidate.get("threatSeparationGainM", -INF))
        var incumbent_gain := float(incumbent.get("threatSeparationGainM", -INF))
        if not is_equal_approx(gain, incumbent_gain):
            return gain > incumbent_gain
    var suitability := float(candidate.get("concealmentSuitability", 0.0))
    var incumbent_suitability := float(incumbent.get("concealmentSuitability", 0.0))
    if not is_equal_approx(suitability, incumbent_suitability):
        return suitability > incumbent_suitability
    var path_length := float(candidate.get("pathLengthM", INF))
    var incumbent_path_length := float(incumbent.get("pathLengthM", INF))
    if not is_equal_approx(path_length, incumbent_path_length):
        return path_length < incumbent_path_length
    return String(candidate.get("affordanceId", "")) < String(incumbent.get("affordanceId", ""))

static func _path_length(path: PackedVector3Array) -> float:
    var total := 0.0
    for index in range(1, path.size()):
        total += path[index - 1].distance_to(path[index])
    return total
