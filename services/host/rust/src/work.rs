//! Work CAS, history readback, and exact request replay against Host PG schema 13.
//!
//! First migration slice only. This module intentionally does not own connection
//! pooling, migrations, MCP transport, or external-effect truth. All mutations
//! share ONE caller-owned PostgreSQL transaction.
use chrono::{DateTime, FixedOffset, SecondsFormat, Utc};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use thiserror::Error;
use tokio_postgres::{types::Json, Client, IsolationLevel, Transaction};

#[derive(Debug, Error)]
pub enum WorkError {
    #[error("INVALID_ARGUMENT: {0}")]
    Invalid(String),
    #[error("CONFLICT: {0}")]
    Conflict(String),
    #[error("NOT_FOUND: {0}")]
    NotFound(String),
    #[error("ACTOR_REF_NOT_FOUND: {0}")]
    ActorNotFound(String),
    #[error("INTEGRITY_ERROR: {0}")]
    Integrity(String),
    #[error(transparent)]
    Database(#[from] tokio_postgres::Error),
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum WorkState {
    #[default]
    Open,
    Completed,
    Abandoned,
}

impl WorkState {
    fn as_str(self) -> &'static str {
        match self {
            Self::Open => "open",
            Self::Completed => "completed",
            Self::Abandoned => "abandoned",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorkSnapshot {
    pub objective: String,
    pub frontier: String,
    #[serde(default)]
    pub established: Vec<String>,
    #[serde(default)]
    pub unresolved: Vec<String>,
    #[serde(default)]
    pub rejected: Vec<String>,
    #[serde(default)]
    pub constraints: Vec<String>,
    #[serde(rename = "nextActions", alias = "next_actions", default)]
    pub next_actions: Vec<String>,
    #[serde(rename = "referenceRefs", alias = "reference_refs", default)]
    pub reference_refs: Vec<String>,
}

impl WorkSnapshot {
    pub fn validate(&self) -> Result<(), WorkError> {
        for (name, text) in [("objective", &self.objective), ("frontier", &self.frontier)] {
            if text.is_empty() || text.chars().count() > 4096 {
                return Err(WorkError::Invalid(format!(
                    "{name} must have 1..=4096 codepoints"
                )));
            }
        }
        for (name, values, bound) in [
            ("established", &self.established, 128),
            ("unresolved", &self.unresolved, 128),
            ("rejected", &self.rejected, 128),
            ("constraints", &self.constraints, 128),
            ("nextActions", &self.next_actions, 128),
            ("referenceRefs", &self.reference_refs, 256),
        ] {
            if values.len() > bound
                || values.iter().any(|s| {
                    // Python str.strip includes U+001C..U+001F; Rust trim does not.
                    s.is_empty()
                        || s.trim_matches(|ch: char| {
                            ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch)
                        }) != s
                })
            {
                return Err(WorkError::Invalid(format!(
                    "{name} has invalid entries/count"
                )));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct CommitSnapshot {
    pub work_ref: String,
    pub expected_revision: i64,
    pub snapshot: WorkSnapshot,
    pub actor_ref: String,
    pub state: WorkState,
    pub client_request_id: String,
}

impl CommitSnapshot {
    fn validate(&self) -> Result<(), WorkError> {
        if !(1..i64::MAX).contains(&self.expected_revision) {
            return Err(WorkError::Invalid(
                "expected_revision must be a positive PostgreSQL BIGINT predecessor".into(),
            ));
        }
        if self.expected_revision > 9_007_199_254_740_991 {
            return Err(WorkError::Invalid(
                "expected_revision exceeds Python RFC 8785 safe integer domain".into(),
            ));
        }
        validate_identifier(&self.work_ref, 3, 1024)?;
        validate_identifier(&self.actor_ref, 3, 512)?;
        // MCP validation enforces additional request-identity rules.
        if self.client_request_id.is_empty() {
            return Err(WorkError::Invalid(
                "client_request_id cannot be empty".into(),
            ));
        }
        self.snapshot.validate()
    }
}

fn validate_identifier(value: &str, min: usize, max: usize) -> Result<(), WorkError> {
    if !(min..=max).contains(&value.chars().count())
        || value.trim() != value
        || value.chars().any(|c| (c as u32) < 0x20)
    {
        return Err(WorkError::Invalid("invalid trimmed identifier".into()));
    }
    Ok(())
}

/// The identical RFC 8785 algorithm is also used by the Python Host.
/// Cross-language byte equality remains a separate mandatory qualification.
pub fn canonical_digest(value: &Value) -> Result<String, WorkError> {
    ensure_safe_json_numbers(value)?;
    let bytes = serde_json_canonicalizer::to_vec(value)
        .map_err(|error| WorkError::Invalid(format!("invalid canonical JSON: {error}")))?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(bytes))))
}

/// Python rfc8785 rejects JSON integers outside the I-JSON safe domain.
/// serde_json_canonicalizer may round them as f64; do not silently change
/// request identities during the Python -> Rust migration.
fn ensure_safe_json_numbers(value: &Value) -> Result<(), WorkError> {
    const MAX: i64 = 9_007_199_254_740_991;
    match value {
        Value::Number(n) => {
            if n.as_i64().is_some_and(|v| !(-MAX..=MAX).contains(&v))
                || n.as_u64().is_some_and(|v| v > MAX as u64)
            {
                return Err(WorkError::Invalid(
                    "integer exceeds Python RFC 8785 safe integer domain".into(),
                ));
            }
        }
        Value::Array(items) => {
            for item in items {
                ensure_safe_json_numbers(item)?;
            }
        }
        Value::Object(fields) => {
            for item in fields.values() {
                ensure_safe_json_numbers(item)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn postgres_timestamp(value: DateTime<Utc>, offset_seconds: i32) -> Result<String, WorkError> {
    let offset = FixedOffset::east_opt(offset_seconds)
        .ok_or_else(|| WorkError::Integrity("invalid PostgreSQL timezone offset".into()))?;
    let local = value.with_timezone(&offset);
    let precision = if local.timestamp_subsec_micros() == 0 {
        SecondsFormat::Secs
    } else {
        SecondsFormat::Micros
    };
    Ok(local.to_rfc3339_opts(precision, false))
}

/// One RR read-only snapshot, matching Python WorkReadQueries.get_work.
/// Missing historical revisions are explicitly CONFLICT, never fabricated.
pub async fn get_work(
    client: &mut Client,
    work_ref: &str,
    revision: Option<i64>,
) -> Result<Value, WorkError> {
    if revision.is_some_and(|r| r < 1) {
        return Err(WorkError::Invalid(
            "revision must be positive BIGINT".into(),
        ));
    }
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let result = get_work_in_tx(&tx, work_ref, revision).await?;
    tx.commit().await?;
    Ok(result)
}

async fn get_work_in_tx(
    tx: &Transaction<'_>,
    work_ref: &str,
    revision: Option<i64>,
) -> Result<Value, WorkError> {
    let work = tx
        .query_opt(
            "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref,created_at,updated_at, \
             EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz, \n             EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \n             FROM works WHERE work_ref=$1",
            &[&work_ref],
        )
        .await?
        .ok_or_else(|| WorkError::NotFound(work_ref.into()))?;

    let current_revision: i64 = work.try_get("current_revision")?;
    let target_revision = revision.unwrap_or(current_revision);
    let snapshot = tx
        .query_opt(
            "SELECT snapshot_digest,payload,writer_actor_ref,created_at \
             FROM work_snapshots WHERE work_ref=$1 AND revision=$2",
            &[&work_ref, &target_revision],
        )
        .await?
        .ok_or_else(|| {
            WorkError::Conflict(format!("work {work_ref} has no revision {target_revision}"))
        })?;

    let digest: String = snapshot.try_get("snapshot_digest")?;
    let payload: Value = snapshot.try_get::<_, Json<Value>>("payload")?.0;
    if !payload.is_object() || canonical_digest(&payload)? != digest {
        return Err(WorkError::Integrity(
            "durable Work snapshot payload digest differs".into(),
        ));
    }
    let current_digest: String = work.try_get("current_snapshot_digest")?;
    if target_revision == current_revision && current_digest != digest {
        return Err(WorkError::Integrity(
            "current Work snapshot pointer digest differs".into(),
        ));
    }

    let current_state: String = work.try_get("state")?;
    let state = if target_revision == current_revision {
        current_state.as_str()
    } else {
        "historical_state_unknown"
    };
    let created_at: DateTime<Utc> = work.try_get("created_at")?;
    let updated_at: DateTime<Utc> = work.try_get("updated_at")?;
    let created_tz: i32 = work.try_get("created_tz")?;
    let updated_tz: i32 = work.try_get("updated_tz")?;
    Ok(json!({
        "schemaVersion": 1,
        "kind": "ordivon.host-work",
        "workRef": work.try_get::<_, String>("work_ref")?,
        "workKind": work.try_get::<_, String>("kind")?,
        "state": state,
        "revision": target_revision,
        "snapshotDigest": digest,
        "snapshot": payload,
        "writerActorRef": snapshot.try_get::<_, String>("writer_actor_ref")?,
        "createdByActorRef": work.try_get::<_, String>("created_by_actor_ref")?,
        "createdAt": postgres_timestamp(created_at, created_tz)?,
        "updatedAt": postgres_timestamp(updated_at, updated_tz)?,
        "truthBoundary": "Host semantic Work continuity only; Runtime/Git/domain truth must be revalidated"
    }))
}

async fn claim_receipt(
    tx: &Transaction<'_>,
    client_request_id: &str,
    operation: &str,
    request_digest: &str,
) -> Result<Option<Value>, WorkError> {
    let new_claim = tx
        .query_opt(
            "INSERT INTO command_receipts(client_request_id,operation,request_digest,response) \
             VALUES ($1,$2,$3,NULL) ON CONFLICT (client_request_id) DO NOTHING RETURNING client_request_id",
            &[&client_request_id, &operation, &request_digest],
        )
        .await?;
    if new_claim.is_some() {
        return Ok(None);
    }

    let row = tx
        .query_opt(
            "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=$1",
            &[&client_request_id],
        )
        .await?
        .ok_or_else(|| WorkError::Integrity("idempotency claim disappeared".into()))?;
    let prior_operation: String = row.try_get("operation")?;
    let prior_digest: String = row.try_get("request_digest")?;
    if prior_operation != operation || prior_digest != request_digest {
        return Err(WorkError::Conflict(
            "client_request_id was already used for different content".into(),
        ));
    }
    let response: Option<Json<Value>> = row.try_get("response")?;
    let mut result = response
        .ok_or_else(|| WorkError::Integrity("committed receipt has no response".into()))?
        .0;
    if !result.is_object() {
        return Err(WorkError::Integrity(
            "idempotency response is not an object".into(),
        ));
    }
    result["admission"] = json!("existing");
    Ok(Some(result))
}

async fn record_receipt(
    tx: &Transaction<'_>,
    client_request_id: &str,
    operation: &str,
    digest: &str,
    result: &Value,
) -> Result<(), WorkError> {
    if tx
        .query_opt(
            "UPDATE command_receipts SET response=$1 \
             WHERE client_request_id=$2 AND operation=$3 AND request_digest=$4 AND response IS NULL \
             RETURNING client_request_id",
            &[&Json(result), &client_request_id, &operation, &digest],
        )
        .await?
        .is_none()
    {
        return Err(WorkError::Integrity("idempotency claim could not be finalized".into()));
    }
    Ok(())
}

/// Host actor references are stable labels, not authentication principals.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ActorKind {
    Unknown,
    Human,
    Agent,
    Service,
    Organization,
}

impl ActorKind {
    fn as_str(self) -> &'static str {
        match self {
            Self::Unknown => "unknown",
            Self::Human => "human",
            Self::Agent => "agent",
            Self::Service => "service",
            Self::Organization => "organization",
        }
    }
}

#[derive(Clone, Debug)]
pub struct ActorDeclare {
    pub actor_ref: String,
    pub actor_kind: ActorKind,
    pub client_request_id: String,
}

impl ActorDeclare {
    fn validate(&self) -> Result<(), WorkError> {
        // Pydantic ActorRefInput: 3..512 codepoints, printable, namespace,
        // Python str.strip and no U+0000..U+001F control characters.
        validate_identifier(&self.actor_ref, 3, 512)?;
        if !self.actor_ref.contains(':') {
            return Err(WorkError::Invalid(
                "actor_ref must contain a namespace separator".into(),
            ));
        }
        if self.client_request_id.is_empty() {
            return Err(WorkError::Invalid(
                "client_request_id cannot be empty".into(),
            ));
        }
        Ok(())
    }
}

/// One PG transaction and one receipt authority for actor.declare.
///
/// ON CONFLICT is the insert linearization point. A concurrent identical
/// declaration becomes existing, but an altered actor kind is a conflict.
/// Neither ActorKind nor an actor reference proves identity/permission.
pub async fn declare_actor(
    client: &mut Client,
    command: &ActorDeclare,
) -> Result<Value, WorkError> {
    command.validate()?;
    const OPERATION: &str = "actor.declare";
    // The Python request digest uses *snake_case* Pydantic field names, NOT
    // the camelCase MCP argument names or the output response shape.
    let request = json!({
        "operation": OPERATION,
        "actor_ref": command.actor_ref,
        "actor_kind": command.actor_kind.as_str(),
    });
    let request_digest = canonical_digest(&request)?;
    let tx = client.transaction().await?;
    if let Some(previous) =
        claim_receipt(&tx, &command.client_request_id, OPERATION, &request_digest).await?
    {
        tx.commit().await?;
        return Ok(previous);
    }
    let inserted = tx
        .query_opt(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ($1,$2) \
         ON CONFLICT (actor_ref) DO NOTHING \
         RETURNING actor_ref,actor_kind,created_at, \
         EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz",
            &[&command.actor_ref, &command.actor_kind.as_str()],
        )
        .await?;
    let (row, admission) = if let Some(row) = inserted {
        (row, "committed")
    } else {
        // READ COMMITTED: after ON CONFLICT waited for the winning insert,
        // this fresh statement can read the committed row.
        let row = tx
            .query_opt(
                "SELECT actor_ref,actor_kind,created_at, \
             EXTRACT(TIMEZONE FROM created_at)::integer AS created_tz \
             FROM actor_refs WHERE actor_ref=$1",
                &[&command.actor_ref],
            )
            .await?
            .ok_or_else(|| {
                WorkError::Integrity("actor declaration disappeared after conflict".into())
            })?;
        let previous_kind: String = row.try_get("actor_kind")?;
        if previous_kind != command.actor_kind.as_str() {
            return Err(WorkError::Conflict(
                "actor_ref already exists with a different actor_kind".into(),
            ));
        }
        (row, "existing")
    };
    let created_at: DateTime<Utc> = row.try_get("created_at")?;
    let created_tz: i32 = row.try_get("created_tz")?;
    let response = json!({
        "schemaVersion": 1,
        "kind": "ordivon.host-actor-ref",
        "admission": admission,
        "actorRef": row.try_get::<_, String>("actor_ref")?,
        "actorKind": row.try_get::<_, String>("actor_kind")?,
        "createdAt": postgres_timestamp(created_at, created_tz)?,
        "truthBoundary": "Host-stored stable actor reference only; not authenticated identity or authorization",
    });
    record_receipt(
        &tx,
        &command.client_request_id,
        OPERATION,
        &request_digest,
        &response,
    )
    .await?;
    tx.commit().await?;
    Ok(response)
}

/// One Work identity and its immutable initial semantic payload.
#[derive(Clone, Debug)]
pub struct CreateWork {
    pub work_ref: String,
    pub kind: String,
    pub actor_ref: String,
    pub initial_snapshot: WorkSnapshot,
    pub client_request_id: String,
}

impl CreateWork {
    fn validate(&self) -> Result<(), WorkError> {
        validate_identifier(&self.work_ref, 3, 1024)?;
        validate_identifier(&self.kind, 1, 128)?;
        validate_identifier(&self.actor_ref, 3, 512)?;
        if self.client_request_id.is_empty() {
            return Err(WorkError::Invalid(
                "client_request_id cannot be empty".into(),
            ));
        }
        self.initial_snapshot.validate()
    }
}

/// Python-compatible create semantics: unique WorkRef is the insertion
/// linearization point. A concurrent creator must re-read revision one after
/// ON CONFLICT and return current Work state, not invent a new revision.
pub async fn create_work(client: &mut Client, command: &CreateWork) -> Result<Value, WorkError> {
    command.validate()?;
    let payload = serde_json::to_value(&command.initial_snapshot)
        .map_err(|e| WorkError::Invalid(e.to_string()))?;
    let snapshot_digest = canonical_digest(&payload)?;
    let operation = "work.create";
    let request = json!({
        "operation": operation,
        "workRef": command.work_ref,
        "kind": command.kind,
        "actorRef": command.actor_ref,
        "initialSnapshot": payload
    });
    let request_digest = canonical_digest(&request)?;
    let tx = client.transaction().await?;
    if let Some(previous) =
        claim_receipt(&tx, &command.client_request_id, operation, &request_digest).await?
    {
        tx.commit().await?;
        return Ok(previous);
    }
    if tx
        .query_opt(
            "SELECT 1 FROM actor_refs WHERE actor_ref=$1",
            &[&command.actor_ref],
        )
        .await?
        .is_none()
    {
        return Err(WorkError::ActorNotFound(command.actor_ref.clone()));
    }
    let inserted = tx
        .query_opt(
            "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref) \
             VALUES ($1,$2,'open',1,$3,$4) ON CONFLICT (work_ref) DO NOTHING RETURNING work_ref",
            &[
                &command.work_ref,
                &command.kind,
                &snapshot_digest,
                &command.actor_ref,
            ],
        )
        .await?;
    let admission = if inserted.is_some() {
        tx.execute(
            "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) \
             VALUES ($1,1,$2,$3,$4)",
            &[
                &command.work_ref,
                &snapshot_digest,
                &Json(&payload),
                &command.actor_ref,
            ],
        )
        .await?;
        "committed"
    } else {
        // Must re-read after conflicting creator commits (READ COMMITTED);
        // SELECT-before-INSERT is not a correct uniqueness/concurrency check.
        let current = tx
            .query_opt(
                "SELECT kind FROM works WHERE work_ref=$1 FOR UPDATE",
                &[&command.work_ref],
            )
            .await?
            .ok_or_else(|| WorkError::Integrity("work_ref disappeared after conflict".into()))?;
        let initial = tx
            .query_opt(
                "SELECT snapshot_digest,writer_actor_ref FROM work_snapshots \
                 WHERE work_ref=$1 AND revision=1",
                &[&command.work_ref],
            )
            .await?;
        let matching = if let Some(initial) = initial {
            let prior_digest: String = initial.try_get("snapshot_digest")?;
            let prior_actor: String = initial.try_get("writer_actor_ref")?;
            let prior_kind: String = current.try_get("kind")?;
            prior_kind == command.kind
                && prior_digest == snapshot_digest
                && prior_actor == command.actor_ref
        } else {
            false
        };
        if !matching {
            return Err(WorkError::Conflict(
                "work_ref already exists with different initial semantics".into(),
            ));
        }
        "existing"
    };
    let mut result = get_work_in_tx(&tx, &command.work_ref, None).await?;
    result["admission"] = json!(admission);
    record_receipt(
        &tx,
        &command.client_request_id,
        operation,
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

/// Cursor inputs and UTF-8 response envelope budget mirror Python Work.list.
#[derive(Clone, Debug)]
pub struct ListWorks {
    pub state: Option<WorkState>,
    pub limit: usize,
    pub before_updated_at: Option<String>,
    pub before_work_ref: Option<String>,
    pub max_bytes: usize,
}

impl Default for ListWorks {
    fn default() -> Self {
        Self {
            state: None,
            limit: 50,
            before_updated_at: None,
            before_work_ref: None,
            max_bytes: 262_144,
        }
    }
}

impl ListWorks {
    fn validate(&self) -> Result<(), WorkError> {
        if !(1..=200).contains(&self.limit) {
            return Err(WorkError::Invalid("limit must be in [1,200]".into()));
        }
        if self.before_updated_at.is_some() != self.before_work_ref.is_some() {
            return Err(WorkError::Invalid(
                "before_updated_at and before_work_ref must be supplied together".into(),
            ));
        }
        if !(16_384..=4_194_304).contains(&self.max_bytes) {
            return Err(WorkError::Invalid(
                "max_bytes must be in [16384,4194304]".into(),
            ));
        }
        Ok(())
    }
}

fn work_list_envelope(works: &[Value], has_more: bool) -> Value {
    let cursor = if has_more {
        works.last().map(|last| {
            json!({
                "beforeUpdatedAt": last["updatedAt"],
                "beforeWorkRef": last["workRef"]
            })
        })
    } else {
        None
    };
    json!({
        "schemaVersion": 1,
        "kind": "ordivon.host-work-list",
        "works": works,
        "hasMore": has_more,
        "nextCursor": cursor,
        "rankingApplied": false,
        "truthBoundary": "compact point-in-time Work inventory; not priority, assignment, Runtime activity, or domain currentness"
    })
}

/// Stable descending (updated_at, work_ref) pagination within a single
/// read-only RR transaction, including exact RFC 8785 byte-budget truncation.
pub async fn list_works(client: &mut Client, input: &ListWorks) -> Result<Value, WorkError> {
    input.validate()?;
    let state = input.state.map(WorkState::as_str);
    let before_at = input.before_updated_at.as_deref();
    let before_ref = input.before_work_ref.as_deref();
    let limit_plus_one =
        i64::try_from(input.limit + 1).map_err(|_| WorkError::Invalid("limit overflow".into()))?;
    let tx = client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await?;
    let rows = tx
        .query(
            "SELECT work_ref,kind,state,current_revision,current_snapshot_digest,updated_at, \
             EXTRACT(TIMEZONE FROM updated_at)::integer AS updated_tz \
             FROM works WHERE ($1::text IS NULL OR state=$1) \
             AND ($2::text::timestamptz IS NULL OR (updated_at,work_ref)<($2::text::timestamptz,$3)) \
             ORDER BY updated_at DESC,work_ref DESC LIMIT $4",
            &[&state, &before_at, &before_ref, &limit_plus_one],
        )
        .await?;

    let sql_more = rows.len() > input.limit;
    let candidates = rows
        .iter()
        .take(input.limit)
        .map(|row| -> Result<Value, WorkError> {
            let updated_at: DateTime<Utc> = row.try_get("updated_at")?;
            let offset: i32 = row.try_get("updated_tz")?;
            Ok(json!({
                "workRef": row.try_get::<_, String>("work_ref")?,
                "workKind": row.try_get::<_, String>("kind")?,
                "state": row.try_get::<_, String>("state")?,
                "revision": row.try_get::<_, i64>("current_revision")?,
                "snapshotDigest": row.try_get::<_, String>("current_snapshot_digest")?,
                "updatedAt": postgres_timestamp(updated_at, offset)?
            }))
        })
        .collect::<Result<Vec<_>, _>>()?;

    let mut page: Vec<Value> = Vec::with_capacity(candidates.len());
    let mut byte_more = false;
    for row in candidates {
        page.push(row);
        // Existing Python bounded_prefix measures canonical bytes assuming
        // hasMore=true even when this is eventually the final page.
        let test_envelope = work_list_envelope(&page, true);
        ensure_safe_json_numbers(&test_envelope)?;
        let bytes = serde_json_canonicalizer::to_vec(&test_envelope)
            .map_err(|e| WorkError::Invalid(e.to_string()))?;
        if bytes.len() > input.max_bytes {
            page.pop();
            if page.is_empty() {
                return Err(WorkError::Invalid(
                    "max_bytes cannot fit one legal item plus response envelope".into(),
                ));
            }
            byte_more = true;
            break;
        }
    }
    tx.commit().await?;
    Ok(work_list_envelope(&page, sql_more || byte_more))
}

/// Atomic Work CAS and exact replay. External effects and semantic domain success
/// are deliberately outside this transaction and outside Host authority.
pub async fn commit_snapshot(
    client: &mut Client,
    command: &CommitSnapshot,
) -> Result<Value, WorkError> {
    command.validate()?;
    let payload = serde_json::to_value(&command.snapshot)
        .map_err(|error| WorkError::Invalid(error.to_string()))?;
    let snapshot_digest = canonical_digest(&payload)?;
    let operation = "work.snapshot.commit";
    let request = json!({
        "operation": operation,
        "workRef": command.work_ref,
        "expectedRevision": command.expected_revision,
        "snapshot": payload,
        "actorRef": command.actor_ref,
        "state": command.state.as_str()
    });
    let request_digest = canonical_digest(&request)?;
    let tx = client.transaction().await?;

    if let Some(previous) =
        claim_receipt(&tx, &command.client_request_id, operation, &request_digest).await?
    {
        tx.commit().await?;
        return Ok(previous);
    }

    if tx
        .query_opt(
            "SELECT 1 FROM actor_refs WHERE actor_ref=$1",
            &[&command.actor_ref],
        )
        .await?
        .is_none()
    {
        return Err(WorkError::ActorNotFound(command.actor_ref.clone()));
    }
    let work = tx
        .query_opt(
            "SELECT work_ref,state,current_revision FROM works WHERE work_ref=$1 FOR UPDATE",
            &[&command.work_ref],
        )
        .await?
        .ok_or_else(|| WorkError::NotFound(command.work_ref.clone()))?;

    let current_revision: i64 = work.try_get("current_revision")?;
    let current_state: String = work.try_get("state")?;
    let next_revision = command.expected_revision + 1;

    // Python permits a new request identity with exactly matching next-revision
    // content, actor and Work state to observe an already-committed CAS effect.
    if current_revision == next_revision {
        if let Some(existing) = tx
            .query_opt(
                "SELECT snapshot_digest,writer_actor_ref FROM work_snapshots \
                 WHERE work_ref=$1 AND revision=$2",
                &[&command.work_ref, &next_revision],
            )
            .await?
        {
            let prior_digest: String = existing.try_get("snapshot_digest")?;
            let prior_writer: String = existing.try_get("writer_actor_ref")?;
            if prior_digest == snapshot_digest
                && prior_writer == command.actor_ref
                && current_state == command.state.as_str()
            {
                let mut result =
                    get_work_in_tx(&tx, &command.work_ref, Some(next_revision)).await?;
                result["admission"] = json!("existing");
                record_receipt(
                    &tx,
                    &command.client_request_id,
                    operation,
                    &request_digest,
                    &result,
                )
                .await?;
                tx.commit().await?;
                return Ok(result);
            }
        }
    }

    if current_revision != command.expected_revision {
        return Err(WorkError::Conflict(format!(
            "expected revision {}, current revision is {}",
            command.expected_revision, current_revision
        )));
    }
    if current_state != "open" {
        return Err(WorkError::Conflict(
            "terminal work cannot be checkpointed or reopened".into(),
        ));
    }

    let updated = tx
        .query_opt(
            "UPDATE works SET state=$1,current_revision=$2,current_snapshot_digest=$3,updated_at=clock_timestamp() \
             WHERE work_ref=$4 AND current_revision=$5 AND state='open' RETURNING work_ref",
            &[
                &command.state.as_str(),
                &next_revision,
                &snapshot_digest,
                &command.work_ref,
                &command.expected_revision,
            ],
        )
        .await?;
    if updated.is_none() {
        return Err(WorkError::Conflict(
            "same-revision transition lost concurrency race".into(),
        ));
    }
    tx.execute(
        "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) \
         VALUES ($1,$2,$3,$4,$5)",
        &[
            &command.work_ref,
            &next_revision,
            &snapshot_digest,
            &Json(&payload),
            &command.actor_ref,
        ],
    )
    .await?;

    let mut result = get_work_in_tx(&tx, &command.work_ref, Some(next_revision)).await?;
    result["admission"] = json!("committed");
    record_receipt(
        &tx,
        &command.client_request_id,
        operation,
        &request_digest,
        &result,
    )
    .await?;
    tx.commit().await?;
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn python_str_strip_control_boundary_is_preserved() {
        let mut snapshot: WorkSnapshot = serde_json::from_value(json!({
            "objective": "o",
            "frontier": "f"
        }))
        .unwrap();
        // Python str.strip removes four Unicode C0 separators that Rust trim
        // does not. Preserve edge-only rejection, not a blanket control ban.
        for ch in ['\u{001c}', '\u{001d}', '\u{001e}', '\u{001f}'] {
            snapshot.established = vec![format!("a{ch}")];
            assert!(
                matches!(snapshot.validate(), Err(WorkError::Invalid(_))),
                "edge U+{:04X} must be rejected",
                ch as u32
            );
            snapshot.established = vec![format!("a{ch}b")];
            assert!(
                snapshot.validate().is_ok(),
                "internal U+{:04X} must remain accepted",
                ch as u32
            );
        }
    }

    #[test]
    fn revision_bounds_fail_closed() {
        let s = WorkSnapshot {
            objective: "obj".into(),
            frontier: "next".into(),
            established: vec![],
            unresolved: vec![],
            rejected: vec![],
            constraints: vec![],
            next_actions: vec![],
            reference_refs: vec![],
        };
        for revision in [0, -1, i64::MAX] {
            let cmd = CommitSnapshot {
                work_ref: "work:test:revision".into(),
                expected_revision: revision,
                snapshot: s.clone(),
                actor_ref: "actor:test:one".into(),
                state: WorkState::Open,
                client_request_id: "request:test:revision".into(),
            };
            assert!(matches!(cmd.validate(), Err(WorkError::Invalid(_))));
        }
    }
    #[test]
    fn snapshot_defaults_and_camelcase_are_preserved() {
        let value = json!({"objective":"a","frontier":"b"});
        let snapshot: WorkSnapshot = serde_json::from_value(value).unwrap();
        let output = serde_json::to_value(snapshot).unwrap();
        assert_eq!(output["nextActions"], json!([]));
        assert_eq!(output["referenceRefs"], json!([]));
        assert!(output.get("next_actions").is_none());
        assert_eq!(output.as_object().unwrap().len(), 8);
    }
    #[test]
    fn digest_ignores_json_object_key_order() {
        let a = json!({"z": 1, "a": "你好"});
        let b = json!({"a": "你好", "z": 1});
        assert_eq!(canonical_digest(&a).unwrap(), canonical_digest(&b).unwrap());
    }

    #[test]
    fn python_rfc8785_work_golden_vectors() {
        let one: WorkSnapshot = serde_json::from_value(json!({
            "objective":"你好🌍","frontier":"下一步"
        }))
        .unwrap();
        assert_eq!(
            canonical_digest(&serde_json::to_value(one).unwrap()).unwrap(),
            "sha256:b7ee66968fecaa610fcace9603d3d343a545607c0d71d340f40eb4e515d6fd80"
        );
        let two: WorkSnapshot = serde_json::from_value(json!({
            "objective":"a","frontier":"b",
            "next_actions":["组合字符 e\u{301}","🙌"],
            "reference_refs":["git:revision:abc"]
        }))
        .unwrap();
        assert_eq!(
            canonical_digest(&serde_json::to_value(two).unwrap()).unwrap(),
            "sha256:1240bb2f1647f0d7e95ff92785c89106f62a71f217565da91c5b0b501dc1dc40"
        );
    }

    #[test]
    fn python_rfc8785_rejects_unsafe_json_integer() {
        assert!(canonical_digest(&json!({"expectedRevision": 9_007_199_254_740_991_i64})).is_ok());
        assert!(matches!(
            canonical_digest(&json!({"expectedRevision": 9_007_199_254_740_992_i64})),
            Err(WorkError::Invalid(_))
        ));
    }
}
