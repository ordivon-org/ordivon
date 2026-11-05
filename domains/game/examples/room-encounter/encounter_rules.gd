extends Node

# Single owner of encounter state; UI is a read-only observer.
const Tuning = preload("res://encounter_tuning.gd")
signal state_changed(state: Dictionary)
signal action_accepted(action: String)
@export var tuning: Resource = preload("res://configs/default.tres")

var active: Resource
var room: int = 0
var foes: int = 0
var enemy_health: int = 0
var player_health: int = 0
var stamina: int = 0
var turn: int = 0
var phase: String = "uninitialized"

func accepts(candidate: Resource) -> bool:
    if not candidate is Tuning:
        return false
    if candidate.enemies_per_room.size() < 1 or candidate.enemies_per_room.size() > 8:
        return false
    for count in candidate.enemies_per_room:
        if count < 1 or count > 12:
            return false
    return (candidate.player_health > 0 and candidate.enemy_health > 0
        and candidate.attack_damage > 0 and candidate.enemy_damage >= 0
        and candidate.stamina_capacity > 0 and candidate.attack_cost > 0
        and candidate.attack_cost <= candidate.stamina_capacity
        and candidate.guard_restore > 0 and candidate.guard_block >= 0)

func reset_run(replacement: Resource = null) -> bool:
    var selected: Resource = replacement if replacement != null else tuning
    if not accepts(selected):
        return false
    active = selected.duplicate(true)
    room = 1
    foes = active.enemies_per_room[0]
    enemy_health = active.enemy_health
    player_health = active.player_health
    stamina = active.stamina_capacity
    turn = 0
    phase = "fighting"
    state_changed.emit(snapshot())
    return true

func attack() -> bool:
    if phase != "fighting" or stamina < active.attack_cost:
        return false
    stamina -= active.attack_cost
    turn += 1
    enemy_health -= active.attack_damage
    if enemy_health <= 0:
        foes -= 1
        if foes == 0:
            phase = "cleared"
            enemy_health = 0
        else:
            enemy_health = active.enemy_health
    if phase == "fighting":
        _retaliate(0)
    state_changed.emit(snapshot())
    action_accepted.emit("attack")
    return true

func guard() -> bool:
    if phase != "fighting":
        return false
    stamina = mini(active.stamina_capacity, stamina + active.guard_restore)
    turn += 1
    _retaliate(active.guard_block)
    state_changed.emit(snapshot())
    action_accepted.emit("guard")
    return true

func advance() -> bool:
    if phase != "cleared":
        return false
    if room >= active.enemies_per_room.size():
        phase = "won"
    else:
        room += 1
        foes = active.enemies_per_room[room - 1]
        enemy_health = active.enemy_health
        phase = "fighting"
    state_changed.emit(snapshot())
    return true

func _retaliate(block: int) -> void:
    player_health = maxi(0, player_health - maxi(0, active.enemy_damage - block))
    if player_health == 0:
        phase = "lost"

func snapshot() -> Dictionary:
    return {
        "room": room,
        "total_rooms": active.enemies_per_room.size() if active != null else 0,
        "foes": foes,
        "enemy_health": enemy_health,
        "player_health": player_health,
        "stamina": stamina,
        "attack_cost": active.attack_cost if active != null else 0,
        "turn": turn,
        "phase": phase
    }

# Rule-owned checkpoint contract; ConfigFile alone owns storage bytes.
func checkpoint() -> Dictionary:
    return {"tuning": {
        "enemies_per_room": active.enemies_per_room,
        "player_health": active.player_health,
        "enemy_health": active.enemy_health,
        "attack_damage": active.attack_damage,
        "enemy_damage": active.enemy_damage,
        "stamina_capacity": active.stamina_capacity,
        "attack_cost": active.attack_cost,
        "guard_restore": active.guard_restore,
        "guard_block": active.guard_block
    }, "state": snapshot()}

func restore_checkpoint(saved: Variant) -> bool:
    if active == null or not saved is Dictionary:
        return false
    if not saved.has("tuning") or not saved.has("state"):
        return false
    if saved["tuning"] != checkpoint()["tuning"]:
        return false
    var s: Variant = saved["state"]
    if not s is Dictionary:
        return false
    for key in ["room", "total_rooms", "foes", "enemy_health",
            "player_health", "stamina", "attack_cost", "turn"]:
        if not s.has(key) or typeof(s[key]) != TYPE_INT:
            return false
    if not s.has("phase") or typeof(s["phase"]) != TYPE_STRING:
        return false
    var new_phase: String = s["phase"]
    if new_phase not in ["fighting", "cleared", "won", "lost"]:
        return false
    var new_room: int = s["room"]
    var new_foes: int = s["foes"]
    var new_enemy_health: int = s["enemy_health"]
    var new_player_health: int = s["player_health"]
    var new_stamina: int = s["stamina"]
    if new_room < 1 or new_room > active.enemies_per_room.size():
        return false
    if s["total_rooms"] != active.enemies_per_room.size() or s["attack_cost"] != active.attack_cost:
        return false
    if new_foes < 0 or new_foes > active.enemies_per_room[new_room - 1]:
        return false
    if new_enemy_health < 0 or new_enemy_health > active.enemy_health:
        return false
    if new_player_health < 0 or new_player_health > active.player_health:
        return false
    if new_stamina < 0 or new_stamina > active.stamina_capacity or s["turn"] < 0:
        return false
    if new_phase == "fighting" and (new_foes == 0 or new_enemy_health == 0 or new_player_health == 0):
        return false
    if new_phase == "cleared" and (new_foes != 0 or new_enemy_health != 0 or new_player_health == 0):
        return false
    if new_phase == "won" and (new_room != active.enemies_per_room.size() or
            new_foes != 0 or new_enemy_health != 0 or new_player_health == 0):
        return false
    if new_phase == "lost" and (new_player_health != 0 or new_foes == 0 or new_enemy_health == 0):
        return false
    room = new_room
    foes = new_foes
    enemy_health = new_enemy_health
    player_health = new_player_health
    stamina = new_stamina
    turn = s["turn"]
    phase = new_phase
    state_changed.emit(snapshot())
    return true
