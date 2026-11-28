extends SceneTree

# Verify the real Godot texture importer, scene loader, and native appearance
# replacement. This is not an engine-independent or player-enjoyment proof.
func _initialize() -> void:
    call_deferred("_verify")

func _verify() -> void:
    var blueprint := load("res://main.tscn") as PackedScene
    var alternate_blueprint := load("res://alternate_avatar.tscn") as PackedScene
    if blueprint == null or alternate_blueprint == null:
        _fail("PackedScene load")
        return
    var composition := blueprint.instantiate() as Node2D
    if composition == null:
        _fail("root Node2D")
        return
    root.add_child(composition)
    var original := composition.get_node_or_null("Avatar") as Sprite2D
    var replacement := alternate_blueprint.instantiate() as Sprite2D
    if original == null or replacement == null:
        _fail("native Sprite2D component")
        return
    if original.texture == null or replacement.texture == null:
        _fail("imported Texture2D")
        return
    var baseline_bytes := original.texture.get_image().get_data()
    var alternate_bytes := replacement.texture.get_image().get_data()
    var original_size := original.texture.get_size()
    var replacement_size := replacement.texture.get_size()
    if original_size.x <= 0 or original_size.y <= 0 or replacement_size.x <= 0 or replacement_size.y <= 0:
        _fail("non-empty texture")
        return
    if baseline_bytes == alternate_bytes:
        _fail("distinct interchangeable pixel content")
        return
    var previous_position := original.position
    composition.remove_child(original)
    original.free()
    composition.add_child(replacement)
    if composition.get_node_or_null("Avatar") != replacement or replacement.position != previous_position:
        _fail("scene substitution")
        return
    if composition.get_child_count() != 1:
        _fail("single-consumer composition")
        return
    print("GAME_NATIVE_VISUAL_COMPOSITION_PASS original_size=", original_size, " replacement_size=", replacement_size, " substitutions=1")
    composition.free()
    quit(0)

func _fail(reason: String) -> void:
    printerr("GAME_NATIVE_VISUAL_COMPOSITION_FAIL ", reason)
    quit(1)
