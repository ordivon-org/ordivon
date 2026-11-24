//! True Python 3.15 source differential of versioned Run Contract semantics.
//! Does not connect to PostgreSQL, Runtime or any production Provider.
use std::path::Path;
use std::process::Command;

use ordivon_harness_core::loads_strict;
use ordivon_harness_pg::contract_semantics::validate_contract;

#[test]
fn python_315_exact_contract_consumer_parity() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("Harness root");
    let script = harness.join("crates/harness-pg/tests/contract_source_oracle.py");
    let output = Command::new("uv")
        .args(["run", "--offline", "--locked", "--project"])
        .arg(&harness)
        .arg("python")
        .arg(&script)
        .output()
        .expect("launch real Python contract oracle");
    assert!(
        output.status.success(),
        "Python oracle failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let mut cases = 0;
    let mut accepted = 0;
    let mut rejected = 0;
    for line in String::from_utf8(output.stdout)
        .expect("Python UTF-8")
        .lines()
    {
        let item: serde_json::Value = serde_json::from_str(line).expect("oracle line JSON");
        let name = item["case"].as_str().expect("case name");
        let raw = item["canonical"].as_str().expect("canonical JSON");
        let expected = item["accepted"].as_bool().expect("source acceptance");
        let decoded = loads_strict(raw).unwrap_or_else(|err| {
            panic!("Rust sealed parser disagrees with source canonical {name}: {err}")
        });
        let actual = validate_contract(&decoded);
        assert_eq!(
            actual.is_ok(),
            expected,
            "Contract source-parity mismatch on {name}: {actual:?}"
        );
        cases += 1;
        if expected {
            accepted += 1;
        } else {
            rejected += 1;
        }
    }
    assert!(cases >= 190, "insufficient source vectors: {cases}");
    assert!(
        accepted >= 10 && rejected >= 150,
        "{accepted} accepted, {rejected} rejected"
    );
    println!("PYTHON_HARNESS_RUN_CONTRACT_SOURCE_PARITY cases={cases} accepted={accepted} rejected={rejected}");
}
