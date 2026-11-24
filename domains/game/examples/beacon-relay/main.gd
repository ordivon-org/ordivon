extends Node

# Adapted over the upstream official Godot Player, Mob, scene and audio.
@export var mob_scene: PackedScene
@export var relay_plan: RelayPlan

var phase: String = "ready"
var delivered: int = 0
var carrying: bool = false
var elapsed_seconds: int = 0
const CONTACT_RADIUS: float = 34.0

func _ready() -> void:
    assert(relay_plan != null and relay_plan.pickup_sites.size() >= 3)
    $HUD.update_score(0, relay_plan.pickup_sites.size())
    $HUD.update_time(0)
    $HUD.set_status("WASD / arrows. Collect amber cores; return to green depot.")
    $RelaySites.set_route(relay_plan.pickup_sites[0], relay_plan.depot, false, false)

func new_game() -> void:
    get_tree().call_group(&"mobs", &"queue_free")
    $ScoreTimer.stop()
    $MobTimer.stop()
    $StartTimer.stop()
    delivered = 0
    carrying = false
    elapsed_seconds = 0
    phase = "playing"
    $Player.speed = 400
    $Player.start($StartPosition.position)
    $HUD.update_score(0, relay_plan.pickup_sites.size())
    $HUD.update_time(0)
    $HUD.set_status("CORE 1: touch the amber beacon.")
    $RelaySites.set_route(relay_plan.pickup_sites[0], relay_plan.depot, false, true)
    $MobTimer.wait_time = relay_plan.initial_enemy_interval
    $StartTimer.start()
    $HUD.show_message("GO!")
    $Music.play()

func _physics_process(_delta: float) -> void:
    if phase != "playing" or not $Player.visible:
        return
    var current: Vector2 = $Player.position
    if not carrying and current.distance_to(relay_plan.pickup_sites[delivered]) <= CONTACT_RADIUS:
        carrying = true
        $Player.speed = 330
        $RelaySites.set_route(relay_plan.pickup_sites[delivered], relay_plan.depot, true, true)
        $HUD.set_status("CARRYING CORE %d: return to GREEN depot." % [delivered + 1])
        $HUD.show_message("CORE SECURED")
    elif carrying and current.distance_to(relay_plan.depot) <= CONTACT_RADIUS:
        carrying = false
        delivered += 1
        $Player.speed = 400
        $HUD.update_score(delivered, relay_plan.pickup_sites.size())
        if delivered == relay_plan.pickup_sites.size():
            _finish(true)
            return
        $MobTimer.wait_time = maxf(0.36, relay_plan.initial_enemy_interval - float(delivered) * 0.16)
        if not $MobTimer.is_stopped():
            $MobTimer.start()
        $RelaySites.set_route(relay_plan.pickup_sites[delivered], relay_plan.depot, false, true)
        $HUD.set_status("CORE %d: touch the NEXT amber beacon." % [delivered + 1])
        $HUD.show_message("DELIVERED %d / %d" % [delivered, relay_plan.pickup_sites.size()])

func game_over() -> void:
    if phase == "playing":
        _finish(false)

func _finish(won: bool) -> void:
    if phase != "playing":
        return
    phase = "won" if won else "lost"
    $StartTimer.stop()
    $ScoreTimer.stop()
    $MobTimer.stop()
    $Music.stop()
    $Player.hide()
    $RelaySites.set_route(relay_plan.pickup_sites[0], relay_plan.depot, false, false)
    if won:
        $HUD.set_status("All signal cores delivered. Relay restored!")
        $HUD.show_result("RELAY RESTORED!\n%d SECONDS" % elapsed_seconds)
    else:
        $DeathSound.play()
        $HUD.set_status("Signal lost after %d deliveries. Try again." % delivered)
        $HUD.show_result("SIGNAL LOST\nTRY AGAIN")

func _on_MobTimer_timeout() -> void:
    if phase != "playing":
        return
    var mob = mob_scene.instantiate()
    var spawn = get_node(^"MobPath/MobSpawnLocation")
    spawn.progress_ratio = randf()
    mob.position = spawn.position
    var direction: float = spawn.rotation + PI / 2.0 + randf_range(-PI / 4.0, PI / 4.0)
    mob.rotation = direction
    mob.linear_velocity = Vector2(randf_range(150.0, 250.0), 0.0).rotated(direction)
    add_child(mob)

func _on_ScoreTimer_timeout() -> void:
    if phase == "playing":
        elapsed_seconds += 1
        $HUD.update_time(elapsed_seconds)

func _on_StartTimer_timeout() -> void:
    if phase == "playing":
        $MobTimer.start()
        $ScoreTimer.start()
