extends SceneTree

func _initialize() -> void:
    call_deferred("_capture")

func _capture() -> void:
    var game: Node = load("res://main.tscn").instantiate()
    root.add_child(game)
    await process_frame
    game.get_node("HUD/StartButton").pressed.emit()
    game.get_node("StartTimer").stop()
    game.get_node("MobTimer").stop()
    game.get_node("ScoreTimer").stop()
    # Screenshot actual Godot Scene, Player, native drawn depot and active core.
    for n in range(5):
        await process_frame
    var args: PackedStringArray = OS.get_cmdline_user_args()
    var output: String = args[1] if args.size() > 1 and args[0] == "--out" else "/tmp/beacon-relay-preview.png"
    var err: Error = root.get_texture().get_image().save_png(output)
    if err != OK:
        push_error("GAME_BEACON_CAPTURE_FAILED: %d" % err)
        quit(1)
        return
    print("GAME_BEACON_CAPTURE_PASS path=" + output)
    quit()
