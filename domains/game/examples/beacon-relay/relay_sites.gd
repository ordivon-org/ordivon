extends Node2D

# Native Godot draw API; no world-state or collision authority here.
var pickup: Vector2
var depot: Vector2
var carrying: bool = false
var active: bool = false

func set_route(next_pickup: Vector2, home: Vector2, has_core: bool, enabled: bool) -> void:
    pickup = next_pickup
    depot = home
    carrying = has_core
    active = enabled
    queue_redraw()

func _draw() -> void:
    if not active:
        return
    draw_circle(depot, 38.0, Color(0.1, 0.55, 0.37, 0.37))
    draw_arc(depot, 37.0, 0.0, TAU, 64, Color(0.45, 0.96, 0.72), 4.5, true)
    draw_line(depot + Vector2(-11, 0), depot + Vector2(11, 0), Color(0.9, 1.0, 0.95), 3.0, true)
    draw_line(depot + Vector2(0, -11), depot + Vector2(0, 11), Color(0.9, 1.0, 0.95), 3.0, true)
    if not carrying:
        var points := PackedVector2Array([
            pickup + Vector2(0, -24), pickup + Vector2(22, 0),
            pickup + Vector2(0, 24), pickup + Vector2(-22, 0)
        ])
        draw_colored_polygon(points, Color(0.98, 0.75, 0.2))
        draw_arc(pickup, 30.0, 0.0, TAU, 48, Color(1.0, 0.91, 0.45), 2.5, true)
