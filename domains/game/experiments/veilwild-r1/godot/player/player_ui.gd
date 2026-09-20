class_name VeilwildPlayerUI
extends Control
## A25/F18 bounded HUD/settings implementation.
## It intentionally contains no target/world-position API and no raw hidden-state display.

const ALLOWED_FEEDBACK_CLASSES: Array[StringName] = [
	&"TRACE",
	&"THREAT_RESPONSE",
	&"OBSERVATION_PROGRESS",
	&"SUCCESS_CONSEQUENCE",
]
const REQUIRED_ONBOARDING_ACTIONS: Array[StringName] = [&"MOVE", &"LOOK", &"OBSERVE"]
const REMAP_ACTIONS: Array[StringName] = [
	&"vw_move_forward",
	&"vw_move_back",
	&"vw_move_left",
	&"vw_move_right",
	&"vw_look_left",
	&"vw_look_right",
	&"vw_look_up",
	&"vw_look_down",
	&"vw_observe",
	&"vw_settings",
	&"vw_pointer_capture",
	&"vw_cancel",
]
const REMAP_BUTTON_NAMES: Array[StringName] = [
	&"RemapForward",
	&"RemapBack",
	&"RemapLeft",
	&"RemapRight",
	&"RemapLookLeft",
	&"RemapLookRight",
	&"RemapLookUp",
	&"RemapLookDown",
	&"RemapObserve",
	&"RemapSettings",
	&"RemapCapture",
	&"RemapCancel",
]
const F22_SOURCE_FRONT := "A25/F18"

@onready var onboarding_panel: PanelContainer = %OnboardingPanel
@onready var onboarding_text: Label = %OnboardingText
@onready var feedback_panel: PanelContainer = %FeedbackPanel
@onready var feedback_text: Label = %FeedbackText
@onready var observation_progress: ProgressBar = %ObservationProgress
@onready var settings_panel: PanelContainer = %SettingsPanel
@onready var settings_help: Label = $SettingsPanel/SettingsScroll/SettingsBox/SettingsHelp
@onready var horizontal_sensitivity_slider: HSlider = %HorizontalSensitivitySlider
@onready var vertical_sensitivity_slider: HSlider = %VerticalSensitivitySlider
@onready var fov_slider: HSlider = %FovSlider
@onready var invert_x_check: CheckBox = %InvertXCheck
@onready var invert_y_check: CheckBox = %InvertYCheck
@onready var observe_mode: OptionButton = %ObserveMode
@onready var ui_scale_slider: HSlider = %UiScaleSlider
@onready var close_settings_button: Button = %CloseSettingsButton

var _ui_scale_factor := 1.0
var _demonstrated: Dictionary = {}
var _player: Node = null
var _pending_remap_action: StringName = &""

func _ready() -> void:
	add_to_group("veilwild.player_ui")
	_player = get_tree().get_first_node_in_group("veilwild.player_runtime")
	if _player != null:
		_player.connect("action_demonstrated", mark_action_demonstrated)
		_player.connect("action_binding_changed", _on_action_binding_changed)
		_player.connect("settings_requested", toggle_settings)
	_wire_settings_controls()
	refresh_control_prompt()
	refresh_remap_buttons()
	set_ui_scale_factor(1.0)

func _unhandled_input(event: InputEvent) -> void:
	if not settings_panel.visible:
		return
	if event is InputEventKey and (event as InputEventKey).pressed and not (event as InputEventKey).echo:
		var key_event := event as InputEventKey
		if _pending_remap_action != &"":
			if event.is_action_pressed(&"vw_cancel") and _pending_remap_action != &"vw_cancel":
				_pending_remap_action = &""
				refresh_remap_buttons()
			else:
				var physical := key_event.physical_keycode if key_event.physical_keycode != KEY_NONE else key_event.keycode
				if _player != null and bool(_player.call("remap_action_to_physical_key", _pending_remap_action, physical)):
					_pending_remap_action = &""
					refresh_control_prompt()
					refresh_remap_buttons()
			get_viewport().set_input_as_handled()
			return
		if event.is_action_pressed(&"vw_cancel"):
			set_settings_visible(false)
			get_viewport().set_input_as_handled()

func set_onboarding_visible(visible: bool) -> void:
	onboarding_panel.visible = visible

func mark_action_demonstrated(action_id: StringName) -> void:
	if action_id not in REQUIRED_ONBOARDING_ACTIONS:
		return
	_demonstrated[action_id] = true
	for required in REQUIRED_ONBOARDING_ACTIONS:
		if not _demonstrated.has(required):
			return
	onboarding_panel.visible = false

func refresh_control_prompt() -> void:
	if _player == null:
		onboarding_text.text = "Move / Look / Observe controls unavailable"
		return
	var forward := String(_player.call("get_action_binding_label", &"vw_move_forward"))
	var back := String(_player.call("get_action_binding_label", &"vw_move_back"))
	var left := String(_player.call("get_action_binding_label", &"vw_move_left"))
	var right := String(_player.call("get_action_binding_label", &"vw_move_right"))
	var look_left := String(_player.call("get_action_binding_label", &"vw_look_left"))
	var look_right := String(_player.call("get_action_binding_label", &"vw_look_right"))
	var look_up := String(_player.call("get_action_binding_label", &"vw_look_up"))
	var look_down := String(_player.call("get_action_binding_label", &"vw_look_down"))
	var observe := String(_player.call("get_action_binding_label", &"vw_observe"))
	var settings := String(_player.call("get_action_binding_label", &"vw_settings"))
	var capture := String(_player.call("get_action_binding_label", &"vw_pointer_capture"))
	var cancel := String(_player.call("get_action_binding_label", &"vw_cancel"))
	onboarding_text.text = "Move: %s / %s / %s / %s   Look: Mouse or %s / %s / %s / %s   Observe: %s   Settings: %s   Capture: %s\nRead traces, motion, and sound; observation requires an intentional action." % [forward, left, back, right, look_left, look_up, look_down, look_right, observe, settings, capture]
	settings_help.text = "Keyboard: Tab/Shift+Tab moves focus. Enter/Space activates. %s closes/releases. Remap buttons capture one physical key." % cancel

func present_feedback(cue_class: StringName, progress_normalized: float = -1.0) -> bool:
	if cue_class not in ALLOWED_FEEDBACK_CLASSES:
		return false
	feedback_panel.visible = true
	observation_progress.visible = false
	match cue_class:
		&"TRACE":
			feedback_text.text = "Trace noticed"
		&"THREAT_RESPONSE":
			feedback_text.text = "Your approach is affecting the creature"
		&"OBSERVATION_PROGRESS":
			feedback_text.text = "Observing…"
			observation_progress.visible = true
			observation_progress.value = clamp(progress_normalized, 0.0, 1.0) * 100.0
			_publish_feedback_event(&"observation_progress", "F18.OBSERVATION_PROGRESS_PRESENTED", cue_class, clamp(progress_normalized, 0.0, 1.0))
		&"SUCCESS_CONSEQUENCE":
			feedback_text.text = "Observation recorded"
			_publish_feedback_event(&"success_consequence", "F18.SUCCESS_CONSEQUENCE_PRESENTED", cue_class, -1.0)
	return true

func clear_feedback() -> void:
	feedback_panel.visible = false
	observation_progress.visible = false
	feedback_text.text = ""

func toggle_settings() -> void:
	set_settings_visible(not settings_panel.visible)

func set_settings_visible(visible: bool) -> void:
	settings_panel.visible = visible
	_pending_remap_action = &""
	if _player != null:
		_player.call("set_gameplay_input_enabled", not visible)
		_player.call("set_pointer_captured", not visible)
	if visible:
		_sync_settings_from_player()
		close_settings_button.grab_focus()
	else:
		close_settings_button.release_focus()

func is_settings_visible() -> bool:
	return settings_panel.visible

func set_ui_scale_factor(factor: float) -> void:
	_ui_scale_factor = clamp(factor, 1.0, 2.0)
	var scaled_font_size := int(round(20.0 * _ui_scale_factor))
	for node in find_children("*", "Control", true, false):
		if node is Label or node is Button or node is CheckBox or node is OptionButton:
			(node as Control).add_theme_font_size_override("font_size", scaled_font_size)

func get_ui_scale_factor() -> float:
	return _ui_scale_factor

func get_feedback_contract() -> Dictionary:
	return {
		"allowedCueClasses": ALLOWED_FEEDBACK_CLASSES.map(func(value: StringName) -> String: return String(value)),
		"targetLocationInput": false,
		"hiddenStateInput": false,
		"baseTextPixels": 20,
		"currentTextPixels": int(round(20.0 * _ui_scale_factor)),
		"uiScaleRange": [1.0, 2.0],
		"opaqueBackingAvailable": true,
		"colorOnlyCriticalMeaning": false,
		"remappedPromptPropagation": true,
	}

func get_accessibility_ui_receipt() -> Dictionary:
	return {
		"textScalePercent": int(round(_ui_scale_factor * 100.0)),
		"baseTextPixels": 20,
		"criticalTextOpaqueBacking": true,
		"settingsKeyboardPath": "Remappable Settings action opens; focusable controls; remappable Cancel action or Close exits",
		"remapKeyboardPath": "Settings remap buttons capture one physical key per live semantic action, including Settings/Cancel/pointer capture/digital look",
		"digitalLookAlternativeMode": "SEMANTIC_DIGITAL_ACTIONS",
		"allLiveControlsRemappable": true,
		"promptReflectsRemap": true,
		"colorOnlyCriticalMeaning": false,
		"deliberateRapidFlashing": false,
	}

func refresh_remap_buttons() -> void:
	for index in range(REMAP_ACTIONS.size()):
		var button := get_node_or_null("%" + String(REMAP_BUTTON_NAMES[index])) as Button
		if button == null:
			continue
		var action_id := REMAP_ACTIONS[index]
		var binding := "Unbound" if _player == null else String(_player.call("get_action_binding_label", action_id))
		button.text = "%s: %s" % [_semantic_action_label(action_id), binding]
		if action_id == _pending_remap_action:
			button.text = "%s: press a key…" % _semantic_action_label(action_id)

func _wire_settings_controls() -> void:
	observe_mode.clear()
	observe_mode.add_item("Single press", 0)
	observe_mode.add_item("Hold", 1)
	observe_mode.add_item("Toggle", 2)
	horizontal_sensitivity_slider.value_changed.connect(_on_horizontal_sensitivity_changed)
	vertical_sensitivity_slider.value_changed.connect(_on_vertical_sensitivity_changed)
	fov_slider.value_changed.connect(_on_fov_changed)
	invert_x_check.toggled.connect(_on_inversion_changed.bind(true))
	invert_y_check.toggled.connect(_on_inversion_changed.bind(false))
	observe_mode.item_selected.connect(_on_observe_mode_selected)
	ui_scale_slider.value_changed.connect(_on_ui_scale_changed)
	close_settings_button.pressed.connect(func() -> void: set_settings_visible(false))
	for index in range(REMAP_ACTIONS.size()):
		var button := get_node_or_null("%" + String(REMAP_BUTTON_NAMES[index])) as Button
		if button != null:
			button.pressed.connect(_begin_remap.bind(REMAP_ACTIONS[index]))

func _sync_settings_from_player() -> void:
	if _player == null:
		return
	horizontal_sensitivity_slider.set_value_no_signal(float(_player.get("horizontal_look_sensitivity_multiplier")))
	vertical_sensitivity_slider.set_value_no_signal(float(_player.get("vertical_look_sensitivity_multiplier")))
	fov_slider.set_value_no_signal(float(_player.get("field_of_view_degrees")))
	invert_x_check.set_pressed_no_signal(bool(_player.get("invert_look_x")))
	invert_y_check.set_pressed_no_signal(bool(_player.get("invert_look_y")))
	observe_mode.select(int(_player.get("observe_activation_mode_index")))
	ui_scale_slider.set_value_no_signal(_ui_scale_factor)
	refresh_remap_buttons()

func _on_horizontal_sensitivity_changed(value: float) -> void:
	if _player != null:
		_player.call("set_look_sensitivity_multipliers", value, vertical_sensitivity_slider.value)

func _on_vertical_sensitivity_changed(value: float) -> void:
	if _player != null:
		_player.call("set_look_sensitivity_multipliers", horizontal_sensitivity_slider.value, value)

func _on_fov_changed(value: float) -> void:
	if _player != null:
		_player.call("set_camera_fov_degrees", value)

func _on_inversion_changed(_pressed: bool, _x_control: bool) -> void:
	if _player != null:
		_player.call("set_look_inversion", invert_x_check.button_pressed, invert_y_check.button_pressed)

func _on_observe_mode_selected(index: int) -> void:
	if _player == null:
		return
	var mode: StringName = [&"SINGLE_PRESS", &"HOLD", &"TOGGLE"][clampi(index, 0, 2)]
	_player.call("set_observe_activation_mode", mode)

func _on_ui_scale_changed(value: float) -> void:
	set_ui_scale_factor(value)

func _begin_remap(action_id: StringName) -> void:
	_pending_remap_action = action_id
	refresh_remap_buttons()

func _on_action_binding_changed(_action_id: StringName, _binding_label: String) -> void:
	refresh_control_prompt()
	refresh_remap_buttons()

func _semantic_action_label(action_id: StringName) -> String:
	match action_id:
		&"vw_move_forward": return "Forward"
		&"vw_move_back": return "Back"
		&"vw_move_left": return "Left"
		&"vw_move_right": return "Right"
		&"vw_look_left": return "Look left"
		&"vw_look_right": return "Look right"
		&"vw_look_up": return "Look up"
		&"vw_look_down": return "Look down"
		&"vw_observe": return "Observe"
		&"vw_settings": return "Settings"
		&"vw_pointer_capture": return "Capture pointer"
		&"vw_cancel": return "Cancel / release"
	return String(action_id)

func _publish_feedback_event(event_type: StringName, producer_semantic_id: String, cue_class: StringName, scalar: float) -> void:
	var bus := get_node_or_null("/root/VeilwildEventBus")
	if bus == null or not bus.has_method("publish"):
		return
	var payload := {
		"sourceFront": F22_SOURCE_FRONT,
		"producerSemanticId": producer_semantic_id,
		"cueClass": String(cue_class),
	}
	if scalar >= 0.0:
		payload["scalar"] = scalar
	bus.call("publish", event_type, payload, &"A25/F18")
