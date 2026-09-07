extends SceneTree

const MAX_READY_FRAMES := 240

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17 final strict health: main scene did not load")
        quit(2)
        return
    var integration := packed.instantiate()
    root.add_child(integration)
    await process_frame

    var ready := false
    var last_wait_witness: Dictionary = {}
    for frame_index in range(MAX_READY_FRAMES):
        last_wait_witness = _readiness_witness(integration)
        if bool(last_wait_witness.get("ready", false)):
            ready = true
            break
        await physics_frame
    if not ready:
        push_error("A17 final strict health: bounded readiness timeout %s" % JSON.stringify(last_wait_witness))
        quit(3)
        return

    var status: Dictionary = integration.candidate_health(true)
    if not bool(status.get("pass", false)):
        push_error("A17 final strict health: candidate_health(true) failed %s" % JSON.stringify(status))
        quit(4)
        return
    if not (status.get("missingModules", []) as Array).is_empty():
        push_error("A17 final strict health: missing modules after readiness")
        quit(5)
        return
    if not (status.get("loadFailures", []) as Array).is_empty() or not (status.get("integrationFailures", []) as Array).is_empty():
        push_error("A17 final strict health: load/integration failure after readiness")
        quit(6)
        return

    var observation: Dictionary = status.get("observationBinding", {})
    if not bool(observation.get("candidateReady", false)) or not bool(observation.get("ownerWorldQualifierBound", false)) or String(observation.get("worldQualifierOwner", "")) != "A14/F14":
        push_error("A17 final strict health: exact A14 world qualifier identity missing %s" % JSON.stringify(observation))
        quit(7)
        return

    var animation: Dictionary = status.get("animationBinding", {})
    var strict_snapshot: Dictionary = animation.get("strictProbeSnapshot", {})
    if not bool(animation.get("candidateReady", false)) or not bool(animation.get("strictProbePass", false)):
        push_error("A17 final strict health: A09 strict path not ready %s" % JSON.stringify(animation))
        quit(8)
        return
    if String(strict_snapshot.get("behavior_state_id", "")) != "veilwild.behavior.unaware.r1" or String(strict_snapshot.get("clip_name", "")) != "VW_MOTION_IDLE" or int(strict_snapshot.get("transition_serial", 0)) != 1:
        push_error("A17 final strict health: F13->F09->final-creature witness drift %s" % JSON.stringify(strict_snapshot))
        quit(9)
        return

    var nav_instance: Node = integration.loaded_modules["navigation"]["instance"]
    if not nav_instance.has_method("runtime_snapshot"):
        push_error("A17 final strict health: A14 navigation runtime lacks runtime_snapshot")
        quit(10)
        return
    var nav: Dictionary = nav_instance.call("runtime_snapshot")
    if not bool(nav.get("initialized", false)) or not (nav.get("failureReasons", []) as Array).is_empty():
        push_error("A17 final strict health: A14 navigation not initialized cleanly %s" % JSON.stringify(nav))
        quit(11)
        return

    print("VEILWILD_A17_FINAL_STRICT_HEALTH_PASS loaded=%d owner=A14/F14 animation=%s/%s serial=%d nav_player_iter=%s nav_creature_iter=%s" % [
        integration.loaded_modules.size(),
        strict_snapshot.get("behavior_state_id", ""),
        strict_snapshot.get("clip_name", ""),
        int(strict_snapshot.get("transition_serial", 0)),
        str(nav.get("navigationMapIteration", {}).get("player", 0)),
        str(nav.get("navigationMapIteration", {}).get("creature", 0)),
    ])
    quit(0)

func _readiness_witness(integration: Node) -> Dictionary:
    var modules: Variant = integration.get("loaded_modules")
    if not (modules is Dictionary):
        return {"ready": false, "reason": "loaded_modules_unavailable"}
    var loaded: Dictionary = modules
    if not loaded.has("navigation"):
        return {"ready": false, "reason": "navigation_not_loaded", "loadedCount": loaded.size()}
    var nav_instance: Node = loaded["navigation"]["instance"]
    var nav_ready := nav_instance.has_method("is_initialized") and bool(nav_instance.call("is_initialized"))
    var observation: Dictionary = {} if integration.observation_binding == null else integration.observation_binding.call("get_binding_health")
    var animation: Dictionary = {} if integration.animation_binding == null else integration.animation_binding.call("snapshot")
    var ready: bool = nav_ready and bool(observation.get("candidateReady", false)) and bool(observation.get("ownerWorldQualifierBound", false)) and String(observation.get("worldQualifierOwner", "")) == "A14/F14" and bool(animation.get("candidateReady", false)) and integration.load_failures.is_empty() and integration.integration_failures.is_empty()
    return {
        "ready": ready,
        "navigationInitialized": nav_ready,
        "ownerWorldQualifierBound": bool(observation.get("ownerWorldQualifierBound", false)),
        "worldQualifierOwner": String(observation.get("worldQualifierOwner", "")),
        "animationReady": bool(animation.get("candidateReady", false)),
        "loadedCount": loaded.size(),
        "loadFailures": integration.load_failures.duplicate(),
        "integrationFailures": integration.integration_failures.duplicate(),
    }
