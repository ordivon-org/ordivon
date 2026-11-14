//! True Python Store→PG18→A verified CAS/Journal→B Provider recovery head.
//! All Provider events are synthetic test-only identities, with zero external
//! model requests. A readonly DB role is enforced by the shared PG runner.
use std::{fs, io::Read, net::TcpListener, path::Path, thread, time::Duration};

use ordivon_harness_core::{loads_strict, CanonicalDocument, CanonicalRef};
use ordivon_harness_loop::native_loop::{Provider, ProviderResult};
use ordivon_harness_loop::native_provider_http::HttpModelProvider;
use ordivon_harness_loop::pg_domain_read::{
    inspect_pg_no_tool_run, inspect_pg_provider_head, ExpectedModel, PgDomainInspectionError,
    PgProviderRecoveryError,
};
use ordivon_harness_loop::provider_head::{ProviderStatus, RecoveryPosture};
use ordivon_harness_pg::{
    journal_write::{
        append_events, observe_exact_batch, Admission, EventWrite, JournalObservation, StoredRef,
        WriteError,
    },
    lease::acquire_run_lease,
    read_run_readonly, ReadError,
};
use postgres::{Client, NoTls};

fn text<'a>(v: &'a CanonicalDocument, key: &str) -> &'a str {
    v.field(key).and_then(CanonicalRef::as_str).unwrap()
}

#[test]
#[ignore = "requires existing A-owned disposable PostgreSQL18 Store test fixture"]
fn source_python_provider_v4_cas_head_recovery_does_not_dispatch_or_blind_retry() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    let path = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let raw = fs::read_to_string(Path::new(&path)).unwrap();
    let all = loads_strict(&raw).unwrap();
    let no_tool = all.get("no_tool").unwrap();
    let provider_records = all.get("provider_records").unwrap();
    let expected = ExpectedModel {
        provider_id: text(&no_tool, "providerId"),
        adapter_id: text(&no_tool, "adapterId"),
        requested_model_id: text(&no_tool, "requestedModelId"),
    };
    let mut client = Client::connect(&dsn, NoTls).unwrap();

    for (label, status, posture) in [
        (
            "claimed",
            ProviderStatus::Claimed,
            RecoveryPosture::RecheckClaimAndDurableFence,
        ),
        (
            "claimed_next_turn",
            ProviderStatus::Claimed,
            RecoveryPosture::RecheckClaimAndDurableFence,
        ),
        (
            "claimed_superseded",
            ProviderStatus::Claimed,
            RecoveryPosture::RecheckClaimAndDurableFence,
        ),
        (
            "unknown",
            ProviderStatus::Unknown,
            RecoveryPosture::RetainUnknownAndReconcile,
        ),
        (
            "completed_redacted",
            ProviderStatus::Completed,
            RecoveryPosture::ReadCommittedResult,
        ),
        (
            "failed",
            ProviderStatus::Failed,
            RecoveryPosture::CheckFailureReceiptAndRetryBudget,
        ),
    ] {
        let item = provider_records.get(label).unwrap();
        let observed =
            inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected)
                .unwrap_or_else(|error| {
                    panic!("{label} provider head could not be recovered: {error:?}")
                })
                .unwrap();
        assert_eq!(observed.run_id(), text(&item, "runId"));
        assert_eq!(observed.status(), status);
        assert_eq!(observed.recovery_posture(), posture);
        assert_eq!(
            observed.record_digest(),
            text(&item, "expectedRecordDigest")
        );
        assert!(observed.run_revision() >= 2);
        if label == "completed_redacted" {
            // The real Python V4 record permits privacy-redacted content while
            // preserving the semantic result SHA256: never invent a body.
            assert_eq!(
                observed.result_digest(),
                item.field("expectedResultDigest")
                    .and_then(CanonicalRef::as_str)
            );
        } else {
            assert_eq!(observed.result_digest(), None);
        }
    }
    {
        let item = provider_records.get("cleared").unwrap();
        let result =
            inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected).unwrap();
        assert!(
            result.is_none(),
            "Python _heads clears Provider head after Run pause"
        );
    }
    let wrong = provider_records.get("wrong_digest").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&wrong, "runId"), expected),
        Err(PgProviderRecoveryError::EventRecordMismatch(_))
    ));
    for label in [
        "wrong_state",
        "extra_reference",
        "wrong_event_status",
        "wrong_previous_record",
        "wrong_previous_identity",
        "claimed_bad_previous",
        "claimed_missing_previous",
    ] {
        let item = provider_records.get(label).unwrap();
        assert!(
            matches!(
                inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected),
                Err(PgProviderRecoveryError::EventRecordMismatch(_))
            ),
            "PG verified a raw CAS/edge set but B must reject invalid Provider semantics: {label}"
        );
    }
    let legacy = provider_records.get("v3_legacy").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&legacy, "runId"), expected),
        Err(PgProviderRecoveryError::UnsupportedV3ProviderRecord)
    ));
    let kind = provider_records.get("wrong_kind").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&kind, "runId"), expected),
        Err(PgProviderRecoveryError::MissingOrAmbiguousEventReference)
    ));
    let corrupted = provider_records.get("tampered_cas").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(&mut client, &schema, text(&corrupted, "runId"), expected),
        Err(PgProviderRecoveryError::Run(
            PgDomainInspectionError::Store(ReadError::Corruption(_))
        ))
    ));
    let empty_run = text(&no_tool, "runId");
    assert!(
        inspect_pg_provider_head(&mut client, &schema, empty_run, expected)
            .unwrap()
            .is_none()
    );
    let claimed = provider_records.get("claimed").unwrap();
    assert!(matches!(
        inspect_pg_provider_head(
            &mut client,
            &schema,
            text(&claimed, "runId"),
            ExpectedModel {
                adapter_id: "adapter:other",
                ..expected
            }
        ),
        Err(PgProviderRecoveryError::Run(
            PgDomainInspectionError::ProviderSelectionMismatch("adapterId")
        ))
    ));
    for label in [
        "bad_failure_safety",
        "bad_failure_detail",
        "bad_failure_code",
        "bad_failure_schema",
        "bad_failure_kind",
        "bad_failure_extra",
        "bad_failure_overlong",
    ] {
        let item = provider_records
            .get(label)
            .expect("real Python CAS fixture");
        let result = inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected);
        assert!(
            matches!(
                result,
                Err(PgProviderRecoveryError::InvalidProviderFailureReceipt)
            ),
            "source-invalid Provider FailureReceipt accepted/misclassified: {label}: {result:?}"
        );
    }
    for label in [
        "bad_failure_digest",
        "bad_failure_call",
        "bad_failure_request",
        "bad_failure_provider_request",
    ] {
        let item = provider_records
            .get(label)
            .expect("real Python CAS fixture");
        let result = inspect_pg_provider_head(&mut client, &schema, text(&item, "runId"), expected);
        assert!(
            matches!(
                result,
                Err(PgProviderRecoveryError::FailureReceiptBindingMismatch)
            ),
            "CAS-valid but unrelated FailureReceipt accepted/misclassified: {label}: {result:?}"
        );
    }
    println!("PG18_PYTHON_PROVIDER_V4_VERIFIED_CAS_RECOVERY_PASS");
}

/// The cross-Owner proof omitted by separately green Writer and Provider tests:
/// Python authors immutable CAS V4 Records; Rust commits Claim+Dispatch,
/// an actual loopback HTTP Provider send loses its response, Rust then commits
/// UNKNOWN; readonly Rust + the original Python Store independently verify
/// same Run. No external model, billing, or physical Tool is inferred.
#[test]
#[ignore = "real shared disposable PG18 Python CAS source + A Rust Writer + B Provider reader"]
fn native_rust_writer_to_verified_provider_unknown_head_after_connection_loss() {
    let writer_dsn = std::env::var("HARNESS_RUST_TEST_PG_WRITER_DSN").expect("writer test DSN");
    let readonly_dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").expect("reader test DSN");
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").expect("single PG18 schema");
    let fixture = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").expect("Python fixture");
    let all = loads_strict(&fs::read_to_string(fixture).unwrap()).unwrap();
    let native = all
        .get("rust_native_provider")
        .expect("Python V4 source objects");
    let run_id = text(&native, "runId");
    let expected_record = text(&native, "expectedRecordDigest");
    let no_tool = all.get("no_tool").expect("real source no-Tool contract");
    let model = ExpectedModel {
        provider_id: text(&no_tool, "providerId"),
        adapter_id: text(&no_tool, "adapterId"),
        requested_model_id: text(&no_tool, "requestedModelId"),
    };

    let events = native.get("events").unwrap();
    assert_eq!(events.as_borrowed().array_len(), Some(3));
    let mut batch = Vec::new();
    for n in 0..3 {
        let source = events.index(n).unwrap();
        let references = source.field("references").unwrap();
        let mut refs = Vec::new();
        for i in 0..references.array_len().unwrap() {
            let reference = references.index(i).unwrap();
            refs.push(StoredRef {
                digest: reference
                    .field("digest")
                    .and_then(CanonicalRef::as_str)
                    .unwrap()
                    .to_owned(),
                kind: reference
                    .field("kind")
                    .and_then(CanonicalRef::as_str)
                    .unwrap()
                    .to_owned(),
                byte_length: reference
                    .field("byteLength")
                    .and_then(CanonicalRef::integer_text)
                    .unwrap()
                    .parse::<i64>()
                    .unwrap(),
            });
        }
        let event_data_ref = source.field("data").unwrap();
        let event_data =
            loads_strict(std::str::from_utf8(&event_data_ref.canonical_bytes()).unwrap()).unwrap();
        batch.push(EventWrite {
            event_id: source
                .field("eventId")
                .and_then(CanonicalRef::as_str)
                .unwrap()
                .to_owned(),
            event_kind: source
                .field("eventKind")
                .and_then(CanonicalRef::as_str)
                .unwrap()
                .to_owned(),
            data: event_data,
            recorded_at_ms: source
                .field("recordedAtMs")
                .and_then(CanonicalRef::integer_text)
                .unwrap()
                .parse()
                .unwrap(),
            caused_by_event_id: None,
            referenced_objects: refs,
        });
    }

    // First commit durable Claim+Dispatch *before* any physical outbound
    // HTTP request. The final source-authored UNKNOWN Event must be committed
    // only after an actual ambiguous loopback Provider transport response.
    let mut writer = Client::connect(&writer_dsn, NoTls).unwrap();
    let first = acquire_run_lease(
        &mut writer,
        &schema,
        run_id,
        "test:rust-native-provider-journal",
        30_000,
        1008,
        Some(1),
    )
    .unwrap();
    assert_eq!(
        append_events(&mut writer, &schema, run_id, &batch[..2], 1, &first, 1008).unwrap(),
        Admission::Created
    );
    drop(writer);

    let mut readonly = Client::connect(&readonly_dsn, NoTls).unwrap();
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 1, &batch[..2]).unwrap(),
        JournalObservation::ExactCommitted
    );
    let dispatch = inspect_pg_provider_head(&mut readonly, &schema, run_id, model)
        .unwrap()
        .expect("durable DISPATCHING must exist before any socket send");
    assert_eq!(dispatch.status(), ProviderStatus::Dispatching);
    assert_eq!(
        dispatch.recovery_posture(),
        RecoveryPosture::ReconcileWithProviderOwner
    );

    // This is an actual loopback socket, not a synthetic ProviderResult. The
    // server deliberately closes after accepting a request, without returning
    // an HTTP result. The client must report UNKNOWN and never auto-resend.
    let verified = inspect_pg_no_tool_run(&mut readonly, &schema, run_id, model)
        .expect("same PG Contract must be source valid");
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let endpoint = format!(
        "http://{}/v1/chat/completions",
        listener.local_addr().unwrap()
    );
    let inbound = thread::spawn(move || {
        let (mut socket, _) = listener.accept().unwrap();
        socket
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut bytes = [0u8; 4096];
        let count = socket.read(&mut bytes).unwrap();
        assert!(count > 0);
        let received = String::from_utf8_lossy(&bytes[..count]);
        assert!(received.starts_with("POST /v1/chat/completions HTTP/1.1"));
        // Drop socket deliberately: response status/commit is unknowable.
    });
    let mut provider =
        HttpModelProvider::new_provider_only(&endpoint, "test", "system", "question", &verified)
            .unwrap();
    assert!(matches!(provider.turn(1, &[]), ProviderResult::Unknown));
    inbound.join().unwrap();
    assert!(provider.last_usage().is_none());

    // Now, and only now, commit source-authored UNKNOWN in the same PG Run.
    let mut writer = Client::connect(&writer_dsn, NoTls).unwrap();
    let second = acquire_run_lease(
        &mut writer,
        &schema,
        run_id,
        "test:rust-native-provider-journal",
        30_000,
        1012,
        Some(3),
    )
    .unwrap();
    assert_eq!(
        append_events(&mut writer, &schema, run_id, &batch[2..], 3, &second, 1012).unwrap(),
        Admission::Created
    );
    drop(writer);
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 3, &batch[2..]).unwrap(),
        JournalObservation::ExactCommitted
    );
    let observed = read_run_readonly(&mut readonly, &schema, run_id).unwrap();
    assert_eq!(observed.projection.revision, 4);
    assert_eq!(observed.events.len(), 4);
    let head = inspect_pg_provider_head(&mut readonly, &schema, run_id, model)
        .unwrap()
        .expect("native Rust Journal must expose real Python V4 CAS");
    assert_eq!(head.record_digest(), expected_record);
    assert_eq!(head.event_id(), batch[2].event_id);
    assert_eq!(head.status(), ProviderStatus::Unknown);
    assert_eq!(
        head.recovery_posture(),
        RecoveryPosture::RetainUnknownAndReconcile
    );

    // A lost response to the PG Writer itself may replay the exact commit,
    // but this does NOT authorize a second physical Provider send.
    let mut retry = Client::connect(&writer_dsn, NoTls).unwrap();
    assert_eq!(
        append_events(&mut retry, &schema, run_id, &batch[2..], 3, &second, 1012).unwrap(),
        Admission::Existing
    );
    assert_eq!(
        read_run_readonly(&mut readonly, &schema, run_id)
            .unwrap()
            .projection
            .revision,
        4
    );
    let mut wrong = batch[2..].to_vec();
    wrong[0].data = loads_strict(r#"{"forged":"physical effect completed"}"#).unwrap();
    assert!(matches!(
        observe_exact_batch(&mut readonly, &schema, run_id, 3, &wrong),
        Err(WriteError::Conflict(_))
    ));
    println!("PG18_RUST_WRITER_PYTHON_PROVIDER_V4_UNKNOWN_READBACK_EXACT_PASS");
}
