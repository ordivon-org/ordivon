extends Node

# Godot-native storage adapter; rules own validity and restoration.
@export var slot_path: String = "user://room_encounter_run.cfg"
const SCHEMA_VERSION: int = 1

func save_rules(rules: Node) -> bool:
    var config := ConfigFile.new()
    config.set_value("run", "schema_version", SCHEMA_VERSION)
    config.set_value("run", "checkpoint", rules.checkpoint())
    return config.save(slot_path) == OK

func load_rules(rules: Node) -> bool:
    var config := ConfigFile.new()
    if config.load(slot_path) != OK:
        return false
    if config.get_value("run", "schema_version", null) != SCHEMA_VERSION:
        return false
    return rules.restore_checkpoint(config.get_value("run", "checkpoint", null))
