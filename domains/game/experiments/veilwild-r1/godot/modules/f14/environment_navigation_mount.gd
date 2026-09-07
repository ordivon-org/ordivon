class_name VeilwildEnvironmentNavigationMount
extends Node3D

## F14-owned environment-bound navigation/collision runtime for Veilwild R1.
##
## Authority boundaries:
## - F05 owns authored geometry and solid/soft physical intent.
## - F14 owns collider representation, clearance, legal affordance admission,
##   path realization and mechanical reacquisition-route evidence.
## - F13 owns behavior state/nav intent semantics.
## - F01/A23 own whether the integrated candidate has actually produced a
##   non-spoiling reacquisition opportunity and successful product-loop trace.
##
## No target coordinates from this module are player UI data.

signal navigation_ready(snapshot: Dictionary)
signal navigation_failed(reasons: PackedStringArray)

const F05_SOURCE_REVISION := "ffbee6188e17e39cd174ec3e9a7d63cedefc2743"
const F05_GLB_SHA256 := "f980ea94b074de9001a72b10d19fd6a495dae73878ab157472a6a416a4e33143"
const F05_SOLID_INTENT_REVISION := "2b8d5e5893cc9db4c2d1710cb0915e673563c5a3"
const F05_SOLID_INTENT_SHA256 := "0352749ca05b8dc2f19a1c0a763438f8b5337a9fc03d47e5a2231acddeaf6a8b"
const F13_SEMANTIC_REVISION := "60cb5faf0d386ae9815647c1ffddc9bc0c123af3"
const F13_INTERFACE_SHA256 := "bb4d5e27d457bae528454fdc917cbff62a30a445d0c9a4c8e554c6b894fa4824"
const F18_BODY_REVISION := "935221a1a8c9710eb83380bddef0a006c09b838e"
const F18_PLAYER_SCENE_SHA256 := "390d1bfee021d3f87fddd09c769389a7790dbe2b1efd79e08b7eb7377674cb0d"
const F01_TRACE_REVISION := "729b98b8448119907698395bc21b0cd34fdf6b03"
const F01_TRACE_SHA256 := "6779be6a45d9a78729b0b308bf74229769afd22086c0a43a37250111e68b6204"

const PLAYER_NAV_RADIUS_M := 0.40
const PLAYER_NAV_HEIGHT_M := 1.80
const PLAYER_MAX_SLOPE_DEG := 45.0
const PLAYER_MAX_CLIMB_M := 0.10

const A07_PRODUCT_RIG_REVISION := "373506f9a2865bf4520aab7d17fab5275ed21ec2"
const A08_PRODUCT_ANIMATION_REVISION := "6c4c91654bdadf5c139399dfe6ece4b12f42db89"
const A08_PRODUCT_BYTE_ORIGIN_REVISION := "bbf16cd8ba74d8fbbead3cd259edb63a8365bdc4"
const A08_PRODUCT_GLB_SHA256 := "bc460bb8c48f8296d25a3f2e23323845e851b5669335ac6fb5a9126d3519c4d8"
const A08_ENVELOPE_RECEIPT_SHA256 := "fe0fdf2dd88b7f7df9e6c0aa8bf558559635062b640e69a509f7303d2c701896"
const A08_MEASURED_HORIZONTAL_RADIUS_MAX_M := 1.7145102333355273
const A08_MEASURED_HEIGHT_MAX_M := 2.147455930709839
# Final A07-backed A08 product was exact-frame sampled over all seven animations.
# Godot navigation paths represent the agent center; 1.80 m radius and 2.20 m
# height conservatively round the measured animated envelope upward to the
# 0.20 m / 0.10 m bake voxel resolutions.
const CREATURE_NAV_RADIUS_M := 1.80
const CREATURE_NAV_HEIGHT_M := 2.20
const CREATURE_MAX_SLOPE_DEG := 45.0
const CREATURE_MAX_CLIMB_M := 0.20
const CREATURE_CLEARANCE_QUALIFICATION := "A07_BACKED_A08_FINAL_ANIMATED_ENVELOPE_R4A_REPLAY_PASS"

const SOLID_ROLES := {
    "authored_terrain": true,
    "forest_trunk": true,
    "rock_outcrop": true,
    "fallen_log": true,
    "landmark_fallen_log": true,
    "landmark_root_buttress": true,
}

const REQUIRED_MARKERS := [
    "VW_MARKER_ApproachAnchor_North",
    "VW_MARKER_ApproachAnchor_South",
    "VW_MARKER_ApproachAnchor_West",
    "VW_MARKER_SearchLandmark_Glade",
    "VW_MARKER_ConcealCandidate_FallenLog",
    "VW_MARKER_ConcealCandidate_NorthFern",
    "VW_MARKER_ConcealCandidate_RockRidge",
]

var _player_map: RID
var _player_region: RID
var _creature_map: RID
var _creature_region: RID
var _markers: Dictionary = {}
var _solid_counts: Dictionary = {}
var _candidate_acceptance: Dictionary = {}
var _initialized := false
var _failure_reasons := PackedStringArray()

@onready var _navigation_runtime: Node = $VeilwildNavigationRuntime
@onready var _collision_root: Node3D = $WorldCollision
@onready var _affordance_root: Node3D = $Affordances

func _ready() -> void:
    add_to_group("veilwild.f14.navigation_mount")
    call_deferred("_initialize_from_a17_environment")

func _exit_tree() -> void:
    _free_navigation_rids()

func is_initialized() -> bool:
    return _initialized

func player_navigation_map() -> RID:
    return _player_map

func creature_navigation_map() -> RID:
    return _creature_map

func bind_creature_agent(agent: NavigationAgent3D) -> bool:
    if not _initialized or agent == null or not _creature_map.is_valid():
        return false
    agent.set_navigation_map(_creature_map)
    return true

func behavior_affordance_snapshot(creature_position_m: Vector3, threat_position_m: Vector3) -> Dictionary:
    if not _initialized or not _creature_map.is_valid():
        return {
            "concealment_available": false,
            "concealment_quality": 0.0,
            "escape_available": false,
            "selected_concealment_affordance_id": "",
            "selected_escape_affordance_id": "",
            "navigation_map_iteration": 0,
        }
    return _navigation_runtime.behavior_affordance_snapshot(_creature_map, creature_position_m, threat_position_m)

func resolve_behavior_nav_intent(nav_intent: Dictionary, creature_position_m: Vector3, threat_position_m: Vector3) -> Dictionary:
    if not _initialized or not _creature_map.is_valid():
        return {"accepted": false, "action": StringName(String(nav_intent.get("action", "NONE"))), "reason": &"F14_NOT_INITIALIZED"}
    return _navigation_runtime.resolve_nav_intent(nav_intent, _creature_map, creature_position_m, threat_position_m)

func player_route_between_markers(from_marker_id: String, to_marker_id: String) -> Dictionary:
    return _marker_route(_player_map, from_marker_id, to_marker_id)

func runtime_snapshot() -> Dictionary:
    return {
        "initialized": _initialized,
        "failureReasons": Array(_failure_reasons),
        "environment": {
            "producerRevision": F05_SOURCE_REVISION,
            "glbSha256": F05_GLB_SHA256,
            "solidIntentRevision": F05_SOLID_INTENT_REVISION,
            "solidIntentSha256": F05_SOLID_INTENT_SHA256,
        },
        "behaviorSemantics": {
            "producerRevision": F13_SEMANTIC_REVISION,
            "interfaceSha256": F13_INTERFACE_SHA256,
            "reacquisitionProvenByF13": false,
        },
        "playerBody": {
            "producerRevision": F18_BODY_REVISION,
            "playerSceneSha256": F18_PLAYER_SCENE_SHA256,
            "navigationRadiusM": PLAYER_NAV_RADIUS_M,
            "navigationHeightM": PLAYER_NAV_HEIGHT_M,
        },
        "productTrace": {
            "producerRevision": F01_TRACE_REVISION,
            "traceSha256": F01_TRACE_SHA256,
            "mechanicalRouteIsNotReacquisitionEvent": true,
        },
        "creatureClearance": {
            "a07RigRevision": A07_PRODUCT_RIG_REVISION,
            "a08AnimationRevision": A08_PRODUCT_ANIMATION_REVISION,
            "a08ByteOriginRevision": A08_PRODUCT_BYTE_ORIGIN_REVISION,
            "a08GlbSha256": A08_PRODUCT_GLB_SHA256,
            "envelopeReceiptSha256": A08_ENVELOPE_RECEIPT_SHA256,
            "measuredHorizontalRadiusMaxM": A08_MEASURED_HORIZONTAL_RADIUS_MAX_M,
            "measuredHeightMaxM": A08_MEASURED_HEIGHT_MAX_M,
            "navigationRadiusM": CREATURE_NAV_RADIUS_M,
            "navigationHeightM": CREATURE_NAV_HEIGHT_M,
            "qualification": CREATURE_CLEARANCE_QUALIFICATION,
        },
        "solidRoleCounts": _solid_counts.duplicate(true),
        "candidateAcceptance": _candidate_acceptance.duplicate(true),
        "navigationMapIteration": {
            "player": NavigationServer3D.map_get_iteration_id(_player_map) if _player_map.is_valid() else 0,
            "creature": NavigationServer3D.map_get_iteration_id(_creature_map) if _creature_map.is_valid() else 0,
        },
        "humanClaims": "UNKNOWN",
    }

func _initialize_from_a17_environment() -> void:
    var integration_root := _find_integration_root()
    if integration_root == null or not integration_root.has_method("get_mount"):
        _fail("A17_INTEGRATION_ROOT_MISSING")
        return
    var environment_mount: Node = integration_root.call("get_mount", &"EnvironmentMount")
    if environment_mount == null:
        _fail("A17_ENVIRONMENT_MOUNT_MISSING")
        return

    _collect_environment(environment_mount)
    for marker_id in REQUIRED_MARKERS:
        if not _markers.has(marker_id):
            _fail("F05_REQUIRED_MARKER_MISSING:%s" % marker_id)
    if int(_solid_counts.get("authored_terrain", 0)) != 1:
        _fail("F05_TERRAIN_COLLISION_SOURCE_COUNT_INVALID")
    if int(_solid_counts.get("landmark_root_buttress", 0)) != 3:
        _fail("F05_ROOT_BUTTRESS_SOLID_COUNT_INVALID")
    if not _failure_reasons.is_empty():
        navigation_failed.emit(_failure_reasons)
        return

    var player_build := await _build_map(PLAYER_NAV_RADIUS_M, PLAYER_NAV_HEIGHT_M, PLAYER_MAX_SLOPE_DEG, PLAYER_MAX_CLIMB_M)
    if not bool(player_build.get("ok", false)):
        _fail("PLAYER_NAV_BUILD_FAIL:%s" % String(player_build.get("reason", "UNKNOWN")))
        navigation_failed.emit(_failure_reasons)
        return
    _player_map = player_build["map"]
    _player_region = player_build["region"]

    var creature_build := await _build_map(CREATURE_NAV_RADIUS_M, CREATURE_NAV_HEIGHT_M, CREATURE_MAX_SLOPE_DEG, CREATURE_MAX_CLIMB_M)
    if not bool(creature_build.get("ok", false)):
        _fail("CREATURE_NAV_BUILD_FAIL:%s" % String(creature_build.get("reason", "UNKNOWN")))
        navigation_failed.emit(_failure_reasons)
        return
    _creature_map = creature_build["map"]
    _creature_region = creature_build["region"]

    _evaluate_candidates_and_materialize_affordances()
    if not _validate_product_requirements():
        navigation_failed.emit(_failure_reasons)
        return

    _initialized = true
    var snapshot := runtime_snapshot()
    navigation_ready.emit(snapshot)
    print("VEILWILD_F14_NAVIGATION_READY %s" % JSON.stringify(snapshot))

func _find_integration_root() -> Node:
    var roots := get_tree().get_nodes_in_group("veilwild.integration_root")
    if roots.size() != 1:
        return null
    return roots[0]

func _collect_environment(node: Node) -> void:
    if node is Node3D and String(node.name).begins_with("VW_MARKER_"):
        var extras := _extras(node)
        _markers[String(node.name)] = {
            "positionM": (node as Node3D).global_position,
            "radiusM": float(extras.get("radius_m", 0.0)),
            "candidateKind": String(extras.get("candidate_kind", "")),
            "semanticAuthority": String(extras.get("semantic_authority", "")),
            "sourceContract": String(extras.get("veilwild_marker_contract", "")),
        }
    if node is MeshInstance3D:
        var extras := _extras(node)
        var role := String(extras.get("veilwild_role", ""))
        if SOLID_ROLES.has(role):
            _add_static_collision(node as MeshInstance3D, role)
    for child in node.get_children():
        _collect_environment(child)

func _extras(node: Node) -> Dictionary:
    var value: Variant = node.get_meta("extras", {})
    return value if value is Dictionary else {}

func _add_static_collision(mesh_node: MeshInstance3D, role: String) -> void:
    if mesh_node.mesh == null:
        return
    var shape := mesh_node.mesh.create_trimesh_shape()
    if shape == null:
        return
    var body := StaticBody3D.new()
    body.name = "F14_COL_%s" % mesh_node.name
    body.collision_layer = 1
    body.collision_mask = 0
    _collision_root.add_child(body)
    body.global_transform = mesh_node.global_transform
    var shape_node := CollisionShape3D.new()
    shape_node.name = "Shape"
    shape_node.shape = shape
    body.add_child(shape_node)
    _solid_counts[role] = int(_solid_counts.get(role, 0)) + 1

func _build_map(radius_m: float, height_m: float, max_slope_deg: float, max_climb_m: float) -> Dictionary:
    var navmesh := NavigationMesh.new()
    navmesh.agent_radius = radius_m
    navmesh.agent_height = height_m
    navmesh.agent_max_slope = max_slope_deg
    navmesh.agent_max_climb = max_climb_m
    navmesh.cell_size = 0.20
    navmesh.cell_height = 0.10
    navmesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
    navmesh.geometry_collision_mask = 1
    navmesh.filter_walkable_low_height_spans = true
    navmesh.filter_ledge_spans = true
    navmesh.filter_low_hanging_obstacles = true

    var source := NavigationMeshSourceGeometryData3D.new()
    NavigationServer3D.parse_source_geometry_data(navmesh, source, _collision_root)
    NavigationServer3D.bake_from_source_geometry_data(navmesh, source)
    if navmesh.get_polygon_count() <= 0 or navmesh.get_vertices().is_empty():
        return {"ok": false, "reason": "EMPTY_BAKE"}

    var map_rid := NavigationServer3D.map_create()
    NavigationServer3D.map_set_active(map_rid, true)
    NavigationServer3D.map_set_up(map_rid, Vector3.UP)
    NavigationServer3D.map_set_cell_size(map_rid, navmesh.cell_size)
    NavigationServer3D.map_set_cell_height(map_rid, navmesh.cell_height)
    var region_rid := NavigationServer3D.region_create()
    NavigationServer3D.region_set_enabled(region_rid, true)
    NavigationServer3D.region_set_map(region_rid, map_rid)
    NavigationServer3D.region_set_navigation_mesh(region_rid, navmesh)

    var iteration := 0
    for _i in range(30):
        await get_tree().physics_frame
        iteration = NavigationServer3D.map_get_iteration_id(map_rid)
        if iteration > 0:
            break
    if iteration == 0:
        NavigationServer3D.free_rid(region_rid)
        NavigationServer3D.free_rid(map_rid)
        return {"ok": false, "reason": "MAP_UNSYNCHRONIZED_ITERATION_0"}

    # Avoid a same-synchronization-tick closest-point query race reproduced in R2.
    await get_tree().physics_frame
    await get_tree().physics_frame
    return {
        "ok": true,
        "map": map_rid,
        "region": region_rid,
        "iteration": iteration,
        "polygonCount": navmesh.get_polygon_count(),
        "vertexCount": navmesh.get_vertices().size(),
    }

func _evaluate_candidates_and_materialize_affordances() -> void:
    _candidate_acceptance.clear()
    for marker_id in REQUIRED_MARKERS:
        var marker: Dictionary = _markers[marker_id]
        var source_position: Vector3 = marker["positionM"]
        var radius_m := float(marker["radiusM"])
        var player_anchor := NavigationServer3D.map_get_closest_point(_player_map, source_position)
        var creature_anchor := NavigationServer3D.map_get_closest_point(_creature_map, source_position)
        var player_offset := player_anchor.distance_to(source_position)
        var creature_offset := creature_anchor.distance_to(source_position)
        var row := {
            "candidateKind": marker["candidateKind"],
            "candidateRadiusM": radius_m,
            "playerAccepted": player_offset <= radius_m,
            "playerOffsetM": player_offset,
            "creatureAccepted": creature_offset <= radius_m,
            "creatureOffsetM": creature_offset,
        }
        _candidate_acceptance[marker_id] = row
        if String(marker["candidateKind"]) == "concealment_context" and bool(row["creatureAccepted"]):
            _materialize_affordance(marker_id, marker, creature_anchor)

func _materialize_affordance(marker_id: String, marker: Dictionary, navigation_anchor_m: Vector3) -> void:
    var affordance := Area3D.new()
    affordance.name = "Affordance_%s" % marker_id
    affordance.set_script(preload("res://modules/f14/concealment_affordance_3d.gd"))
    _affordance_root.add_child(affordance)
    affordance.global_position = marker["positionM"]
    affordance.set("affordance_id", StringName(marker_id))
    affordance.set("concealment_suitability", 0.5)
    affordance.set("traversal_eligible", true)
    affordance.set("evasion_eligible", true)
    affordance.set("environment_revision", F05_SOURCE_REVISION)

    var marker_node := Marker3D.new()
    marker_node.name = "NavigationAnchor"
    affordance.add_child(marker_node)
    marker_node.global_position = navigation_anchor_m
    affordance.set("navigation_anchor_path", NodePath("NavigationAnchor"))

    var collision := CollisionShape3D.new()
    collision.name = "ContextVolume"
    var sphere := SphereShape3D.new()
    sphere.radius = maxf(float(marker["radiusM"]), 0.1)
    collision.shape = sphere
    affordance.add_child(collision)

func _validate_product_requirements() -> bool:
    if NavigationServer3D.map_get_iteration_id(_player_map) <= 0:
        _fail("PLAYER_MAP_NOT_SYNCHRONIZED")
    if NavigationServer3D.map_get_iteration_id(_creature_map) <= 0:
        _fail("CREATURE_MAP_NOT_SYNCHRONIZED")

    # Player-critical search/observation/reacquisition routes must all remain feasible.
    for route_pair in [
        ["VW_MARKER_ApproachAnchor_South", "VW_MARKER_SearchLandmark_Glade"],
        ["VW_MARKER_ApproachAnchor_West", "VW_MARKER_SearchLandmark_Glade"],
        ["VW_MARKER_ApproachAnchor_North", "VW_MARKER_SearchLandmark_Glade"],
        ["VW_MARKER_SearchLandmark_Glade", "VW_MARKER_ConcealCandidate_FallenLog"],
        ["VW_MARKER_SearchLandmark_Glade", "VW_MARKER_ConcealCandidate_NorthFern"],
        ["VW_MARKER_SearchLandmark_Glade", "VW_MARKER_ConcealCandidate_RockRidge"],
    ]:
        var route := _marker_route(_player_map, route_pair[0], route_pair[1])
        if String(route.get("result", "FAIL")) != "PASS":
            _fail("PLAYER_CRITICAL_ROUTE_FAIL:%s->%s" % [route_pair[0], route_pair[1]])

    var creature_context_count := 0
    for marker_id in [
        "VW_MARKER_ConcealCandidate_FallenLog",
        "VW_MARKER_ConcealCandidate_NorthFern",
        "VW_MARKER_ConcealCandidate_RockRidge",
    ]:
        if bool(_candidate_acceptance.get(marker_id, {}).get("creatureAccepted", false)):
            creature_context_count += 1
    if creature_context_count < 2:
        _fail("CREATURE_REQUIRES_AT_LEAST_TWO_REACHABLE_CONCEALMENT_CONTEXTS")
    if not bool(_candidate_acceptance.get("VW_MARKER_ConcealCandidate_FallenLog", {}).get("creatureAccepted", false)):
        _fail("FALLEN_LOG_INITIAL_CONCEALMENT_UNREACHABLE")
    return _failure_reasons.is_empty()

func _marker_route(map_rid: RID, from_marker_id: String, to_marker_id: String) -> Dictionary:
    if not map_rid.is_valid() or NavigationServer3D.map_get_iteration_id(map_rid) <= 0:
        return {"result": "FAIL", "reason": "MAP_UNSYNCHRONIZED"}
    if not _markers.has(from_marker_id) or not _markers.has(to_marker_id):
        return {"result": "FAIL", "reason": "MARKER_MISSING", "from": from_marker_id, "to": to_marker_id}
    var from_marker: Dictionary = _markers[from_marker_id]
    var to_marker: Dictionary = _markers[to_marker_id]
    var start := NavigationServer3D.map_get_closest_point(map_rid, from_marker["positionM"])
    var target := NavigationServer3D.map_get_closest_point(map_rid, to_marker["positionM"])
    var start_offset := start.distance_to(from_marker["positionM"])
    var target_offset := target.distance_to(to_marker["positionM"])
    if start_offset > float(from_marker["radiusM"]) or target_offset > float(to_marker["radiusM"]):
        return {
            "result": "FAIL",
            "reason": "MARKER_OUTSIDE_CANDIDATE_RADIUS",
            "from": from_marker_id,
            "to": to_marker_id,
            "startOffsetM": start_offset,
            "targetOffsetM": target_offset,
        }
    var path := NavigationServer3D.map_get_path(map_rid, start, target, true)
    var reached := path.size() >= 2 and path[path.size() - 1].distance_to(target) <= 0.25
    return {
        "result": "PASS" if reached else "FAIL",
        "reason": "PATH_REACHES_TARGET" if reached else "NO_PATH",
        "from": from_marker_id,
        "to": to_marker_id,
        "pathPoints": path.size(),
        "pathLengthM": _path_length(path),
        "startOffsetM": start_offset,
        "targetOffsetM": target_offset,
    }

func _path_length(path: PackedVector3Array) -> float:
    var total := 0.0
    for index in range(1, path.size()):
        total += path[index - 1].distance_to(path[index])
    return total

func _fail(reason: String) -> void:
    if not _failure_reasons.has(reason):
        _failure_reasons.append(reason)

func _free_navigation_rids() -> void:
    for rid in [_player_region, _creature_region, _player_map, _creature_map]:
        if rid.is_valid():
            NavigationServer3D.free_rid(rid)
