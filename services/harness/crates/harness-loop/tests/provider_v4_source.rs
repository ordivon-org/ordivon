//! Differential verification of v4 Python ProviderRecord code against B's
//! read-only Rust inspection, with A's sealed JSON codec as sole decoder.
use ordivon_harness_core::{digest_bytes, loads_strict};
use ordivon_harness_loop::provider_head::{
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

/// P0 H01: independent source-shape expectation BEFORE promoting a reusable
/// native Provider Event author. The old source Journal used Python-fixture
/// EventWrite templates even though its ProviderRecord CAS was native Rust.
#[test]
fn native_provider_event_author_matches_python_source_shape() {
    use ordivon_harness_core::{canonical_bytes, CanonicalDocument};
    use ordivon_harness_loop::provider_v4_author::{
        author_provider_event_v4, author_provider_v4, ProviderV4EventKind, ProviderV4EventRefs,
        ProviderV4Seed, ProviderV4Transition,
    };
    use ordivon_harness_pg::journal_write::StoredRef;

    let binding = digest_bytes(b"bound-model-binding");
    let source = digest_bytes(b"real-source-cas");
    let state_digest = digest_bytes(b"current-state-cas");
    let request = digest_bytes(b"original-turn-request");
    let provider_request = digest_bytes(b"exact-provider-http-wire");
    let seed = ProviderV4Seed {
        provider_call_id: "provider-call:consumer-r40",
        harness_run_id: "harness-run:consumer-r40",
        binding_digest: &binding,
        source_kind: "assignment",
        source_digest: &source,
        source_object_digest: &source,
        state_object_digest: &state_digest,
        turn_id: "turn:r40",
        turn_sequence: 1,
        request_digest: &request,
        request_object_digest: None,
        provider_request_digest: &provider_request,
        adapter_id: "adapter:source",
        requested_model_id: "model:source",
        holder_id: "holder:r40",
        claim_generation: 1,
        issued_at_ms: 99,
        expires_at_ms: 999,
    };
    let record =
        author_provider_v4(&seed, ProviderV4Transition::Claimed { previous: None }, 101).unwrap();
    let state = StoredRef {
        digest: state_digest.clone(),
        kind: "harness-run-state".into(),
        byte_length: 55,
    };
    let event = author_provider_event_v4(
        "event:provider-r40-claimed",
        ProviderV4EventKind::Claimed,
        &record,
        ProviderV4EventRefs {
            state: &state,
            request: None,
            result: None,
            failure: None,
        },
        None,
        101,
    )
    .unwrap();
    assert_eq!(event.event_kind, "harness.provider-call-claimed");
    assert_eq!(event.caused_by_event_id, None);
    let record_digest = digest_bytes(&canonical_bytes(&record));
    assert_eq!(
        canonical_bytes(&event.data),
        canonical_bytes(
            &CanonicalDocument::object(vec![
                (
                    "providerCallRecordDigest".into(),
                    CanonicalDocument::string(&record_digest)
                ),
                (
                    "providerCallRecordObjectDigest".into(),
                    CanonicalDocument::string(&record_digest)
                ),
                (
                    "stateObjectDigest".into(),
                    CanonicalDocument::string(&state_digest)
                ),
                ("requestObjectDigest".into(), CanonicalDocument::null()),
                ("resultObjectDigest".into(), CanonicalDocument::null()),
                ("failureObjectDigest".into(), CanonicalDocument::null()),
            ])
            .unwrap()
        ),
    );
    assert_eq!(event.referenced_objects.len(), 2);
    assert_eq!(event.referenced_objects[0].digest, record_digest);
    assert_eq!(
        event.referenced_objects[0].kind,
        "harness-provider-call-record"
    );
    assert_eq!(event.referenced_objects[1], state);
    assert!(author_provider_event_v4(
        "event:provider-r40-mismatched",
        ProviderV4EventKind::Dispatching,
        &record,
        ProviderV4EventRefs {
            state: &event.referenced_objects[1],
            request: None,
            result: None,
            failure: None,
        },
        None,
        101,
    )
    .is_err());
}
