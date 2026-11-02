extends VBoxContainer

# Room rules own all legality. Presentation and transient choices are local.
@onready var gate: Node = $GameState
@onready var line_text: Label = $Line
@onready var choices: HBoxContainer = $Choices
@onready var status: Label = $Status
var dialogue: DialogueResource = preload("res://narrative/gate.dialogue")
var rules: Node
var last_phase: String = ""
var last_room: int = -1
var generation: int = 0

func bind_rules(source: Node) -> void:
    rules = source
    gate.bind_rules(rules)
    rules.state_changed.connect(_on_state_changed)
    _on_state_changed(rules.snapshot())

func _on_state_changed(s: Dictionary) -> void:
    var cleared: bool = s["phase"] == "cleared"
    var fresh: bool = cleared and (last_phase != "cleared" or last_room != int(s["room"]))
    last_phase = s["phase"]
    last_room = int(s["room"])
    visible = cleared
    status.text = "Room %d | gate tokens %d" % [s["room"], gate.tokens]
    if fresh:
        show_line("start")
    elif not cleared:
        generation += 1
        for child in choices.get_children():
            child.queue_free()
        line_text.text = ""

func show_line(key: String) -> void:
    generation += 1
    var own_generation: int = generation
    var line: DialogueLine = await DialogueManager.get_next_dialogue_line(
        dialogue, key, [{"game": gate}])
    if not is_inside_tree() or generation != own_generation:
        return
    for child in choices.get_children():
        child.queue_free()
    if line == null:
        line_text.text = "END"
        return
    line_text.text = line.text
    for response: DialogueResponse in line.responses:
        var button := Button.new()
        button.text = response.text
        button.disabled = not response.is_allowed
        choices.add_child(button)
        button.pressed.connect(func(): show_line(response.next_id))
