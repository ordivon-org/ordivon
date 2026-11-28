//! Differential verification of v4 Python ProviderRecord code against B's
//! read-only Rust inspection, with A's sealed JSON codec as sole decoder.
use ordivon_harness_core::{canonical_bytes, digest_bytes, loads_strict, CanonicalDocument};
use ordivon_harness_loop_b_probe::provider_head::{
    build_event_v4, build_v4, inspect_v4, ProviderRecordError, ProviderStatus, RecoveryPosture,
};
use ordivon_harness_pg::journal_write::StoredRef;
use std::collections::BTreeSet;
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
    let mut built = 0;
    let mut events = 0;
    let mut kinds = BTreeSet::new();
    for line in text.lines() {
        let fields: Vec<&str> = line.split('\t').collect();
        if let ["E", bytes_hex] = fields.as_slice() {
            let raw = unhex(bytes_hex);
            let expected = loads_strict(std::str::from_utf8(&raw).unwrap()).unwrap();
            let record = expected.get("record").unwrap();
            let refs = expected.field("references").unwrap();
            let objects: Vec<_> = (0..refs.array_len().unwrap())
                .map(|i| {
                    let item = refs.index(i).unwrap();
                    StoredRef {
                        digest: item.field("digest").unwrap().as_str().unwrap().to_owned(),
                        kind: item.field("kind").unwrap().as_str().unwrap().to_owned(),
                        byte_length: item
                            .field("byteLength")
                            .unwrap()
                            .integer_text()
                            .unwrap()
                            .parse()
                            .unwrap(),
                    }
                })
                .collect();
            let cause = expected.field("cause").unwrap().as_str().map(str::to_owned);
            let event = build_event_v4(&record, &objects[1..], cause.clone()).unwrap();
            assert_eq!(
                event.event_id,
                expected.field("eventId").unwrap().as_str().unwrap()
            );
            assert_eq!(
                event.event_kind,
                expected.field("eventKind").unwrap().as_str().unwrap()
            );
            assert_eq!(
                event.recorded_at_ms.to_string(),
                expected
                    .field("recordedAtMs")
                    .unwrap()
                    .integer_text()
                    .unwrap()
            );
            assert_eq!(event.caused_by_event_id, cause);
            assert_eq!(
                canonical_bytes(&event.data),
                expected.field("data").unwrap().canonical_bytes()
            );
            assert_eq!(event.referenced_objects, objects);
            kinds.insert(event.event_kind);
            events += 1;
            continue;
        }
        if let ["B", bytes_hex] = fields.as_slice() {
            let raw = unhex(bytes_hex);
            let expected = loads_strict(std::str::from_utf8(&raw).unwrap()).unwrap();
            let inputs = || {
                expected
                    .object_entries()
                    .unwrap()
                    .filter(|(key, _)| !matches!(*key, "kind" | "schemaVersion" | "recordId"))
                    .map(|(key, _)| (key.to_owned(), expected.get(key).unwrap()))
                    .collect::<Vec<_>>()
            };
            let actual = build_v4(inputs()).expect("native construction");
            assert_eq!(canonical_bytes(&actual), raw);
            let mut reordered = inputs();
            reordered.reverse();
            assert_eq!(build_v4(reordered).unwrap(), actual);
            let mut missing = inputs();
            missing.pop();
            assert_eq!(build_v4(missing), Err(ProviderRecordError::InvalidV4Record));
            let mut duplicate = inputs();
            duplicate[0] = duplicate[1].clone();
            assert_eq!(
                build_v4(duplicate),
                Err(ProviderRecordError::InvalidV4Record)
            );
            let mut forged = inputs();
            forged[0] = ("recordId".into(), CanonicalDocument::string("forged"));
            assert_eq!(build_v4(forged), Err(ProviderRecordError::InvalidV4Record));
            let mut invalid = inputs();
            invalid
                .iter_mut()
                .find(|(k, _)| k == "turnSequence")
                .unwrap()
                .1 = CanonicalDocument::boolean(true);
            assert_eq!(build_v4(invalid), Err(ProviderRecordError::InvalidV4Record));
            built += 1;
            continue;
        }
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
    assert_eq!(built, 8);
    assert_eq!(events, 9);
    assert_eq!(kinds.len(), 6);
    assert_eq!(accepted, 54);
    assert_eq!(cases, 525);
}
