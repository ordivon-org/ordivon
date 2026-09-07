extends Node3D
## Engine-owned composition root. It loads producer-owned PackedScenes into stable mounts.
## It deliberately does not define player, creature, cue, animation, audio, or evidence semantics.

const ObservationCommitBinding = preload("res://integration/observation_commit_binding.gd")

const MODULE_SPECS: Array[Dictionary] = [
    {"id": "environment", "setting": "veilwild/integration/environment_scene", "mount": "EnvironmentMount"},
    {"id": "creature", "setting": "veilwild/integration/creature_scene", "mount": "CreatureMount"},
    {"id": "lighting", "setting": "veilwild/integration/lighting_scene", "mount": "LightingMount"},
    {"id": "navigation", "setting": "veilwild/integration/navigation_scene", "mount": "NavigationMount"},
    {"id": "animation_system", "setting": "veilwild/integration/animation_system_scene", "mount": "SystemsMount"},
    {"id": "behavior", "setting": "veilwild/integration/behavior_scene", "mount": "SystemsMount"},
    {"id": "audio", "setting": "veilwild/integration/audio_scene", "mount": "AudioMount"},
    {"id": "player_runtime", "setting": "veilwild/integration/player_runtime_scene", "mount": "PlayerRuntimeMount"},
    {"id": "evidence", "setting": "veilwild/integration/evidence_scene", "mount": "EvidenceMount"},
    {"id": "ui", "setting": "veilwild/integration/ui_scene", "mount": "UIOverlay"},
]

var loaded_modules: Dictionary = {}
var load_failures: Array[String] = []
var observation_binding: Node = null
var integration_failures: Array[String] = []

func _ready() -> void:
    add_to_group("veilwild.integration_root")
    _load_configured_modules()
    _bind_observation_commit_adapter()
    var status := candidate_health(bool(ProjectSettings.get_setting("veilwild/integration/strict_candidate", false)))
    if status["pass"]:
        print("VEILWILD_ENGINE_COMPOSITION_HEALTH_PASS loaded=%d strict=%s" % [loaded_modules.size(), status["strict"]])
    else:
        push_error("VEILWILD_ENGINE_COMPOSITION_HEALTH_FAIL %s" % JSON.stringify(status))

func get_mount(mount_name: StringName) -> Node:
    return get_node_or_null(NodePath(String(mount_name)))

func candidate_health(strict: bool = false) -> Dictionary:
    var missing: Array[String] = []
    if strict:
        for spec in MODULE_SPECS:
            if not loaded_modules.has(spec["id"]):
                missing.append(spec["id"])
    var observation_health: Dictionary = {} if observation_binding == null else observation_binding.call("get_binding_health")
    var integration_ok := integration_failures.is_empty()
    var observation_ready := bool(observation_health.get("candidateReady", false))
    return {
        "pass": load_failures.is_empty() and integration_ok and (not strict or (missing.is_empty() and observation_ready)),
        "strict": strict,
        "loadedModules": loaded_modules.keys(),
        "loadFailures": load_failures.duplicate(),
        "integrationFailures": integration_failures.duplicate(),
        "missingModules": missing,
        "observationBinding": observation_health,
    }

func _load_configured_modules() -> void:
    for spec in MODULE_SPECS:
        var raw_path: Variant = ProjectSettings.get_setting(spec["setting"], "")
        if not (raw_path is String) or raw_path.is_empty():
            continue
        var scene_path := String(raw_path)
        var mount := get_node_or_null(NodePath(spec["mount"]))
        if mount == null:
            load_failures.append("missing mount %s for %s" % [spec["mount"], spec["id"]])
            continue
        if not ResourceLoader.exists(scene_path, "PackedScene"):
            load_failures.append("missing PackedScene %s for %s" % [scene_path, spec["id"]])
            continue
        var resource := ResourceLoader.load(scene_path, "PackedScene")
        if not (resource is PackedScene):
            load_failures.append("not PackedScene %s for %s" % [scene_path, spec["id"]])
            continue
        var instance := (resource as PackedScene).instantiate()
        mount.add_child(instance)
        loaded_modules[spec["id"]] = {"path": scene_path, "instance": instance}

func get_observation_binding() -> Node:
    return observation_binding

func bind_observation_world_qualifier(qualifier: Callable, owner_source_front: StringName) -> bool:
    if observation_binding == null:
        return false
    return bool(observation_binding.call("bind_world_qualifier", qualifier, owner_source_front))

func _bind_observation_commit_adapter() -> void:
    observation_binding = ObservationCommitBinding.new()
    observation_binding.name = "ObservationCommitBinding"
    var systems_mount := get_node_or_null("SystemsMount")
    if systems_mount == null:
        integration_failures.append("missing SystemsMount for observation binding")
        observation_binding = null
        return
    systems_mount.add_child(observation_binding)
    var player: Node = null
    var ui: Node = null
    var behavior: Node = null
    if loaded_modules.has("player_runtime"):
        player = loaded_modules["player_runtime"]["instance"]
    if loaded_modules.has("ui"):
        ui = loaded_modules["ui"]["instance"]
    if loaded_modules.has("behavior"):
        behavior = loaded_modules["behavior"]["instance"]
    var errors: Array = observation_binding.call("bind_runtime", player, ui, behavior)
    for error in errors:
        integration_failures.append("observation binding: " + str(error))
