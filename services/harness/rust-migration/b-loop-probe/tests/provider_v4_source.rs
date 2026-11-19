//! Differential verification of v4 Python ProviderRecord code against B's
//! read-only Rust inspection, with A's sealed JSON codec as sole decoder.
use ordivon_harness_core::{digest_bytes, loads_strict};
use ordivon_harness_loop_b_probe::provider_head::{
    inspect_v4, ProviderRecordError, ProviderStatus, RecoveryPosture,
};
use std::path::Path;
use std::process::Command;

fn unhex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&input[i..i + 2], 16).unwrap())
        .collect()
}

#[test]
fn python_provider_v4_source_parity() {
    let harness = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let oracle = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/provider_v4_oracle.py");
    let output = Command::new("uv")
        .args(["run", "--offline", "--locked", "python"])
        .arg(oracle)
        .current_dir(&harness)
        .output()
        .expect("locked Harness Python environment required for real source oracle");
    assert!(
        output.status.success(),
        "Python oracle: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let text = String::from_utf8(output.stdout).expect("source oracle must produce UTF-8");
    let mut cases = 0;
    let mut accepted = 0;
    for line in text.lines() {
        let fields: Vec<&str> = line.split('\t').collect();
        let ["V", valid, bytes_hex, digest, status, sequence, generation] = fields.as_slice()
        else {
            panic!("invalid Python line {line}");
        };
        let raw = unhex(bytes_hex);
        let source = std::str::from_utf8(&raw).expect("Python canonical bytes UTF-8");
        let value = loads_strict(source).expect("bounded Python canonical source valid");
        let inspected = inspect_v4(&value);
        if *valid == "1" {
            let got = inspected.unwrap_or_else(|err| {
                panic!("Rust incorrectly rejected Python valid record: {err:?}, {source}")
            });
            assert_eq!(got.canonical_digest, *digest);
            assert_eq!(got.canonical_digest, digest_bytes(&raw));
            assert_eq!(got.status.as_str(), *status);
            assert_eq!(got.turn_sequence.as_str(), *sequence);
            assert_eq!(got.claim_generation.as_str(), *generation);
            match got.status {
                ProviderStatus::Dispatching | ProviderStatus::Unknown => assert!(matches!(
                    got.status.recovery_posture(),
                    RecoveryPosture::ReconcileWithProviderOwner
                        | RecoveryPosture::RetainUnknownAndReconcile
                )),
                _ => {}
            }
            accepted += 1;
        } else {
            assert!(
                matches!(inspected, Err(ProviderRecordError::InvalidV4Record)),
                "Rust admitted Python-invalid ProviderRecordV4: {source}"
            );
        }
        cases += 1;
    }
    assert_eq!(accepted, 54);
    assert_eq!(cases, 525);
}
