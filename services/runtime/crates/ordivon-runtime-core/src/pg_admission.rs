//! Native PostgreSQL Runtime admission contract, NOT production authority.
//! Explicitly opt-in until the full lifecycle/refinement/consumer proof exists.
use postgres::{Client, GenericClient, IsolationLevel, NoTls};
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use uuid::Uuid;

#[path = "pg_dispatch.rs"]
mod dispatch;
pub use dispatch::{PgBundleReady, PgDispatchIssued};

#[derive(Debug)]
pub enum PgAdmissionError {
    InvalidInput,
    Unqualified,
    Capacity,
    IdempotencyConflict,
    PendingEffect,
    Blocked,
    UnknownCommit,
    Database(postgres::Error),
}
impl From<postgres::Error> for PgAdmissionError {
    fn from(error: postgres::Error) -> Self {
        Self::Database(error)
    }
}

#[derive(Clone)]
pub struct PgAdmissionInput {
    pub job_id: String,
    pub attempt_id: String,
    pub reservation_id: String,
    pub principal: String,
    pub client_request_id: String,
    pub request_digest: String,
    pub operation_digest: String,
    pub workspace_id: String,
    pub workspace_snapshot_json: String,
    pub execution_plan_json: String,
    pub execution_plan_digest: String,
    pub launch_token_digest: String,
    pub bundle_path: String,
    pub unit_name: String,
    pub global_limit: i32,
    pub created_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionOutcome {
    Created(String),
    Existing(String),
}

fn exact_schema(s: &str) -> bool {
    !matches!(s, "public" | "information_schema")
        && !s.starts_with("pg_")
        && !s.is_empty()
        && s.len() <= 63
        && s.as_bytes()[0].is_ascii_alphabetic()
        && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_')
}
/// One-pass JSON admission: reject duplicate members at ANY depth, including
/// keys that become identical after JSON escape decoding. Do not retain a
/// second JSON AST; the durable typed consumers parse only after this gate.
struct JsonObjectWithUniqueKeys(bool);

impl<'de> Deserialize<'de> for JsonObjectWithUniqueKeys {
    fn deserialize<D: serde::Deserializer<'de>>(input: D) -> Result<Self, D::Error> {
        struct UniqueKeysVisitor;
        impl<'de> Visitor<'de> for UniqueKeysVisitor {
            type Value = JsonObjectWithUniqueKeys;

            fn expecting(&self, fmt: &mut std::fmt::Formatter) -> std::fmt::Result {
                write!(fmt, "a JSON value with unique object members")
            }

            fn visit_bool<E: de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_i64<E: de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_u64<E: de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_f64<E: de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_str<E: de::Error>(self, _: &str) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_string<E: de::Error>(self, _: String) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_unit<E: de::Error>(self) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Self::Value, A::Error> {
                while seq.next_element::<JsonObjectWithUniqueKeys>()?.is_some() {}
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut keys = HashSet::new();
                while let Some((key, _)) = map.next_entry::<String, JsonObjectWithUniqueKeys>()? {
                    if !keys.insert(key) {
                        return Err(de::Error::custom("duplicate JSON object member"));
                    }
                }
                Ok(JsonObjectWithUniqueKeys(true))
            }
        }
        input.deserialize_any(UniqueKeysVisitor)
    }
}

fn unambiguous_json_object(raw: &str) -> bool {
    matches!(
        serde_json::from_str::<JsonObjectWithUniqueKeys>(raw),
        Ok(JsonObjectWithUniqueKeys(true))
    )
}

impl PgAdmissionInput {
    fn validate(&self) -> Result<(), PgAdmissionError> {
        let strings = [
            &self.job_id,
            &self.attempt_id,
            &self.reservation_id,
            &self.principal,
            &self.client_request_id,
            &self.request_digest,
            &self.operation_digest,
            &self.workspace_id,
            &self.workspace_snapshot_json,
            &self.execution_plan_json,
            &self.execution_plan_digest,
            &self.launch_token_digest,
            &self.bundle_path,
            &self.unit_name,
        ];
        if strings.iter().any(|s| s.is_empty())
            || self.created_at_ms < 0
            || self.global_limit < 1
            || self.expected_source_sha256.len() != 64
            || !self
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            // Durable Runtime consumers decode both carriers as records.
            // Parsing any JSON value alone admits null/scalars/arrays that
            // cannot satisfy their existing typed source contracts.
            || !unambiguous_json_object(&self.workspace_snapshot_json)
            || !unambiguous_json_object(&self.execution_plan_json)
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        Ok(())
    }
}

/// An operator-owned epoch seal is the *same existing* _stage_control table,
/// not a second registry.  Source-only qualification can survive a PITR while
/// PostgreSQL forks a different WAL timeline and loses downstream effect IDs.
///
/// The operator stamps id='epoch', state='QUALIFIED_EPOCH', and the digest
/// calculated by this function while its qualified source/cluster/timeline
/// is current.  A missing/old epoch always refuses new effects.  The app role
/// requires SELECT on _stage_control and PUBLIC read-only pg_control functions,
/// but cannot INSERT/UPDATE the protected state or fingerprint itself.
pub fn pg_writer_epoch_digest(source: &str, system_id: &str, timeline: i32) -> String {
    let bytes = format!("ordivon-pg-writer-epoch-v1\0{source}\0{system_id}\0{timeline}");
    hex::encode(Sha256::digest(bytes.as_bytes()))
}

pub(crate) fn require_pg_writer_epoch<C: GenericClient>(
    db: &mut C,
    expected_source: &str,
    lock_for_write: bool,
) -> Result<(), PgAdmissionError> {
    let physical = db.query_one(
        "SELECT (SELECT system_identifier::text FROM pg_control_system()), \
                (SELECT timeline_id FROM pg_control_checkpoint()), \
                (SELECT left(pg_walfile_name(pg_current_wal_lsn()),8))",
        &[],
    )?;
    let system_id: String = physical.get(0);
    let timeline: i32 = physical.get(1);
    let current_wal_timeline: String = physical.get(2);
    // The control-file checkpoint may lag a promotion. If it does, refuse
    // admission rather than mistake a freshly branched WAL for the old epoch.
    if current_wal_timeline != format!("{timeline:08X}") {
        return Err(PgAdmissionError::Unqualified);
    }
    if timeline < 1 {
        return Err(PgAdmissionError::Unqualified);
    }
    let digest = pg_writer_epoch_digest(expected_source, &system_id, timeline);
    let query = if lock_for_write {
        "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='epoch' FOR SHARE"
    } else {
        "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='epoch'"
    };
    let seal = db
        .query_opt(query, &[])?
        .ok_or(PgAdmissionError::Unqualified)?;
    if seal.get::<_, String>(0) != "QUALIFIED_EPOCH"
        || seal.get::<_, String>(1) != digest
        || !seal.get::<_, bool>(2)
    {
        return Err(PgAdmissionError::Unqualified);
    }
    Ok(())
}

/// Required keys and references for the durable PG authority, not merely
/// a row-correct historical import. The native stage intentionally does not
/// assert all of these, and must not be promoted as an active write schema.
fn qualified_schema_constraints(client: &mut Client, schema: &str) -> Result<(), PgAdmissionError> {
    let rows = client.query(
        "SELECT r.relname::text,c.contype::text,ARRAY_AGG(a.attname::text ORDER BY k.ordinality), \
         COALESCE(ref_ns.nspname::text,''),COALESCE(ref_rel.relname::text,'') \
         FROM pg_catalog.pg_constraint c \
         JOIN pg_catalog.pg_class r ON r.oid=c.conrelid \
         JOIN pg_catalog.pg_namespace n ON n.oid=r.relnamespace \
         LEFT JOIN pg_catalog.pg_class ref_rel ON ref_rel.oid=c.confrelid \
         LEFT JOIN pg_catalog.pg_namespace ref_ns ON ref_ns.oid=ref_rel.relnamespace \
         JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum,ordinality) ON TRUE \
         JOIN pg_catalog.pg_attribute a ON a.attrelid=r.oid AND a.attnum=k.attnum \
         WHERE n.nspname=$1 AND c.contype IN ('p','u','f') \
           AND c.convalidated AND NOT c.condeferrable \
         GROUP BY r.relname,c.oid,c.contype,ref_ns.nspname,ref_rel.relname",
        &[&schema],
    )?;
    let actual: HashSet<(String, String, Vec<String>, String)> = rows
        .iter()
        .map(|row| {
            let ref_schema: String = row.get(3);
            let ref_table: String = row.get(4);
            (
                row.get(0),
                row.get(1),
                row.get(2),
                if ref_schema == schema {
                    ref_table
                } else {
                    String::new()
                },
            )
        })
        .collect();
    let required: &[(&str, &str, &[&str], &str)] = &[
        ("jobs", "p", &["job_id"], ""),
        ("jobs", "u", &["principal", "client_request_id"], ""),
        ("attempts", "p", &["attempt_id"], ""),
        ("attempts", "u", &["job_id", "attempt_number"], ""),
        ("attempts", "f", &["job_id"], "jobs"),
        (
            "idempotency_keys",
            "p",
            &["principal", "client_request_id"],
            "",
        ),
        ("idempotency_keys", "u", &["job_id"], ""),
        ("idempotency_keys", "f", &["job_id"], "jobs"),
        ("concurrency_reservations", "p", &["reservation_id"], ""),
        ("concurrency_reservations", "u", &["attempt_id"], ""),
        ("concurrency_reservations", "f", &["attempt_id"], "attempts"),
        ("job_events", "p", &["event_id"], ""),
        ("job_events", "u", &["job_id", "event_sequence"], ""),
        ("job_events", "f", &["job_id"], "jobs"),
        ("job_events", "f", &["attempt_id"], "attempts"),
        ("artifacts", "p", &["artifact_id"], ""),
        ("job_runtime_release_effects", "p", &["job_id"], ""),
        ("job_runtime_release_effects", "u", &["effect_id"], ""),
        ("job_runtime_release_effects", "f", &["job_id"], "jobs"),
        (
            "artifacts",
            "u",
            &["attempt_id", "kind", "relative_path"],
            "",
        ),
        ("artifacts", "f", &["job_id"], "jobs"),
        ("artifacts", "f", &["attempt_id"], "attempts"),
        ("_stage_control", "p", &["id"], ""),
    ];
    if required.iter().any(|(table, kind, columns, target)| {
        !actual.contains(&(
            (*table).to_owned(),
            (*kind).to_owned(),
            columns.iter().map(|name| (*name).to_owned()).collect(),
            (*target).to_owned(),
        ))
    }) {
        return Err(PgAdmissionError::Unqualified);
    }
    Ok(())
}

pub struct PgAdmissionStore {
    pub(crate) client: Client,
}
impl PgAdmissionStore {
    pub fn connect(dsn: &str, schema: &str) -> Result<Self, PgAdmissionError> {
        if !exact_schema(schema) {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut client = Client::connect(dsn, NoTls)?;
        client.query_one(
            "SELECT set_config('search_path',$1,false)",
            &[&format!("\"{schema}\"")],
        )?;
        let actual: Option<String> = client.query_one("SELECT current_schema()", &[])?.get(0);
        if actual.as_deref() != Some(schema) {
            return Err(PgAdmissionError::Unqualified);
        }
        qualified_schema_constraints(&mut client, schema)?;
        Ok(Self { client })
    }

    /// One atomic admission. No dispatch/terminal/repair effect is authorized.
    pub fn admit(&mut self, i: &PgAdmissionInput) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        i.validate()?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Serialize the global+per-Workspace capacity predicates and replay.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE", &[]
        )?;
        let Some(authority) = authority else {
            return Err(PgAdmissionError::Unqualified);
        };
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        if let Some(row) = tx.query_opt(
            "SELECT k.job_id,j.request_digest FROM idempotency_keys k \
             JOIN jobs j ON j.job_id=k.job_id AND j.principal=k.principal \
                AND j.client_request_id=k.client_request_id \
                AND j.operation_digest=k.operation_digest \
             WHERE k.principal=$1 AND k.client_request_id=$2",
            &[&i.principal, &i.client_request_id],
        )? {
            let job_id: String = row.get(0);
            let request_digest: String = row.get(1);
            // Exact replay binds the proposal, not current Workspace bytes,
            // resolved plan, or provider identity. Those facts belong to
            // the original committed Operation, not this second admission.
            if request_digest != i.request_digest {
                return Err(PgAdmissionError::IdempotencyConflict);
            }
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgAdmissionOutcome::Existing(job_id));
        }
        // This predicate fences new writer effects, not read-only replay of a
        // previously committed identity. Resolving the exact idempotency key
        // must precede transient pending-Effect and capacity admission gates.
        let pending:bool=tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects r JOIN jobs j ON j.job_id=r.job_id WHERE j.resolution IS NULL OR EXISTS(SELECT 1 FROM attempts a JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id WHERE a.job_id=j.job_id AND c.state IN ('active','held_orphaned')))",&[])?.get(0);
        if pending {
            return Err(PgAdmissionError::PendingEffect);
        }
        let workspace_count:i64=tx.query_one(
            "SELECT count(*) FROM concurrency_reservations r JOIN attempts a ON a.attempt_id=r.attempt_id JOIN jobs j ON j.job_id=a.job_id WHERE r.state IN ('active','held_orphaned') AND j.workspace_id=$1",
            &[&i.workspace_id])?.get(0);
        let global_count:i64=tx.query_one(
            "SELECT count(*) FROM concurrency_reservations WHERE state IN ('active','held_orphaned')",&[])?.get(0);
        if workspace_count >= 1 || global_count >= i64::from(i.global_limit) {
            return Err(PgAdmissionError::Capacity);
        }
        tx.execute(
            "INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution,current_attempt_id,row_version) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'run',NULL,NULL,0)",
            &[&i.job_id,&i.principal,&i.client_request_id,&i.request_digest,&i.operation_digest,
              &i.workspace_id,&i.workspace_snapshot_json,&i.execution_plan_json,
              &i.execution_plan_digest,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,1,'accepted','natural',$3,$4,$5,$6,0)",
            &[&i.attempt_id,&i.job_id,&i.launch_token_digest,&i.bundle_path,&i.unit_name,&i.created_at_ms])?;
        tx.execute(
            "UPDATE jobs SET current_attempt_id=$1 WHERE job_id=$2",
            &[&i.attempt_id, &i.job_id],
        )?;
        tx.execute(
            "INSERT INTO idempotency_keys(principal,client_request_id,operation_digest,job_id,created_at_ms) VALUES($1,$2,$3,$4,$5)",
            &[&i.principal,&i.client_request_id,&i.operation_digest,&i.job_id,&i.created_at_ms])?;
        tx.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&i.reservation_id,&i.attempt_id,&i64::from(i.global_limit),&i.created_at_ms])?;
        let events = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (idx, (event_type, reason, next_state, detail)) in events.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,'SYSTEM_DERIVED',NULL,$6,$7,$8,$9,$10)",
                &[&format!("event-{}",Uuid::now_v7()),&i.job_id,&i.attempt_id,
                  &((idx+1) as i64),event_type,next_state,reason,&encoded,&digest,&i.created_at_ms])?;
        }
        // A failed COMMIT is UNKNOWN, not a retryable assertion of no effect.
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionOutcome::Created(i.job_id.clone()))
    }
}

/// Read-only witness for a potentially committed admission whose response was lost.
///
/// Inconclusive is deliberately NOT equivalent to "the write did not commit".
/// The witness binds the exact submitted identity, its initial Attempt and
/// capacity reservation, and all three admission events. It does not assert
/// dispatch, runner activity, terminal completion, or installed PG authority.
#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionObservation {
    Confirmed(String),
    Inconclusive,
}

impl PgAdmissionStore {
    pub fn observe_admission(
        &mut self,
        i: &PgAdmissionInput,
    ) -> Result<PgAdmissionObservation, PgAdmissionError> {
        i.validate()?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;

        // A key by itself is insufficient: require the original immutable Job,
        // first Attempt and capacity reservation to be mutually consistent.
        // Mutable lifecycle/desired-state columns must NOT be pinned to their
        // initial values: the original admission stays true after progression.
        let row = tx.query_opt(
            "SELECT j.job_id,j.request_digest,j.operation_digest,j.workspace_id, \
                    j.workspace_snapshot_json,j.execution_plan_json,j.execution_plan_digest, \
                    j.created_at_ms,a.attempt_id,a.attempt_number,a.launch_token_digest, \
                    a.bundle_path,a.unit_name,a.created_at_ms, \
                    r.reservation_id,r.global_limit,r.acquired_at_ms \
             FROM idempotency_keys k \
             JOIN jobs j ON j.job_id=k.job_id AND j.principal=k.principal \
                AND j.client_request_id=k.client_request_id \
             JOIN attempts a ON a.job_id=j.job_id AND a.attempt_number=1 \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
             WHERE k.principal=$1 AND k.client_request_id=$2 \
                AND k.operation_digest=j.operation_digest",
            &[&i.principal, &i.client_request_id],
        )?;
        let Some(row) = row else {
            return Ok(PgAdmissionObservation::Inconclusive);
        };
        let matches = row.get::<_, String>(0) == i.job_id
            && row.get::<_, String>(1) == i.request_digest
            && row.get::<_, String>(2) == i.operation_digest
            && row.get::<_, String>(3) == i.workspace_id
            && row.get::<_, String>(4) == i.workspace_snapshot_json
            && row.get::<_, String>(5) == i.execution_plan_json
            && row.get::<_, String>(6) == i.execution_plan_digest
            && row.get::<_, i64>(7) == i.created_at_ms
            && row.get::<_, String>(8) == i.attempt_id
            && row.get::<_, i64>(9) == 1
            && row.get::<_, String>(10) == i.launch_token_digest
            && row.get::<_, String>(11) == i.bundle_path
            && row.get::<_, String>(12) == i.unit_name
            && row.get::<_, i64>(13) == i.created_at_ms
            && row.get::<_, String>(14) == i.reservation_id
            && row.get::<_, i64>(15) == i64::from(i.global_limit)
            && row.get::<_, i64>(16) == i.created_at_ms;
        if !matches {
            return Ok(PgAdmissionObservation::Inconclusive);
        }

        let rows = tx.query(
            "SELECT event_sequence,event_type,origin,previous_state,new_state, \
                    reason_code,detail_json,detail_digest,observed_at_ms,attempt_id \
             FROM job_events WHERE job_id=$1 AND event_sequence BETWEEN 1 AND 3 \
             ORDER BY event_sequence",
            &[&i.job_id],
        )?;
        if rows.len() != 3 {
            return Ok(PgAdmissionObservation::Inconclusive);
        }
        let expected = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (index, (row, (event_type, reason, new_state, detail))) in
            rows.iter().zip(expected.iter()).enumerate()
        {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            if row.get::<_, i64>(0) != (index + 1) as i64
                || row.get::<_, String>(1) != *event_type
                || row.get::<_, String>(2) != "SYSTEM_DERIVED"
                || row.get::<_, Option<String>>(3).is_some()
                || row.get::<_, Option<String>>(4).as_deref() != *new_state
                || row.get::<_, String>(5) != *reason
                || row.get::<_, String>(6) != encoded
                || row.get::<_, String>(7) != digest
                || row.get::<_, i64>(8) != i.created_at_ms
                || row.get::<_, Option<String>>(9).as_deref() != Some(i.attempt_id.as_str())
            {
                return Ok(PgAdmissionObservation::Inconclusive);
            }
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionObservation::Confirmed(i.job_id.clone()))
    }
}

#[derive(Clone)]
pub struct PgTerminalNoArtifacts {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub terminal_state: String,
    pub result_digest: String,
    pub reason_code: String,
    pub exit_code: Option<i32>,
    pub finished_at_ms: i64,
    pub expected_source_sha256: String,
}
#[derive(Debug, PartialEq, Eq)]
pub enum PgTerminalOutcome {
    Committed(String),
    Existing(String),
}

/// PG only commits metadata; physical bytes must be validated by the Runner.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PgArtifactRegistration {
    pub artifact_id: String,
    pub kind: String,
    pub relative_path: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: i64,
    pub truncated: bool,
    pub created_at_ms: i64,
}
pub(crate) fn pg_artifact_manifest_digest(artifacts: &[PgArtifactRegistration]) -> String {
    let mut ordered = artifacts.to_vec();
    ordered.sort_by(|a, b| a.artifact_id.cmp(&b.artifact_id));
    let manifest: Vec<_> = ordered
        .iter()
        .map(|a| {
            serde_json::json!({
                "artifactId":a.artifact_id, "kind":a.kind, "relativePath":a.relative_path,
                "digest":a.digest, "mediaType":a.media_type,"byteLength":a.byte_length,
                "truncated":a.truncated, "createdAtMs":a.created_at_ms
            })
        })
        .collect();
    let bytes = serde_json::to_vec(&manifest).expect("bounded Artifact manifest is JSON");
    format!("sha256:{}", hex::encode(Sha256::digest(&bytes)))
}
pub(crate) fn valid_pg_artifacts(artifacts: &[PgArtifactRegistration]) -> bool {
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    artifacts.iter().all(|a| {
        !a.artifact_id.is_empty()
            && !a.kind.is_empty()
            && !a.media_type.is_empty()
            && a.media_type.len() <= 256
            && a.byte_length >= 0
            && a.created_at_ms >= 0
            && a.digest.starts_with("sha256:")
            && a.digest.len() == 71
            && a.digest[7..].bytes().all(|b| b.is_ascii_hexdigit())
            && !a.relative_path.is_empty()
            && !a.relative_path.starts_with('/')
            && !a.relative_path.contains('\\')
            && !a
                .relative_path
                .split('/')
                .any(|p| p == ".." || p.is_empty())
            && ids.insert(a.artifact_id.as_str())
            && paths.insert((a.kind.as_str(), a.relative_path.as_str()))
    })
}
fn terminal_transition(from: &str, to: &str) -> bool {
    match from {
        "accepted" => matches!(to, "cancelled" | "failed" | "lost" | "orphaned"),
        "starting" | "running" | "stopping" | "recovering" => matches!(
            to,
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ),
        _ => false,
    }
}
#[cfg(kani)]
mod kani_transition_proofs {
    use super::terminal_transition;

    #[kani::proof]
    fn proof_pg_terminal_transition_matches_contract() {
        let from_id: u8 = kani::any();
        let to_id: u8 = kani::any();
        kani::assume(from_id < 12 && to_id < 12);
        let state = |id: u8| match id {
            0 => "accepted",
            1 => "starting",
            2 => "running",
            3 => "stopping",
            4 => "recovering",
            5 => "succeeded",
            6 => "failed",
            7 => "timed_out",
            8 => "cancelled",
            9 => "lost",
            10 => "orphaned",
            _ => "unqualified",
        };
        // Independent, finite contract for the declared runtime state alphabet.
        let expected = match from_id {
            0 => matches!(to_id, 6 | 8 | 9 | 10),
            1..=4 => matches!(to_id, 5..=10),
            _ => false,
        };
        assert_eq!(terminal_transition(state(from_id), state(to_id)), expected);
    }
}

impl PgAdmissionStore {
    /// Exact no-Artifact terminal/Job/reservation/event atomicity, no runner or
    /// external output effect. Arbitrary Artifact-bearing terminal commits are
    /// deliberately unsupported until a complete consumer-owned transaction.
    pub fn commit_terminal_no_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        self.commit_terminal_artifacts_impl(i, &[])
    }
    pub fn commit_terminal_with_artifacts(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if artifacts.is_empty() {
            return Err(PgAdmissionError::InvalidInput);
        }
        self.commit_terminal_artifacts_impl(i, artifacts)
    }
    fn commit_terminal_artifacts_impl(
        &mut self,
        i: &PgTerminalNoArtifacts,
        artifacts: &[PgArtifactRegistration],
    ) -> Result<PgTerminalOutcome, PgAdmissionError> {
        if !valid_pg_artifacts(artifacts) {
            return Err(PgAdmissionError::InvalidInput);
        }
        if i.attempt_id.is_empty()
            || i.result_digest.is_empty()
            || i.reason_code.is_empty()
            || i.finished_at_ms < 0
            || i.expected_row_version < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            || !matches!(
                i.terminal_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
            )
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let auth=tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",&[])?;
        let Some(auth) = auth else {
            return Err(PgAdmissionError::Unqualified);
        };
        let status: String = auth.get(0);
        let seal: String = auth.get(1);
        let permitted: bool = auth.get(2);
        if status != "QUALIFIED_WRITER" || !permitted || seal != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        let current=tx.query_opt(
            "SELECT job_id,state,result_digest,row_version FROM attempts WHERE attempt_id=$1 FOR UPDATE",
            &[&i.attempt_id])?.ok_or(PgAdmissionError::InvalidInput)?;
        let job_id: String = current.get(0);
        let previous: String = current.get(1);
        let digest: Option<String> = current.get(2);
        let version: i64 = current.get(3);
        let job = tx.query_one(
            "SELECT resolution,current_attempt_id FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&job_id],
        )?;
        let job_resolution: Option<String> = job.get(0);
        let current_attempt: Option<String> = job.get(1);
        let existing = tx.query(
            "SELECT artifact_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE attempt_id=$1 ORDER BY artifact_id",
            &[&i.attempt_id],
        )?;
        if artifacts.is_empty() && !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        let mut sorted = artifacts.to_vec();
        sorted.sort_by(|a, b| a.artifact_id.cmp(&b.artifact_id));
        let same_artifacts = existing.len() == sorted.len()
            && existing.iter().zip(&sorted).all(|(row, a)| {
                row.get::<_, String>(0) == a.artifact_id
                    && row.get::<_, String>(1) == a.kind
                    && row.get::<_, String>(2) == a.relative_path
                    && row.get::<_, String>(3) == a.digest
                    && row.get::<_, String>(4) == a.media_type
                    && row.get::<_, i64>(5) == a.byte_length
                    && row.get::<_, bool>(6) == a.truncated
                    && row.get::<_, i64>(7) == a.created_at_ms
            });
        if matches!(
            previous.as_str(),
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ) {
            if previous == i.terminal_state
                && digest.as_deref() == Some(&i.result_digest)
                && job_resolution.as_deref() == Some(&i.terminal_state)
                && same_artifacts
            {
                tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
                return Ok(PgTerminalOutcome::Existing(job_id));
            }
            return Err(PgAdmissionError::IdempotencyConflict);
        }
        if !existing.is_empty() {
            return Err(PgAdmissionError::Blocked);
        }
        // The Job's current Attempt is the only Attempt allowed to commit a
        // fresh terminal effect. A superseded Attempt may not resolve the Job,
        // release another Attempt's capacity, or append terminal events.
        // Completed exact replay above remains legal after the Job clears
        // current_attempt_id.
        if current_attempt.as_deref() != Some(i.attempt_id.as_str()) {
            return Err(PgAdmissionError::Blocked);
        }
        if version != i.expected_row_version
            || !terminal_transition(&previous, &i.terminal_state)
            || job_resolution.is_some()
        {
            return Err(PgAdmissionError::Blocked);
        }
        let changed=tx.execute(
            "UPDATE attempts SET state=$1,result_digest=$2,exit_code=$3,finished_at_ms=$4,row_version=row_version+1 WHERE attempt_id=$5 AND row_version=$6 AND state=$7",
            &[&i.terminal_state,&i.result_digest,&i.exit_code,&i.finished_at_ms,
              &i.attempt_id,&i.expected_row_version,&previous])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        for a in artifacts {
            tx.execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                &[&a.artifact_id,&job_id,&i.attempt_id,&a.kind,&a.relative_path,
                &a.digest,&a.media_type,&a.byte_length,&a.truncated,&a.created_at_ms],
            )?;
        }
        if i.terminal_state == "orphaned" {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='held_orphaned',release_reason=$1,state_observed_at_ms=$2 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.reason_code,&i.finished_at_ms,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        } else {
            let count=tx.execute(
                "UPDATE concurrency_reservations SET state='released',released_at_ms=$1,release_reason=$2,state_observed_at_ms=$1 WHERE attempt_id=$3 AND state IN ('active','held_orphaned')",
                &[&i.finished_at_ms,&i.reason_code,&i.attempt_id])?;
            if count != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        let changed=tx.execute(
            "UPDATE jobs SET resolution=$1,current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=$2 AND resolution IS NULL",
            &[&i.terminal_state,&job_id])?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let start: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&job_id],
            )?
            .get(0);
        let items = [
            (
                "PROCESS_EXITED",
                "SYSTEM_OBSERVED",
                if artifacts.is_empty() {
                    serde_json::json!({"resultDigest":i.result_digest,"exitCode":i.exit_code})
                } else {
                    serde_json::json!({
                        "resultDigest":i.result_digest,
                        "exitCode":i.exit_code,
                        "artifactSetDigest":pg_artifact_manifest_digest(artifacts)
                    })
                },
            ),
            (
                "JOB_TERMINAL",
                "SYSTEM_DERIVED",
                serde_json::json!({"resolution":i.terminal_state}),
            ),
        ];
        for (n, (event_type, origin, detail)) in items.iter().enumerate() {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            tx.execute(
                "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
                &[&format!("event-{}",Uuid::now_v7()),&job_id,&i.attempt_id,
                  &(start+n as i64),event_type,origin,&previous,&i.terminal_state,
                  &i.reason_code,&encoded,&digest,&i.finished_at_ms])?;
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgTerminalOutcome::Committed(job_id))
    }
}

#[derive(Clone)]
pub struct PgCancelIntent {
    pub job_id: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgCancelOutcome {
    IntentRecorded(String),
    Existing(String),
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgCancelObservation {
    Confirmed(String),
    Inconclusive,
}

fn cancel_detail(i: &PgCancelIntent) -> String {
    // The original cancel timestamp is part of the immutable request identity
    // used for reconciliation after an ambiguous COMMIT.
    let identity = format!(
        "pg-cancel-intent\\0{}\\0{}\\0{}",
        i.expected_source_sha256, i.job_id, i.observed_at_ms
    );
    let digest = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(identity.as_bytes()))
    );
    serde_json::json!({"cancelIntentDigest":digest}).to_string()
}

impl PgAdmissionStore {
    /// Persist only a cancel/stop intent. Do not infer that a runner has
    /// stopped, release capacity, or resolve an accepted Job without an
    /// independently observed dispatch fence and terminal receipt.
    pub fn request_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelOutcome, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }

        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Same serialization boundary as admission and terminal CAS.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;

        let job = tx.query_opt(
            "SELECT resolution,desired_state,current_attempt_id FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&i.job_id],
        )?.ok_or(PgAdmissionError::InvalidInput)?;
        let resolution: Option<String> = job.get(0);
        let desired: String = job.get(1);
        let current_attempt: Option<String> = job.get(2);

        if resolution.is_some() && resolution.as_deref() != Some("orphaned") {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        let attempt_id = if resolution.as_deref() == Some("orphaned") {
            // A resolved orphan has no current_attempt_id; use the latest
            // durable Attempt and prove the reservation is still held.
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.ok_or(PgAdmissionError::Blocked)?.get::<_, String>(0)
        } else {
            current_attempt.ok_or(PgAdmissionError::Blocked)?
        };
        let attempt = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2 FOR UPDATE",
            &[&attempt_id,&i.job_id],
        )?.ok_or(PgAdmissionError::Blocked)?;
        let previous: String = attempt.get(0);
        let stop_intent: String = attempt.get(1);

        // Never treat a lifecycle projection alone as evidence that a
        // stopped/terminal attempt released its real capacity.
        let reservation = tx
            .query_opt(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1 FOR UPDATE",
                &[&attempt_id],
            )?
            .ok_or(PgAdmissionError::Blocked)?;
        let reservation_state: String = reservation.get(0);
        let is_orphan = resolution.as_deref() == Some("orphaned");
        if is_orphan {
            if previous != "orphaned" || reservation_state != "held_orphaned" {
                return Err(PgAdmissionError::Blocked);
            }
        } else if !matches!(
            previous.as_str(),
            "accepted" | "starting" | "running" | "recovering" | "stopping"
        ) || reservation_state != "active"
        {
            return Err(PgAdmissionError::Blocked);
        }

        if desired == "cancelled"
            && stop_intent == "stop_requested"
            && (is_orphan || matches!(previous.as_str(), "accepted" | "stopping"))
        {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        if !matches!(desired.as_str(), "run" | "cancelled")
            || !matches!(stop_intent.as_str(), "natural" | "stop_requested")
        {
            return Err(PgAdmissionError::Blocked);
        }

        // First record the Job intent, even when its Attempt has not yet
        // started. An accepted Attempt stays accepted until dispatch fencing
        // and terminal ownership prove that early cancellation completed.
        if desired != "cancelled" {
            let changed = tx.execute(
                "UPDATE jobs SET desired_state='cancelled',row_version=row_version+1 WHERE job_id=$1 AND desired_state='run'",
                &[&i.job_id],
            )?;
            if changed != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        let next_state = if matches!(previous.as_str(), "starting" | "running" | "recovering") {
            "stopping"
        } else {
            previous.as_str()
        };
        let changed = tx.execute(
            "UPDATE attempts SET state=$1,termination_intent='stop_requested',row_version=row_version+1 WHERE attempt_id=$2 AND state=$3 AND termination_intent=$4",
            &[&next_state,&attempt_id,&previous,&stop_intent],
        )?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let next_sequence: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&i.job_id],
            )?
            .get(0);
        let reason = if is_orphan {
            "ORPHAN_CANCEL_INTENT_COMMITTED"
        } else if previous == "accepted" {
            "CANCEL_INTENT_AWAITING_DISPATCH_FENCE"
        } else {
            "CANCEL_INTENT_COMMITTED"
        };
        let detail = cancel_detail(i);
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        tx.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,'STOP_REQUESTED','SYSTEM_DERIVED',$5,$6,$7,$8,$9,$10)",
            &[&format!("event-{}", Uuid::now_v7()),&i.job_id,&attempt_id,&next_sequence,
                &previous,&next_state,&reason,&detail,&digest,&i.observed_at_ms],
        )?;
        // No capacity release, no resolved Job, no runner side effects.
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelOutcome::IntentRecorded(i.job_id.clone()))
    }
}

impl PgAdmissionStore {
    /// Reconcile a lost COMMIT acknowledgement using a NEW qualified PG
    /// connection. Only an exact durable STOP_REQUESTED event plus coherent
    /// Job/Attempt/Reservation state proves this particular cancel intent.
    /// Absence is INCONCLUSIVE, never proof that a mutation did not commit.
    pub fn observe_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelObservation, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;
        let Some(job) = tx.query_opt(
            "SELECT desired_state,resolution,current_attempt_id FROM jobs WHERE job_id=$1",
            &[&i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let desired: String = job.get(0);
        let resolution: Option<String> = job.get(1);
        let current_attempt: Option<String> = job.get(2);
        if desired != "cancelled" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let attempt_id = if resolution.is_some() {
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.map(|row| row.get::<_, String>(0))
        } else {
            current_attempt
        };
        let Some(attempt_id) = attempt_id else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2",
            &[&attempt_id, &i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let attempt_state: String = attempt.get(0);
        let intent: String = attempt.get(1);
        if intent != "stop_requested" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let reservation_state: String = reservation.get(0);
        let coherent = if resolution.as_deref() == Some("orphaned") {
            attempt_state == "orphaned" && reservation_state == "held_orphaned"
        } else if resolution.is_some() {
            matches!(
                attempt_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost"
            ) && reservation_state == "released"
        } else {
            matches!(attempt_state.as_str(), "accepted" | "stopping")
                && reservation_state == "active"
        };
        if !coherent {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let detail = cancel_detail(i);
        let event_digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        let event_exists: bool = tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type='STOP_REQUESTED' AND origin='SYSTEM_DERIVED' AND detail_digest=$3 AND detail_json=$4 AND observed_at_ms=$5 AND reason_code IN ('CANCEL_INTENT_AWAITING_DISPATCH_FENCE','CANCEL_INTENT_COMMITTED','ORPHAN_CANCEL_INTENT_COMMITTED'))",
            &[&i.job_id,&attempt_id,&event_digest,&detail,&i.observed_at_ms],
        )?.get(0);
        if !event_exists {
            return Ok(PgCancelObservation::Inconclusive);
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelObservation::Confirmed(i.job_id.clone()))
    }
}

#[cfg(test)]
mod tests {

    #[test]
    fn physical_epoch_fingerprint_is_domain_and_timeline_bound() {
        let source = "a".repeat(64);
        let previous = pg_writer_epoch_digest(&source, "77123", 1);
        assert_eq!(previous.len(), 64);
        assert_ne!(previous, pg_writer_epoch_digest(&source, "77123", 2));
        assert_ne!(previous, pg_writer_epoch_digest(&source, "77124", 1));
        assert_ne!(
            previous,
            pg_writer_epoch_digest(&"b".repeat(64), "77123", 1)
        );
        assert_eq!(previous, pg_writer_epoch_digest(&source, "77123", 1));
    }

    use super::*;
    #[test]
    fn schema_boundary_fails_closed() {
        for name in ["", "public", "pg_catalog", "_secret", "x;DROP SCHEMA"] {
            assert!(!exact_schema(name), "unsafe {name}");
        }
        assert!(exact_schema("runtime_pg_qualified_r1"));
    }
    #[test]
    fn non_object_durable_json_is_rejected_before_postgres_effects() {
        // RuntimeExecutionPlan and Workspace snapshots are records. Parsing as
        // arbitrary JSON Value would accept a scalar/array that a consumer
        // cannot decode as a valid durable state object.
        let qualified = PgAdmissionInput {
            job_id: "job".into(),
            attempt_id: "attempt".into(),
            reservation_id: "reservation".into(),
            principal: "principal".into(),
            client_request_id: "request".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: "a".repeat(64),
        };
        assert!(qualified.validate().is_ok(), "fixture must be admitted");
        for raw in ["null", "true", "false", "[]", "42", "\"text\""] {
            let mut invalid_snapshot = qualified.clone();
            invalid_snapshot.workspace_snapshot_json = raw.into();
            assert!(
                matches!(
                    invalid_snapshot.validate(),
                    Err(PgAdmissionError::InvalidInput)
                ),
                "workspace_snapshot_json accepted non-object {raw}"
            );
            let mut invalid_plan = qualified.clone();
            invalid_plan.execution_plan_json = raw.into();
            assert!(
                matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
                "execution_plan_json accepted non-object {raw}"
            );
        }
    }

    #[test]
    fn duplicate_nested_json_keys_are_rejected_before_durable_pg_effects() {
        let qualified = PgAdmissionInput {
            job_id: "job".into(),
            attempt_id: "attempt".into(),
            reservation_id: "reservation".into(),
            principal: "principal".into(),
            client_request_id: "request".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: r#"{"snapshot":{"revision":1}}"#.into(),
            execution_plan_json: r#"{"plan":{"timeoutMs":1000}}"#.into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: "a".repeat(64),
        };
        assert!(
            qualified.validate().is_ok(),
            "ordinary nested objects qualify"
        );
        for raw in [
            r#"{"revision":1,"revision":2}"#,
            r#"{"snapshot":{"revision":1,"revision":2}}"#,
            r#"{"snapshots":[{"revision":1,"revision":2}]}"#,
            r#"{"\u0061":1,"a":2}"#,
        ] {
            let mut invalid_snapshot = qualified.clone();
            invalid_snapshot.workspace_snapshot_json = raw.into();
            assert!(
                matches!(
                    invalid_snapshot.validate(),
                    Err(PgAdmissionError::InvalidInput)
                ),
                "workspace_snapshot_json admitted ambiguous JSON {raw}"
            );
            let mut invalid_plan = qualified.clone();
            invalid_plan.execution_plan_json = raw.into();
            assert!(
                matches!(invalid_plan.validate(), Err(PgAdmissionError::InvalidInput)),
                "execution_plan_json admitted ambiguous JSON {raw}"
            );
        }
    }

    #[test]
    fn source_identity_must_be_present() {
        let i = PgAdmissionInput {
            job_id: "j".into(),
            attempt_id: "a".into(),
            reservation_id: "r".into(),
            principal: "p".into(),
            client_request_id: "c".into(),
            request_digest: "sha256:r".into(),
            operation_digest: "sha256:o".into(),
            workspace_id: "ws".into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:plan".into(),
            launch_token_digest: "sha256:l".into(),
            bundle_path: "/tmp/test".into(),
            unit_name: "unit".into(),
            global_limit: 1,
            created_at_ms: 1,
            expected_source_sha256: String::new(),
        };
        assert!(matches!(i.validate(), Err(PgAdmissionError::InvalidInput)));
    }
}

#[cfg(all(test, feature = "postgres-registry-admission"))]
mod live_pg_tests {
    use super::*;
    use std::sync::{Arc, Barrier};
    use std::thread;

    fn physical_pg_test_dsn() -> String {
        std::env::var("ORDIVON_PG_TEST_DSN").expect(
            "physical PostgreSQL tests require ORDIVON_PG_TEST_DSN; run the dedicated mise task",
        )
    }

    fn historical_pg_stage_test_dsn() -> String {
        std::env::var("ORDIVON_PG_STAGE_TEST_DSN").expect(
            "historical stage qualification requires ORDIVON_PG_STAGE_TEST_DSN; run the dedicated stage task",
        )
    }

    // An operator supplies an isolated PostgreSQL DSN for physical tests.
    // No environment value means the ordinary CI suite never mutates PG.
    const SCHEMA: &str = include_str!("../sql/pg_fresh_epoch.sql");

    struct Scratch {
        admin: Client,
        name: String,
    }
    impl Scratch {
        fn new(dsn: &str) -> Self {
            let name = format!("test_admit_{}", Uuid::now_v7().simple());
            let mut admin = Client::connect(dsn, NoTls).expect("test PG18 connection");
            admin
                .batch_execute(&format!("CREATE SCHEMA \"{name}\""))
                .expect("private test schema");
            admin
                .query_one(
                    "SELECT set_config('search_path',$1,false)",
                    &[&format!("\"{name}\"")],
                )
                .expect("test-only search path");
            admin
                .batch_execute(SCHEMA)
                .expect("native PG fixture constraints");
            admin
                .execute(
                    "INSERT INTO _stage_control VALUES('source','VERIFIED_NON_AUTHORITY',$1,false)",
                    &[&"a".repeat(64)],
                )
                .expect("non-authority fixture");
            Self { admin, name }
        }
        fn qualify(&mut self) {
            self.admin.execute(
                "UPDATE _stage_control SET state='QUALIFIED_WRITER',promotion_allowed=true WHERE id='source'",
                &[]
            ).expect("test-only synthetic qualifier");
            let pg = self.admin.query_one(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()),                         (SELECT timeline_id FROM pg_control_checkpoint())",
                &[],
            ).expect("native physical PostgreSQL epoch");
            let digest = pg_writer_epoch_digest(
                &"a".repeat(64),
                &pg.get::<_, String>(0),
                pg.get::<_, i32>(1),
            );
            self.admin.execute(
                "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)                  ON CONFLICT(id) DO UPDATE SET state='QUALIFIED_EPOCH',source_sha256=EXCLUDED.source_sha256,promotion_allowed=true",
                &[&digest],
            ).expect("operator-owned epoch fixture");
        }
        fn count(&mut self, table: &str) -> i64 {
            self.admin
                .query_one(&format!("SELECT count(*) FROM {table}"), &[])
                .unwrap()
                .get(0)
        }
    }
    impl Drop for Scratch {
        fn drop(&mut self) {
            // A dedicated scratch namespace, never an installed Runtime
            // schema; do not retain test effects across test runs.
            let _ = self.admin.batch_execute(&format!(
                "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
                self.name
            ));
        }
    }
    fn payload(client_key: &str, job: &str, workspace: &str, cap: i32) -> PgAdmissionInput {
        PgAdmissionInput {
            job_id: job.to_string(),
            attempt_id: format!("attempt-{job}"),
            reservation_id: format!("reservation-{job}"),
            principal: "pg-native-test".into(),
            client_request_id: client_key.to_string(),
            request_digest: format!("sha256:request-{client_key}"),
            operation_digest: format!("sha256:operation-{client_key}"),
            workspace_id: workspace.into(),
            workspace_snapshot_json: "{}".into(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: "sha256:test-plan".into(),
            launch_token_digest: "sha256:launch".into(),
            bundle_path: "/nonproduction/pg-test".into(),
            unit_name: format!("{job}.service"),
            global_limit: cap,
            created_at_ms: 1234567,
            expected_source_sha256: "a".repeat(64),
        }
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_synthetic_writer_without_event_sequence_uniqueness() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
        scratch
            .admin
            .batch_execute(
                "ALTER TABLE job_events DROP CONSTRAINT job_events_job_id_event_sequence_key",
            )
            .expect("test-only weakened catalog");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_foreign_key_that_points_at_wrong_pg_target() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &scratch.name).is_ok());
        scratch
            .admin
            .batch_execute(
                "CREATE TABLE unrelated_jobs(job_id text PRIMARY KEY);
             ALTER TABLE attempts DROP CONSTRAINT attempts_job_id_fkey;
             ALTER TABLE attempts ADD CONSTRAINT attempts_job_id_fkey
               FOREIGN KEY(job_id) REFERENCES unrelated_jobs(job_id)",
            )
            .expect("test-only misdirected foreign key");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &scratch.name),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_rejects_shallow_release_and_artifact_owner_constraints() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut release = Scratch::new(&dsn);
        release.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &release.name).is_ok());
        release.admin.batch_execute(
            "ALTER TABLE job_runtime_release_effects DROP CONSTRAINT job_runtime_release_effects_effect_id_key"
        ).expect("test-only weakened release uniqueness");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &release.name),
            Err(PgAdmissionError::Unqualified)
        ));

        let mut artifact = Scratch::new(&dsn);
        artifact.qualify();
        assert!(PgAdmissionStore::connect(&dsn, &artifact.name).is_ok());
        artifact
            .admin
            .batch_execute(
                "ALTER TABLE artifacts DROP CONSTRAINT artifacts_attempt_id_kind_relative_path_key",
            )
            .expect("test-only weakened artifact uniqueness");
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, &artifact.name),
            Err(PgAdmissionError::Unqualified)
        ));
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_native_atomic_admission_replay_fence_and_rollback() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("request-A", "job-A", "workspace-A", 2);
        assert!(matches!(
            store.admit(&a),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("jobs"), 0, "no write before PG qualification");
        scratch.qualify();
        for (name, raw) in [
            ("workspace", "null"),
            ("plan", "[]"),
            ("workspace", r#"{"revision":1,"revision":2}"#),
            ("plan", r#"{"plan":{"timeoutMs":1000,"timeoutMs":2000}}"#),
            ("workspace", r#"{"nested":[{"a":1,"a":2}]}"#),
        ] {
            let mut invalid = a.clone();
            if name == "workspace" {
                invalid.workspace_snapshot_json = raw.into();
            } else {
                invalid.execution_plan_json = raw.into();
            }
            assert!(matches!(
                store.admit(&invalid),
                Err(PgAdmissionError::InvalidInput)
            ));
            assert_eq!(scratch.count("jobs"), 0, "invalid JSON persisted a PG Job");
        }
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created("job-A".into())
        );
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Existing("job-A".into())
        );
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        // A previously committed idempotency key is a read-only observation.
        // An unrelated unfinished release Effect can forbid *new* PG Jobs,
        // but cannot erase the answer to the original exact replay.
        scratch
            .admin
            .execute(
                "INSERT INTO job_runtime_release_effects(job_id,effect_id,contract,request_digest,workspace_id,commit_revision,candidate_manifest_digest,expected_tool_count,receipt_path,binding_digest) VALUES($1,'effect-fixture','release-v1','test-request','ws-fixture','revision-fixture','manifest-fixture',0,'effect-receipt','effect-binding')",
                &[&a.job_id],
            )
            .unwrap();
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Existing(a.job_id.clone())
        );
        let mut conflicting_during_effect = a.clone();
        conflicting_during_effect.request_digest = "sha256:other-request".into();
        assert!(matches!(
            store.admit(&conflicting_during_effect),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert!(matches!(
            store.admit(&payload(
                "new-during-effect",
                "job-forbidden",
                "other-ws",
                2
            )),
            Err(PgAdmissionError::PendingEffect)
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        scratch
            .admin
            .execute(
                "DELETE FROM job_runtime_release_effects WHERE job_id=$1",
                &[&a.job_id],
            )
            .unwrap();
        let mut conflict = a.clone();
        conflict.request_digest = "sha256:different-request".into();
        assert!(matches!(
            store.admit(&conflict),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert!(matches!(
            store.admit(&payload("request-B", "job-B", "workspace-A", 2)),
            Err(PgAdmissionError::Capacity)
        ));
        assert!(matches!(
            store.admit(&payload("request-B", "job-B", "workspace-B", 1)),
            Err(PgAdmissionError::Capacity)
        ));

        // A row uniqueness error after inserting Job must rollback every
        // consumer-visible part of this admission.
        let mut duplicate_attempt = payload("request-C", "job-C", "workspace-B", 2);
        duplicate_attempt.attempt_id = a.attempt_id.clone();
        assert!(matches!(
            store.admit(&duplicate_attempt),
            Err(PgAdmissionError::Database(_))
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store
                .admit(&payload("request-D", "job-D", "workspace-B", 2))
                .unwrap(),
            PgAdmissionOutcome::Created("job-D".into())
        );
        assert_eq!(scratch.count("jobs"), 2);
        assert_eq!(scratch.count("job_events"), 6);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_terminal_cas_replay_orphan_hold_and_atomic_rollback() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("terminal-one", "job-terminal", "workspace-term", 2);
        store.admit(&input).unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "NATIVE_PG_TEST".into(),
            exit_code: Some(3),
            finished_at_ms: 1234578,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        let mut stale = terminal.clone();
        stale.expected_row_version = 1;
        assert!(matches!(
            store.commit_terminal_no_artifacts(&stale),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(input.job_id.clone())
        );
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Existing(input.job_id.clone())
        );
        assert_eq!(scratch.count("job_events"), 5);
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "released");
        let mut conflicting = terminal.clone();
        conflicting.result_digest = "sha256:other".into();
        assert!(matches!(
            store.commit_terminal_no_artifacts(&conflicting),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert_eq!(scratch.count("job_events"), 5);

        let orphan = payload("orphan", "job-orphan", "workspace-term", 2);
        store.admit(&orphan).unwrap();
        let hold = PgTerminalNoArtifacts {
            attempt_id: orphan.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "orphaned".into(),
            result_digest: "sha256:orphan".into(),
            reason_code: "ORPHAN".into(),
            exit_code: None,
            finished_at_ms: 1234580,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        store.commit_terminal_no_artifacts(&hold).unwrap();
        let held: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&orphan.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(held, "held_orphaned");
        assert!(matches!(
            store.admit(&payload("after-orphan", "job-after", "workspace-term", 2)),
            Err(PgAdmissionError::Capacity)
        ));
        assert_eq!(scratch.count("jobs"), 2);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_stale_attempt_cannot_terminalize_current_job() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("stale-terminal", "job-stale-terminal", "workspace-stale", 2);
        store.admit(&input).unwrap();
        scratch.admin.execute(
            "INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,row_version) VALUES($1,$2,2,'accepted','natural','launch-new','/nonproduction/new','newer.service',$3,0)",
            &[&"attempt-newer", &input.job_id, &input.created_at_ms],
        ).unwrap();
        scratch
            .admin
            .execute(
                "UPDATE jobs SET current_attempt_id='attempt-newer' WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();

        let old_attempt = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:stale".into(),
            reason_code: "STALE_ATTEMPT".into(),
            exit_code: Some(5),
            finished_at_ms: input.created_at_ms + 1,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.commit_terminal_no_artifacts(&old_attempt),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3, "no stale terminal event");
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "accepted", "old Attempt must remain unchanged");
        let job = scratch
            .admin
            .query_one(
                "SELECT resolution,current_attempt_id FROM jobs WHERE job_id=$1",
                &[&input.job_id],
            )
            .unwrap();
        let resolution: Option<String> = job.get(0);
        let current: Option<String> = job.get(1);
        assert_eq!((resolution, current), (None, Some("attempt-newer".into())));
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_artifact_bearing_terminal_is_denied_until_full_owner_exists() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("has-artifact", "job-artifact", "workspace-artifact", 1);
        store.admit(&input).unwrap();
        scratch
            .admin
            .execute(
                "INSERT INTO artifacts(artifact_id,job_id,attempt_id) VALUES('artifact-test',$1,$2)",
                &[&input.job_id, &input.attempt_id],
            )
            .unwrap();
        let terminal = PgTerminalNoArtifacts {
            attempt_id: input.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result".into(),
            reason_code: "ARTIFACT_STOP".into(),
            exit_code: Some(1),
            finished_at_ms: 1234599,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.commit_terminal_no_artifacts(&terminal),
            Err(PgAdmissionError::Blocked)
        ));
        let standing: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(standing, "accepted");
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_STAGE_TEST_DSN historical-stage qualification"]
    fn historical_pg_stage_is_not_an_admission_authority() {
        let dsn = historical_pg_stage_test_dsn();
        let mut inspector = Client::connect(&dsn, NoTls).unwrap();
        let before: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        let row=inspector.query_one(
            "SELECT state,source_sha256,promotion_allowed FROM rw12_stage_cutover_r1._stage_control WHERE id='source'",
            &[]).unwrap();
        let state: String = row.get(0);
        let source: String = row.get(1);
        let permitted: bool = row.get(2);
        assert_eq!(state, "VERIFIED_NON_AUTHORITY");
        assert!(!permitted);
        assert_eq!(source.len(), 64, "staged source identity exists");
        // A historical row-exact import is not a durable writer schema:
        // fail at connect before any operation can even be admitted.
        assert!(matches!(
            PgAdmissionStore::connect(&dsn, "rw12_stage_cutover_r1"),
            Err(PgAdmissionError::Unqualified)
        ));
        let after: i64 = inspector
            .query_one("SELECT count(*) FROM rw12_stage_cutover_r1.jobs", &[])
            .unwrap()
            .get(0);
        assert_eq!(before, after);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_commit_readback_is_exact_and_fail_closed_after_ack_loss() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("readback-cancel", "job-readback", "ws-readback", 1);
        let intent = PgCancelIntent {
            job_id: input.job_id.clone(),
            observed_at_ms: 1234600,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        assert!(matches!(
            observer.observe_cancel_intent(&intent),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        writer.admit(&input).unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        writer.request_cancel_intent(&intent).unwrap();
        // Reconcile on a separate native PG connection after a simulated
        // loss of the write-side acknowledgement.
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Confirmed(input.job_id.clone())
        );
        let mut wrong_request = intent.clone();
        wrong_request.observed_at_ms += 1;
        assert_eq!(
            observer.observe_cancel_intent(&wrong_request).unwrap(),
            PgCancelObservation::Inconclusive
        );
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='held_orphaned' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='STOP_REQUESTED'",
            &[&input.job_id],
        ).unwrap();
        assert_eq!(
            observer.observe_cancel_intent(&intent).unwrap(),
            PgCancelObservation::Inconclusive
        );
        assert_eq!(scratch.count("job_events"), 4);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_intent_is_atomic_replayable_and_never_implies_dispatch_stopped() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let first = payload("cancel-before-dispatch", "job-cancel-accepted", "ws-a", 2);
        let cancel = PgCancelIntent {
            job_id: first.job_id.clone(),
            observed_at_ms: 1234569,
            expected_source_sha256: first.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.request_cancel_intent(&cancel),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        store.admit(&first).unwrap();
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(first.job_id.clone())
        );
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(first.job_id.clone())
        );
        let row = scratch.admin.query_one(
            "SELECT j.desired_state,j.resolution,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&first.job_id],
        ).unwrap();
        assert_eq!(row.get::<_, String>(0), "cancelled");
        assert_eq!(row.get::<_, Option<String>>(1), None);
        assert_eq!(row.get::<_, String>(2), "accepted");
        assert_eq!(row.get::<_, String>(3), "stop_requested");
        assert_eq!(row.get::<_, String>(4), "active");
        assert_eq!(scratch.count("job_events"), 4);
        assert!(matches!(
            store.admit(&payload("new-job", "new-job", "ws-a", 2)),
            Err(PgAdmissionError::Capacity)
        ));
        let wrong_source = PgCancelIntent {
            expected_source_sha256: "b".repeat(64),
            ..cancel
        };
        assert!(matches!(
            store.request_cancel_intent(&wrong_source),
            Err(PgAdmissionError::Unqualified)
        ));
        assert_eq!(scratch.count("job_events"), 4);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancel_intent_running_orphan_and_missing_reservation_fences() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let running = payload("cancel-running", "job-running", "ws-a", 3);
        store.admit(&running).unwrap();
        scratch
            .admin
            .execute(
                "UPDATE attempts SET state='running',row_version=row_version+1 WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap();
        let cancel = PgCancelIntent {
            job_id: running.job_id.clone(),
            observed_at_ms: 1234570,
            expected_source_sha256: running.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(running.job_id.clone())
        );
        let state: String = scratch
            .admin
            .query_one(
                "SELECT state FROM attempts WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(state, "stopping");
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(running.job_id.clone())
        );
        let terminal = PgTerminalNoArtifacts {
            attempt_id: running.attempt_id.clone(),
            expected_row_version: 2,
            terminal_state: "cancelled".into(),
            result_digest: "sha256:stopped-by-runner".into(),
            reason_code: "PG_CANCEL_RUNNER_OBSERVED".into(),
            exit_code: None,
            finished_at_ms: 1234571,
            expected_source_sha256: running.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.commit_terminal_no_artifacts(&terminal).unwrap(),
            PgTerminalOutcome::Committed(running.job_id.clone())
        );
        assert_eq!(
            store.request_cancel_intent(&cancel).unwrap(),
            PgCancelOutcome::Existing(running.job_id.clone())
        );
        let released: String = scratch
            .admin
            .query_one(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
                &[&running.attempt_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(released, "released");

        let orphan = payload("cancel-orphan", "job-orphan", "ws-a", 3);
        store.admit(&orphan).unwrap();
        store
            .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
                attempt_id: orphan.attempt_id.clone(),
                expected_row_version: 0,
                terminal_state: "orphaned".into(),
                result_digest: "sha256:orphan".into(),
                reason_code: "ORPHAN_OBSERVED".into(),
                exit_code: None,
                finished_at_ms: 1234572,
                expected_source_sha256: orphan.expected_source_sha256.clone(),
            })
            .unwrap();
        let orphan_cancel = PgCancelIntent {
            job_id: orphan.job_id.clone(),
            observed_at_ms: 1234573,
            expected_source_sha256: orphan.expected_source_sha256.clone(),
        };
        assert_eq!(
            store.request_cancel_intent(&orphan_cancel).unwrap(),
            PgCancelOutcome::IntentRecorded(orphan.job_id.clone())
        );
        let orphan_row=scratch.admin.query_one(
            "SELECT j.resolution,j.desired_state,a.state,a.termination_intent,r.state FROM jobs j JOIN attempts a ON a.job_id=j.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE j.job_id=$1",
            &[&orphan.job_id],
        ).unwrap();
        assert_eq!(orphan_row.get::<_, String>(0), "orphaned");
        assert_eq!(orphan_row.get::<_, String>(1), "cancelled");
        assert_eq!(orphan_row.get::<_, String>(2), "orphaned");
        assert_eq!(orphan_row.get::<_, String>(3), "stop_requested");
        assert_eq!(orphan_row.get::<_, String>(4), "held_orphaned");
        assert_eq!(
            store.request_cancel_intent(&orphan_cancel).unwrap(),
            PgCancelOutcome::Existing(orphan.job_id.clone())
        );

        let invalid = payload("missing-reservation", "job-missing", "ws-b", 3);
        store.admit(&invalid).unwrap();
        scratch
            .admin
            .execute(
                "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
                &[&invalid.attempt_id],
            )
            .unwrap();
        let before = scratch.count("job_events");
        let failed = PgCancelIntent {
            job_id: invalid.job_id.clone(),
            observed_at_ms: 1234574,
            expected_source_sha256: invalid.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.request_cancel_intent(&failed),
            Err(PgAdmissionError::Blocked)
        ));
        let desired: String = scratch
            .admin
            .query_one(
                "SELECT desired_state FROM jobs WHERE job_id=$1",
                &[&invalid.job_id],
            )
            .unwrap()
            .get(0);
        assert_eq!(desired, "run");
        assert_eq!(scratch.count("job_events"), before);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_admission_readback_is_exact_and_never_claims_absence() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let a = payload("ack-lost", "job-ack-lost", "ws-ack-lost", 2);
        let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive,
            "absence must not prove that the original COMMIT did not happen"
        );

        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        assert_eq!(
            writer.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        // Treat writer COMMIT acknowledgement as lost. Read back on an
        // independent qualified connection without issuing a second write.
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Confirmed(a.job_id.clone())
        );
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("job_events"), 3);

        let mut conflicting = a.clone();
        conflicting.request_digest = "sha256:altered-request".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        conflicting = a.clone();
        conflicting.operation_digest = "sha256:altered-operation".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        conflicting = a.clone();
        conflicting.attempt_id = "attempt-unrelated".into();
        assert_eq!(
            observer.observe_admission(&conflicting).unwrap(),
            PgAdmissionObservation::Inconclusive
        );

        // A missing capacity reservation is independently disqualifying,
        // even while the complete original event sequence remains intact.
        scratch
            .admin
            .execute(
                "DELETE FROM concurrency_reservations WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        scratch.admin.execute(
            "INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,state_observed_at_ms) VALUES($1,$2,$3,'active',$4,$4)",
            &[&a.reservation_id,&a.attempt_id,&i64::from(a.global_limit),&a.created_at_ms],
        ).unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Confirmed(a.job_id.clone()),
            "restoring the original reservation must restore the complete witness"
        );

        // Conversely, the key/Job/Attempt/reservation rows are not sufficient
        // without all original admission events.
        scratch
            .admin
            .execute(
                "DELETE FROM job_events WHERE job_id=$1 AND event_sequence=2",
                &[&a.job_id],
            )
            .unwrap();
        assert_eq!(
            observer.observe_admission(&a).unwrap(),
            PgAdmissionObservation::Inconclusive
        );
        assert_eq!(scratch.count("jobs"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_bundle_and_dispatch_commit_before_external_effect() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("dispatch-request", "dispatch-job", "dispatch-ws", 2);
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        let digest = format!("sha256:{}", "b".repeat(64));
        let issued = PgDispatchIssued {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 2,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 3);
        let prepared = PgBundleReady {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 1,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&prepared).unwrap(), 1);
        assert!(matches!(
            store.commit_bundle_ready_pg(&prepared),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 4);
        // Wrong source cut and missing original bundle evidence must never
        // permit an attempted dispatch, even when the Attempt row looks ready.
        let mut wrong_source = issued.clone();
        wrong_source.expected_source_sha256 = "f".repeat(64);
        assert!(matches!(
            store.mark_dispatch_issued_pg(&wrong_source),
            Err(PgAdmissionError::Unqualified)
        ));
        let original_detail = serde_json::json!({"bundleDigest": digest}).to_string();
        let original_digest = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(original_detail.as_bytes()))
        );
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered'              WHERE job_id=$1 AND event_type='BUNDLE_READY'",
            &[&a.job_id],
        ).unwrap();
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 4);
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest=$1              WHERE job_id=$2 AND event_type='BUNDLE_READY'",
            &[&original_digest, &a.job_id],
        ).unwrap();
        assert_eq!(store.mark_dispatch_issued_pg(&issued).unwrap(), 2);
        assert_eq!(scratch.count("job_events"), 5);
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued),
            Err(PgAdmissionError::Blocked)
        ));
        assert_eq!(scratch.count("job_events"), 5);
        let row = scratch
            .admin
            .query_one(
                "SELECT state,row_version,bundle_digest FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "starting");
        assert_eq!(row.get::<_, i64>(1), 2);
        assert_eq!(
            row.get::<_, Option<String>>(2).as_deref(),
            Some(digest.as_str())
        );
        let event = scratch.admin.query_one(
            "SELECT origin,reason_code,previous_state,new_state FROM job_events WHERE job_id=$1 AND event_sequence=5",
            &[&a.job_id],
        ).unwrap();
        assert_eq!(event.get::<_, String>(0), "SYSTEM_DERIVED");
        assert_eq!(event.get::<_, String>(1), "AT_MOST_ONCE_BOUNDARY_COMMITTED");
        assert_eq!(
            event.get::<_, Option<String>>(2).as_deref(),
            Some("accepted")
        );
        assert_eq!(
            event.get::<_, Option<String>>(3).as_deref(),
            Some("starting")
        );
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_cancellation_blocks_unissued_dispatch_without_false_terminal() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let a = payload("cancel-pre-dispatch", "cancel-job", "cancel-ws", 2);
        assert_eq!(
            store.admit(&a).unwrap(),
            PgAdmissionOutcome::Created(a.job_id.clone())
        );
        let digest = format!("sha256:{}", "d".repeat(64));
        let ready = PgBundleReady {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 1,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&ready).unwrap(), 1);
        assert_eq!(
            store
                .request_cancel_intent(&PgCancelIntent {
                    job_id: a.job_id.clone(),
                    observed_at_ms: a.created_at_ms + 2,
                    expected_source_sha256: a.expected_source_sha256.clone(),
                })
                .unwrap(),
            PgCancelOutcome::IntentRecorded(a.job_id.clone())
        );
        let issued = PgDispatchIssued {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: 2,
            expected_bundle_digest: digest.clone(),
            observed_at_ms: a.created_at_ms + 3,
            expected_source_sha256: a.expected_source_sha256.clone(),
        };
        assert!(matches!(
            store.mark_dispatch_issued_pg(&issued),
            Err(PgAdmissionError::Blocked)
        ));
        let row = scratch.admin.query_one(
            "SELECT a.state,j.desired_state,j.resolution,r.state FROM attempts a JOIN jobs j ON j.job_id=a.job_id JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id WHERE a.attempt_id=$1",
            &[&a.attempt_id],
        ).unwrap();
        assert_eq!(row.get::<_, String>(0), "accepted");
        assert_eq!(row.get::<_, String>(1), "cancelled");
        assert_eq!(row.get::<_, Option<String>>(2), None);
        assert_eq!(row.get::<_, String>(3), "active");
        assert_eq!(scratch.count("job_events"), 5);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_clean_epoch_needs_no_old_sqlite_requests() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut pg = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        // This was an old SQLite request ID, but the owner explicitly
        // retired all old history. In a NEW PG epoch it is simply a new key.
        let request = payload("formerly-old-key", "new-pg-job", "new-workspace", 2);
        assert_eq!(
            pg.admit(&request).unwrap(),
            PgAdmissionOutcome::Created(request.job_id.clone())
        );
        assert_eq!(
            pg.admit(&request).unwrap(),
            PgAdmissionOutcome::Existing(request.job_id.clone())
        );
        let mut changed = request.clone();
        // A changed resolved physical Operation cannot redefine an existing
        // request key: the original replay is valid even after source drift.
        changed.operation_digest = "sha256:different-current-epoch-operation".into();
        assert_eq!(
            pg.admit(&changed).unwrap(),
            PgAdmissionOutcome::Existing(request.job_id.clone())
        );
        changed.request_digest = "sha256:different-current-epoch-request".into();
        assert!(matches!(
            pg.admit(&changed),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
        assert_eq!(scratch.count("job_events"), 3);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_readonly_job_projection_fences_stage_and_incoherent_terminal() {
        use crate::PgJobReadback;
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let input = payload("readback-req", "readback-job", "readback-workspace", 2);
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &input.expected_source_sha256),
            Err(PgAdmissionError::Unqualified)
        ));
        scratch.qualify();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
        store.admit(&input).unwrap();
        let events_before = scratch.count("job_events");
        let first = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(first) = first else {
            panic!("admitted PG job must be read coherently");
        };
        assert_eq!(first.attempt_id, input.attempt_id);
        assert_eq!(first.attempt_state, "accepted");
        assert_eq!(first.resolution, None);
        assert_eq!(first.reservation_state, "active");
        assert_eq!(
            scratch.count("job_events"),
            events_before,
            "readback must not append effects"
        );
        assert!(matches!(
            store.observe_job_readonly(&input.job_id, &"f".repeat(64)),
            Err(PgAdmissionError::Unqualified)
        ));
        let cancel = PgCancelIntent {
            job_id: input.job_id.clone(),
            observed_at_ms: 1234570,
            expected_source_sha256: input.expected_source_sha256.clone(),
        };
        store.request_cancel_intent(&cancel).unwrap();
        let cancelling = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(cancelling) = cancelling else {
            panic!("cancel intent must not erase the active Attempt");
        };
        assert_eq!(cancelling.desired_state, "cancelled");
        assert_eq!(cancelling.resolution, None);
        assert_eq!(cancelling.reservation_state, "active");
        store
            .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 1,
                terminal_state: "cancelled".into(),
                result_digest: "sha256:terminal".into(),
                reason_code: "READBACK_TEST".into(),
                exit_code: None,
                finished_at_ms: 1234571,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .unwrap();
        let terminal = store
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap();
        let PgJobReadback::Observed(terminal) = terminal else {
            panic!("verified PG terminal transaction must be projected");
        };
        assert_eq!(terminal.resolution.as_deref(), Some("cancelled"));
        assert_eq!(terminal.reservation_state, "released");
        assert_eq!(terminal.current_attempt_id, None);
        let original_digest: String = scratch
            .admin
            .query_one(
                "SELECT detail_digest FROM job_events WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
                &[&input.job_id],
            )
            .unwrap()
            .get(0);
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest='sha256:tampered' WHERE job_id=$1 AND event_type='JOB_TERMINAL'",
            &[&input.job_id],
        ).unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
        scratch.admin.execute(
            "UPDATE job_events SET detail_digest=$1 WHERE job_id=$2 AND event_type='JOB_TERMINAL'",
            &[&original_digest, &input.job_id],
        ).unwrap();

        // A corrupt durable reservation must never yield a successful readback.
        scratch
            .admin
            .execute(
                "UPDATE concurrency_reservations SET state='active' WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
                .unwrap(),
            PgJobReadback::Inconclusive,
        );
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_artifact_metadata_terminal_is_atomic_replayable_and_rejects_corruption() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let first = payload(
            "artifact-request-one",
            "artifact-job-one",
            "artifact-workspace",
            2,
        );
        store.admit(&first).unwrap();
        let artifact = PgArtifactRegistration {
            artifact_id: "artifact-A".into(),
            kind: "stdout".into(),
            relative_path: "output/stdout.txt".into(),
            digest: format!("sha256:{}", "a".repeat(64)),
            media_type: "text/plain".into(),
            byte_length: 14,
            truncated: false,
            created_at_ms: 1234568,
        };
        let terminal = PgTerminalNoArtifacts {
            attempt_id: first.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:result-with-artifact".into(),
            reason_code: "PG_ARTIFACT_TERMINAL_TEST".into(),
            exit_code: Some(1),
            finished_at_ms: 1234569,
            expected_source_sha256: first.expected_source_sha256.clone(),
        };
        let mut invalid = artifact.clone();
        invalid.relative_path = "../outside".into();
        assert!(matches!(
            store.commit_terminal_with_artifacts(&terminal, &[invalid]),
            Err(PgAdmissionError::InvalidInput)
        ));
        assert_eq!(scratch.count("artifacts"), 0);
        assert_eq!(scratch.count("job_events"), 3);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Committed(first.job_id.clone())
        );
        assert_eq!(scratch.count("artifacts"), 1);
        assert_eq!(scratch.count("job_events"), 5);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Existing(first.job_id.clone()),
            "identical replay never writes duplicate Artifact"
        );
        assert!(matches!(
            store.commit_terminal_no_artifacts(&terminal),
            Err(PgAdmissionError::Blocked)
        ));
        let mut corrupted = artifact.clone();
        corrupted.digest = format!("sha256:{}", "b".repeat(64));
        assert!(matches!(
            store.commit_terminal_with_artifacts(&terminal, &[corrupted]),
            Err(PgAdmissionError::IdempotencyConflict)
        ));
        let observed = store
            .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
            .unwrap();
        assert!(matches!(observed, crate::PgJobReadback::Observed(_)));
        let current: String = scratch
            .admin
            .query_one(
                "SELECT digest FROM artifacts WHERE artifact_id=$1",
                &[&"artifact-A"],
            )
            .unwrap()
            .get(0);
        scratch
            .admin
            .execute(
                "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
                &[&format!("sha256:{}", "c".repeat(64)), &"artifact-A"],
            )
            .unwrap();
        assert_eq!(
            store
                .observe_job_readonly(&first.job_id, &first.expected_source_sha256)
                .unwrap(),
            crate::PgJobReadback::Inconclusive,
            "existing terminal event must bind the exact Artifact manifest"
        );
        scratch
            .admin
            .execute(
                "UPDATE artifacts SET digest=$1 WHERE artifact_id=$2",
                &[&current, &"artifact-A"],
            )
            .unwrap();
        let second = payload(
            "artifact-request-two",
            "artifact-job-two",
            "another-workspace",
            2,
        );
        store.admit(&second).unwrap();
        let second_terminal = PgTerminalNoArtifacts {
            attempt_id: second.attempt_id.clone(),
            expected_row_version: 0,
            terminal_state: "failed".into(),
            result_digest: "sha256:second-result".into(),
            reason_code: "PG_DUPLICATE_ARTIFACT".into(),
            exit_code: Some(1),
            finished_at_ms: 1234570,
            expected_source_sha256: second.expected_source_sha256.clone(),
        };
        // Global Artifact ID collision rejects the WHOLE terminal transaction.
        assert!(matches!(
            store.commit_terminal_with_artifacts(&second_terminal, &[artifact]),
            Err(PgAdmissionError::Database(_))
        ));
        assert_eq!(scratch.count("artifacts"), 1);
        assert_eq!(
            scratch.count("job_events"),
            8,
            "second Job keeps only its 3 admission events"
        );
        let projection = store
            .observe_job_readonly(&second.job_id, &second.expected_source_sha256)
            .unwrap();
        let crate::PgJobReadback::Observed(projection) = projection else {
            panic!("failed artifact insert must not terminalize Attempt or free capacity");
        };
        assert_eq!(projection.resolution, None);
        assert_eq!(projection.attempt_state, "accepted");
        assert_eq!(projection.reservation_state, "active");
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_composed_admit_dispatch_artifact_terminal_is_one_consumer_chain() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification required");
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let mut store = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let request = payload("chain-request", "chain-job", "chain-workspace", 2);
        assert_eq!(
            store.admit(&request).unwrap(),
            PgAdmissionOutcome::Created(request.job_id.clone())
        );
        let bundle = PgBundleReady {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 0,
            bundle_digest: format!("sha256:{}", "b".repeat(64)),
            observed_at_ms: 1234568,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(store.commit_bundle_ready_pg(&bundle).unwrap(), 1);
        let dispatch = PgDispatchIssued {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 1,
            expected_bundle_digest: bundle.bundle_digest,
            observed_at_ms: 1234569,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(store.mark_dispatch_issued_pg(&dispatch).unwrap(), 2);
        assert!(matches!(
            store.mark_dispatch_issued_pg(&dispatch),
            Err(PgAdmissionError::Blocked),
        ));
        let artifact = PgArtifactRegistration {
            artifact_id: "chain-artifact".into(),
            kind: "stdout".into(),
            relative_path: "output/chain.txt".into(),
            digest: format!("sha256:{}", "c".repeat(64)),
            media_type: "text/plain".into(),
            byte_length: 8,
            truncated: false,
            created_at_ms: 1234570,
        };
        let terminal = PgTerminalNoArtifacts {
            attempt_id: request.attempt_id.clone(),
            expected_row_version: 2,
            terminal_state: "failed".into(),
            result_digest: "sha256:chain-result".into(),
            reason_code: "CHAIN_TEST".into(),
            exit_code: Some(1),
            finished_at_ms: 1234571,
            expected_source_sha256: request.expected_source_sha256.clone(),
        };
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, std::slice::from_ref(&artifact))
                .unwrap(),
            PgTerminalOutcome::Committed(request.job_id.clone()),
        );
        assert_eq!(
            scratch.count("job_events"),
            7,
            "admission 3, dispatch 2, terminal 2"
        );
        assert_eq!(scratch.count("artifacts"), 1);
        let outcome = store
            .observe_job_readonly(&request.job_id, &request.expected_source_sha256)
            .unwrap();
        let crate::PgJobReadback::Observed(snapshot) = outcome else {
            panic!("full PG lifecycle must remain coherently observable");
        };
        assert_eq!(snapshot.resolution.as_deref(), Some("failed"));
        assert_eq!(snapshot.reservation_state, "released");
        assert_eq!(snapshot.attempt_row_version, 3);
        assert_eq!(
            store
                .commit_terminal_with_artifacts(&terminal, &[artifact])
                .unwrap(),
            PgTerminalOutcome::Existing(request.job_id.clone()),
        );
        assert_eq!(
            scratch.count("job_events"),
            7,
            "retry may not append a second terminal"
        );
        assert_eq!(scratch.count("artifacts"), 1);
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
    fn pg18_concurrent_duplicate_never_creates_second_job() {
        let dsn = physical_pg_test_dsn();
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        let gate = Arc::new(Barrier::new(5));
        let mut workers = Vec::new();
        for n in 0..4 {
            let dsn = dsn.clone();
            let schema = scratch.name.clone();
            let gate = gate.clone();
            workers.push(thread::spawn(move || {
                let mut store = PgAdmissionStore::connect(&dsn, &schema).unwrap();
                let request = payload("same-key", &format!("job-{n}"), "workspace-one", 2);
                gate.wait();
                store.admit(&request)
            }));
        }
        gate.wait();
        let mut created = 0usize;
        for worker in workers {
            match worker.join().unwrap() {
                Ok(PgAdmissionOutcome::Created(_)) => created += 1,
                Ok(PgAdmissionOutcome::Existing(_)) => (),
                Err(PgAdmissionError::Database(error))
                    if error.code()
                        == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) => {}
                unexpected => panic!("unsafe concurrent admission result: {unexpected:?}"),
            }
        }
        assert_eq!(created, 1);
        assert_eq!(scratch.count("jobs"), 1);
        assert_eq!(scratch.count("idempotency_keys"), 1);
        assert_eq!(scratch.count("attempts"), 1);
        assert_eq!(scratch.count("concurrency_reservations"), 1);
    }
}
