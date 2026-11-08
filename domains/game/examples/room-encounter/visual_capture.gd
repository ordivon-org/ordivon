extends SceneTree

# Actual rendered OpenGL/Viewport capture under a private Xvfb display.
# This is machine-visual, not a real Human session and not a pixel Agent port.
# Usage: DISPLAY=:95 godot --path ... --script res://visual_capture.gd -- --out /absolute/path
var captured: Array[String] = []
var checks: int = 0
var failures: int = 0

func check(ok: bool, description: String) -> void:
    checks += 1
    if not ok:
        failures += 1
        push_error("GAME_VISUAL_FAIL " + description)

func no_overlap(game: Control) -> void:
    var hud: Control = game.get_node("View")
    var dialogue: Control = game.get_node("GateDialogue")
    check(hud.get_global_rect().position.y >= -0.1, "HUD begins inside viewport")
    check(hud.get_global_rect().end.y <= root.size.y + 0.1, "HUD fits viewport")
    if dialogue.visible:
        check(dialogue.get_global_rect().position.y >= hud.get_global_rect().end.y - 0.1,
            "native layout does not overlap dialogue and HUD")
        check(dialogue.get_global_rect().end.y <= root.size.y + 0.1,
            "dialogue fits inside viewport")

func capture(game: Control, directory: String, name: String) -> void:
    await RenderingServer.frame_post_draw
    no_overlap(game)
    var image: Image = root.get_texture().get_image()
    check(image != null and image.get_width() >= 800 and image.get_height() >= 500,
        "native renderer returns full viewport pixels")
    var output: String = directory.path_join(name + ".png")
    check(image.save_png(output) == OK, "Godot viewport PNG export succeeds " + name)
    captured.append(name)

func _initialize() -> void:
    call_deferred("run_visual_capture")

func run_visual_capture() -> void:
    var args: PackedStringArray = OS.get_cmdline_user_args()
    if args.size() != 2 or args[0] != "--out" or not args[1].is_absolute_path():
        push_error("expected -- --out /absolute/directory")
        quit(2)
        return
    var directory: String = args[1]
    if DirAccess.make_dir_recursive_absolute(directory) != OK:
        push_error("cannot create capture directory")
        quit(2)
        return
    var packed: PackedScene = load("res://main.tscn")
    check(packed != null, "real game scene loads")
    var game: Control = packed.instantiate()
    root.add_child(game)
    if not game.is_node_ready():
        await game.ready
    check(game is VBoxContainer, "native responsive root layout")
    check(game.get_node("View").get_index() < game.get_node("GateDialogue").get_index(),
        "HUD before narrative in native layout")
    await capture(game, directory, "01-classic")
    check(game.start_tactical_trial(), "same Human Trial action")
    await capture(game, directory, "02-tactical")
    var rules: Node = game.get_node("Rules")
    check(rules.attack() and rules.attack(), "two native attacks reach charged telegraph")
    check(rules.snapshot()["forecast"]["threat_damage"] == 4,
        "third-turn threat prediction actually visible")
    await capture(game, directory, "03-charged-threat")
    check(rules.guard(), "real native charged parry")
    check(rules.attack() and rules.attack(), "first trial room cleared")
    check(rules.snapshot()["phase"] == "cleared", "real room clear")
    var dialogue: Node = game.get_node("GateDialogue")
    if dialogue.available_responses.is_empty():
        await dialogue.response_settled
    check(dialogue.visible and not dialogue.available_responses.is_empty(),
        "actual upstream narrative response becomes visible")
    await process_frame
    var focus: Control = root.gui_get_focus_owner()
    check(focus is Button and focus.text.contains("Unlock"),
        "native keyboard focus moves to enabled semantic passage choice")
    await capture(game, directory, "04-gate-dialogue")
    if failures == 0:
        print("GAME_NATIVE_VISUAL_CAPTURE_PASS frames=%d geometry_checks=%d mode=real_viewport_not_human" %
            [captured.size(), checks])
    else:
        print("GAME_NATIVE_VISUAL_CAPTURE_FAIL failures=%d geometry_checks=%d" %
            [failures, checks])
    var audio: AudioStreamPlayer = game.get_node("EncounterAudio")
    audio.stop()
    audio.stream = null
    game.queue_free()
    quit(0 if failures == 0 else 1)
