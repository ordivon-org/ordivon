class_name VeilwildCamouflageBinding
extends Node

# Source-bound producer interface consumed by F12. A13 owns state meaning and the
# numeric camouflage intent. F12 validates/pass-throughs the target; it does not
# remap state names to stronger/weaker concealment values.
const F13_CONTRACT_COMMIT := "60cb5faf0d386ae9815647c1ffddc9bc0c123af3"
const F13_CONTRACT_SHA256 := "bb4d5e27d457bae528454fdc917cbff62a30a445d0c9a4c8e554c6b894fa4824"
const F13_CUE_AUTH_SHA256 := "bd32688e9895dee587949979eb5120f3ff4c734e79178ff876aeb630880a6115"
const F14_CONTRACT_COMMIT := "5c627b598e90319c2f9aa529f182f928a6b312da"
const F14_CONTRACT_SHA256 := "a35e460dde73a838704b759ab544dd33fa217a1410bc972e4c7e0f4f163e3f22"
const F13_STATE_NAMES_BY_ID := {
    &"veilwild.behavior.unaware.r1": &"UNAWARE",
    &"veilwild.behavior.orient.r1": &"ORIENT",
    &"veilwild.behavior.freeze.r1": &"FREEZE",
    &"veilwild.behavior.conceal.r1": &"CONCEAL",
    &"veilwild.behavior.evade.r1": &"EVADE",
    &"veilwild.behavior.recover.r1": &"RECOVER",
}

# Exact source-current F10 region semantics @6bbea58…, which in turn binds the
# repaired Round-2 material contract @b7dd5c5…. These are consumer snapshots of
# F10 owner truth, not F12 authority. Stable slot/semantic identity selects the
# profile; approximate color matching is intentionally forbidden.
const F10_REGION_CONTRACT_COMMIT := "7b210a950a8e1020f9d4de00ceda0c46819dc582"
const F10_REGION_CONTRACT_SHA256 := "7b4be6b87aa792effd4baef48b11a332fed880a741e00dc537dbcc64f41b744d"
const F10_R2_BINDING_COMMIT := "b7dd5c5ca76a5e06ec27e6d15d1ce7ee5995842f"
const F10_R2_BINDING_SHA256 := "e300996ced4f3a27807cd3d076f05eecb5a3a0f0a1e9ebc9e514fbceeceada66"
const F10_ADAPTIVE_SURFACE_PROFILES := {
    &"VR_SURFACE_DORSAL_SLOT": {
        "semantic_id": &"veilwild.material.creature.dorsal.r3",
        "base_albedo": Color(0.3215686275, 0.3803921569, 0.3254901961, 1.0),
        "roughness": 0.78,
    }, # #526153
    &"VR_SURFACE_VENTRAL_SLOT": {
        "semantic_id": &"veilwild.material.creature.ventral.r3",
        "base_albedo": Color(0.4274509804, 0.4705882353, 0.4117647059, 1.0),
        "roughness": 0.68,
    }, # #6D7869
}
const F10_IDENTITY_ONLY_SURFACE_PROFILES := {
    &"VR_SURFACE_EYE_SLOT": {
        "semantic_id": &"veilwild.material.creature.eye.r3",
        "base_albedo": Color(0.1058823529, 0.1647058824, 0.1372549020, 1.0),
        "roughness": 0.90,
    }, # #1B2A23; metallic 0, OPAQUE, no emission by F10 owner contract.
}
const F10_PATTERN_SCALE := 4.5
const F10_PATTERN_STRENGTH := 0.06

# These response constants are fictional/game-authored realization parameters,
# not biological effect sizes. Nonzero values deliberately prevent instantaneous
# appearance adaptation (F03-R5) and make motion exposure temporally bounded (R3).
var camouflage_response_seconds := 0.45
var context_response_seconds := 0.30
var motion_response_seconds := 0.12

var shader_material: ShaderMaterial # Backward-compatible DORSAL alias only.
var surface_materials: Dictionary = {}
var last_behavior_state_id: StringName = &"veilwild.behavior.unaware.r1"
var last_state_name: StringName = &"UNAWARE"
var last_camouflage_mismatch_authorization := "NONE"
var last_authorization_only := false
var target_camouflage_drive := 0.0
var applied_camouflage_drive := 0.0
var target_environment_match := 0.0
var applied_environment_match := 0.0
var target_motion_exposure := 0.0
var applied_motion_exposure := 0.0
var last_concealment_available := false
var last_concealment_affordance_id := ""
var last_navigation_map_iteration := 0
var last_error := ""

func _process(delta: float) -> void:
    advance(delta)

func bind_material(value: ShaderMaterial) -> bool:
    # R1 compatibility helper. New product integration must call
    # bind_surface_material() for every F10-declared adaptive slot.
    return bind_surface_material(&"VR_SURFACE_DORSAL_SLOT", value)

func bind_surface_material(slot_id: StringName, value: ShaderMaterial) -> bool:
    if F10_IDENTITY_ONLY_SURFACE_PROFILES.has(slot_id):
        last_error = "f10_identity_region_must_not_receive_f12_shader"
        return false
    if not F10_ADAPTIVE_SURFACE_PROFILES.has(slot_id):
        last_error = "f10_surface_slot_not_in_bound_adaptive_contract"
        return false
    if value == null or value.shader == null:
        last_error = "material_or_shader_missing"
        return false
    # Godot ShaderMaterial parameters live on the material resource. Distinct F10
    # base profiles therefore require distinct ShaderMaterial objects. Replacing a
    # slot's material also requires explicit unbind so the old resource cannot keep
    # receiving stale dynamic state outside the binding registry.
    if surface_materials.has(slot_id) and surface_materials[slot_id] != value:
        last_error = "f10_surface_slot_rebind_requires_explicit_unbind"
        return false
    for existing_slot in surface_materials.keys():
        if existing_slot != slot_id and surface_materials[existing_slot] == value:
            last_error = "shared_shader_material_across_distinct_f10_profiles"
            return false
    surface_materials[slot_id] = value
    if slot_id == &"VR_SURFACE_DORSAL_SLOT":
        shader_material = value
    var profile: Dictionary = F10_ADAPTIVE_SURFACE_PROFILES[slot_id]
    value.set_shader_parameter("base_albedo", profile["base_albedo"])
    value.set_shader_parameter("surface_roughness", profile["roughness"])
    value.set_shader_parameter("pattern_scale", F10_PATTERN_SCALE)
    value.set_shader_parameter("pattern_strength", F10_PATTERN_STRENGTH)
    _apply_dynamic(value)
    last_error = ""
    return true

func unbind_surface_material(slot_id: StringName) -> void:
    surface_materials.erase(slot_id)
    if slot_id == &"VR_SURFACE_DORSAL_SLOT":
        shader_material = null

func consume_behavior_sample(sample: Dictionary) -> bool:
    # R2 consumes F13's stable semantic ID as primary identity. state_name is
    # retained only as an exact compatibility cross-check, not as the key.
    for key in ["behavior_state_id", "state_name", "camouflage_drive", "player_cue_authorization"]:
        if not sample.has(key):
            last_error = "behavior_sample_missing_required_fields"
            return false
    var state_id := StringName(str(sample["behavior_state_id"]))
    if not F13_STATE_NAMES_BY_ID.has(state_id):
        last_error = "behavior_state_id_not_in_bound_f13_contract"
        return false
    var state_name := StringName(str(sample["state_name"]))
    if state_name != F13_STATE_NAMES_BY_ID[state_id]:
        last_error = "behavior_state_name_id_mismatch"
        return false
    var drive := float(sample["camouflage_drive"])
    if not _normalized(drive):
        last_error = "camouflage_drive_out_of_range"
        return false
    var authorization: Variant = sample["player_cue_authorization"]
    if not authorization is Dictionary:
        last_error = "player_cue_authorization_not_dictionary"
        return false
    var auth: Dictionary = authorization
    for key in ["sustained_classes", "edge_classes", "explicit_none_classes", "authorization_only"]:
        if not auth.has(key):
            last_error = "player_cue_authorization_missing_fields"
            return false
    if not bool(auth["authorization_only"]):
        last_error = "player_cue_authorization_boundary_missing"
        return false
    var sustained: Array = auth["sustained_classes"]
    var edge: Array = auth["edge_classes"]
    var explicit_none: Array = auth["explicit_none_classes"]
    var camo_sustained := "CAMOUFLAGE_MISMATCH" in sustained
    var camo_edge := "CAMOUFLAGE_MISMATCH" in edge
    var camo_none := "CAMOUFLAGE_MISMATCH" in explicit_none
    if not camo_sustained and not camo_edge and not camo_none:
        last_error = "camouflage_mismatch_authorization_not_exhaustive"
        return false
    if camo_none and (camo_sustained or camo_edge):
        last_error = "camouflage_mismatch_authorization_contradiction"
        return false
    if not _has_bound_surface():
        last_error = "shader_material_not_bound"
        return false
    last_behavior_state_id = state_id
    last_state_name = state_name
    last_camouflage_mismatch_authorization = "EDGE_AND_SUSTAINED" if camo_edge and camo_sustained else ("EDGE" if camo_edge else ("SUSTAINED" if camo_sustained else "NONE"))
    last_authorization_only = true
    # Authorization is metadata only. It does NOT gate the material intent; a state
    # may carry nonzero camouflage_drive while CAMOUFLAGE_MISMATCH is F13 NONE.
    # F12 only calls a player cue "CAMOUFLAGE_MISMATCH" when authorization allows
    # it and an actual context/material consequence is later evidenced.
    target_camouflage_drive = drive
    last_error = ""
    return true

# Source-bound F14 consumer surface. F14 owns whether an affordance is legal and
# reachable plus its game-normalized concealment suitability. F12 consumes the
# selected suitability unchanged as environment_match; it does not re-rank
# affordances or reinterpret suitability as Human visibility/detectability.
func consume_affordance_snapshot(snapshot: Dictionary) -> bool:
    if not snapshot.has("concealment_available") or not snapshot.has("concealment_quality") or not snapshot.has("navigation_map_iteration"):
        last_error = "f14_snapshot_missing_required_fields"
        return false
    if not _has_bound_surface():
        last_error = "shader_material_not_bound"
        return false
    var map_iteration := int(snapshot["navigation_map_iteration"])
    if map_iteration <= 0:
        last_error = "f14_navigation_map_unsynchronized"
        return false
    var available := bool(snapshot["concealment_available"])
    var quality := float(snapshot["concealment_quality"])
    if not _normalized(quality):
        last_error = "f14_concealment_quality_out_of_range"
        return false
    var affordance_id := String(snapshot.get("selected_concealment_affordance_id", ""))
    if available and affordance_id.strip_edges().is_empty():
        last_error = "f14_selected_affordance_id_missing"
        return false
    last_concealment_available = available
    last_concealment_affordance_id = affordance_id if available else ""
    last_navigation_map_iteration = map_iteration
    target_environment_match = quality if available else 0.0
    last_error = ""
    return true

# Lower-level owner-supplied bounded target retained for integration adapters that
# have already source-bound F14 semantics. It must not be fed Human/perceptual truth.
func set_environment_match(value: float) -> bool:
    if not _normalized(value):
        last_error = "environment_match_out_of_range"
        return false
    if not _has_bound_surface():
        last_error = "shader_material_not_bound"
        return false
    target_environment_match = value
    last_error = ""
    return true

# Motion owner/runtime adapter supplies the normalized target exposure signal.
# F12 smooths only its rendering consequence; it does not reinterpret motion.
func set_motion_exposure(value: float) -> bool:
    if not _normalized(value):
        last_error = "motion_exposure_out_of_range"
        return false
    if not _has_bound_surface():
        last_error = "shader_material_not_bound"
        return false
    target_motion_exposure = value
    last_error = ""
    return true

func set_environment_reference(value: Color) -> bool:
    if not _has_bound_surface():
        last_error = "shader_material_not_bound"
        return false
    for material in surface_materials.values():
        material.set_shader_parameter("environment_reference", value)
    last_error = ""
    return true

# Deterministic stepping surface used both by _process and owner tests. Response
# is finite for any positive target delta because each configured time is > 0.
func advance(delta: float) -> void:
    if not _has_bound_surface() or not is_finite(delta) or delta <= 0.0:
        return
    applied_camouflage_drive = _approach(applied_camouflage_drive, target_camouflage_drive, delta, camouflage_response_seconds)
    applied_environment_match = _approach(applied_environment_match, target_environment_match, delta, context_response_seconds)
    applied_motion_exposure = _approach(applied_motion_exposure, target_motion_exposure, delta, motion_response_seconds)
    _apply_all()

func snapshot() -> Dictionary:
    return {
        "f13_contract_commit": F13_CONTRACT_COMMIT,
        "f13_contract_sha256": F13_CONTRACT_SHA256,
        "f13_cue_authorization_sha256": F13_CUE_AUTH_SHA256,
        "behavior_state_id": String(last_behavior_state_id),
        "camouflage_mismatch_authorization": last_camouflage_mismatch_authorization,
        "authorization_only": last_authorization_only,
        "f14_contract_commit": F14_CONTRACT_COMMIT,
        "f14_contract_sha256": F14_CONTRACT_SHA256,
        "f10_region_contract_commit": F10_REGION_CONTRACT_COMMIT,
        "f10_region_contract_sha256": F10_REGION_CONTRACT_SHA256,
        "f10_r2_binding_commit": F10_R2_BINDING_COMMIT,
        "f10_r2_binding_sha256": F10_R2_BINDING_SHA256,
        "state_name": String(last_state_name),
        "target_camouflage_drive": target_camouflage_drive,
        "applied_camouflage_drive": applied_camouflage_drive,
        "target_environment_match": target_environment_match,
        "concealment_available": last_concealment_available,
        "selected_concealment_affordance_id": last_concealment_affordance_id,
        "navigation_map_iteration": last_navigation_map_iteration,
        "applied_environment_match": applied_environment_match,
        "target_motion_exposure": target_motion_exposure,
        "applied_motion_exposure": applied_motion_exposure,
        "camouflage_response_seconds": camouflage_response_seconds,
        "context_response_seconds": context_response_seconds,
        "motion_response_seconds": motion_response_seconds,
        "bound_adaptive_surface_slots": _bound_surface_slot_names(),
        "bound_adaptive_surface_semantics": _bound_surface_semantics(),
        "region_witnesses": region_witnesses(),
        "candidate_surface_binding_ready": candidate_surface_binding_ready(),
        "last_error": last_error,
    }

# Narrow read-only evidence surface for candidate-frame consumers such as A04.
# It reports only current bound material state and owner semantic identity; it does
# not mutate materials, reinterpret camouflage as Human detectability, or expose
# hidden world/target coordinates.
func region_witness(slot_id: StringName) -> Dictionary:
    if not surface_materials.has(slot_id) or not F10_ADAPTIVE_SURFACE_PROFILES.has(slot_id):
        return {}
    var material: ShaderMaterial = surface_materials[slot_id]
    var profile: Dictionary = F10_ADAPTIVE_SURFACE_PROFILES[slot_id]
    return {
        "semanticId": String(profile["semantic_id"]),
        "base_albedo": material.get_shader_parameter("base_albedo"),
        "roughness": material.get_shader_parameter("surface_roughness"),
        "camouflage_drive": material.get_shader_parameter("camouflage_drive"),
        "environment_match": material.get_shader_parameter("environment_match"),
        "motion_exposure": material.get_shader_parameter("motion_exposure"),
        "environment_reference": material.get_shader_parameter("environment_reference"),
    }

func region_witnesses() -> Dictionary:
    var result := {}
    for slot_name in _bound_surface_slot_names():
        var slot_id := StringName(slot_name)
        result[slot_name] = region_witness(slot_id)
    return result

func _apply_all() -> void:
    for material in surface_materials.values():
        _apply_dynamic(material)

func _apply_dynamic(material: ShaderMaterial) -> void:
    material.set_shader_parameter("camouflage_drive", applied_camouflage_drive)
    material.set_shader_parameter("environment_match", applied_environment_match)
    material.set_shader_parameter("motion_exposure", applied_motion_exposure)

func _has_bound_surface() -> bool:
    return not surface_materials.is_empty()

func _bound_surface_slot_names() -> Array[String]:
    var names: Array[String] = []
    for slot_id in surface_materials.keys():
        names.append(String(slot_id))
    names.sort()
    return names

func _bound_surface_semantics() -> Dictionary:
    var result := {}
    for slot_id in surface_materials.keys():
        var profile: Dictionary = F10_ADAPTIVE_SURFACE_PROFILES[slot_id]
        result[String(slot_id)] = String(profile["semantic_id"])
    return result

func candidate_surface_binding_ready() -> bool:
    return surface_materials.has(&"VR_SURFACE_DORSAL_SLOT") and surface_materials.has(&"VR_SURFACE_VENTRAL_SLOT")

func _approach(current: float, target: float, delta: float, response_seconds: float) -> float:
    if response_seconds <= 0.0:
        # Fail closed to a tiny finite response rather than reintroducing an
        # instantaneous appearance jump through a bad tuning value.
        response_seconds = 0.001
    return move_toward(current, target, delta / response_seconds)

func _normalized(value: float) -> bool:
    return is_finite(value) and value >= 0.0 and value <= 1.0
