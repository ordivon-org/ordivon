extends SceneTree

var failures: Array[String] = []
var published_topics: Array[StringName] = []
var published_payloads: Array[Dictionary] = []
var observe_count := 0
var observe_id := 0

func _init() -> void:
	call_deferred("_run")

func _expect(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func _on_envelope(topic: StringName, payload: Dictionary, source: StringName) -> void:
	if source == &"A25/F18":
		published_topics.append(topic)
		published_payloads.append(payload.duplicate(true))

func _on_observe_requested(request_id: int, _origin: Vector3, _forward: Vector3) -> void:
	observe_count += 1
	observe_id = request_id

func _physical_key_event(key: Key, pressed: bool) -> InputEventKey:
	var event := InputEventKey.new()
	event.physical_keycode = key
	event.pressed = pressed
	return event

func _run() -> void:
	var bus: Node = root.get_node_or_null("VeilwildEventBus")
	_expect(bus != null, "VeilwildEventBus autoload missing")
	if bus != null:
		bus.connect("envelope_published", _on_envelope)

	var player_scene: PackedScene = load("res://player/player_runtime.tscn") as PackedScene
	_expect(player_scene != null, "player_runtime.tscn failed to load")
	if player_scene == null:
		_finish()
		return
	var player: Variant = player_scene.instantiate()
	root.add_child(player)
	await process_frame

	for action: StringName in [&"vw_move_forward", &"vw_move_back", &"vw_move_left", &"vw_move_right", &"vw_observe"]:
		_expect(InputMap.has_action(action), "InputMap missing action %s" % action)
		_expect(not InputMap.action_get_events(action).is_empty(), "InputMap action has no device event %s" % action)
	_expect(InputMap.has_action(&"vw_settings"), "keyboard settings action missing")

	var footprint: Dictionary = player.call("get_player_collision_footprint")
	_expect(is_equal_approx(float(footprint["radiusMeters"]), 0.35), "unexpected player capsule radius")
	_expect(is_equal_approx(float(footprint["totalHeightMeters"]), 1.8), "unexpected player capsule height")
	_expect(int(footprint["collisionLayerMaskValue"]) == 2, "player collision layer drift")
	_expect(int(footprint["collisionMaskValue"]) == 1, "player collision mask drift")
	_expect(String(footprint["motionMode"]) == "GROUNDED", "player motion mode drift")
	_expect(is_equal_approx(float(footprint["floorMaxAngleDegrees"]), 45.0), "player floor max angle drift")
	_expect(is_equal_approx(float(footprint["floorSnapLengthMeters"]), 0.1), "player floor snap drift")
	_expect(bool(footprint["floorStopOnSlope"]), "player floor stop-on-slope disabled")
	_expect(bool(footprint["floorBlockOnWall"]), "player floor block-on-wall disabled")
	_expect(bool(footprint["floorConstantSpeed"]), "player floor constant-speed disabled")
	var camera_condition: Dictionary = player.call("get_camera_validation_condition")
	_expect(is_equal_approx(float(camera_condition["fovDegrees"]), 70.0), "unexpected camera FOV")
	_expect(camera_condition["nonEssentialBobShake"] == false, "camera fixture unexpectedly enables bob/shake")
	_expect(camera_condition["invertXSupported"] == true and camera_condition["invertYSupported"] == true, "independent look inversion support missing")

	var start_position: Vector3 = player.global_position
	Input.parse_input_event(_physical_key_event(KEY_W, true))
	await physics_frame
	await physics_frame
	Input.parse_input_event(_physical_key_event(KEY_W, false))
	await physics_frame
	_expect(player.global_position.z < start_position.z - 0.001, "physical W input did not produce forward -Z locomotion")

	var yaw_before: float = player.rotation.y
	var pitch_node: Node3D = player.get_node("PitchPivot") as Node3D
	var pitch_before: float = pitch_node.rotation.x
	var mouse_motion := InputEventMouseMotion.new()
	mouse_motion.relative = Vector2(40.0, -20.0)
	player.call("_unhandled_input", mouse_motion)
	_expect(not is_equal_approx(player.rotation.y, yaw_before), "mouse motion did not change yaw")
	_expect(not is_equal_approx(pitch_node.rotation.x, pitch_before), "mouse motion did not change pitch")
	player.call("apply_look_delta", Vector2(0.0, 100000.0))
	_expect(abs(rad_to_deg(pitch_node.rotation.x)) <= float(player.get("pitch_limit_degrees")) + 0.01, "pitch clamp exceeded declared limit")
	player.call("set_look_sensitivity_multiplier", 0.5)
	_expect(is_equal_approx(float(player.get("look_sensitivity_multiplier")), 0.5), "50% look sensitivity unavailable")
	player.call("set_look_sensitivity_multiplier", 1.5)
	_expect(is_equal_approx(float(player.get("look_sensitivity_multiplier")), 1.5), "+50% look sensitivity unavailable")
	player.call("set_look_inversion", true, false)
	_expect(bool(player.get("invert_look_x")) and not bool(player.get("invert_look_y")), "independent inversion setting failed")
	player.call("set_camera_fov_degrees", 95.0)
	_expect(is_equal_approx(float(player.get_node("PitchPivot/Camera3D").fov), 95.0), "adjustable FOV binding failed")

	player.connect("observe_requested", _on_observe_requested)
	_expect(StringName(player.call("get_observe_activation_mode")) == &"SINGLE_PRESS", "observe default must provide non-hold activation")
	Input.parse_input_event(_physical_key_event(KEY_E, true))
	await physics_frame
	Input.parse_input_event(_physical_key_event(KEY_E, false))
	await physics_frame
	_expect(observe_count == 1, "physical E input did not emit exactly one explicit observe request")
	_expect(observe_id > 0, "observe request id was not positive")
	_expect(bool(player.call("is_observe_action_active")), "single-press observe did not latch after key release")
	_expect(&"observe_action_started" in published_topics, "observe start did not reach F22-compatible event transport")
	player.call("cancel_observe_action", &"MECHANICAL_TEST_CANCEL")
	_expect(not bool(player.call("is_observe_action_active")), "observe cancellation did not clear active request")
	_expect(&"observe_action_cancelled" in published_topics, "observe cancellation did not reach F22-compatible event transport")
	_expect(not player.has_signal("observation_succeeded"), "PlayerController must not own observation success")
	var saw_f22_fields := false
	for payload in published_payloads:
		if payload.get("producerSemanticId", "") == "F18.OBSERVE_ACTION_STARTED":
			saw_f22_fields = payload.get("sourceFront", "") == "A25/F18"
	_expect(saw_f22_fields, "observe event missing F22 producer sourceFront/producerSemanticId")

	var ui_scene: PackedScene = load("res://player/player_ui.tscn") as PackedScene
	_expect(ui_scene != null, "player_ui.tscn failed to load")
	if ui_scene != null:
		var ui: Variant = ui_scene.instantiate()
		root.add_child(ui)
		await process_frame
		var feedback_contract: Dictionary = ui.call("get_feedback_contract")
		_expect(feedback_contract["targetLocationInput"] == false, "UI contract unexpectedly accepts target location")
		_expect(feedback_contract["hiddenStateInput"] == false, "UI contract unexpectedly accepts hidden state")
		_expect(int(feedback_contract["baseTextPixels"]) >= 18, "UI base text below 18 px mechanical target")
		ui.call("set_ui_scale_factor", 2.0)
		_expect(is_equal_approx(float(ui.call("get_ui_scale_factor")), 2.0), "UI did not accept 200% scale")
		_expect(bool(ui.call("present_feedback", &"OBSERVATION_PROGRESS", 0.5)), "observation progress feedback rejected")
		_expect(bool(ui.call("present_feedback", &"SUCCESS_CONSEQUENCE")), "success consequence feedback rejected")
		_expect(not bool(ui.call("present_feedback", &"EXACT_TARGET_LOCATION")), "UI accepted forbidden locator feedback class")
		_expect(&"observation_progress" in published_topics, "qualified progress feedback did not emit F22 event type")
		_expect(&"success_consequence" in published_topics, "success consequence presentation did not emit F22 event type")

		var prompt_before := String(ui.get_node("OnboardingPanel/OnboardingText").text)
		_expect(prompt_before.find("E") >= 0, "onboarding prompt missing current observe binding")
		_expect(bool(player.call("remap_action_to_physical_key", &"vw_observe", KEY_Q)), "semantic observe remap failed")
		await process_frame
		var prompt_after := String(ui.get_node("OnboardingPanel/OnboardingText").text)
		_expect(prompt_after.find("Q") >= 0 and prompt_after != prompt_before, "onboarding prompt did not update after remap")
		player.call("remap_action_to_physical_key", &"vw_observe", KEY_E)

		Input.parse_input_event(_physical_key_event(KEY_F1, true))
		await process_frame
		Input.parse_input_event(_physical_key_event(KEY_F1, false))
		await process_frame
		_expect(bool(ui.call("is_settings_visible")), "F1 did not open keyboard-operable settings")
		_expect(not bool(player.call("is_gameplay_input_enabled")), "gameplay input remained active behind settings")
		ui.call("set_settings_visible", false)
		_expect(bool(player.call("is_gameplay_input_enabled")), "gameplay input did not restore after settings close")
		ui.queue_free()

	player.queue_free()
	await process_frame
	_finish()

func _finish() -> void:
	if failures.is_empty():
		print("VEILWILD_F18_MECHANICAL_PASS input=remappable observe=single_press camera=adjustable ui=non_locator accessibility=settings")
		quit(0)
		return
	for failure in failures:
		push_error("VEILWILD_F18_TEST_FAILURE %s" % failure)
	print("VEILWILD_F18_MECHANICAL_FAIL count=%d" % failures.size())
	quit(1)
