extends VBoxContainer

func render_state(state: Dictionary) -> void:
    var forecast: Dictionary = state.get("forecast", {})
    $Hint.visible = state["phase"] == "fighting" and not forecast.is_empty()
    if $Hint.visible:
        $Hint.text = ("CHARGED STRIKE: Guard perfectly parries this next blow. "
            + "A final killing Attack also prevents retaliation.") if forecast.get("charged", false) else (
            "TIP: The enemy reacts after your move. Guard recovers stamina; "
            + "a final killing Attack prevents retaliation.")
    $Status.text = "ROOM %d/%d | HP %d | STAMINA %d | TURN %d" % [
        state["room"], state["total_rooms"], state["player_health"],
        state["stamina"], state["turn"]
    ]
    match state["phase"]:
        "fighting":
            var f: Dictionary = forecast
            if f.is_empty():
                $Encounter.text = "ENCOUNTER: %d foes | active enemy HP %d" % [
                    state["foes"], state["enemy_health"]
                ]
            else:
                $Encounter.text = (
                    "ENCOUNTER: %d foes | active enemy HP %d\n"
                    + "NEXT FOE HIT: %d | ATTACK: %d damage, -%d stamina, %d HP at risk\n"
                    + "GUARD: +%d stamina, %d HP at risk | every third turn: perfect parry"
                ) % [
                    state["foes"], state["enemy_health"], f["threat_damage"],
                    f["attack_damage"], f["attack_cost"], f["attack_health_loss"],
                    f["guard_stamina_gain"], f["guard_health_loss"]
                ]
        "cleared":
            $Encounter.text = "ROOM CLEARED! Open the door to continue."
        "won":
            $Encounter.text = "VICTORY! All rooms cleared."
        "lost":
            $Encounter.text = "DEFEAT! Restart your expedition."
    $Actions/Attack.disabled = state["phase"] != "fighting" or state["stamina"] < state["attack_cost"]
    $Actions/Guard.disabled = state["phase"] != "fighting"
    $Actions/Next.disabled = state["phase"] != "cleared"
    # Godot retains keyboard focus on a button after it becomes disabled.
    # Transfer only an invalid focus, rather than stealing a valid Human
    # selection on every turn.
    var focused: Control = get_viewport().gui_get_focus_owner()
    if focused is Button and focused.disabled:
        var next_focus: Button = $Actions/Guard
        if state["phase"] == "cleared":
            next_focus = $Actions/Next
        elif state["phase"] in ["won", "lost"]:
            next_focus = $Actions/Restart
        if not next_focus.disabled:
            next_focus.grab_focus.call_deferred()
