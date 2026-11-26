extends SceneTree

const MAX_DEPTH = 48
const CAP = 100000
const Search = preload("res://native_search.gd")

func _initialize() -> void:
    call_deferred("run")

func tuning_for(name: String) -> Resource:
    var t: Resource = load("res://configs/default.tres" if name == "classic" else
        "res://configs/tactical_trial.tres").duplicate(true)
    if name == "trial_block2":
        t.guard_block = 2
    if name == "trial_block2_hp53":
        t = load("res://configs/trial_block2_hp53.tres").duplicate(true)
    return t

func run() -> void:
    var rules: Node = preload("res://encounter_rules.gd").new()
    root.add_child(rules)
    var rows: Array = []
    var engine := Search.new()
    for name in ["classic", "trial", "trial_block2", "trial_block2_hp53"]:
        var tuning := tuning_for(name)
        var reduced := engine.search(rules, tuning, MAX_DEPTH, false)
        var exact := engine.search(rules, tuning, MAX_DEPTH, true)
        if reduced.has("error") or exact.has("error"):
            push_error("search failed %s %s %s" % [name, reduced.get("error", ""), exact.get("error", "")])
            rules.free()
            quit(1)
            return
        if engine.signature(reduced) != engine.signature(exact):
            push_error("quotient frontier differs %s" % name)
            rules.free()
            quit(1)
            return
        var greedy := engine.policy(rules, tuning, false)
        var aware := engine.policy(rules, tuning, true)
        if greedy.has("error") or aware.has("error"):
            rules.free()
            quit(1)
            return
        var cycle := engine.guard_cycle(rules, tuning)
        if cycle.has("error"):
            rules.free()
            quit(1)
            return
        rows.append({"case": name, "initial_health": tuning.player_health,
            "guard_block": tuning.guard_block, "enemy_damage": tuning.enemy_damage,
            "reduced": reduced, "exact": exact, "attack_first": greedy, "forecast_aware": aware,
            "guard_cycle": cycle})
    rules.free()
    print("GAME_MECHANIC_SEARCH=" + JSON.stringify(rows))
    quit(0)
