extends AudioStreamPlayer

# Native sound response to a changed turn; the GridRules node alone owns moves.
var last_turn: int = 0
var observed_play_count: int = 0

func bind_rules(rules: Node) -> void:
    last_turn = int(rules.snapshot()["turn"])
    rules.state_changed.connect(_on_state_changed)

func _on_state_changed(next_state: Dictionary) -> void:
    var next_turn: int = int(next_state["turn"])
    var advanced: bool = next_turn > last_turn
    last_turn = next_turn
    if advanced and stream != null:
        play()
        observed_play_count += 1
