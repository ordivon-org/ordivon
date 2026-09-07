extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/F13 binding: main scene did not load")
        quit(2)
        return
    var instance := packed.instantiate()
    root.add_child(instance)
    await process_frame
    var host := instance.get_node_or_null("SystemsMount/F13BehaviorHost")
    if host == null:
        push_error("A17/F13 binding: mounted host absent")
        quit(3)
        return
    var sample := {
        "player_distance_m": 20.0,
        "line_of_sight": false,
        "visual_exposure": 0.0,
        "player_motion": 0.0,
        "observation_pressure": 0.0,
        "nonvisual_stimulus": 0.0,
        "concealment_available": false,
        "concealment_quality": 0.0,
        "escape_available": false,
    }
    var result: Dictionary = host.step_policy(0.1, sample)
    if result.get("state_name") != "UNAWARE":
        push_error("A17/F13 binding changed A13 calm-state semantics")
        quit(4)
        return
    if not result.has("nav_intent") or not result.has("camouflage_drive"):
        push_error("A17/F13 binding lost producer output fields")
        quit(5)
        return
    print("VEILWILD_A17_F13_BINDING_VALID state=%s" % result["state_name"])
    quit(0)
