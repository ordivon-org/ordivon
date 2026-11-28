extends Node

# Adapted over the upstream official Godot Player, Mob, scene and audio.
@export var mob_scene: PackedScene
@export var relay_plan: RelayPlan

const Rules = preload("res://relay_rules.gd")
var _rules = Rules.new()

# Read-only projections for the scene and existing native consumers.
var phase: String:
    get: return _rules.phase
var delivered: int:
    get: return _rules.delivered
var carrying: bool:
    get: return _rules.carrying
var elapsed_seconds: int:
    get: return _rules.elapsed_seconds

func _ready() -> void:
    if not _rules.configure(relay_plan):
        push_error("Invalid Beacon relay plan")
        return
    $HUD.update_score(0, _rules.total)
    $HUD.update_time(0)
    $HUD.set_status("WASD / arrows. Collect amber cores; return to green depot.")
    $RelaySites.set_route(_rules.next_pickup(), _rules.depot, false, false)

func new_game() -> void:
    if not _rules.start(relay_plan):
        push_error("Invalid Beacon relay plan")
        return
    get_tree().call_group(&"mobs", &"queue_free")
    $ScoreTimer.stop()
    $MobTimer.stop()
    $StartTimer.stop()
    $Player.speed = 400
    $Player.start($StartPosition.position)
    $HUD.update_score(0, _rules.total)
    $HUD.update_time(0)
    $HUD.set_status("CORE 1: touch the amber beacon.")
    $RelaySites.set_route(_rules.next_pickup(), _rules.depot, false, true)
    $MobTimer.wait_time = _rules.enemy_interval()
    $StartTimer.start()
    $HUD.show_message("GO!")
    $Music.play()

func _physics_process(_delta: float) -> void:
    if phase != "playing" or not $Player.visible:
        return
    match _rules.step_position($Player.position):
        Rules.Event.PICKED_UP:
            $Player.speed = 330
            $RelaySites.set_route(_rules.next_pickup(), _rules.depot, true, true)
            $HUD.set_status("CARRYING CORE %d: return to GREEN depot." % [delivered + 1])
            $HUD.show_message("CORE SECURED")
        Rules.Event.DELIVERED, Rules.Event.WON:
            $Player.speed = 400
            $HUD.update_score(delivered, _rules.total)
            if phase == "won":
                _finish(true)
                return
            $MobTimer.wait_time = _rules.enemy_interval()
            if not $MobTimer.is_stopped():
                $MobTimer.start()
            $RelaySites.set_route(_rules.next_pickup(), _rules.depot, false, true)
            $HUD.set_status("CORE %d: touch the NEXT amber beacon." % [delivered + 1])
            $HUD.show_message("DELIVERED %d / %d" % [delivered, _rules.total])

func game_over() -> void:
    if _rules.lose():
        _finish(false)

func _finish(won: bool) -> void:
    $StartTimer.stop()
    $ScoreTimer.stop()
    $MobTimer.stop()
    $Music.stop()
    $Player.hide()
    $RelaySites.set_route(_rules.next_pickup(), _rules.depot, false, false)
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
    if _rules.tick():
        $HUD.update_time(elapsed_seconds)

func _on_StartTimer_timeout() -> void:
    if phase == "playing":
        $MobTimer.start()
        $ScoreTimer.start()
