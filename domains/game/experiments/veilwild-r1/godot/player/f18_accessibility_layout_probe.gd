extends SceneTree

var failures: Array[String] = []

func _init() -> void:
	call_deferred("_run")

func _expect(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func _run() -> void:
	root.size = Vector2i(1920, 1080)
	var player_scene := load("res://player/player_runtime.tscn") as PackedScene
	var ui_scene := load("res://player/player_ui.tscn") as PackedScene
	_expect(player_scene != null, "player scene missing")
	_expect(ui_scene != null, "ui scene missing")
	if player_scene == null or ui_scene == null:
		_finish()
		return
	var player := player_scene.instantiate()
	root.add_child(player)
	var ui := ui_scene.instantiate()
	root.add_child(ui)
	await process_frame
	ui.call("set_ui_scale_factor", 2.0)
	ui.call("set_settings_visible", true)
	await process_frame
	await process_frame
	var settings_panel := ui.get_node("SettingsPanel") as Control
	var settings_box := ui.get_node("SettingsPanel/SettingsScroll/SettingsBox") as Control
	var min_size := settings_box.get_combined_minimum_size()
	var scroll := ui.get_node("SettingsPanel/SettingsScroll") as ScrollContainer
	var panel_size := settings_panel.size
	var panel_rect := settings_panel.get_global_rect()
	var viewport_rect := Rect2(Vector2.ZERO, Vector2(root.size))
	print("F18_LAYOUT_200 settings_panel=%s content_minimum=%s scroll=%s rect=%s" % [panel_size, min_size, scroll.size, panel_rect])
	_expect(min_size.x <= panel_size.x + 0.5, "200% settings minimum width exceeds panel width")
	_expect(scroll.size.y <= panel_size.y + 0.5, "settings scroll viewport exceeds panel height")
	_expect(min_size.y > scroll.size.y, "200% fixture does not exercise vertical scrolling pressure")
	_expect(viewport_rect.encloses(panel_rect), "200% settings panel extends beyond 1920x1080 viewport")
	for name in [
		"HorizontalSensitivitySlider", "VerticalSensitivitySlider", "FovSlider",
		"InvertXCheck", "InvertYCheck", "ObserveMode", "UiScaleSlider",
		"RemapForward", "RemapBack", "RemapLeft", "RemapRight",
		"RemapLookLeft", "RemapLookRight", "RemapLookUp", "RemapLookDown",
		"RemapObserve", "RemapSettings", "RemapCapture", "RemapCancel",
		"CloseSettingsButton",
	]:
		var control := ui.get_node("%" + name) as Control
		_expect(control != null and control.focus_mode != Control.FOCUS_NONE, "keyboard focus missing for %s" % name)
	_finish()

func _finish() -> void:
	if failures.is_empty():
		print("VEILWILD_F18_ACCESSIBILITY_LAYOUT_PASS scale=200 viewport=1920x1080")
		quit(0)
		return
	for failure in failures:
		push_error("VEILWILD_F18_ACCESSIBILITY_LAYOUT_FAILURE %s" % failure)
	print("VEILWILD_F18_ACCESSIBILITY_LAYOUT_FAIL count=%d" % failures.size())
	quit(1)
