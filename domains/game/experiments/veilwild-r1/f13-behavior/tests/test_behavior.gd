extends SceneTree

const Policy = preload("res://creature_behavior_policy.gd")

var failures: Array[String] = []

func _init() -> void:
	_test_calm_stays_unaware()
	_test_visible_pressure_orients_then_freezes_without_cover()
	_test_cover_selects_concealment()
	_test_high_threat_evades_only_with_escape_path()
	_test_escape_unavailable_falls_back_without_emitting_evade()
	_test_decay_recovers_to_unaware()
	_test_deterministic_replay()
	if failures.is_empty():
		print("F13_BEHAVIOR_TESTS_PASS cases=7")
		quit(0)
	else:
		for failure in failures:
			push_error(failure)
		print("F13_BEHAVIOR_TESTS_FAIL count=%d" % failures.size())
		quit(1)

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
		"escape_available": false,
	}
	for key in overrides:
		value[key] = overrides[key]
	return value

func _advance(policy, sample: Dictionary, seconds: float, dt := 0.1) -> Dictionary:
	var result: Dictionary = {}
	var elapsed := 0.0
	while elapsed < seconds - 0.0001:
		result = policy.step(dt, sample)
		elapsed += dt
	return result

func _expect(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func _test_calm_stays_unaware() -> void:
	var policy = Policy.new()
	var result = _advance(policy, _sample(), 1.0)
	_expect(result.state_name == "UNAWARE", "calm/far/no-LOS must remain UNAWARE")
	_expect(result.nav_intent.action == "NONE", "UNAWARE must emit no nav action")

func _test_visible_pressure_orients_then_freezes_without_cover() -> void:
	var policy = Policy.new()
	var moderate := _sample({
		"player_distance_m": 8.0,
		"line_of_sight": true,
		"visual_exposure": 0.55,
		"player_motion": 0.40,
		"observation_pressure": 0.25,
	})
	var oriented = _advance(policy, moderate, 0.4)
	_expect(oriented.state_name == "ORIENT" or oriented.state_name == "FREEZE", "moderate visible pressure must leave UNAWARE")
	var high := moderate.duplicate()
	high.observation_pressure = 0.60
	var frozen = _advance(policy, high, 0.5)
	_expect(frozen.state_name == "FREEZE", "threat without cover/escape must FREEZE")
	_expect(frozen.nav_intent.action == "HOLD_POSITION", "FREEZE must request HOLD_POSITION")

func _test_cover_selects_concealment() -> void:
	var policy = Policy.new()
	var sample := _sample({
		"player_distance_m": 7.0,
		"line_of_sight": true,
		"visual_exposure": 0.75,
		"player_motion": 0.55,
		"observation_pressure": 0.62,
		"concealment_available": true,
		"concealment_quality": 0.8,
	})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "CONCEAL", "available cover under threat must select CONCEAL")
	_expect(is_equal_approx(result.camouflage_drive, 1.0), "CONCEAL must expose full camouflage intent drive")
	_expect(result.nav_intent.action == "SEEK_OR_MAINTAIN_CONCEALMENT", "CONCEAL must request concealment intent")

func _test_high_threat_evades_only_with_escape_path() -> void:
	var policy = Policy.new()
	var sample := _sample({
		"player_distance_m": 3.0,
		"line_of_sight": true,
		"visual_exposure": 1.0,
		"player_motion": 1.0,
		"observation_pressure": 0.95,
		"concealment_available": true,
		"concealment_quality": 0.6,
		"escape_available": true,
	})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "EVADE", "high threat with escape path must EVADE")
	_expect(result.nav_intent.action == "EVADE_FROM_THREAT", "EVADE must request F14 escape traversal")

func _test_escape_unavailable_falls_back_without_emitting_evade() -> void:
	var policy = Policy.new()
	var sample := _sample({
		"player_distance_m": 3.0,
		"line_of_sight": true,
		"visual_exposure": 1.0,
		"player_motion": 1.0,
		"observation_pressure": 0.95,
		"concealment_available": true,
		"concealment_quality": 0.9,
		"escape_available": false,
	})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "CONCEAL", "high threat without escape but with cover must CONCEAL")
	_expect(result.state_name != "EVADE", "EVADE must never be emitted without escape_available")

func _test_decay_recovers_to_unaware() -> void:
	var policy = Policy.new()
	var threat := _sample({
		"player_distance_m": 3.0,
		"line_of_sight": true,
		"visual_exposure": 1.0,
		"player_motion": 1.0,
		"observation_pressure": 0.95,
		"escape_available": true,
	})
	_advance(policy, threat, 0.8)
	var calm := _sample()
	var recovered = _advance(policy, calm, 2.5)
	_expect(recovered.state_name == "UNAWARE", "decayed threat must eventually recover to UNAWARE")

func _test_deterministic_replay() -> void:
	var sequence := [
		_sample(),
		_sample({"player_distance_m": 10.0, "line_of_sight": true, "visual_exposure": 0.4, "player_motion": 0.3}),
		_sample({"player_distance_m": 6.0, "line_of_sight": true, "visual_exposure": 0.8, "player_motion": 0.6, "observation_pressure": 0.55, "concealment_available": true}),
		_sample({"player_distance_m": 3.0, "line_of_sight": true, "visual_exposure": 1.0, "player_motion": 1.0, "observation_pressure": 0.95, "concealment_available": true, "escape_available": true}),
		_sample(),
	]
	var a = Policy.new()
	var b = Policy.new()
	var trace_a: Array[String] = []
	var trace_b: Array[String] = []
	for sample in sequence:
		for i in range(6):
			trace_a.append(JSON.stringify(a.step(0.1, sample)))
			trace_b.append(JSON.stringify(b.step(0.1, sample)))
	_expect(trace_a == trace_b, "same input sequence must replay to byte-equal decision trace")
