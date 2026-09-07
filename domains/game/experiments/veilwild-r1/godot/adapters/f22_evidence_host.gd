extends Node
## A17 lifecycle host for the exact A21/F22 telemetry recorder runtime copy.
## No producer event semantics are inferred here. Callers must provide A21-valid event types/fields.

const Recorder = preload("res://vendor/f22/veilwild_telemetry_recorder.gd")

var _recorder: RefCounted = Recorder.new()

func begin_run(context: Dictionary, output_path: String) -> Dictionary:
    return _recorder.begin_run(context, output_path)

func record_event(event_type: String, fields: Dictionary) -> Dictionary:
    return _recorder.record_event(event_type, fields)

func finalize_run(final_status: String) -> Dictionary:
    return _recorder.finalize_run(final_status)

func is_open() -> bool:
    return _recorder.is_open()
