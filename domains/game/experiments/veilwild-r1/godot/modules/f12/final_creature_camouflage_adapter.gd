class_name VeilwildFinalCreatureCamouflageAdapter
extends Node

# Owner-side adapter for the final A10 material-bound animated creature. A17 may
# attach this node to the exact loaded CreatureMount instance and call
# bind_creature(). It validates exact F10 material identity before applying F12
# instance-local surface overrides; it never rewrites the imported mesh/GLB.
const DORSAL_NAME := "VR_SURFACE_DORSAL_SLOT"
const VENTRAL_NAME := "VR_SURFACE_VENTRAL_SLOT"
const EYE_NAME := "VR_SURFACE_EYE_SLOT"
const SLOT_BY_MATERIAL_NAME := {
    DORSAL_NAME: &"VR_SURFACE_DORSAL_SLOT",
    VENTRAL_NAME: &"VR_SURFACE_VENTRAL_SLOT",
}
const EXPECTED := {
    DORSAL_NAME: {"base": "526153", "roughness": 0.78},
    VENTRAL_NAME: {"base": "6d7869", "roughness": 0.68},
    EYE_NAME: {"base": "1b2a23", "roughness": 0.90},
}

var binding: Node = null
var bound_creature: Node = null
var last_error := ""
var matched_surface_counts := {}

func bind_creature(creature_root: Node) -> bool:
    if creature_root == null:
        last_error = "creature_root_missing"
        return false
    if bound_creature != null:
        last_error = "adapter_already_bound"
        return false
    var matches := {DORSAL_NAME: [], VENTRAL_NAME: [], EYE_NAME: []}
    _collect_material_surfaces(creature_root, matches)
    for material_name in [DORSAL_NAME, VENTRAL_NAME, EYE_NAME]:
        if matches[material_name].is_empty():
            last_error = "required_final_material_missing:" + material_name
            return false
        for entry in matches[material_name]:
            if not _validate_input_surface(material_name, entry):
                return false

    var binding_script_path: String = get_script().resource_path.get_base_dir().path_join("camouflage_binding.gd")
    var shader_path: String = get_script().resource_path.get_base_dir().path_join("camouflage_spatial.gdshader")
    var binding_script := load(binding_script_path)
    var shader := load(shader_path)
    if not (binding_script is Script) or not (shader is Shader):
        last_error = "f12_binding_or_shader_load_failed"
        return false
    binding = binding_script.new()
    binding.name = "F12CamouflageBinding"
    add_child(binding)

    var overrides := {}
    for material_name in [DORSAL_NAME, VENTRAL_NAME]:
        var adaptive_material := ShaderMaterial.new()
        adaptive_material.resource_name = material_name + "_F12_ADAPTIVE"
        adaptive_material.shader = shader
        var slot_id: StringName = SLOT_BY_MATERIAL_NAME[material_name]
        if not bool(binding.call("bind_surface_material", slot_id, adaptive_material)):
            last_error = "f12_bind_surface_failed:" + material_name + ":" + str(binding.get("last_error"))
            _rollback_binding()
            return false
        overrides[material_name] = adaptive_material

    # Apply only instance-local overrides after every exact input surface has
    # validated. This keeps the imported A10 mesh/material bytes immutable.
    for material_name in [DORSAL_NAME, VENTRAL_NAME]:
        var adaptive_material: ShaderMaterial = overrides[material_name]
        for entry in matches[material_name]:
            var mesh_instance: MeshInstance3D = entry[0]
            var surface_index: int = entry[1]
            mesh_instance.set_surface_override_material(surface_index, adaptive_material)

    # EYE is identity-only: no F12 override is permitted.
    for entry in matches[EYE_NAME]:
        var eye_mesh: MeshInstance3D = entry[0]
        var eye_surface_index: int = entry[1]
        if eye_mesh.get_surface_override_material(eye_surface_index) != null:
            last_error = "eye_surface_override_present_after_binding"
            _clear_adaptive_overrides(matches)
            _rollback_binding()
            return false

    matched_surface_counts = {
        DORSAL_NAME: matches[DORSAL_NAME].size(),
        VENTRAL_NAME: matches[VENTRAL_NAME].size(),
        EYE_NAME: matches[EYE_NAME].size(),
    }
    bound_creature = creature_root
    last_error = ""
    return true

func get_binding() -> Node:
    return binding

func region_witnesses() -> Dictionary:
    if binding == null:
        return {}
    return binding.call("region_witnesses")

func adapter_witness() -> Dictionary:
    return {
        "bound": bound_creature != null and binding != null,
        "matchedSurfaceCounts": matched_surface_counts.duplicate(true),
        "regions": region_witnesses(),
        "eyeAdaptiveOverride": false,
        "lastError": last_error,
    }

func _collect_material_surfaces(node: Node, matches: Dictionary) -> void:
    if node is MeshInstance3D:
        var mesh_instance := node as MeshInstance3D
        if mesh_instance.mesh != null:
            for surface_index in range(mesh_instance.mesh.get_surface_count()):
                var material := mesh_instance.mesh.surface_get_material(surface_index)
                if material != null and matches.has(String(material.resource_name)):
                    matches[String(material.resource_name)].append([mesh_instance, surface_index, material])
    for child in node.get_children():
        _collect_material_surfaces(child, matches)

func _validate_input_surface(material_name: String, entry: Array) -> bool:
    var mesh_instance: MeshInstance3D = entry[0]
    var surface_index: int = entry[1]
    var material: Material = entry[2]
    if mesh_instance.get_surface_override_material(surface_index) != null:
        last_error = "preexisting_surface_override:" + material_name
        return false
    if not (material is StandardMaterial3D):
        last_error = "final_material_not_standard_material3d:" + material_name
        return false
    var standard := material as StandardMaterial3D
    var expected: Dictionary = EXPECTED[material_name]
    if standard.albedo_color.to_html(false).to_lower() != String(expected["base"]):
        last_error = "final_material_base_albedo_drift:" + material_name
        return false
    if absf(standard.roughness - float(expected["roughness"])) > 0.0001:
        last_error = "final_material_roughness_drift:" + material_name
        return false
    if absf(standard.metallic) > 0.0001:
        last_error = "final_material_metallic_drift:" + material_name
        return false
    if standard.emission_enabled:
        last_error = "final_material_emission_enabled:" + material_name
        return false
    if standard.albedo_color.a < 0.9999:
        last_error = "final_material_not_opaque:" + material_name
        return false
    return true

func _clear_adaptive_overrides(matches: Dictionary) -> void:
    for material_name in [DORSAL_NAME, VENTRAL_NAME]:
        for entry in matches[material_name]:
            var mesh_instance: MeshInstance3D = entry[0]
            mesh_instance.set_surface_override_material(int(entry[1]), null)

func _rollback_binding() -> void:
    if binding != null:
        binding.queue_free()
        binding = null
    bound_creature = null
    matched_surface_counts.clear()
