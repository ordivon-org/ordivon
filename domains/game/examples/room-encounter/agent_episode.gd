extends SceneTree

# Bounded, engine-native symbolic episode port for this one game fixture.
# Input: -- --actions attack,guard,advance,trial,classic [--observation player|debug].
# Default player mode projects native rendered HUD/dialogue, never full rules state.
# This is not a generic Game service, screen reader, or human-playtest proxy.
const MAX_ACTIONS: int = 64
const PREFIX: String = "GAME_AGENT_EPISODE_JSON="

# Observe the actual native presentation. No hidden rule snapshot in this port.
func _player_observation(game: Control) -> Dictionary:
    var view: VBoxContainer = game.get_node("View")
    var dialogue: VBoxContainer = game.get_node("GateDialogue")
    var actions: Dictionary = {}
    for action in ["Attack", "Guard", "Next", "Trial", "Classic"]:
        var control: Button = view.get_node("Actions/" + action)
        actions[{"Attack": "attack", "Guard": "guard", "Next": "advance", "Trial": "trial", "Classic": "classic"}[action]] = (
            control.visible and not control.disabled
        )
    var observation: Dictionary = {
        "title": view.get_node("Title").text,
        "status": view.get_node("Status").text,
        "encounter": view.get_node("Encounter").text,
        "actions": actions
    }
    if view.get_node("Hint").visible:
        observation["hint"] = view.get_node("Hint").text
    if dialogue.visible:
        var responses: Array[Dictionary] = []
        for node in dialogue.get_node("Choices").get_children():
            if node is Button and node.visible and not node.is_queued_for_deletion():
                responses.append({"text": node.text, "enabled": not node.disabled})
        observation["dialogue"] = {
            "text": dialogue.get_node("Line").text,
            "status": dialogue.get_node("Status").text,
            "responses": responses
        }
    return observation

func _observation(game: Control, rules: Node, mode: String) -> Dictionary:
    if mode == "debug":
        return rules.snapshot().duplicate(true)
    return _player_observation(game)

func _initialize() -> void:
    call_deferred("run_episode")

func run_episode() -> void:
    var args: PackedStringArray = OS.get_cmdline_user_args()
    var observation_mode: String = "player"
    if args.size() == 4 and args[2] == "--observation":
        observation_mode = args[3]
    if (args.size() != 2 and args.size() != 4) or args[0] != "--actions" or (
        args.size() == 4 and args[2] != "--observation"
    ) or observation_mode not in ["player", "debug"]:
        print(PREFIX + JSON.stringify({
            "schema_version": 2,
            "error": "expected: -- --actions attack,guard,advance [--observation player|debug]"
        }))
        quit(2)
        return

    var actions: Array[String] = []
    if not args[1].is_empty():
        for item in args[1].split(",", true):
            actions.append(item.strip_edges())
    if actions.size() > MAX_ACTIONS:
        print(PREFIX + JSON.stringify({
            "schema_version": 2,
            "error": "action limit exceeded",
            "max_actions": MAX_ACTIONS
        }))
        quit(2)
        return

    var packed: PackedScene = load("res://main.tscn")
    if packed == null:
        print(PREFIX + JSON.stringify({"schema_version": 2, "error": "scene unavailable"}))
        quit(3)
        return
    var game: Control = packed.instantiate()
    root.add_child(game)
    if not game.is_node_ready():
        await game.ready
    var rules: Node = game.get_node("Rules")
    var initial: Dictionary = _observation(game, rules, observation_mode)
    if rules.snapshot()["phase"] == "uninitialized":
        print(PREFIX + JSON.stringify({
            "schema_version": 2,
            "error": "native game not initialized; run Godot editor import first"
        }))
        game.queue_free()
        quit(3)
        return
    var steps: Array[Dictionary] = []

    for action in actions:
        var before: Dictionary = _observation(game, rules, observation_mode)
        var accepted: bool = false
        var control_path: String = "unrecognized"
        match action:
            "attack":
                accepted = rules.attack()
                control_path = "native.rules"
            "guard":
                accepted = rules.guard()
                control_path = "native.rules"
            "trial":
                accepted = game.start_tactical_trial()
                control_path = "native.trial_resource"
            "classic":
                accepted = game.start_classic_run()
                control_path = "native.classic_resource"
            "advance":
                control_path = "dialogue.unavailable"
                if rules.snapshot()["phase"] == "cleared":
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
        # Ensure asynchronous dialogue renders visible buttons before a player observation.
        var dialogue_after: VBoxContainer = game.get_node("GateDialogue")
        if (observation_mode == "player" and rules.snapshot()["phase"] == "cleared"
                and dialogue_after.visible and dialogue_after.available_responses.is_empty()):
            await dialogue_after.response_settled
        var after: Dictionary = _observation(game, rules, observation_mode)
        # A player-mode step contains only the chosen input and real visible
        # before/after observations. Private admission/dispatch diagnostics
        # belong solely to the opt-in debug channel.
        var observed_step: Dictionary = {
            "action": action,
            "before": before,
            "after": after
        }
        if observation_mode == "debug":
            observed_step["control_path"] = control_path
            observed_step["recognized"] = action in ["attack", "guard", "advance", "trial", "classic"]
            observed_step["accepted"] = accepted
        steps.append(observed_step)

    var last: Dictionary = rules.snapshot().duplicate(true)
    print(PREFIX + JSON.stringify({
        "schema_version": 2,
        "game": "room-encounter",
        "observation_mode": "player_visible_ui" if observation_mode == "player" else "authoritative_debug_state_not_pixels",
        "actions": ["attack", "guard", "advance", "trial", "classic"],
        "initial": initial,
        "steps": steps,
        "final": _observation(game, rules, observation_mode),
        "terminal": last["phase"] in ["won", "lost"]
    }))
    var audio: AudioStreamPlayer = game.get_node("EncounterAudio")
    audio.stop()
    audio.stream = null
    game.queue_free()
    quit(0)
