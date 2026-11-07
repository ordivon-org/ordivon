extends SceneTree

# Bounded, engine-native symbolic episode port for this one game fixture.
# Input: -- --actions attack,guard,advance ; output: one prefixed JSON record.
# This is not a generic Game service, screen reader, or human-playtest proxy.
const MAX_ACTIONS: int = 64
const PREFIX: String = "GAME_AGENT_EPISODE_JSON="

func _initialize() -> void:
    call_deferred("run_episode")

func run_episode() -> void:
    var args: PackedStringArray = OS.get_cmdline_user_args()
    if args.size() != 2 or args[0] != "--actions":
        print(PREFIX + JSON.stringify({
            "schema_version": 1,
            "error": "expected: -- --actions attack,guard,advance"
        }))
        quit(2)
        return

    var actions: Array[String] = []
    if not args[1].is_empty():
        for item in args[1].split(",", true):
            actions.append(item.strip_edges())
    if actions.size() > MAX_ACTIONS:
        print(PREFIX + JSON.stringify({
            "schema_version": 1,
            "error": "action limit exceeded",
            "max_actions": MAX_ACTIONS
        }))
        quit(2)
        return

    var packed: PackedScene = load("res://main.tscn")
    if packed == null:
        print(PREFIX + JSON.stringify({"schema_version": 1, "error": "scene unavailable"}))
        quit(3)
        return
    var game: Control = packed.instantiate()
    root.add_child(game)
    await process_frame
    await process_frame
    var rules: Node = game.get_node("Rules")
    var initial: Dictionary = rules.snapshot().duplicate(true)
    if initial["phase"] == "uninitialized":
        print(PREFIX + JSON.stringify({
            "schema_version": 1,
            "error": "native game not initialized; run Godot editor import first"
        }))
        game.free()
        quit(3)
        return
    var steps: Array[Dictionary] = []

    for action in actions:
        var before: Dictionary = rules.snapshot().duplicate(true)
        var accepted: bool = false
        var control_path: String = "unrecognized"
        match action:
            "attack":
                accepted = rules.attack()
                control_path = "native.rules"
            "guard":
                accepted = rules.guard()
                control_path = "native.rules"
            "advance":
                control_path = "dialogue.unavailable"
                if before["phase"] == "cleared":
                    # The Agent must select the same native narrative gate choice
                    # available to a Human, not bypass G09 with rules.advance().
                    var gate: VBoxContainer = game.get_node("GateDialogue")
                    await process_frame
                    await process_frame
                    var choices: HBoxContainer = gate.get_node("Choices")
                    if gate.visible and choices.get_child_count() > 0:
                        var unlock: Button = choices.get_child(0)
                        if not unlock.disabled:
                            unlock.pressed.emit()
                            await process_frame
                            await process_frame
                            control_path = "dialogue.unlock_choice"
                            accepted = rules.snapshot() != before
            _:
                pass
        var after: Dictionary = rules.snapshot().duplicate(true)
        steps.append({
            "action": action,
            "control_path": control_path,
            "recognized": action in ["attack", "guard", "advance"],
            "accepted": accepted,
            "before": before,
            "after": after
        })

    var last: Dictionary = rules.snapshot().duplicate(true)
    print(PREFIX + JSON.stringify({
        "schema_version": 1,
        "game": "room-encounter",
        "observation_mode": "authoritative_state_not_pixels",
        "actions": ["attack", "guard", "advance"],
        "initial": initial,
        "steps": steps,
        "final": last,
        "terminal": last["phase"] in ["won", "lost"]
    }))
    var audio: AudioStreamPlayer = game.get_node("EncounterAudio")
    audio.stop()
    audio.stream = null
    game.free()
    quit(0)
