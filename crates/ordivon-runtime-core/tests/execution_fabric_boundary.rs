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
