extends Control

@export var view_scene: PackedScene = preload("res://encounter_view.tscn")
@onready var rules: Node = $Rules
@onready var feedback: AudioStreamPlayer = $EncounterAudio
@onready var save_slot: Node = $SaveSlot
@onready var gate_dialogue: VBoxContainer = $GateDialogue
var view: VBoxContainer

func _ready() -> void:
    view = view_scene.instantiate()
    view.name = "View"
    add_child(view)
    view.get_node("Actions/Attack").pressed.connect(func(): rules.attack())
    view.get_node("Actions/Guard").pressed.connect(func(): rules.guard())
    view.get_node("Actions/Next").pressed.connect(request_door)
    view.get_node("Actions/Restart").pressed.connect(func(): rules.reset_run())
    view.get_node("Actions/Save").pressed.connect(save_run)
    view.get_node("Actions/Load").pressed.connect(load_run)
    rules.state_changed.connect(view.render_state)
    feedback.bind_rules(rules)
    gate_dialogue.bind_rules(rules)
    rules.reset_run()

func _unhandled_key_input(event: InputEvent) -> void:
    if not event is InputEventKey or not event.pressed or event.echo:
        return
    match event.keycode:
        KEY_A, KEY_SPACE:
            rules.attack()
        KEY_G:
            rules.guard()
        KEY_N, KEY_ENTER:
            request_door()
        KEY_R:
            rules.reset_run()
        KEY_S:
            save_run()
        KEY_L:
            load_run()
        _:
            return
    get_viewport().set_input_as_handled()

func save_run() -> void:
    view.get_node("Storage").text = "Run saved." if save_slot.save_rules(rules) else "Save failed."

func load_run() -> void:
    view.get_node("Storage").text = "Run resumed." if save_slot.load_rules(rules) else "No compatible save."

func request_door() -> void:
    if gate_dialogue.visible:
        gate_dialogue.show_line("start")
    else:
        rules.advance()
