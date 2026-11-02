extends SceneTree
var checks: int = 0
var failures: Array[String] = []
func expect(ok: bool, why: String) -> void:
    checks += 1
    if not ok:
        failures.append(why)
        push_error(why)

func _initialize() -> void:
    call_deferred("run_product")

func run_product() -> void:
    var scene: PackedScene = load("res://main.tscn")
    expect(scene != null, "native integrated scene loads")
    if scene == null:
        quit(1)
        return
    var product := scene.instantiate()
    root.add_child(product)
    await process_frame
    await process_frame
    var rules = product.get_node("Rules")
    var gate = product.get_node("GateDialogue")
    var audio = product.get_node("EncounterAudio")
    expect(rules.snapshot()["phase"] == "fighting", "real room combat starts")
    expect(not gate.visible, "narrative hidden during combat")
    expect(rules.attack(), "first native enemy defeated")
    await process_frame
    await process_frame
    expect(rules.snapshot()["phase"] == "cleared", "first room cleared")
    expect(gate.visible and gate.get_node("Line").text.contains("passage"), "native dialogue gate after real clear")
    var choices = gate.get_node("Choices")
    expect(choices.get_child_count() == 2, "native dialogue two choices")
    expect(not choices.get_child(0).disabled, "real cleared gate eligible")
    var before: Dictionary = rules.snapshot()
    product.get_node("View/Actions/Next").pressed.emit()
    await process_frame
    await process_frame
    expect(rules.snapshot() == before, "door button requires narrative choice")
    choices.get_child(1).pressed.emit()
    await process_frame
    await process_frame
    expect(rules.snapshot() == before, "leave choice preserves room game")
    expect(gate.get_node("Line").text.contains("another time"), "leave narrative rendered")
    gate.show_line("start")
    await process_frame
    await process_frame
    choices.get_child(0).pressed.emit()
    await process_frame
    await process_frame
    expect(rules.snapshot()["room"] == 2, "dialogue unlock invokes actual legal room advance")
    expect(not gate.visible, "dialogue hidden after transition")
    expect(audio.observed_play_count == 1, "dialogue does not fake combat audio")
    expect(rules.attack() and rules.attack(), "room two still playable")
    await process_frame
    await process_frame
    expect(gate.visible, "dialogue re-appears on next cleared room")
    var cleared: Dictionary = rules.snapshot()
    expect(rules.reset_run(), "native rules reset")
    await process_frame
    expect(not gate.visible and rules.snapshot() != cleared, "reset hides narrative")
    audio.stop()
    audio.stream = null
    product.free()
    await create_timer(0.15).timeout
    if failures.is_empty():
        print("GAME_INTEGRATED_ROOM_DIALOGUE_PASS checks=%d" % checks)
        quit(0)
    else:
        print("GAME_INTEGRATED_ROOM_DIALOGUE_FAIL checks=%d fails=%d" % [checks,failures.size()])
        quit(1)
