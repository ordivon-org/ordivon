extends VBoxContainer

# One Dialogue Manager semantic-choice port shared by Human UI and Agent.
# Response IDs and eligibility remain upstream Dialogue Manager facts.
signal response_settled(response_id: String)
var available_responses: Dictionary = {}

func choose_response(response_id: String) -> bool:
    if not visible:
        return false
    var response: Dictionary = available_responses.get(response_id, {})
    if not response.get("allowed", false):
        return false
    if response_id == "unlock" and gate.tokens <= 0:
        return false
    available_responses.clear()
    # The actual next_id is returned by Dialogue Manager, never invented by
    # Game or reconstructed from its resource-specific internal string.
    call_deferred("show_line", response["next_id"])
    return true


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
        available_responses.clear()
        for child in choices.get_children():
            child.queue_free()
        line_text.text = ""

func show_line(key: String) -> void:
    generation += 1
    var own_generation: int = generation
    var line: DialogueLine = await DialogueManager.get_next_dialogue_line(
        dialogue, key, [{"game": gate}])
    if not is_inside_tree() or generation != own_generation:
        response_settled.emit(key)
        return
    available_responses.clear()
    for child in choices.get_children():
        child.queue_free()
    if line == null:
        line_text.text = "END"
        response_settled.emit(key)
        return
    line_text.text = line.text
    for response: DialogueResponse in line.responses:
        var button := Button.new()
        button.text = response.text
        button.disabled = not response.is_allowed
        choices.add_child(button)
        var semantic_id: String = response.get_tag_value("intent")
        var target_id: String = semantic_id if not semantic_id.is_empty() else response.next_id
        available_responses[target_id] = {
            "allowed": response.is_allowed,
            "next_id": response.next_id
        }
        button.pressed.connect(func(): choose_response(target_id))
    response_settled.emit(key)
