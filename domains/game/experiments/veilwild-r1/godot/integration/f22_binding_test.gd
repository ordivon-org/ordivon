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
    var host := instance.get_node_or_null("EvidenceMount/F22EvidenceHost")
    if host == null or not instance.loaded_modules.has("evidence"):
        push_error("A17/F22 binding: evidence host not mounted")
        quit(3)
        return
    var bad: Dictionary = host.begin_run({"runId":"incomplete"}, "user://a17_f22_invalid.jsonl")
    if bool(bad.get("ok", false)) or bad.get("error") != "missing_context:sourceRevision":
        push_error("A17/F22 binding: missing run identity was not rejected")
        quit(4)
        return
    var context := {
        "runId": "A17_BINDING_FIXTURE",
        "sourceRevision": "A17_BINDING_FIXTURE_SOURCE_NOT_CANDIDATE",
        "buildId": "A17_BINDING_FIXTURE_NOT_A_BUILD",
        "conditionId": "A17_MECHANICAL_BINDING_ONLY",
        "accessibilityConditionId": "A17_MECHANICAL_BINDING_ONLY",
    }
    var started: Dictionary = host.begin_run(context, "user://a17_f22_binding.jsonl")
    if not bool(started.get("ok", false)):
        push_error("A17/F22 binding: begin_run failed: %s" % JSON.stringify(started))
        quit(5)
        return
    var event: Dictionary = host.record_event("session_started", {
        "sourceFront": "A17/F17",
        "producerSemanticId": "A17_BINDING_FIXTURE_SESSION_START",
    })
    if not bool(event.get("ok", false)) or int(event["event"].get("sequence", 0)) != 1:
        push_error("A17/F22 binding: session_started transport failed")
        quit(6)
        return
    var finished: Dictionary = host.finalize_run("MECHANICAL_BINDING_ONLY")
    if not bool(finished.get("ok", false)) or int(finished.get("eventCount", 0)) != 1:
        push_error("A17/F22 binding: finalize failed")
        quit(7)
        return
    print("VEILWILD_A17_F22_BINDING_VALID events=%d manifest=%s" % [finished["eventCount"], finished["manifestSha256"]])
    quit(0)
