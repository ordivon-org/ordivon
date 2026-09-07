extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/A09 binding test: main scene did not load")
        quit(2)
        return
    var integration := packed.instantiate()
    root.add_child(integration)
    await process_frame
    if not integration.integration_failures.is_empty():
        push_error("A17/A09 binding test: integration failures %s" % JSON.stringify(integration.integration_failures))
        quit(3)
        return
    if integration.animation_binding == null:
        push_error("A17/A09 binding test: binding adapter missing")
        quit(4)
        return
    if not bool(integration.animation_binding.call("strict_probe")):
        push_error("A17/A09 binding test: strict probe failed %s" % str(integration.animation_binding.get("last_error")))
        quit(5)
        return
    var witness: Dictionary = integration.animation_binding.call("snapshot")
    var strict_snapshot: Dictionary = witness.get("strictProbeSnapshot", {})
    if not bool(witness.get("strictProbePass", false)):
        push_error("A17/A09 binding test: strict probe witness false")
        quit(6)
        return
    if String(strict_snapshot.get("behavior_state_id", "")) != "veilwild.behavior.unaware.r1":
        push_error("A17/A09 binding test: F13 state identity drift")
        quit(7)
        return
    if String(strict_snapshot.get("clip_name", "")) != "VW_MOTION_IDLE":
        push_error("A17/A09 binding test: F09 clip identity drift")
        quit(8)
        return
    if int(strict_snapshot.get("transition_serial", 0)) != 1:
        push_error("A17/A09 binding test: expected exactly one real initial transition")
        quit(9)
        return
    print("VEILWILD_A17_F13_F09_FINAL_CREATURE_PASS player=%s state=%s clip=%s serial=%d" % [witness.get("animationPlayerPath", ""), strict_snapshot.get("behavior_state_id", ""), strict_snapshot.get("clip_name", ""), int(strict_snapshot.get("transition_serial", 0))])
    quit(0)
