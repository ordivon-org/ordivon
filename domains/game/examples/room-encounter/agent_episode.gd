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
                    # Shared semantic response ID, not a button index or visual tree.
                    var dialogue: VBoxContainer = game.get_node("GateDialogue")
                    if dialogue.visible:
                        if dialogue.available_responses.is_empty():
                            await dialogue.response_settled
                        var native_gate: Node = dialogue.get_node("GameState")
                        var committed: Array[bool] = [false]
                        var on_committed: Callable = func(): committed[0] = true
                        native_gate.passage_advanced.connect(on_committed, CONNECT_ONE_SHOT)
                        var selected: bool = dialogue.choose_response("unlock")
                        if selected:
                            await dialogue.response_settled
                            accepted = committed[0]
                            if accepted:
                                control_path = "dialogue.unlock_choice"
                            else:
                                control_path = "dialogue.not_committed"
                        if native_gate.passage_advanced.is_connected(on_committed):
                            native_gate.passage_advanced.disconnect(on_committed)
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
