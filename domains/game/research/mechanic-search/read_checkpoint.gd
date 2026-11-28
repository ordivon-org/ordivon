extends SceneTree
func _initialize() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 1:
        quit(2)
        return
    var cfg := ConfigFile.new()
    if cfg.load(args[0]) != OK or cfg.get_value("run", "schema_version", null) != 1:
        quit(2)
        return
    var cp: Variant = cfg.get_value("run", "checkpoint", null)
    if not cp is Dictionary:
        quit(2)
        return
    print("STUDY_CHECKPOINT=" + JSON.stringify(cp))
    quit(0)
