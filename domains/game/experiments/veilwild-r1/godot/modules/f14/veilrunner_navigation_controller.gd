class_name VeilrunnerNavigationController
extends Node

## F14-owned collision-aware locomotion adapter. Target choice remains in F14
## navigation/affordance resolution; behavior state/policy remains F13-owned.

signal navigation_outcome(intent_id: StringName, outcome: StringName, failure_fallback: Variant)

const OUTCOME_ACCEPTED := &"ACCEPTED"
const OUTCOME_REACHED := &"REACHED"
const OUTCOME_UNREACHABLE := &"UNREACHABLE"
const OUTCOME_STUCK := &"STUCK"
const OUTCOME_INVALID_TARGET := &"INVALID_TARGET"
const OUTCOME_CANCELLED := &"CANCELLED"

@export var body_path: NodePath = NodePath("..")
@export var navigation_agent_path: NodePath = NodePath("../NavigationAgent3D")
@export_range(0.05, 10.0, 0.05) var default_speed_mps: float = 2.5
@export_range(0.05, 5.0, 0.05) var stuck_timeout_s: float = 1.5
@export_range(0.001, 1.0, 0.001) var progress_epsilon_m: float = 0.05
@export_range(0.01, 2.0, 0.01) var target_tolerance_m: float = 0.25

var _active := false
var _intent_id: StringName
var _failure_fallback: Variant = null
var _speed_mps := 0.0
var _stuck_elapsed_s := 0.0
var _best_distance_m := INF
var _avoidance_delta_s := 0.0

func _ready() -> void:
    var agent := _agent()
    if agent != null and not agent.velocity_computed.is_connected(_on_velocity_computed):
        agent.velocity_computed.connect(_on_velocity_computed)

func _body() -> CharacterBody3D:
    return get_node_or_null(body_path) as CharacterBody3D

func _agent() -> NavigationAgent3D:
    return get_node_or_null(navigation_agent_path) as NavigationAgent3D

func issue_world_position_intent(intent_id: StringName, target_position_m: Vector3, speed_mps: float = -1.0, failure_fallback: Variant = null) -> bool:
    var body := _body()
    var agent := _agent()
    if body == null or agent == null or String(intent_id).strip_edges().is_empty():
        navigation_outcome.emit(intent_id, OUTCOME_INVALID_TARGET, failure_fallback)
        return false
    if not target_position_m.is_finite():
        navigation_outcome.emit(intent_id, OUTCOME_INVALID_TARGET, failure_fallback)
        return false
    var navigation_map := agent.get_navigation_map()
    if not navigation_map.is_valid() or NavigationServer3D.map_get_iteration_id(navigation_map) == 0:
        navigation_outcome.emit(intent_id, OUTCOME_UNREACHABLE, failure_fallback)
        return false
    _intent_id = intent_id
    _failure_fallback = failure_fallback
    _speed_mps = speed_mps if speed_mps > 0.0 else default_speed_mps
    _active = true
    _stuck_elapsed_s = 0.0
    _best_distance_m = body.global_position.distance_to(target_position_m)
    _avoidance_delta_s = 0.0
    agent.target_position = target_position_m
    navigation_outcome.emit(_intent_id, OUTCOME_ACCEPTED, _failure_fallback)
    return true

func issue_affordance_intent(intent_id: StringName, affordance: Node, speed_mps: float = -1.0, failure_fallback: Variant = null) -> bool:
    if affordance == null or not affordance.has_method("validate_contract") or not affordance.has_method("world_navigation_anchor"):
        navigation_outcome.emit(intent_id, OUTCOME_INVALID_TARGET, failure_fallback)
        return false
    var errors: PackedStringArray = affordance.call("validate_contract")
    if not errors.is_empty() or not bool(affordance.get("traversal_eligible")):
        navigation_outcome.emit(intent_id, OUTCOME_INVALID_TARGET, failure_fallback)
        return false
    var target: Vector3 = affordance.call("world_navigation_anchor")
    return issue_world_position_intent(intent_id, target, speed_mps, failure_fallback)

func cancel_active_intent() -> void:
    if not _active:
        return
    var old_id := _intent_id
    var old_fallback: Variant = _failure_fallback
    _clear_motion()
    navigation_outcome.emit(old_id, OUTCOME_CANCELLED, old_fallback)

func _physics_process(delta: float) -> void:
    if not _active:
        return
    var body := _body()
    var agent := _agent()
    if body == null or agent == null:
        _finish(OUTCOME_INVALID_TARGET)
        return

    if agent.is_navigation_finished():
        if agent.is_target_reached() or body.global_position.distance_to(agent.target_position) <= target_tolerance_m:
            _finish(OUTCOME_REACHED)
        elif not agent.is_target_reachable():
            _finish(OUTCOME_UNREACHABLE)
        return

    # Required once per physics frame by NavigationAgent3D to advance its path.
    var next_position: Vector3 = agent.get_next_path_position()
    var planar_delta := next_position - body.global_position
    planar_delta.y = 0.0
    if planar_delta.length_squared() <= 0.000001:
        _update_stuck(delta, body.global_position.distance_to(agent.target_position))
        return

    var desired_velocity := planar_delta.normalized() * _speed_mps
    if agent.avoidance_enabled:
        # The safe velocity arrives asynchronously through velocity_computed.
        # Do not move using stale desired velocity in this branch.
        _avoidance_delta_s = delta
        agent.velocity = desired_velocity
    else:
        _apply_collision_aware_velocity(desired_velocity, delta, agent.target_position)

func _on_velocity_computed(safe_velocity: Vector3) -> void:
    if not _active:
        return
    var agent := _agent()
    if agent == null:
        _finish(OUTCOME_INVALID_TARGET)
        return
    _apply_collision_aware_velocity(safe_velocity, _avoidance_delta_s, agent.target_position)

func _apply_collision_aware_velocity(planar_velocity: Vector3, delta: float, target_position: Vector3) -> void:
    var body := _body()
    if body == null:
        _finish(OUTCOME_INVALID_TARGET)
        return
    body.velocity.x = planar_velocity.x
    body.velocity.z = planar_velocity.z
    # V-S4 requires CharacterBody3D contact semantics; direct transform mutation
    # would bypass collision resolution.
    body.move_and_slide()
    _update_stuck(delta, body.global_position.distance_to(target_position))

func _update_stuck(delta: float, distance_m: float) -> void:
    if distance_m + progress_epsilon_m < _best_distance_m:
        _best_distance_m = distance_m
        _stuck_elapsed_s = 0.0
        return
    _stuck_elapsed_s += maxf(delta, 0.0)
    if _stuck_elapsed_s >= stuck_timeout_s:
        _finish(OUTCOME_STUCK)

func _finish(outcome: StringName) -> void:
    var old_id := _intent_id
    var old_fallback: Variant = _failure_fallback
    _clear_motion()
    navigation_outcome.emit(old_id, outcome, old_fallback)

func _clear_motion() -> void:
    _active = false
    _intent_id = StringName()
    _failure_fallback = null
    _speed_mps = 0.0
    _stuck_elapsed_s = 0.0
    _best_distance_m = INF
    _avoidance_delta_s = 0.0
    var body := _body()
    if body != null:
        body.velocity.x = 0.0
        body.velocity.z = 0.0

static func validate_clearance_contract(collision_radius_m: float, navmesh_agent_radius_m: float, clearance_margin_m: float = 0.0) -> PackedStringArray:
    var errors := PackedStringArray()
    if collision_radius_m <= 0.0:
        errors.append("collision_radius_non_positive")
    if navmesh_agent_radius_m <= 0.0:
        errors.append("navmesh_agent_radius_non_positive")
    if clearance_margin_m < 0.0:
        errors.append("clearance_margin_negative")
    if navmesh_agent_radius_m + 0.0001 < collision_radius_m + clearance_margin_m:
        errors.append("navmesh_clearance_smaller_than_runtime_body")
    return errors
