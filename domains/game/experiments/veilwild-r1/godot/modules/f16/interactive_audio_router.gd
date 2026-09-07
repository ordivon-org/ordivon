extends Node
class_name VeilwildInteractiveAudioRouter

signal audio_command_emitted(command: Dictionary)

var _policies: Array = []
var _streams: Dictionary = {}
var _active_loops: Dictionary = {}
var _active_loop_semantics: Dictionary = {}
var _command_sequence: int = 0

func configure(policy_rows: Array) -> PackedStringArray:
    var errors := PackedStringArray()
    var accepted: Array = []
    for index in range(policy_rows.size()):
        var row = policy_rows[index]
        if typeof(row) != TYPE_DICTIONARY:
            errors.append("policy[%d] must be Dictionary" % index)
            continue
        var row_errors := _validate_policy(row)
        for error in row_errors:
            errors.append("policy[%d]: %s" % [index, error])
        if row_errors.is_empty():
            accepted.append(row.duplicate(true))
    if errors.is_empty():
        _policies = accepted
    return errors

func register_stream(cue_semantic_id: String, stream: AudioStream) -> void:
    if cue_semantic_id.is_empty() or stream == null:
        push_error("register_stream requires non-empty cue_semantic_id and AudioStream")
        return
    _streams[cue_semantic_id] = stream

func stream_binding_count() -> int:
    return _streams.size()

func has_stream(cue_semantic_id: String) -> bool:
    return _streams.has(cue_semantic_id)

func process_event(event: Dictionary) -> Array:
    if not event.has("behavior_state_id") or not event.has("transition_kind"):
        return [_emit_command({
            "action": "REJECT_EVENT",
            "reason": "MISSING_REQUIRED_EVENT_FIELD",
            "behavior_state_id": event.get("behavior_state_id", ""),
            "binding_status": "NOT_APPLICABLE"
        })]

    var commands: Array = []
    for row in _policies:
        if not _matches(row, event):
            continue
        commands.append(_apply_policy(row, event))

    if commands.is_empty():
        commands.append(_emit_command({
            "action": "NO_MATCH",
            "behavior_state_id": str(event["behavior_state_id"]),
            "transition_kind": str(event["transition_kind"]),
            "binding_status": "NOT_APPLICABLE"
        }))
    return commands

func active_loop_count() -> int:
    return _active_loops.size()

func active_loop_groups() -> Array:
    return _active_loops.keys()

func get_active_loop_player(group: String) -> Node:
    if not _active_loops.has(group):
        return null
    return _active_loops[group]

func stop_all() -> void:
    _stop_all_loops()
    for child in get_children():
        if (child is AudioStreamPlayer or child is AudioStreamPlayer3D) and not child.is_queued_for_deletion():
            child.stop()
            child.queue_free()

func _apply_policy(row: Dictionary, event: Dictionary) -> Dictionary:
    var kind := str(row["playback_kind"])
    var group := str(row.get("concurrency_group", row["cue_semantic_id"]))
    var cue_id := str(row["cue_semantic_id"])
    var base_command := {
        "cue_semantic_id": cue_id,
        "cue_class_id": str(row["cue_class_id"]),
        "behavior_state_id": str(event["behavior_state_id"]),
        "transition_kind": str(event["transition_kind"]),
        "transition_reason_id": str(event.get("transition_reason_id", "")),
        "required_authorization_mode": str(row.get("required_authorization_mode", "NONE")),
        "event_id": str(event.get("event_id", "")),
        "priority_rank": int(row.get("priority_rank", 0)),
        "bus": str(row.get("bus", "Master")),
        "spatial": bool(row.get("spatial", false)),
        "source_position_m": event.get("source_position_m", null),
        "criticality": str(row.get("criticality", "UNDECLARED")),
        "redundant_carrier_or_route": str(row.get("redundant_carrier_or_route", "UNDECLARED")),
        "caption_or_visual_alternative": str(row.get("caption_or_visual_alternative", "UNDECLARED")),
        "spatial_information_class": str(row.get("spatial_information_class", "UNDECLARED")),
        "concurrency_group": group
    }

    if kind == "SILENCE_ALL":
        base_command["stopped_cues"] = _stop_all_loops()
        base_command["action"] = "SILENCE_ALL"
        base_command["binding_status"] = "NOT_APPLICABLE"
        return _emit_command(base_command)

    if kind == "STOP_GROUP":
        var stopped := _stop_group(group)
        base_command["stopped_cues"] = [] if stopped.is_empty() else [stopped]
        base_command["action"] = "STOP_GROUP"
        base_command["binding_status"] = "NOT_APPLICABLE"
        return _emit_command(base_command)

    if kind == "START_LOOP" and _active_loops.has(group) and not bool(row.get("restart", false)):
        base_command["action"] = "SUPPRESS_DUPLICATE_LOOP"
        base_command["binding_status"] = "BOUND" if _streams.has(cue_id) else "STREAM_UNBOUND"
        return _emit_command(base_command)

    if kind == "START_LOOP" and _active_loops.has(group):
        _stop_group(group)

    if bool(row.get("spatial", false)) and not _valid_vector3_value(event.get("source_position_m", null)):
        base_command["action"] = "REJECT_EVENT"
        base_command["reason"] = "MISSING_OR_INVALID_SOURCE_POSITION"
        base_command["binding_status"] = "NOT_APPLICABLE"
        return _emit_command(base_command)

    var stream: AudioStream = _streams.get(cue_id, null)
    base_command["binding_status"] = "BOUND" if stream != null else "STREAM_UNBOUND"
    base_command["action"] = kind

    if stream != null:
        var player := _create_player(row, event, stream)
        if kind == "START_LOOP":
            _active_loops[group] = player
            _active_loop_semantics[group] = base_command.duplicate(true)
            player.connect("finished", Callable(self, "_restart_loop").bind(group, player))
        else:
            player.connect("finished", player.queue_free)
        player.play()

    return _emit_command(base_command)

func _create_player(row: Dictionary, event: Dictionary, stream: AudioStream) -> Node:
    var bus_name := str(row.get("bus", "Master"))
    _ensure_bus(bus_name)
    if bool(row.get("spatial", false)):
        var player_3d := AudioStreamPlayer3D.new()
        var profile: Dictionary = row.get("spatial_profile", {})
        player_3d.stream = stream
        player_3d.bus = bus_name
        player_3d.unit_size = float(profile.get("unit_size_m", 1.0))
        player_3d.max_distance = float(profile.get("max_distance_m", 40.0))
        player_3d.max_db = float(profile.get("max_db", 0.0))
        player_3d.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
        player_3d.position = _vector3_from(event.get("source_position_m", [0.0, 0.0, 0.0]))
        add_child(player_3d)
        return player_3d

    var player := AudioStreamPlayer.new()
    player.stream = stream
    player.bus = bus_name
    add_child(player)
    return player

func _restart_loop(group: String, player: Node) -> void:
    if _active_loops.get(group, null) == player and is_instance_valid(player) and player.has_method("play"):
        player.play()

func _stop_group(group: String) -> Dictionary:
    if not _active_loops.has(group):
        return {}
    var stopped: Dictionary = _active_loop_semantics.get(group, {}).duplicate(true)
    var player: Node = _active_loops[group]
    if is_instance_valid(player):
        if player.has_method("stop"):
            player.stop()
        player.queue_free()
    _active_loops.erase(group)
    _active_loop_semantics.erase(group)
    return stopped

func _stop_all_loops() -> Array:
    var stopped: Array = []
    for group in _active_loops.keys().duplicate():
        var stopped_one := _stop_group(str(group))
        if not stopped_one.is_empty():
            stopped.append(stopped_one)
    return stopped

func _ensure_bus(bus_name: String) -> void:
    if bus_name.is_empty() or bus_name == "Master":
        return
    if AudioServer.get_bus_index(bus_name) >= 0:
        return
    AudioServer.add_bus()
    var index := AudioServer.bus_count - 1
    AudioServer.set_bus_name(index, bus_name)

func _matches(row: Dictionary, event: Dictionary) -> bool:
    var states: Array = row.get("trigger_state_ids", [])
    var transitions: Array = row.get("trigger_transition_kinds", [])
    if not states.has(str(event["behavior_state_id"])) or not transitions.has(str(event["transition_kind"])):
        return false
    var reasons: Array = row.get("trigger_transition_reason_ids", [])
    if not reasons.is_empty() and not reasons.has(str(event.get("transition_reason_id", ""))):
        return false
    return _authorization_allows(row, event)

func _authorization_allows(row: Dictionary, event: Dictionary) -> bool:
    var mode := str(row.get("required_authorization_mode", "NONE"))
    if mode == "NONE":
        return true
    var authorization = event.get("player_cue_authorization", event.get("playerCueAuthorization", null))
    if typeof(authorization) != TYPE_DICTIONARY:
        return false
    var cue_class := str(row.get("cue_class_id", ""))
    var explicit_none: Array = authorization.get("explicit_none_classes", [])
    if explicit_none.has(cue_class):
        return false
    if mode == "EDGE":
        return authorization.get("edge_classes", []).has(cue_class)
    if mode == "SUSTAINED":
        return authorization.get("sustained_classes", []).has(cue_class)
    return false

func _validate_policy(row: Dictionary) -> PackedStringArray:
    var errors := PackedStringArray()
    for field in ["cue_semantic_id", "cue_class_id", "trigger_state_ids", "trigger_transition_kinds", "playback_kind"]:
        if not row.has(field):
            errors.append("missing %s" % field)
    if not errors.is_empty():
        return errors
    if str(row["cue_semantic_id"]).is_empty():
        errors.append("cue_semantic_id must be non-empty")
    var valid_cue_classes := ["TRACE", "BEHAVIOR_AUDIO", "MOTION_COUNTERCUE", "CAMOUFLAGE_MISMATCH", "THREAT_RESPONSE", "OBSERVATION_PROGRESS", "SUCCESS_CONSEQUENCE"]
    if not valid_cue_classes.has(str(row["cue_class_id"])):
        errors.append("unsupported cue_class_id")
    if typeof(row["trigger_state_ids"]) != TYPE_ARRAY or row["trigger_state_ids"].is_empty():
        errors.append("trigger_state_ids must be non-empty Array")
    if typeof(row["trigger_transition_kinds"]) != TYPE_ARRAY or row["trigger_transition_kinds"].is_empty():
        errors.append("trigger_transition_kinds must be non-empty Array")
    var valid_kinds := ["PLAY_ONE_SHOT", "START_LOOP", "STOP_GROUP", "SILENCE_ALL"]
    if not valid_kinds.has(str(row["playback_kind"])):
        errors.append("unsupported playback_kind")
    var authorization_mode := str(row.get("required_authorization_mode", "NONE"))
    if not ["NONE", "EDGE", "SUSTAINED"].has(authorization_mode):
        errors.append("unsupported required_authorization_mode")
    if authorization_mode == "EDGE" and row.get("trigger_transition_reason_ids", []).is_empty():
        errors.append("EDGE authorization requires trigger_transition_reason_ids")
    if bool(row.get("spatial", false)):
        var profile = row.get("spatial_profile", null)
        if typeof(profile) != TYPE_DICTIONARY:
            errors.append("spatial policy requires spatial_profile Dictionary")
        else:
            var unit_size := float(profile.get("unit_size_m", 0.0))
            var max_distance := float(profile.get("max_distance_m", 0.0))
            if unit_size <= 0.0:
                errors.append("unit_size_m must be > 0")
            if max_distance <= unit_size:
                errors.append("max_distance_m must exceed unit_size_m")
    return errors

func _valid_vector3_value(value) -> bool:
    if value is Vector3:
        return true
    if typeof(value) != TYPE_ARRAY or value.size() != 3:
        return false
    for component in value:
        if typeof(component) != TYPE_FLOAT and typeof(component) != TYPE_INT:
            return false
    return true

func _vector3_from(value) -> Vector3:
    if value is Vector3:
        return value
    if typeof(value) == TYPE_ARRAY and value.size() == 3:
        return Vector3(float(value[0]), float(value[1]), float(value[2]))
    return Vector3.ZERO

func _emit_command(command: Dictionary) -> Dictionary:
    _command_sequence += 1
    command["command_sequence"] = _command_sequence
    audio_command_emitted.emit(command.duplicate(true))
    return command
