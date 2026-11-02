extends SceneTree

var failures: Array[String] = []
var assertions: int = 0

func expect(ok: bool, description: String) -> void:
    assertions += 1
    if not ok:
        failures.append(description)
        push_error(description)

func _initialize() -> void:
    call_deferred("run_native_audio_consumer")

func run_native_audio_consumer() -> void:
    var scene = load("res://main.tscn").instantiate()
    root.add_child(scene)
    var rules: Node = scene.get_node("Rules")
    var feedback: AudioStreamPlayer = scene.get_node("MovementAudio")
    var initial_clip = AudioStreamWAV.load_from_file("res://assets/kenney-ui-audio/click1.wav")
    var alternate_clip = AudioStreamWAV.load_from_file("res://assets/kenney-ui-audio/click2.wav")
    expect(initial_clip != null and alternate_clip != null, "source-licensed Kenney WAV clips load via native Godot")
    if initial_clip == null or alternate_clip == null:
        quit(1)
        return
    expect(feedback.stream != null, "real startup scene installs its own audio resource and event binding")
    expect(feedback.stream.get_data() == initial_clip.get_data(), "startup uses exact source-licensed click WAV")
    expect(feedback.observed_play_count == 0, "initial state notification does not mint movement feedback")
    expect(not rules.move(0), "invalid action is rejected by existing rules")
    expect(feedback.observed_play_count == 0, "rejected action produces no sound effect")
    expect(InputMap.has_action("move_right") and InputMap.has_action("move_left"), "project-native InputMap defines gameplay actions")
    var right = InputEventKey.new()
    right.pressed = true
    right.physical_keycode = KEY_RIGHT
    Input.parse_input_event(right)
    await process_frame
    expect(rules.snapshot()["turn"] == 1, "physical RIGHT key traverses native input dispatch to game rules")
    expect(feedback.observed_play_count == 1, "actual rule state signal triggers native audio")
    expect(feedback.playing, "AudioStreamPlayer playback starts")
    feedback.stream = alternate_clip
    expect(feedback.stream == alternate_clip, "source-licensed audio can be substituted independently")
    Input.parse_input_event(right)
    await process_frame
    expect(rules.snapshot()["turn"] == 2, "audio substitution leaves mapped RIGHT action unchanged")
    expect(feedback.observed_play_count == 2, "second state transition is observed")
    expect(feedback.stream == alternate_clip and feedback.playing, "new audio resource is used by the same player")
    var before = rules.snapshot()
    expect(not rules.move(100), "invalid action after substitution is rejected")
    expect(feedback.observed_play_count == 2 and rules.snapshot() == before, "invalid action produces neither rules nor audio effect")
    # Change the actual engine InputMap, not any Rule/View/Audio script.
    var d_key = InputEventKey.new()
    d_key.pressed = true
    d_key.physical_keycode = KEY_D
    InputMap.action_erase_events("move_right")
    InputMap.action_add_event("move_right", d_key)
    var before_remap = rules.snapshot()
    var audio_before_remap = feedback.observed_play_count
    Input.parse_input_event(right)
    await process_frame
    expect(rules.snapshot() == before_remap and feedback.observed_play_count == audio_before_remap, "removed key binding no longer changes game/audio")
    Input.parse_input_event(d_key)
    await process_frame
    expect(rules.snapshot()["turn"] == before_remap["turn"] + 1, "remapped physical D key enters same gameplay rule")
    expect(feedback.observed_play_count == audio_before_remap + 1, "remapped action retains native sound feedback")
    InputMap.load_from_project_settings()
    var left = InputEventKey.new()
    left.pressed = true
    left.physical_keycode = KEY_LEFT
    var before_left = rules.snapshot()
    var audio_before_left = feedback.observed_play_count
    Input.parse_input_event(left)
    await process_frame
    expect(rules.snapshot()["x"] == before_left["x"] - 1 and rules.snapshot()["turn"] == before_left["turn"] + 1, "native LEFT action uses same rule port after input mapping restoration")
    expect(feedback.observed_play_count == audio_before_left + 1, "native LEFT action reuses one movement audio consumer")

    # Reuse the existing native MovementAudio; no competing audio manager.
    var button: TextureButton = scene.get_node("View/MoveRightButton")
    expect(button.texture_normal is ImageTexture, "pinned Kenney UI sprite is a native TextureButton texture")
    if button.texture_normal is ImageTexture:
        expect(button.texture_normal.get_size() == Vector2(192.0, 64.0), "source-licensed Kenney sprite has pinned native size")
    var before_button: Dictionary = rules.snapshot()
    var board_before: String = scene.get_node("View/Board").text
    var audio_before: int = feedback.observed_play_count
    button.pressed.emit()
    expect(rules.snapshot()["x"] == before_button["x"] + 1, "native Kenney button action enters actual existing grid rules")
    expect(feedback.observed_play_count == audio_before + 1, "button-driven rule transition reuses existing MovementAudio feedback")
    expect(scene.get_node("View/Board").text != board_before, "button-driven rule transition updates native visible board")
    print("GAME_NATIVE_AUDIO_COMPOSITION_%s assertions=%d played=%d" % ["PASS" if failures.is_empty() else "FAIL", assertions, feedback.observed_play_count])
    feedback.stop()
    feedback.stream = null
    scene.free()
    initial_clip = null
    alternate_clip = null
    await create_timer(0.15).timeout
    quit(0 if failures.is_empty() else 1)
