extends SceneTree

var checks: int = 0

func expect(ok: bool, why: String) -> void:
    checks += 1
    if not ok:
        push_error(why)
        quit(1)

func _initialize() -> void:
    call_deferred("run_acceptance")

func run_acceptance() -> void:
    var scene: PackedScene = load("res://main.tscn")
    expect(scene != null, "actual native PackedScene loads")
    var game := scene.instantiate()
    root.add_child(game)
    await process_frame
    await process_frame
    var state = game.get_node("GameState")
    var choices = game.get_node("Choices")
    expect(game.get_node("Dialogue").text.contains("passage"), "native addon produced first dialogue")
    expect(choices.get_child_count() == 2, "two branching response buttons")
    expect(not choices.get_child(0).disabled and not choices.get_child(1).disabled, "initial decisions allowed")
    choices.get_child(0).pressed.emit()
    await process_frame
    await process_frame
    expect(state.unlocked and state.tokens == 0, "upstream dialogue mutation reached authoritative game state")
    expect(game.get_node("Status").text.contains("OPEN"), "UI observed authoritative state")
    expect(game.get_node("Dialogue").text.contains("unlocked"), "chosen narrative branch rendered")
    var other := scene.instantiate()
    root.add_child(other)
    await process_frame
    await process_frame
    other.get_node("Choices").get_child(1).pressed.emit()
    await process_frame
    await process_frame
    expect(not other.get_node("GameState").unlocked, "alternative narrative branch does not unlock")
    expect(other.get_node("GameState").tokens == 1, "alternative narrative branch preserves token")
    var locked := scene.instantiate()
    root.add_child(locked)
    await process_frame
    locked.get_node("GameState").tokens = 0
    locked.show_line("start")
    await process_frame
    await process_frame
    expect(locked.get_node("Choices").get_child(0).disabled, "zero-token conditional option disabled")
    game.queue_free()
    other.queue_free()
    locked.queue_free()
    await process_frame
    await process_frame
    print("GAME_NATIVE_DIALOGUE_COMPOSITION_PASS checks=%d" % checks)
    quit(0)
