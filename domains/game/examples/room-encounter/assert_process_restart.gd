extends SceneTree

# Two *separate Godot processes*, both consuming the same ConfigFile bytes.
# The file's location is injected by mise's existing native test command;
# the game keeps sole authority for state/checkpoint validation.
var checks: int = 0
var failures: int = 0

func expect(condition: bool, reason: String) -> void:
    checks += 1
    if not condition:
        failures += 1
        push_error(reason)

func _initialize() -> void:
    call_deferred("run_acceptance")

func run_acceptance() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 4 or args[0] != "--phase" or args[2] != "--slot":
        push_error("Expected: -- --phase save|load --slot ABSOLUTE_PATH")
        quit(2)
        return
    var phase: String = args[1]
    var path: String = args[3]
    if phase not in ["save", "load"] or not path.is_absolute_path():
        push_error("Invalid phase or non-absolute temporary slot path")
        quit(2)
        return

    var packed: PackedScene = load("res://main.tscn")
    if packed == null:
        push_error("Native room scene did not load")
        quit(1)
        return
    var game := packed.instantiate()
    root.add_child(game)
    await process_frame
    var rules: Node = game.get_node("Rules")
    var save_slot: Node = game.get_node("SaveSlot")
    var audio: AudioStreamPlayer = game.get_node("EncounterAudio")
    save_slot.slot_path = path

    if phase == "save":
        expect(rules.snapshot()["room"] == 1 and rules.snapshot()["turn"] == 0,
            "new process begins from its own fresh room state")
        expect(rules.attack(), "accepted first-room attack")
        expect(rules.snapshot()["phase"] == "cleared", "first room cleared")
        expect(rules.advance(), "entered second room")
        expect(rules.guard(), "accepted second-room guard")
        expect(rules.snapshot()["room"] == 2 and rules.snapshot()["turn"] == 2
            and rules.snapshot()["phase"] == "fighting", "checkpoint is a nontrivial, mutable room state")
        expect(save_slot.save_rules(rules), "Godot native ConfigFile persists rule checkpoint")
        expect(FileAccess.file_exists(path), "checkpoint survives on physical disk before process exits")
    else:
        expect(FileAccess.file_exists(path), "second process sees first process checkpoint")
        expect(rules.snapshot()["room"] == 1 and rules.snapshot()["turn"] == 0,
            "new process cannot rely on previous SceneTree memory")
        expect(save_slot.load_rules(rules), "fresh process restores through existing SaveSlot/Rule contract")
        var recovered: Dictionary = rules.snapshot()
        expect(recovered["room"] == 2 and recovered["turn"] == 2
            and recovered["phase"] == "fighting" and recovered["foes"] == 2,
            "second process reconstitutes exact room, turn, phase and foes")
        expect(game.get_node("View/Status").text.contains("ROOM 2/3"),
            "restored Signal re-renders the native UI")
        expect(audio.observed_play_count == 0,
            "state restoration is not an accepted combat action or sound")
        expect(rules.attack(), "restored game can continue accepting gameplay")
        expect(rules.snapshot()["turn"] == 3 and rules.snapshot()["room"] == 2,
            "continued gameplay mutates restored rules, not a detached snapshot")
        expect(audio.observed_play_count == 1,
            "continued gameplay emits the existing native audio effect exactly once")

    audio.stop()
    audio.stream = null
    game.free()
    await create_timer(0.15).timeout
    # Release scene/Node/Resource references before asking Godot to quit.
    rules = null
    save_slot = null
    audio = null
    game = null
    packed = null
    print("GAME_ROOM_PROCESS_RESTART_%s checks=%d phase=%s" % [
        "PASS" if failures == 0 else "FAIL", checks, phase])
    quit(0 if failures == 0 else 1)
