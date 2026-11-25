extends SceneTree

func _initialize() -> void:
    call_deferred("observe")

func observe() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 1:
        quit(2)
        return
    var parsed: Variant = JSON.parse_string(args[0])
    if not parsed is Array or parsed.is_empty() or parsed.size() > 40:
        quit(2)
        return
    var results: Array = []
    for mode in ["classic", "trial"]:
        var rules = preload("res://encounter_rules.gd").new()
        root.add_child(rules)
        var events: Array = []
        rules.state_changed.connect(func(s: Dictionary) -> void:
            events.append(["state", s.duplicate(true)]))
        rules.action_accepted.connect(func(a: String) -> void:
            events.append(["action", a]))
        var ok: bool = rules.reset_run(load("res://configs/tactical_trial.tres") if mode == "trial" else null)
        if not ok:
            rules.free()
            quit(2)
            return
        var initial: Dictionary = rules.snapshot()
        var initial_events: Array = events.duplicate(true)
        var saved: Dictionary = rules.checkpoint()
        var steps: Array = []
        for action in parsed:
            events.clear()
            var before: Dictionary = rules.snapshot()
            var accepted: bool = false
            match action:
                "attack": accepted = rules.attack()
                "guard": accepted = rules.guard()
                "advance": accepted = rules.advance()
                "restart": accepted = rules.restart_run()
                "checkpoint":
                    saved = rules.checkpoint()
                    accepted = true
                "restore": accepted = rules.restore_checkpoint(saved)
                "invalid_restore":
                    var bad: Dictionary = saved.duplicate(true)
                    bad["state"]["turn"] = -1
                    accepted = rules.restore_checkpoint(bad)
                _:
                    rules.free()
                    quit(2)
                    return
            steps.append({"action": action, "before": before, "after": rules.snapshot(),
                "accepted": accepted, "events": events.duplicate(true)})
        results.append({"mode": mode, "initial": initial, "initial_events": initial_events, "steps": steps})
        rules.free()
    print("GAME_NATIVE_TRACE_OBSERVATION=" + JSON.stringify(results))
    quit(0)
