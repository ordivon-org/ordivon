extends Node2D

var frames := 0

func _ready() -> void:
    print("ORDIVON_GAME_COLD_START_BOOT")
    queue_redraw()

func _process(_delta: float) -> void:
    frames += 1
    if frames >= 3:
        print("ORDIVON_GAME_COLD_START_OK")
        get_tree().quit(0)

func _draw() -> void:
    draw_rect(Rect2(96, 96, 448, 168), Color(0.12, 0.18, 0.28, 1.0), true)
    draw_circle(Vector2(192, 180), 44.0, Color(0.35, 0.78, 0.70, 1.0))
    draw_circle(Vector2(448, 180), 44.0, Color(0.55, 0.62, 0.92, 1.0))
    draw_line(Vector2(236, 180), Vector2(404, 180), Color(0.82, 0.86, 0.93, 1.0), 6.0)
