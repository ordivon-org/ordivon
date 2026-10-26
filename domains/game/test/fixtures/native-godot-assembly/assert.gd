extends SceneTree

var failures: Array[String] = []
var assertions: int = 0

func expect(ok: bool, explanation: String) -> void:
    assertions += 1
    if not ok:
        failures.append(explanation)
        push_error(explanation)

func invariant(s: Dictionary, width: int, limit: int) -> void:
    expect(s["x"] >= 0 and s["x"] < width, "player remains inside board")
    expect(s["energy"] >= 0, "energy never becomes negative")
    expect(s["turn"] >= 0 and s["turn"] <= limit, "turn count stays bounded")
    expect(s["phase"] in ["playing", "won", "lost"], "phase belongs to declared states")

func _initialize() -> void:
    call_deferred("run_acceptance")

func run_acceptance() -> void:
    # Test from the public packed scene and replaceable resource, not a mock.
    var packed = load("res://main.tscn")
    expect(packed is PackedScene, "Godot can load native assembled scene")
    if not packed is PackedScene:
        quit(1)
        return
    var scene = packed.instantiate()
    root.add_child(scene)
    var rules = scene.get_node("Rules")
    var view = scene.get_node("View")
    expect(rules.snapshot()["phase"] == "playing", "scene starts in playable state")
    expect(view.get_node("Board").text.contains("P"), "native UI observes initial rules state")
    expect(not rules.move(0), "non-neighbor action rejected")
    expect(not rules.move(-1), "out-of-bound action rejected")
    for step in range(4):
        expect(rules.move(1), "legal action accepted")
    var state: Dictionary = rules.snapshot()
    invariant(state, 5, 6)
    expect(state["phase"] == "won", "goal is reached using existing action LEGO")
    expect(view.get_node("Status").text.contains("won"), "UI observes terminal state via native signal")
    expect(not rules.move(1), "terminal state cannot be mutated")

    var mod_config = load("res://configs/player_variant.tres")
    expect(rules.reset_game(mod_config), "player-supplied native resource replaces gameplay configuration")
    expect(rules.snapshot()["goal_x"] == 2, "replacement changes real target")
    expect(rules.move(1) and rules.move(1), "same mechanics play with replacement")
    expect(rules.snapshot()["phase"] == "won", "replacement produces its own win condition")
    var before: Dictionary = rules.snapshot()
    var invalid = mod_config.duplicate()
    invalid.goal_x = 100
    expect(not rules.reset_game(invalid), "invalid replacement is rejected")
    expect(rules.snapshot() == before, "invalid replacement leaves running state unchanged")

    # A second composition uses the exact same rules and native scene scripts
    # while selecting another presentation PackedScene before entering the tree.
    var alternate_scene = packed.instantiate()
    alternate_scene.view_scene = load("res://view_variant.tscn")
    root.add_child(alternate_scene)
    var alternate = alternate_scene.get_node("View")
    expect(alternate.get_node("Title").text.contains("Player UI"), "native scene replacement changes UI")
    expect(alternate_scene.get_node("Rules").move(1), "rules execute under swapped UI")
    expect(alternate.get_node("Board").text.begins_with(". P"), "alternate UI receives rule signals")
    alternate_scene.queue_free()

    var base = load("res://configs/base.tres")
    for sequence in range(1 << base.turn_limit):
        expect(rules.reset_game(base), "base scenario resets")
        for turn in range(base.turn_limit):
            var dx = 1 if (sequence & (1 << turn)) != 0 else -1
            rules.move(dx)
            invariant(rules.snapshot(), base.board_width, base.turn_limit)
            if rules.snapshot()["phase"] != "playing":
                break

    scene.queue_free()
    if failures.size() == 0:
        print("GAME_NATIVE_COMPOSITION_PASS assertions=", assertions, " sequences=", 1 << base.turn_limit)
        quit(0)
    else:
        printerr("GAME_NATIVE_COMPOSITION_FAIL count=", failures.size(), " assertions=", assertions)
        quit(1)
