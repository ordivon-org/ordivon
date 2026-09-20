extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://main.tscn") as PackedScene
    if packed == null:
        push_error("A17/F11 binding: main scene did not load")
        quit(2)
        return
    var instance := packed.instantiate()
    root.add_child(instance)
    await process_frame
    if not instance.loaded_modules.has("lighting"):
        push_error("A17/F11 binding: integration root did not record lighting module")
        quit(3)
        return
    var rig := instance.get_node_or_null("LightingMount/VeilwildLightingRig")
    var environment := instance.get_node_or_null("LightingMount/VeilwildLightingRig/WorldEnvironment")
    var key_sun := instance.get_node_or_null("LightingMount/VeilwildLightingRig/KeySun")
    if rig == null or environment == null or key_sun == null:
        push_error("A17/F11 binding: producer scene structure was not preserved under LightingMount")
        quit(4)
        return
    if not (key_sun is DirectionalLight3D) or not (environment is WorldEnvironment):
        push_error("A17/F11 binding: producer node types changed at mount boundary")
        quit(5)
        return
    print("VEILWILD_A17_F11_BINDING_VALID mount=LightingMount")
    quit(0)
