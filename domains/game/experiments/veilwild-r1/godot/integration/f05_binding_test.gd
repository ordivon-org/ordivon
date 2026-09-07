extends SceneTree

const REQUIRED_MARKERS: Array[StringName] = [&"VW_MARKER_ApproachAnchor_North", &"VW_MARKER_ApproachAnchor_South", &"VW_MARKER_ApproachAnchor_West", &"VW_MARKER_ConcealCandidate_FallenLog", &"VW_MARKER_ConcealCandidate_NorthFern", &"VW_MARKER_ConcealCandidate_RockRidge", &"VW_MARKER_SearchLandmark_Glade"]

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var scene := load("res://main.tscn") as PackedScene
    if scene == null:
        push_error("A17/F05 binding: main scene missing")
        quit(2); return
    var integration := scene.instantiate()
    root.add_child(integration)
    await process_frame
    if not integration.loaded_modules.has("environment"):
        push_error("A17/F05 binding: environment not recorded")
        quit(3); return
    var mount := integration.get_node_or_null("EnvironmentMount")
    if mount == null or mount.get_child_count() != 1:
        push_error("A17/F05 binding: expected exactly one environment root")
        quit(4); return
    var env_root := mount.get_child(0)
    var mesh_count := _count_meshes(env_root)
    if mesh_count != 153:
        push_error("A17/F05 binding: mesh inventory drift expected=153 actual=%d" % mesh_count)
        quit(5); return
    for marker in REQUIRED_MARKERS:
        if env_root.find_child(String(marker), true, false) == null:
            push_error("A17/F05 binding: missing producer marker %s" % marker)
            quit(6); return
    print("VEILWILD_A17_F05_BINDING_VALID meshes=%d markers=%d" % [mesh_count, REQUIRED_MARKERS.size()])
    quit(0)

func _count_meshes(node: Node) -> int:
    var total := 1 if node is MeshInstance3D else 0
    for child in node.get_children():
        total += _count_meshes(child)
    return total
