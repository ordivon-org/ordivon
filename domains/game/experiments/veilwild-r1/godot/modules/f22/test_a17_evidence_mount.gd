extends SceneTree
## Composite validation only: proves A21's producer-owned PackedScene can be
## loaded by A17's exact EvidenceMount without making this shell a product candidate.

const EVIDENCE_SCENE := "res://modules/f22/evidence_runtime.tscn"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var source_revision := OS.get_environment("VEILWILD_SOURCE_REVISION")
	if not _require(source_revision.length() == 40, "missing_exact_source_revision"):
		return
	var invocation_id := OS.get_environment("VEILWILD_FIXTURE_RUN_ID")
	if not _require(_valid_invocation_id(invocation_id), "VEILWILD_FIXTURE_RUN_ID_required_and_must_match_[A-Za-z0-9._-]+"):
		return
	var run_id := "a21-a17-mount-" + invocation_id
	var output := "user://veilwild_a21_a17_mount_" + invocation_id + ".jsonl"
	ProjectSettings.set_setting("veilwild/integration/evidence_scene", EVIDENCE_SCENE)
	ProjectSettings.set_setting("veilwild/integration/strict_candidate", false)
	var main_scene := load("res://main.tscn") as PackedScene
	if not _require(main_scene != null, "main_scene_missing"):
		return
	var integration_root := main_scene.instantiate()
	root.add_child(integration_root)
	await process_frame
	var evidence_mount := integration_root.get_node_or_null("EvidenceMount")
	if not _require(evidence_mount != null, "evidence_mount_missing"):
		return
	if not _require(evidence_mount.get_child_count() == 1, "evidence_module_not_mounted"):
		return
	var evidence_runtime := evidence_mount.get_child(0)
	if not _require(evidence_runtime.name == "VeilwildEvidenceRuntime", "unexpected_evidence_module"):
		return

	var begin_receipt: Dictionary = evidence_runtime.begin_evidence_run({
		"runId": run_id,
		"sourceRevision": source_revision,
		"buildId": "A17_SHELL_PLUS_A21_F22_COMPOSITE_FIXTURE",
		"conditionId": "A17_EVIDENCE_MOUNT_HEADLESS_FIXTURE",
		"accessibilityConditionId": "A22_NOT_EVALUATED_COMPOSITE_FIXTURE",
	}, output)
	if not _require(begin_receipt.get("ok", false), "begin_failed:" + str(begin_receipt)):
		return
	for row in [
		["session_started", {"sourceFront": "A21/F22", "producerSemanticId": "A17_EVIDENCE_MOUNT_FIXTURE_START", "sessionPhaseId": "ORIENT"}],
		["session_ended", {"sourceFront": "A21/F22", "producerSemanticId": "A17_EVIDENCE_MOUNT_FIXTURE_END", "sessionPhaseId": "OPTIONAL_REPLAY_OR_END", "reasonId": "composite_mount_validation_complete"}],
	]:
		var receipt: Dictionary = evidence_runtime.record_semantic_event(row[0], row[1])
		if not _require(receipt.get("ok", false), "record_failed:" + str(receipt)):
			return
	var final_receipt: Dictionary = evidence_runtime.finalize_evidence_run("composite_mount_fixture_complete")
	if not _require(final_receipt.get("ok", false), "finalize_failed:" + str(final_receipt)):
		return
	if not _require(final_receipt.get("eventCount", -1) == 2, "event_count_mismatch"):
		return
	print("VEILWILD_A21_A17_EVIDENCE_MOUNT_PASS loaded_evidence=1 strict=false")
	print("A21_A17_EVENTS=" + ProjectSettings.globalize_path(output))
	print("A21_A17_EVENTS_SHA256=" + str(final_receipt["eventSha256"]))
	print("A21_A17_MANIFEST=" + ProjectSettings.globalize_path(final_receipt["manifestPath"]))
	print("A21_A17_MANIFEST_SHA256=" + str(final_receipt["manifestSha256"]))
	integration_root.queue_free()
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
	push_error("VEILWILD_A21_A17_EVIDENCE_MOUNT_FAIL " + message)
	quit(1)
	return false
