extends Node2D

const F0_DESIGN_RELATIVE := "../../pc01-causal-works-f0/design.json"
const F0_EVIDENCE_RELATIVE := "../../pc01-causal-works-f0/evidence/structural-falsifier-r1.json"
const ARCHITECTURES := ["source", "process", "route"]
const DIAGNOSTICS := ["none", "process", "route"]
const ARCH_LABELS := {"source": "SOURCE", "process": "PROCESS", "route": "ROUTE"}
const NODE_POSITIONS := {
    "source": Vector2(95, 244),
    "process": Vector2(305, 244),
    "route": Vector2(515, 244),
    "output": Vector2(760, 244),
}

var design: Dictionary = {}
var cycles: Array = []
var cycle_index := 0
var resolved_cycle_index := -1
var awaiting_next_cycle := false
var built_architecture := ""
var selected_architecture := ""
var selected_diagnostic := "none"
var inspection_performed := false
var inspection_diagnostic := "none"
var inspection_observation := "none"
var pending_cause := ""
var cumulative_score := 0
var replay: Array[String] = []
var last_aftermath := "No run committed yet."
var rng := RandomNumberGenerator.new()

var title_label: Label
var cycle_label: Label
var objective_label: Label
var context_label: Label
var symptom_label: Label
var built_label: Label
var diagnostic_picker: OptionButton
var inspect_button: Button
var commit_button: Button
var advance_button: Button
var inspection_label: Label
var aftermath_label: Label
var replay_label: Label
var architecture_buttons: Dictionary = {}

func _ready() -> void:
    var design_path := ProjectSettings.globalize_path("res://" + F0_DESIGN_RELATIVE)
    var raw := FileAccess.get_file_as_string(design_path)
    var parsed = JSON.parse_string(raw)
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("PC01-F1 could not parse F0 design: " + design_path)
        get_tree().quit(2)
        return
    design = parsed
    cycles = design["cycles"]
    rng.randomize()
    _build_ui()
    _refresh_ui()
    queue_redraw()
    if "--acceptance" in OS.get_cmdline_user_args():
        call_deferred("_run_acceptance")

func _build_ui() -> void:
    title_label = _label("PC01-F1 · CAUSAL WORKS", Vector2(24, 18), Vector2(500, 28), 22)
    cycle_label = _label("", Vector2(24, 52), Vector2(180, 22), 16)
    objective_label = _label("", Vector2(205, 52), Vector2(720, 22), 16)
    context_label = _label("", Vector2(24, 82), Vector2(910, 42), 14)
    context_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    symptom_label = _label("", Vector2(24, 125), Vector2(910, 42), 14)
    symptom_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART

    built_label = _label("", Vector2(24, 335), Vector2(355, 22), 14)
    _label("ARCHITECTURE", Vector2(24, 363), Vector2(140, 20), 13)
    for i in ARCHITECTURES.size():
        var arch: String = ARCHITECTURES[i]
        var button := Button.new()
        button.text = ARCH_LABELS[arch]
        button.position = Vector2(24 + i * 118, 388)
        button.size = Vector2(108, 34)
        button.toggle_mode = true
        button.pressed.connect(_select_architecture.bind(arch))
        add_child(button)
        architecture_buttons[arch] = button

    _label("DIAGNOSTIC · optional, cost " + str(int(design["diagnosticCost"])), Vector2(392, 363), Vector2(270, 20), 13)
    diagnostic_picker = OptionButton.new()
    diagnostic_picker.position = Vector2(392, 388)
    diagnostic_picker.size = Vector2(170, 34)
    diagnostic_picker.add_item("No scan")
    diagnostic_picker.add_item("Process scan")
    diagnostic_picker.add_item("Route scan")
    diagnostic_picker.item_selected.connect(_on_diagnostic_selected)
    add_child(diagnostic_picker)

    inspect_button = Button.new()
    inspect_button.text = "INSPECT"
    inspect_button.position = Vector2(570, 388)
    inspect_button.size = Vector2(104, 34)
    inspect_button.pressed.connect(_on_inspect_pressed)
    add_child(inspect_button)

    commit_button = Button.new()
    commit_button.text = "COMMIT & RUN"
    commit_button.position = Vector2(682, 388)
    commit_button.size = Vector2(138, 34)
    commit_button.pressed.connect(_on_commit_pressed)
    add_child(commit_button)

    advance_button = Button.new()
    advance_button.text = "NEXT CYCLE"
    advance_button.position = Vector2(828, 388)
    advance_button.size = Vector2(108, 34)
    advance_button.pressed.connect(_on_advance_pressed)
    advance_button.visible = false
    add_child(advance_button)

    inspection_label = _label("", Vector2(24, 429), Vector2(912, 20), 12)
    aftermath_label = _label("", Vector2(24, 451), Vector2(912, 30), 12)
    aftermath_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    replay_label = _label("", Vector2(24, 482), Vector2(912, 56), 11)
    replay_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART

func _label(text_value: String, at: Vector2, extent: Vector2, font_size: int) -> Label:
    var label := Label.new()
    label.text = text_value
    label.position = at
    label.size = extent
    label.add_theme_font_size_override("font_size", font_size)
    add_child(label)
    return label

func _objective_for(index: int) -> String:
    match index:
        0:
            return "OBJECTIVE · recover balanced output"
        1:
            return "OBJECTIVE SHIFT · route-sensitive delivery now dominates"
        2:
            return "RULE REVALUATION · source resilience now dominates"
        _:
            return "RUN COMPLETE"

func _context_tag(index: int) -> String:
    match index:
        0:
            return "baseline"
        1:
            return "objective-shift"
        2:
            return "rule-revaluation"
        _:
            return "complete"

func _persistence_status() -> String:
    var switch_cost := int(design["switchCost"])
    if built_architecture == "":
        return "FIRST BUILD 0"
    if selected_architecture == "":
        return "KEEP 0 / SWITCH -" + str(switch_cost)
    if selected_architecture == built_architecture:
        return "KEEP 0"
    return "SWITCH -" + str(switch_cost)

func _refresh_ui() -> void:
    var complete := cycle_index >= cycles.size()
    var interaction_locked := complete or awaiting_next_cycle
    if awaiting_next_cycle:
        var resolved_cycle: Dictionary = cycles[resolved_cycle_index]
        cycle_label.text = "CYCLE " + str(resolved_cycle_index + 1) + " / " + str(cycles.size()) + " RESOLVED"
        objective_label.text = _objective_for(resolved_cycle_index)
        context_label.text = "Resolved context: " + str(resolved_cycle["operatingContext"])
        symptom_label.text = "Resolved symptom: " + str(resolved_cycle["visibleSymptom"])
    elif complete:
        cycle_label.text = "RUN COMPLETE"
        objective_label.text = "THREE-CYCLE CAUSAL REPLAY COMPLETE"
        context_label.text = "Final built architecture: " + ARCH_LABELS[built_architecture]
        symptom_label.text = "Final cumulative score: " + str(cumulative_score)
    else:
        var cycle: Dictionary = cycles[cycle_index]
        cycle_label.text = "CYCLE " + str(cycle_index + 1) + " / " + str(cycles.size())
        objective_label.text = _objective_for(cycle_index)
        context_label.text = "Context: " + str(cycle["operatingContext"])
        symptom_label.text = "Visible symptom: " + str(cycle["visibleSymptom"])

    var built_text: String = "none yet" if built_architecture == "" else str(ARCH_LABELS[built_architecture])
    var selected_text: String = "choose one" if selected_architecture == "" else str(ARCH_LABELS[selected_architecture])
    built_label.text = "BUILT: " + built_text + " · candidate: " + selected_text + " · " + _persistence_status()

    if complete:
        inspection_label.text = "INSPECTION · run complete"
    elif awaiting_next_cycle:
        inspection_label.text = "INSPECTION · cycle locked; advance only after reading aftermath"
    elif inspection_performed:
        inspection_label.text = "INSPECTION · " + inspection_diagnostic + " → " + inspection_observation + " · cost locked " + str(int(design["diagnosticCost"])) + " · cause remains hidden"
    elif selected_diagnostic == "none":
        inspection_label.text = "INSPECTION · skipped unless you choose a scan"
    else:
        inspection_label.text = "INSPECTION · ready: " + selected_diagnostic + " scan reveals FAULT/OK only"

    aftermath_label.text = "AFTERMATH · " + last_aftermath
    replay_label.text = "REPLAY · —" if replay.is_empty() else "REPLAY\n" + "\n".join(replay)
    diagnostic_picker.disabled = interaction_locked or inspection_performed
    inspect_button.disabled = interaction_locked or inspection_performed or selected_diagnostic == "none"
    commit_button.disabled = interaction_locked or selected_architecture == ""
    commit_button.text = "COMMIT & RUN"
    advance_button.visible = awaiting_next_cycle or complete
    advance_button.text = "RESTART" if complete else "NEXT CYCLE"
    for arch in ARCHITECTURES:
        var button: Button = architecture_buttons[arch]
        button.disabled = interaction_locked
        button.button_pressed = arch == selected_architecture
    queue_redraw()

func _select_architecture(arch: String) -> void:
    selected_architecture = arch
    _refresh_ui()

func _on_diagnostic_selected(index: int) -> void:
    selected_diagnostic = DIAGNOSTICS[index]
    _refresh_ui()

func _on_inspect_pressed() -> void:
    _perform_inspection("", true)

func _on_commit_pressed() -> void:
    _resolve_cycle(true)

func _on_advance_pressed() -> void:
    if cycle_index >= cycles.size():
        _restart_run()
    else:
        _advance_cycle(true)

func _observation(diagnostic: String, cause: String) -> String:
    if diagnostic == "none":
        return "none"
    return "FAULT" if diagnostic == cause else "OK"

func _sample_cause(cycle: Dictionary) -> String:
    var roll := rng.randf()
    var cumulative := 0.0
    for cause in ARCHITECTURES:
        cumulative += float(cycle["causePrior"][cause])
        if roll <= cumulative:
            return cause
    return "route"

func _perform_inspection(forced_cause: String = "", refresh: bool = true) -> Dictionary:
    if cycle_index >= cycles.size() or awaiting_next_cycle or inspection_performed or selected_diagnostic == "none":
        return {}
    var cycle: Dictionary = cycles[cycle_index]
    pending_cause = forced_cause if forced_cause != "" else _sample_cause(cycle)
    inspection_diagnostic = selected_diagnostic
    inspection_observation = _observation(inspection_diagnostic, pending_cause)
    inspection_performed = true
    var result := {
        "diagnostic": inspection_diagnostic,
        "observation": inspection_observation,
        "diagnosticCost": int(design["diagnosticCost"]),
    }
    if refresh:
        _refresh_ui()
    return result

func _resolve_cycle(refresh: bool, forced_cause: String = "") -> Dictionary:
    if cycle_index >= cycles.size() or awaiting_next_cycle or selected_architecture == "":
        return {}
    var current_index := cycle_index
    var cycle: Dictionary = cycles[current_index]
    var previous_architecture := built_architecture
    var cause: String
    if pending_cause != "":
        cause = pending_cause
    elif forced_cause != "":
        cause = forced_cause
    else:
        cause = _sample_cause(cycle)
    var actual_diagnostic := inspection_diagnostic if inspection_performed else "none"
    var observation := inspection_observation if inspection_performed else "none"
    var reward_row: Dictionary = cycle["rewardByCauseAndArchitecture"][cause]
    var base_reward := int(reward_row[selected_architecture])
    var diagnostic_cost := int(design["diagnosticCost"]) if inspection_performed else 0
    var switch_cost := int(design["switchCost"]) if previous_architecture != "" and previous_architecture != selected_architecture else 0
    var net := base_reward - diagnostic_cost - switch_cost
    cumulative_score += net

    var result := {
        "cycle": current_index + 1,
        "context": _context_tag(current_index),
        "previousArchitecture": previous_architecture,
        "cause": cause,
        "diagnostic": actual_diagnostic,
        "observation": observation,
        "architecture": selected_architecture,
        "baseReward": base_reward,
        "diagnosticCost": diagnostic_cost,
        "switchCost": switch_cost,
        "net": net,
    }
    var diag_text := "no scan" if actual_diagnostic == "none" else actual_diagnostic + " scan → " + observation
    last_aftermath = "cause=" + cause.to_upper() + "; " + diag_text + "; committed=" + selected_architecture.to_upper() + "; base=" + str(base_reward) + " - diagnostic=" + str(diagnostic_cost) + " - switch=" + str(switch_cost) + " → net=" + str(net)
    var previous_text := "none" if previous_architecture == "" else previous_architecture
    replay.append("C" + str(current_index + 1) + "[" + _context_tag(current_index) + "] prev=" + previous_text + " diag=" + actual_diagnostic + "/" + observation + " arch=" + selected_architecture + " switch=" + str(switch_cost) + " cause=" + cause + " base=" + str(base_reward) + " net=" + str(net))

    built_architecture = selected_architecture
    cycle_index += 1
    resolved_cycle_index = current_index
    awaiting_next_cycle = cycle_index < cycles.size()
    selected_architecture = built_architecture
    selected_diagnostic = "none"
    inspection_performed = false
    inspection_diagnostic = "none"
    inspection_observation = "none"
    pending_cause = ""
    diagnostic_picker.select(0)
    if refresh:
        _refresh_ui()
    return result

func _advance_cycle(refresh: bool = true) -> void:
    if not awaiting_next_cycle:
        return
    awaiting_next_cycle = false
    resolved_cycle_index = -1
    if refresh:
        _refresh_ui()

func _restart_run() -> void:
    cycle_index = 0
    resolved_cycle_index = -1
    awaiting_next_cycle = false
    built_architecture = ""
    selected_architecture = ""
    selected_diagnostic = "none"
    inspection_performed = false
    inspection_diagnostic = "none"
    inspection_observation = "none"
    pending_cause = ""
    cumulative_score = 0
    replay.clear()
    last_aftermath = "No run committed yet."
    diagnostic_picker.select(0)
    _refresh_ui()

func _best_policy(index: int, previous: String, switch_cost: float, allow_diagnostics: bool) -> Dictionary:
    if index >= cycles.size():
        return {"value": 0.0, "diagnostic": "none", "architectureByObservation": {}}
    var cycle: Dictionary = cycles[index]
    var choices: Array = DIAGNOSTICS if allow_diagnostics else ["none"]
    var best_value := -INF
    var best_diagnostic := "none"
    var best_actions: Dictionary = {}
    for diagnostic_variant in choices:
        var diagnostic: String = diagnostic_variant
        var groups: Dictionary = {}
        for cause in ARCHITECTURES:
            var obs := _observation(diagnostic, cause)
            if not groups.has(obs):
                groups[obs] = []
            groups[obs].append({"cause": cause, "prior": float(cycle["causePrior"][cause])})
        var total := -float(design["diagnosticCost"]) if diagnostic != "none" else 0.0
        var actions: Dictionary = {}
        for observation_variant in groups.keys():
            var obs_key: String = observation_variant
            var members: Array = groups[obs_key]
            var p_obs := 0.0
            for member_variant in members:
                var member: Dictionary = member_variant
                p_obs += float(member["prior"])
            var branch_best := -INF
            var branch_arch := ""
            for arch in ARCHITECTURES:
                var immediate := 0.0
                for member_variant in members:
                    var member: Dictionary = member_variant
                    var cause: String = member["cause"]
                    immediate += (float(member["prior"]) / p_obs) * float(cycle["rewardByCauseAndArchitecture"][cause][arch])
                if previous != "" and arch != previous:
                    immediate -= switch_cost
                var future: Dictionary = _best_policy(index + 1, arch, switch_cost, allow_diagnostics)
                var candidate := immediate + float(future["value"])
                if candidate > branch_best:
                    branch_best = candidate
                    branch_arch = arch
            total += p_obs * branch_best
            actions[obs_key] = branch_arch
        if total > best_value:
            best_value = total
            best_diagnostic = diagnostic
            best_actions = actions
    return {"value": best_value, "diagnostic": best_diagnostic, "architectureByObservation": best_actions}

func _run_acceptance() -> void:
    var failures: Array[String] = []
    if design.get("id") != "pc01-causal-works-f0":
        failures.append("carrier did not load F0 design")
    if cycles.size() != 3:
        failures.append("expected exactly three F0 cycles")
    if int(design.get("diagnosticCost", -1)) != 6 or int(design.get("switchCost", -1)) != 8:
        failures.append("F0 costs drifted")
    for cycle_variant in cycles:
        var cycle: Dictionary = cycle_variant
        for cause in ARCHITECTURES:
            var row: Dictionary = cycle["rewardByCauseAndArchitecture"][cause]
            if int(row[cause]) != 100:
                failures.append("cause-aligned architecture reward drifted")
    if _observation("route", "source") != "OK" or _observation("route", "process") != "OK":
        failures.append("negative route scan must remain ambiguous across two causes")

    var evidence_path := ProjectSettings.globalize_path("res://" + F0_EVIDENCE_RELATIVE)
    var evidence_variant = JSON.parse_string(FileAccess.get_file_as_string(evidence_path))
    if typeof(evidence_variant) != TYPE_DICTIONARY:
        failures.append("could not parse F0 structural evidence")

    var direct_with_diag: Dictionary = _best_policy(0, "", float(design["switchCost"]), true)
    var direct_without_diag: Dictionary = _best_policy(0, "", float(design["switchCost"]), false)
    var direct_uplift := float(direct_with_diag["value"]) - float(direct_without_diag["value"])
    if direct_uplift < 5.0:
        failures.append("direct diagnosis-uplift solver failed")

    var no_scan_choices: Array[String] = []
    for i in range(cycles.size()):
        var no_scan_policy: Dictionary = _best_policy(i, "", float(design["switchCost"]), false)
        no_scan_choices.append(str(no_scan_policy["architectureByObservation"]["none"]))
    if no_scan_choices != ["process", "route", "source"]:
        failures.append("direct no-scan revaluation solver failed")

    var persistent_policy: Dictionary = _best_policy(0, "process", float(design["switchCost"]), true)
    var zero_switch_policy: Dictionary = _best_policy(0, "process", 0.0, true)
    if persistent_policy["diagnostic"] == zero_switch_policy["diagnostic"] and persistent_policy["architectureByObservation"] == zero_switch_policy["architectureByObservation"]:
        failures.append("persistence counterfactual did not change policy")

    for i in range(cycles.size()):
        var seen: Dictionary = {}
        for seed_value in range(1, 129):
            rng.seed = seed_value * 7919 + i * 104729
            seen[_sample_cause(cycles[i])] = true
        if seen.size() < 2:
            failures.append("causePrior sampling did not reach two causes in cycle " + str(i + 1))

    _restart_run()
    selected_architecture = "route"
    selected_diagnostic = "route"
    var i1 := _perform_inspection("process", false)
    selected_architecture = "process"
    var c1 := _resolve_cycle(false)
    if not awaiting_next_cycle or built_architecture != "process" or resolved_cycle_index != 0:
        failures.append("cycle 1 aftermath gate/persisted state mismatch")
    _advance_cycle(false)

    selected_diagnostic = "route"
    var i2 := _perform_inspection("route", false)
    selected_architecture = "route"
    var c2 := _resolve_cycle(false)
    if not awaiting_next_cycle or built_architecture != "route" or resolved_cycle_index != 1:
        failures.append("cycle 2 aftermath gate/persisted state mismatch")
    _advance_cycle(false)

    selected_architecture = "source"
    selected_diagnostic = "none"
    var c3 := _resolve_cycle(false, "source")

    if i1.get("observation") != "OK" or i1.has("cause") or int(i1.get("diagnosticCost", -1)) != 6:
        failures.append("cycle 1 inspection must reveal ambiguous observation before cause")
    if c1.get("architecture") != "process" or c1.get("observation") != "OK" or int(c1.get("diagnosticCost", -1)) != 6 or int(c1.get("switchCost", -1)) != 0:
        failures.append("cycle 1 inspect-then-revise carrier mismatch")
    if i2.get("observation") != "FAULT" or c2.get("architecture") != "route" or c2.get("previousArchitecture") != "process" or int(c2.get("switchCost", -1)) != 8:
        failures.append("cycle 2 fault-conditional persistence mismatch")
    if c3.get("diagnostic") != "none" or int(c3.get("diagnosticCost", -1)) != 0 or int(c3.get("switchCost", -1)) != 8 or c3.get("previousArchitecture") != "route":
        failures.append("cycle 3 optional no-scan switching mismatch")
    if cumulative_score != 272 or replay.size() != 3 or built_architecture != "source" or awaiting_next_cycle:
        failures.append("deterministic replay mismatch")
    if not replay[0].contains("prev=none") or not replay[1].contains("diag=route/FAULT") or not replay[2].contains("diag=none/none"):
        failures.append("replay causal fields incomplete")

    if not failures.is_empty():
        for failure in failures:
            push_error("PC01_F1_ACCEPTANCE_FAIL " + failure)
        get_tree().quit(3)
        return
    print("PC01_F1_ACCEPTANCE_PASS total=272 chronology=inspect_then_commit aftermath_gate=next_cycle direct_uplift=" + str(direct_uplift) + " no_scan=" + str(no_scan_choices) + " persistence_cf=" + str(persistent_policy["diagnostic"]) + "_vs_" + str(zero_switch_policy["diagnostic"]))
    get_tree().quit(0)

func _draw() -> void:
    var font := ThemeDB.fallback_font
    var route_y := 282.0
    var line_color := Color(0.55, 0.62, 0.72, 1.0)
    draw_line(Vector2(205, route_y), Vector2(305, route_y), line_color, 5.0)
    draw_line(Vector2(415, route_y), Vector2(515, route_y), line_color, 5.0)
    draw_line(Vector2(625, route_y), Vector2(760, route_y), line_color, 5.0)
    for arch in ARCHITECTURES:
        var pos: Vector2 = NODE_POSITIONS[arch]
        var rect := Rect2(pos, Vector2(110, 76))
        var fill := Color(0.10, 0.15, 0.23, 1.0)
        var border := Color(0.72, 0.78, 0.88, 1.0)
        if arch == selected_architecture:
            fill = Color(0.16, 0.27, 0.40, 1.0)
            border = Color(0.86, 0.93, 1.0, 1.0)
        draw_rect(rect, fill, true)
        draw_rect(rect, border, false, 3.0)
        draw_string(font, pos + Vector2(0, 45), ARCH_LABELS[arch], HORIZONTAL_ALIGNMENT_CENTER, 110, 17, Color(0.94, 0.96, 1.0, 1.0))
        if arch == built_architecture:
            draw_circle(pos + Vector2(96, 13), 6.0, Color(0.45, 0.92, 0.68, 1.0))
    var output_pos: Vector2 = NODE_POSITIONS["output"]
    var output_rect := Rect2(output_pos, Vector2(145, 76))
    draw_rect(output_rect, Color(0.20, 0.16, 0.28, 1.0), true)
    draw_rect(output_rect, Color(0.86, 0.76, 0.96, 1.0), false, 3.0)
    draw_string(font, output_pos + Vector2(0, 45), "OUTPUT", HORIZONTAL_ALIGNMENT_CENTER, 145, 17, Color(0.97, 0.94, 1.0, 1.0))
