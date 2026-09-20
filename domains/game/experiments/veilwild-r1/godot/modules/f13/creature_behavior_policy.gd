class_name VeilwildBehaviorPolicy
extends RefCounted

## F13-owned deterministic creature behavior policy.
## Consumes bounded observations; owns behavior-state decision and semantic intents.
## It does not own cover/path geometry, animation, shader, audio, engine composition,
## observation-success adjudication, or telemetry transport.

enum State { UNAWARE, ORIENT, FREEZE, CONCEAL, EVADE, RECOVER }
enum TransitionReason { NONE, STIMULUS_ACQUIRED, THREAT_ESCALATED, CONCEALMENT_SELECTED, CONCEALMENT_LOST, ESCAPE_SELECTED, ESCAPE_UNAVAILABLE, THREAT_DECAYED, RECOVERY_COMPLETE }

const STATE_NAMES := {
	State.UNAWARE: "UNAWARE", State.ORIENT: "ORIENT", State.FREEZE: "FREEZE",
	State.CONCEAL: "CONCEAL", State.EVADE: "EVADE", State.RECOVER: "RECOVER",
}
const STATE_IDS := {
	State.UNAWARE: "veilwild.behavior.unaware.r1",
	State.ORIENT: "veilwild.behavior.orient.r1",
	State.FREEZE: "veilwild.behavior.freeze.r1",
	State.CONCEAL: "veilwild.behavior.conceal.r1",
	State.EVADE: "veilwild.behavior.evade.r1",
	State.RECOVER: "veilwild.behavior.recover.r1",
}
# A01 product intents are source-bound semantics, not mandatory engine enums.
# OBSERVATION_SUCCESS is absent by design: F13 never awards product success.
const PRODUCT_INTENTS := {
	State.UNAWARE: "UNTHREATENED", State.ORIENT: "ALERT_ORIENT",
	State.FREEZE: "ALERT_ORIENT", State.CONCEAL: "CONCEAL",
	State.EVADE: "EVADE", State.RECOVER: "ALERT_ORIENT",
}
const REASON_NAMES := {
	TransitionReason.NONE: "NONE",
	TransitionReason.STIMULUS_ACQUIRED: "STIMULUS_ACQUIRED",
	TransitionReason.THREAT_ESCALATED: "THREAT_ESCALATED",
	TransitionReason.CONCEALMENT_SELECTED: "CONCEALMENT_SELECTED",
	TransitionReason.CONCEALMENT_LOST: "CONCEALMENT_LOST",
	TransitionReason.ESCAPE_SELECTED: "ESCAPE_SELECTED",
	TransitionReason.ESCAPE_UNAVAILABLE: "ESCAPE_UNAVAILABLE",
	TransitionReason.THREAT_DECAYED: "THREAT_DECAYED",
	TransitionReason.RECOVERY_COMPLETE: "RECOVERY_COMPLETE",
}
const REASON_IDS := {
	TransitionReason.NONE: "veilwild.behavior.transition.none.r1",
	TransitionReason.STIMULUS_ACQUIRED: "veilwild.behavior.transition.stimulus_acquired.r1",
	TransitionReason.THREAT_ESCALATED: "veilwild.behavior.transition.threat_escalated.r1",
	TransitionReason.CONCEALMENT_SELECTED: "veilwild.behavior.transition.concealment_selected.r1",
	TransitionReason.CONCEALMENT_LOST: "veilwild.behavior.transition.concealment_lost.r1",
	TransitionReason.ESCAPE_SELECTED: "veilwild.behavior.transition.escape_selected.r1",
	TransitionReason.ESCAPE_UNAVAILABLE: "veilwild.behavior.transition.escape_unavailable.r1",
	TransitionReason.THREAT_DECAYED: "veilwild.behavior.transition.threat_decayed.r1",
	TransitionReason.RECOVERY_COMPLETE: "veilwild.behavior.transition.recovery_complete.r1",
}

# F13 owns cue-class authorization semantics only. It does not choose concrete
# carrier assets, filenames, playback/stop policy, attenuation, priority, UI text,
# animation clips, or accessibility presentation. "SUSTAINED" means a cue class
# remains semantically eligible while the state persists; it never means a carrier
# must emit continuously. TRACE is intentionally never F13-authorized.
const PLAYER_CUE_CLASSES := ["TRACE", "BEHAVIOR_AUDIO", "MOTION_COUNTERCUE", "CAMOUFLAGE_MISMATCH", "THREAT_RESPONSE"]
const SUSTAINED_CUE_AUTH_BY_STATE := {
	State.UNAWARE: ["BEHAVIOR_AUDIO"],
	State.ORIENT: ["THREAT_RESPONSE", "MOTION_COUNTERCUE"],
	State.FREEZE: ["THREAT_RESPONSE"],
	State.CONCEAL: ["CAMOUFLAGE_MISMATCH", "MOTION_COUNTERCUE"],
	State.EVADE: ["THREAT_RESPONSE", "MOTION_COUNTERCUE"],
	State.RECOVER: ["THREAT_RESPONSE", "MOTION_COUNTERCUE"],
}
const EDGE_CUE_AUTH_BY_REASON := {
	TransitionReason.NONE: [],
	TransitionReason.STIMULUS_ACQUIRED: ["THREAT_RESPONSE", "BEHAVIOR_AUDIO", "MOTION_COUNTERCUE"],
	TransitionReason.THREAT_ESCALATED: ["THREAT_RESPONSE", "MOTION_COUNTERCUE"],
	TransitionReason.CONCEALMENT_SELECTED: ["MOTION_COUNTERCUE"],
	TransitionReason.CONCEALMENT_LOST: ["THREAT_RESPONSE", "CAMOUFLAGE_MISMATCH", "MOTION_COUNTERCUE"],
	TransitionReason.ESCAPE_SELECTED: ["THREAT_RESPONSE", "BEHAVIOR_AUDIO", "MOTION_COUNTERCUE"],
	TransitionReason.ESCAPE_UNAVAILABLE: ["THREAT_RESPONSE"],
	TransitionReason.THREAT_DECAYED: ["THREAT_RESPONSE", "MOTION_COUNTERCUE"],
	TransitionReason.RECOVERY_COMPLETE: ["MOTION_COUNTERCUE"],
}

# Game-authored fixture defaults only. Not biological effect sizes, real-species
# flight-initiation distances, or Human-balanced thresholds.
var config := {
	"near_distance_m": 2.0, "far_distance_m": 18.0,
	"awareness_rise_per_s": 1.6, "awareness_fall_per_s": 0.8,
	"orient_threshold": 0.24, "freeze_threshold": 0.43,
	"evade_threshold": 0.72, "recover_threshold": 0.18,
	"min_orient_s": 0.20, "min_freeze_s": 0.25,
	"min_conceal_s": 0.35, "min_evade_s": 0.45, "min_recover_s": 0.40,
}

var state: int = State.UNAWARE
var state_age_s: float = 0.0
var awareness: float = 0.0
var threat: float = 0.0
var last_transition_reason: int = TransitionReason.NONE
var last_transition_from_state: int = State.UNAWARE
var transition_sequence: int = 0
var state_entered_this_step: bool = false

func reset() -> void:
	state = State.UNAWARE
	state_age_s = 0.0
	awareness = 0.0
	threat = 0.0
	last_transition_reason = TransitionReason.NONE
	last_transition_from_state = State.UNAWARE
	transition_sequence = 0
	state_entered_this_step = false

func step(delta_s: float, perception: Dictionary) -> Dictionary:
	assert(delta_s >= 0.0, "delta_s must be non-negative")
	_validate_input(perception)
	state_entered_this_step = false
	state_age_s += delta_s
	var distance_factor := _distance_factor(float(perception["player_distance_m"]))
	var line_of_sight := bool(perception["line_of_sight"])
	var visual_signal := clampf(float(perception["visual_exposure"]), 0.0, 1.0) if line_of_sight else 0.0
	var motion_signal := clampf(float(perception["player_motion"]), 0.0, 1.0) if line_of_sight else 0.0
	var observation_pressure := clampf(float(perception["observation_pressure"]), 0.0, 1.0)
	var nonvisual_stimulus := clampf(float(perception.get("nonvisual_stimulus", 0.0)), 0.0, 1.0)
	var visual_awareness := distance_factor * (0.65 * visual_signal + 0.35 * motion_signal)
	var awareness_target := clampf(maxf(nonvisual_stimulus, maxf(observation_pressure * 0.90, visual_awareness)), 0.0, 1.0)
	var awareness_rate := float(config["awareness_rise_per_s"]) if awareness_target > awareness else float(config["awareness_fall_per_s"])
	awareness = move_toward(awareness, awareness_target, awareness_rate * delta_s)
	threat = clampf(maxf(observation_pressure, awareness * (0.55 + 0.45 * distance_factor)), 0.0, 1.0)
	_update_state(bool(perception["concealment_available"]), bool(perception["escape_available"]))
	return _decision(perception)

func _validate_input(perception: Dictionary) -> void:
	for key in ["player_distance_m", "line_of_sight", "visual_exposure", "player_motion", "observation_pressure", "concealment_available", "concealment_quality", "escape_available"]:
		assert(perception.has(key), "missing perception field: %s" % key)
	assert(float(perception["player_distance_m"]) >= 0.0, "player_distance_m must be non-negative")

func _distance_factor(distance_m: float) -> float:
	var near_m := float(config["near_distance_m"])
	var far_m := float(config["far_distance_m"])
	assert(far_m > near_m, "far_distance_m must exceed near_distance_m")
	return clampf((far_m - distance_m) / (far_m - near_m), 0.0, 1.0)

func _update_state(concealment_available: bool, escape_available: bool) -> void:
	var orient_threshold := float(config["orient_threshold"])
	var freeze_threshold := float(config["freeze_threshold"])
	var evade_threshold := float(config["evade_threshold"])
	var recover_threshold := float(config["recover_threshold"])
	match state:
		State.UNAWARE:
			if awareness >= orient_threshold: _transition(State.ORIENT, TransitionReason.STIMULUS_ACQUIRED)
		State.ORIENT:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_orient_s"]): _transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif threat >= freeze_threshold and state_age_s >= float(config["min_orient_s"]): _transition(State.CONCEAL if concealment_available else State.FREEZE, TransitionReason.CONCEALMENT_SELECTED if concealment_available else TransitionReason.THREAT_ESCALATED)
			elif awareness < recover_threshold and state_age_s >= float(config["min_orient_s"]): _transition(State.UNAWARE, TransitionReason.THREAT_DECAYED)
		State.FREEZE:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_freeze_s"]): _transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif concealment_available and threat >= freeze_threshold and state_age_s >= float(config["min_freeze_s"]): _transition(State.CONCEAL, TransitionReason.CONCEALMENT_SELECTED)
			elif threat < recover_threshold and state_age_s >= float(config["min_freeze_s"]): _transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.CONCEAL:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_conceal_s"]): _transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif not concealment_available and state_age_s >= float(config["min_conceal_s"]): _transition(State.FREEZE, TransitionReason.CONCEALMENT_LOST)
			elif threat < recover_threshold and state_age_s >= float(config["min_conceal_s"]): _transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.EVADE:
			if threat < recover_threshold and state_age_s >= float(config["min_evade_s"]): _transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.RECOVER:
			if threat >= evade_threshold and escape_available: _transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif threat >= freeze_threshold: _transition(State.CONCEAL if concealment_available else State.FREEZE, TransitionReason.CONCEALMENT_SELECTED if concealment_available else TransitionReason.THREAT_ESCALATED)
			elif awareness < recover_threshold and state_age_s >= float(config["min_recover_s"]): _transition(State.UNAWARE, TransitionReason.RECOVERY_COMPLETE)

	# F03-R4 + A01 recovery guard: never manufacture EVADE without downstream
	# traversal availability. EVADE is an observation abort boundary, not session fail.
	if threat >= evade_threshold and not escape_available and state != State.EVADE and state_age_s >= 0.20:
		if concealment_available and state != State.CONCEAL: _transition(State.CONCEAL, TransitionReason.ESCAPE_UNAVAILABLE)
		elif not concealment_available and state != State.FREEZE: _transition(State.FREEZE, TransitionReason.ESCAPE_UNAVAILABLE)

func _transition(next_state: int, reason: int) -> void:
	if next_state == state: return
	last_transition_from_state = state
	state = next_state
	state_age_s = 0.0
	last_transition_reason = reason
	transition_sequence += 1
	state_entered_this_step = true

func _decision(perception: Dictionary) -> Dictionary:
	var nav_action := "NONE"
	var nav_intent_id := "veilwild.nav.none.r1"
	var orientation_intent := "NONE"
	var camouflage_drive := 0.0
	var speed_mode := "NONE"
	var failure_fallback := "NONE"
	var target_affordance_id := ""
	match state:
		State.ORIENT:
			nav_action = "FACE_THREAT"; nav_intent_id = "veilwild.nav.face_threat.r1"; orientation_intent = "TRACK_THREAT"; camouflage_drive = 0.10; speed_mode = "TURN_ONLY"
		State.FREEZE:
			nav_action = "HOLD_POSITION"; nav_intent_id = "veilwild.nav.hold_position.r1"; orientation_intent = "HOLD_ORIENTATION"; camouflage_drive = 0.55; speed_mode = "STOP"
		State.CONCEAL:
			nav_action = "SEEK_OR_MAINTAIN_CONCEALMENT"; nav_intent_id = "veilwild.nav.concealment_request.r1"; orientation_intent = "MINIMIZE_EXPOSURE"; camouflage_drive = 1.0; speed_mode = "CAUTIOUS"; failure_fallback = "FREEZE_IF_AFFORDANCE_INVALID"; target_affordance_id = String(perception.get("concealment_affordance_id", ""))
		State.EVADE:
			nav_action = "EVADE_FROM_THREAT"; nav_intent_id = "veilwild.nav.evade_request.r1"; orientation_intent = "ESCAPE"; camouflage_drive = 0.20; speed_mode = "FAST"; failure_fallback = "CONCEAL_IF_AVAILABLE_ELSE_FREEZE"; target_affordance_id = String(perception.get("escape_affordance_id", ""))
		State.RECOVER:
			nav_action = "HOLD_OR_SLOW_REPOSITION"; nav_intent_id = "veilwild.nav.recover_request.r1"; orientation_intent = "REASSESS"; camouflage_drive = 0.25; speed_mode = "SLOW"
	return {
		"behavior_state_id": STATE_IDS[state], "state": state, "state_name": STATE_NAMES[state],
		"product_intent": PRODUCT_INTENTS[state], "state_age_s": state_age_s,
		"state_entered": state_entered_this_step, "previous_behavior_state_id": STATE_IDS[last_transition_from_state],
		"transition_sequence": transition_sequence, "transition_reason": last_transition_reason,
		"transition_reason_name": REASON_NAMES[last_transition_reason], "transition_semantic_id": REASON_IDS[last_transition_reason],
		"awareness": awareness, "threat": threat, "threat_units": "normalized_game_authored_0_to_1",
		"observation_abort": state == State.EVADE, "reacquisition_phase": state == State.RECOVER,
		"reacquisition_proven": false,
		"player_cue_authorization": _player_cue_authorization(),
		"cue_opportunities": _cue_opportunities(state),
		"nav_intent": {"intent_id": nav_intent_id, "action": nav_action, "target_affordance_id": target_affordance_id, "target_semantics": _target_semantics(nav_action), "urgency": threat, "speed_mode": speed_mode, "failure_fallback": failure_fallback},
		"orientation_intent": orientation_intent, "camouflage_drive": camouflage_drive,
		"concealment_suitability": clampf(float(perception["concealment_quality"]), 0.0, 1.0),
	}

func _player_cue_authorization() -> Dictionary:
	var sustained: Array = SUSTAINED_CUE_AUTH_BY_STATE[state]
	var edge: Array = EDGE_CUE_AUTH_BY_REASON[last_transition_reason] if state_entered_this_step else []
	var allowed: Array[String] = []
	for cue_class in sustained:
		if not allowed.has(cue_class): allowed.append(cue_class)
	for cue_class in edge:
		if not allowed.has(cue_class): allowed.append(cue_class)
	var explicit_none: Array[String] = []
	for cue_class in PLAYER_CUE_CLASSES:
		if not allowed.has(cue_class): explicit_none.append(cue_class)
	return {
		"state_semantic_id": STATE_IDS[state],
		"transition_semantic_id": REASON_IDS[last_transition_reason] if state_entered_this_step else REASON_IDS[TransitionReason.NONE],
		"sustained_classes": sustained.duplicate(),
		"edge_classes": edge.duplicate(),
		"explicit_none_classes": explicit_none,
		"authorization_only": true,
	}

func _cue_opportunities(_current_state: int) -> Array[String]:
	# Backward-compatible union only. New consumers MUST use player_cue_authorization
	# to distinguish EDGE from SUSTAINED and explicit NONE.
	var auth := _player_cue_authorization()
	var result: Array[String] = []
	for cue_class in auth["sustained_classes"]:
		if not result.has(cue_class): result.append(cue_class)
	for cue_class in auth["edge_classes"]:
		if not result.has(cue_class): result.append(cue_class)
	return result

func _target_semantics(nav_action: String) -> String:
	match nav_action:
		"FACE_THREAT": return "face perceived threat source; no path authority implied"
		"SEEK_OR_MAINTAIN_CONCEALMENT": return "consume F14-supplied concealment affordance identity; F13 does not choose path geometry"
		"EVADE_FROM_THREAT": return "request F14 traversal toward an accepted escape affordance away from perceived threat"
		"HOLD_POSITION": return "suppress locomotion while evaluating threat"
		"HOLD_OR_SLOW_REPOSITION": return "recovery intent only; F14 decides any legal reposition path"
		_: return "no navigation request"
