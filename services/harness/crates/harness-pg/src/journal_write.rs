//! Atomic Journal admission in the existing Python PostgreSQL v1 schema.
//! A committed Event is not a Provider/Tool effect or semantic success.
//! Lost commit responses are UNKNOWN until exact Event-ID reconciliation.

use super::lease::{check_schema, LeaseError, RunLease};
use super::provider_cas::{prepare_provider_cas, ProviderStagedCas};
use super::run_create::store_cas;
use super::{
    contract_semantics, decode_cas, run_projection, transition, valid_schema, ReadError,
    RunProjection, CONTRACT_KIND,
};
use ordivon_harness_core::provider_head::{
    inspect_v4, provider_event_clears_head, validate_provider_failure_source,
    ProviderFailureSourceView, ProviderStatus,
};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalError};
use postgres::{Client, Transaction};
use std::{collections::BTreeSet, fmt};

const EVENT_PAYLOAD_KIND: &str = "ordivon.harness-run-event-payload";
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Admission {
    Created,
    Existing,
}
#[derive(Debug)]
pub enum WriteError {
    Db(postgres::Error),
    Lease(LeaseError),
    Read(ReadError),
    Codec(CanonicalError),
    Invalid(&'static str),
    Conflict(String),
    MissingRun(String),
    Revision,
    Terminal,
    Fenced,
    Overflow,
}
impl fmt::Display for WriteError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Db(e) => write!(f, "PostgreSQL commit/result uncertain: {e}"),
            Self::Lease(e) => write!(f, "Lease schema error: {e}"),
            Self::Read(e) => write!(f, "Readback validation: {e}"),
            Self::Codec(e) => write!(f, "Canonical error: {e}"),
            Self::Invalid(e) => write!(f, "Invalid event: {e}"),
            Self::Conflict(e) => write!(f, "Conflicting Event identity/contents: {e}"),
            Self::MissingRun(e) => write!(f, "Run not found: {e}"),
            Self::Revision => write!(f, "Run revision conflict"),
            Self::Terminal => write!(f, "Terminal Run/Event"),
            Self::Fenced => write!(f, "Lease expired/superseded"),
            Self::Overflow => write!(f, "Journal integer overflow"),
        }
    }
}
impl std::error::Error for WriteError {}
impl From<postgres::Error> for WriteError {
    fn from(e: postgres::Error) -> Self {
        Self::Db(e)
    }
}
impl From<LeaseError> for WriteError {
    fn from(e: LeaseError) -> Self {
        Self::Lease(e)
    }
}
impl From<ReadError> for WriteError {
    fn from(e: ReadError) -> Self {
        Self::Read(e)
    }
}
impl From<CanonicalError> for WriteError {
    fn from(e: CanonicalError) -> Self {
        Self::Codec(e)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StoredRef {
    pub digest: String,
    pub kind: String,
    pub byte_length: i64,
}
#[derive(Debug, Clone)]
pub struct EventWrite {
    pub event_id: String,
    pub event_kind: String,
    pub data: CanonicalDocument,
    pub recorded_at_ms: i64,
    pub caused_by_event_id: Option<String>,
    pub referenced_objects: Vec<StoredRef>,
}
/// One source-owned atomic Provider Journal batch. The staged CAS documents
/// must be referenced by the exact attached Event, not a separate datastore.
pub struct ProviderEventBatch<'a> {
    pub events: &'a [EventWrite],
    pub staged: &'a [ProviderStagedCas<'a>],
}
struct Prepared<'a> {
    source: &'a EventWrite,
    digest: String,
    bytes: Vec<u8>,
}

fn allowed(kind: &str) -> bool {
    matches!(
        kind,
        "harness.snapshot-recorded"
            | "harness.working-set-recorded"
            | "harness.provider-call-claimed"
            | "harness.provider-call-superseded"
            | "harness.provider-call-dispatching"
            | "harness.provider-call-completed"
            | "harness.provider-call-failed"
            | "harness.provider-call-unknown"
            | "harness.tool-step-prepared"
            | "harness.tool-step-recorded"
            | "harness.tool-step-unknown"
            | "harness.tool-step-reconciled"
            | "harness.run-paused"
            | "harness.trace-recorded"
            | "harness.run-stopped"
            | "harness.run-failed"
            | "harness.run-completed"
    )
}
fn id_valid(id: &str) -> bool {
    id.starts_with("event:")
        && id.len() <= 500
        && id.trim_matches(|c: char| c.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&c))
            == id
}
fn payload(e: &EventWrite) -> Result<Vec<u8>, WriteError> {
    if e.data.object_len().is_none() {
        return Err(WriteError::Invalid("data not object"));
    }
    let doc = CanonicalDocument::object(vec![
        (
            "schemaVersion".into(),
            CanonicalDocument::integer_from_decimal("1")?,
        ),
        ("kind".into(), CanonicalDocument::string(EVENT_PAYLOAD_KIND)),
        ("eventKind".into(), CanonicalDocument::string(&e.event_kind)),
        ("data".into(), e.data.clone()),
    ])?;
    Ok(canonical_bytes(&doc))
}
fn edges(p: &Prepared<'_>) -> BTreeSet<(String, String)> {
    let mut refs = BTreeSet::from([(p.digest.clone(), "payload".to_owned())]);
    refs.extend(
        p.source
            .referenced_objects
            .iter()
            .map(|r| (r.digest.clone(), "reference".to_owned())),
    );
    refs
}
fn cas_require(tx: &mut Transaction<'_>, d: &str, kind: &str, len: i64) -> Result<(), WriteError> {
    let row = tx
        .query_opt(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&d],
        )?
        .ok_or_else(|| WriteError::Conflict(format!("missing CAS {d}")))?;
    let actual_kind: String = row.get("kind");
    let actual_length: i64 = row.get("byte_length");
    if actual_kind != kind || actual_length != len {
        return Err(WriteError::Conflict(format!("CAS metadata {d}")));
    }
    decode_cas(
        d,
        kind,
        &actual_kind,
        actual_length,
        &row.get::<_, Vec<u8>>("content"),
    )?;
    Ok(())
}
/// Reuse the Reader's ONE versioned Contract semantic validator under the
/// SAME locked Run transaction. CAS hashes and lease identity alone are not
/// proof that a Python-invalid Contract can be extended by the Rust Writer.
/// O(1) source Contract lookup; never scan/re-implement the Journal parser.
fn require_current_run_contract(
    tx: &mut Transaction<'_>,
    current: &RunProjection,
) -> Result<CanonicalDocument, WriteError> {
    if current.contract_digest != current.contract_object_digest {
        return Err(WriteError::Read(ReadError::Corruption(
            "Run Contract digest vs stored object digest differs".into(),
        )));
    }
    let row = tx
        .query_opt(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&current.contract_object_digest],
        )?
        .ok_or_else(|| {
            WriteError::Read(ReadError::Corruption("Run Contract object missing".into()))
        })?;
    let contract = decode_cas(
        &current.contract_object_digest,
        CONTRACT_KIND,
        &row.get::<_, String>("kind"),
        row.get::<_, i64>("byte_length"),
        &row.get::<_, Vec<u8>>("content"),
    )?;
    contract_semantics::validate_contract(&contract)?;
    for (key, expected) in [
        ("harnessRunId", current.harness_run_id.as_str()),
        ("callerId", current.caller_id.as_str()),
        ("callerRunRef", current.caller_run_ref.as_str()),
    ] {
        if contract.field(key).and_then(|value| value.as_str()) != Some(expected) {
            return Err(WriteError::Read(ReadError::Corruption(format!(
                "Run Contract vs projection differs at {key}"
            ))));
        }
    }
    Ok(contract)
}

/// A source-defined per-Run cap on physical Provider dispatch admission.
/// The legacy Python cognitive loop counts successful model calls plus
/// globally limited safe retries; a PG dispatch edge is a conservative
/// physical attempt. Do not treat reported token usage or claimed status as
/// permission to spend, and never permit a new dispatch after this cap.
fn require_dispatch_budget(
    tx: &mut Transaction<'_>,
    run: &str,
    contract: &CanonicalDocument,
    new_events: &[EventWrite],
) -> Result<(), WriteError> {
    let extra = i64::try_from(
        new_events
            .iter()
            .filter(|e| e.event_kind == "harness.provider-call-dispatching")
            .count(),
    )
    .map_err(|_| WriteError::Overflow)?;
    if extra == 0 {
        return Ok(());
    }
    let budget = contract
        .field("budget")
        .ok_or(WriteError::Invalid("source budget absent"))?;
    let model_calls = budget.field("maxModelCalls").and_then(|v| v.integer_text());
    let retries = budget
        .field("maxModelRetries")
        .and_then(|v| v.integer_text());
    // Historical v1 contracts may predate this budget, but a current v2
    // source Contract cannot physically dispatch without both exact limits.
    let (Some(calls), Some(retries)) = (model_calls, retries) else {
        return if contract
            .field("schemaVersion")
            .and_then(|v| v.integer_text())
            == Some("2")
        {
            Err(WriteError::Invalid("current Run Provider budget absent"))
        } else {
            Ok(())
        };
    };
    // Arbitrarily large legitimate integers mean the representable
    // PostgreSQL event count cannot exhaust this budget. Invalid negative
    // or noninteger source values fail closed for a model dispatch.
    let valid = |txt: &str| !txt.is_empty() && txt.bytes().all(|b| b.is_ascii_digit());
    if !valid(calls) || !valid(retries) {
        return Err(WriteError::Invalid("source model budget invalid"));
    }
    let limit = match (calls.parse::<i64>(), retries.parse::<i64>()) {
        (Ok(a), Ok(b)) => a.saturating_add(b),
        _ => i64::MAX,
    };
    let used:i64=tx.query_one(
        "SELECT count(*) FROM run_events WHERE harness_run_id=$1          AND event_kind='harness.provider-call-dispatching'",
        &[&run],
    )?.get(0);
    let requested = used.checked_add(extra).ok_or(WriteError::Overflow)?;
    if requested > limit {
        return Err(WriteError::Invalid(
            "source Provider dispatch budget exhausted",
        ));
    }
    Ok(())
}

/// Enforce the source Run's immutable content-retention authority inside
/// the same transaction that stores CAS and appends the Provider Event.
/// The caller's proposed journal adapter is NOT a privacy authority.
///
/// We check staged documents, Event edges and the Provider Event's direct
/// resultObjectDigest field. This prevents both staged and pre-existing
/// full-result CAS objects from being referenced by a metadata-only Run.
/// Exact historical replays are reconciled before this check: replay does not
/// introduce another physical or privacy effect.
fn require_source_result_retention(
    contract: &CanonicalDocument,
    events: &[EventWrite],
    staged: &[ProviderStagedCas<'_>],
) -> Result<(), WriteError> {
    let allowed = contract
        .field("privacy")
        .and_then(|p| p.field("allowModelContent"))
        .and_then(|v| v.as_bool())
        .ok_or(WriteError::Invalid("source Contract model privacy absent"))?;
    if allowed {
        return Ok(());
    }
    if staged
        .iter()
        .any(|s| s.kind == super::provider_cas::ProviderCasKind::AgentTurnResult)
        || events.iter().any(|event| {
            event
                .referenced_objects
                .iter()
                .any(|r| r.kind == "agent-turn-result")
                || event
                    .data
                    .field("resultObjectDigest")
                    .is_some_and(|v| !v.is_null())
        })
    {
        return Err(WriteError::Invalid(
            "model content forbidden by source Contract",
        ));
    }
    Ok(())
}

/// Read the nearest current Provider transition under the same locked PG Run.
/// In-batch events dominate the retained journal; a clearing event is also
/// a boundary. This is shared by DISPATCHING and COMPLETED admission.
fn current_provider_predecessor(
    tx: &mut Transaction<'_>,
    run: &str,
    events: &[EventWrite],
    position: usize,
) -> Result<(String, Option<String>), WriteError> {
    let recent = events[..position].iter().rev().find(|e| {
        e.event_kind.starts_with("harness.provider-call-")
            || provider_event_clears_head(&e.event_kind)
    });
    if let Some(recent) = recent {
        let record = recent
            .referenced_objects
            .iter()
            .find(|r| r.kind == "harness-provider-call-record");
        return Ok((recent.event_kind.clone(), record.map(|r| r.digest.clone())));
    }
    let observed = tx.query_opt(
        "SELECT event_id,event_kind FROM run_events \
         WHERE harness_run_id=$1 AND ( \
         event_kind LIKE 'harness.provider-call-%' OR \
         event_kind IN ('harness.snapshot-recorded',\
         'harness.working-set-recorded','harness.run-paused',\
         'harness.tool-step-prepared','harness.run-stopped',\
         'harness.run-completed','harness.run-failed')) \
         ORDER BY run_revision DESC LIMIT 1",
        &[&run],
    )?;
    if let Some(row) = observed {
        let id: String = row.get("event_id");
        let kind: String = row.get("event_kind");
        let reference = tx.query_opt(
            "SELECT r.digest FROM run_object_refs r \
             JOIN objects o ON o.digest=r.digest \
             WHERE r.event_id=$1 AND o.kind='harness-provider-call-record' \
             LIMIT 1",
            &[&id],
        )?;
        Ok((kind, reference.map(|r| r.get::<_, String>("digest"))))
    } else {
        Ok((String::new(), None))
    }
}

/// A valid lease is not a license to change Provider identity or fabricate
/// a DISPATCHING event. Authoritative Rust V4 admissions must use the original
/// locked Run Contract and current same-attempt CLAIMED record, before HTTP.
fn require_source_provider_admission(
    tx: &mut Transaction<'_>,
    run: &str,
    contract: &CanonicalDocument,
    events: &[EventWrite],
) -> Result<(), WriteError> {
    for (position, event) in events.iter().enumerate() {
        let expected = match event.event_kind.as_str() {
            "harness.provider-call-claimed" => ProviderStatus::Claimed,
            "harness.provider-call-dispatching" => ProviderStatus::Dispatching,
            _ => continue,
        };
        let mut records = event
            .referenced_objects
            .iter()
            .filter(|r| r.kind == "harness-provider-call-record");
        let record_ref = records
            .next()
            .ok_or(WriteError::Invalid("Provider admission missing V4 record"))?;
        if records.next().is_some()
            || event
                .data
                .field("providerCallRecordDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
            || event
                .data
                .field("providerCallRecordObjectDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
        {
            return Err(WriteError::Invalid("Provider admission CAS/Event mismatch"));
        }
        let row = tx.query_one(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&record_ref.digest],
        )?;
        let doc = decode_cas(
            &record_ref.digest,
            "harness-provider-call-record",
            &row.get::<_, String>("kind"),
            row.get::<_, i64>("byte_length"),
            &row.get::<_, Vec<u8>>("content"),
        )?;
        // Old V3 history is readable through the original Source Store,
        // but newly admitted physical dispatch must have strict V4 identity.
        if doc.field("schemaVersion").and_then(|v| v.integer_text()) != Some("4") {
            return Err(WriteError::Invalid("native Provider admission requires V4"));
        }
        let parsed = inspect_v4(&doc)
            .map_err(|_| WriteError::Invalid("Provider admission invalid V4 source"))?;
        if parsed.status != expected
            || parsed.canonical_digest != record_ref.digest
            || doc.field("harnessRunId").and_then(|v| v.as_str()) != Some(run)
            || doc.field("adapterId").and_then(|v| v.as_str())
                != contract.field("adapterId").and_then(|v| v.as_str())
            || doc.field("requestedModelId").and_then(|v| v.as_str())
                != contract.field("requestedModelId").and_then(|v| v.as_str())
            || doc.field("recordedAtMs").and_then(|v| v.integer_text())
                != Some(event.recorded_at_ms.to_string().as_str())
        {
            return Err(WriteError::Invalid(
                "Provider admission source identity/status mismatch",
            ));
        }
        for key in ["stateObjectDigest", "requestObjectDigest"] {
            if event.data.field(key).and_then(|v| v.as_str())
                != doc.field(key).and_then(|v| v.as_str())
            {
                return Err(WriteError::Invalid(
                    "Provider admission source data mismatch",
                ));
            }
        }
        if expected == ProviderStatus::Dispatching {
            let previous_digest = parsed
                .previous_record_digest
                .as_deref()
                .ok_or(WriteError::Invalid("Provider dispatch predecessor absent"))?;
            let (kind, prior_digest) = current_provider_predecessor(tx, run, events, position)?;
            if kind != "harness.provider-call-claimed"
                || prior_digest.as_deref() != Some(previous_digest)
            {
                return Err(WriteError::Invalid(
                    "Provider dispatch not linked to current durable claim",
                ));
            }
            let previous_row = tx.query_one(
                "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
                &[&previous_digest],
            )?;
            let previous_doc = decode_cas(
                previous_digest,
                "harness-provider-call-record",
                &previous_row.get::<_, String>("kind"),
                previous_row.get::<_, i64>("byte_length"),
                &previous_row.get::<_, Vec<u8>>("content"),
            )?;
            let previous = inspect_v4(&previous_doc)
                .map_err(|_| WriteError::Invalid("Provider claim invalid V4 source"))?;
            if previous.status != ProviderStatus::Claimed
                || !previous.same_attempt_identity(&parsed)
            {
                return Err(WriteError::Invalid(
                    "Provider dispatch predecessor attempt identity mismatch",
                ));
            }
        }
    }
    Ok(())
}

/// UNKNOWN/FAILED are durable recovery claims, not arbitrary failure labels.
/// Check the same current V4 attempt and typed FailureReceipt under the
/// original PG Run lock before permitting an ambiguous result to be recorded.
/// This does not prove the external Provider's actual billing/effect.
fn require_source_provider_failure(
    tx: &mut Transaction<'_>,
    run: &str,
    contract: &CanonicalDocument,
    events: &[EventWrite],
) -> Result<(), WriteError> {
    for (position, event) in events.iter().enumerate() {
        let expected = match event.event_kind.as_str() {
            "harness.provider-call-unknown" => ProviderStatus::Unknown,
            "harness.provider-call-failed" => ProviderStatus::Failed,
            _ => continue,
        };
        let mut records = event
            .referenced_objects
            .iter()
            .filter(|r| r.kind == "harness-provider-call-record");
        let record_ref = records
            .next()
            .ok_or(WriteError::Invalid("Provider failure missing V4 record"))?;
        if records.next().is_some()
            || event
                .data
                .field("providerCallRecordDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
            || event
                .data
                .field("providerCallRecordObjectDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
        {
            return Err(WriteError::Invalid("Provider failure CAS/Event mismatch"));
        }
        let row = tx.query_one(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&record_ref.digest],
        )?;
        let doc = decode_cas(
            &record_ref.digest,
            "harness-provider-call-record",
            &row.get::<_, String>("kind"),
            row.get::<_, i64>("byte_length"),
            &row.get::<_, Vec<u8>>("content"),
        )?;
        let parsed = inspect_v4(&doc)
            .map_err(|_| WriteError::Invalid("Provider failure invalid V4 source"))?;
        if parsed.status != expected
            || parsed.canonical_digest != record_ref.digest
            || doc.field("harnessRunId").and_then(|v| v.as_str()) != Some(run)
            || doc.field("adapterId").and_then(|v| v.as_str())
                != contract.field("adapterId").and_then(|v| v.as_str())
            || doc.field("requestedModelId").and_then(|v| v.as_str())
                != contract.field("requestedModelId").and_then(|v| v.as_str())
            || doc.field("recordedAtMs").and_then(|v| v.integer_text())
                != Some(event.recorded_at_ms.to_string().as_str())
        {
            return Err(WriteError::Invalid(
                "Provider failure source identity/status mismatch",
            ));
        }
        for key in [
            "stateObjectDigest",
            "requestObjectDigest",
            "failureObjectDigest",
        ] {
            if event.data.field(key).and_then(|v| v.as_str())
                != doc.field(key).and_then(|v| v.as_str())
            {
                return Err(WriteError::Invalid(
                    "Provider failure event/source data mismatch",
                ));
            }
        }
        let mut receipts = event
            .referenced_objects
            .iter()
            .filter(|r| r.kind == "harness-provider-call-failure");
        let receipt_ref = receipts.next().ok_or(WriteError::Invalid(
            "Provider failure missing referenced receipt",
        ))?;
        if receipts.next().is_some()
            || doc.field("failureObjectDigest").and_then(|v| v.as_str())
                != Some(receipt_ref.digest.as_str())
            || parsed.failure_digest.as_deref() != Some(receipt_ref.digest.as_str())
        {
            return Err(WriteError::Invalid(
                "Provider failure receipt binding mismatch",
            ));
        }
        let receipt_row = tx.query_one(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&receipt_ref.digest],
        )?;
        let receipt = decode_cas(
            &receipt_ref.digest,
            "harness-provider-call-failure",
            &receipt_row.get::<_, String>("kind"),
            receipt_row.get::<_, i64>("byte_length"),
            &receipt_row.get::<_, Vec<u8>>("content"),
        )?;
        let view = ProviderFailureSourceView {
            field_count: receipt.object_len(),
            version_one: receipt
                .field("schemaVersion")
                .and_then(|v| v.integer_text())
                == Some("1"),
            kind: receipt.field("kind").and_then(|v| v.as_str()),
            detail_source_valid: receipt
                .field("detail")
                .and_then(|v| v.as_str())
                .is_some_and(|v| ordivon_harness_core::valid_trimmed(v, 2048)),
            provider_call_id: receipt.field("providerCallId").and_then(|v| v.as_str()),
            request_digest: receipt.field("requestDigest").and_then(|v| v.as_str()),
            provider_request_digest: receipt
                .field("providerRequestDigest")
                .and_then(|v| v.as_str()),
            failure_code: receipt.field("failureCode").and_then(|v| v.as_str()),
            dispatch_safety: receipt.field("dispatchSafety").and_then(|v| v.as_str()),
        };
        validate_provider_failure_source(view, &receipt_ref.digest, &parsed)
            .map_err(|_| WriteError::Invalid("Provider failure invalid source receipt"))?;
        let previous_digest = parsed
            .previous_record_digest
            .as_deref()
            .ok_or(WriteError::Invalid("Provider failure predecessor absent"))?;
        let (kind, prior_digest) = current_provider_predecessor(tx, run, events, position)?;
        let predecessor_allowed = kind == "harness.provider-call-dispatching"
            || (expected == ProviderStatus::Failed && kind == "harness.provider-call-claimed");
        if !predecessor_allowed || prior_digest.as_deref() != Some(previous_digest) {
            return Err(WriteError::Invalid(
                "Provider failure not linked to current durable attempt",
            ));
        }
        let prior_row = tx.query_one(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&previous_digest],
        )?;
        let prior_doc = decode_cas(
            previous_digest,
            "harness-provider-call-record",
            &prior_row.get::<_, String>("kind"),
            prior_row.get::<_, i64>("byte_length"),
            &prior_row.get::<_, Vec<u8>>("content"),
        )?;
        let prior = inspect_v4(&prior_doc)
            .map_err(|_| WriteError::Invalid("Provider failure predecessor invalid V4"))?;
        if !prior.same_attempt_identity(&parsed)
            || !matches!(
                prior.status,
                ProviderStatus::Claimed | ProviderStatus::Dispatching
            )
            || (expected == ProviderStatus::Unknown && prior.status != ProviderStatus::Dispatching)
        {
            return Err(WriteError::Invalid(
                "Provider failure predecessor attempt identity mismatch",
            ));
        }
    }
    Ok(())
}

/// The authoritative original PG Run cannot acquire a Provider COMPLETED
/// fact from a bare caller-chosen Event label. Its source CAS record must
/// actually describe this Run, model, status and result. Reuse the *same* V4
/// parser used by the native Provider author and read-only recovery consumer,
/// now in harness-core. Do not invent a second Provider V4 interpretation.
fn require_source_provider_completion(
    tx: &mut Transaction<'_>,
    run: &str,
    contract: &CanonicalDocument,
    events: &[EventWrite],
) -> Result<(), WriteError> {
    for event in events {
        if event.event_kind != "harness.provider-call-completed" {
            continue;
        }
        let mut records = event
            .referenced_objects
            .iter()
            .filter(|r| r.kind == "harness-provider-call-record");
        let record_ref = records.next().ok_or(WriteError::Invalid(
            "Provider completed missing bound record",
        ))?;
        if records.next().is_some()
            || event
                .data
                .field("providerCallRecordDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
            || event
                .data
                .field("providerCallRecordObjectDigest")
                .and_then(|v| v.as_str())
                != Some(record_ref.digest.as_str())
        {
            return Err(WriteError::Invalid(
                "Provider completed record/event mismatch",
            ));
        }
        let row = tx.query_one(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&record_ref.digest],
        )?;
        let doc = decode_cas(
            &record_ref.digest,
            "harness-provider-call-record",
            &row.get::<_, String>("kind"),
            row.get::<_, i64>("byte_length"),
            &row.get::<_, Vec<u8>>("content"),
        )?;
        if doc.field("harnessRunId").and_then(|v| v.as_str()) != Some(run)
            || doc.field("status").and_then(|v| v.as_str()) != Some("completed")
            || doc.field("adapterId").and_then(|v| v.as_str())
                != contract.field("adapterId").and_then(|v| v.as_str())
            || doc.field("requestedModelId").and_then(|v| v.as_str())
                != contract.field("requestedModelId").and_then(|v| v.as_str())
        {
            return Err(WriteError::Invalid(
                "Provider completed source identity/status mismatch",
            ));
        }
        if doc.field("schemaVersion").and_then(|v| v.integer_text()) == Some("4") {
            let parsed = inspect_v4(&doc)
                .map_err(|_| WriteError::Invalid("Provider completed invalid V4 source"))?;
            if parsed.status != ProviderStatus::Completed
                || parsed.canonical_digest != record_ref.digest
                || doc.field("recordedAtMs").and_then(|v| v.integer_text())
                    != Some(event.recorded_at_ms.to_string().as_str())
            {
                return Err(WriteError::Invalid(
                    "Provider completed V4 status/time mismatch",
                ));
            }
            let event_result = event
                .data
                .field("resultObjectDigest")
                .and_then(|v| v.as_str());
            if event_result != parsed.result_object_digest.as_deref() {
                return Err(WriteError::Invalid(
                    "Provider completed result binding mismatch",
                ));
            }
            if let Some(digest) = parsed.result_object_digest.as_deref() {
                if !event
                    .referenced_objects
                    .iter()
                    .any(|r| r.kind == "agent-turn-result" && r.digest == digest)
                {
                    return Err(WriteError::Invalid(
                        "Provider completed Result CAS edge absent",
                    ));
                }
            }
            // A mere historical DISPATCHING somewhere in the Run does not
            // authorize a completed result. The predecessor must be the
            // current head since the last source-defined clearing event,
            // and MUST be the same ProviderCall/turn/request/generation.
            // Use the same Core identity + head-clearing semantics as the
            // independent read-only Provider recovery consumer.
            let previous_digest = parsed
                .previous_record_digest
                .as_deref()
                .ok_or(WriteError::Invalid("Provider completed predecessor absent"))?;
            let position = events
                .iter()
                .position(|e| e.event_id == event.event_id)
                .ok_or(WriteError::Invalid(
                    "Provider completion source event absent",
                ))?;
            let (kind, prior_digest) = current_provider_predecessor(tx, run, events, position)?;
            if kind != "harness.provider-call-dispatching"
                || prior_digest.as_deref() != Some(previous_digest)
            {
                return Err(WriteError::Invalid(
                    "Provider completed not linked to current durable dispatch",
                ));
            }
            let previous_row = tx.query_one(
                "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
                &[&previous_digest],
            )?;
            let previous_doc = decode_cas(
                previous_digest,
                "harness-provider-call-record",
                &previous_row.get::<_, String>("kind"),
                previous_row.get::<_, i64>("byte_length"),
                &previous_row.get::<_, Vec<u8>>("content"),
            )?;
            let previous = inspect_v4(&previous_doc)
                .map_err(|_| WriteError::Invalid("Provider predecessor invalid V4"))?;
            if previous.status != ProviderStatus::Dispatching
                || !previous.same_attempt_identity(&parsed)
            {
                return Err(WriteError::Invalid(
                    "Provider completed predecessor attempt identity mismatch",
                ));
            }
        }
    }
    Ok(())
}

fn exact(
    tx: &mut Transaction<'_>,
    run: &str,
    rev: i64,
    p: &Prepared<'_>,
) -> Result<(), WriteError> {
    let e = p.source;
    let row=tx.query_opt(
        "SELECT harness_run_id,run_revision,event_kind,payload_digest,caused_by_event_id,recorded_at_ms \
         FROM run_events WHERE event_id=$1",&[&e.event_id])?
        .ok_or_else(||WriteError::Conflict(format!("missing replay {}",e.event_id)))?;
    if (
        row.get::<_, String>("harness_run_id"),
        row.get::<_, i64>("run_revision"),
        row.get::<_, String>("event_kind"),
        row.get::<_, String>("payload_digest"),
        row.get::<_, Option<String>>("caused_by_event_id"),
        row.get::<_, i64>("recorded_at_ms"),
    ) != (
        run.to_owned(),
        rev,
        e.event_kind.clone(),
        p.digest.clone(),
        e.caused_by_event_id.clone(),
        e.recorded_at_ms,
    ) {
        return Err(WriteError::Conflict(format!(
            "altered replay {}",
            e.event_id
        )));
    }
    let rows = tx.query(
        "SELECT digest,role FROM run_object_refs WHERE event_id=$1",
        &[&e.event_id],
    )?;
    let observed: BTreeSet<_> = rows
        .iter()
        .map(|r| (r.get::<_, String>("digest"), r.get::<_, String>("role")))
        .collect();
    if observed != edges(p) {
        return Err(WriteError::Conflict(format!("replay edges {}", e.event_id)));
    }
    Ok(())
}
fn require_lease(
    tx: &mut Transaction<'_>,
    run: &str,
    revision: i64,
    lease: &RunLease,
    at: i64,
) -> Result<(), WriteError> {
    if lease.harness_run_id() != run || lease.run_revision() != revision {
        return Err(WriteError::Fenced);
    }
    let row = tx
        .query_opt(
            "SELECT owner_id,lease_revision,run_revision,expires_at_ms FROM run_leases \
         WHERE harness_run_id=$1 FOR UPDATE",
            &[&run],
        )?
        .ok_or(WriteError::Fenced)?;
    if row.get::<_, String>("owner_id") != lease.owner_id()
        || row.get::<_, i64>("lease_revision") != lease.lease_revision()
        || row.get::<_, i64>("run_revision") != lease.run_revision()
        || row.get::<_, i64>("expires_at_ms") != lease.expires_at_ms()
        || lease.expires_at_ms() <= at
    {
        return Err(WriteError::Fenced);
    }
    Ok(())
}

/// One transaction: validate canonical payloads/references, lock Run,
/// idempotently reconcile exact Event IDs, check lease and revision, append
/// Event batch + edges + projection, consume the exact lease. No external effect.
pub fn append_events(
    db: &mut Client,
    schema: &str,
    run: &str,
    events: &[EventWrite],
    expected_revision: i64,
    lease: &RunLease,
    lease_checked_at_ms: i64,
) -> Result<Admission, WriteError> {
    append_events_with_provider_cas(
        db,
        schema,
        run,
        ProviderEventBatch {
            events,
            staged: &[],
        },
        expected_revision,
        lease,
        lease_checked_at_ms,
    )
}

/// Same native Writer, same source PG Lease and Event transaction. Provider
/// result V4 CAS is inserted *inside* the Event transaction: rejected or
/// rolled-back Event cannot leave a private answer orphaned in PG.
pub fn append_events_with_provider_cas(
    db: &mut Client,
    schema: &str,
    run: &str,
    batch: ProviderEventBatch<'_>,
    expected_revision: i64,
    lease: &RunLease,
    lease_checked_at_ms: i64,
) -> Result<Admission, WriteError> {
    let events = batch.events;
    let staged = batch.staged;
    if !valid_schema(schema) {
        return Err(WriteError::Invalid("schema"));
    }
    if events.is_empty() || events.len() > 256 || expected_revision < 1 || lease_checked_at_ms < 0 {
        return Err(WriteError::Invalid("batch/revision/time"));
    }
    let mut ids = BTreeSet::new();
    let mut prepared = Vec::with_capacity(events.len());
    for e in events {
        if !id_valid(&e.event_id)
            || !allowed(&e.event_kind)
            || e.recorded_at_ms < 0
            || !ids.insert(e.event_id.as_str())
        {
            return Err(WriteError::Invalid("id/kind/time/duplicate"));
        }
        let bytes = payload(e)?;
        let digest = digest_bytes(&bytes);
        let refs: BTreeSet<_> = e
            .referenced_objects
            .iter()
            .map(|r| r.digest.as_str())
            .collect();
        // Python's Store deduplicates repeated identical object reference
        // digests when constructing the edge set. Do the same rather than
        // spuriously rejecting a valid legacy event.
        if refs.contains(digest.as_str()) {
            return Err(WriteError::Invalid("reference aliases payload digest"));
        }
        prepared.push(Prepared {
            source: e,
            digest,
            bytes,
        });
    }
    let mut pending = Vec::with_capacity(staged.len());
    if staged.len() > 256 {
        return Err(WriteError::Invalid("too many Provider CAS objects"));
    }
    for spec in staged {
        let (reference, bytes) = prepare_provider_cas(*spec)?;
        if !events
            .iter()
            .any(|event| event.referenced_objects.contains(&reference))
        {
            return Err(WriteError::Invalid(
                "staged Provider CAS lacks exact Event reference",
            ));
        }
        if pending
            .iter()
            .any(|(r, _, _): &(StoredRef, Vec<u8>, i64)| r.digest == reference.digest)
        {
            return Err(WriteError::Invalid("duplicate staged Provider CAS"));
        }
        pending.push((reference, bytes, spec.first_seen_at_ms));
    }
    let mut tx = db.transaction()?;
    check_schema(&mut tx, schema)?;
    for (reference, bytes, first_seen) in &pending {
        store_cas(
            &mut tx,
            &reference.digest,
            &reference.kind,
            bytes,
            *first_seen,
        )?;
    }
    for p in &prepared {
        let n = i64::try_from(p.bytes.len()).map_err(|_| WriteError::Overflow)?;
        tx.execute(
            "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) \
                    VALUES($1,$2,$3,$4,$5) ON CONFLICT(digest) DO NOTHING",
            &[
                &p.digest,
                &EVENT_PAYLOAD_KIND,
                &n,
                &p.bytes,
                &p.source.recorded_at_ms,
            ],
        )?;
        cas_require(&mut tx, &p.digest, EVENT_PAYLOAD_KIND, n)?;
        for r in &p.source.referenced_objects {
            cas_require(&mut tx, &r.digest, &r.kind, r.byte_length)?;
        }
    }
    let row = tx
        .query_opt(
            "SELECT * FROM runs WHERE harness_run_id=$1 FOR UPDATE",
            &[&run],
        )?
        .ok_or_else(|| WriteError::MissingRun(run.into()))?;
    let current = run_projection(&row)?;
    let contract = require_current_run_contract(&mut tx, &current)?;
    let lookup: Vec<_> = events.iter().map(|e| e.event_id.clone()).collect();
    let found = tx.query(
        "SELECT event_id FROM run_events WHERE event_id=ANY($1::text[])",
        &[&lookup],
    )?;
    if !found.is_empty() {
        if found.len() != events.len() {
            return Err(WriteError::Conflict("partially committed batch".into()));
        }
        for (i, p) in prepared.iter().enumerate() {
            let rev = expected_revision
                .checked_add(i64::try_from(i).map_err(|_| WriteError::Overflow)? + 1)
                .ok_or(WriteError::Overflow)?;
            exact(&mut tx, run, rev, p)?;
        }
        tx.commit()?;
        return Ok(Admission::Existing);
    }
    if current.revision != expected_revision {
        return Err(WriteError::Revision);
    }
    if matches!(current.status.as_str(), "completed" | "failed" | "stopped") {
        return Err(WriteError::Terminal);
    }
    require_lease(&mut tx, run, expected_revision, lease, lease_checked_at_ms)?;
    require_source_result_retention(&contract, events, staged)?;
    // Check the immutable per-Run physical dispatch limit first. A request
    // over budget is rejected regardless of its additional wire/identity
    // defects and must never acquire a physical send right.
    require_dispatch_budget(&mut tx, run, &contract, events)?;
    require_source_provider_admission(&mut tx, run, &contract, events)?;
    require_source_provider_failure(&mut tx, run, &contract, events)?;
    require_source_provider_completion(&mut tx, run, &contract, events)?;
    let mut status = current.status.as_str();
    let mut when = current.updated_at_ms;
    let mut terminal: Option<&str> = None;
    let mut preceding = BTreeSet::new();
    for (i, p) in prepared.iter().enumerate() {
        let e = p.source;
        if matches!(status, "completed" | "failed" | "stopped") || terminal.is_some() {
            return Err(WriteError::Terminal);
        }
        if e.recorded_at_ms < when {
            return Err(WriteError::Invalid("timestamp regressed"));
        }
        if let Some(cause) = e.caused_by_event_id.as_deref() {
            if !preceding.contains(cause) {
                let row = tx.query_opt(
                    "SELECT harness_run_id FROM run_events WHERE event_id=$1",
                    &[&cause],
                )?;
                if row.as_ref().map(|r| r.get::<_, String>(0)).as_deref() != Some(run) {
                    return Err(WriteError::Conflict("absent/foreign causal Event".into()));
                }
            }
        }
        status = transition(status, &e.event_kind)?;
        if matches!(status, "completed" | "failed" | "stopped") {
            if i + 1 != prepared.len() {
                return Err(WriteError::Terminal);
            }
            terminal = Some(e.event_id.as_str());
        }
        when = e.recorded_at_ms;
        preceding.insert(e.event_id.as_str());
    }
    let final_rev = expected_revision
        .checked_add(i64::try_from(prepared.len()).map_err(|_| WriteError::Overflow)?)
        .ok_or(WriteError::Overflow)?;
    if tx.execute(
        "UPDATE runs SET status=$1,revision=$2,updated_at_ms=$3,terminal_event_id=$4 \
                   WHERE harness_run_id=$5 AND revision=$6",
        &[
            &status,
            &final_rev,
            &when,
            &terminal,
            &run,
            &expected_revision,
        ],
    )? != 1
    {
        return Err(WriteError::Revision);
    }
    for (i, p) in prepared.iter().enumerate() {
        let e = p.source;
        let rev = expected_revision
            .checked_add(i64::try_from(i).map_err(|_| WriteError::Overflow)? + 1)
            .ok_or(WriteError::Overflow)?;
        tx.execute("INSERT INTO run_events(event_id,harness_run_id,run_revision,event_kind,payload_digest,\
                    caused_by_event_id,recorded_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7)",
                   &[&e.event_id,&run,&rev,&e.event_kind,&p.digest,&e.caused_by_event_id,&e.recorded_at_ms])?;
        for (digest, role) in edges(p) {
            tx.execute("INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) VALUES($1,$2,$3,$4)",
                       &[&run,&e.event_id,&digest,&role])?;
        }
    }
    if tx.execute(
        "DELETE FROM run_leases WHERE harness_run_id=$1 AND owner_id=$2 AND lease_revision=$3 \
                   AND run_revision=$4 AND expires_at_ms=$5",
        &[
            &run,
            &lease.owner_id(),
            &lease.lease_revision(),
            &lease.run_revision(),
            &lease.expires_at_ms(),
        ],
    )? != 1
    {
        return Err(WriteError::Fenced);
    }
    tx.commit()?;
    Ok(Admission::Created)
}

/// A Run Journal observation, not an external physical-effect assertion.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JournalObservation {
    ExactCommitted,
    NotObserved,
}

/// Reconcile exact Event IDs after a lost PostgreSQL commit response without
/// possessing an in-memory/consumed RunLease. Reuses the single authoritative
/// read_run_readonly PG REPEATABLE READ snapshot, which checks the entire Run,
/// typed versioned Contract, CAS bytes and all reference edges before this
/// pure comparison. NotObserved is NOT evidence that an external effect did
/// not happen, and does not authorize any automatic re-dispatch.
pub fn observe_exact_batch(
    db: &mut Client,
    schema: &str,
    run: &str,
    expected_revision: i64,
    events: &[EventWrite],
) -> Result<JournalObservation, WriteError> {
    if expected_revision < 1 || events.is_empty() || events.len() > 256 {
        return Err(WriteError::Invalid("reconciliation batch/revision"));
    }
    let mut ids = BTreeSet::new();
    for e in events {
        if !id_valid(&e.event_id)
            || !allowed(&e.event_kind)
            || e.recorded_at_ms < 0
            || !ids.insert(e.event_id.as_str())
        {
            return Err(WriteError::Invalid("reconciliation event id/kind/time"));
        }
    }
    let read = super::read_run_readonly(db, schema, run)?;
    let found: Vec<_> = events
        .iter()
        .filter(|event| {
            read.events
                .iter()
                .any(|existing| existing.event_id == event.event_id)
        })
        .collect();
    if found.is_empty() {
        return Ok(JournalObservation::NotObserved);
    }
    if found.len() != events.len() {
        return Err(WriteError::Conflict(
            "partial Journal batch observed".into(),
        ));
    }
    for (i, event) in events.iter().enumerate() {
        let desired_revision = expected_revision
            .checked_add(i64::try_from(i).map_err(|_| WriteError::Overflow)? + 1)
            .ok_or(WriteError::Overflow)?;
        let existing = read
            .events
            .iter()
            .find(|entry| entry.event_id == event.event_id)
            .expect("observed identity indexed");
        let desired_digest = digest_bytes(&payload(event)?);
        let supplied_refs: BTreeSet<_> = event
            .referenced_objects
            .iter()
            .map(|reference| {
                (
                    reference.digest.clone(),
                    reference.kind.clone(),
                    reference.byte_length,
                )
            })
            .collect();
        let stored_refs: BTreeSet<_> = read
            .verified_reference_links
            .iter()
            .filter(|reference| reference.event_id() == event.event_id)
            .map(|reference| {
                (
                    reference.digest().to_owned(),
                    reference.kind().to_owned(),
                    reference.byte_length(),
                )
            })
            .collect();
        if existing.run_revision != desired_revision
            || existing.event_kind != event.event_kind
            || existing.payload_digest != desired_digest
            || existing.caused_by_event_id != event.caused_by_event_id
            || existing.recorded_at_ms != event.recorded_at_ms
            || supplied_refs != stored_refs
        {
            return Err(WriteError::Conflict(format!(
                "committed Event differs from requested replay: {}",
                event.event_id
            )));
        }
    }
    Ok(JournalObservation::ExactCommitted)
}
