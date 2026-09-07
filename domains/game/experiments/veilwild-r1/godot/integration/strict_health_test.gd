extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17 strict gate: main scene did not load")
        quit(2)
        return
    var instance := packed.instantiate()
    root.add_child(instance)
    await process_frame
    var status: Dictionary = instance.candidate_health(true)
    if bool(status["pass"]):
        push_error("A17 strict gate accepted an empty integration candidate")
        quit(3)
        return
    var missing: Array = status["missingModules"]
    if missing.size() != 10:
        push_error("A17 strict gate expected 10 missing modules, got %d" % missing.size())
        quit(4)
        return
    print("VEILWILD_A17_STRICT_GATE_VALID missing=%d" % missing.size())
    quit(0)
