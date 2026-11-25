extends RefCounted

# Product-specific state machine. No scene, timers, input, audio or RNG.
enum Event { NONE, PICKED_UP, DELIVERED, WON }
const CONTACT_RADIUS_SQUARED: float = 34.0 * 34.0

var _phase: String = "ready"
var _delivered: int = 0
var _carrying: bool = false
var _elapsed_seconds: int = 0
var _sites: PackedVector2Array
var _depot: Vector2
var _initial_interval: float

var phase: String:
    get: return _phase
var delivered: int:
    get: return _delivered
var carrying: bool:
    get: return _carrying
var elapsed_seconds: int:
    get: return _elapsed_seconds
var total: int:
    get: return _sites.size()
var depot: Vector2:
    get: return _depot

func configure(plan: RelayPlan) -> bool:
    return _phase == "ready" and _capture_plan(plan)

func _capture_plan(plan: RelayPlan) -> bool:
    if plan == null or plan.pickup_sites.size() < 3:
        return false
    if not plan.depot.is_finite() or not is_finite(plan.initial_enemy_interval) or plan.initial_enemy_interval <= 0.0:
        return false
    for site in plan.pickup_sites:
        if not site.is_finite():
            return false
    _sites = plan.pickup_sites.duplicate()
    _depot = plan.depot
    _initial_interval = plan.initial_enemy_interval
    return true

func start(plan: RelayPlan) -> bool:
    if not _capture_plan(plan):
        return false
    _delivered = 0
    _carrying = false
    _elapsed_seconds = 0
    _phase = "playing"
    return true

func next_pickup() -> Vector2:
    return _sites[_delivered] if _delivered < total else _sites[0]

func enemy_interval() -> float:
    if _delivered == 0:
        return _initial_interval
    return maxf(0.36, _initial_interval - float(_delivered) * 0.16)

func step_position(position: Vector2) -> Event:
    if _phase != "playing":
        return Event.NONE
    if not _carrying and position.distance_squared_to(next_pickup()) <= CONTACT_RADIUS_SQUARED:
        _carrying = true
        return Event.PICKED_UP
    if _carrying and position.distance_squared_to(_depot) <= CONTACT_RADIUS_SQUARED:
        _carrying = false
        _delivered += 1
        if _delivered == total:
            _phase = "won"
            return Event.WON
        return Event.DELIVERED
    return Event.NONE

func lose() -> bool:
    if _phase != "playing":
        return false
    _phase = "lost"
    return true

func tick() -> bool:
    if _phase != "playing":
        return false
    _elapsed_seconds += 1
    return true
