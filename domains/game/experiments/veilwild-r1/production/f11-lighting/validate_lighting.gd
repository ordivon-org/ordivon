extends SceneTree

const RIG_PATH := "res://lighting_rig.tscn"

func fail(message: String) -> void:
    push_error("F11_VALIDATE_FAIL:" + message)
    quit(2)

func _initialize() -> void:
    var packed: PackedScene = load(RIG_PATH) as PackedScene
    if packed == null:
        fail("rig_load")
        return
    var rig: Node = packed.instantiate()
    root.add_child(rig)
    var world := rig.get_node_or_null("WorldEnvironment") as WorldEnvironment
    var sun := rig.get_node_or_null("KeySun") as DirectionalLight3D
    if world == null or world.environment == null:
        fail("explicit_world_environment_missing")
        return
    if sun == null:
        fail("explicit_directional_light_missing")
        return
    if not sun.shadow_enabled:
        fail("sun_shadows_disabled")
        return
    if sun.directional_shadow_max_distance < 24.0 or sun.directional_shadow_max_distance > 64.0:
        fail("shadow_distance_out_of_fixture_envelope")
        return
    if sun.light_energy < 0.6 or sun.light_energy > 1.6:
        fail("key_energy_out_of_fixture_envelope")
        return
    var env := world.environment
    if env.ambient_light_energy < 0.15 or env.ambient_light_energy > 0.55:
        fail("ambient_energy_out_of_fixture_envelope")
        return
    if env.background_mode != Environment.BG_COLOR:
        fail("unexpected_background_mode")
        return
    print("F11_VALIDATE_PASS key_energy=%.3f ambient_energy=%.3f shadow_max=%.1f mode=%d" % [sun.light_energy, env.ambient_light_energy, sun.directional_shadow_max_distance, sun.directional_shadow_mode])
    quit(0)
