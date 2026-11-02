extends VBoxContainer

func render_state(state: Dictionary) -> void:
    $Status.text = "ROOM %d/%d | HP %d | STAMINA %d | TURN %d" % [
        state["room"], state["total_rooms"], state["player_health"],
        state["stamina"], state["turn"]
    ]
    match state["phase"]:
        "fighting":
            $Encounter.text = "ENCOUNTER: %d foes | active enemy HP %d" % [
                state["foes"], state["enemy_health"]
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
