extends AudioStreamPlayer

# Explicit action event: restoration cannot masquerade as a new combat turn.
var observed_play_count: int = 0

func bind_rules(rules: Node) -> void:
    rules.action_accepted.connect(_on_action_accepted)

func _on_action_accepted(_action: String) -> void:
    if stream != null:
        play()
        observed_play_count += 1
