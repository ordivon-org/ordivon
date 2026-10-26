extends Resource

# Native Godot Resource, not a new Ordivon configuration language.
@export var board_width: int = 5
@export var goal_x: int = 4
@export var starting_energy: int = 5
@export var step_cost: int = 1
@export var turn_limit: int = 6

func is_valid() -> bool:
    return (
        board_width >= 2 and board_width <= 64
        and goal_x > 0 and goal_x < board_width
        and starting_energy >= 0 and starting_energy <= 128
        and step_cost >= 1 and step_cost <= 128
        and turn_limit >= 1 and turn_limit <= 64
    )
