extends SceneTree

var count: int = 0
var moves: int = 0
var failed: bool = false

func check(ok: bool, description: String) -> void:
    if not ok:
        failed = true
        push_error("GAME_BEACON_RELAY_FAIL: " + description)
        quit(1)
        return
    count += 1

func _initialize() -> void:
    call_deferred("_run")

func _release_actions() -> void:
    for action in ["move_up", "move_down", "move_left", "move_right"]:
        Input.action_release(action)

# Walk using the real upstream Player._process input path. No direct state
# substitution is used in the success trajectory.
func _walk_to(player: Area2D, dest: Vector2) -> bool:
    for attempt in range(250):
        var d: Vector2 = dest - player.position
        if d.length() <= 18.0:
            _release_actions()
            return true
        _release_actions()
        if d.x > 11.0:
            Input.action_press("move_right")
        elif d.x < -11.0:
            Input.action_press("move_left")
        if d.y > 11.0:
            Input.action_press("move_down")
        elif d.y < -11.0:
            Input.action_press("move_up")
        await process_frame
        moves += 1
    _release_actions()
    return false

func _run() -> void:
    var game: Node = load("res://main.tscn").instantiate()
    root.add_child(game)
    await process_frame
    var player: Area2D = game.get_node("Player")
    var hud: CanvasLayer = game.get_node("HUD")
    check(game.phase == "ready" and not player.visible, "initial native title state")
    check(hud.get_node("StartButton").visible, "playable launch button visible")
    check(game.relay_plan.pickup_sites.size() == 4, "resource-driven four-stage content")
    check(game.mob_scene != null, "official PackedScene mob supplier present")
    hud.get_node("StartButton").pressed.emit()
    check(game.phase == "playing" and player.visible, "native UI StartButton launches actual Player")
    # Pause only hazard/time suppliers for deterministic input-driven acceptance;
    # separately test native Mob instancing and physical collision below.
    game.get_node("StartTimer").stop()
    game.get_node("MobTimer").stop()
    game.get_node("ScoreTimer").stop()
    check(not game.carrying and game.delivered == 0, "nothing automatically delivered at start")
    await process_frame
    check(game.delivered == 0, "standing at home without a core does not score")
    for n in range(4):
        check(await _walk_to(player, game.relay_plan.pickup_sites[n]),
            "actual upstream movement reaches pickup %d" % (n+1))
        await physics_frame
        check(game.carrying, "native scene picks up core after input movement %d" % (n+1))
        check(player.speed == 330, "carrying slows actual native Player %d" % (n+1))
        check(hud.get_node("StatusLabel").text.contains("CARRYING"),
            "native HUD displays carried stage %d" % (n+1))
        check(await _walk_to(player, game.relay_plan.depot),
            "actual upstream movement returns to hub %d" % (n+1))
        await physics_frame
        check(game.delivered == n+1, "delivery %d credited once at depot" % (n+1))
        check(hud.get_node("ScoreLabel").text.contains("%d / 4" % (n+1)),
            "actual HUD records delivery %d" % (n+1))
        if n < 3:
            check(not game.carrying and player.speed == 400,
                "next-stage pickup required and original speed restored")
    check(game.phase == "won", "finite whole product complete")
    check(not player.visible and hud.get_node("StartButton").visible,
        "win screen supports real replay")
    check(hud.get_node("MessageLabel").text.contains("RELAY RESTORED"),
        "native visible completion endpoint")
    hud.get_node("StartButton").pressed.emit()
    check(game.phase == "playing" and game.delivered == 0 and player.visible,
        "native UI retry resets actual world and progression")
    game.get_node("StartTimer").stop()
    game.get_node("MobTimer").stop()
    game.get_node("ScoreTimer").stop()
    game._on_MobTimer_timeout()
    var mobs: Array[Node] = get_nodes_in_group("mobs")
    check(mobs.size() == 1, "original official Mob PackedScene instantiates and joins mobs group")
    check(mobs[0] is RigidBody2D and mobs[0].get_node("CollisionShape2D") != null,
        "real upstream physics body and collision shape present")
    # Use the existing upstream Area2D-vs-RigidBody collision (NOT a
    # fabricated hit signal), and allow real physics frames to process it.
    mobs[0].position = player.position
    mobs[0].linear_velocity = Vector2.ZERO
    for frame in range(12):
        await physics_frame
        if game.phase == "lost":
            break
    check(game.phase == "lost", "actual upstream Player body_entered loses game")
    check(hud.get_node("StartButton").visible and
        hud.get_node("MessageLabel").text.contains("SIGNAL LOST"),
        "loss has complete replay UI")
    hud.get_node("StartButton").pressed.emit()
    check(game.phase == "playing" and game.delivered == 0 and not game.carrying,
        "after loss, next production-game run starts clean")
    await process_frame
    check(get_nodes_in_group("mobs").is_empty(),
        "restart cleans upstream enemy group without retained world state")
    _release_actions()
    if failed:
        quit(1)
        return
    print("GAME_BEACON_RELAY_PASS assertions=%d keyboard_frames=%d delivery_cycles=4 endpoints=win,loss,retry upstream_physics=yes" % [count, moves])
    game.queue_free()
    await process_frame
    quit()
