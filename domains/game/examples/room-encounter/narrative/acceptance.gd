extends SceneTree
var checks: int = 0
var failures: Array[String] = []
func expect(ok: bool, why: String) -> void:
    checks += 1
    if not ok:
        failures.append(why)
        push_error(why)

# Input.parse_input_event dispatches through the *real* Godot viewport,
# including native GUI focus/consumption before _unhandled_key_input.
func send_native_key(code: Key) -> void:
    var down := InputEventKey.new()
    down.keycode = code
    down.physical_keycode = code
    down.pressed = true
    Input.parse_input_event(down)
    Input.flush_buffered_events()
    await process_frame
    var up := InputEventKey.new()
    up.keycode = code
    up.physical_keycode = code
    up.pressed = false
    Input.parse_input_event(up)
    Input.flush_buffered_events()
    await process_frame

# Pass a native Godot action through the same Viewport event queue;
# direct action dispatch does not claim an operating-system keyboard event.
func send_ui_accept() -> void:
    var down := InputEventAction.new()
    down.action = &"ui_accept"
    down.pressed = true
    Input.parse_input_event(down)
    Input.flush_buffered_events()
    await process_frame
    var up := InputEventAction.new()
    up.action = &"ui_accept"
    up.pressed = false
    Input.parse_input_event(up)
    Input.flush_buffered_events()
    await process_frame

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
    expect(gate.choose_response("unlock"), "semantic Unlock choice is legal")
    await gate.response_settled
    expect(rules.snapshot()["room"] == 2, "dialogue unlock invokes actual legal room advance")
    expect(not gate.visible, "dialogue hidden after transition")
    expect(not gate.choose_response("unlock"), "cannot reselect Unlock outside cleared state")
    expect(audio.observed_play_count == 1, "dialogue does not fake combat audio")
    expect(rules.attack() and rules.attack(), "room two still playable")
    await process_frame
    await process_frame
    expect(gate.visible, "dialogue re-appears on next cleared room")
    var cleared: Dictionary = rules.snapshot()
    expect(rules.reset_run(), "native rules reset")
    await process_frame
    expect(not gate.visible and rules.snapshot() != cleared, "reset hides narrative")
    # Hidden presentation is not authorization to bypass the real Dialogue
    # Manager Unlock choice. The only passage effect is the gate's native
    # semantic response and subsequent passage_advanced event.
    expect(rules.attack(), "fresh native encounter clears before hidden-gate test")
    await process_frame
    await process_frame
    var before_hidden_gate: Dictionary = rules.snapshot().duplicate(true)
    gate.hide()
    product.get_node("View/Actions/Next").pressed.emit()
    await process_frame
    await process_frame
    expect(rules.snapshot() == before_hidden_gate,
        "hidden gate cannot turn Open Door into a direct Rules.advance bypass")
    expect(gate.visible, "Open Door restores cleared-room native dialogue presentation")
    if gate.visible and rules.snapshot()["phase"] == "cleared":
        if gate.available_responses.is_empty():
            await gate.response_settled
        expect(gate.choose_response("unlock"), "restored gate admits actual semantic Unlock")
        await gate.response_settled
        expect(rules.snapshot()["room"] == 2,
            "only semantic Unlock can commit passage after hidden-gate recovery")
    # Actual keyboard routing, not emitting Buttons or calling request_door
    # directly. GUI focus must not grant premature room progression.
    expect(rules.reset_run(), "keyboard ingress starts in a fresh room")
    await process_frame
    var fighting_before: Dictionary = rules.snapshot().duplicate(true)
    await send_native_key(KEY_N)
    expect(rules.snapshot() == fighting_before,
        "native N key cannot open a closed room")
    expect(not gate.visible, "N does not reveal gate while still fighting")
    expect(rules.attack(), "real Rules clear the room for keyboard admission")
    await process_frame
    await process_frame
    var ready_before: Dictionary = rules.snapshot().duplicate(true)
    var settled_keys: Array[String] = []
    gate.response_settled.connect(func(key: String): settled_keys.append(key))
    gate.hide()
    var gen_before_n: int = gate.generation
    await send_native_key(KEY_N)
    for step in range(24):
        if not settled_keys.is_empty():
            break
        await process_frame
    expect(rules.snapshot() == ready_before,
        "real N input requests Open Door without advancing Rules")
    expect(gate.visible and gate.generation > gen_before_n,
        "N actually reaches root input and restores hidden gate")
    expect(settled_keys.size() >= 1 and settled_keys[-1] == "start",
        "N restores a settled, real Dialogue Manager start choice")
    expect(gate.get_node("Choices").get_child_count() == 2,
        "native N leaves the real Unlock/Leave choices visible")
    var commits: Array[int] = [0]
    gate.get_node("GameState").passage_advanced.connect(func(): commits[0] += 1)
    var next_button: Button = product.get_node("View/Actions/Next")
    next_button.grab_focus()
    await process_frame
    expect(root.gui_get_focus_owner() == next_button,
        "native Open Door is the currently focused GUI Button")
    var enter_event := InputEventKey.new()
    enter_event.keycode = KEY_ENTER
    enter_event.physical_keycode = KEY_ENTER
    enter_event.pressed = true
    expect(enter_event.is_action("ui_accept"),
        "real native Return key is admitted by built-in Godot UI accept mapping")
    var next_presses: Array[int] = [0]
    next_button.pressed.connect(func(): next_presses[0] += 1)
    var settled_before_enter: int = settled_keys.size()
    await send_ui_accept()
    expect(not Input.is_action_pressed("ui_accept"),
        "native UI accept release clears focused GUI action state")
    for step in range(24):
        if settled_keys.size() > settled_before_enter:
            break
        await process_frame
    expect(rules.snapshot() == ready_before and commits[0] == 0,
        "focused Open Door ui_accept never auto-Unlocks")
    expect(settled_keys.size() > settled_before_enter and next_presses[0] == 1,
        "native focused Open Door Button handles ui_accept and reopens Dialogue")
    var unlock_choice: Button
    for node in gate.get_node("Choices").get_children():
        if node is Button and node.text.contains("Unlock"):
            unlock_choice = node
            break
    expect(unlock_choice != null and not unlock_choice.disabled,
        "real semantic Unlock choice remains keyboard-accessible")
    if unlock_choice != null:
        var unlock_presses: Array[int] = [0]
        unlock_choice.pressed.connect(func(): unlock_presses[0] += 1)
        unlock_choice.grab_focus()
        await process_frame
        expect(root.gui_get_focus_owner() == unlock_choice,
            "native GUI focus reaches the real semantic Unlock Button")
        await send_ui_accept()
        for step in range(24):
            if commits[0] > 0:
                break
            await process_frame
        expect(unlock_presses[0] == 1,
            "native ui_accept presses the real focused Unlock Button once")
        expect(rules.snapshot()["room"] == 2 and commits[0] == 1,
            "focused Unlock ui_accept commits one passage through native GUI")
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
