extends Node
class_name VeilwildObservationCommitBinding
## A17/F17 narrow gameplay integration adapter.
## It owns request lifecycle/ordering only. It NEVER computes world qualification.
## The actual close-observation predicate must be supplied by an owner-bound Callable.

const OBSERVATION_COMMITTED_TOPIC: StringName = &"observation_committed"
const SEMANTIC_OBSERVATION_COMMITTED := "F17.OBSERVATION_COMMITTED_OWNER_QUALIFIED"

var _player: Node = null
var _ui: Node = null
var _behavior: Node = null
var _world_qualifier: Callable = Callable()
var _world_qualifier_owner: StringName = &""
var _active_request_id: int = 0
var _active_origin := Vector3.ZERO
var _active_forward := Vector3.ZERO
var _encounter_committed := false
var _last_qualification: Dictionary = {}
var _binding_errors: Array[String] = []

func bind_runtime(player: Node, ui: Node, behavior: Node) -> Array[String]:
    _binding_errors.clear()
    _player = player
    _ui = ui
    _behavior = behavior
    if _player == null or not _player.has_signal("observe_requested") or not _player.has_signal("observe_cancelled"):
        _binding_errors.append("F18_PLAYER_OBSERVE_SIGNALS_MISSING")
    if _player == null or not _player.has_method("close_observe_request") or not _player.has_method("cancel_observe_action"):
        _binding_errors.append("F18_PLAYER_REQUEST_LIFECYCLE_API_MISSING")
    if _ui == null or not _ui.has_method("present_feedback"):
        _binding_errors.append("F18_UI_PRESENTATION_API_MISSING")
    if _behavior == null or not _behavior.has_signal("behavior_transition"):
        _binding_errors.append("F13_BEHAVIOR_TRANSITION_SIGNAL_MISSING")
    if not _binding_errors.is_empty():
        return _binding_errors.duplicate()
    if not _player.observe_requested.is_connected(_on_observe_requested):
        _player.observe_requested.connect(_on_observe_requested)
    if not _player.observe_cancelled.is_connected(_on_observe_cancelled):
        _player.observe_cancelled.connect(_on_observe_cancelled)
    if not _behavior.behavior_transition.is_connected(_on_behavior_transition):
        _behavior.behavior_transition.connect(_on_behavior_transition)
    return []

func bind_world_qualifier(qualifier: Callable, owner_source_front: StringName) -> bool:
    if not qualifier.is_valid() or owner_source_front == &"" or owner_source_front == &"A17/F17":
        return false
    _world_qualifier = qualifier
    _world_qualifier_owner = owner_source_front
    return true

func clear_world_qualifier() -> void:
    _world_qualifier = Callable()
    _world_qualifier_owner = &""

func candidate_ready() -> bool:
    return _binding_errors.is_empty() and _player != null and _ui != null and _behavior != null and _world_qualifier.is_valid() and _world_qualifier_owner != &""

func get_binding_health() -> Dictionary:
    return {
        "runtimeBound": _binding_errors.is_empty() and _player != null and _ui != null and _behavior != null,
        "ownerWorldQualifierBound": _world_qualifier.is_valid() and _world_qualifier_owner != &"",
        "worldQualifierOwner": String(_world_qualifier_owner),
        "candidateReady": candidate_ready(),
        "bindingErrors": _binding_errors.duplicate(),
        "activeRequestId": _active_request_id,
        "encounterCommitted": _encounter_committed,
    }

func evaluate_active_request() -> Dictionary:
    if _encounter_committed:
        return {"ok": false, "result": "ENCOUNTER_ALREADY_COMMITTED"}
    if _active_request_id <= 0:
        return {"ok": false, "result": "NO_ACTIVE_OBSERVE_REQUEST"}
    if not _world_qualifier.is_valid():
        return {"ok": false, "result": "OWNER_WORLD_QUALIFIER_NOT_BOUND"}
    var result = _world_qualifier.call(_active_request_id, _active_origin, _active_forward)
    if typeof(result) != TYPE_DICTIONARY:
        return {"ok": false, "result": "OWNER_QUALIFICATION_NOT_DICTIONARY"}
    var witness: Dictionary = result
    _last_qualification = witness.duplicate(true)
    if witness.get("qualified", false) != true:
        return {"ok": true, "result": "NOT_QUALIFIED", "ownerWitness": witness.duplicate(true)}
    var source_front := StringName(str(witness.get("sourceFront", "")))
    var producer_semantic_id := str(witness.get("producerSemanticId", ""))
    if source_front != _world_qualifier_owner or producer_semantic_id.is_empty():
        return {"ok": false, "result": "OWNER_QUALIFICATION_IDENTITY_INVALID"}
    return _commit_active_request(witness)

func reset_encounter() -> bool:
    if _active_request_id != 0:
        return false
    _encounter_committed = false
    _last_qualification.clear()
    return true

func _on_observe_requested(request_id: int, origin: Vector3, forward: Vector3) -> void:
    if _encounter_committed:
        if _player != null and _player.has_method("close_observe_request"):
            _player.call("close_observe_request", request_id, &"ENCOUNTER_ALREADY_COMMITTED")
        return
    _active_request_id = request_id
    _active_origin = origin
    _active_forward = forward
    # F18 publishes observe_action_started only after observe_requested returns.
    # Defer owner evaluation so observation_committed can never precede the explicit start event.
    if _world_qualifier.is_valid():
        call_deferred("_evaluate_deferred_request", request_id)

func _evaluate_deferred_request(request_id: int) -> void:
    if request_id != _active_request_id or _encounter_committed:
        return
    evaluate_active_request()

func _on_observe_cancelled(request_id: int, _reason_id: StringName) -> void:
    if request_id == _active_request_id:
        _clear_active_request()

func _on_behavior_transition(event: Dictionary) -> void:
    if _active_request_id <= 0 or _encounter_committed:
        return
    if bool(event.get("observationAbort", false)):
        var request_id := _active_request_id
        _clear_active_request()
        if _player != null and _player.has_method("cancel_observe_action"):
            _player.call("cancel_observe_action", &"F13_OBSERVATION_ABORT")
        # F18 cancellation remains producer-owned. This branch deliberately emits no commit/success.
        if request_id <= 0:
            push_error("F17 observation abort lost request identity")

func _commit_active_request(owner_witness: Dictionary) -> Dictionary:
    var request_id := _active_request_id
    if request_id <= 0 or _player == null or _ui == null:
        return {"ok": false, "result": "RUNTIME_NOT_BOUND"}
    if not bool(_player.call("is_observe_action_active")):
        _clear_active_request()
        return {"ok": false, "result": "F18_REQUEST_NOT_ACTIVE"}

    # Event ordering is synchronous: commitment is published before UI is authorized
    # to present SUCCESS_CONSEQUENCE. UI owns presentation; F01 owns product semantics.
    _publish_commit(request_id, owner_witness)
    var closed := bool(_player.call("close_observe_request", request_id, &"OBSERVATION_COMMITTED"))
    if not closed:
        return {"ok": false, "result": "F18_REQUEST_CLOSE_FAILED"}
    _clear_active_request()
    _encounter_committed = true
    var presented := bool(_ui.call("present_feedback", &"SUCCESS_CONSEQUENCE"))
    if not presented:
        _encounter_committed = false
        return {"ok": false, "result": "F18_SUCCESS_PRESENTATION_REJECTED"}
    return {"ok": true, "result": "OBSERVATION_COMMITTED", "requestId": request_id, "ownerWitness": owner_witness.duplicate(true)}

func _publish_commit(request_id: int, owner_witness: Dictionary) -> void:
    var bus := get_node_or_null("/root/VeilwildEventBus")
    if bus == null or not bus.has_method("publish"):
        push_error("F17 observation binding requires VeilwildEventBus")
        return
    bus.call("publish", OBSERVATION_COMMITTED_TOPIC, {
        "sourceFront": "A17/F17",
        "producerSemanticId": SEMANTIC_OBSERVATION_COMMITTED,
        "producerData": {
            "requestId": request_id,
            "qualificationSourceFront": str(owner_witness.get("sourceFront", "")),
            "qualificationProducerSemanticId": str(owner_witness.get("producerSemanticId", "")),
        },
    }, &"F17")

func _clear_active_request() -> void:
    _active_request_id = 0
    _active_origin = Vector3.ZERO
    _active_forward = Vector3.ZERO
