extends SceneTree

const Recorder := preload("res://veilwild_telemetry_recorder.gd")
const PUBLICATION_PROTOCOL := "veilwild.manifest-last-publication.r1"

func _initialize() -> void:
	var invocation_id := OS.get_environment("VEILWILD_FIXTURE_RUN_ID")
	if not _require(_valid_invocation_id(invocation_id), "VEILWILD_FIXTURE_RUN_ID_required_and_must_match_[A-Za-z0-9._-]+"):
		return
	var source_revision := OS.get_environment("VEILWILD_SOURCE_REVISION")
	if not _require(not source_revision.is_empty(), "VEILWILD_SOURCE_REVISION_required"):
		return
	var run_id := "a21-fixture-" + invocation_id
	var output := "user://veilwild_a21_fixture_" + invocation_id + ".jsonl"
	var manifest_path := output.get_basename() + ".manifest.json"
	var claim_path := output + ".claim"
	var recorder := Recorder.new()
	var begin_result := recorder.begin_run({
		"runId": run_id,
		"sourceRevision": source_revision,
		"buildId": "a21-fixture-build-001",
		"conditionId": "a21-fixture-condition-headless",
		"accessibilityConditionId": "a21-fixture-access-default",
	}, output)
	if not _require(begin_result.get("ok", false), "begin_run_failed:" + str(begin_result)):
		return
	if not _require(begin_result.get("publicationState", "") == "STAGING", "begin_publication_state_not_staging"):
		return
	if not _require(not FileAccess.file_exists(output), "final_raw_visible_before_finalize"):
		return
	if not _require(not FileAccess.file_exists(manifest_path), "final_manifest_visible_before_finalize"):
		return
	if not _require(DirAccess.dir_exists_absolute(claim_path), "claim_not_materialized"):
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
	if not _require(not FileAccess.file_exists(output), "final_raw_visible_during_run"):
		return
	if not _require(not FileAccess.file_exists(manifest_path), "final_manifest_visible_during_run"):
		return

	var finish_result := recorder.finalize_run("mechanical_fixture_complete")
	if not _require(finish_result.get("ok", false), "finalize_failed:" + str(finish_result)):
		return
	if not _require(finish_result.get("eventCount", -1) == fixture_events.size(), "unexpected_event_count"):
		return
	if not _require(finish_result.get("publicationState", "") == "FINALIZED", "final_publication_state_not_finalized"):
		return
	if not _require(finish_result.get("publicationProtocol", "") == PUBLICATION_PROTOCOL, "publication_protocol_mismatch"):
		return
	if not _require(FileAccess.file_exists(output) and FileAccess.file_exists(manifest_path), "final_pair_missing"):
		return
	if not _require(not DirAccess.dir_exists_absolute(claim_path), "claim_not_cleaned_after_finalize"):
		return

	var raw_text := FileAccess.get_file_as_string(output)
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
		if not _require(event["eventId"] == run_id + ":" + str(expected_sequence), "event_id_mismatch"):
			return
		if not _require(event["sourceRevision"] == source_revision, "source_revision_drift"):
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
	if not _require(manifest["publicationProtocol"] == PUBLICATION_PROTOCOL, "manifest_publication_protocol_mismatch"):
		return
	if not _require(manifest["publicationState"] == "FINALIZED", "manifest_not_finalized"):
		return
	if not _require(manifest["eventFile"] == output, "manifest_final_event_path_mismatch"):
		return
	if not _require(manifest["eventFileSha256"] == FileAccess.get_sha256(output), "manifest_digest_mismatch"):
		return
	if not _require(manifest["eventCount"] == fixture_events.size(), "manifest_count_mismatch"):
		return

	var collision_recorder := Recorder.new()
	var collision_result := collision_recorder.begin_run({
		"runId": run_id,
		"sourceRevision": source_revision,
		"buildId": "a21-fixture-build-001",
		"conditionId": "a21-fixture-condition-headless",
		"accessibilityConditionId": "a21-fixture-access-default",
	}, output)
	if not _require(not collision_result.get("ok", true) and str(collision_result.get("error", "")).begins_with("output_path_already_exists:"), "collision_guard_failed:" + str(collision_result)):
		return

	print("VEILWILD_A21_TELEMETRY_FIXTURE_PASS events=" + str(fixture_events.size()) + " collision_guard=PASS publication=MANIFEST_LAST")
	print("A21_TELEMETRY_OUTPUT=" + ProjectSettings.globalize_path(output))
	print("A21_TELEMETRY_SHA256=" + str(finish_result["eventSha256"]))
	print("A21_MANIFEST_OUTPUT=" + ProjectSettings.globalize_path(finish_result["manifestPath"]))
	print("A21_MANIFEST_SHA256=" + str(finish_result["manifestSha256"]))
	quit(0)

func _valid_invocation_id(value: String) -> bool:
	if value.is_empty():
		return false
	var regex := RegEx.new()
	if regex.compile("^[A-Za-z0-9._-]+$") != OK:
		return false
	return regex.search(value) != null

func _require(condition: bool, message: String) -> bool:
	if condition:
		return true
	push_error("VEILWILD_A21_TELEMETRY_FIXTURE_FAIL " + message)
	quit(1)
	return false
