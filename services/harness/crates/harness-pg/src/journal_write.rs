//! Atomic Journal admission in the existing Python PostgreSQL v1 schema.
//! A committed Event is not a Provider/Tool effect or semantic success.
//! Lost commit responses are UNKNOWN until exact Event-ID reconciliation.

use super::lease::{check_schema, LeaseError, RunLease};
use super::{decode_cas, run_projection, transition, valid_schema, ReadError};
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
    let mut tx = db.transaction()?;
    check_schema(&mut tx, schema)?;
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
