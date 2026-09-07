extends SceneTree

var failures: Array[String] = []
var integration_instance: Node = null

func _init() -> void:
	var scene = load("res://main.tscn")
	if not (scene is PackedScene):
		_fail("A17 main.tscn must load as PackedScene")
		_finish()
		return
	integration_instance = scene.instantiate()
	root.add_child(integration_instance)
	# Node _ready/module mounting completes on the SceneTree lifecycle boundary.
	# Check on the next process frame rather than racing it from SceneTree._init().
	process_frame.connect(_check_after_ready, CONNECT_ONE_SHOT)

func _check_after_ready() -> void:
	if not integration_instance.loaded_modules.has("behavior"):
		_fail("A17 integration root did not mount configured behavior module")
	var behavior_nodes := get_nodes_in_group("veilwild.f13_behavior_runtime")
	if behavior_nodes.size() != 1:
		_fail("expected exactly one F13 behavior runtime mounted; got %d" % behavior_nodes.size())
	elif not behavior_nodes[0].has_method("submit_perception"):
		_fail("mounted F13 runtime lacks submit_perception")
	var health = integration_instance.candidate_health(false)
	if not bool(health["pass"]):
		_fail("non-strict A17 shell health failed after F13 mount: %s" % JSON.stringify(health))
	if failures.is_empty():
		print("F13_A17_MOUNT_PASS loaded_behavior=true")
	_finish()

func _fail(message: String) -> void:
	failures.append(message)
	push_error(message)

func _finish() -> void:
	quit(0 if failures.is_empty() else 1)
