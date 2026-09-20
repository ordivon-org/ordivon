extends Node
## Engine-owned transport only. Topic/payload semantics are producer-owned contracts.

signal envelope_published(topic: StringName, payload: Dictionary, source: StringName)

func publish(topic: StringName, payload: Dictionary = {}, source: StringName = &"unknown") -> void:
    envelope_published.emit(topic, payload, source)
