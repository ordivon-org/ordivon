extends Node3D
class_name VeilwildAudioSystem

signal evidence_event_ready(event: Dictionary)
signal runtime_configuration_completed(status: Dictionary)

const DEFAULT_PRODUCT_POLICY_PATH := "res://modules/f16/F16_PRODUCT_AUDIO_POLICY_R2.json"
const DEFAULT_STREAM_BINDINGS_PATH := "res://modules/f16/F16_PRODUCT_STREAM_BINDINGS_R2.json"

@export var auto_configure_product: bool = true
@export_file("*.json") var product_policy_path: String = DEFAULT_PRODUCT_POLICY_PATH
@export_file("*.json") var stream_bindings_path: String = DEFAULT_STREAM_BINDINGS_PATH

@onready var router: VeilwildInteractiveAudioRouter = $InteractiveAudioRouter

var product_configuration_status: Dictionary = {
    "pass": false,
    "state": "NOT_CONFIGURED",
    "errors": []
}

func _ready() -> void:
    add_to_group("veilwild.f16_audio_runtime")
    router.audio_command_emitted.connect(_on_audio_command_emitted)
    if auto_configure_product:
        var status := configure_product_runtime()
        runtime_configuration_completed.emit(status.duplicate(true))
        if bool(status.get("pass", false)):
            print("VEILWILD_F16_PRODUCT_RUNTIME_READY policies=%d streams=%d" % [int(status.get("policy_count", 0)), int(status.get("stream_count", 0))])
        else:
            push_error("VEILWILD_F16_PRODUCT_RUNTIME_CONFIG_FAIL %s" % JSON.stringify(status))

func configure(policy_rows: Array, stream_bindings: Dictionary = {}) -> PackedStringArray:
    var errors := router.configure(policy_rows)
    if not errors.is_empty():
        return errors
    for cue_semantic_id in stream_bindings.keys():
        var stream = stream_bindings[cue_semantic_id]
        if stream is AudioStream:
            router.register_stream(str(cue_semantic_id), stream)
        else:
            errors.append("stream binding %s is not AudioStream" % str(cue_semantic_id))
    return errors

func configure_resource_bindings(policy_rows: Array, binding_rows: Array) -> PackedStringArray:
    var streams: Dictionary = {}
    var errors := PackedStringArray()
    for index in range(binding_rows.size()):
        var row = binding_rows[index]
        if typeof(row) != TYPE_DICTIONARY:
            errors.append("binding[%d] must be Dictionary" % index)
            continue
        var cue_id := str(row.get("cue_semantic_id", ""))
        var resource_path := str(row.get("resource_path", ""))
        if cue_id.is_empty() or resource_path.is_empty():
            errors.append("binding[%d] requires cue_semantic_id and resource_path" % index)
            continue
        if not ResourceLoader.exists(resource_path):
            errors.append("binding[%d] resource does not exist: %s" % [index, resource_path])
            continue
        var resource = load(resource_path)
        if not resource is AudioStream:
            errors.append("binding[%d] resource is not AudioStream: %s" % [index, resource_path])
            continue
        streams[cue_id] = resource
    if not errors.is_empty():
        return errors
    return configure(policy_rows, streams)

func configure_mix_profiles(profile_rows: Array) -> PackedStringArray:
    var errors := PackedStringArray()
    for index in range(profile_rows.size()):
        var row = profile_rows[index]
        if typeof(row) != TYPE_DICTIONARY:
            errors.append("mix[%d] must be Dictionary" % index)
            continue
        var bus_name := str(row.get("bus", ""))
        if bus_name.is_empty() or bus_name == "Master":
            errors.append("mix[%d] requires non-Master bus" % index)
            continue
        var bus_index := AudioServer.get_bus_index(bus_name)
        if bus_index < 0:
            AudioServer.add_bus()
            bus_index = AudioServer.bus_count - 1
            AudioServer.set_bus_name(bus_index, bus_name)
        AudioServer.set_bus_volume_db(bus_index, float(row.get("volume_db", 0.0)))
        AudioServer.set_bus_mute(bus_index, bool(row.get("mute", false)))
    return errors

func configure_product_runtime(policy_path: String = product_policy_path, bindings_path: String = stream_bindings_path) -> Dictionary:
    var errors := PackedStringArray()
    if not FileAccess.file_exists(policy_path):
        errors.append("product policy missing: %s" % policy_path)
    if not FileAccess.file_exists(bindings_path):
        errors.append("stream bindings missing: %s" % bindings_path)
    if not errors.is_empty():
        product_configuration_status = {
            "pass": false,
            "state": "INPUT_MISSING",
            "policy_path": policy_path,
            "bindings_path": bindings_path,
            "errors": Array(errors)
        }
        return product_configuration_status.duplicate(true)

    var policy_doc = JSON.parse_string(FileAccess.get_file_as_string(policy_path))
    var bindings_doc = JSON.parse_string(FileAccess.get_file_as_string(bindings_path))
    if typeof(policy_doc) != TYPE_DICTIONARY:
        errors.append("product policy must parse as Dictionary")
    if typeof(bindings_doc) != TYPE_DICTIONARY:
        errors.append("stream bindings must parse as Dictionary")
    if not errors.is_empty():
        product_configuration_status = {
            "pass": false,
            "state": "INPUT_INVALID",
            "policy_path": policy_path,
            "bindings_path": bindings_path,
            "errors": Array(errors)
        }
        return product_configuration_status.duplicate(true)

    for error in configure_mix_profiles(policy_doc.get("mixProfiles", [])):
        errors.append(error)
    for error in configure_resource_bindings(policy_doc.get("policies", []), bindings_doc.get("bindings", [])):
        errors.append(error)

    product_configuration_status = {
        "pass": errors.is_empty(),
        "state": "READY" if errors.is_empty() else "CONFIGURATION_REJECTED",
        "policy_path": policy_path,
        "bindings_path": bindings_path,
        "policy_count": policy_doc.get("policies", []).size(),
        "stream_count": router.stream_binding_count(),
        "errors": Array(errors)
    }
    return product_configuration_status.duplicate(true)

func candidate_health() -> Dictionary:
    return product_configuration_status.duplicate(true)

func consume_f13_behavior_transition(event: Dictionary, source_position_m, source_event_id: String = "") -> Array:
    var required := ["behaviorStateId", "transitionSemanticId", "transitionSequence", "playerCueAuthorization"]
    for field in required:
        if not event.has(field):
            return router.process_event({})
    var event_id := source_event_id
    if event_id.is_empty():
        event_id = "f13-transition:%s:%s" % [str(event["transitionSequence"]), str(event["transitionSemanticId"])]
    return consume_audio_semantic_event({
        "behavior_state_id": str(event["behaviorStateId"]),
        "transition_kind": "ENTER",
        "transition_reason_id": str(event["transitionSemanticId"]),
        "event_id": event_id,
        "source_position_m": source_position_m,
        "player_cue_authorization": event["playerCueAuthorization"]
    })

func consume_audio_semantic_event(event: Dictionary) -> Array:
    return router.process_event(event)

func listener_condition() -> Dictionary:
    var current_camera := get_viewport().get_camera_3d()
    var current_listeners: Array[AudioListener3D] = []
    _collect_current_audio_listeners(get_tree().root, current_listeners)
    return {
        "listener_owner": "A25/F18 or integrated runtime",
        "camera_3d_present": current_camera != null,
        "current_audio_listener_count": current_listeners.size(),
        "audio_listener_3d_present": not current_listeners.is_empty(),
        "audio_listener_transform": null if current_listeners.is_empty() else current_listeners[0].get_listener_transform(),
        "world_basis": {"unit": "meter", "right": "+X", "up": "+Y", "forward": "-Z"}
    }

func _collect_current_audio_listeners(node: Node, out: Array[AudioListener3D]) -> void:
    if node is AudioListener3D and node.is_current():
        out.append(node)
    for child in node.get_children():
        _collect_current_audio_listeners(child, out)

func stop_all_audio_loops() -> void:
    router.stop_all()

func _on_audio_command_emitted(command: Dictionary) -> void:
    var action := str(command.get("action", ""))
    if action == "PLAY_ONE_SHOT" or action == "START_LOOP":
        if str(command.get("binding_status", "")) == "BOUND":
            evidence_event_ready.emit(_make_f22_event("audio_cue_started", command, action))
        return

    if action == "STOP_GROUP" or action == "SILENCE_ALL":
        for stopped in command.get("stopped_cues", []):
            if typeof(stopped) == TYPE_DICTIONARY:
                evidence_event_ready.emit(_make_f22_event("audio_cue_stopped", stopped, action))

func _make_f22_event(event_type: String, semantic: Dictionary, reason: String) -> Dictionary:
    return {
        "eventType": event_type,
        "sourceFront": "A16/F16",
        "producerSemanticId": str(semantic.get("cue_semantic_id", "")),
        "reasonId": reason,
        "cueClass": str(semantic.get("cue_class_id", "")),
        "worldPositionMeters": semantic.get("source_position_m", null),
        "producerData": {
            "audioCommandSequence": int(semantic.get("command_sequence", 0)),
            "behaviorStateId": str(semantic.get("behavior_state_id", "")),
            "transitionKind": str(semantic.get("transition_kind", "")),
            "sourceEventId": str(semantic.get("event_id", "")),
            "bindingStatus": str(semantic.get("binding_status", "")),
            "bus": str(semantic.get("bus", "")),
            "priorityRank": int(semantic.get("priority_rank", 0)),
            "spatial": bool(semantic.get("spatial", false)),
            "criticality": str(semantic.get("criticality", "UNDECLARED")),
            "primaryCarrier": "AUDIO_SPATIAL" if bool(semantic.get("spatial", false)) else "AUDIO_NONSPATIAL",
            "redundantCarrierOrRoute": str(semantic.get("redundant_carrier_or_route", "UNDECLARED")),
            "captionOrVisualAlternative": str(semantic.get("caption_or_visual_alternative", "UNDECLARED")),
            "spatialInformationClass": str(semantic.get("spatial_information_class", "UNDECLARED"))
        }
    }
