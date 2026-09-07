extends SceneTree

const RuntimeScene = preload("res://modules/f13/behavior_runtime.tscn")
const EventBusScript = preload("res://integration/event_bus.gd")

var failures: Array[String] = []
var direct_events: Array[Dictionary] = []
var generic_topics: Array[String] = []
var created_bus := false
var runtime: Node = null
var bus: Node = null

func _init() -> void:
	call_deferred("_run")

func _sample(overrides := {}) -> Dictionary:
	var value := {
		"player_distance_m": 20.0,
		"line_of_sight": false,
		"visual_exposure": 0.0,
		"player_motion": 0.0,
		"observation_pressure": 0.0,
		"nonvisual_stimulus": 0.0,
		"concealment_available": false,
		"concealment_quality": 0.0,
		"concealment_affordance_id": "",
		"escape_available": false,
		"escape_affordance_id": "",
	}
	for key in overrides:
		value[key] = overrides[key]
	return value

func _expect(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func _on_envelope(topic: StringName, payload: Dictionary, source: StringName) -> void:
	var topic_text := String(topic)
	if topic_text in ["creature_state_changed", "evade_started", "reacquisition_opportunity"]:
		direct_events.append({"topic": topic_text, "payload": payload.duplicate(true), "source": String(source)})
	elif topic_text.begins_with("creature.behavior."):
		generic_topics.append(topic_text)

func _run() -> void:
	bus = root.get_node_or_null("VeilwildEventBus")
	if bus == null:
		bus = EventBusScript.new()
		bus.name = "VeilwildEventBus"
		root.add_child(bus)
		created_bus = true
	bus.envelope_published.connect(_on_envelope)

	runtime = RuntimeScene.instantiate()
	root.add_child(runtime)

	var evade := _sample({
		"player_distance_m": 3.0,
		"line_of_sight": true,
		"visual_exposure": 1.0,
		"player_motion": 1.0,
		"observation_pressure": 0.95,
		"escape_available": true,
		"escape_affordance_id": "escape-owner-event",
	})
	for _i in range(12):
		runtime.submit_perception(0.1, evade)
	var calm := _sample()
	for _i in range(24):
		runtime.submit_perception(0.1, calm)

	var state_events: Array[Dictionary] = []
	var evade_events: Array[Dictionary] = []
	var reacquisition_events: Array[Dictionary] = []
	for envelope in direct_events:
		match envelope["topic"]:
			"creature_state_changed": state_events.append(envelope)
			"evade_started": evade_events.append(envelope)
			"reacquisition_opportunity": reacquisition_events.append(envelope)

	_expect(not state_events.is_empty(), "state entry must publish creature_state_changed")
	_expect(evade_events.size() == 1, "one actual EVADE entry must publish exactly one evade_started")
	_expect(reacquisition_events.is_empty(), "F13 must never publish reacquisition_opportunity from RECOVER")
	_expect(generic_topics.has("creature.behavior.transition"), "generic behavior transition transport must remain preserved")

	if not evade_events.is_empty():
		var envelope: Dictionary = evade_events[0]
		var payload: Dictionary = envelope["payload"]
		var data: Dictionary = payload.get("producerData", {})
		_expect(envelope["source"] == "F13", "EventBus source must remain F13")
		_expect(payload.get("sourceFront", "") == "A13/F13", "sourceFront mismatch")
		_expect(payload.get("producerSemanticId", "") == "F13.EVADE_STARTED", "evade producerSemanticId mismatch")
		_expect(data.get("behaviorStateId", "") == "veilwild.behavior.evade.r1", "evade behaviorStateId mismatch")
		_expect(data.get("transitionSemanticId", "") == "veilwild.behavior.transition.escape_selected.r1", "evade transitionSemanticId mismatch")
		_expect(int(data.get("transitionSequence", 0)) > 0, "evade transitionSequence must be positive")
		_expect(data.get("reasonId", "") == payload.get("reasonId", ""), "reasonId must survive owner mapping")
		_expect(data.get("playerCueAuthorization", null) is Dictionary, "playerCueAuthorization must survive owner mapping")
		_expect(bool(data.get("observationAbort", false)), "actual EVADE entry must retain observationAbort=true")

	for envelope in state_events:
		var payload: Dictionary = envelope["payload"]
		var data: Dictionary = payload.get("producerData", {})
		_expect(payload.get("sourceFront", "") == "A13/F13", "state event sourceFront mismatch")
		_expect(payload.get("producerSemanticId", "") == "F13.CREATURE_STATE_CHANGED", "state event producerSemanticId mismatch")
		_expect(not str(data.get("behaviorStateId", "")).is_empty(), "state event behaviorStateId missing")
		_expect(not str(data.get("transitionSemanticId", "")).is_empty(), "state event transitionSemanticId missing")
		_expect(int(data.get("transitionSequence", 0)) > 0, "state event transitionSequence must be positive")
		_expect(data.get("playerCueAuthorization", null) is Dictionary, "state event playerCueAuthorization missing")

	if failures.is_empty():
		print("F13_F22_OWNER_EVENTS_PASS state_changed=%d evade_started=%d reacquisition=%d" % [state_events.size(), evade_events.size(), reacquisition_events.size()])
		_finish(0)
	else:
		for failure in failures:
			push_error(failure)
		print("F13_F22_OWNER_EVENTS_FAIL count=%d" % failures.size())
		_finish(1)

func _finish(code: int) -> void:
	if runtime != null and is_instance_valid(runtime):
		root.remove_child(runtime)
		runtime.free()
	if created_bus and bus != null and is_instance_valid(bus):
		root.remove_child(bus)
		bus.free()
	quit(code)
