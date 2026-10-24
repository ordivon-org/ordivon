use serde_json::Value;
use std::process::{Command, Output};

fn run_cli(args: &[&str]) -> Output {
    // Cargo builds this exact binary alongside the native integration test.
    // Canonicalize a Runtime /proc/self/fd Cargo target alias before spawning
    // a subprocess, without changing the Game owner or adding another CLI.
    let executable = std::fs::canonicalize(env!("CARGO_BIN_EXE_room-action"))
        .expect("Cargo-built room-action executable must be addressable");
    Command::new(executable)
        .args(args)
        .output()
        .expect("the exact current Game binary must start")
}

#[test]
fn executable_json_palette_and_seeded_recipe_are_deterministic() {
    let palette = run_cli(&["--palette-json"]);
    assert!(palette.status.success(), "{:?}", palette);
    let decoded: Value = serde_json::from_slice(&palette.stdout).unwrap();
    for key in ["rooms", "weapons", "enemies"] {
        assert!(decoded[key].is_array(), "{key} is missing from palette");
        assert!(!decoded[key].as_array().unwrap().is_empty());
    }

    let args = ["--seed", "42", "--rooms", "4", "--json"];
    let first = run_cli(&args);
    let second = run_cli(&args);
    assert!(first.status.success(), "{:?}", first);
    assert_eq!(
        first.stdout, second.stdout,
        "same locked recipe must replay"
    );
    let recipe: Value = serde_json::from_slice(&first.stdout).unwrap();
    assert_eq!(recipe["rooms"].as_array().unwrap().len(), 4);
}

#[test]
fn invalid_cli_input_fails_closed_before_engine_start() {
    let outcome = run_cli(&["--rooms", "0", "--json"]);
    assert_eq!(outcome.status.code(), Some(2), "{:?}", outcome);
    let error = String::from_utf8_lossy(&outcome.stderr);
    assert!(error.contains("require --seed"), "{error}");
    assert!(outcome.stdout.is_empty());
}
