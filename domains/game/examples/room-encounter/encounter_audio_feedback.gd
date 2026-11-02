extends AudioStreamPlayer

# Product-owned feedback; authoritative encounter state stays in Rules.
var previous_turn: int = 0
var observed_play_count: int = 0

func bind_rules(rules: Node) -> void:
    previous_turn = int(rules.snapshot()["turn"])
    rules.state_changed.connect(_on_state_changed)

func _on_state_changed(next_state: Dictionary) -> void:
    var current_turn: int = int(next_state["turn"])
    var accepted_action: bool = current_turn > previous_turn
    previous_turn = current_turn
    if accepted_action and stream != null:
        play()
        observed_play_count += 1
