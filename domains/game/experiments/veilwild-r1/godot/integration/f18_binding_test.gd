extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/F18 binding: main scene did not load")
        quit(2)
        return
    var instance := packed.instantiate()
    root.add_child(instance)
    await process_frame
    if not instance.loaded_modules.has("player_runtime") or not instance.loaded_modules.has("ui"):
        push_error("A17/F18 binding: configured player/UI modules not recorded")
        quit(3)
        return
    var player := instance.get_node_or_null("PlayerRuntimeMount/PlayerRuntime")
    var ui := instance.get_node_or_null("UIOverlay/PlayerUI")
    if player == null or ui == null:
        push_error("A17/F18 binding: exact producer scene roots not mounted")
        quit(4)
        return
    if not (player is CharacterBody3D):
        push_error("A17/F18 binding: player root type changed")
        quit(5)
        return
    if int(player.collision_layer) != 2 or int(player.collision_mask) != 1:
        push_error("A17/F18 binding: player collision contract drift")
        quit(6)
        return
    if player.has_signal("observation_succeeded") or player.has_signal("observation_committed"):
        push_error("A17/F18 binding: F18 illegally owns observation success/commit")
        quit(7)
        return
    var footprint: Dictionary = player.call("get_player_collision_footprint")
    if not is_equal_approx(float(footprint["radiusMeters"]), 0.35) or not is_equal_approx(float(footprint["totalHeightMeters"]), 1.8):
        push_error("A17/F18 binding: player body dimensions drift")
        quit(8)
        return
    print("VEILWILD_A17_F18_BINDING_VALID player=PlayerRuntime ui=PlayerUI observe_success_owner=false")
    quit(0)
