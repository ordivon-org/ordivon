class_name VeilwildBehaviorRuntime
extends Node

## Mountable F13 runtime module for A17 SystemsMount.
## Perception is pushed explicitly by an integrated caller; this node never invents
## line-of-sight, affordance, player-intent, navigation or evidence truth.

signal behavior_decision(decision: Dictionary)
signal behavior_transition(event: Dictionary)

const Policy = preload("res://modules/f13/creature_behavior_policy.gd")
var policy := Policy.new()
var last_decision: Dictionary = {}

func _ready() -> void:
	add_to_group("veilwild.f13_behavior_runtime")

func reset_policy() -> void:
	policy.reset()
	last_decision = {}

func submit_perception(delta_s: float, perception: Dictionary) -> Dictionary:
	var decision := policy.step(delta_s, perception)
	last_decision = decision.duplicate(true)
	behavior_decision.emit(last_decision)
	_publish(&"creature.behavior.decision", last_decision)
	if bool(decision["state_entered"]):
		var event := {
			"behaviorStateId": decision["behavior_state_id"],
			"previousBehaviorStateId": decision["previous_behavior_state_id"],
			"productIntent": decision["product_intent"],
			"transitionSemanticId": decision["transition_semantic_id"],
			"reasonId": decision["transition_semantic_id"],
			"transitionSequence": decision["transition_sequence"],
			"threat": decision["threat"],
			"threatUnits": decision["threat_units"],
			"observationAbort": decision["observation_abort"],
			"reacquisitionPhase": decision["reacquisition_phase"],
			"reacquisitionProven": decision["reacquisition_proven"],
			"playerCueAuthorization": decision["player_cue_authorization"],
			"cueOpportunities": decision["cue_opportunities"],
		}
		behavior_transition.emit(event)
		_publish(&"creature.behavior.transition", event)
	return last_decision

func get_last_decision() -> Dictionary:
	return last_decision.duplicate(true)

func _publish(topic: StringName, payload: Dictionary) -> void:
	var bus := get_node_or_null("/root/VeilwildEventBus")
	if bus != null and bus.has_method("publish"):
		bus.call("publish", topic, payload.duplicate(true), &"F13")
