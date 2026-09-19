use std::fs;
use std::path::PathBuf;

fn runtime_source(manifest: &PathBuf) -> String {
    let root = manifest.join("src/runtime");
    let mut sources = Vec::new();
    for entry in fs::read_dir(&root).expect("read runtime module directory") {
        let entry = entry.expect("read runtime module entry");
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) == Some("rs") {
            sources.push(fs::read_to_string(path).expect("read runtime source"));
        }
    }
    let engine_root = root.join("engine");
    for entry in fs::read_dir(engine_root).expect("read engine module directory") {
        let entry = entry.expect("read engine module entry");
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) == Some("rs") {
            sources.push(fs::read_to_string(path).expect("read engine source"));
        }
    }
    sources.join("\n")
}

#[test]
fn retired_physical_provider_facade_stays_absent() {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    assert!(
        !manifest.join("src/runtime/physical_provider.rs").exists(),
        "retired physical_provider facade reappeared"
    );
    let combined = runtime_source(&manifest);
    assert!(
        !combined.contains("mod physical_provider;"),
        "retired physical_provider module was reintroduced"
    );
    assert!(
        !combined.contains("physical_provider::"),
        "runtime code again depends on the retired physical_provider facade"
    );
}

#[test]
fn runtime_uses_natural_platform_owners_directly() {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let combined = runtime_source(&manifest);
    for required in [
        "systemd_run(",
        "spawn_windows_native(",
        "observe_windows_launcher_owner(",
        "release_terminal_unit(",
    ] {
        assert!(
            combined.contains(required),
            "expected direct platform-owner integration {required} is missing"
        );
    }
}
