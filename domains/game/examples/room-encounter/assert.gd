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
    expect(game is VBoxContainer and view.get_parent() == game,
        "Godot native VBoxContainer owns HUD and narrative layout")
    expect(view.get_index() < game.get_node("GateDialogue").get_index(),
        "native UI order places HUD above dialogue")
    expect(not rules.advance(), "closed room rejects door")
    expect(audio.observed_play_count == 0, "illegal door action produces no audio")
    expect(rules.snapshot() == first, "illegal transition preserves state")
    view.get_node("Actions/Attack").pressed.emit()
    expect(rules.snapshot()["phase"] == "cleared", "native button input reaches authoritative rules")
    expect(audio.observed_play_count == 1 and audio.playing, "button input to rules to sound")
    expect(view.get_node("Encounter").text.contains("CLEARED"), "UI observes clear by Signal")
    await process_frame
    expect(not view.get_node("Actions/Attack").has_focus(),
        "focus does not remain on disabled Attack after room clear")
    expect(game.get_node("GateDialogue").get_global_rect().position.y >=
        view.get_global_rect().end.y,
        "native Container places narrative under HUD without absolute-position overlap")
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

    # Machine-arithmetic consumer witness for formal/verify_room_arithmetic.py:
    # the native GDScript used to overflow before the fix, although tuning and
    # restored turns at INT64_MAX are admitted by the existing rules contract.
    var i64_max: int = 9223372036854775807
    var extremal: Resource = load("res://configs/default.tres").duplicate(true)
    extremal.stamina_capacity = i64_max
    extremal.guard_restore = 1
    extremal.enemy_damage = 0
    extremal.attack_damage = 1
    expect(rules.reset_run(extremal), "valid machine-int max stamina tuning is admitted")
    expect(rules.guard(), "native guard accepted at full maximal stamina")
    expect(rules.snapshot()["stamina"] == i64_max, "guard at capacity never overflows")

    var maximal_checkpoint: Dictionary = rules.checkpoint()
    maximal_checkpoint["state"]["turn"] = i64_max
    expect(rules.restore_checkpoint(maximal_checkpoint), "restored maximum turn is valid")
    expect(rules.guard(), "guard operates after restored maximum turn")
    expect(rules.snapshot()["turn"] == i64_max, "guard turn counter saturates without wrapping")
    expect(rules.attack(), "attack operates after restored maximum turn")
    expect(rules.snapshot()["turn"] == i64_max, "attack turn counter saturates without wrapping")
    expect(rules.snapshot()["stamina"] == i64_max - 2, "attack spends stamina without underflow")

    extremal.guard_restore = i64_max
    expect(rules.reset_run(extremal), "valid maximal stamina restoration accepted")
    expect(rules.attack(), "attack leaves capacity for maximum restoration")
    expect(rules.guard(), "native guard applies maximal restoration")
    expect(rules.snapshot()["stamina"] == i64_max, "maximal restoration is capped before addition")

    # Product Trial uses the same real Rule/Signal/HUD/SaveSlot seams.
    # A fixed-policy native game run is a mechanical reproducibility witness,
    # not a claim that real people enjoy this encounter.
    var tactical_button: Button = view.get_node("Actions/Trial")
    tactical_button.pressed.emit()
    expect(rules.snapshot()["foes"] == 2 and rules.snapshot()["enemy_health"] == 5,
        "trial button selects native Resource and starts a real tactical encounter")
    expect(view.get_node("Encounter").text.contains("NEXT FOE HIT"),
        "player HUD receives source-of-truth damage forecast")
    expect(rules.snapshot()["forecast"]["attack_health_loss"] == 3,
        "first risky attack has an explicit nonzero health forecast")
    expect(rules.snapshot()["forecast"]["guard_health_loss"] == 0,
        "guard blocks first ordinary enemy strike")
    expect(not rules.checkpoint()["state"].has("forecast"),
        "checkpoint excludes recomputable player-facing forecast")
    # In native action traces, the forecast must predict actual HP effect.
    var tactical_steps: int = 0
    var tactical_guards: int = 0
    var tactical_attacks: int = 0
    while rules.snapshot()["phase"] in ["fighting", "cleared"] and tactical_steps < 120:
        var current: Dictionary = rules.snapshot()
        if current["phase"] == "cleared":
            expect(rules.advance(), "real room transition in tactical Trial")
            continue
        var f: Dictionary = current["forecast"]
        # A blind "guard on every charged turn" policy was falsified:
        # it sometimes guarded when a killing attack would cancel retaliation.
        # Use the *actual* non-mutating native forecast as decision evidence.
        var choose_guard: bool = (current["stamina"] < f["attack_cost"]
            or (f["threat_damage"] > 3
                and f["guard_health_loss"] < f["attack_health_loss"]))
        var committed: bool = rules.guard() if choose_guard else rules.attack()
        expect(committed, "chosen native tactical action accepted")
        var after_tactical: Dictionary = rules.snapshot()
        expect(current["player_health"] - after_tactical["player_health"] ==
            f["guard_health_loss"] if choose_guard else
            current["player_health"] - after_tactical["player_health"] ==
            f["attack_health_loss"], "HUD damage prediction refines actual native result")
        if choose_guard:
            tactical_guards += 1
            expect(after_tactical["stamina"] - current["stamina"] == f["guard_stamina_gain"],
                "forecast guard stamina gain equals native result")
        else:
            tactical_attacks += 1
        tactical_steps += 1
    var tactical_final_hp: int = rules.snapshot()["player_health"]
    expect(rules.snapshot()["phase"] == "won",
        "telegraph-aware tactical policy can win the entire native Trial")
    expect(tactical_guards >= 3 and tactical_attacks >= 8,
        "Trial creates nontrivial attack/guard choices")
    expect(tactical_steps >= 20 and tactical_steps <= 120,
        "Trial has bounded nontrivial native combat length")
    # Restart remains within Trial: mode is not silently dropped on R.
    view.get_node("Actions/Restart").pressed.emit()
    expect(rules.snapshot()["enemy_health"] == 5 and rules.snapshot()["foes"] == 2,
        "restart retains selected tactical mode")
    # Native persistence works with Trial tuning, not the unrelated default.
    expect(save_slot.save_rules(rules), "tactical trial save through real ConfigFile")
    expect(rules.attack(), "modify tactical game after saving")
    expect(save_slot.load_rules(rules), "same-tuning tactical checkpoint restores")
    expect(rules.snapshot()["turn"] == 0, "trial restore exact authoritative turn")

    # Native control comparison: naive attack-if-possible policy vs explicitly
    # observing the third-turn telegraph. This is a bounded design hypothesis,
    # not a Human enjoyment, balance or statistical-significance claim.
    expect(game.start_tactical_trial(), "same tactical resource resets naive control")
    var naive_steps: int = 0
    while rules.snapshot()["phase"] in ["fighting", "cleared"] and naive_steps < 120:
        var naive: Dictionary = rules.snapshot()
        if naive["phase"] == "cleared":
            expect(rules.advance(), "naive Trial advances through same native rules")
            continue
        var naive_action: bool = rules.guard() if naive["stamina"] < naive["attack_cost"] else rules.attack()
        expect(naive_action, "naive tactical action accepted")
        naive_steps += 1
    var naive_final: Dictionary = rules.snapshot()
    print("GAME_TACTICAL_TRIAL_COMPARISON aware_hp=%d aware_actions=%d naive_phase=%s naive_hp=%d naive_actions=%d" %
        [tactical_final_hp, tactical_steps, naive_final["phase"], naive_final["player_health"], naive_steps])
    expect(tactical_final_hp > 0, "aware trial retains health after win")
    expect(tactical_final_hp > naive_final["player_health"] or
        naive_final["phase"] == "lost",
        "telegraph-aware native policy outperforms naive attack-first control")
    # Native policy divergence is a design falsification candidate; actual
    # Human player comprehension remains UNKNOWN.

    expect(view.get_node("Actions") is HFlowContainer,
        "native FlowContainer wraps expanded action list without custom layout")
    view.get_node("Actions/Classic").pressed.emit()
    expect(rules.snapshot()["foes"] == 1 and rules.snapshot()["enemy_health"] == 3,
        "Classic button returns to original game tuning")
    expect(view.get_node("Title").text.contains("ORIGINAL"),
        "Human-visible title reflects selected native mode")
    expect(not rules.snapshot().has("forecast"),
        "Classic keeps original snapshot schema without trial-only forecast")
    expect(view.get_node("Encounter").text == "ENCOUNTER: 1 foes | active enemy HP 3",
        "Classic keeps original brief HUD without trial telegraph")
    var original_classic: Resource = load("res://configs/default.tres").duplicate(true)
    original_classic.enemy_health = 100
    original_classic.attack_damage = 1
    original_classic.enemy_damage = 3
    original_classic.player_health = 50
    expect(not original_classic.tactical_trial, "Classic opt-in false in unchanged default tuning")
    expect(rules.reset_run(original_classic), "long Classic combat for regression checks")
    expect(rules.attack() and rules.attack(), "advance Classic turn to the third action")
    var hp_before_third: int = rules.snapshot()["player_health"]
    expect(rules.attack(), "third Classic attack accepted")
    expect(hp_before_third - rules.snapshot()["player_health"] == 3,
        "third Classic turn has no extra trial strike")
    expect(view.get_node("Actions/Attack").disabled,
        "Classic player-facing Attack disables at zero stamina; no stale early-return")
    expect(not view.get_node("Actions/Guard").disabled,
        "Classic still offers native Guard when Attack is exhausted")
    expect(rules.reset_run(original_classic), "prepare Classic guard comparison")
    expect(rules.attack() and rules.attack(), "two Classic attacks before guard")
    hp_before_third = rules.snapshot()["player_health"]
    expect(rules.guard(), "third Classic guard accepted")
    expect(hp_before_third - rules.snapshot()["player_health"] == 2,
        "third Classic guard keeps tuned block, not perfect trial parry")
    expect(not rules.checkpoint()["tuning"].has("tactical_trial"),
        "Classic checkpoint tuning remains backward compatible")
    expect(rules.reset_run(), "return to original fixture before bounded traces")

    # Run 3^5 bounded native traces under both historical Classic and Trial
    # without creating a second simulator. 486 total traces.
    var trace_trial: Resource = load("res://configs/tactical_trial.tres")
    for trial_variant in range(2):
        for trace in range(243):
            expect(rules.reset_run(trace_trial if trial_variant == 1 else null),
                "reset correct native recipe for bounded traces")
            var code: int = trace
            for step in range(5):
                var action: int = code % 3
                code = floori(float(code) / 3.0)
                var state_before: Dictionary = rules.snapshot()
                var result: bool = false
                if action == 0:
                    result = rules.attack()
                elif action == 1:
                    result = rules.guard()
                else:
                    result = rules.advance()
                var state_after: Dictionary = rules.snapshot()
                if result and state_before["phase"] == "fighting" and action < 2 and state_before.has("forecast"):
                    var prediction: Dictionary = state_before["forecast"]
                    var key: String = "attack_health_loss" if action == 0 else "guard_health_loss"
                    expect(state_before["player_health"] - state_after["player_health"] ==
                        prediction[key], "every accepted native action obeys its pre-action forecast")
                invariant(state_after)

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
        print("GAME_ROOM_ENCOUNTER_PASS assertions=%d traces=486" % checks)
        quit(0)
    else:
        print("GAME_ROOM_ENCOUNTER_FAIL failures=%d checks=%d" % [failures.size(), checks])
        quit(1)
