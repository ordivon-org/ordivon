extends Node3D

const EVIDENCE_PATH := "res://evidence/f11-lighting-fixture.png"

func _ready() -> void:
    await get_tree().process_frame
    await get_tree().process_frame
    await RenderingServer.frame_post_draw
    var image := get_viewport().get_texture().get_image()
    var err := image.save_png(EVIDENCE_PATH)
    if err != OK:
        push_error("F11_CAPTURE_SAVE_FAILED:%s" % err)
        get_tree().quit(2)
        return
    print("F11_CAPTURE_OK path=%s size=%dx%d" % [EVIDENCE_PATH, image.get_width(), image.get_height()])
    get_tree().quit(0)
