//! Read-only verified observation of the EXISTING PostgreSQL Harness schema v1.
//!
//! No CREATE/UPDATE/DELETE, lease acquisition, duplicate writer, or schema migration.
//! The caller controls a PostgreSQL role with read-only permissions and the DSN.
//! A single REPEATABLE READ / READ ONLY transaction binds the projection,
//! immutable CAS bytes, and committed Journal event chain to one PG snapshot.

#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use ordivon_harness_core::{canonical_bytes, digest_bytes, loads_strict, CanonicalDocument};
use postgres::{Client, IsolationLevel, Row};

const CONTRACT_KIND: &str = "harness-run-contract";
const EVENT_KIND: &str = "ordivon.harness-run-event-payload";

#[derive(Debug)]
pub enum ReadError {
    Database(postgres::Error),
    MissingRun(String),
    InvalidSchema,
    Corruption(String),
}

impl fmt::Display for ReadError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Database(error) => write!(f, "PostgreSQL read failed: {error}"),
            Self::MissingRun(run_id) => write!(f, "Harness Run is absent: {run_id}"),
            Self::InvalidSchema => {
                write!(f, "Harness schema must be one lower-case SQL identifier")
            }
            Self::Corruption(message) => write!(f, "Harness Journal corruption: {message}"),
        }
    }
}

impl std::error::Error for ReadError {}

impl From<postgres::Error> for ReadError {
    fn from(value: postgres::Error) -> Self {
        Self::Database(value)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunProjection {
    pub harness_run_id: String,
    pub contract_digest: String,
    pub contract_object_digest: String,
    pub caller_id: String,
    pub caller_run_ref: String,
    pub status: String,
    pub revision: i64,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    pub terminal_event_id: Option<String>,
}

#[derive(Debug, Clone)]
pub struct RunEvent {
    pub sequence: i64,
    pub event_id: String,
    pub run_revision: i64,
    pub event_kind: String,
    pub payload_digest: String,
    pub payload: CanonicalDocument,
    pub caused_by_event_id: Option<String>,
    pub recorded_at_ms: i64,
}

#[derive(Debug, Clone)]
pub struct Readback {
    pub projection: RunProjection,
    pub contract: CanonicalDocument,
    pub events: Vec<RunEvent>,
}

fn corrupted(message: impl Into<String>) -> ReadError {
    ReadError::Corruption(message.into())
}

fn valid_schema(schema: &str) -> bool {
    schema.len() <= 63
        && schema
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_lowercase)
        && schema
            .bytes()
            .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
}

fn require_string(doc: &CanonicalDocument, key: &str) -> Result<String, ReadError> {
    doc.field(key)
        .and_then(|item| item.as_str())
        .map(str::to_owned)
        .ok_or_else(|| corrupted(format!("field {key} is not a string")))
}

fn require_int<'a>(doc: &'a CanonicalDocument, key: &str) -> Result<&'a str, ReadError> {
    doc.field(key)
        .and_then(|item| item.integer_text())
        .ok_or_else(|| corrupted(format!("field {key} is not an integer")))
}

/// Decode and verify content exactly as the established Python
/// PostgresHarnessStore._decode_object_row does, without lossy JSON numbers.
pub fn decode_cas(
    expected_digest: &str,
    expected_kind: &str,
    row_kind: &str,
    byte_length: i64,
    raw: &[u8],
) -> Result<CanonicalDocument, ReadError> {
    if row_kind != expected_kind {
        return Err(corrupted(format!("CAS kind differs for {expected_digest}")));
    }
    if byte_length < 0 || usize::try_from(byte_length).ok() != Some(raw.len()) {
        return Err(corrupted(format!(
            "CAS length differs for {expected_digest}"
        )));
    }
    let text = std::str::from_utf8(raw)
        .map_err(|_| corrupted(format!("CAS invalid UTF-8: {expected_digest}")))?;
    let value = loads_strict(text)
        .map_err(|e| corrupted(format!("CAS invalid strict JSON: {expected_digest}: {e}")))?;
    if digest_bytes(raw) != expected_digest || canonical_bytes(&value) != raw {
        return Err(corrupted(format!(
            "CAS digest/canonical bytes differ for {expected_digest}"
        )));
    }
    Ok(value)
}

fn run_projection(row: &Row) -> Result<RunProjection, ReadError> {
    let status: String = row.get("status");
    if !matches!(
        status.as_str(),
        "created" | "active" | "paused" | "stopped" | "completed" | "failed"
    ) {
        return Err(corrupted(format!("invalid Run status: {status}")));
    }
    let projection = RunProjection {
        harness_run_id: row.get("harness_run_id"),
        contract_digest: row.get("contract_digest"),
        contract_object_digest: row.get("contract_object_digest"),
        caller_id: row.get("caller_id"),
        caller_run_ref: row.get("caller_run_ref"),
        status,
        revision: row.get("revision"),
        created_at_ms: row.get("created_at_ms"),
        updated_at_ms: row.get("updated_at_ms"),
        terminal_event_id: row.get("terminal_event_id"),
    };
    if projection.revision < 1
        || projection.created_at_ms < 0
        || projection.updated_at_ms < projection.created_at_ms
    {
        return Err(corrupted("Run revision/timestamps inconsistent"));
    }
    Ok(projection)
}

fn transition(previous: &str, event: &str) -> Result<&'static str, ReadError> {
    match event {
        "harness.run-created" => Ok("created"),
        "harness.run-paused" => Ok("paused"),
        "harness.run-stopped" => Ok("stopped"),
        "harness.run-completed" => Ok("completed"),
        "harness.run-failed" => Ok("failed"),
        "harness.trace-recorded" => match previous {
            "created" => Ok("created"),
            "active" => Ok("active"),
            "paused" => Ok("paused"),
            _ => Err(corrupted("trace event after terminal state")),
        },
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
        | "harness.tool-step-reconciled" => Ok("active"),
        _ => Err(corrupted(format!("unknown Harness Event kind: {event}"))),
    }
}

fn read_event(row: &Row) -> Result<RunEvent, ReadError> {
    let payload_digest: String = row.get("payload_digest");
    let object_kind: Option<String> = row.get("object_kind");
    let object_length: Option<i64> = row.get("object_byte_length");
    let content: Option<Vec<u8>> = row.get("object_content");
    let (kind, len, bytes) = match (object_kind, object_length, content) {
        (Some(kind), Some(len), Some(bytes)) => (kind, len, bytes),
        _ => {
            return Err(corrupted(format!(
                "event payload object missing: {payload_digest}"
            )))
        }
    };
    let payload = decode_cas(&payload_digest, EVENT_KIND, &kind, len, &bytes)?;
    let event_kind: String = row.get("event_kind");
    if payload.object_len() != Some(4)
        || require_int(&payload, "schemaVersion")? != "1"
        || require_string(&payload, "kind")? != EVENT_KIND
        || require_string(&payload, "eventKind")? != event_kind
        || payload
            .field("data")
            .and_then(|data| data.object_len())
            .is_none()
    {
        return Err(corrupted("event payload envelope differs from metadata"));
    }
    Ok(RunEvent {
        sequence: row.get("sequence"),
        event_id: row.get("event_id"),
        run_revision: row.get("run_revision"),
        event_kind,
        payload_digest,
        payload,
        caused_by_event_id: row.get("caused_by_event_id"),
        recorded_at_ms: row.get("recorded_at_ms"),
    })
}

fn validate_chain(
    projection: &RunProjection,
    contract: &CanonicalDocument,
    events: &[RunEvent],
) -> Result<(), ReadError> {
    if contract.object_len().is_none()
        || require_string(contract, "kind")? != "ordivon.harness-run-contract"
        || !matches!(require_int(contract, "schemaVersion")?, "1" | "2")
        || require_string(contract, "harnessRunId")? != projection.harness_run_id
        || require_string(contract, "callerId")? != projection.caller_id
        || require_string(contract, "callerRunRef")? != projection.caller_run_ref
        || projection.contract_digest != projection.contract_object_digest
    {
        return Err(corrupted("Run contract vs projection identity differs"));
    }
    if events.is_empty() || events[0].event_kind != "harness.run-created" {
        return Err(corrupted("missing Run creation event"));
    }
    let mut status = "created";
    let mut time = -1;
    let mut terminal: Option<&str> = None;
    let mut preceding = BTreeSet::new();
    let mut prior_sequence = 0;
    for (index, event) in events.iter().enumerate() {
        let expected_revision = i64::try_from(index).map_err(|_| corrupted("too many events"))? + 1;
        if event.run_revision != expected_revision
            || event.sequence <= prior_sequence
            || event.recorded_at_ms < time
            || terminal.is_some()
            || (index > 0 && event.event_kind == "harness.run-created")
        {
            return Err(corrupted(
                "Run event chain revision/time/terminal constraint violated",
            ));
        }
        if let Some(cause) = &event.caused_by_event_id {
            if !preceding.contains(cause.as_str()) {
                return Err(corrupted("Run event cause not in previous same-Run events"));
            }
        }
        status = transition(status, &event.event_kind)?;
        if matches!(status, "stopped" | "completed" | "failed") {
            terminal = Some(event.event_id.as_str());
        }
        if index == 0 {
            let data = event.payload.field("data").expect("validated event data");
            for (key, expected) in [
                ("contractDigest", projection.contract_digest.as_str()),
                (
                    "contractObjectDigest",
                    projection.contract_object_digest.as_str(),
                ),
                ("callerId", projection.caller_id.as_str()),
                ("callerRunRef", projection.caller_run_ref.as_str()),
            ] {
                if data.field(key).and_then(|item| item.as_str()) != Some(expected) {
                    return Err(corrupted(format!("creation Event data differs at {key}")));
                }
            }
        }
        preceding.insert(event.event_id.as_str());
        time = event.recorded_at_ms;
        prior_sequence = event.sequence;
    }
    if projection.revision
        != i64::try_from(events.len()).map_err(|_| corrupted("too many events"))?
        || projection.status != status
        || projection.updated_at_ms != time
        || projection.terminal_event_id.as_deref() != terminal
    {
        return Err(corrupted("projection differs from Journal replay"));
    }
    Ok(())
}

/// Observe a complete Harness Run from one database snapshot. This never
/// calls any write API; the read-only transaction also fails closed on writes.
pub fn read_run_readonly(
    connection: &mut Client,
    schema: &str,
    run_id: &str,
) -> Result<Readback, ReadError> {
    if !valid_schema(schema) {
        return Err(ReadError::InvalidSchema);
    }
    let mut tx = connection
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()?;
    tx.batch_execute(&format!("SET LOCAL search_path TO {schema}"))?;
    let version: Option<String> = tx
        .query_opt(
            "SELECT value FROM schema_info WHERE key='schema_version'",
            &[],
        )?
        .map(|r| r.get(0));
    if version.as_deref() != Some("1") {
        return Err(corrupted("PG Harness schema_version is not v1"));
    }
    let projection = match tx.query_opt("SELECT * FROM runs WHERE harness_run_id=$1", &[&run_id])? {
        Some(row) => run_projection(&row)?,
        None => return Err(ReadError::MissingRun(run_id.to_owned())),
    };
    let contract = match tx.query_opt(
        "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
        &[&projection.contract_object_digest],
    )? {
        Some(row) => decode_cas(
            &projection.contract_object_digest,
            CONTRACT_KIND,
            &row.get::<_, String>("kind"),
            row.get::<_, i64>("byte_length"),
            &row.get::<_, Vec<u8>>("content"),
        )?,
        None => return Err(corrupted("Run Contract object missing")),
    };
    let rows = tx.query(
        "SELECT e.sequence,e.event_id,e.run_revision,e.event_kind,e.payload_digest, \
         e.caused_by_event_id,e.recorded_at_ms, \
         o.kind AS object_kind,o.byte_length AS object_byte_length, \
         o.content AS object_content \
         FROM run_events e LEFT JOIN objects o ON o.digest=e.payload_digest \
         WHERE e.harness_run_id=$1 ORDER BY e.sequence",
        &[&run_id],
    )?;
    let events: Vec<RunEvent> = rows.iter().map(read_event).collect::<Result<_, _>>()?;
    validate_chain(&projection, &contract, &events)?;
    // The original Store checks referenced objects during write, and each
    // event's payload reference is a persisted edge. Qualify the relationship
    // without interpreting any effect/Provider-specific referenced content.
    let edges = tx.query(
        "SELECT r.event_id,r.digest,r.role,o.kind AS object_kind, \
         o.byte_length AS object_byte_length,o.content AS object_content \
         FROM run_object_refs r LEFT JOIN objects o ON o.digest=r.digest \
         WHERE r.harness_run_id=$1 ORDER BY r.event_id,r.digest",
        &[&run_id],
    )?;
    let known: BTreeMap<&str, &str> = events
        .iter()
        .map(|e| (e.event_id.as_str(), e.payload_digest.as_str()))
        .collect();
    let mut payload_edges = BTreeSet::new();
    for row in edges {
        let event_id: String = row.get("event_id");
        let digest: String = row.get("digest");
        let role: String = row.get("role");
        let expected = known
            .get(event_id.as_str())
            .ok_or_else(|| corrupted("CAS edge references another Run or unknown Event"))?;
        if role == "payload" {
            if *expected != digest || !payload_edges.insert(event_id.clone()) {
                return Err(corrupted("event CAS payload edge differs"));
            }
        } else if role != "reference" || *expected == digest {
            return Err(corrupted("invalid CAS reference edge role/digest"));
        }
        let kind: Option<String> = row.get("object_kind");
        let len: Option<i64> = row.get("object_byte_length");
        let content: Option<Vec<u8>> = row.get("object_content");
        match (kind, len, content) {
            (Some(kind), Some(len), Some(bytes)) => {
                decode_cas(&digest, &kind, &kind, len, &bytes)?;
            }
            _ => return Err(corrupted("CAS reference edge target missing")),
        }
    }
    if payload_edges.len() != events.len() {
        return Err(corrupted("Run Event lacks CAS payload reference edge"));
    }
    tx.commit()?;
    Ok(Readback {
        projection,
        contract,
        events,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_sql_schema_names_and_malformed_objects() {
        for schema in [
            "",
            "Public",
            "pg-test",
            "harness;drop schema public",
            "_hidden",
            "1foo",
            "x y",
        ] {
            assert!(!valid_schema(schema), "{schema}");
        }
        for schema in ["harness", "harness_1", "hpg_test_abc"] {
            assert!(valid_schema(schema), "{schema}");
        }
        let src = br#"{"a":1}"#;
        let digest = digest_bytes(src);
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64, src).is_ok());
        assert!(decode_cas(&digest, "kind", "wrong", src.len() as i64, src).is_err());
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64 + 1, src).is_err());
        assert!(decode_cas("sha256:corrupt", "kind", "kind", src.len() as i64, src).is_err());
        assert!(decode_cas(&digest, "kind", "kind", src.len() as i64, br#"{ "a":1}"#).is_err());
    }
}
