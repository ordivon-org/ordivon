extends Control

# Native PackedScene is the swappable presentation LEGO.
# Game rules know nothing about the chosen presentation.
@export var view_scene: PackedScene = preload("res://view.tscn")
@onready var rules: Node = $Rules
var view: VBoxContainer

func _ready() -> void:
    view = view_scene.instantiate()
    view.name = "View"
    add_child(view)
    rules.state_changed.connect(view.render_state)
    rules.reset_game()

func _unhandled_key_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_RIGHT:
            rules.move(1)
            get_viewport().set_input_as_handled()
        elif event.keycode == KEY_LEFT:
            rules.move(-1)
            get_viewport().set_input_as_handled()
