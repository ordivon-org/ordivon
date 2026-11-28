extends Control

@export var view_scene: PackedScene = preload("res://encounter_view.tscn")
@onready var rules: Node = $Rules
@onready var feedback: AudioStreamPlayer = $EncounterAudio
@onready var save_slot: Node = $SaveSlot
@onready var gate_dialogue: VBoxContainer = $GateDialogue
var view: VBoxContainer
const TACTICAL_TRIAL: Resource = preload("res://configs/tactical_trial.tres")

func start_tactical_trial() -> bool:
    return rules.reset_run(TACTICAL_TRIAL)

func start_classic_run() -> bool:
    return rules.reset_run()

func _project_mode_title(_state: Dictionary) -> void:
    # Mode title is a disposable projection of the admitted Rule Resource.
    # Direct Rule Resource substitution, Restart and restore all use this one
    # signal path, rather than maintaining a second mode/UI state ledger.
    view.render_mode_title(rules.is_tactical_trial())

func restart_run() -> void:
    # Rules owns the admitted tuning Resource. Do not shadow its mode in
    # the presentation/input adapter; a selected variant survives Restart.
    rules.restart_run()

func _ready() -> void:
    view = view_scene.instantiate()
    view.name = "View"
    add_child(view)
    # Keep the existing direct-child paths for all native and Agent consumers,
    # but let Godot's VBoxContainer stack HUD and Dialogue responsively.
    move_child(view, 0)
    view.get_node("Actions/Attack").grab_focus.call_deferred()
    view.get_node("Actions/Attack").pressed.connect(func(): rules.attack())
    view.get_node("Actions/Guard").pressed.connect(func(): rules.guard())
    view.get_node("Actions/Next").pressed.connect(request_door)
    view.get_node("Actions/Restart").pressed.connect(restart_run)
    view.get_node("Actions/Trial").pressed.connect(start_tactical_trial)
    view.get_node("Actions/Classic").pressed.connect(start_classic_run)
    view.get_node("Actions/Save").pressed.connect(save_run)
    view.get_node("Actions/Load").pressed.connect(load_run)
    rules.state_changed.connect(view.render_state)
    rules.state_changed.connect(_project_mode_title)
    # Strictly post-resolution UI feedback; Rule still owns the outcome.
    rules.action_accepted.connect(view.render_combat_result)
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
            restart_run()
        KEY_T:
            start_tactical_trial()
        KEY_C:
            start_classic_run()
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
    var loaded: bool = save_slot.load_rules(rules)
    if loaded:
        view.reset_action_feedback()
    view.get_node("Storage").text = "Run resumed." if loaded else "No compatible save."

func request_door() -> void:
    # Hidden/delayed dialogue is never authority to bypass native Unlock.
    # The semantic Dialogue Manager response alone drives the passage effect.
    if rules.snapshot()["phase"] != "cleared":
        return
    gate_dialogue.show()
    gate_dialogue.show_line("start")
