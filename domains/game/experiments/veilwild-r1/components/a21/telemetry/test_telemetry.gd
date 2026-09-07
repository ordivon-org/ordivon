extends SceneTree

const Recorder := preload("res://veilwild_telemetry_recorder.gd")
const BASELINE := "8ebc23144ed5b49d685cc32ac11428bbddf64d2f"
const OUTPUT := "user://veilwild_a21_fixture_events.jsonl"

func _initialize() -> void:
	var recorder := Recorder.new()
	var begin_result := recorder.begin_run({
		"runId": "a21-fixture-run-001",
		"sourceRevision": BASELINE,
		"buildId": "a21-fixture-build-001",
		"conditionId": "a21-fixture-condition-headless",
		"accessibilityConditionId": "a21-fixture-access-default",
	}, OUTPUT)
	if not _require(begin_result.get("ok", false), "begin_run_failed:" + str(begin_result)):
		return

	var fixture_events := [
		["session_started", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_SESSION_START", "sessionPhaseId": "ORIENT"}],
		["session_phase_changed", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_PHASE_SEARCH", "sessionPhaseId": "SEARCH", "reasonId": "fixture_orient_complete"}],
		["cue_exposed", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_TRACE_CUE", "sessionPhaseId": "SEARCH", "cueClass": "TRACE", "worldPositionMeters": [1.0, 0.0, 2.0], "playerDistanceMeters": 4.5}],
		["creature_state_changed", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_EVADE", "sessionPhaseId": "APPROACH_OR_REACQUIRE", "reasonId": "fixture_threat_boundary"}],
		["evade_started", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_EVADE_STARTED", "sessionPhaseId": "APPROACH_OR_REACQUIRE", "entityId": "veilrunner-fixture"}],
		["reacquisition_opportunity", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_REACQUIRE", "sessionPhaseId": "APPROACH_OR_REACQUIRE", "worldPositionMeters": [3.0, 0.0, -2.0]}],
		["observe_action_started", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_OBSERVE", "sessionPhaseId": "OBSERVE_OR_REACQUIRE"}],
		["observation_committed", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_OBSERVATION_COMMITTED", "sessionPhaseId": "SUCCESS_OR_REACQUIRE", "playerDistanceMeters": 2.2}],
		["success_consequence", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_SUCCESS", "sessionPhaseId": "SUCCESS_OR_REACQUIRE"}],
		["session_ended", {"sourceFront": "A21/F22", "producerSemanticId": "FIXTURE_SESSION_END", "sessionPhaseId": "OPTIONAL_REPLAY_OR_END", "reasonId": "fixture_complete"}],
	]
	for row in fixture_events:
		var event_result := recorder.record_event(row[0], row[1])
		if not _require(event_result.get("ok", false), "record_event_failed:" + str(event_result)):
			return

	var rejected_identifier := recorder.record_event("cue_exposed", {
		"sourceFront": "A21/F22",
		"producerSemanticId": "FIXTURE_FORBIDDEN_IDENTIFIER",
		"producerData": {"email": "should-not-be-recorded@example.invalid"},
	})
	if not _require(not rejected_identifier.get("ok", true) and rejected_identifier.get("error", "") == "direct_participant_identifier_forbidden", "identifier_guard_failed:" + str(rejected_identifier)):
		return

	var finish_result := recorder.finalize_run("mechanical_fixture_complete")
	if not _require(finish_result.get("ok", false), "finalize_failed:" + str(finish_result)):
		return
	if not _require(finish_result.get("eventCount", -1) == fixture_events.size(), "unexpected_event_count"):
		return

	var raw_text := FileAccess.get_file_as_string(OUTPUT)
	var lines := raw_text.split("\n", false)
	if not _require(lines.size() == fixture_events.size(), "line_count_mismatch"):
		return
	var previous_time := -1
	for index in range(lines.size()):
		var event = JSON.parse_string(lines[index])
		if not _require(typeof(event) == TYPE_DICTIONARY, "event_not_dictionary"):
			return
		var expected_sequence := index + 1
		if not _require(event["sequence"] == expected_sequence, "sequence_gap"):
			return
		if not _require(event["eventId"] == "a21-fixture-run-001:" + str(expected_sequence), "event_id_mismatch"):
			return
		if not _require(event["sourceRevision"] == BASELINE, "source_revision_drift"):
			return
		if not _require(event["buildId"] == "a21-fixture-build-001", "build_id_drift"):
			return
		if not _require(event["conditionId"] == "a21-fixture-condition-headless", "condition_drift"):
			return
		if not _require(event["monotonicTimeMs"] >= previous_time, "time_regression"):
			return
		previous_time = event["monotonicTimeMs"]

	var manifest = JSON.parse_string(FileAccess.get_file_as_string(finish_result["manifestPath"]))
	if not _require(typeof(manifest) == TYPE_DICTIONARY, "manifest_not_dictionary"):
		return
	if not _require(manifest["eventFileSha256"] == FileAccess.get_sha256(OUTPUT), "manifest_digest_mismatch"):
		return
	if not _require(manifest["eventCount"] == fixture_events.size(), "manifest_count_mismatch"):
		return

	print("VEILWILD_A21_TELEMETRY_FIXTURE_PASS events=" + str(fixture_events.size()))
	print("A21_TELEMETRY_OUTPUT=" + ProjectSettings.globalize_path(OUTPUT))
	print("A21_TELEMETRY_SHA256=" + str(finish_result["eventSha256"]))
	print("A21_MANIFEST_OUTPUT=" + ProjectSettings.globalize_path(finish_result["manifestPath"]))
	print("A21_MANIFEST_SHA256=" + str(finish_result["manifestSha256"]))
	quit(0)

func _require(condition: bool, message: String) -> bool:
	if condition:
		return true
	push_error("VEILWILD_A21_TELEMETRY_FIXTURE_FAIL " + message)
	quit(1)
	return false
