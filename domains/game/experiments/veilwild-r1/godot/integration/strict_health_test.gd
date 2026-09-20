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
        push_error("A17 strict gate accepted an incomplete integration candidate")
        quit(3)
        return
    var missing: Array = status["missingModules"]
    if missing.is_empty():
        push_error("A17 strict gate failed without missing-module evidence")
        quit(4)
        return
    if "behavior" in missing:
        push_error("A17 strict gate did not recognize configured F13 behavior module")
        quit(5)
        return
    if not instance.loaded_modules.has("behavior"):
        push_error("A17 strict gate did not mount configured F13 behavior module")
        quit(6)
        return
    print("VEILWILD_A17_STRICT_GATE_VALID loaded=%d missing=%d" % [instance.loaded_modules.size(), missing.size()])
    quit(0)
