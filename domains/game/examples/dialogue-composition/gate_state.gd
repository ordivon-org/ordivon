extends Node
signal state_changed

var tokens: int = 1
var unlocked: bool = false

func spend_token() -> void:
    if tokens < 1 or unlocked:
        return
    tokens -= 1
    unlocked = true
    state_changed.emit()
