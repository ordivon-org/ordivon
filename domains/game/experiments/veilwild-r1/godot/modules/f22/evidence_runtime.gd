extends Node
## A21-owned evidence transport module for the A17 EvidenceMount.
## Producer semantics remain with the producer front; this node only forwards
## already-declared semantic IDs into the F22 recorder envelope.

const Recorder := preload("res://modules/f22/veilwild_telemetry_recorder.gd")

signal evidence_run_started(receipt: Dictionary)
signal evidence_event_recorded(event: Dictionary)
signal evidence_run_finalized(receipt: Dictionary)
signal evidence_rejected(error: String)

var _recorder := Recorder.new()

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
