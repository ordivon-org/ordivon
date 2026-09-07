class_name VeilwildAnimationStateController
extends Node

signal motion_transitioned(
	from_state: StringName,
	to_state: StringName,
	motion_semantic_id: StringName,
	clip_name: StringName,
	reason: String
)
signal motion_rejected(state_id: StringName, code: StringName, detail: String)

var _player: AnimationPlayer
var _mapping: Dictionary = {}
var _legal_transitions: Dictionary = {}
var _strict_transitions := true

var active_behavior_state: StringName = &""
var active_motion_semantic_id: StringName = &""
var active_clip_name: StringName = &""
var transition_serial := 0
var last_rejection_code: StringName = &""
var last_rejection_detail := ""


func configure(
	animation_player: AnimationPlayer,
	state_to_motion: Dictionary,
	legal_transitions: Dictionary,
	strict_transitions := true
) -> bool:
	_player = animation_player
	_mapping.clear()
	_legal_transitions.clear()
	_strict_transitions = strict_transitions
	active_behavior_state = &""
	active_motion_semantic_id = &""
	active_clip_name = &""
	transition_serial = 0
	_clear_rejection()

	if _player == null:
		return _reject(&"", &"NO_ANIMATION_PLAYER", "AnimationPlayer binding is required")

	for raw_state in state_to_motion.keys():
		var state_id := StringName(String(raw_state))
		var raw_descriptor: Variant = state_to_motion[raw_state]
		if typeof(raw_descriptor) != TYPE_DICTIONARY:
			return _reject(state_id, &"INVALID_DESCRIPTOR", "mapping entry must be a Dictionary")
		var descriptor: Dictionary = raw_descriptor
		if not descriptor.has("motion_semantic_id") or not descriptor.has("clip_name"):
			return _reject(state_id, &"INVALID_DESCRIPTOR", "motion_semantic_id and clip_name are required")
		var motion_semantic_id := StringName(String(descriptor["motion_semantic_id"]))
		var clip_name := StringName(String(descriptor["clip_name"]))
		if motion_semantic_id.is_empty() or clip_name.is_empty():
			return _reject(state_id, &"INVALID_DESCRIPTOR", "semantic and clip identities must be non-empty")
		var blend_seconds := float(descriptor.get("blend_seconds", 0.15))
		var playback_speed := float(descriptor.get("playback_speed", 1.0))
		if blend_seconds < 0.0:
			return _reject(state_id, &"INVALID_DESCRIPTOR", "blend_seconds must be >= 0")
		if playback_speed <= 0.0:
			return _reject(state_id, &"INVALID_DESCRIPTOR", "playback_speed must be > 0")
		_mapping[state_id] = {
			"motion_semantic_id": motion_semantic_id,
			"clip_name": clip_name,
			"blend_seconds": blend_seconds,
			"playback_speed": playback_speed,
		}

	for raw_from in legal_transitions.keys():
		var from_state := StringName(String(raw_from))
		var normalized_targets: Array[StringName] = []
		var raw_targets: Variant = legal_transitions[raw_from]
		if typeof(raw_targets) != TYPE_ARRAY and typeof(raw_targets) != TYPE_PACKED_STRING_ARRAY:
			return _reject(from_state, &"INVALID_TRANSITION_GRAPH", "transition targets must be an Array")
		for raw_target in raw_targets:
			normalized_targets.append(StringName(String(raw_target)))
		_legal_transitions[from_state] = normalized_targets

	return true


func request_behavior_state(state_id: StringName, reason := "") -> bool:
	_clear_rejection()
	if _player == null:
		return _reject(state_id, &"NO_ANIMATION_PLAYER", "controller is not configured")
	if not _mapping.has(state_id):
		return _reject(state_id, &"MISSING_STATE_MAPPING", "no motion mapping exists for behavior state")

	# Repeated snapshots of the same semantic state must not restart playback every frame.
	# However, assigned_animation is the current-or-last selected animation key in Godot;
	# if another runtime path changed it, accepting the snapshot as a no-op would preserve
	# stale motion after the behavior state has already changed or been reaffirmed.
	if state_id == active_behavior_state:
		if _player.assigned_animation != active_clip_name:
			return _reject(
				state_id,
				&"STALE_RUNTIME_ANIMATION",
				"behavior state expects %s but AnimationPlayer assigned %s" % [active_clip_name, _player.assigned_animation]
			)
		return true

	if _strict_transitions and not active_behavior_state.is_empty():
		if not _legal_transitions.has(active_behavior_state):
			return _reject(state_id, &"MISSING_TRANSITION_RULE", "active state has no transition rule")
		var allowed_targets: Array = _legal_transitions[active_behavior_state]
		if not allowed_targets.has(state_id):
			return _reject(state_id, &"ILLEGAL_TRANSITION", "%s -> %s is not admitted" % [active_behavior_state, state_id])

	var descriptor: Dictionary = _mapping[state_id]
	var clip_name: StringName = descriptor["clip_name"]
	if not _player.has_animation(clip_name):
		return _reject(state_id, &"MISSING_RUNTIME_CLIP", "AnimationPlayer has no clip named %s" % clip_name)

	var previous_state := active_behavior_state
	var blend_seconds: float = descriptor["blend_seconds"]
	var playback_speed: float = descriptor["playback_speed"]
	_player.play(clip_name, blend_seconds, playback_speed, false)
	if _player.assigned_animation != clip_name:
		return _reject(
			state_id,
			&"PLAYBACK_SELECTION_FAILED",
			"AnimationPlayer did not accept requested clip %s" % clip_name
		)

	active_behavior_state = state_id
	active_motion_semantic_id = descriptor["motion_semantic_id"]
	active_clip_name = clip_name
	transition_serial += 1
	motion_transitioned.emit(
		previous_state,
		active_behavior_state,
		active_motion_semantic_id,
		active_clip_name,
		reason
	)
	return true


func snapshot() -> Dictionary:
	return {
		"behavior_state_id": String(active_behavior_state),
		"motion_semantic_id": String(active_motion_semantic_id),
		"clip_name": String(active_clip_name),
		"transition_serial": transition_serial,
		"last_rejection_code": String(last_rejection_code),
		"last_rejection_detail": last_rejection_detail,
	}


func _clear_rejection() -> void:
	last_rejection_code = &""
	last_rejection_detail = ""


func _reject(state_id: StringName, code: StringName, detail: String) -> bool:
	last_rejection_code = code
	last_rejection_detail = detail
	motion_rejected.emit(state_id, code, detail)
	return false
