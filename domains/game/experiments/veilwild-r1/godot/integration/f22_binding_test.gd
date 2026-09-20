extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/F22 binding: main scene did not load")
        quit(2)
        return
    var instance := packed.instantiate()
    root.add_child(instance)
    await process_frame
    var runtime := instance.get_node_or_null("EvidenceMount/VeilwildEvidenceRuntime")
    if runtime == null or not instance.loaded_modules.has("evidence"):
        push_error("A17/F22 binding: A21 evidence runtime not mounted")
        quit(3)
        return
    var suffix := str(OS.get_process_id()) + "_" + str(Time.get_ticks_usec())
    var output_path := "user://a17_f22_binding_" + suffix + ".jsonl"
    var bad: Dictionary = runtime.begin_evidence_run({"runId":"incomplete"}, output_path)
    if bool(bad.get("ok", false)) or bad.get("error") != "missing_context:sourceRevision":
        push_error("A17/F22 binding: missing run identity was not rejected")
        quit(4)
        return
    var context := {
        "runId": "A17_BINDING_FIXTURE_" + suffix,
        "sourceRevision": "A17_BINDING_FIXTURE_SOURCE_NOT_CANDIDATE",
        "buildId": "A17_BINDING_FIXTURE_NOT_A_BUILD",
        "conditionId": "A17_MECHANICAL_BINDING_ONLY",
        "accessibilityConditionId": "A17_MECHANICAL_BINDING_ONLY",
    }
    var started: Dictionary = runtime.begin_evidence_run(context, output_path)
    if not bool(started.get("ok", false)):
        push_error("A17/F22 binding: begin failed: %s" % JSON.stringify(started))
        quit(5)
        return
    var event: Dictionary = runtime.record_semantic_event("session_started", {
        "sourceFront": "A17/F17",
        "producerSemanticId": "A17_BINDING_FIXTURE_SESSION_START",
    })
    if not bool(event.get("ok", false)) or int(event["event"].get("sequence", 0)) != 1:
        push_error("A17/F22 binding: event transport failed")
        quit(6)
        return
    var finished: Dictionary = runtime.finalize_evidence_run("MECHANICAL_BINDING_ONLY")
    if not bool(finished.get("ok", false)) or int(finished.get("eventCount", 0)) != 1:
        push_error("A17/F22 binding: finalize failed")
        quit(7)
        return
    print("VEILWILD_A17_F22_OWNER_MODULE_BINDING_VALID events=%d manifest=%s output=%s" % [finished["eventCount"], finished["manifestSha256"], output_path])
    quit(0)
