extends VBoxContainer

# Presentation is a replaceable native scene consumer of state snapshots.
# Rule implementation never reaches into a UI node.
func render_state(state: Dictionary) -> void:
    var cells: Array[String] = []
    for i in range(state["board_width"]):
        if i == state["x"]:
            cells.append("P")
        elif i == state["goal_x"]:
            cells.append("G")
        else:
            cells.append(".")
    $Board.text = " ".join(PackedStringArray(cells))
    $Status.text = "energy=%d  turn=%d/%d  phase=%s" % [
        state["energy"], state["turn"], state["turn_limit"], state["phase"]
    ]
