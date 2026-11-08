extends CanvasLayer

signal start_game

func show_message(value: String) -> void:
    $MessageLabel.text = value
    $MessageLabel.show()
    $MessageTimer.start()

func show_result(value: String) -> void:
    $MessageTimer.stop()
    $MessageLabel.text = value
    $MessageLabel.show()
    $StartButton.text = "RETRY"
    $StartButton.show()
    $StartButton.grab_focus()

func update_score(value: int, total: int) -> void:
    $ScoreLabel.text = "CORES  %d / %d" % [value, total]

func update_time(value: int) -> void:
    $TimeLabel.text = "TIME  %ds" % value

func set_status(value: String) -> void:
    $StatusLabel.text = value

func _on_StartButton_pressed() -> void:
    $StartButton.hide()
    start_game.emit()

func _on_MessageTimer_timeout() -> void:
    $MessageLabel.hide()
