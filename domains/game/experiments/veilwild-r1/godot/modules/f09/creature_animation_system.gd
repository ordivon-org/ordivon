class_name VeilwildCreatureAnimationSystem
extends Node

signal behavior_motion_applied(state_id: StringName, transition_reason: StringName, transition_serial: int)
signal behavior_motion_rejected(state_id: StringName, transition_reason: StringName, code: StringName, detail: String)

var _controller: Node


func _ready() -> void:
	if _controller == null:
		var controller_path: String = String(get_script().resource_path.get_base_dir()) + "/creature_animation_controller.gd"
		var controller_script := load(controller_path)
		if controller_script == null:
			push_error("A09 animation controller script missing at %s" % controller_path)
			return
		_controller = controller_script.new()
		_controller.name = "AnimationStateController"
		add_child(_controller)


func bind_runtime(
	animation_player: AnimationPlayer,
	state_to_motion: Dictionary,
	legal_transitions: Dictionary,
	strict_transitions := true
) -> bool:
	if _controller == null:
		_ready()
	if _controller == null:
		return false
	return _controller.configure(animation_player, state_to_motion, legal_transitions, strict_transitions)


func apply_behavior_decision(decision: Dictionary) -> bool:
	if _controller == null:
		_ready()
	if _controller == null:
		behavior_motion_rejected.emit(&"", &"", &"CONTROLLER_UNAVAILABLE", "A09 controller could not be materialized")
		return false
	# Round-2 canonical F13 carrier is the stable semantic ID. R1 state_name remains
	# an explicit compatibility fallback only; F09 must not rename or infer F13 truth.
	var state_value: Variant = decision.get("behavior_state_id", decision.get("state_name", ""))
	if String(state_value).is_empty():
		behavior_motion_rejected.emit(&"", &"", &"MISSING_BEHAVIOR_STATE", "F13 decision lacks behavior_state_id/state_name")
		return false
	var state_id := StringName(String(state_value))
	var transition_value: Variant = decision.get("transition_semantic_id", decision.get("transition_reason_name", "UNSPECIFIED"))
	var transition_reason := StringName(String(transition_value))
	var accepted: bool = _controller.request_behavior_state(state_id, String(transition_reason))
	if accepted:
		behavior_motion_applied.emit(state_id, transition_reason, _controller.transition_serial)
	else:
		behavior_motion_rejected.emit(
			state_id,
			transition_reason,
			_controller.last_rejection_code,
			_controller.last_rejection_detail
		)
	return accepted


func snapshot() -> Dictionary:
	if _controller == null:
		return {
			"behavior_state_id": "",
			"motion_semantic_id": "",
			"clip_name": "",
			"transition_serial": 0,
			"last_rejection_code": "NOT_INITIALIZED",
			"last_rejection_detail": "animation system has not entered the scene tree",
		}
	return _controller.snapshot()
