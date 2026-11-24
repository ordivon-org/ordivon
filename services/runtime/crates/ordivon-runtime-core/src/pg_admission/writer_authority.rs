//! PostgreSQL writer authority: schema identification, epoch provenance,
//! and the existing qualified relational constraints. No Job admission here.
use super::PgAdmissionError;
use postgres::{Client, GenericClient};
use sha2::{Digest, Sha256};
use std::collections::HashSet;

pub(super) fn exact_schema(s: &str) -> bool {
    !matches!(s, "public" | "information_schema")
        && !s.starts_with("pg_")
        && !s.is_empty()
        && s.len() <= 63
        && s.as_bytes()[0].is_ascii_alphabetic()
        && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_')
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
pub(super) fn qualified_schema_constraints(
    client: &mut Client,
    schema: &str,
) -> Result<(), PgAdmissionError> {
    let rows = client.query(
        "SELECT r.relname::text,c.contype::text,ARRAY_AGG(a.attname::text ORDER BY k.ordinality), \
         COALESCE(ref_ns.nspname::text,''),COALESCE(ref_rel.relname::text,''), \
         ARRAY(SELECT ra.attname::text FROM unnest(c.confkey) WITH ORDINALITY AS rk(attnum,ordinality) \
               JOIN pg_catalog.pg_attribute ra ON ra.attrelid=c.confrelid AND ra.attnum=rk.attnum \
               ORDER BY rk.ordinality) \
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
    #[derive(Eq, Hash, PartialEq)]
    struct ConstraintIdentity {
        table: String,
        kind: String,
        columns: Vec<String>,
        target_table: String,
        target_columns: Vec<String>,
    }
    let actual: HashSet<ConstraintIdentity> = rows
        .iter()
        .map(|row| {
            let ref_schema: String = row.get(3);
            let ref_table: String = row.get(4);
            ConstraintIdentity {
                table: row.get(0),
                kind: row.get(1),
                columns: row.get(2),
                target_table: if ref_schema == schema {
                    ref_table
                } else {
                    String::new()
                },
                target_columns: row.get(5),
            }
        })
        .collect();
    // All existing foreign keys reference the identically named identity
    // columns on their target. Validate confkey as well as conkey: a valid
    // FK to another unique column on the same table is not that relation.
    let required: &[(&str, &str, &[&str], &str)] = &[
        ("workspace_consumer_claims", "p", &["claim_id"], ""),
        (
            "workspace_consumer_claims",
            "u",
            &["principal", "client_request_id"],
            "",
        ),
        ("job_allocations", "p", &["attempt_id"], ""),
        ("job_allocations", "f", &["attempt_id"], "attempts"),
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
        !actual.contains(&ConstraintIdentity {
            table: (*table).to_owned(),
            kind: (*kind).to_owned(),
            columns: columns.iter().map(|name| (*name).to_owned()).collect(),
            target_table: (*target).to_owned(),
            target_columns: if *kind == "f" {
                columns.iter().map(|name| (*name).to_owned()).collect()
            } else {
                Vec::new()
            },
        })
    }) {
        return Err(PgAdmissionError::Unqualified);
    }
    Ok(())
}
