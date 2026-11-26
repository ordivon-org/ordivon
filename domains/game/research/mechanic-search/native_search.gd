extends RefCounted

# Native rule traversal; no parallel simulation or domain authority.
const MAX_DEPTH = 48
const CAP = 100000

func state_key(s: Dictionary, exact: bool) -> String:
    return "%d/%d/%d/%d/%d/%s/%d" % [s.room, s.foes, s.enemy_health,
        s.player_health, s.stamina, s.phase, s.turn if exact else s.turn % 3]

func apply_action(rules: Node, action: String) -> bool:
    match action:
        "attack": return rules.attack()
        "guard": return rules.guard()
        "advance": return rules.advance()
    return false

func path_to(nodes: Array, index: int) -> Array:
    var path: Array = []
    while nodes[index].parent >= 0:
        path.push_front(nodes[index].action)
        index = nodes[index].parent
    return path

func replay(rules: Node, tuning: Resource, path: Array) -> Dictionary:
    if not rules.reset_run(tuning):
        return {}
    for action in path:
        if not apply_action(rules, action):
            return {}
    return rules.snapshot()

func search(rules: Node, tuning: Resource, horizon: int, exact: bool) -> Dictionary:
    if not rules.reset_run(tuning):
        return {"error": "reset failed"}
    var initial: Dictionary = rules.checkpoint()
    var identity: Dictionary = initial.tuning
    var nodes: Array = [{"state": initial.state, "parent": -1, "action": "", "depth": 0}]
    var seen: Dictionary = {state_key(initial.state, exact): true}
    var best: Dictionary = {}
    var transitions := 0
    var cursor := 0
    var lost := 0
    var horizon_nodes := 0
    while cursor < nodes.size():
        var row: Dictionary = nodes[cursor]
        var state: Dictionary = row.state
        if state.phase == "won":
            if not best.has(state.player_health):
                best[state.player_health] = cursor
        elif state.phase == "lost":
            lost += 1
        elif row.depth == horizon:
            horizon_nodes += 1
        else:
            var available: Array = ["advance"] if state.phase == "cleared" else ["guard"]
            if state.phase == "fighting" and state.stamina >= state.attack_cost:
                available.push_front("attack")
            for action in available:
                if not rules.restore_checkpoint({"tuning": identity, "state": state}):
                    return {"error": "restore rejected"}
                if not apply_action(rules, action):
                    return {"error": "legal action rejected"}
                transitions += 1
                var next: Dictionary = rules.checkpoint().state
                var key := state_key(next, exact)
                if not seen.has(key):
                    if nodes.size() >= CAP:
                        return {"error": "state cap exceeded"}
                    seen[key] = true
                    nodes.append({"state": next, "parent": cursor, "action": action, "depth": row.depth + 1})
        cursor += 1
    var healths: Array = best.keys()
    healths.sort()
    healths.reverse()
    var frontier: Array = []
    var shortest := horizon + 1
    for hp in healths:
        var idx: int = best[hp]
        var depth: int = nodes[idx].depth
        if depth < shortest:
            var path := path_to(nodes, idx)
            var actual := replay(rules, tuning, path)
            var stored: Dictionary = nodes[idx].state
            if actual.is_empty() or actual.phase != "won" or actual.player_health != hp or actual.turn != stored.turn:
                return {"error": "witness replay differs"}
            shortest = depth
            frontier.append({"health": hp, "actions": depth, "turns": actual.turn, "path": path})
    return {"states": nodes.size(), "transitions": transitions, "lost_states": lost,
        "horizon_states": horizon_nodes, "frontier": frontier, "horizon": horizon, "exact": exact}

func policy(rules: Node, tuning: Resource, forecast: bool) -> Dictionary:
    if not rules.reset_run(tuning):
        return {"error": "reset"}
    var path: Array = []
    while path.size() < MAX_DEPTH:
        var s: Dictionary = rules.snapshot()
        if s.phase in ["won", "lost"]:
            break
        var action := "advance" if s.phase == "cleared" else "attack"
        if s.phase == "fighting" and (s.stamina < s.attack_cost or
                (forecast and s.has("forecast") and s.forecast.charged)):
            action = "guard"
        if not apply_action(rules, action):
            return {"error": "policy action rejected"}
        path.append(action)
    var final: Dictionary = rules.snapshot()
    return {"phase": final.phase, "health": final.player_health, "turns": final.turn,
        "actions": path.size(), "path": path}

func guard_cycle(rules: Node, tuning: Resource) -> Dictionary:
    if not rules.reset_run(tuning):
        return {"error": "reset"}
    var before: Dictionary = rules.snapshot()
    var path: Array = ["guard", "guard", "guard"]
    for action in path:
        if not apply_action(rules, action):
            return {"error": "guard rejected"}
    var after: Dictionary = rules.snapshot()
    return {"before": before, "after": after, "path": path,
        "same_quotient": state_key(before, false) == state_key(after, false)}

func signature(result: Dictionary) -> Array:
    var out: Array = []
    for point in result.frontier:
        out.append([point.health, point.actions])
    return out
