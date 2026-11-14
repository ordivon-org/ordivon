//! True Python Store→PG18→A verified CAS/Journal→B Provider recovery head.
//! All Provider events are synthetic test-only identities, with zero external
//! model requests. A readonly DB role is enforced by the shared PG runner.
use std::{fs, io::Read, net::TcpListener, path::Path, thread, time::Duration};

use ordivon_harness_core::{
    canonical_bytes, digest_bytes, loads_strict, CanonicalDocument, CanonicalRef,
};
use ordivon_harness_loop::native_loop::{
    AdmittedTool, DurableJournal, EffectReceiver, EffectResult, ModelDecision, ModelVisibleContent,
    NativeAgentLoop, RunResult,
};
use ordivon_harness_loop::native_provider_http::HttpModelProvider;
use ordivon_harness_loop::pg_domain_read::{
    inspect_pg_no_tool_run, inspect_pg_provider_head, ExpectedModel, PgDomainInspectionError,
    PgProviderRecoveryError,
};
use ordivon_harness_loop::pg_provider_config::inspect_pg_provider_transport;
use ordivon_harness_loop::provider_head::{ProviderStatus, RecoveryPosture};
use ordivon_harness_loop::provider_v4_author::{
    author_provider_failure, author_provider_v4, DispatchSafety, ProviderFailureCode,
    ProviderFailureSpec, ProviderV4Seed, ProviderV4Transition,
};
use ordivon_harness_pg::{
    journal_write::{
        append_events, observe_exact_batch, Admission, EventWrite, JournalObservation, StoredRef,
        WriteError,
    },
    lease::{acquire_run_lease, RunLease},
    provider_cas::{put_provider_cas, ProviderCasKind},
    read_run_readonly, ReadError,
};
use postgres::{Client, NoTls};

fn text<'a>(v: &'a CanonicalDocument, key: &str) -> &'a str {
    v.field(key).and_then(CanonicalRef::as_str).unwrap()
}

/// Test adapter consuming the EXISTING PG Lease/Writer, never a new Store.
/// Distinct from R24: Provider V4 record CAS is authored by Rust at the exact
/// lifecycle transition, not pre-computed or stored by Python or test setup.
/// Security materialization + current issuer are deliberately NOT proven.
struct SourcePgUnknownJournal {
    writer_dsn: String,
    schema: String,
    run_id: String,
    batch: Vec<EventWrite>,
    python_first_source: CanonicalDocument,
    python_failure_oracle: CanonicalDocument,
    prepared: bool,
    dispatch_digest: Option<String>,
    unknown_lease: Option<RunLease>,
}
fn native_seed<'a>(doc: &'a CanonicalDocument) -> ProviderV4Seed<'a> {
    let int = |key: &str| -> u64 {
        doc.field(key)
            .unwrap()
            .integer_text()
            .unwrap()
            .parse()
            .unwrap()
    };
    ProviderV4Seed {
        provider_call_id: text(doc, "providerCallId"),
        harness_run_id: text(doc, "harnessRunId"),
        binding_digest: text(doc, "bindingDigest"),
        source_kind: text(doc, "sourceKind"),
        source_digest: text(doc, "sourceDigest"),
        source_object_digest: text(doc, "sourceObjectDigest"),
        state_object_digest: text(doc, "stateObjectDigest"),
        turn_id: text(doc, "turnId"),
        turn_sequence: int("turnSequence"),
        request_digest: text(doc, "requestDigest"),
        request_object_digest: None,
        provider_request_digest: text(doc, "providerRequestDigest"),
        adapter_id: text(doc, "adapterId"),
        requested_model_id: text(doc, "requestedModelId"),
        holder_id: text(doc, "holderId"),
        claim_generation: int("claimGeneration"),
        issued_at_ms: int("issuedAtMs"),
        expires_at_ms: int("expiresAtMs"),
    }
}
fn expected_ref<'a>(e: &'a EventWrite, kind: &str) -> Result<&'a StoredRef, String> {
    e.referenced_objects
        .iter()
        .find(|r| r.kind == kind)
        .ok_or_else(|| format!("source reference absent for kind {kind}"))
}
impl DurableJournal for SourcePgUnknownJournal {
    fn prepare_provider(&mut self, turn: u32) -> Result<(), String> {
        if self.prepared || turn != 1 || self.batch.len() != 3 {
            return Err("unexpected Provider dispatch".into());
        }
        let seed = native_seed(&self.python_first_source);
        if seed.harness_run_id != self.run_id {
            return Err("source Run identity drift".into());
        }
        let mut db = Client::connect(&self.writer_dsn, NoTls).map_err(|e| e.to_string())?;
        let claimed = author_provider_v4(
            &seed,
            ProviderV4Transition::Claimed { previous: None },
            u64::try_from(self.batch[0].recorded_at_ms).map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("{e:?}"))?;
        let claim_ref = put_provider_cas(
            &mut db,
            &self.schema,
            ProviderCasKind::RecordV4,
            &claimed,
            self.batch[0].recorded_at_ms,
        )
        .map_err(|e| e.to_string())?;
        if &claim_ref != expected_ref(&self.batch[0], "harness-provider-call-record")? {
            return Err("Rust V4 claimed bytes differ from independent Python source".into());
        }
        let dispatching = author_provider_v4(
            &seed,
            ProviderV4Transition::Dispatching {
                previous: &claim_ref.digest,
            },
            u64::try_from(self.batch[1].recorded_at_ms).map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("{e:?}"))?;
        let dispatch_ref = put_provider_cas(
            &mut db,
            &self.schema,
            ProviderCasKind::RecordV4,
            &dispatching,
            self.batch[1].recorded_at_ms,
        )
        .map_err(|e| e.to_string())?;
        if &dispatch_ref != expected_ref(&self.batch[1], "harness-provider-call-record")? {
            return Err("Rust V4 dispatch bytes differ from independent Python source".into());
        }
        // Only after the CAS witnesses exist, obtain a live PG lease and
        // commit the exact two Event transitions before physical HTTP.
        let lease = acquire_run_lease(
            &mut db,
            &self.schema,
            &self.run_id,
            "test:rust-native-provider-journal",
            30_000,
            1008,
            Some(1),
        )
        .map_err(|e| e.to_string())?;
        match append_events(
            &mut db,
            &self.schema,
            &self.run_id,
            &self.batch[..2],
            1,
            &lease,
            1008,
        )
        .map_err(|e| e.to_string())?
        {
            Admission::Created => {}
            Admission::Existing => return Err("source Run unexpectedly already dispatched".into()),
        }
        self.dispatch_digest = Some(dispatch_ref.digest);
        self.prepared = true;
        Ok(())
    }
    fn complete_provider(&mut self, _: u32, _: &ModelDecision) -> Result<(), String> {
        Err("test intentionally loses Provider response".into())
    }
    fn admit_tool(
        &mut self,
        _: u32,
        _: &ordivon_harness_loop::tool_call::ModelToolCall,
    ) -> Result<AdmittedTool, String> {
        Err("no Tool Grant on source no-Tool Run".into())
    }
    fn record_effect(
        &mut self,
        _: u32,
        _: &AdmittedTool,
        _: &EffectResult,
    ) -> Result<ModelVisibleContent, String> {
        Err("no Tool may be executed".into())
    }
    fn record_completion(&mut self, _: u32, _: &str) -> Result<(), String> {
        Err("no claimed task completion".into())
    }
    fn record_pause(&mut self, turn: u32) -> Result<(), String> {
        let previous = self
            .dispatch_digest
            .as_ref()
            .ok_or_else(|| "Cannot record UNKNOWN without committed DISPATCHING".to_owned())?;
        if !self.prepared || self.unknown_lease.is_some() || turn != 1 {
            return Err("unadmitted or repeated UNKNOWN".into());
        }
        let failure = &self.python_failure_oracle;
        if text(failure, "failureCode") != "provider_transport_failed"
            || text(failure, "dispatchSafety") != "dispatch_ambiguous"
        {
            return Err("source failure oracle isn't transport UNKNOWN".into());
        }
        let fail = author_provider_failure(&ProviderFailureSpec {
            provider_call_id: text(failure, "providerCallId"),
            request_digest: text(failure, "requestDigest"),
            provider_request_digest: text(failure, "providerRequestDigest"),
            failure_code: ProviderFailureCode::TransportFailed,
            dispatch_safety: DispatchSafety::Ambiguous,
            detail: text(failure, "detail"),
        })
        .map_err(|e| format!("{e:?}"))?;
        let mut db = Client::connect(&self.writer_dsn, NoTls).map_err(|e| e.to_string())?;
        // The failure receipt and UNKNOWN V4 record are created only AFTER
        // NativeAgentLoop observed a truly ambiguous HTTP response.
        let fail_ref = put_provider_cas(
            &mut db,
            &self.schema,
            ProviderCasKind::FailureReceipt,
            &fail,
            self.batch[2].recorded_at_ms,
        )
        .map_err(|e| e.to_string())?;
        if &fail_ref != expected_ref(&self.batch[2], "harness-provider-call-failure")? {
            return Err("Rust failure CAS differs from Python source oracle".into());
        }
        let unknown = author_provider_v4(
            &native_seed(&self.python_first_source),
            ProviderV4Transition::Unknown {
                previous,
                failure_digest: &fail_ref.digest,
                failure_object_digest: &fail_ref.digest,
            },
            u64::try_from(self.batch[2].recorded_at_ms).map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("{e:?}"))?;
        let unknown_ref = put_provider_cas(
            &mut db,
            &self.schema,
            ProviderCasKind::RecordV4,
            &unknown,
            self.batch[2].recorded_at_ms,
        )
        .map_err(|e| e.to_string())?;
        if &unknown_ref != expected_ref(&self.batch[2], "harness-provider-call-record")? {
            return Err("Rust unknown CAS differs from Python source oracle".into());
        }
        let lease = acquire_run_lease(
            &mut db,
            &self.schema,
            &self.run_id,
            "test:rust-native-provider-journal",
            30_000,
            1012,
            Some(3),
        )
        .map_err(|e| e.to_string())?;
        match append_events(
            &mut db,
            &self.schema,
            &self.run_id,
            &self.batch[2..],
            3,
            &lease,
            1012,
        )
        .map_err(|e| e.to_string())?
        {
            Admission::Created => {}
            Admission::Existing => return Err("source UNKNOWN already committed".into()),
        }
        self.unknown_lease = Some(lease);
        Ok(())
    }
}
struct NoEffect;
impl EffectReceiver for NoEffect {
    fn execute(&mut self, _: &AdmittedTool, _: &CanonicalDocument) -> EffectResult {
        panic!("source no-Tool Run physically executed a Tool");
    }
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

    // Python is the independent source oracle only; all Provider V4 and
    // failure CAS documents are now written by Rust AT THE ACTUAL TRANSITION.
    let source_records = native
        .get("sourceRecords")
        .expect("Python V4 source oracle");
    assert_eq!(source_records.as_borrowed().array_len(), Some(3));
    let first_doc = loads_strict(
        std::str::from_utf8(&source_records.index(0).unwrap().canonical_bytes()).unwrap(),
    )
    .unwrap();
    let failure_oracle = native.get("sourceFailure").unwrap();
    assert_eq!(native_seed(&first_doc).harness_run_id, run_id);
    assert_eq!(
        native_seed(&first_doc).requested_model_id,
        model.requested_model_id
    );

    // Freeze the exact HTTP body *before* native PostgreSQL Claim/Dispatch.
    // It must match the original Python source-authored V4 ProviderRequest
    // digest, not a synthetic hash invented by this Rust test.
    let mut source_db = Client::connect(&readonly_dsn, NoTls).unwrap();
    let verified = inspect_pg_no_tool_run(&mut source_db, &schema, run_id, model)
        .expect("source-valid no-Tool Run");
    let transport = inspect_pg_provider_transport(&mut source_db, &schema, &verified)
        .expect("Run-bound, CAS-authenticated Provider transport");
    let expected_wire_digest = text(&native, "expectedProviderRequestDigest").to_string();
    let mut provider = HttpModelProvider::new_provider_only_pg_bound(
        &transport,
        &verified,
        "credential:verified-source-r22",
        "test",
        "system",
        "question",
    )
    .unwrap();
    assert_eq!(
        provider.freeze_next_request_digest(&[]).unwrap(),
        expected_wire_digest,
        "Provider V4 CAS must name the EXACT bytes frozen for outbound send"
    );
    let target_port = reqwest::Url::parse(transport.endpoint())
        .unwrap()
        .port()
        .unwrap();
    drop(source_db);

    let mut journal = SourcePgUnknownJournal {
        writer_dsn: writer_dsn.clone(),
        schema: schema.clone(),
        run_id: run_id.to_owned(),
        batch: batch.clone(),
        prepared: false,
        python_first_source: first_doc,
        python_failure_oracle: failure_oracle,
        dispatch_digest: None,
        unknown_lease: None,
    };

    // Real localhost HTTP send, at the endpoint obtained from the same PG
    // Contract-bound CAS configuration. Read the complete JSON body and bind
    // its actual bytes to the original Python V4 providerRequestDigest.
    let listener = TcpListener::bind(("127.0.0.1", target_port)).unwrap();
    let inbound_digest = expected_wire_digest.clone();
    let reader_dsn_for_server = readonly_dsn.clone();
    let schema_for_server = schema.clone();
    let run_id_for_server = run_id.to_owned();
    let server_provider_id = model.provider_id.to_owned();
    let server_adapter_id = model.adapter_id.to_owned();
    let server_requested_model_id = model.requested_model_id.to_owned();
    let prepare_batch_for_server = batch[..2].to_vec();
    let inbound = thread::spawn(move || {
        let (mut socket, _) = listener.accept().unwrap();
        // The server is an independent observer: an HTTP connection before
        // a durable PG DISPATCHING record is a fatal consumer violation.
        let mut pg = Client::connect(&reader_dsn_for_server, NoTls).unwrap();
        assert_eq!(
            observe_exact_batch(
                &mut pg,
                &schema_for_server,
                &run_id_for_server,
                1,
                &prepare_batch_for_server
            )
            .unwrap(),
            JournalObservation::ExactCommitted
        );
        let dispatched = inspect_pg_provider_head(
            &mut pg,
            &schema_for_server,
            &run_id_for_server,
            ExpectedModel {
                provider_id: &server_provider_id,
                adapter_id: &server_adapter_id,
                requested_model_id: &server_requested_model_id,
            },
        )
        .unwrap()
        .unwrap();
        assert_eq!(dispatched.status(), ProviderStatus::Dispatching);
        drop(pg);
        socket
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut collected = Vec::new();
        let mut buf = [0u8; 8192];
        loop {
            let n = socket.read(&mut buf).unwrap();
            assert!(n > 0, "request must not end before complete HTTP body");
            collected.extend_from_slice(&buf[..n]);
            if let Some(at) = collected.windows(4).position(|b| b == b"\r\n\r\n") {
                let header = String::from_utf8_lossy(&collected[..at]);
                assert!(header.starts_with("POST /v1/chat/completions HTTP/1.1"));
                let content_length = header
                    .lines()
                    .find_map(|line| {
                        let (k, v) = line.split_once(':')?;
                        k.eq_ignore_ascii_case("content-length")
                            .then(|| v.trim().parse::<usize>().ok())
                            .flatten()
                    })
                    .expect("provider sends a content length");
                if collected.len() >= at + 4 + content_length {
                    assert_eq!(
                        digest_bytes(&collected[at + 4..at + 4 + content_length]),
                        inbound_digest,
                        "physically transmitted JSON differs from V4 CAS request digest"
                    );
                    break;
                }
            }
        }
        // Drop after receiving actual bytes; no response status or content
        // exists, so the physical Provider outcome is genuinely ambiguous.
    });
    let mut no_effect = NoEffect;
    let result = NativeAgentLoop::new_provider_only(
        &mut provider,
        &mut journal,
        &mut no_effect,
        &verified,
        1,
    )
    .unwrap()
    .run();
    assert_eq!(result, Ok(RunResult::PausedUnknown));
    inbound.join().unwrap();
    assert!(provider.last_usage().is_none());
    assert!(
        provider.freeze_next_request_digest(&[]).is_err(),
        "Unknown instance must never be rearmed to resend frozen request"
    );
    let mut readonly = Client::connect(&readonly_dsn, NoTls).unwrap();
    assert!(
        journal.unknown_lease.is_some(),
        "NativeAgentLoop journal must commit UNKNOWN after physical loss"
    );
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 3, &batch[2..]).unwrap(),
        JournalObservation::ExactCommitted
    );
    let observed = read_run_readonly(&mut readonly, &schema, run_id).unwrap();
    assert_eq!(observed.projection.revision, 4);
    assert_eq!(observed.events.len(), 4);
    // The independent Python original V4 source oracle was never persisted
    // on this Run. Validate the exact Rust-produced, live-PG CAS documents
    // AFTER NativeAgentLoop physically executed and recovered.
    for (i, event) in batch.iter().enumerate() {
        let expected = loads_strict(
            std::str::from_utf8(&source_records.index(i).unwrap().canonical_bytes()).unwrap(),
        )
        .unwrap();
        let record_ref = expected_ref(event, "harness-provider-call-record").unwrap();
        let found = ordivon_harness_pg::read_cas_object_readonly(
            &mut readonly,
            &schema,
            &record_ref.digest,
            "harness-provider-call-record",
        )
        .unwrap();
        assert_eq!(canonical_bytes(&found), canonical_bytes(&expected));
    }
    let failure_ref = expected_ref(&batch[2], "harness-provider-call-failure").unwrap();
    let found = ordivon_harness_pg::read_cas_object_readonly(
        &mut readonly,
        &schema,
        &failure_ref.digest,
        "harness-provider-call-failure",
    )
    .unwrap();
    assert_eq!(
        canonical_bytes(&found),
        canonical_bytes(&journal.python_failure_oracle)
    );

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
        append_events(
            &mut retry,
            &schema,
            run_id,
            &batch[2..],
            3,
            journal.unknown_lease.as_ref().unwrap(),
            1012
        )
        .unwrap(),
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
