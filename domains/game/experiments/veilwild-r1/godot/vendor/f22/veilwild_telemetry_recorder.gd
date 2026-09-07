extends RefCounted
class_name VeilwildTelemetryRecorder

const EVENT_SCHEMA_VERSION := "veilwild.telemetry-event.r1"
const MANIFEST_SCHEMA_VERSION := "veilwild.telemetry-manifest.r1"
const ALLOWED_EVENT_TYPES := {
	"session_started": true,
	"session_phase_changed": true,
	"cue_exposed": true,
	"creature_state_changed": true,
	"detection_opportunity": true,
	"threat_changed": true,
	"evade_started": true,
	"reacquisition_opportunity": true,
	"observe_action_started": true,
	"observe_action_cancelled": true,
	"observation_progress": true,
	"observation_committed": true,
	"success_consequence": true,
	"audio_cue_started": true,
	"audio_cue_stopped": true,
	"session_ended": true,
}
const REQUIRED_CONTEXT_KEYS := [
	"runId",
	"sourceRevision",
	"buildId",
	"conditionId",
	"accessibilityConditionId",
]
const FORBIDDEN_IDENTIFIER_KEYS := {
	"participantName": true,
	"realName": true,
	"email": true,
	"phone": true,
	"address": true,
	"ipAddress": true,
}

var _file: FileAccess = null
var _context: Dictionary = {}
var _output_path := ""
var _manifest_path := ""
var _sequence := 0
var _last_monotonic_ms := -1

func begin_run(context: Dictionary, output_path: String) -> Dictionary:
	if _file != null:
		return _failure("run_already_open")
	for key in REQUIRED_CONTEXT_KEYS:
		if not context.has(key) or str(context[key]).is_empty():
			return _failure("missing_context:" + str(key))
	if not output_path.begins_with("user://"):
		return _failure("output_path_must_use_user_scheme")
	if _contains_forbidden_identifier(context):
		return _failure("direct_participant_identifier_forbidden")

	_context = context.duplicate(true)
	_output_path = output_path
	_manifest_path = output_path.get_basename() + ".manifest.json"
	_sequence = 0
	_last_monotonic_ms = -1
	_file = FileAccess.open(_output_path, FileAccess.WRITE)
	if _file == null:
		var open_error := FileAccess.get_open_error()
		_context = {}
		_output_path = ""
		_manifest_path = ""
		return _failure("open_failed:" + str(open_error))
	return {"ok": true, "runId": _context["runId"], "outputPath": _output_path}

func record_event(event_type: String, fields: Dictionary) -> Dictionary:
	if _file == null:
		return _failure("run_not_open")
	if not ALLOWED_EVENT_TYPES.has(event_type):
		return _failure("unknown_event_type:" + event_type)
	if not fields.has("sourceFront") or str(fields["sourceFront"]).is_empty():
		return _failure("missing_sourceFront")
	if not fields.has("producerSemanticId") or str(fields["producerSemanticId"]).is_empty():
		return _failure("missing_producerSemanticId")
	if _contains_forbidden_identifier(fields):
		return _failure("direct_participant_identifier_forbidden")
	if fields.has("worldPositionMeters") and not _valid_position(fields["worldPositionMeters"]):
		return _failure("invalid_worldPositionMeters")
	if fields.has("playerDistanceMeters"):
		var distance_value = fields["playerDistanceMeters"]
		if not _is_number(distance_value) or float(distance_value) < 0.0:
			return _failure("invalid_playerDistanceMeters")

	_sequence += 1
	var monotonic_ms := Time.get_ticks_msec()
	if monotonic_ms < _last_monotonic_ms:
		_sequence -= 1
		return _failure("monotonic_time_regressed")
	_last_monotonic_ms = monotonic_ms

	var event := {
		"schemaVersion": EVENT_SCHEMA_VERSION,
		"eventId": str(_context["runId"]) + ":" + str(_sequence),
		"eventType": event_type,
		"runId": _context["runId"],
		"sequence": _sequence,
		"monotonicTimeMs": monotonic_ms,
		"sourceRevision": _context["sourceRevision"],
		"buildId": _context["buildId"],
		"conditionId": _context["conditionId"],
		"accessibilityConditionId": _context["accessibilityConditionId"],
		"sourceFront": fields["sourceFront"],
		"producerSemanticId": fields["producerSemanticId"],
	}
	for optional_key in ["sessionPhaseId", "reasonId", "entityId", "cueClass", "worldPositionMeters", "playerDistanceMeters", "scalar", "producerData"]:
		if fields.has(optional_key):
			event[optional_key] = fields[optional_key]

	_file.store_string(JSON.stringify(event) + "\n")
	_file.flush()
	return {"ok": true, "event": event.duplicate(true)}

func finalize_run(final_status: String) -> Dictionary:
	if _file == null:
		return _failure("run_not_open")
	if final_status.is_empty():
		return _failure("missing_final_status")
	_file.flush()
	_file.close()
	_file = null

	var raw_sha256 := FileAccess.get_sha256(_output_path)
	if raw_sha256.is_empty():
		return _failure("raw_sha256_failed")
	var manifest := {
		"schemaVersion": MANIFEST_SCHEMA_VERSION,
		"runId": _context["runId"],
		"eventFile": _output_path,
		"eventFileSha256": raw_sha256,
		"eventCount": _sequence,
		"sourceRevision": _context["sourceRevision"],
		"buildId": _context["buildId"],
		"conditionId": _context["conditionId"],
		"accessibilityConditionId": _context["accessibilityConditionId"],
		"finalStatus": final_status,
	}
	var manifest_file := FileAccess.open(_manifest_path, FileAccess.WRITE)
	if manifest_file == null:
		return _failure("manifest_open_failed:" + str(FileAccess.get_open_error()))
	manifest_file.store_string(JSON.stringify(manifest, "  ") + "\n")
	manifest_file.flush()
	manifest_file.close()
	var manifest_sha256 := FileAccess.get_sha256(_manifest_path)
	var result := {
		"ok": true,
		"runId": _context["runId"],
		"eventCount": _sequence,
		"eventPath": _output_path,
		"eventSha256": raw_sha256,
		"manifestPath": _manifest_path,
		"manifestSha256": manifest_sha256,
	}
	_context = {}
	_output_path = ""
	_manifest_path = ""
	_sequence = 0
	_last_monotonic_ms = -1
	return result

func is_open() -> bool:
	return _file != null

func _failure(code: String) -> Dictionary:
	return {"ok": false, "error": code}

func _is_number(value: Variant) -> bool:
	var kind := typeof(value)
	return kind == TYPE_INT or kind == TYPE_FLOAT

func _valid_position(value: Variant) -> bool:
	if typeof(value) != TYPE_ARRAY or value.size() != 3:
		return false
	for component in value:
		if not _is_number(component):
			return false
	return true

func _contains_forbidden_identifier(value: Variant) -> bool:
	if typeof(value) == TYPE_DICTIONARY:
		for key in value.keys():
			if FORBIDDEN_IDENTIFIER_KEYS.has(str(key)):
				return true
			if _contains_forbidden_identifier(value[key]):
				return true
	elif typeof(value) == TYPE_ARRAY:
		for item in value:
			if _contains_forbidden_identifier(item):
				return true
	return false
