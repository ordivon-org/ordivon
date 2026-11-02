extends Control

@export var view_scene: PackedScene = preload("res://encounter_view.tscn")
@onready var rules: Node = $Rules
@onready var feedback: AudioStreamPlayer = $EncounterAudio
var view: VBoxContainer

func _ready() -> void:
    view = view_scene.instantiate()
    view.name = "View"
    add_child(view)
    view.get_node("Actions/Attack").pressed.connect(func(): rules.attack())
    view.get_node("Actions/Guard").pressed.connect(func(): rules.guard())
    view.get_node("Actions/Next").pressed.connect(func(): rules.advance())
    view.get_node("Actions/Restart").pressed.connect(func(): rules.reset_run())
    rules.state_changed.connect(view.render_state)
    feedback.bind_rules(rules)
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
            rules.advance()
        KEY_R:
            rules.reset_run()
        _:
            return
    get_viewport().set_input_as_handled()
