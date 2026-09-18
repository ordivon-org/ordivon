use std::fs;
use std::path::PathBuf;

#[test]
fn engine_dispatch_crosses_physical_provider_facade_not_raw_os_spawners() {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let execution = fs::read_to_string(manifest.join("src/runtime/engine/execution.rs"))
        .expect("read engine execution source");

    for forbidden in [
        "systemd_run(",
        "windows_systemd_run(",
        "spawn_windows_native(",
    ] {
        assert!(
            !execution.contains(forbidden),
            "engine/execution.rs still crosses raw physical dispatch function {forbidden}"
        );
    }
}

#[test]
fn engine_tree_observes_process_owners_through_physical_provider_facade() {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let engine_root = manifest.join("src/runtime/engine");
    let mut sources = vec![fs::read_to_string(manifest.join("src/runtime/engine.rs"))
        .expect("read engine root source")];
    for entry in fs::read_dir(engine_root).expect("read engine module directory") {
        let entry = entry.expect("read engine module entry");
        if entry.path().extension().and_then(|value| value.to_str()) == Some("rs") {
            sources.push(fs::read_to_string(entry.path()).expect("read engine module source"));
        }
    }
    let combined = sources.join("\n");
    for forbidden in [
        "observe_windows_launcher_owner(",
        "supervisor_identity(attempt)",
        "release_terminal_unit(&attempt.unit_name)",
    ] {
        assert!(
            !combined.contains(forbidden),
            "Engine still crosses raw process-provider lifecycle helper {forbidden}"
        );
    }
}
