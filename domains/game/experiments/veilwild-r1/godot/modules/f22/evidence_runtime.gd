extends Node
## A21-owned evidence transport module for the A17 EvidenceMount.
## Producer semantics remain with the producer front. Direct EventBus transport is
## admitted only when the producer already publishes an exact F22 event type and
## supplies its own sourceFront + producerSemanticId. Unknown/generic topics are
## ignored rather than reinterpreted by A21.

const Recorder := preload("res://modules/f22/veilwild_telemetry_recorder.gd")

signal evidence_run_started(receipt: Dictionary)
signal evidence_event_recorded(event: Dictionary)
signal evidence_run_finalized(receipt: Dictionary)
signal evidence_rejected(error: String)
signal event_bus_bound(receipt: Dictionary)

var _recorder := Recorder.new()
var _event_bus: Node = null

func _ready() -> void:
	var bus := get_node_or_null("/root/VeilwildEventBus")
	if bus != null:
		bind_event_bus(bus)

func bind_event_bus(bus: Node) -> Dictionary:
	if bus == null:
		return _binding_failure("event_bus_missing")
	if not bus.has_signal("envelope_published"):
		return _binding_failure("event_bus_missing_envelope_published_signal")
	var callback := Callable(self, "_on_event_bus_envelope")
	if _event_bus != null and is_instance_valid(_event_bus) and _event_bus.has_signal("envelope_published"):
		if _event_bus.is_connected("envelope_published", callback):
			_event_bus.disconnect("envelope_published", callback)
	_event_bus = bus
	if not _event_bus.is_connected("envelope_published", callback):
		var connect_error := _event_bus.connect("envelope_published", callback)
		if connect_error != OK:
			_event_bus = null
			return _binding_failure("event_bus_connect_failed:" + str(connect_error))
	var receipt := {
		"ok": true,
		"transport": "VeilwildEventBus.envelope_published",
		"policy": "EXACT_F22_EVENT_TYPES_ONLY_NO_SEMANTIC_RENAMING",
	}
	event_bus_bound.emit(receipt.duplicate(true))
	return receipt

func begin_evidence_run(context: Dictionary, output_path: String) -> Dictionary:
	var receipt: Dictionary = _recorder.begin_run(context, output_path)
	if receipt.get("ok", false):
		evidence_run_started.emit(receipt.duplicate(true))
	else:
		evidence_rejected.emit(str(receipt.get("error", "unknown_begin_error")))
	return receipt

func record_semantic_event(event_type: String, producer_fields: Dictionary) -> Dictionary:
	var receipt: Dictionary = _recorder.record_event(event_type, producer_fields)
	if receipt.get("ok", false):
		evidence_event_recorded.emit((receipt["event"] as Dictionary).duplicate(true))
	else:
		evidence_rejected.emit(str(receipt.get("error", "unknown_record_error")))
	return receipt

func finalize_evidence_run(final_status: String) -> Dictionary:
	var receipt: Dictionary = _recorder.finalize_run(final_status)
	if receipt.get("ok", false):
		evidence_run_finalized.emit(receipt.duplicate(true))
	else:
		evidence_rejected.emit(str(receipt.get("error", "unknown_finalize_error")))
	return receipt

func is_recording() -> bool:
	return _recorder.is_open()

func _on_event_bus_envelope(topic: StringName, payload: Dictionary, _source: StringName) -> void:
	if not _recorder.is_open():
		return
	var event_type := String(topic)
	if not Recorder.ALLOWED_EVENT_TYPES.has(event_type):
		return
	# The recorder itself validates sourceFront, producerSemanticId, optional field
	# shapes, direct-identifier guards, ordering, and frozen run identity.
	record_semantic_event(event_type, payload.duplicate(true))

func _binding_failure(error: String) -> Dictionary:
	var receipt := {"ok": false, "error": error}
	evidence_rejected.emit(error)
	return receipt
