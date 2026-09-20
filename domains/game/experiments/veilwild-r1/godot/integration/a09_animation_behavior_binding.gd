extends Node
## A17-owned integration adapter. It preserves the exact A09 runtime profile and
## wires current F13 behavior_decision to the selected final-creature AnimationPlayer.
## It does not define F09 motion semantics or F13 behavior truth.

const EXPECTED_CLIPS: Array[StringName] = [
    &"VW_MOTION_IDLE", &"VW_MOTION_ORIENT", &"VW_MOTION_FREEZE",
    &"VW_MOTION_CONCEAL", &"VW_MOTION_FORAGE", &"VW_MOTION_EVADE", &"VW_MOTION_RECOVER",
]

var animation_system: Node = null
var behavior_runtime: Node = null
var animation_player: AnimationPlayer = null
var last_error := ""
var configured := false
var signal_connected := false
var strict_probe_pass := false
var strict_probe_snapshot: Dictionary = {}

func bind_runtime(animation_system_node: Node, creature_root: Node, behavior_node: Node) -> bool:
    last_error = ""
    strict_probe_pass = false
    strict_probe_snapshot = {}
    animation_system = animation_system_node
    behavior_runtime = behavior_node
    animation_player = null
    configured = false
    signal_connected = false
    if animation_system == null or creature_root == null or behavior_runtime == null:
        return _fail("missing A09/F13/final-creature runtime node")
    if not animation_system.has_method("bind_runtime") or not animation_system.has_method("apply_behavior_decision"):
        return _fail("A09 runtime API mismatch")
    if not behavior_runtime.has_signal("behavior_decision") or not behavior_runtime.has_method("submit_perception"):
        return _fail("F13 behavior_decision API mismatch")
    var players: Array[AnimationPlayer] = []
    _collect_animation_players(creature_root, players)
    if players.size() != 1:
        return _fail("final creature must expose exactly one AnimationPlayer; found %d" % players.size())
    animation_player = players[0]
    var inventory := animation_player.get_animation_list()
    if inventory.size() != EXPECTED_CLIPS.size():
        return _fail("final creature runtime clip count mismatch: %d" % inventory.size())
    for clip_name in EXPECTED_CLIPS:
        if not animation_player.has_animation(clip_name):
            return _fail("missing final creature runtime clip: %s" % clip_name)
    if not _configure_controller():
        return false
    var callback := Callable(animation_system, "apply_behavior_decision")
    if not behavior_runtime.is_connected(&"behavior_decision", callback):
        var err := behavior_runtime.connect(&"behavior_decision", callback)
        if err != OK:
            return _fail("F13->F09 signal connect failed: %d" % err)
    signal_connected = true
    return true

func strict_probe() -> bool:
    strict_probe_pass = false
    strict_probe_snapshot = {}
    if animation_system == null or behavior_runtime == null or animation_player == null or not signal_connected:
        return _fail("strict probe requested before runtime binding")
    if not _configure_controller():
        return false
    if behavior_runtime.has_method("reset_policy"):
        behavior_runtime.call("reset_policy")
    # Neutral, fully-specified F13 owner input. This exercises the real signal path
    # without claiming any world observation or Human outcome.
    var neutral_perception := {
        "player_distance_m": 18.0,
        "line_of_sight": false,
        "visual_exposure": 0.0,
        "player_motion": 0.0,
        "observation_pressure": 0.0,
        "concealment_available": false,
        "concealment_quality": 0.0,
        "escape_available": false,
    }
    var decision: Variant = behavior_runtime.call("submit_perception", 0.0, neutral_perception)
    if not (decision is Dictionary):
        return _fail("F13 strict probe returned non-Dictionary decision")
    var snapshot: Variant = animation_system.call("snapshot")
    if not (snapshot is Dictionary):
        return _fail("F09 strict probe returned non-Dictionary snapshot")
    strict_probe_snapshot = (snapshot as Dictionary).duplicate(true)
    if String(strict_probe_snapshot.get("behavior_state_id", "")) != String((decision as Dictionary).get("behavior_state_id", "")):
        return _fail("F13->F09 strict probe state identity mismatch")
    if String(strict_probe_snapshot.get("clip_name", "")) != "VW_MOTION_IDLE":
        return _fail("F13->F09 strict probe did not select VW_MOTION_IDLE")
    if int(strict_probe_snapshot.get("transition_serial", 0)) != 1:
        return _fail("F13->F09 strict probe must create exactly one initial transition")
    if String(animation_player.assigned_animation) != "VW_MOTION_IDLE":
        return _fail("final creature AnimationPlayer did not receive F09 selected clip")
    strict_probe_pass = true
    return true

func snapshot() -> Dictionary:
    return {
        "candidateReady": configured and signal_connected,
        "configured": configured,
        "signalConnected": signal_connected,
        "animationPlayerPath": "" if animation_player == null else String(animation_player.get_path()),
        "runtimeClips": [] if animation_player == null else Array(animation_player.get_animation_list()),
        "strictProbePass": strict_probe_pass,
        "strictProbeSnapshot": strict_probe_snapshot.duplicate(true),
        "lastError": last_error,
        "producerFront": "A09/F09",
        "producerCommit": "be64167aa1a96921996349fafc3a6318226ff92a",
    }

func _configure_controller() -> bool:
    var ok := bool(animation_system.call("bind_runtime", animation_player, _state_to_motion(), _legal_transitions(), true))
    if not ok:
        return _fail("A09 bind_runtime rejected exact owner profile")
    configured = true
    return true

func _state_to_motion() -> Dictionary:
    return {
        &"veilwild.behavior.unaware.r1": {"motion_semantic_id": &"MOTION_IDLE", "clip_name": &"VW_MOTION_IDLE", "blend_seconds": 0.12},
        &"veilwild.behavior.orient.r1": {"motion_semantic_id": &"MOTION_ORIENT", "clip_name": &"VW_MOTION_ORIENT", "blend_seconds": 0.08},
        &"veilwild.behavior.freeze.r1": {"motion_semantic_id": &"MOTION_FREEZE", "clip_name": &"VW_MOTION_FREEZE", "blend_seconds": 0.08},
        &"veilwild.behavior.conceal.r1": {"motion_semantic_id": &"MOTION_CONCEAL", "clip_name": &"VW_MOTION_CONCEAL", "blend_seconds": 0.10},
        &"veilwild.behavior.evade.r1": {"motion_semantic_id": &"MOTION_EVADE", "clip_name": &"VW_MOTION_EVADE", "blend_seconds": 0.06},
        &"veilwild.behavior.recover.r1": {"motion_semantic_id": &"MOTION_RECOVER", "clip_name": &"VW_MOTION_RECOVER", "blend_seconds": 0.10},
    }

func _legal_transitions() -> Dictionary:
    return {
        &"veilwild.behavior.unaware.r1": [&"veilwild.behavior.orient.r1", &"veilwild.behavior.freeze.r1", &"veilwild.behavior.conceal.r1"],
        &"veilwild.behavior.orient.r1": [&"veilwild.behavior.unaware.r1", &"veilwild.behavior.freeze.r1", &"veilwild.behavior.conceal.r1", &"veilwild.behavior.evade.r1"],
        &"veilwild.behavior.freeze.r1": [&"veilwild.behavior.conceal.r1", &"veilwild.behavior.evade.r1", &"veilwild.behavior.recover.r1"],
        &"veilwild.behavior.conceal.r1": [&"veilwild.behavior.freeze.r1", &"veilwild.behavior.evade.r1", &"veilwild.behavior.recover.r1"],
        &"veilwild.behavior.evade.r1": [&"veilwild.behavior.recover.r1"],
        &"veilwild.behavior.recover.r1": [&"veilwild.behavior.unaware.r1", &"veilwild.behavior.freeze.r1", &"veilwild.behavior.conceal.r1", &"veilwild.behavior.evade.r1"],
    }

func _collect_animation_players(node: Node, result: Array[AnimationPlayer]) -> void:
    if node is AnimationPlayer:
        result.append(node as AnimationPlayer)
    for child in node.get_children():
        _collect_animation_players(child, result)

func _fail(message: String) -> bool:
    last_error = message
    return false
