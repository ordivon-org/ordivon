extends Control

@onready var game: Node = $GameState
@onready var line_text: Label = $Dialogue
@onready var choices: HBoxContainer = $Choices
@onready var status: Label = $Status
var resource: DialogueResource = preload("res://gate.dialogue")

func _ready() -> void:
    game.state_changed.connect(render_state)
    render_state()
    show_line("start")

func render_state() -> void:
    status.text = "Tokens: %d | Gate: %s" % [game.tokens, "OPEN" if game.unlocked else "CLOSED"]

func show_line(key: String) -> void:
    var line: DialogueLine = await DialogueManager.get_next_dialogue_line(resource, key, [{"game": game}])
    for child in choices.get_children():
        child.queue_free()
    if line == null:
        line_text.text = "END"
        return
    line_text.text = line.text
    for response: DialogueResponse in line.responses:
        var choice := Button.new()
        choice.text = response.text
        choice.disabled = not response.is_allowed
        choices.add_child(choice)
        choice.pressed.connect(func(): show_line(response.next_id))
