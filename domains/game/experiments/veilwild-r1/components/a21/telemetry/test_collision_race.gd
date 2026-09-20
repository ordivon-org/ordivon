extends SceneTree

const Recorder := preload("res://veilwild_telemetry_recorder.gd")

func _initialize() -> void:
	var race_id := OS.get_environment("VEILWILD_RACE_ID")
	var source_revision := OS.get_environment("VEILWILD_SOURCE_REVISION")
	if race_id.is_empty() or source_revision.is_empty():
		push_error("VEILWILD_A21_RACE_FAIL missing env")
		quit(10)
		return
	var output := "user://veilwild_a21_race_" + race_id + ".jsonl"
	var recorder := Recorder.new()
	var begin_result := recorder.begin_run({
		"runId": "a21-race-" + race_id + "-pid-" + str(OS.get_process_id()),
		"sourceRevision": source_revision,
		"buildId": "a21-race-fixture",
		"conditionId": "a21-concurrent-output-claim",
		"accessibilityConditionId": "a21-race-default",
	}, output)
	if not begin_result.get("ok", false):
		var error := str(begin_result.get("error", ""))
		if error.begins_with("output_path_claim_failed:") or error.begins_with("output_path_already_exists:"):
			print("VEILWILD_A21_RACE_REJECT pid=" + str(OS.get_process_id()) + " error=" + error)
			quit(3)
			return
		push_error("VEILWILD_A21_RACE_FAIL unexpected_begin=" + str(begin_result))
		quit(11)
		return
	OS.delay_msec(350)
	var event_result := recorder.record_event("session_started", {
		"sourceFront": "A21/F22",
		"producerSemanticId": "RACE_WINNER_SESSION_START",
	})
	if not event_result.get("ok", false):
		push_error("VEILWILD_A21_RACE_FAIL event=" + str(event_result))
		quit(12)
		return
	var finish_result := recorder.finalize_run("race_winner_complete")
	if not finish_result.get("ok", false):
		push_error("VEILWILD_A21_RACE_FAIL finalize=" + str(finish_result))
		quit(13)
		return
	print("VEILWILD_A21_RACE_WIN pid=" + str(OS.get_process_id()) + " raw=" + str(finish_result["eventSha256"]) + " manifest=" + str(finish_result["manifestSha256"]))
	quit(0)
