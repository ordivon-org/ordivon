extends SceneTree
const Search = preload("res://native_search.gd")
const Rules = preload("res://encounter_rules.gd")
const Packed = preload("res://main.tscn")

func _initialize() -> void:
    call_deferred("run")

func need(ok: bool, message: String) -> bool:
    if not ok:
        push_error(message)
    return ok

func run() -> void:
    var game: Control = Packed.instantiate()
    root.add_child(game)
    var base := Rules.new()
    root.add_child(base)
    var search := Search.new()
    var rows: Array = []
    var initial: Dictionary = game.observe()
    var early: bool = not game.dispatch("direct") and not game.dispatch("advance") and game.observe() == initial
    if not need(early,"early choice had an effect"):
        quit(1)
        return
    for id in ["direct","gradual"]:
        var t: Resource = game.rules.route_tuning(id)
        var exact: Dictionary = search.search(base,t,48,true)
        var reduced: Dictionary = search.search(base,t,48,false)
        if not need(not exact.has("error") and not reduced.has("error"),"search failed"):
            quit(1)
            return
        if not need(not exact.frontier.is_empty() and search.signature(exact)==search.signature(reduced),"frontier mismatch"):
            quit(1)
            return
        var witness: Dictionary = exact.frontier[-1] # minimum actions
        if not game.dispatch("restart"):
            quit(1)
            return
        var path: Array = []
        var fork: Dictionary = {}
        var count: Array[int] = [0]
        var callback := func(_s): count[0]+=1
        game.rules.state_changed.connect(callback)
        for action in witness.path:
            var actual: String = action
            if action == "advance" and game.rules.can_choose():
                var before: Dictionary = game.observe()
                count[0]=0
                if not need(not game.dispatch("advance") and not game.dispatch("unknown") and
                    not game.rules.choose_route("unknown") and count[0]==0 and game.observe()==before,
                    "fork bypass or rejected effect"):
                    quit(1)
                    return
                actual=id
                # Use the real native Button signal, not a second test-only state transition.
                if not need(not game.buttons[id].disabled and game.buttons.advance.disabled,
                    "fork controls disagree"):
                    quit(1)
                    return
                game.buttons[id].pressed.emit()
                var after: Dictionary = game.observe()
                if not need(after.route==id and after.state.room==2 and count[0]==1 and
                    before.state.player_health==after.state.player_health and before.state.stamina==after.state.stamina and
                    before.state.turn==after.state.turn,"branch transition not atomic"):
                    quit(1)
                    return
                var stable: Dictionary = game.observe()
                if not need(not game.dispatch("direct") and not game.dispatch("gradual") and
                    not game.rules.restore_checkpoint(game.rules.checkpoint()) and game.observe()==stable and count[0]==1,
                    "duplicate selection or restore had an effect"):
                    quit(1)
                    return
                fork={"before":before,"after":after,"state_events":count[0]}
            else:
                if not need(game.dispatch(actual),"witness rejected"):
                    quit(1)
                    return
            path.append(actual)
        game.rules.state_changed.disconnect(callback)
        var last: Dictionary = game.observe()
        if not need(last.state.phase=="won" and last.state.player_health==witness.health and
            last.state.turn==witness.turns and last.encounter.begins_with("VICTORY"),
            "native scene terminal mismatch"):
            quit(1)
            return
        rows.append({"route":id,"rooms":game.rules.route_rooms(id),"exact":exact,"reduced":reduced,
            "witness":path,"fork":fork,"terminal":last})
    if not need(game.dispatch("restart") and game.observe()==initial,"restart not undecided"):
        quit(1)
        return
    game.free()
    base.free()
    print("ROUTE_SEARCH=" + JSON.stringify(rows))
    quit(0)
