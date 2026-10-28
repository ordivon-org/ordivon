extends SceneTree

# A mod-supplied Resource may self-claim is_valid without implementing
# the actual gameplay input ports. Contract admission must reject it.
class MalformedConfig extends Resource:
    func is_valid() -> bool:
        return true

# A user variant that *does* refine the actual native Resource type is allowed.
class DerivedConfig extends "res://config.gd":
    pass

# Subclasses are legitimate consumers, but cannot be their own certificate
# of the base behavior/parameter invariant.
class ForgedDerivedConfig extends "res://config.gd":
    func is_valid() -> bool:
        return true

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

    # The behavioral contract is observable: rejection must be atomic, with
    # unchanged state and no false native Signal/UI notification.
    var observed_changes: Array[Dictionary] = []
    rules.state_changed.connect(func(next_state: Dictionary) -> void:
        observed_changes.append(next_state)
    )
    var before_malformed: Dictionary = rules.snapshot()
    var old_board: String = view.get_node("Board").text
    var old_status: String = view.get_node("Status").text
    for bad_resource in [MalformedConfig.new(), Resource.new()]:
        var before_signals: int = observed_changes.size()
        expect(not rules.reset_game(bad_resource), "resource lacking native typed gameplay ports is rejected")
        expect(rules.snapshot() == before_malformed, "untyped replacement leaves gameplay state unchanged")
        expect(observed_changes.size() == before_signals, "untyped replacement does not emit a false state signal")
        expect(view.get_node("Board").text == old_board, "untyped replacement leaves board presentation unchanged")
        expect(view.get_node("Status").text == old_status, "untyped replacement leaves status presentation unchanged")

    # Enumerate each boundary of the actual numeric input parameters.
    var invalid_boundaries: Array[Array] = [
        ["board_width", 1], ["board_width", 65],
        ["goal_x", 0], ["goal_x", 5],
        ["starting_energy", -1], ["starting_energy", 129],
        ["step_cost", 0], ["step_cost", 129],
        ["turn_limit", 0], ["turn_limit", 65],
    ]
    for fault in invalid_boundaries:
        var out_of_contract = load("res://configs/base.tres").duplicate(true)
        out_of_contract.set(fault[0], fault[1])
        var prior_state: Dictionary = rules.snapshot()
        var prior_events: int = observed_changes.size()
        expect(not rules.reset_game(out_of_contract), "invalid native port rejected: %s=%s" % [fault[0], fault[1]])
        expect(rules.snapshot() == prior_state, "invalid numeric input preserves gameplay state")
        expect(observed_changes.size() == prior_events, "invalid numeric input emits no signal")

    var malicious_derived = ForgedDerivedConfig.new()
    malicious_derived.board_width = 1
    malicious_derived.goal_x = 0
    malicious_derived.turn_limit = 0
    expect(malicious_derived.is_valid(), "a subclass can falsely self-attest its validity")
    var pre_forgery: Dictionary = rules.snapshot()
    var signals_pre_forgery: int = observed_changes.size()
    expect(not rules.reset_game(malicious_derived), "derived Resource cannot bypass base gameplay invariant")
    expect(rules.snapshot() == pre_forgery, "invalid derived Resource leaves state unchanged")
    expect(observed_changes.size() == signals_pre_forgery, "invalid derived Resource emits no signal")

    var derived: Resource = DerivedConfig.new()
    derived.goal_x = 1
    expect(rules.reset_game(derived), "real native Resource subclass satisfies typed LEGO input")
    expect(rules.move(1), "subclass configuration is consumed by real gameplay transition")
    expect(rules.snapshot()["phase"] == "won", "subclass retains game-defined winning semantics")
    expect(view.get_node("Status").text.contains("won"), "subclass gameplay outcome reaches native UI via Signal")

    # A validated Godot Resource is mutable. The current ruleset must not
    # silently acquire changes to caller-owned input after explicit reset.
    var externally_owned = load("res://configs/player_variant.tres").duplicate(true)
    expect(rules.reset_game(externally_owned), "valid external typed configuration is admitted")
    var captured: Dictionary = rules.snapshot()
    externally_owned.board_width = 1
    externally_owned.goal_x = 0
    externally_owned.step_cost = 0
    expect(rules.snapshot() == captured, "later caller mutation cannot rewrite active rule contract")
    expect(rules.move(1), "captured configuration still supports a real valid action")
    expect(rules.snapshot()["x"] == 1, "caller mutation cannot corrupt the action update")

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
