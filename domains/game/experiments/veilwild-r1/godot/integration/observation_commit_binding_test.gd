extends SceneTree

var captured: Array[Dictionary] = []
var qualification_mode := &"DENY"

func _initialize() -> void:
    call_deferred("_run")

func _on_bus(topic: StringName, payload: Dictionary, source: StringName) -> void:
    captured.append({"topic": topic, "payload": payload.duplicate(true), "source": source})

func _qualify(request_id: int, _origin: Vector3, _forward: Vector3) -> Dictionary:
    return {
        "qualified": qualification_mode == &"ALLOW",
        "sourceFront": "A14/F14",
        "producerSemanticId": "F14.FIXTURE_VALID_CLOSE_OBSERVATION" if qualification_mode == &"ALLOW" else "F14.FIXTURE_NOT_QUALIFIED",
        "requestId": request_id,
    }

func _run() -> void:
    var bus := root.get_node_or_null("VeilwildEventBus")
    if bus == null:
        _fail("EventBus missing", 2); return
    bus.envelope_published.connect(_on_bus)
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        _fail("main missing", 3); return
    var integration = packed.instantiate()
    root.add_child(integration)
    await process_frame
    var binding: Node = integration.call("get_observation_binding")
    if binding == null:
        _fail("observation binding missing", 4); return
    var health: Dictionary = binding.call("get_binding_health")
    if not health.get("runtimeBound", false) or health.get("candidateReady", true):
        _fail("binding must be runtime-bound but candidate-blocked before owner qualifier", 5); return
    var player: Node = integration.loaded_modules["player_runtime"]["instance"]
    if not integration.call("bind_observation_world_qualifier", Callable(self, "_qualify"), &"A14/F14"):
        _fail("owner qualifier binding rejected", 6); return
    health = binding.call("get_binding_health")
    if not health.get("candidateReady", false):
        _fail("binding not ready after explicit owner qualifier", 7); return

    # Request-only + owner deny cannot commit or succeed.
    qualification_mode = &"DENY"
    var r1 := int(player.call("begin_observe_action"))
    var denied: Dictionary = binding.call("evaluate_active_request")
    if denied.get("result") != "NOT_QUALIFIED":
        _fail("denied qualification result drift", 8); return
    if _topic_count(&"observation_committed") != 0 or _topic_count(&"success_consequence") != 0:
        _fail("request/deny path laundered into success", 9); return
    player.call("cancel_observe_action", &"FIXTURE_CANCEL")
    if binding.call("evaluate_active_request").get("result") != "NO_ACTIVE_OBSERVE_REQUEST":
        _fail("cancelled request remained committable", 10); return

    # Pre-success behavior abort must cancel the active F18 request and never commit.
    qualification_mode = &"DENY"
    var r_abort := int(player.call("begin_observe_action"))
    var behavior: Node = integration.loaded_modules["behavior"]["instance"]
    behavior.behavior_transition.emit({"observationAbort": true, "behaviorStateId": "veilwild.behavior.evade.r1"})
    if player.call("is_observe_action_active"):
        _fail("F13 observationAbort did not close active request", 11); return
    if _topic_count(&"observation_committed") != 0 or _topic_count(&"success_consequence") != 0:
        _fail("pre-success behavior abort laundered into success", 12); return

    # Active request + exact owner allow commits once, after F18 start and before UI success.
    qualification_mode = &"ALLOW"
    var r2 := int(player.call("begin_observe_action"))
    if r2 == r1 or r2 == r_abort:
        _fail("request identity did not advance", 13); return
    var committed: Dictionary = binding.call("evaluate_active_request")
    if committed.get("result") != "OBSERVATION_COMMITTED" or int(committed.get("requestId", 0)) != r2:
        _fail("owner-qualified request did not commit", 14); return
    var start_idx := _last_topic_index(&"observe_action_started")
    var commit_idx := _first_topic_index(&"observation_committed")
    var success_idx := _first_topic_index(&"success_consequence")
    if start_idx < 0 or commit_idx < 0 or success_idx < 0 or not (start_idx < commit_idx and commit_idx < success_idx):
        _fail("required order observe_start < commit < success violated", 15); return
    if player.call("is_observe_action_active"):
        _fail("committed request not closed", 16); return
    if _topic_count(&"observation_committed") != 1 or _topic_count(&"success_consequence") != 1:
        _fail("successful encounter must emit exactly one commit and one authorized UI success", 17); return
    if binding.call("evaluate_active_request").get("result") != "ENCOUNTER_ALREADY_COMMITTED":
        _fail("duplicate commit guard missing", 18); return

    print("VEILWILD_A17_OBSERVATION_BINDING_PASS denied_no_success=true cancelled_no_success=true evade_abort_no_success=true observe_start_before_commit_before_success=true exact_request_identity=true")
    quit(0)

func _topic_count(topic: StringName) -> int:
    var count := 0
    for row in captured:
        if row["topic"] == topic:
            count += 1
    return count

func _first_topic_index(topic: StringName) -> int:
    for i in range(captured.size()):
        if captured[i]["topic"] == topic:
            return i
    return -1

func _last_topic_index(topic: StringName) -> int:
    for i in range(captured.size() - 1, -1, -1):
        if captured[i]["topic"] == topic:
            return i
    return -1

func _fail(message: String, code: int) -> void:
    push_error("A17_OBSERVATION_BINDING_FAIL " + message)
    quit(code)
