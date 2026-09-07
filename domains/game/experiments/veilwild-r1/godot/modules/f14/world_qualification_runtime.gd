class_name VeilwildWorldQualificationRuntime
extends Node

## A14/F14 owner predicate and post-EVADE world consequence.
## This node never emits observation_committed or success_consequence.

signal a17_world_qualifier_bound(receipt: Dictionary)
signal reacquisition_opportunity_emitted(witness: Dictionary)

const SOURCE_FRONT := "A14/F14"
const CLOSE_QUALIFIED_ID := "F14.VALID_CLOSE_OBSERVATION_WORLD_R4A"
const CLOSE_DENIED_ID := "F14.CLOSE_OBSERVATION_WORLD_NOT_QUALIFIED_R4A"
const REACQUISITION_ID := "F14.REACQUISITION_OPPORTUNITY_WORLD_ROUTE_R4A"
const F13_EVADE_STARTED_ID := "F13.EVADE_STARTED"
const FINAL_A08_GLB_SHA256 := "bc460bb8c48f8296d25a3f2e23323845e851b5669335ac6fb5a9126d3519c4d8"
const FINAL_A08_ENVELOPE_SHA256 := "fe0fdf2dd88b7f7df9e6c0aa8bf558559635062b640e69a509f7303d2c701896"
const FINAL_SELECTED_CREATURE_GLB_SHA256 := "73b36673858464190acfddc32030544ec66efc29f0f0a78d04e331a06b13345e"
const FINAL_SELECTED_CREATURE_PRODUCER_REVISION := "3f9f443256212e3286c4bf90c84fd1d5c224b1fc"
const FINAL_CREATURE_BONE_COUNT := 23
const FINAL_CREATURE_ROOT_BONE := "VW_ROOT"
const REQUIRED_RUNTIME_CLIPS := [
    "VW_MOTION_IDLE", "VW_MOTION_ORIENT", "VW_MOTION_FREEZE", "VW_MOTION_CONCEAL",
    "VW_MOTION_FORAGE", "VW_MOTION_EVADE", "VW_MOTION_RECOVER",
]

# F01 leaves distance/cone tunable outside product authority; F14 freezes these
# exact R4A world tunables. These are mechanical conditions, not Human fit claims.
const MAX_CLOSE_DISTANCE_M := 4.0
const MIN_FORWARD_DOT := 0.75
const MAX_REQUEST_ORIGIN_FROM_PLAYER_M := 2.40
const MAX_PLAYER_NAV_OFFSET_M := 0.60
const MAX_CREATURE_NAV_OFFSET_M := 1.80
const LOS_ENDPOINT_ALLOWANCE_M := 0.35
const MAX_PLAYER_FRAME_STEP_M := 1.50
const MAX_CREATURE_FRAME_STEP_M := 2.50
const MIN_POST_EVADE_CREATURE_DISPLACEMENT_M := 0.50

var _integration_root: Node = null
var _player: Node3D = null
var _creature: Node3D = null
var _event_bus: Node = null
var _player_instance_id := 0
var _creature_instance_id := 0
var _last_player_position := Vector3.ZERO
var _last_creature_position := Vector3.ZERO
var _continuity_armed := false
var _continuity_compromised := false
var _continuity_reason := ""
var _evade_pending := false
var _evade_sequence := 0
var _evade_creature_position := Vector3.ZERO
var _reacquisition_emitted_for_sequence := -1
var _last_reacquisition_witness: Dictionary = {}

@onready var _nav_mount: Node = get_parent()

func _ready() -> void:
    add_to_group("veilwild.f14.world_qualification")
    call_deferred("_bind_candidate_runtime")

func _physics_process(_delta: float) -> void:
    if not _continuity_armed:
        return
    if not _refresh_runtime_instances():
        _mark_continuity_compromised("RUNTIME_INSTANCE_IDENTITY_CHANGED")
        return
    var player_step := _player.global_position.distance_to(_last_player_position)
    var creature_step := _creature.global_position.distance_to(_last_creature_position)
    if player_step > MAX_PLAYER_FRAME_STEP_M:
        _mark_continuity_compromised("PLAYER_NONCONTINUOUS_STEP")
    if creature_step > MAX_CREATURE_FRAME_STEP_M:
        _mark_continuity_compromised("CREATURE_NONCONTINUOUS_STEP")
    _last_player_position = _player.global_position
    _last_creature_position = _creature.global_position
    if _evade_pending and not _continuity_compromised:
        _try_publish_reacquisition_opportunity()

func qualifier_callable() -> Callable:
    return Callable(self, "qualify_close_observation")

func runtime_health() -> Dictionary:
    return {
        "sourceFront": SOURCE_FRONT,
        "boundToA17": _integration_root != null,
        "playerBound": _player != null,
        "creatureBound": _creature != null,
        "continuityArmed": _continuity_armed,
        "continuityCompromised": _continuity_compromised,
        "continuityReason": _continuity_reason,
        "playerNavigationMapIteration": _map_iteration(_nav_mount.call("player_navigation_map")) if _nav_mount != null and _nav_mount.has_method("player_navigation_map") else 0,
        "creatureNavigationMapIteration": _map_iteration(_nav_mount.call("creature_navigation_map")) if _nav_mount != null and _nav_mount.has_method("creature_navigation_map") else 0,
        "animationEnvelopeSourceGlbSha256": FINAL_A08_GLB_SHA256,
        "finalCreatureEnvelopeSha256": FINAL_A08_ENVELOPE_SHA256,
        "expectedSelectedFinalCreatureGlbSha256": FINAL_SELECTED_CREATURE_GLB_SHA256,
        "expectedSelectedFinalCreatureProducerRevision": FINAL_SELECTED_CREATURE_PRODUCER_REVISION,
        "observationTunables": {
            "maxCloseDistanceM": MAX_CLOSE_DISTANCE_M,
            "minForwardDot": MIN_FORWARD_DOT,
            "maxRequestOriginFromPlayerM": MAX_REQUEST_ORIGIN_FROM_PLAYER_M,
        },
        "lastReacquisitionWitness": _last_reacquisition_witness.duplicate(true),
    }

func qualify_close_observation(request_id: int, origin: Vector3, forward: Vector3) -> Dictionary:
    var reasons: Array[String] = []
    var runtime_ok := _refresh_runtime_instances()
    if request_id <= 0:
        reasons.append("REQUEST_ID_INVALID")
    if not runtime_ok:
        reasons.append("A17_RUNTIME_INSTANCES_UNAVAILABLE")
    if _nav_mount == null or not _nav_mount.has_method("is_initialized") or not bool(_nav_mount.call("is_initialized")):
        reasons.append("F14_NAVIGATION_NOT_INITIALIZED")
    if _continuity_compromised:
        reasons.append("WORLD_CONTINUITY_COMPROMISED:%s" % _continuity_reason)
    if not runtime_ok:
        return _witness(request_id, false, reasons, {})

    var player_contract := _player_contract_witness()
    if not bool(player_contract.get("valid", false)):
        reasons.append("PLAYER_BODY_ENVELOPE_INVALID")
    var creature_identity := _creature_identity_witness()
    if not bool(creature_identity.get("valid", false)):
        reasons.append("FINAL_CREATURE_RUNTIME_IDENTITY_INVALID")

    var player_map: RID = _nav_mount.call("player_navigation_map")
    var creature_map: RID = _nav_mount.call("creature_navigation_map")
    var player_iteration := _map_iteration(player_map)
    var creature_iteration := _map_iteration(creature_map)
    if player_iteration <= 0 or creature_iteration <= 0:
        reasons.append("NAVIGATION_MAP_UNSYNCHRONIZED")

    var player_nav_offset := INF
    var creature_nav_offset := INF
    if player_iteration > 0:
        player_nav_offset = NavigationServer3D.map_get_closest_point(player_map, _player.global_position).distance_to(_player.global_position)
        if player_nav_offset > MAX_PLAYER_NAV_OFFSET_M:
            reasons.append("PLAYER_OUTSIDE_NAV_WORLD")
    if creature_iteration > 0:
        creature_nav_offset = NavigationServer3D.map_get_closest_point(creature_map, _creature.global_position).distance_to(_creature.global_position)
        if creature_nav_offset > MAX_CREATURE_NAV_OFFSET_M:
            reasons.append("CREATURE_OUTSIDE_FINAL_ENVELOPE_NAV_WORLD")

    var request_origin_offset := origin.distance_to(_player.global_position)
    if request_origin_offset > MAX_REQUEST_ORIGIN_FROM_PLAYER_M:
        reasons.append("REQUEST_ORIGIN_NOT_PLAYER_BOUND")
    var to_creature := _creature.global_position - origin
    var distance_m := to_creature.length()
    if distance_m <= 0.0001 or distance_m > MAX_CLOSE_DISTANCE_M:
        reasons.append("NOT_CLOSE_DISTANCE")
    var forward_dot := -1.0
    if forward.length_squared() > 0.0001 and distance_m > 0.0001:
        forward_dot = forward.normalized().dot(to_creature.normalized())
    if forward_dot < MIN_FORWARD_DOT:
        reasons.append("CREATURE_OUTSIDE_OBSERVATION_CONE")
    var los_clear := _line_of_sight_clear(origin, _creature.global_position + Vector3(0, 0.5, 0))
    if not los_clear:
        reasons.append("WORLD_OCCLUSION_BLOCKS_CLOSE_OBSERVATION")

    var qualified := reasons.is_empty()
    return _witness(request_id, qualified, reasons, {
        "playerBody": player_contract,
        "finalCreatureIdentity": creature_identity,
        "distanceM": distance_m,
        "forwardDot": forward_dot,
        "lineOfSightClear": los_clear,
        "requestOriginPlayerOffsetM": request_origin_offset,
        "playerNavOffsetM": player_nav_offset,
        "creatureNavOffsetM": creature_nav_offset,
        "navigationMapIteration": {"player": player_iteration, "creature": creature_iteration},
        "samePlayerInstance": _player.get_instance_id() == _player_instance_id,
        "sameCreatureInstance": _creature.get_instance_id() == _creature_instance_id,
        "teleportOrResetObserved": _continuity_compromised,
    })

func _bind_candidate_runtime() -> void:
    _integration_root = _find_integration_root()
    if _integration_root == null:
        return
    # Navigation initialization is deferred and bakes two maps. Wait until owner
    # navigation truth exists before exposing a candidate-ready qualifier.
    for _i in range(120):
        if _nav_mount != null and _nav_mount.has_method("is_initialized") and bool(_nav_mount.call("is_initialized")):
            break
        await get_tree().physics_frame
    if _nav_mount == null or not _nav_mount.has_method("is_initialized") or not bool(_nav_mount.call("is_initialized")):
        return
    if not _refresh_runtime_instances():
        return
    await get_tree().physics_frame
    await get_tree().physics_frame
    _player_instance_id = _player.get_instance_id()
    _creature_instance_id = _creature.get_instance_id()
    _last_player_position = _player.global_position
    _last_creature_position = _creature.global_position
    _continuity_armed = true
    if _integration_root.has_method("bind_observation_world_qualifier"):
        var bound := bool(_integration_root.call("bind_observation_world_qualifier", qualifier_callable(), &"A14/F14"))
        a17_world_qualifier_bound.emit({"ok": bound, "sourceFront": SOURCE_FRONT, "callable": "qualify_close_observation(request_id, origin, forward)"})
    _event_bus = get_node_or_null("/root/VeilwildEventBus")
    if _event_bus != null and _event_bus.has_signal("envelope_published"):
        var callback := Callable(self, "_on_event_bus_envelope")
        if not _event_bus.is_connected("envelope_published", callback):
            _event_bus.connect("envelope_published", callback)

func _refresh_runtime_instances() -> bool:
    if _integration_root == null:
        _integration_root = _find_integration_root()
    if _integration_root == null:
        return false
    var loaded: Variant = _integration_root.get("loaded_modules")
    if not (loaded is Dictionary):
        return false
    var modules: Dictionary = loaded
    if not modules.has("player_runtime") or not modules.has("creature"):
        return false
    var player_value: Variant = modules["player_runtime"].get("instance", null)
    var creature_value: Variant = modules["creature"].get("instance", null)
    if not (player_value is Node3D) or not (creature_value is Node3D):
        return false
    var new_player := player_value as Node3D
    var new_creature := creature_value as Node3D
    if _continuity_armed and (_player_instance_id != new_player.get_instance_id() or _creature_instance_id != new_creature.get_instance_id()):
        return false
    _player = new_player
    _creature = new_creature
    return true

func _find_integration_root() -> Node:
    var roots := get_tree().get_nodes_in_group("veilwild.integration_root")
    return roots[0] if roots.size() == 1 else null

func _player_contract_witness() -> Dictionary:
    if not (_player is CharacterBody3D):
        return {"valid": false, "reason": "PLAYER_NOT_CHARACTER_BODY_3D"}
    var shape_node := _find_first_type(_player, "CollisionShape3D") as CollisionShape3D
    if shape_node == null or not (shape_node.shape is CapsuleShape3D):
        return {"valid": false, "reason": "PLAYER_CAPSULE_MISSING"}
    var capsule := shape_node.shape as CapsuleShape3D
    var valid := is_equal_approx(capsule.radius, 0.35) and is_equal_approx(capsule.height, 1.8) and int((_player as CharacterBody3D).collision_layer) == 2 and int((_player as CharacterBody3D).collision_mask) == 1
    return {
        "valid": valid,
        "carrier": "CharacterBody3D/CapsuleShape3D",
        "radiusM": capsule.radius,
        "heightM": capsule.height,
        "collisionLayer": int((_player as CharacterBody3D).collision_layer),
        "collisionMask": int((_player as CharacterBody3D).collision_mask),
    }

func _creature_identity_witness() -> Dictionary:
    var skeleton := _find_first_type(_creature, "Skeleton3D") as Skeleton3D
    var animation_player := _find_first_type(_creature, "AnimationPlayer") as AnimationPlayer
    var bone_count := 0 if skeleton == null else skeleton.get_bone_count()
    var root_present := false
    if skeleton != null:
        for index in range(bone_count):
            if String(skeleton.get_bone_name(index)) == FINAL_CREATURE_ROOT_BONE:
                root_present = true
                break
    var available: Array[String] = []
    if animation_player != null:
        for clip in animation_player.get_animation_list():
            available.append(String(clip))
    var missing: Array[String] = []
    for required in REQUIRED_RUNTIME_CLIPS:
        if not available.has(required):
            missing.append(required)
    return {
        "valid": skeleton != null and animation_player != null and bone_count == FINAL_CREATURE_BONE_COUNT and root_present and missing.is_empty(),
        "animationEnvelopeSourceA08GlbSha256": FINAL_A08_GLB_SHA256,
        "sourceEnvelopeSha256": FINAL_A08_ENVELOPE_SHA256,
        "expectedSelectedFinalCreatureGlbSha256": FINAL_SELECTED_CREATURE_GLB_SHA256,
        "expectedSelectedFinalCreatureProducerRevision": FINAL_SELECTED_CREATURE_PRODUCER_REVISION,
        "boneCount": bone_count,
        "rootBonePresent": root_present,
        "requiredClipCount": REQUIRED_RUNTIME_CLIPS.size(),
        "missingRequiredClips": missing,
    }

func _find_first_type(node: Node, type_name: String) -> Node:
    if node.get_class() == type_name or node.is_class(type_name):
        return node
    for child in node.get_children():
        var found := _find_first_type(child, type_name)
        if found != null:
            return found
    return null

func _line_of_sight_clear(origin: Vector3, target: Vector3) -> bool:
    if origin.distance_to(target) <= 0.0001:
        return false
    var query := PhysicsRayQueryParameters3D.create(origin, target, 1)
    query.collide_with_areas = false
    query.collide_with_bodies = true
    if _player is CollisionObject3D:
        query.exclude = [(_player as CollisionObject3D).get_rid()]
    var hit: Dictionary = _nav_mount.get_world_3d().direct_space_state.intersect_ray(query)
    if hit.is_empty():
        return true
    var hit_position: Variant = hit.get("position", null)
    return hit_position is Vector3 and (hit_position as Vector3).distance_to(target) <= LOS_ENDPOINT_ALLOWANCE_M

func _witness(request_id: int, qualified: bool, reasons: Array[String], detail: Dictionary) -> Dictionary:
    var result := {
        "qualified": qualified,
        "sourceFront": SOURCE_FRONT,
        "producerSemanticId": CLOSE_QUALIFIED_ID if qualified else CLOSE_DENIED_ID,
        "requestId": request_id,
        "worldCondition": "A14_FINAL_CREATURE_PLAYER_NAV_COLLISION_CLOSE_OBSERVATION_R4A",
        "reasons": reasons.duplicate(),
        "finalCreatureEnvelope": {"radiusM": 1.8, "heightM": 2.2, "sourceA08GlbSha256": FINAL_A08_GLB_SHA256, "expectedSelectedA10GlbSha256": FINAL_SELECTED_CREATURE_GLB_SHA256},
        "humanClaims": "UNKNOWN",
    }
    result.merge(detail, true)
    return result

func _on_event_bus_envelope(topic: StringName, payload: Dictionary, _source: StringName) -> void:
    if topic != &"evade_started":
        return
    if str(payload.get("sourceFront", "")) != "A13/F13":
        return
    if str(payload.get("producerSemanticId", "")) != F13_EVADE_STARTED_ID:
        return
    var producer_data: Variant = payload.get("producerData", {})
    if not (producer_data is Dictionary):
        return
    var data: Dictionary = producer_data
    var sequence := int(data.get("transitionSequence", payload.get("transitionSequence", 0)))
    if sequence <= 0:
        return
    if not _refresh_runtime_instances():
        return
    _evade_sequence = sequence
    _evade_creature_position = _creature.global_position
    _evade_pending = true

func _try_publish_reacquisition_opportunity() -> void:
    if _reacquisition_emitted_for_sequence == _evade_sequence or _event_bus == null or not _refresh_runtime_instances():
        return
    if _creature.global_position.distance_to(_evade_creature_position) < MIN_POST_EVADE_CREATURE_DISPLACEMENT_M:
        return
    var player_map: RID = _nav_mount.call("player_navigation_map")
    if _map_iteration(player_map) <= 0:
        return
    var start := NavigationServer3D.map_get_closest_point(player_map, _player.global_position)
    var target := NavigationServer3D.map_get_closest_point(player_map, _creature.global_position)
    if start.distance_to(_player.global_position) > MAX_PLAYER_NAV_OFFSET_M:
        return
    if target.distance_to(_creature.global_position) > MAX_CREATURE_NAV_OFFSET_M:
        return
    var path := NavigationServer3D.map_get_path(player_map, start, target, true)
    if path.size() < 2 or path[path.size() - 1].distance_to(target) > 0.35:
        return
    var route_hash := _path_sha256(path)
    var route_length := _path_length(path)
    var witness_id := "f14-r4a-reacq-%d-%s" % [_evade_sequence, route_hash.left(12)]
    var event := {
        "sourceFront": SOURCE_FRONT,
        "producerSemanticId": REACQUISITION_ID,
        "reasonId": "POST_EVADE_SAME_SESSION_WORLD_ROUTE_AVAILABLE",
        "producerData": {
            "witnessId": witness_id,
            "transitionSequence": _evade_sequence,
            "navigationMapIteration": _map_iteration(player_map),
            "routeFeasible": true,
            "routePointCount": path.size(),
            "routeEvidenceSha256": route_hash,
            "routeLengthBand": _route_length_band(route_length),
            "samePlayerInstance": _player.get_instance_id() == _player_instance_id,
            "sameCreatureInstance": _creature.get_instance_id() == _creature_instance_id,
            "resetBetweenStages": false,
            "teleportOrResetFallback": false,
            "creatureDisplacedAfterEvade": true,
            "hiddenTargetCoordinatesExposed": false,
            "finalCreatureEnvelopeSha256": FINAL_A08_ENVELOPE_SHA256,
        },
    }
    _event_bus.call("publish", &"reacquisition_opportunity", event, &"F14")
    _reacquisition_emitted_for_sequence = _evade_sequence
    _evade_pending = false
    _last_reacquisition_witness = event["producerData"].duplicate(true)
    reacquisition_opportunity_emitted.emit(_last_reacquisition_witness.duplicate(true))

func _path_sha256(path: PackedVector3Array) -> String:
    var context := HashingContext.new()
    context.start(HashingContext.HASH_SHA256)
    for point in path:
        context.update(("%.5f,%.5f,%.5f;" % [point.x, point.y, point.z]).to_utf8_buffer())
    return context.finish().hex_encode()

func _path_length(path: PackedVector3Array) -> float:
    var total := 0.0
    for index in range(1, path.size()):
        total += path[index - 1].distance_to(path[index])
    return total

func _route_length_band(length_m: float) -> String:
    if length_m < 4.0:
        return "NEAR"
    if length_m < 10.0:
        return "MID"
    return "FAR"

func _map_iteration(map_rid: RID) -> int:
    return NavigationServer3D.map_get_iteration_id(map_rid) if map_rid.is_valid() else 0

func _mark_continuity_compromised(reason: String) -> void:
    if not _continuity_compromised:
        _continuity_compromised = true
        _continuity_reason = reason
