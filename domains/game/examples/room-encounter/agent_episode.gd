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
        match action:
            "attack":
                accepted = rules.attack()
            "guard":
                accepted = rules.guard()
            "advance":
                accepted = rules.advance()
            _:
                pass
        var after: Dictionary = rules.snapshot().duplicate(true)
        steps.append({
            "action": action,
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
