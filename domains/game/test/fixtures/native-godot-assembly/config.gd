extends Resource

# Native Godot Resource, not a new Ordivon configuration language.
@export var board_width: int = 5
@export var goal_x: int = 4
@export var starting_energy: int = 5
@export var step_cost: int = 1
@export var turn_limit: int = 6

# Always call this base-script acceptance rule from the real consumer.
# A player-supplied subclass may override is_valid(), but that self-claim
# must never grant permission to violate the native field invariants.
static func accepts_parameters(source: Resource) -> bool:
    return (
        source.board_width >= 2 and source.board_width <= 64
        and source.goal_x > 0 and source.goal_x < source.board_width
        and source.starting_energy >= 0 and source.starting_energy <= 128
        and source.step_cost >= 1 and source.step_cost <= 128
        and source.turn_limit >= 1 and source.turn_limit <= 64
    )

func is_valid() -> bool:
    return accepts_parameters(self)
