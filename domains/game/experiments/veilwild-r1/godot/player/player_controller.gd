class_name VeilwildPlayerController
extends CharacterBody3D
## A25/F18 player-interaction runtime only.
## InputSignal != GameAction != ObservationSuccess: this controller emits an
## explicit observe request and never decides target validity or success.

signal observe_requested(request_id: int, origin: Vector3, forward: Vector3)
signal observe_cancelled(request_id: int, reason_id: StringName)
signal observe_request_closed(request_id: int, disposition: StringName)
signal pointer_capture_changed(captured: bool)
signal action_demonstrated(action_id: StringName)
signal action_binding_changed(action_id: StringName, binding_label: String)
signal settings_requested()

const ACTION_MOVE_FORWARD: StringName = &"vw_move_forward"
const ACTION_MOVE_BACK: StringName = &"vw_move_back"
const ACTION_MOVE_LEFT: StringName = &"vw_move_left"
const ACTION_MOVE_RIGHT: StringName = &"vw_move_right"
const ACTION_OBSERVE: StringName = &"vw_observe"
const ACTION_POINTER_CAPTURE: StringName = &"vw_pointer_capture"
const ACTION_SETTINGS: StringName = &"vw_settings"

const OBSERVE_STARTED_TOPIC: StringName = &"observe_action_started"
const OBSERVE_CANCELLED_TOPIC: StringName = &"observe_action_cancelled"
const EVENT_SOURCE: StringName = &"A25/F18"
const SEMANTIC_OBSERVE_STARTED: String = "F18.OBSERVE_ACTION_STARTED"
const SEMANTIC_OBSERVE_CANCELLED: String = "F18.OBSERVE_ACTION_CANCELLED"

const OBSERVE_SINGLE_PRESS: StringName = &"SINGLE_PRESS"
const OBSERVE_HOLD: StringName = &"HOLD"
const OBSERVE_TOGGLE: StringName = &"TOGGLE"
const OBSERVE_MODES: Array[StringName] = [OBSERVE_SINGLE_PRESS, OBSERVE_HOLD, OBSERVE_TOGGLE]

const REMAPPABLE_ACTIONS: Array[StringName] = [
	ACTION_MOVE_FORWARD,
	ACTION_MOVE_BACK,
	ACTION_MOVE_LEFT,
	ACTION_MOVE_RIGHT,
	ACTION_OBSERVE,
]

@export_category("Locomotion")
@export var walk_speed_mps: float = 4.0
@export var horizontal_acceleration_mps2: float = 18.0
@export var gravity_enabled: bool = true

@export_category("Camera")
@export var mouse_sensitivity_rad_per_pixel: float = 0.0024
@export_range(0.5, 2.0, 0.05) var look_sensitivity_multiplier: float = 1.0
@export var invert_look_x: bool = false
@export var invert_look_y: bool = false
@export_range(30.0, 89.0, 0.5) var pitch_limit_degrees: float = 82.0
@export_range(60.0, 100.0, 1.0) var field_of_view_degrees: float = 70.0
@export var capture_pointer_on_ready: bool = true

@export_category("Interaction")
@export_enum("SINGLE_PRESS", "HOLD", "TOGGLE") var observe_activation_mode_index: int = 0

@onready var pitch_pivot: Node3D = %PitchPivot
@onready var camera: Camera3D = %Camera3D
@onready var audio_listener: AudioListener3D = %AudioListener3D

var _gravity_mps2: float = 9.8
var _observe_active := false
var _active_observe_request_id := 0
var _next_observe_request_id := 1
var _demonstrated_actions: Dictionary = {}
var _pointer_capture_requested := false
var _gameplay_input_enabled := true

func _ready() -> void:
	add_to_group("veilwild.player_runtime")
	_ensure_default_input_actions()
	_gravity_mps2 = float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
	camera.fov = field_of_view_degrees
	if capture_pointer_on_ready:
		set_pointer_captured(true)

func _physics_process(delta: float) -> void:
	_apply_locomotion(delta)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(ACTION_SETTINGS):
		settings_requested.emit()
		return
	if event is InputEventKey and (event as InputEventKey).pressed and (event as InputEventKey).keycode == KEY_ESCAPE:
		if _gameplay_input_enabled:
			set_pointer_captured(false)
		return
	if not _gameplay_input_enabled:
		return
	if event is InputEventMouseMotion and _pointer_capture_requested:
		apply_look_delta((event as InputEventMouseMotion).relative)
		_mark_action_demonstrated(&"LOOK")
		return
	if event.is_action_pressed(ACTION_OBSERVE):
		_handle_observe_pressed()
		return
	if event.is_action_released(ACTION_OBSERVE):
		_handle_observe_released()
		return
	if event.is_action_pressed(ACTION_POINTER_CAPTURE):
		set_pointer_captured(true)

func _apply_locomotion(delta: float) -> void:
	var input_vector := Vector2.ZERO
	if _gameplay_input_enabled:
		input_vector = Input.get_vector(
			ACTION_MOVE_LEFT,
			ACTION_MOVE_RIGHT,
			ACTION_MOVE_FORWARD,
			ACTION_MOVE_BACK
		)
	var local_direction := Vector3(input_vector.x, 0.0, input_vector.y)
	var world_direction := global_transform.basis * local_direction
	world_direction.y = 0.0
	if world_direction.length_squared() > 1.0:
		world_direction = world_direction.normalized()
	var target_x := world_direction.x * walk_speed_mps
	var target_z := world_direction.z * walk_speed_mps
	velocity.x = move_toward(velocity.x, target_x, horizontal_acceleration_mps2 * delta)
	velocity.z = move_toward(velocity.z, target_z, horizontal_acceleration_mps2 * delta)
	if gravity_enabled and not is_on_floor():
		velocity.y -= _gravity_mps2 * delta
	elif is_on_floor() and velocity.y < 0.0:
		velocity.y = 0.0
	move_and_slide()
	if input_vector.length_squared() > 0.0001:
		_mark_action_demonstrated(&"MOVE")

func apply_look_delta(relative_pixels: Vector2) -> void:
	var x_sign := 1.0 if invert_look_x else -1.0
	var y_sign := 1.0 if invert_look_y else -1.0
	var sensitivity := mouse_sensitivity_rad_per_pixel * look_sensitivity_multiplier
	rotate_y(relative_pixels.x * sensitivity * x_sign)
	var limit := deg_to_rad(pitch_limit_degrees)
	pitch_pivot.rotation.x = clamp(
		pitch_pivot.rotation.x + relative_pixels.y * sensitivity * y_sign,
		-limit,
		limit
	)

func _handle_observe_pressed() -> void:
	var mode := get_observe_activation_mode()
	if mode == OBSERVE_TOGGLE and _observe_active:
		cancel_observe_action(&"PLAYER_TOGGLE_OFF")
		return
	begin_observe_action()

func _handle_observe_released() -> void:
	if get_observe_activation_mode() == OBSERVE_HOLD:
		cancel_observe_action(&"PLAYER_RELEASE")

func begin_observe_action() -> int:
	if _observe_active:
		return _active_observe_request_id
	_observe_active = true
	_active_observe_request_id = _next_observe_request_id
	_next_observe_request_id += 1
	var origin := get_observation_origin()
	var forward := get_observation_forward()
	observe_requested.emit(_active_observe_request_id, origin, forward)
	_publish_runtime_event(OBSERVE_STARTED_TOPIC, {
		"sourceFront": "A25/F18",
		"producerSemanticId": SEMANTIC_OBSERVE_STARTED,
		"worldPositionMeters": [origin.x, origin.y, origin.z],
		"producerData": {
			"requestId": _active_observe_request_id,
			"forward": [forward.x, forward.y, forward.z],
			"activationMode": String(get_observe_activation_mode()),
		},
	})
	_mark_action_demonstrated(&"OBSERVE")
	return _active_observe_request_id

func cancel_observe_action(reason_id: StringName = &"PLAYER_CANCELLED") -> void:
	if not _observe_active:
		return
	var ended_id := _active_observe_request_id
	_observe_active = false
	_active_observe_request_id = 0
	observe_cancelled.emit(ended_id, reason_id)
	_publish_runtime_event(OBSERVE_CANCELLED_TOPIC, {
		"sourceFront": "A25/F18",
		"producerSemanticId": SEMANTIC_OBSERVE_CANCELLED,
		"reasonId": String(reason_id),
		"producerData": {"requestId": ended_id},
	})

func close_observe_request(request_id: int, disposition: StringName = &"OWNER_RESOLVED") -> bool:
	if not _observe_active or request_id != _active_observe_request_id:
		return false
	_observe_active = false
	_active_observe_request_id = 0
	observe_request_closed.emit(request_id, disposition)
	return true

func is_observe_action_active() -> bool:
	return _observe_active

func get_observe_activation_mode() -> StringName:
	return OBSERVE_MODES[clampi(observe_activation_mode_index, 0, OBSERVE_MODES.size() - 1)]

func set_observe_activation_mode(mode: StringName) -> bool:
	var index := OBSERVE_MODES.find(mode)
	if index < 0:
		return false
	if _observe_active:
		cancel_observe_action(&"ACTIVATION_MODE_CHANGED")
	observe_activation_mode_index = index
	return true

func set_gameplay_input_enabled(enabled: bool) -> void:
	_gameplay_input_enabled = enabled
	if not enabled and get_observe_activation_mode() == OBSERVE_HOLD:
		cancel_observe_action(&"GAMEPLAY_INPUT_SUSPENDED")

func is_gameplay_input_enabled() -> bool:
	return _gameplay_input_enabled

func remap_action_to_physical_key(action_id: StringName, physical_keycode: Key) -> bool:
	if action_id not in REMAPPABLE_ACTIONS or physical_keycode == KEY_NONE:
		return false
	if not InputMap.has_action(action_id):
		InputMap.add_action(action_id)
	InputMap.action_erase_events(action_id)
	var key_event := InputEventKey.new()
	key_event.physical_keycode = physical_keycode
	InputMap.action_add_event(action_id, key_event)
	action_binding_changed.emit(action_id, get_action_binding_label(action_id))
	return true

func get_action_binding_label(action_id: StringName) -> String:
	if not InputMap.has_action(action_id):
		return "Unbound"
	var events := InputMap.action_get_events(action_id)
	if events.is_empty():
		return "Unbound"
	return (events[0] as InputEvent).as_text()

func set_look_sensitivity_multiplier(value: float) -> void:
	look_sensitivity_multiplier = clamp(value, 0.5, 2.0)

func set_look_inversion(invert_x: bool, invert_y: bool) -> void:
	invert_look_x = invert_x
	invert_look_y = invert_y

func set_camera_fov_degrees(value: float) -> void:
	field_of_view_degrees = clamp(value, 60.0, 100.0)
	camera.fov = field_of_view_degrees

func get_observation_origin() -> Vector3:
	return camera.global_position

func get_observation_forward() -> Vector3:
	return (-camera.global_transform.basis.z).normalized()

func get_listener_transform() -> Transform3D:
	return audio_listener.global_transform

func get_camera_validation_condition() -> Dictionary:
	return {
		"carrier": "Camera3D",
		"fovDegrees": camera.fov,
		"fovRangeDegrees": [60.0, 100.0],
		"nearMeters": camera.near,
		"farMeters": camera.far,
		"eyeHeightMeters": pitch_pivot.position.y,
		"pitchLimitDegrees": pitch_limit_degrees,
		"mouseSensitivityRadiansPerPixel": mouse_sensitivity_rad_per_pixel,
		"lookSensitivityMultiplierRange": [0.5, 2.0],
		"invertXSupported": true,
		"invertYSupported": true,
		"nonEssentialBobShake": false,
		"motionBlurOwnedOrEnabledByF18": false,
		"runtimeAxes": {"right": "+X", "up": "+Y", "forward": "-Z"},
	}

func get_player_collision_footprint() -> Dictionary:
	return {
		"shape": "capsule",
		"radiusMeters": 0.35,
		"totalHeightMeters": 1.8,
		"rootMeaning": "player feet / traversal origin",
		"eyeHeightMeters": pitch_pivot.position.y,
		"unit": "meter",
		"axes": {"right": "+X", "up": "+Y", "forward": "-Z"},
		"collisionLayerBits": [2],
		"collisionLayerMaskValue": collision_layer,
		"collisionMaskBits": [1],
		"collisionMaskValue": collision_mask,
		"motionMode": "GROUNDED",
		"upDirection": [up_direction.x, up_direction.y, up_direction.z],
		"floorMaxAngleDegrees": rad_to_deg(floor_max_angle),
		"floorSnapLengthMeters": floor_snap_length,
		"floorStopOnSlope": floor_stop_on_slope,
		"floorBlockOnWall": floor_block_on_wall,
		"floorConstantSpeed": floor_constant_speed,
		"safeMarginMeters": safe_margin,
		"maxSlides": max_slides,
		"wallMinSlideAngleDegrees": rad_to_deg(wall_min_slide_angle),
		"environmentCollisionExpectation": "A14/F14 environment traversal collision is expected on physics layer 1; incompatibility must be owner-to-owner versioned rather than silently remapped.",
	}

func get_input_contract() -> Dictionary:
	return {
		"requiredActions": REMAPPABLE_ACTIONS.map(func(value: StringName) -> String: return String(value)),
		"pointerCaptureAction": String(ACTION_POINTER_CAPTURE),
		"settingsAction": String(ACTION_SETTINGS),
		"defaultDevice": "keyboard_mouse",
		"remappingRule": "Semantic Godot InputMap actions; runtime remap replaces only the selected semantic action and emits action_binding_changed.",
		"observeActivationChoices": OBSERVE_MODES.map(func(value: StringName) -> String: return String(value)),
		"observeDefaultActivation": String(OBSERVE_SINGLE_PRESS),
	}

func get_accessibility_runtime_receipt() -> Dictionary:
	var actions: Array[Dictionary] = []
	for action_id in REMAPPABLE_ACTIONS:
		actions.append({
			"actionId": String(action_id),
			"currentBinding": get_action_binding_label(action_id),
			"remappable": true,
			"requiresChord": false,
			"holdDurationMs": 0 if action_id != ACTION_OBSERVE or get_observe_activation_mode() != OBSERVE_HOLD else null,
			"alternateActivation": ["SINGLE_PRESS", "TOGGLE", "HOLD"] if action_id == ACTION_OBSERVE else [],
			"promptReflectsRemap": true,
		})
	return {
		"input": actions,
		"lookSensitivityMultiplier": look_sensitivity_multiplier,
		"lookSensitivityRange": [0.5, 2.0],
		"invertXSupported": true,
		"invertYSupported": true,
		"observeActivationMode": String(get_observe_activation_mode()),
		"cameraBobMode": "NOT_APPLICABLE",
		"cameraShakeMode": "NOT_APPLICABLE",
		"motionBlurMode": "NOT_APPLICABLE",
		"fieldOfViewDegrees": camera.fov,
		"fieldOfViewRangeDegrees": [60.0, 100.0],
	}

func set_pointer_captured(captured: bool) -> void:
	_pointer_capture_requested = captured
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if captured else Input.MOUSE_MODE_VISIBLE
	pointer_capture_changed.emit(captured)

func is_pointer_capture_requested() -> bool:
	return _pointer_capture_requested

func _ensure_default_input_actions() -> void:
	_ensure_key_action(ACTION_MOVE_FORWARD, KEY_W)
	_ensure_key_action(ACTION_MOVE_BACK, KEY_S)
	_ensure_key_action(ACTION_MOVE_LEFT, KEY_A)
	_ensure_key_action(ACTION_MOVE_RIGHT, KEY_D)
	_ensure_key_action(ACTION_OBSERVE, KEY_E)
	_ensure_key_action(ACTION_SETTINGS, KEY_F1)
	_ensure_mouse_button_action(ACTION_POINTER_CAPTURE, MOUSE_BUTTON_LEFT)

func _ensure_key_action(action: StringName, physical_keycode: Key) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	if not InputMap.action_get_events(action).is_empty():
		return
	var key_event := InputEventKey.new()
	key_event.physical_keycode = physical_keycode
	InputMap.action_add_event(action, key_event)

func _ensure_mouse_button_action(action: StringName, button_index: MouseButton) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	if not InputMap.action_get_events(action).is_empty():
		return
	var mouse_event := InputEventMouseButton.new()
	mouse_event.button_index = button_index
	InputMap.action_add_event(action, mouse_event)

func _mark_action_demonstrated(action_id: StringName) -> void:
	if _demonstrated_actions.has(action_id):
		return
	_demonstrated_actions[action_id] = true
	action_demonstrated.emit(action_id)

func _publish_runtime_event(topic: StringName, payload: Dictionary) -> void:
	var bus := get_node_or_null("/root/VeilwildEventBus")
	if bus != null and bus.has_method("publish"):
		bus.call("publish", topic, payload, EVENT_SOURCE)
