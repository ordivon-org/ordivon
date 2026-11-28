//! True Python Store→PG18→A verified CAS/Journal→B Provider recovery head.
//! All Provider events are synthetic test-only identities, with zero external
//! model requests. A readonly DB role is enforced by the shared PG runner.
use std::{fs, path::Path};

use ordivon_harness_core::{
    canonical_bytes, digest_bytes, loads_strict, CanonicalDocument, CanonicalRef,
};
use ordivon_harness_loop_b_probe::pg_domain_read::{
    inspect_pg_provider_head, ExpectedModel, PgDomainInspectionError, PgProviderRecoveryError,
};
use ordivon_harness_loop_b_probe::provider_head::{
    build_event_v4, build_v4, ProviderStatus, RecoveryPosture,
};
use ordivon_harness_pg::{
    journal_write::{
        append_events, append_events_with_objects, observe_exact_batch, Admission, EventWrite,
        JournalObservation, StoredRef, WriteError,
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
    for label in ["wrong_state", "extra_reference", "wrong_event_status"] {
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
/// Python supplies an independent oracle; Rust owns Provider V4 CAS and Event
/// commits; after the writer connection disappears Rust read-only recovery
/// observes UNKNOWN without dispatching or inferring a safe retry. Finally,
/// the original Python Store validates the same immutable Journal.
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
    let mut records = Vec::new();
    let mut previous_digest = CanonicalDocument::null();
    for n in 0..3 {
        let source = events.index(n).unwrap();
        // Python provides semantic inputs and expected metadata, not CAS bytes.
        // Rust derives the ID, canonical bytes and prior record link.
        let field_bytes = source.field("recordFields").unwrap().canonical_bytes();
        let fields = loads_strict(std::str::from_utf8(&field_bytes).unwrap()).unwrap();
        assert_eq!(fields.get("previousRecordDigest").unwrap(), previous_digest);
        let record = build_v4(
            fields
                .object_entries()
                .unwrap()
                .map(|(key, _)| {
                    let value = if key == "previousRecordDigest" {
                        previous_digest.clone()
                    } else {
                        fields.get(key).unwrap()
                    };
                    (key.to_owned(), value)
                })
                .collect(),
        )
        .unwrap();
        let bytes = canonical_bytes(&record);
        let built_digest = digest_bytes(&bytes);
        let data = source.field("data").unwrap();
        assert_eq!(
            built_digest,
            data.field("providerCallRecordDigest")
                .and_then(CanonicalRef::as_str)
                .unwrap()
        );
        assert_eq!(
            built_digest,
            data.field("providerCallRecordObjectDigest")
                .and_then(CanonicalRef::as_str)
                .unwrap()
        );
        previous_digest = CanonicalDocument::string(&built_digest);
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
        let record_ref = refs
            .iter()
            .find(|r| r.kind == "harness-provider-call-record")
            .unwrap();
        assert_eq!(record_ref.digest, built_digest);
        assert_eq!(record_ref.byte_length, i64::try_from(bytes.len()).unwrap());
        let non_record_refs: Vec<_> = refs
            .iter()
            .filter(|r| r.kind != "harness-provider-call-record")
            .cloned()
            .collect();
        let cause = batch.last().map(|e: &EventWrite| e.event_id.clone());
        let event = build_event_v4(&record, &non_record_refs, cause.clone()).unwrap();
        assert_eq!(
            event.event_id,
            source
                .field("eventId")
                .and_then(CanonicalRef::as_str)
                .unwrap()
        );
        assert_eq!(
            event.event_kind,
            source
                .field("eventKind")
                .and_then(CanonicalRef::as_str)
                .unwrap()
        );
        assert_eq!(
            event.recorded_at_ms.to_string(),
            source
                .field("recordedAtMs")
                .and_then(CanonicalRef::integer_text)
                .unwrap()
        );
        assert_eq!(
            event.caused_by_event_id.as_deref(),
            source
                .field("causedByEventId")
                .and_then(CanonicalRef::as_str)
        );
        assert_eq!(
            canonical_bytes(&event.data),
            source.field("data").unwrap().canonical_bytes()
        );
        assert_eq!(event.referenced_objects, refs);
        let mut reordered = non_record_refs.clone();
        reordered.reverse();
        let same = build_event_v4(&record, &reordered, cause.clone()).unwrap();
        assert_eq!(same.referenced_objects, refs);
        let mut missing = non_record_refs.clone();
        missing.pop();
        assert!(build_event_v4(&record, &missing, cause.clone()).is_err());
        let mut wrong = non_record_refs.clone();
        wrong[0].kind = "wrong-kind".into();
        assert!(build_event_v4(&record, &wrong, cause.clone()).is_err());
        let mut duplicate = non_record_refs.clone();
        duplicate.push(duplicate[0].clone());
        assert!(build_event_v4(&record, &duplicate, cause.clone()).is_err());
        let wrong_cause = if cause.is_some() {
            None
        } else {
            Some("event:unexpected".into())
        };
        assert!(build_event_v4(&record, &non_record_refs, wrong_cause).is_err());
        println!(
            "PG18_NATIVE_PROVIDER_EVENT_BUILT stage={n} digest={built_digest} event={}",
            event.event_id
        );
        records.push(record);
        batch.push(event);
    }

    // A real Provider call cannot be represented by one transaction spanning
    // CLAIMED, DISPATCHING and UNKNOWN: the external transport lies between
    // durable states. Exercise each commit/reconnect boundary without sending
    // a model request, and retain the exact original Event identities.
    let mut readonly = Client::connect(&readonly_dsn, NoTls).unwrap();
    let object_exists = |db: &mut Client, digest: &str| -> bool {
        assert!(schema.starts_with("hpg_rust_isolated_a_"));
        db.query_one(
            &format!("SELECT EXISTS(SELECT 1 FROM {schema}.objects WHERE digest=$1)"),
            &[&digest],
        )
        .unwrap()
        .get(0)
    };
    let mut prior_lease = None;
    for (index, (status, posture)) in [
        (
            ProviderStatus::Claimed,
            RecoveryPosture::RecheckClaimAndDurableFence,
        ),
        (
            ProviderStatus::Dispatching,
            RecoveryPosture::ReconcileWithProviderOwner,
        ),
        (
            ProviderStatus::Unknown,
            RecoveryPosture::RetainUnknownAndReconcile,
        ),
    ]
    .into_iter()
    .enumerate()
    {
        let revision = 1 + i64::try_from(index).unwrap();
        let event = &batch[index..index + 1];
        let now = event[0].recorded_at_ms;
        let digest = text(&event[0].data, "providerCallRecordDigest");
        let new_objects = [("harness-provider-call-record", &records[index])];
        assert!(
            !object_exists(&mut readonly, digest),
            "oracle must not preseed CAS"
        );
        assert_eq!(
            observe_exact_batch(&mut readonly, &schema, run_id, revision, event).unwrap(),
            JournalObservation::NotObserved
        );
        // Absence of this Journal Event says nothing about external effects.
        let mut writer = Client::connect(&writer_dsn, NoTls).unwrap();
        if let Some(stale) = &prior_lease {
            assert!(matches!(
                append_events_with_objects(
                    &mut writer,
                    &schema,
                    run_id,
                    (event, &new_objects),
                    revision,
                    stale,
                    now
                ),
                Err(WriteError::Fenced)
            ));
        }
        let lease = acquire_run_lease(
            &mut writer,
            &schema,
            run_id,
            "test:rust-native-provider-journal",
            30_000,
            now,
            Some(revision),
        )
        .unwrap();
        // Existing API cannot succeed before CAS exists.
        assert!(matches!(
            append_events(&mut writer, &schema, run_id, event, revision, &lease, now),
            Err(WriteError::Conflict(_))
        ));
        let mut invalid = event.to_vec();
        invalid[0].recorded_at_ms = 0;
        assert!(matches!(
            append_events_with_objects(
                &mut writer,
                &schema,
                run_id,
                (&invalid, &new_objects),
                revision,
                &lease,
                now
            ),
            Err(WriteError::Invalid("timestamp regressed"))
        ));
        assert!(
            !object_exists(&mut readonly, digest),
            "failed transaction must not leave CAS"
        );
        let wrong_kind = [("wrong-kind", &records[index])];
        assert!(matches!(
            append_events_with_objects(
                &mut writer,
                &schema,
                run_id,
                (event, &wrong_kind),
                revision,
                &lease,
                now
            ),
            Err(WriteError::Invalid("new CAS object not referenced"))
        ));
        assert_eq!(
            append_events_with_objects(
                &mut writer,
                &schema,
                run_id,
                (event, &new_objects),
                revision,
                &lease,
                now
            )
            .unwrap(),
            Admission::Created
        );
        drop(writer);
        // Reconnect rather than rely on the previous writer's memory.
        readonly = Client::connect(&readonly_dsn, NoTls).unwrap();
        assert!(object_exists(&mut readonly, digest));
        assert_eq!(
            observe_exact_batch(&mut readonly, &schema, run_id, revision, event).unwrap(),
            JournalObservation::ExactCommitted
        );
        let head = inspect_pg_provider_head(&mut readonly, &schema, run_id, model)
            .unwrap()
            .expect("committed Provider head");
        assert_eq!(head.run_revision(), revision + 1);
        assert_eq!(head.event_id(), event[0].event_id);
        assert_eq!(
            head.record_digest(),
            text(&event[0].data, "providerCallRecordDigest")
        );
        assert_eq!(head.status(), status);
        assert_eq!(head.recovery_posture(), posture);
        if index < 2 {
            assert!(matches!(
                observe_exact_batch(&mut readonly, &schema, run_id, 1, &batch),
                Err(WriteError::Conflict(_))
            ));
        }
        // Exact Journal re-observation/replay is not permission to resend.
        let mut retry = Client::connect(&writer_dsn, NoTls).unwrap();
        assert_eq!(
            append_events_with_objects(
                &mut retry,
                &schema,
                run_id,
                (event, &new_objects),
                revision,
                &lease,
                now
            )
            .unwrap(),
            Admission::Existing
        );
        assert_eq!(
            read_run_readonly(&mut readonly, &schema, run_id)
                .unwrap()
                .projection
                .revision,
            revision + 1
        );
        prior_lease = Some(lease);
        println!(
            "PG18_NATIVE_PROVIDER_BOUNDARY status={} revision={} posture={:?}",
            status.as_str(),
            revision + 1,
            posture
        );
    }
    let lease = prior_lease.expect("last consumed lease");
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 1, &batch).unwrap(),
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

    // The Writer's source-defined exact retry is idempotent even though its
    // lease was atomically consumed. No duplicate Event and no redispatch.
    let mut retry = Client::connect(&writer_dsn, NoTls).unwrap();
    assert_eq!(
        append_events(&mut retry, &schema, run_id, &batch, 1, &lease, 1008).unwrap(),
        Admission::Existing
    );
    assert_eq!(
        read_run_readonly(&mut readonly, &schema, run_id)
            .unwrap()
            .projection
            .revision,
        4
    );
    let mut wrong = batch.clone();
    wrong[2].data = loads_strict(r#"{"forged":"physical effect completed"}"#).unwrap();
    assert!(matches!(
        observe_exact_batch(&mut readonly, &schema, run_id, 1, &wrong),
        Err(WriteError::Conflict(_))
    ));
    println!("PG18_RUST_WRITER_PYTHON_PROVIDER_V4_UNKNOWN_READBACK_EXACT_PASS");
}
