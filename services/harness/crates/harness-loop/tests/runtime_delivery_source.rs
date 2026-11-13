//! Production Python Runtime Owner observation differential source oracle.
//! No Runtime submission or physical dispatch in this test.
use ordivon_harness_core::loads_strict;
use ordivon_harness_loop::runtime_delivery::{interpret_runtime_delivery, RuntimeDeliveryError};
use std::{path::Path, process::Command};
fn unhex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&input[i..i + 2], 16).unwrap())
        .collect()
}
#[test]
fn python_source_runtime_owner_delivery_classification() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let oracle =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/runtime_delivery_source_oracle.py");
    let output = Command::new("uv")
        .args(["run", "--offline", "--locked", "python"])
        .arg(oracle)
        .current_dir(&harness)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Python oracle failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let source = String::from_utf8(output.stdout).unwrap();
    let mut count = 0usize;
    let mut valid = 0usize;
    let mut unknown = 0usize;
    for line in source.lines() {
        let fields: Vec<_> = line.split('\t').collect();
        let ["R", expected, raw_hex] = fields.as_slice() else {
            panic!("invalid source oracle line")
        };
        let bytes = unhex(raw_hex);
        let doc = loads_strict(std::str::from_utf8(&bytes).unwrap()).unwrap();
        let got = interpret_runtime_delivery(&doc);
        if *expected == "invalid" {
            assert_eq!(
                got,
                Err(RuntimeDeliveryError::InvalidOwnerObservation),
                "Rust accepted Python-invalid owner state: {}",
                String::from_utf8_lossy(&bytes)
            );
        } else {
            let decision = got.unwrap_or_else(|err| {
                panic!(
                    "Rust rejected valid owner state {expected}: {err:?}, {}",
                    String::from_utf8_lossy(&bytes)
                )
            });
            assert_eq!(decision.as_source_str(), *expected);
            valid += 1;
            if *expected == "unknown" {
                unknown += 1;
            }
        }
        count += 1;
    }
    assert!(count >= 1200, "insufficient source cases: {count}");
    assert!(valid >= 60, "source-valid Owner states untested: {valid}");
    assert!(unknown > 0, "unknown lost delivery not covered");
    println!("PYTHON_RUNTIME_OWNER_DELIVERY_SOURCE_PARITY={count} valid={valid} unknown={unknown}");
}
