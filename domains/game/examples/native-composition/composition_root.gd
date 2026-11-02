extends Control

# Native PackedScene is the swappable presentation LEGO.
# Game rules know nothing about the chosen presentation.
@export var view_scene: PackedScene = preload("res://grid_state_view.tscn")
@onready var rules: Node = $Rules
@onready var movement_audio: AudioStreamPlayer = $MovementAudio
var view: VBoxContainer

func _ready() -> void:
    view = view_scene.instantiate()
    view.name = "View"
    add_child(view)
    # The view owns presentation. This root connects optional player input
    # to the existing rules; sound stays in the already-owned MovementAudio.
    var move_right_button: TextureButton = view.get_node_or_null("MoveRightButton")
    if move_right_button != null:
        var image: Image = Image.load_from_file("res://assets/kenney-ui-art/button_rectangle_depth_border.png")
        if image != null and not image.is_empty():
            move_right_button.texture_normal = ImageTexture.create_from_image(image)
        move_right_button.pressed.connect(func() -> void: rules.move(1))
    rules.state_changed.connect(view.render_state)
    movement_audio.stream = AudioStreamWAV.load_from_file("res://assets/kenney-ui-audio/click1.wav")
    movement_audio.bind_rules(rules)
    rules.reset_game()

func _unhandled_key_input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_RIGHT:
            rules.move(1)
            get_viewport().set_input_as_handled()
        elif event.keycode == KEY_LEFT:
            rules.move(-1)
            get_viewport().set_input_as_handled()
