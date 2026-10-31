extends Node

# The game-specific rule connection consumes Godot Resources and emits
# a native signal. No generic Game state or event framework is introduced.
const ConfigType = preload("res://config.gd")

signal state_changed(state: Dictionary)

@export var configuration: Resource

var x: int = 0
var energy: int = 0
var turn: int = 0
var phase: String = "uninitialized"

func reset_game(replacement: Resource = null) -> bool:
    var chosen: Resource = replacement if replacement != null else configuration
    # Godot's native script Resource type is the typed input port for this
    # actual gameplay LEGO. An arbitrary Resource self-reporting is_valid
    # does not supply board/energy/cost/turn fields and must not be installed.
    if not chosen is ConfigType or not ConfigType.accepts_parameters(chosen):
        return false
    # Godot Resource instances are mutable. Admit a deep copy so a player,
    # scene or mod cannot rewrite the active verified input through an alias
    # without explicitly calling reset_game again.
    configuration = chosen.duplicate(true)
    x = 0
    energy = configuration.starting_energy
    turn = 0
    phase = "playing" if energy >= configuration.step_cost else "lost"
    state_changed.emit(snapshot())
    return true

func move(dx: int) -> bool:
    if phase != "playing" or (dx != -1 and dx != 1):
        return false
    var next_x: int = x + dx
    if next_x < 0 or next_x >= configuration.board_width:
        return false
    if energy < configuration.step_cost or turn >= configuration.turn_limit:
        return false
    x = next_x
    energy -= configuration.step_cost
    turn += 1
    if x == configuration.goal_x:
        phase = "won"
    elif turn >= configuration.turn_limit or energy < configuration.step_cost:
        phase = "lost"
    state_changed.emit(snapshot())
    return true

func snapshot() -> Dictionary:
    return {
        "x": x,
        "energy": energy,
        "turn": turn,
        "phase": phase,
        "board_width": configuration.board_width,
        "goal_x": configuration.goal_x,
        "turn_limit": configuration.turn_limit,
    }
