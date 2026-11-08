extends VBoxContainer

func render_state(state: Dictionary) -> void:
    $Status.text = "ROOM %d/%d | HP %d | STAMINA %d | TURN %d" % [
        state["room"], state["total_rooms"], state["player_health"],
        state["stamina"], state["turn"]
    ]
    match state["phase"]:
        "fighting":
            var f: Dictionary = state["forecast"]
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
