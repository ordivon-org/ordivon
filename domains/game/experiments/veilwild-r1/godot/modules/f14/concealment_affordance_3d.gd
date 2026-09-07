class_name ConcealmentAffordance3D
extends Area3D

## F14-owned runtime representation for one authored concealment context.
## concealment_suitability is a game/runtime suitability signal only. It is not
## a Human detectability probability or a biological-fidelity claim.

@export var affordance_id: StringName
@export_range(0.0, 1.0, 0.01) var concealment_suitability: float = 0.5
@export var traversal_eligible: bool = true
@export var evasion_eligible: bool = true
@export var navigation_anchor_path: NodePath
@export var environment_revision: String = "UNBOUND"

func _ready() -> void:
    add_to_group("veilwild_concealment_affordance")

func navigation_anchor() -> Marker3D:
    if navigation_anchor_path.is_empty():
        return null
    return get_node_or_null(navigation_anchor_path) as Marker3D

func world_navigation_anchor() -> Vector3:
    var anchor := navigation_anchor()
    if anchor == null:
        return global_position
    return anchor.global_position

func enabled_collision_shape_count() -> int:
    var count := 0
    for child in get_children():
        var shape := child as CollisionShape3D
        if shape != null and not shape.disabled and shape.shape != null:
            count += 1
    return count

func validate_contract() -> PackedStringArray:
    var errors := PackedStringArray()
    if String(affordance_id).strip_edges().is_empty():
        errors.append("affordance_id_empty")
    if environment_revision.strip_edges().is_empty() or environment_revision == "UNBOUND":
        errors.append("environment_revision_unbound")
    if enabled_collision_shape_count() == 0:
        errors.append("collision_volume_missing")
    if traversal_eligible and navigation_anchor() == null:
        errors.append("traversal_anchor_missing")
    if evasion_eligible and not traversal_eligible:
        errors.append("evasion_requires_traversal")
    if concealment_suitability < 0.0 or concealment_suitability > 1.0:
        errors.append("concealment_suitability_out_of_range")
    return errors

func contract_snapshot() -> Dictionary:
    var anchor := navigation_anchor()
    return {
        "affordanceId": String(affordance_id),
        "concealmentSuitability": concealment_suitability,
        "traversalEligible": traversal_eligible,
        "evasionEligible": evasion_eligible,
        "worldCenterM": global_position,
        "navigationAnchorM": anchor.global_position if anchor != null else null,
        "environmentRevision": environment_revision,
        "enabledCollisionShapes": enabled_collision_shape_count(),
    }
