extends Node
## A17 engine adapter over the exact A13/F13 behavior policy runtime copy.
## This adapter supplies no perception values and changes no F13 state semantics.

const Policy = preload("res://vendor/f13/creature_behavior_policy.gd")

signal decision_available(decision: Dictionary)

var _policy: RefCounted

func _ready() -> void:
    _policy = Policy.new()

func reset_policy() -> void:
    if _policy == null:
        _policy = Policy.new()
    else:
        _policy.reset()

func step_policy(delta_s: float, perception: Dictionary) -> Dictionary:
    if _policy == null:
        _policy = Policy.new()
    var decision: Dictionary = _policy.step(delta_s, perception)
    decision_available.emit(decision)
    return decision
