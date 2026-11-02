extends SceneTree

var failures: Array[String] = []
var checks: int = 0

func expect(ok: bool, label: String) -> void:
    checks += 1
    if not ok:
        failures.append(label)
        push_error(label)

func invariant(s: Dictionary) -> void:
    expect(s["room"] >= 1 and s["room"] <= s["total_rooms"], "room bounded")
    expect(s["foes"] >= 0, "foes nonnegative")
    expect(s["player_health"] >= 0, "player health bounded")
    expect(s["stamina"] >= 0, "stamina nonnegative")
    expect(s["enemy_health"] >= 0, "enemy health nonnegative")
    expect(s["phase"] in ["fighting", "cleared", "won", "lost"], "phase valid")

func _initialize() -> void:
    call_deferred("run_acceptance")

func run_acceptance() -> void:
    var packed = load("res://main.tscn")
    expect(packed is PackedScene, "real packed scene loads")
    if not packed is PackedScene:
        quit(1)
        return
    var game = packed.instantiate()
    root.add_child(game)
    var rules = game.get_node("Rules")
    var save_slot = game.get_node("SaveSlot")
    save_slot.slot_path = "user://game_room_encounter_acceptance.cfg"
    DirAccess.remove_absolute(ProjectSettings.globalize_path(save_slot.slot_path))
    var view = game.get_node("View")
    var audio = game.get_node("EncounterAudio")
    expect(audio.stream is AudioStream, "installed CC0 audio decodes as native AudioStream")
    expect(audio.observed_play_count == 0, "initial scene does not sound")
    var first = rules.snapshot()
    expect(first["phase"] == "fighting" and first["foes"] == 1, "native encounter starts")
    expect(view.get_node("Status").text.contains("ROOM 1/3"), "native UI observes initial state")
    expect(not rules.advance(), "closed room rejects door")
    expect(audio.observed_play_count == 0, "illegal door action produces no audio")
    expect(rules.snapshot() == first, "illegal transition preserves state")
    view.get_node("Actions/Attack").pressed.emit()
    expect(rules.snapshot()["phase"] == "cleared", "native button input reaches authoritative rules")
    expect(audio.observed_play_count == 1 and audio.playing, "button input to rules to sound")
    expect(view.get_node("Encounter").text.contains("CLEARED"), "UI observes clear by Signal")
    var first_clear: Dictionary = rules.snapshot().duplicate(true)
    view.get_node("Actions/Save").pressed.emit()
    expect(FileAccess.file_exists(save_slot.slot_path), "native ConfigFile saved current run")
    expect(view.get_node("Storage").text == "Run saved.", "save UI feedback")
    expect(rules.reset_run(), "restart before load")
    expect(rules.snapshot() != first_clear, "restart changes state")
    view.get_node("Actions/Load").pressed.emit()
    expect(rules.snapshot() == first_clear, "load resumes exact authoritative game state")
    expect(view.get_node("Storage").text == "Run resumed.", "load UI feedback")
    expect(audio.observed_play_count == 1, "restore is silent, unlike legal attack")
    expect(not rules.attack(), "cleared room cannot be attacked")
    expect(audio.observed_play_count == 1, "rejected combat action is silent")
    expect(rules.advance(), "advance enters next room")
    expect(audio.observed_play_count == 1, "door transition is silent")
    expect(rules.snapshot()["room"] == 2, "room index advances")
    expect(rules.attack() and rules.attack(), "second room has two defeatable enemies")
    expect(rules.snapshot()["phase"] == "cleared", "second room cleared")
    expect(rules.advance(), "third room entered")
    var guard_count: int = 0
    while rules.snapshot()["phase"] == "fighting" and guard_count < 8:
        if not rules.attack():
            expect(rules.guard(), "guard restores attack resource")
            guard_count += 1
    expect(rules.snapshot()["phase"] == "cleared", "default three-room run winnable")
    expect(rules.advance(), "final cleared door opens")
    expect(rules.snapshot()["phase"] == "won", "three room win achieved")
    expect(view.get_node("Encounter").text.contains("VICTORY"), "victory observed in UI")
    expect(not rules.guard(), "terminal rules reject combat action")

    var variant = load("res://configs/variant.tres")
    var replacement_clip = load("res://assets/click2.wav")
    expect(replacement_clip is AudioStream, "alternative licensed sound is available")
    audio.stream = replacement_clip
    expect(rules.reset_run(variant), "user resource replaces native tuning")
    expect(audio.stream == replacement_clip, "audio substitution keeps rule contract unchanged")
    expect(rules.snapshot()["total_rooms"] == 2, "user tuning changes room count")
    var variant_state: Dictionary = rules.snapshot()
    expect(not save_slot.load_rules(rules), "different tuning cannot consume old checkpoint")
    expect(rules.snapshot() == variant_state, "tuning mismatch is atomic")
    var before = rules.snapshot()
    var invalid = variant.duplicate(true)
    invalid.enemies_per_room = PackedInt32Array([0])
    var observed: Array[Dictionary] = []
    rules.state_changed.connect(func(s: Dictionary) -> void: observed.append(s))
    expect(not rules.reset_run(invalid), "invalid native resource is rejected")
    expect(rules.snapshot() == before and observed.is_empty(), "bad resource rejection is atomic")
    var owned = variant.duplicate(true)
    expect(rules.reset_run(owned), "valid caller-owned tuning accepted")
    owned.enemies_per_room = PackedInt32Array([9, 9, 9])
    expect(rules.snapshot()["total_rooms"] == 2, "active state is independent of mutated caller resource")

    var alternate = packed.instantiate()
    alternate.view_scene = load("res://encounter_view_variant.tscn")
    root.add_child(alternate)
    var replacement_view = alternate.get_node("View")
    expect(replacement_view.modulate.g > 0.9, "alternative Godot scene has independent rendering")
    replacement_view.get_node("Actions/Attack").pressed.emit()
    expect(alternate.get_node("Rules").snapshot()["phase"] == "cleared", "alternate button invokes unchanged rule action")
    expect(alternate.get_node("EncounterAudio").observed_play_count == 1, "alternate HUD retains sound consumer")
    expect(replacement_view.get_node("Encounter").text.contains("CLEARED"),
        "alternative view consumes native Signal")

    # 3^5 = 243 distinct bounded action sequences through the real rule node.
    for trace in range(243):
        expect(rules.reset_run(), "reset canonical resource")
        var code: int = trace
        for step in range(5):
            var action: int = code % 3
            code = floori(float(code) / 3.0)
            if action == 0:
                rules.attack()
            elif action == 1:
                rules.guard()
            else:
                rules.advance()
            invariant(rules.snapshot())

    var damaged := ConfigFile.new()
    damaged.set_value("run", "schema_version", 1)
    var bad_checkpoint: Dictionary = rules.checkpoint()
    bad_checkpoint["state"]["player_health"] = -1
    damaged.set_value("run", "checkpoint", bad_checkpoint)
    expect(damaged.save(save_slot.slot_path) == OK, "create damaged save")
    var before_bad_load: Dictionary = rules.snapshot()
    expect(not save_slot.load_rules(rules), "damaged save rejected")
    expect(rules.snapshot() == before_bad_load, "damaged save does not mutate game state")
    DirAccess.remove_absolute(ProjectSettings.globalize_path(save_slot.slot_path))

    audio.stop()
    audio.stream = null
    var alternate_audio: AudioStreamPlayer = alternate.get_node("EncounterAudio")
    alternate_audio.stop()
    alternate_audio.stream = null
    game.free()
    alternate.free()
    replacement_clip = null
    await create_timer(0.15).timeout
    if failures.is_empty():
        print("GAME_ROOM_ENCOUNTER_PASS assertions=%d traces=243" % checks)
        quit(0)
    else:
        print("GAME_ROOM_ENCOUNTER_FAIL failures=%d checks=%d" % [failures.size(), checks])
        quit(1)
