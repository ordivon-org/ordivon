extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/F13 R2 binding: main scene did not load")
        quit(2)
        return
    var integration := packed.instantiate()
    root.add_child(integration)
    await process_frame
    if not integration.loaded_modules.has("behavior"):
        push_error("A17/F13 R2 binding: behavior module not recorded")
        quit(3)
        return
    var nodes := get_nodes_in_group("veilwild.f13_behavior_runtime")
    if nodes.size() != 1:
        push_error("A17/F13 R2 binding: expected one producer runtime, got %d" % nodes.size())
        quit(4)
        return
    var runtime := nodes[0]
    var sample := {
        "player_distance_m": 8.0,
        "line_of_sight": true,
        "visual_exposure": 0.55,
        "player_motion": 0.40,
        "observation_pressure": 0.25,
        "nonvisual_stimulus": 0.0,
        "concealment_available": false,
        "concealment_quality": 0.0,
        "concealment_affordance_id": "",
        "escape_available": false,
        "escape_affordance_id": "",
    }
    var result: Dictionary = {}
    for i in range(5):
        result = runtime.submit_perception(0.1, sample)
    var auth: Dictionary = result.get("player_cue_authorization", {})
    if auth.get("authorization_only") != true:
        push_error("A17/F13 R2 binding: authorization_only guard lost")
        quit(5)
        return
    for key in ["sustained_classes", "edge_classes", "explicit_none_classes"]:
        if not auth.has(key):
            push_error("A17/F13 R2 binding: cue authorization lacks %s" % key)
            quit(6)
            return
    if bool(result.get("reacquisition_proven", true)):
        push_error("A17/F13 R2 binding: F13 illegally proves reacquisition")
        quit(7)
        return
    if str(result.get("product_intent", "")) == "OBSERVATION_SUCCESS":
        push_error("A17/F13 R2 binding: F13 illegally owns success")
        quit(8)
        return
    print("VEILWILD_A17_F13_R2_BINDING_VALID state=%s authorization_only=true reacquisition_proven=false" % result.get("state_name", "?"))
    quit(0)
