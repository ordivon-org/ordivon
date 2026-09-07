shader_type spatial;
render_mode depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

// F12 owns this representation only. Upstream fronts own the meaning/source of
// creature state, environment reference, concealment suitability and motion.
// base_albedo is source-bound to A10 VW_CREATURE_BASE sRGB #526153.
uniform vec4 base_albedo : source_color = vec4(0.3215686275, 0.3803921569, 0.3254901961, 1.0);
uniform vec4 environment_reference : source_color = vec4(0.30, 0.39, 0.22, 1.0);
uniform float camouflage_drive : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform float environment_match : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform float motion_exposure : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform float protected_counter_cue : hint_range(0.08, 0.50, 0.01) = 0.14;
uniform float pattern_scale : hint_range(0.5, 20.0, 0.1) = 4.5;
uniform float pattern_strength : hint_range(0.0, 0.25, 0.01) = 0.06;
uniform float surface_roughness : hint_range(0.0, 1.0, 0.01) = 0.78;

float veil_pattern(vec2 uv) {
    float a = sin((uv.x * pattern_scale + uv.y * (pattern_scale * 0.63)) * 6.2831853);
    float b = sin((uv.y * (pattern_scale * 1.27) - uv.x * (pattern_scale * 0.41)) * 6.2831853);
    return clamp((a + b) * 0.25 + 0.5, 0.0, 1.0);
}

void fragment() {
    float drive = clamp(camouflage_drive, 0.0, 1.0);
    float context = clamp(environment_match, 0.0, 1.0);
    float moving = clamp(motion_exposure, 0.0, 1.0);
    float cue_floor = clamp(protected_counter_cue, 0.08, 0.50);

    // Camouflage cannot become full replacement: cue_floor bounds residual
    // source-surface contribution. Motion weakens concealment mechanically.
    float effective = drive * context * (1.0 - 0.65 * moving);
    effective = min(clamp(effective, 0.0, 1.0), 1.0 - cue_floor);

    float pattern = mix(1.0 - pattern_strength, 1.0 + pattern_strength, veil_pattern(UV));
    vec3 environmental_surface = clamp(environment_reference.rgb * pattern, vec3(0.0), vec3(1.0));
    vec3 camouflaged = mix(base_albedo.rgb, environmental_surface, effective);

    // Preserve a bounded view-dependent counter-signal without transparency.
    float facing = clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0);
    float grazing = pow(1.0 - facing, 2.0);
    vec3 final_albedo = mix(camouflaged, base_albedo.rgb, grazing * cue_floor);

    ALBEDO = final_albedo;
    ROUGHNESS = clamp(surface_roughness, 0.0, 1.0);
    METALLIC = 0.0;
}
