class_name VeilwildBehaviorPolicy
extends RefCounted

enum State {
	UNAWARE,
	ORIENT,
	FREEZE,
	CONCEAL,
	EVADE,
	RECOVER,
}

enum TransitionReason {
	NONE,
	STIMULUS_ACQUIRED,
	THREAT_ESCALATED,
	CONCEALMENT_SELECTED,
	CONCEALMENT_LOST,
	ESCAPE_SELECTED,
	ESCAPE_UNAVAILABLE,
	THREAT_DECAYED,
	RECOVERY_COMPLETE,
}

const STATE_NAMES := {
	State.UNAWARE: "UNAWARE",
	State.ORIENT: "ORIENT",
	State.FREEZE: "FREEZE",
	State.CONCEAL: "CONCEAL",
	State.EVADE: "EVADE",
	State.RECOVER: "RECOVER",
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

# These are fixture defaults, not Human-balanced product values. Consumers may inject
# exact product-tuned values once A01/A02/A03 interfaces are frozen.
var config := {
	"near_distance_m": 2.0,
	"far_distance_m": 18.0,
	"awareness_rise_per_s": 1.6,
	"awareness_fall_per_s": 0.8,
	"orient_threshold": 0.24,
	"freeze_threshold": 0.43,
	"evade_threshold": 0.72,
	"recover_threshold": 0.18,
	"min_orient_s": 0.20,
	"min_freeze_s": 0.25,
	"min_conceal_s": 0.35,
	"min_evade_s": 0.45,
	"min_recover_s": 0.40,
}

var state: int = State.UNAWARE
var state_age_s: float = 0.0
var awareness: float = 0.0
var threat: float = 0.0
var last_transition_reason: int = TransitionReason.NONE

func reset() -> void:
	state = State.UNAWARE
	state_age_s = 0.0
	awareness = 0.0
	threat = 0.0
	last_transition_reason = TransitionReason.NONE

func step(delta_s: float, perception: Dictionary) -> Dictionary:
	assert(delta_s >= 0.0, "delta_s must be non-negative")
	_validate_input(perception)
	state_age_s += delta_s

	var distance_factor := _distance_factor(float(perception["player_distance_m"]))
	var line_of_sight := bool(perception["line_of_sight"])
	var visual_signal := clampf(float(perception["visual_exposure"]), 0.0, 1.0) if line_of_sight else 0.0
	var motion_signal := clampf(float(perception["player_motion"]), 0.0, 1.0) if line_of_sight else 0.0
	var observation_pressure := clampf(float(perception["observation_pressure"]), 0.0, 1.0)
	var nonvisual_stimulus := clampf(float(perception.get("nonvisual_stimulus", 0.0)), 0.0, 1.0)

	var visual_awareness := distance_factor * (0.65 * visual_signal + 0.35 * motion_signal)
	var awareness_target: float = clampf(maxf(nonvisual_stimulus, maxf(observation_pressure * 0.90, visual_awareness)), 0.0, 1.0)
	var awareness_rate := float(config["awareness_rise_per_s"]) if awareness_target > awareness else float(config["awareness_fall_per_s"])
	awareness = move_toward(awareness, awareness_target, awareness_rate * delta_s)
	threat = clampf(maxf(observation_pressure, awareness * (0.55 + 0.45 * distance_factor)), 0.0, 1.0)

	var concealment_available := bool(perception["concealment_available"])
	var escape_available := bool(perception["escape_available"])
	_update_state(concealment_available, escape_available)

	return _decision()

func _validate_input(perception: Dictionary) -> void:
	for key in [
		"player_distance_m",
		"line_of_sight",
		"visual_exposure",
		"player_motion",
		"observation_pressure",
		"concealment_available",
		"concealment_quality",
		"escape_available",
	]:
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
			if awareness >= orient_threshold:
				_transition(State.ORIENT, TransitionReason.STIMULUS_ACQUIRED)
		State.ORIENT:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_orient_s"]):
				_transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif threat >= freeze_threshold and state_age_s >= float(config["min_orient_s"]):
				if concealment_available:
					_transition(State.CONCEAL, TransitionReason.CONCEALMENT_SELECTED)
				else:
					_transition(State.FREEZE, TransitionReason.THREAT_ESCALATED)
			elif awareness < recover_threshold and state_age_s >= float(config["min_orient_s"]):
				_transition(State.UNAWARE, TransitionReason.THREAT_DECAYED)
		State.FREEZE:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_freeze_s"]):
				_transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif concealment_available and threat >= freeze_threshold and state_age_s >= float(config["min_freeze_s"]):
				_transition(State.CONCEAL, TransitionReason.CONCEALMENT_SELECTED)
			elif threat < recover_threshold and state_age_s >= float(config["min_freeze_s"]):
				_transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.CONCEAL:
			if threat >= evade_threshold and escape_available and state_age_s >= float(config["min_conceal_s"]):
				_transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif not concealment_available and state_age_s >= float(config["min_conceal_s"]):
				_transition(State.FREEZE, TransitionReason.CONCEALMENT_LOST)
			elif threat < recover_threshold and state_age_s >= float(config["min_conceal_s"]):
				_transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.EVADE:
			if threat < recover_threshold and state_age_s >= float(config["min_evade_s"]):
				_transition(State.RECOVER, TransitionReason.THREAT_DECAYED)
		State.RECOVER:
			if threat >= evade_threshold and escape_available:
				_transition(State.EVADE, TransitionReason.ESCAPE_SELECTED)
			elif threat >= freeze_threshold:
				if concealment_available:
					_transition(State.CONCEAL, TransitionReason.CONCEALMENT_SELECTED)
				else:
					_transition(State.FREEZE, TransitionReason.THREAT_ESCALATED)
			elif awareness < recover_threshold and state_age_s >= float(config["min_recover_s"]):
				_transition(State.UNAWARE, TransitionReason.RECOVERY_COMPLETE)

	# High threat without an escape path must never emit EVADE. The fallback is
	# concealment if available, otherwise freezing in place while downstream F14
	# remains authoritative for traversal/path feasibility.
	if threat >= evade_threshold and not escape_available and state != State.EVADE:
		if state_age_s >= 0.20:
			if concealment_available and state != State.CONCEAL:
				_transition(State.CONCEAL, TransitionReason.ESCAPE_UNAVAILABLE)
			elif not concealment_available and state != State.FREEZE:
				_transition(State.FREEZE, TransitionReason.ESCAPE_UNAVAILABLE)

func _transition(next_state: int, reason: int) -> void:
	if next_state == state:
		return
	state = next_state
	state_age_s = 0.0
	last_transition_reason = reason

func _decision() -> Dictionary:
	var nav_action := "NONE"
	var orientation_intent := "NONE"
	var camouflage_drive := 0.0
	match state:
		State.ORIENT:
			nav_action = "FACE_THREAT"
			orientation_intent = "TRACK_THREAT"
			camouflage_drive = 0.10
		State.FREEZE:
			nav_action = "HOLD_POSITION"
			orientation_intent = "HOLD_ORIENTATION"
			camouflage_drive = 0.55
		State.CONCEAL:
			nav_action = "SEEK_OR_MAINTAIN_CONCEALMENT"
			orientation_intent = "MINIMIZE_EXPOSURE"
			camouflage_drive = 1.0
		State.EVADE:
			nav_action = "EVADE_FROM_THREAT"
			orientation_intent = "ESCAPE"
			camouflage_drive = 0.20
		State.RECOVER:
			nav_action = "HOLD_OR_SLOW_REPOSITION"
			orientation_intent = "REASSESS"
			camouflage_drive = 0.25

	return {
		"state": state,
		"state_name": STATE_NAMES[state],
		"state_age_s": state_age_s,
		"transition_reason": last_transition_reason,
		"transition_reason_name": REASON_NAMES[last_transition_reason],
		"awareness": awareness,
		"threat": threat,
		"nav_intent": {
			"action": nav_action,
			"target_semantics": _target_semantics(nav_action),
		},
		"orientation_intent": orientation_intent,
		"camouflage_drive": camouflage_drive,
	}

func _target_semantics(nav_action: String) -> String:
	match nav_action:
		"FACE_THREAT":
			return "face perceived threat source; no path authority implied"
		"SEEK_OR_MAINTAIN_CONCEALMENT":
			return "consume F14-selected concealment affordance; F13 does not choose path geometry"
		"EVADE_FROM_THREAT":
			return "request F14 traversal away from perceived threat toward a valid escape affordance"
		"HOLD_POSITION":
			return "suppress locomotion while evaluating threat"
		"HOLD_OR_SLOW_REPOSITION":
			return "recovery intent only; F14 decides any legal reposition path"
		_:
			return "no navigation request"
