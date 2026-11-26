extends SceneTree

const Search = preload("res://native_search.gd")
const SELECTED = [1, 2, 2, 3]

func _initialize() -> void:
    call_deferred("run")

func evaluate(rules: Node, engine: RefCounted, base: Resource, rooms: Array, reference: bool) -> Dictionary:
    var tuning := base.duplicate(true)
    tuning.enemies_per_room = PackedInt32Array(rooms)
    var reduced: Dictionary = engine.search(rules, tuning, 48, false)
    if reduced.has("error"):
        return reduced
    var row := {"rooms": rooms, "reduced": reduced,
        "attack_first": engine.policy(rules, tuning, false),
        "forecast_aware": engine.policy(rules, tuning, true)}
    if row.attack_first.has("error") or row.forecast_aware.has("error"):
        return {"error": "policy failure"}
    if reference:
        var exact: Dictionary = engine.search(rules, tuning, 48, true)
        if exact.has("error"):
            return exact
        if engine.signature(exact) != engine.signature(reduced):
            return {"error": "reference frontier mismatch"}
        row["exact"] = exact
    if rooms == SELECTED and not reduced.frontier.is_empty():
        if not rules.reset_run(tuning):
            return {"error": "selected tuning rejected"}
        var identity: Dictionary = rules.checkpoint().tuning
        if ResourceSaver.save(tuning, "res://selected.tres") != OK:
            return {"error": "ResourceSaver failed"}
        var restored: Resource = ResourceLoader.load("res://selected.tres", "", ResourceLoader.CACHE_MODE_IGNORE)
        if not rules.reset_run(restored) or rules.checkpoint().tuning != identity:
            return {"error": "generated Resource semantics differ"}
    return row

func run() -> void:
    var rules: Node = preload("res://encounter_rules.gd").new()
    root.add_child(rules)
    var base: Resource = load("res://configs/tactical_trial.tres")
    var engine := Search.new()
    var cases: Array = [[2,3,3]]
    for a in range(1,4):
        for b in range(1,4):
            for c in range(1,4):
                for d in range(1,4):
                    if a+b+c+d == 8:
                        cases.append([a,b,c,d])
    var rows: Array = []
    for rooms in cases:
        var row := evaluate(rules, engine, base, rooms, rooms == [2,3,3] or rooms == SELECTED)
        if row.has("error"):
            push_error(str(rooms) + ": " + row.error)
            rules.free()
            quit(1)
            return
        rows.append(row)
    rules.free()
    print("CONTENT_SEARCH=" + JSON.stringify(rows))
    quit(0)
