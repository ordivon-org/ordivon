//! True Python Store→PG18→A verified CAS/Journal→B Provider recovery head.
//! All Provider events are synthetic test-only identities, with zero external
//! model requests. A readonly DB role is enforced by the shared PG runner.
use std::{
    fs,
    io::{Read, Write},
    net::TcpListener,
    path::Path,
    thread,
    time::Duration,
};

use ordivon_harness_core::{
    canonical_bytes, digest_bytes, loads_strict, CanonicalDocument, CanonicalRef,
};
use ordivon_harness_loop::agent_turn_result::author_no_tool_turn_result;
use ordivon_harness_loop::native_loop::{
    AdmittedTool, DurableJournal, EffectReceiver, EffectResult, ModelDecision, ModelVisibleContent,
    NativeAgentLoop, PauseCause, Provider, ProviderResult, ProviderWireObservation, RunFault,
    RunResult, ToolObservation,
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
        append_events, append_events_with_provider_cas, observe_exact_batch, Admission, EventWrite,
        JournalObservation, ProviderEventBatch, StoredRef, WriteError,
    },
    lease::{acquire_run_lease, RunLease},
    provider_cas::{put_provider_cas, ProviderCasKind, ProviderStagedCas},
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
fn source_event_batch(native: &CanonicalDocument) -> Vec<EventWrite> {
    let events = native.get("events").expect("source event oracle");
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

    batch
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
    fn complete_provider(
        &mut self,
        _: u32,
        _: &ModelDecision,
        _: Option<&ProviderWireObservation>,
    ) -> Result<(), String> {
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
    fn record_pause(&mut self, turn: u32, cause: PauseCause) -> Result<(), String> {
        if cause != PauseCause::ProviderUnknown {
            return Err("Provider V4 Journal refuses non-Provider pause cause".into());
        }
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
/// R29 POSITIVE real localhost model-response test consumer. The source
/// Python AgentTurnResult and V4 records are pure independent Oracle bytes.
/// The real native Rust Loop must author and write the entire result/COMPLETED
/// CAS+Event only AFTER receiving a verified positive HTTP wire response.
struct SourcePgCompletedJournal {
    base: SourcePgUnknownJournal,
    original_result_oracle: CanonicalDocument,
    model_call_id: String,
    requested_model: String,
    retain_model_content: bool,
    completed: bool,
}
impl DurableJournal for SourcePgCompletedJournal {
    fn prepare_provider(&mut self, turn: u32) -> Result<(), String> {
        self.base.prepare_provider(turn)
    }
    fn complete_provider(
        &mut self,
        turn: u32,
        decision: &ModelDecision,
        wire: Option<&ProviderWireObservation>,
    ) -> Result<(), String> {
        if turn != 1 || self.completed || !self.base.prepared || self.base.batch.len() != 3 {
            return Err("Unqualified positive Provider transition".into());
        }
        let result =
            author_no_tool_turn_result(&self.model_call_id, &self.requested_model, decision, wire)
                .map_err(|e| format!("Positive AgentTurnResult rejected: {e:?}"))?;
        if canonical_bytes(&result) != canonical_bytes(&self.original_result_oracle) {
            return Err("Rust result differs from original Python AgentTurnResult".into());
        }
        let previous = self
            .base
            .dispatch_digest
            .as_deref()
            .ok_or("no source current DISPATCHING record")?;
        let recorded_at = self.base.batch[2].recorded_at_ms;
        let mut db = Client::connect(&self.base.writer_dsn, NoTls).map_err(|e| e.to_string())?;
        // R30 SOURCE AUTHORITY, not a test-provided retention flag:
        // this is the canonical, verified same-Run PG Contract privacy field.
        // A stale/concurrent Run is still rejected by the original PG Lease.
        let source = read_run_readonly(&mut db, &self.base.schema, &self.base.run_id)
            .map_err(|e| format!("original source PG Run invalid: {e:?}"))?;
        if source.projection.revision != 3
            || source.projection.status != "active"
            || source
                .contract
                .field("harnessRunId")
                .and_then(|v| v.as_str())
                != Some(self.base.run_id.as_str())
        {
            return Err("live original PG Run/Contract currentness lost".into());
        }
        let privacy = source
            .contract
            .field("privacy")
            .and_then(|value| value.field("allowModelContent"))
            .ok_or("source PG Contract privacy flag absent")?;
        let source_allows_content = match privacy.canonical_bytes().as_slice() {
            b"true" => true,
            b"false" => false,
            _ => return Err("invalid source PG privacy flag".into()),
        };
        if source_allows_content != self.retain_model_content {
            return Err("caller retention flag differs from immutable source Contract".into());
        }
        let result_digest = digest_bytes(&canonical_bytes(&result));
        // The source Contract's privacy policy governs actual CAS retention.
        // The positive Provider fact survives redaction through resultDigest;
        // forbidden model content must never enter the PostgreSQL objects table.
        let result_object = if source_allows_content {
            let reference = StoredRef {
                digest: result_digest.clone(),
                kind: "agent-turn-result".to_string(),
                byte_length: i64::try_from(canonical_bytes(&result).len())
                    .map_err(|e| e.to_string())?,
            };
            if &reference != expected_ref(&self.base.batch[2], "agent-turn-result")? {
                return Err("Source result object reference mismatch".into());
            }
            Some(reference)
        } else {
            if self.base.batch[2]
                .referenced_objects
                .iter()
                .any(|r| r.kind == "agent-turn-result")
            {
                return Err("Privacy-redacted Provider result referenced".into());
            }
            None
        };
        let completed = author_provider_v4(
            &native_seed(&self.base.python_first_source),
            ProviderV4Transition::Completed {
                previous,
                result_digest: &result_digest,
                result_object_digest: result_object.as_ref().map(|r| r.digest.as_str()),
            },
            u64::try_from(recorded_at).map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("{e:?}"))?;
        let completed_ref = StoredRef {
            digest: digest_bytes(&canonical_bytes(&completed)),
            kind: "harness-provider-call-record".to_string(),
            byte_length: i64::try_from(canonical_bytes(&completed).len())
                .map_err(|e| e.to_string())?,
        };
        if &completed_ref != expected_ref(&self.base.batch[2], "harness-provider-call-record")? {
            return Err("Completed provider V4 source byte reference mismatch".into());
        }
        // No standalone CAS writes. Both source-authorized objects and the
        // COMPLETED event are committed or rolled back in ONE original PG TX.
        let mut staged = vec![ProviderStagedCas {
            kind: ProviderCasKind::RecordV4,
            document: &completed,
            first_seen_at_ms: recorded_at,
        }];
        if source_allows_content {
            staged.push(ProviderStagedCas {
                kind: ProviderCasKind::AgentTurnResult,
                document: &result,
                first_seen_at_ms: recorded_at,
            });
        }
        let lease = acquire_run_lease(
            &mut db,
            &self.base.schema,
            &self.base.run_id,
            "test:rust-native-provider-journal",
            30_000,
            recorded_at,
            Some(3),
        )
        .map_err(|e| e.to_string())?;
        match append_events_with_provider_cas(
            &mut db,
            &self.base.schema,
            &self.base.run_id,
            ProviderEventBatch {
                events: &self.base.batch[2..],
                staged: &staged,
            },
            3,
            &lease,
            recorded_at,
        )
        .map_err(|e| e.to_string())?
        {
            Admission::Created => {}
            Admission::Existing => return Err("source COMPLETED already committed".into()),
        }
        self.completed = true;
        Ok(())
    }
    fn admit_tool(
        &mut self,
        _: u32,
        _: &ordivon_harness_loop::tool_call::ModelToolCall,
    ) -> Result<AdmittedTool, String> {
        Err("no source Tool grant on no-Tool Provider Run".into())
    }
    fn record_effect(
        &mut self,
        _: u32,
        _: &AdmittedTool,
        _: &EffectResult,
    ) -> Result<ModelVisibleContent, String> {
        Err("no source Tool effect".into())
    }
    fn record_completion(&mut self, turn: u32, proposal: &str) -> Result<(), String> {
        // This acknowledges a candidate output, not DomainSuccess.
        if self.completed && turn == 1 && proposal == "A useful answer" {
            return Ok(());
        }
        Err("unqualified completion candidate".into())
    }
    fn record_pause(&mut self, _: u32, _: PauseCause) -> Result<(), String> {
        Err("positive-only source consumer cannot fabricate UNKNOWN".into())
    }
}

struct RefuseAnyProviderSend;
impl Provider for RefuseAnyProviderSend {
    fn turn(&mut self, _: u32, _: &[ToolObservation]) -> ProviderResult {
        panic!("stale PG Run passed Journal gate and attempted a Provider send");
    }
}
struct NoEffect;
impl EffectReceiver for NoEffect {
    fn execute(&mut self, _: &AdmittedTool, _: &CanonicalDocument) -> EffectResult {
        panic!("source no-Tool Run physically executed a Tool");
    }
}

/// R29 positive consumer: actual localhost HTTP 200 JSON with reported Usage,
/// NativeAgentLoop drives the original same-Run PG Claim→Dispatch→COMPLETED,
/// Python is ONLY the independent source for V4 + AgentTurnResult canonical
/// bytes. No external LLM was queried; candidate is not DomainSuccess.
fn verify_native_rust_pg_v4_completed_case(source_case: &str, retain_model_content: bool) {
    let writer_dsn = std::env::var("HARNESS_RUST_TEST_PG_WRITER_DSN").unwrap();
    let readonly_dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    let fixture = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let all = loads_strict(&fs::read_to_string(fixture).unwrap()).unwrap();
    let native = all.get(source_case).unwrap();
    let run_id = text(&native, "runId");
    let source_records = native.get("sourceRecords").unwrap();
    let first = loads_strict(
        std::str::from_utf8(&source_records.index(0).unwrap().canonical_bytes()).unwrap(),
    )
    .unwrap();
    let original_result = native.get("sourceResult").unwrap();
    let batch = source_event_batch(&native);
    let model_source = all.get("no_tool").unwrap();
    let model = ExpectedModel {
        provider_id: text(&model_source, "providerId"),
        adapter_id: text(&model_source, "adapterId"),
        requested_model_id: text(&model_source, "requestedModelId"),
    };
    let mut readonly = Client::connect(&readonly_dsn, NoTls).unwrap();
    let verified = inspect_pg_no_tool_run(&mut readonly, &schema, run_id, model).unwrap();
    let transport = inspect_pg_provider_transport(&mut readonly, &schema, &verified).unwrap();
    let mut provider = HttpModelProvider::new_provider_only_pg_bound(
        &transport,
        &verified,
        "credential:verified-source-r22",
        "test",
        "system",
        "question",
    )
    .unwrap();
    let expected_wire = text(&native, "expectedProviderRequestDigest");
    assert_eq!(
        provider.freeze_next_request_digest(&[]).unwrap(),
        expected_wire
    );
    let target_port = reqwest::Url::parse(transport.endpoint())
        .unwrap()
        .port()
        .unwrap();
    let mut journal = SourcePgCompletedJournal {
        base: SourcePgUnknownJournal {
            writer_dsn: writer_dsn.clone(),
            schema: schema.clone(),
            run_id: run_id.to_owned(),
            batch: batch.clone(),
            python_first_source: first,
            python_failure_oracle: loads_strict(r#"{"kind":"unused-positive-failure-oracle"}"#)
                .unwrap(),
            prepared: false,
            dispatch_digest: None,
            unknown_lease: None,
        },
        original_result_oracle: original_result.clone(),
        model_call_id: text(&native, "modelCallId").to_owned(),
        requested_model: model.requested_model_id.to_owned(),
        retain_model_content,
        completed: false,
    };
    // Invalid action MUST be rejected before any real successful transition.
    assert!(journal
        .complete_provider(1, &ModelDecision::RequestInput, None)
        .is_err());
    assert!(!journal.completed);

    let response = text(&native, "responseBody").as_bytes().to_vec();
    let response_digest = digest_bytes(&response);
    assert_eq!(response_digest, text(&native, "expectedRawResponseDigest"));
    let listener = TcpListener::bind(("127.0.0.1", target_port)).unwrap();
    let reader_dsn = readonly_dsn.clone();
    let verify_schema = schema.clone();
    let verify_run = run_id.to_owned();
    let expected_model = (
        model.provider_id.to_owned(),
        model.adapter_id.to_owned(),
        model.requested_model_id.to_owned(),
    );
    let first_two = batch[..2].to_vec();
    let expected_wire_digest = expected_wire.to_owned();
    let inbound = thread::spawn(move || {
        let (mut socket, _) = listener.accept().unwrap();
        // Independent SELECT-only consumer observes the durable DISPATCHING
        // before the external endpoint even reads the model request body.
        let mut pg = Client::connect(&reader_dsn, NoTls).unwrap();
        assert_eq!(
            observe_exact_batch(&mut pg, &verify_schema, &verify_run, 1, &first_two).unwrap(),
            JournalObservation::ExactCommitted
        );
        let observed = inspect_pg_provider_head(
            &mut pg,
            &verify_schema,
            &verify_run,
            ExpectedModel {
                provider_id: &expected_model.0,
                adapter_id: &expected_model.1,
                requested_model_id: &expected_model.2,
            },
        )
        .unwrap()
        .unwrap();
        assert_eq!(observed.status(), ProviderStatus::Dispatching);
        drop(pg);
        socket
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut collected = Vec::new();
        let mut buf = [0u8; 8192];
        loop {
            let n = socket.read(&mut buf).unwrap();
            assert!(n > 0, "read complete admitted HTTP request before reply");
            collected.extend_from_slice(&buf[..n]);
            if let Some(at) = collected.windows(4).position(|b| b == b"\r\n\r\n") {
                let headers = String::from_utf8_lossy(&collected[..at]);
                assert!(headers.starts_with("POST /v1/chat/completions HTTP/1.1"));
                let length = headers
                    .lines()
                    .find_map(|line| {
                        let (k, v) = line.split_once(':')?;
                        k.eq_ignore_ascii_case("content-length")
                            .then(|| v.trim().parse::<usize>().ok())
                            .flatten()
                    })
                    .expect("exact request content length");
                if collected.len() >= at + 4 + length {
                    assert_eq!(
                        digest_bytes(&collected[at + 4..at + 4 + length]),
                        expected_wire_digest
                    );
                    break;
                }
            }
        }
        let head=format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
            response.len()
        );
        socket.write_all(head.as_bytes()).unwrap();
        socket.write_all(&response).unwrap();
        socket.flush().unwrap();
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
    assert_eq!(
        result,
        Ok(RunResult::CompletionProposal("A useful answer".into()))
    );
    inbound.join().unwrap();
    assert!(journal.completed);
    assert_eq!(provider.last_usage().unwrap().input_tokens, 9);
    assert_eq!(provider.last_usage().unwrap().output_tokens, 4);
    // A completed Provider V4 is NOT a confirmed completed Agent Run.
    let after = read_run_readonly(&mut readonly, &schema, run_id).unwrap();
    assert_eq!(after.projection.revision, 4);
    assert_eq!(after.projection.status, "active");
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 1, &batch[..2]).unwrap(),
        JournalObservation::ExactCommitted
    );
    assert_eq!(
        observe_exact_batch(&mut readonly, &schema, run_id, 3, &batch[2..]).unwrap(),
        JournalObservation::ExactCommitted
    );
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
    let positive_digest = digest_bytes(&canonical_bytes(&original_result));
    if retain_model_content {
        let result_ref = expected_ref(&batch[2], "agent-turn-result").unwrap();
        let stored = ordivon_harness_pg::read_cas_object_readonly(
            &mut readonly,
            &schema,
            &result_ref.digest,
            "agent-turn-result",
        )
        .unwrap();
        assert_eq!(canonical_bytes(&stored), canonical_bytes(&original_result));
        assert_eq!(result_ref.digest, positive_digest);
    } else {
        // A true SELECT-only consumer proves the result object was never
        // committed, rather than trusting absent event references alone.
        assert!(batch[2]
            .referenced_objects
            .iter()
            .all(|ref_| ref_.kind != "agent-turn-result"));
        let sql = format!("SELECT count(*) FROM {schema}.objects WHERE digest=$1");
        let count: i64 = readonly
            .query_one(&sql, &[&positive_digest])
            .unwrap()
            .get(0);
        assert_eq!(count, 0, "private model content entered original PG CAS");
    }
    let observed = inspect_pg_provider_head(&mut readonly, &schema, run_id, model)
        .unwrap()
        .unwrap();
    assert_eq!(observed.status(), ProviderStatus::Completed);
    assert_eq!(
        observed.recovery_posture(),
        RecoveryPosture::ReadCommittedResult
    );
    assert_eq!(
        observed.record_digest(),
        text(&native, "expectedRecordDigest")
    );
    assert_eq!(observed.result_digest(), Some(positive_digest.as_str()));
    assert!(journal.base.unknown_lease.is_none());
    // Intentional consumer negative: after the original Run advanced from
    // revision 1 to 4, the same old source cannot issue another Provider send.
    assert!(journal.prepare_provider(1).is_err());
    // Independent transactional privacy falsifier: the model has returned
    // good positive HTTP content. A DIFFERENT private result object must not
    // survive when the PG Event is rejected because the original Run advanced
    // from rev3 to rev4 (even if the actor now has a valid rev4 lease).
    // This specifically catches R30's old two-transaction CAS-before-Event
    // leak, which could leave an orphaned private answer after a stale lease.
    let rejected_call_id = format!("model-call:aborted-staged-{source_case}");
    let rejected = author_no_tool_turn_result(
        &rejected_call_id,
        model.requested_model_id,
        &ModelDecision::ProposeCompletion("A useful answer".into()),
        provider.last_wire_observation(),
    )
    .unwrap();
    let rejected_ref = StoredRef {
        digest: digest_bytes(&canonical_bytes(&rejected)),
        kind: "agent-turn-result".to_owned(),
        byte_length: i64::try_from(canonical_bytes(&rejected).len()).unwrap(),
    };
    let mut rejected_event = batch[2].clone();
    rejected_event.event_id = format!("event:aborted-staged-{source_case}");
    rejected_event.recorded_at_ms = 1040;
    rejected_event.referenced_objects.push(rejected_ref.clone());
    let mut denied_db = Client::connect(&writer_dsn, NoTls).unwrap();
    let newer_lease = acquire_run_lease(
        &mut denied_db,
        &schema,
        run_id,
        "test:aborted-staged-cas",
        30_000,
        1039,
        Some(4),
    )
    .unwrap();
    let failed = append_events_with_provider_cas(
        &mut denied_db,
        &schema,
        run_id,
        ProviderEventBatch {
            events: &[rejected_event],
            staged: &[ProviderStagedCas {
                kind: ProviderCasKind::AgentTurnResult,
                document: &rejected,
                first_seen_at_ms: 1040,
            }],
        },
        3,
        &newer_lease,
        1040,
    );
    assert!(
        matches!(failed, Err(WriteError::Revision)),
        "stale source PG revision must abort the entire CAS+Event TX: {failed:?}"
    );
    // Verify through a fresh read-only connection that the entire private
    // Result CAS was rolled back: checking Event absence alone is not enough.
    let rollback_sql = format!("SELECT count(*) FROM {schema}.objects WHERE digest=$1");
    let post_rollback: i64 = readonly
        .query_one(&rollback_sql, &[&rejected_ref.digest])
        .unwrap()
        .get(0);
    assert_eq!(
        post_rollback, 0,
        "rejected Event left private AgentTurnResult orphan CAS"
    );
    assert_eq!(
        read_run_readonly(&mut readonly, &schema, run_id)
            .unwrap()
            .projection
            .revision,
        4
    );
    // Source-budget falsifier: the original Run Contract now has
    // maxModelCalls=1,maxModelRetries=0 and one durable DISPATCHING.
    // The existing valid rev4 lease is NOT enough to authorize another
    // physical Provider dispatch. This must fail before any new model send.
    let mut extra_dispatch = batch[1].clone();
    extra_dispatch.event_id = format!("event:excess-provider-dispatch-{source_case}");
    extra_dispatch.recorded_at_ms = 1041;
    let exceeds = append_events(
        &mut denied_db,
        &schema,
        run_id,
        &[extra_dispatch.clone()],
        4,
        &newer_lease,
        1041,
    );
    assert!(
        matches!(
            exceeds,
            Err(WriteError::Invalid(
                "source Provider dispatch budget exhausted"
            ))
        ),
        "source dispatch cap was not enforced by original PG Run lock: {exceeds:?}"
    );
    let evt_sql = format!("SELECT count(*) FROM {schema}.run_events WHERE event_id=$1");
    let denied_count: i64 = readonly
        .query_one(&evt_sql, &[&extra_dispatch.event_id])
        .unwrap()
        .get(0);
    assert_eq!(
        denied_count, 0,
        "rejected budget overrun became a durable Event"
    );
    assert_eq!(
        read_run_readonly(&mut readonly, &schema, run_id)
            .unwrap()
            .projection
            .revision,
        4
    );
    // Source exact replay of an already completed event must remain legal
    // even after this finite budget is exhausted; no second physical send.
    assert!(matches!(
        append_events(
            &mut denied_db,
            &schema,
            run_id,
            &batch[2..],
            3,
            &newer_lease,
            1042,
        ),
        Ok(Admission::Existing)
    ));
    println!("PG18_SOURCE_PROVIDER_DISPATCH_BUDGET_GATE_PASS");
    println!("PG18_REJECTED_COMPLETED_EVENT_NO_PRIVATE_CAS_ORPHAN_PASS");
    if retain_model_content {
        println!("PG18_NATIVE_RUST_POSITIVE_HTTP_PYTHON_SOURCE_V4_COMPLETED_READBACK_PASS");
    } else {
        println!("PG18_NATIVE_RUST_POSITIVE_HTTP_PRIVACY_REDACTED_COMPLETED_PASS");
    }
}
#[test]
#[ignore = "real disposable PG18 source + native positive Provider V4"]
fn native_rust_pg_v4_completed_after_real_local_http_positive() {
    verify_native_rust_pg_v4_completed_case("rust_native_provider_completed", true);
}
#[test]
#[ignore = "real disposable PG18 source + privacy-redacted native Provider V4"]
fn native_rust_pg_v4_completed_privacy_redacted() {
    verify_native_rust_pg_v4_completed_case("rust_native_provider_completed_redacted", false);
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

    let batch = source_event_batch(&native);

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

    // The same Journal can never misinterpret caller input or an uncertain
    // Tool physical effect as an UNKNOWN external Provider call.
    for wrong in [PauseCause::NeedsInput, PauseCause::ToolUnknown] {
        assert!(journal.record_pause(1, wrong).is_err());
        assert!(!journal.prepared);
        assert!(journal.unknown_lease.is_none());
    }

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
    // TOCTOU falsifier: the old source-verified initial Run snapshot alone
    // is NOT a dispatch grant. After the Run advanced to revision 4 and the
    // Provider head became UNKNOWN, a fresh Loop using this STALE snapshot
    // must never reach Provider::turn. Existing PG revision/lease reject it.
    let mut stale_journal = SourcePgUnknownJournal {
        writer_dsn: writer_dsn.clone(),
        schema: schema.clone(),
        run_id: run_id.to_owned(),
        batch: batch.clone(),
        python_first_source: journal.python_first_source.clone(),
        python_failure_oracle: journal.python_failure_oracle.clone(),
        prepared: false,
        dispatch_digest: None,
        unknown_lease: None,
    };
    let mut never_send = RefuseAnyProviderSend;
    let stale = NativeAgentLoop::new_provider_only(
        &mut never_send,
        &mut stale_journal,
        &mut no_effect,
        &verified,
        1,
    )
    .unwrap()
    .run();
    assert!(
        matches!(stale, Err(RunFault::Journal(_))),
        "A stale but correctly digested source Run must not authorize new Provider transport"
    );
    assert!(!stale_journal.prepared);
    assert_eq!(
        read_run_readonly(&mut readonly, &schema, run_id)
            .unwrap()
            .projection
            .revision,
        4
    );
    println!("PG18_RUST_WRITER_PYTHON_PROVIDER_V4_UNKNOWN_READBACK_EXACT_PASS");
}
