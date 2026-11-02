extends Node

# Single owner of encounter state; UI is a read-only observer.
const Tuning = preload("res://encounter_tuning.gd")
signal state_changed(state: Dictionary)
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
    return true

func guard() -> bool:
    if phase != "fighting":
        return false
    stamina = mini(active.stamina_capacity, stamina + active.guard_restore)
    turn += 1
    _retaliate(active.guard_block)
    state_changed.emit(snapshot())
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
