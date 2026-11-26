extends "res://encounter_rules.gd"

# Mission topology is product data, not another combat kernel.
const DIRECT := [1, 3, 4]
const GRADUAL := [1, 2, 2, 3]
const TRIAL = preload("res://configs/tactical_trial.tres")

func route_rooms(id: String) -> Array:
    match id:
        "direct": return DIRECT.duplicate()
        "gradual": return GRADUAL.duplicate()
    return []

func route_tuning(id: String) -> Resource:
    var rooms := route_rooms(id)
    if rooms.is_empty():
        return null
    var t: Resource = TRIAL.duplicate(true)
    t.enemies_per_room = PackedInt32Array(rooms)
    return t

func reset_run(replacement: Resource = null) -> bool:
    if replacement != null:
        return false
    return super.reset_run(route_tuning("direct"))

func restart_run() -> bool:
    return reset_run()

func route_id() -> String:
    if _active == null or room <= 1:
        return "undecided"
    return "gradual" if _active.enemies_per_room == PackedInt32Array(GRADUAL) else "direct"

func can_choose() -> bool:
    return room == 1 and phase == "cleared"

func advance() -> bool:
    if route_id() == "undecided":
        return false
    return super.advance()

func choose_route(id: String) -> bool:
    var selected := route_rooms(id)
    if not can_choose() or selected.is_empty():
        return false
    # Both admitted routes have the exact common prefix and identical combat
    # tuning. Only the future room schedule changes. super.advance owns the
    # single state_changed event, with the new route already authoritative.
    _active.enemies_per_room = PackedInt32Array(selected)
    return super.advance()

# This product intentionally does not offer persistence. Do not accept
# arbitrary inherited checkpoints as a substitute for branch admission.
func restore_checkpoint(_saved: Variant) -> bool:
    return false
