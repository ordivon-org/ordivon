extends VBoxContainer

# A disposable UI projection of the previous and current Rule snapshots.
# Never participates in action admission, save data, or game authority.
var _prior_view_state: Dictionary = {}
var _current_view_state: Dictionary = {}

func reset_action_feedback() -> void:
    if $Outcome.visible:
        $Outcome.text = "AFTER YOUR MOVE: This panel will show the actual result."
    else:
        $Outcome.text = ""

func render_combat_result(action: String) -> void:
    # EncounterRules emits action_accepted only after state_changed. Compare
    # the last two real native snapshots, never predict or replay a battle.
    if not _prior_view_state.has("forecast") or _prior_view_state.get("phase") != "fighting":
        return
    if action not in ["attack", "guard"] or not $Outcome.visible:
        return
    var hp_loss: int = maxi(0, int(_prior_view_state["player_health"]) -
        int(_current_view_state["player_health"]))
    if action == "attack":
        var damage: int = 0
        if int(_current_view_state["foes"]) < int(_prior_view_state["foes"]):
            damage = int(_prior_view_state["enemy_health"])
        else:
            damage = maxi(0, int(_prior_view_state["enemy_health"]) -
                int(_current_view_state["enemy_health"]))
        $Outcome.text = "LAST MOVE: Attack dealt %d enemy HP; you lost %d HP.%s" % [
            damage, hp_loss,
            " Room cleared; find the passage choice." if _current_view_state["phase"] == "cleared" else ""
        ]
    else:
        var gained: int = maxi(0, int(_current_view_state["stamina"]) -
            int(_prior_view_state["stamina"]))
        if _prior_view_state["forecast"].get("charged", false):
            $Outcome.text = (
                "LAST MOVE: PERFECT PARRY blocked the announced %d damage; "
                + "gained %d stamina; you lost %d HP."
            ) % [int(_prior_view_state["forecast"]["threat_damage"]), gained, hp_loss]
        else:
            $Outcome.text = "LAST MOVE: Guard gained %d stamina; you lost %d HP." % [
                gained, hp_loss
            ]

func render_state(state: Dictionary) -> void:
    _prior_view_state = _current_view_state
    _current_view_state = state.duplicate(true)
    $Outcome.visible = (state.has("forecast") or (
        _prior_view_state.has("forecast") and state["phase"] in ["cleared", "lost"]
    ))
    if $Outcome.visible and (
        int(state["turn"]) == 0 or
        (not _prior_view_state.is_empty() and state["room"] != _prior_view_state["room"])
    ):
        reset_action_feedback()
    elif not $Outcome.visible:
        $Outcome.text = ""
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
