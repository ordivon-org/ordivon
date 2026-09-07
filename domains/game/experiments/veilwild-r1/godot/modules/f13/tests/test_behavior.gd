extends SceneTree

const Policy = preload("res://modules/f13/creature_behavior_policy.gd")
const RuntimeScene = preload("res://modules/f13/behavior_runtime.tscn")
var failures: Array[String] = []

func _init() -> void:
	_test_calm_stays_unaware()
	_test_visible_pressure_orients_then_freezes_without_cover()
	_test_cover_selects_concealment()
	_test_high_threat_evades_only_with_escape_path()
	_test_escape_unavailable_falls_back_without_emitting_evade()
	_test_decay_recovers_to_unaware()
	_test_deterministic_replay()
	_test_product_intent_and_cue_contract()
	_test_transition_edge_contract()
	_test_mountable_runtime_scene()
	_test_cue_authorization_matrix()
	_test_recovery_is_not_reacquisition_proof()
	if failures.is_empty():
		print("F13_BEHAVIOR_TESTS_PASS cases=12")
		quit(0)
	else:
		for failure in failures: push_error(failure)
		print("F13_BEHAVIOR_TESTS_FAIL count=%d" % failures.size())
		quit(1)

func _sample(overrides := {}) -> Dictionary:
	var value := {
		"player_distance_m": 20.0, "line_of_sight": false, "visual_exposure": 0.0,
		"player_motion": 0.0, "observation_pressure": 0.0, "nonvisual_stimulus": 0.0,
		"concealment_available": false, "concealment_quality": 0.0, "concealment_affordance_id": "",
		"escape_available": false, "escape_affordance_id": "",
	}
	for key in overrides: value[key] = overrides[key]
	return value

func _advance(policy, sample: Dictionary, seconds: float, dt := 0.1) -> Dictionary:
	var result: Dictionary = {}
	var elapsed := 0.0
	while elapsed < seconds - 0.0001:
		result = policy.step(dt, sample)
		elapsed += dt
	return result

func _expect(condition: bool, message: String) -> void:
	if not condition: failures.append(message)

func _test_calm_stays_unaware() -> void:
	var result = _advance(Policy.new(), _sample(), 1.0)
	_expect(result.state_name == "UNAWARE", "calm/far/no-LOS must remain UNAWARE")
	_expect(result.behavior_state_id == "veilwild.behavior.unaware.r1", "UNAWARE stable state id mismatch")
	_expect(result.nav_intent.action == "NONE", "UNAWARE must emit no nav action")
	_expect(result.product_intent == "UNTHREATENED", "UNAWARE must map to A01 UNTHREATENED")

func _test_visible_pressure_orients_then_freezes_without_cover() -> void:
	var policy = Policy.new()
	var moderate := _sample({"player_distance_m":8.0,"line_of_sight":true,"visual_exposure":0.55,"player_motion":0.40,"observation_pressure":0.25})
	var oriented = _advance(policy, moderate, 0.4)
	_expect(oriented.state_name == "ORIENT" or oriented.state_name == "FREEZE", "moderate visible pressure must leave UNAWARE")
	var high := moderate.duplicate(); high.observation_pressure = 0.60
	var frozen = _advance(policy, high, 0.5)
	_expect(frozen.state_name == "FREEZE", "threat without cover/escape must FREEZE")
	_expect(frozen.product_intent == "ALERT_ORIENT", "FREEZE must map to A01 ALERT_ORIENT")
	_expect(frozen.nav_intent.action == "HOLD_POSITION", "FREEZE must request HOLD_POSITION")

func _test_cover_selects_concealment() -> void:
	var policy = Policy.new()
	var sample := _sample({"player_distance_m":7.0,"line_of_sight":true,"visual_exposure":0.75,"player_motion":0.55,"observation_pressure":0.62,"concealment_available":true,"concealment_quality":0.8,"concealment_affordance_id":"cover-a"})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "CONCEAL", "available cover under threat must select CONCEAL")
	_expect(result.product_intent == "CONCEAL", "CONCEAL must map to A01 CONCEAL")
	_expect(is_equal_approx(result.camouflage_drive, 1.0), "CONCEAL must expose camouflage intent drive")
	_expect(result.nav_intent.action == "SEEK_OR_MAINTAIN_CONCEALMENT", "CONCEAL nav intent mismatch")
	_expect(result.nav_intent.target_affordance_id == "cover-a", "F14 concealment affordance id must round-trip")

func _test_high_threat_evades_only_with_escape_path() -> void:
	var policy = Policy.new()
	var sample := _sample({"player_distance_m":3.0,"line_of_sight":true,"visual_exposure":1.0,"player_motion":1.0,"observation_pressure":0.95,"concealment_available":true,"concealment_quality":0.6,"concealment_affordance_id":"cover-a","escape_available":true,"escape_affordance_id":"escape-b"})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "EVADE", "high threat with escape path must EVADE")
	_expect(result.product_intent == "EVADE", "EVADE must map to A01 EVADE")
	_expect(result.observation_abort, "EVADE must expose F13 observation-abort boundary")
	_expect(result.nav_intent.action == "EVADE_FROM_THREAT", "EVADE nav intent mismatch")
	_expect(result.nav_intent.target_affordance_id == "escape-b", "F14 escape affordance id must round-trip")

func _test_escape_unavailable_falls_back_without_emitting_evade() -> void:
	var policy = Policy.new()
	var sample := _sample({"player_distance_m":3.0,"line_of_sight":true,"visual_exposure":1.0,"player_motion":1.0,"observation_pressure":0.95,"concealment_available":true,"concealment_quality":0.9,"concealment_affordance_id":"cover-fallback","escape_available":false})
	var result = _advance(policy, sample, 0.8)
	_expect(result.state_name == "CONCEAL", "high threat without escape but with cover must CONCEAL")
	_expect(result.state_name != "EVADE", "EVADE must never be emitted without escape_available")

func _test_decay_recovers_to_unaware() -> void:
	var policy = Policy.new()
	var threat_sample := _sample({"player_distance_m":3.0,"line_of_sight":true,"visual_exposure":1.0,"player_motion":1.0,"observation_pressure":0.95,"escape_available":true,"escape_affordance_id":"escape-a"})
	_advance(policy, threat_sample, 0.8)
	var calm := _sample()
	var saw_recover := false
	for i in range(25):
		var decision = policy.step(0.1, calm)
		if decision.state_name == "RECOVER": saw_recover = true
	var recovered = policy.step(0.1, calm)
	_expect(saw_recover, "EVADE must pass through RECOVER reacquisition phase")
	_expect(recovered.state_name == "UNAWARE", "decayed threat must recover to UNAWARE")
	_expect(not recovered.observation_abort, "recovered state must clear observation abort")

func _test_deterministic_replay() -> void:
	var sequence := [
		_sample(),
		_sample({"player_distance_m":10.0,"line_of_sight":true,"visual_exposure":0.4,"player_motion":0.3}),
		_sample({"player_distance_m":6.0,"line_of_sight":true,"visual_exposure":0.8,"player_motion":0.6,"observation_pressure":0.55,"concealment_available":true,"concealment_affordance_id":"cover-a"}),
		_sample({"player_distance_m":3.0,"line_of_sight":true,"visual_exposure":1.0,"player_motion":1.0,"observation_pressure":0.95,"concealment_available":true,"concealment_affordance_id":"cover-a","escape_available":true,"escape_affordance_id":"escape-b"}),
		_sample(),
	]
	var a = Policy.new(); var b = Policy.new(); var trace_a: Array[String] = []; var trace_b: Array[String] = []
	for sample in sequence:
		for i in range(6):
			trace_a.append(JSON.stringify(a.step(0.1, sample)))
			trace_b.append(JSON.stringify(b.step(0.1, sample)))
	_expect(trace_a == trace_b, "same input sequence must replay to byte-equal decision trace")

func _test_product_intent_and_cue_contract() -> void:
	var policy = Policy.new()
	var result = _advance(policy, _sample({"player_distance_m":8.0,"line_of_sight":true,"visual_exposure":0.7,"player_motion":0.6,"observation_pressure":0.3}), 0.4)
	_expect(result.product_intent == "ALERT_ORIENT", "warning phase must map to ALERT_ORIENT")
	_expect(result.cue_opportunities.has("THREAT_RESPONSE"), "warning phase must expose THREAT_RESPONSE")
	_expect(result.cue_opportunities.has("MOTION_COUNTERCUE"), "warning phase must expose MOTION_COUNTERCUE")
	_expect(not result.has("observation_success"), "F13 must never award OBSERVATION_SUCCESS")

func _test_transition_edge_contract() -> void:
	var policy = Policy.new()
	var sample := _sample({"player_distance_m":8.0,"line_of_sight":true,"visual_exposure":0.8,"player_motion":0.5,"observation_pressure":0.35})
	var first_transition: Dictionary = {}
	for i in range(6):
		var result = policy.step(0.1, sample)
		if result.state_entered:
			first_transition = result; break
	_expect(not first_transition.is_empty(), "transition must expose edge-triggered decision")
	if not first_transition.is_empty():
		_expect(first_transition.transition_sequence == 1, "first transition sequence must be 1")
		_expect(first_transition.transition_semantic_id != "veilwild.behavior.transition.none.r1", "transition semantic id missing")
		var next = policy.step(0.1, sample)
		_expect(not next.state_entered, "sustained state must not repeat state-enter edge")
		_expect(next.transition_sequence == first_transition.transition_sequence, "transition order counter must remain stable during sustained state")

func _test_mountable_runtime_scene() -> void:
	var runtime = RuntimeScene.instantiate()
	_expect(runtime.has_method("submit_perception"), "runtime PackedScene must expose submit_perception")
	var transition_count := [0]
	runtime.behavior_transition.connect(func(_event): transition_count[0] += 1)
	root.add_child(runtime)
	var sample := _sample({"player_distance_m":8.0,"line_of_sight":true,"visual_exposure":0.8,"player_motion":0.5,"observation_pressure":0.35})
	for i in range(6): runtime.submit_perception(0.1, sample)
	_expect(transition_count[0] >= 1, "runtime must emit behavior_transition edge")
	_expect(runtime.get_last_decision().has("behavior_state_id"), "runtime must expose source-owned semantic decision")
	runtime.queue_free()

func _test_cue_authorization_matrix() -> void:
	var policy = Policy.new()
	for current_state in [Policy.State.UNAWARE, Policy.State.ORIENT, Policy.State.FREEZE, Policy.State.CONCEAL, Policy.State.EVADE, Policy.State.RECOVER]:
		policy.state = current_state
		policy.state_entered_this_step = false
		policy.last_transition_reason = Policy.TransitionReason.NONE
		var sustained = policy._player_cue_authorization()
		_expect(sustained["explicit_none_classes"].has("TRACE"), "TRACE must be explicit NONE for every F13 sustained state")
		_expect(not sustained["sustained_classes"].has("TRACE"), "TRACE must never be F13 state-authorized")
		var covered: int = int(sustained["sustained_classes"].size()) + int(sustained["explicit_none_classes"].size())
		_expect(covered == Policy.PLAYER_CUE_CLASSES.size(), "every cue class must be authorized or explicit NONE for sustained state")
	for reason in [Policy.TransitionReason.STIMULUS_ACQUIRED, Policy.TransitionReason.THREAT_ESCALATED, Policy.TransitionReason.CONCEALMENT_SELECTED, Policy.TransitionReason.CONCEALMENT_LOST, Policy.TransitionReason.ESCAPE_SELECTED, Policy.TransitionReason.ESCAPE_UNAVAILABLE, Policy.TransitionReason.THREAT_DECAYED, Policy.TransitionReason.RECOVERY_COMPLETE]:
		policy.state = Policy.State.ORIENT
		policy.state_entered_this_step = true
		policy.last_transition_reason = reason
		var edge = policy._player_cue_authorization()
		_expect(edge["explicit_none_classes"].has("TRACE"), "TRACE must be explicit NONE for every F13 transition")
		_expect(not edge["edge_classes"].has("TRACE"), "TRACE must never be F13 edge-authorized")
	_expect(Policy.SUSTAINED_CUE_AUTH_BY_STATE[Policy.State.EVADE].has("BEHAVIOR_AUDIO") == false, "EVADE must not authorize sustained BEHAVIOR_AUDIO beacon")
	_expect(Policy.EDGE_CUE_AUTH_BY_REASON[Policy.TransitionReason.ESCAPE_SELECTED].has("BEHAVIOR_AUDIO"), "EVADE entry may authorize edge BEHAVIOR_AUDIO")

func _test_recovery_is_not_reacquisition_proof() -> void:
	var policy = Policy.new()
	var evade := _sample({"player_distance_m":3.0,"line_of_sight":true,"visual_exposure":1.0,"player_motion":1.0,"observation_pressure":0.95,"escape_available":true,"escape_affordance_id":"escape-r2"})
	_advance(policy, evade, 0.8)
	var calm := _sample()
	var saw_recover := false
	for i in range(20):
		var decision = policy.step(0.1, calm)
		if decision["state_name"] == "RECOVER":
			saw_recover = true
			_expect(decision["reacquisition_phase"], "RECOVER must expose reacquisition phase")
			_expect(not decision["reacquisition_proven"], "RECOVER must never claim reacquisition is proven")
	_expect(saw_recover, "fixture must execute RECOVER to test reacquisition boundary")
