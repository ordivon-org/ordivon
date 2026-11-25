//! Durable new-Job admission closure on the existing operator-owned PG authority.
//!
//! Source-level primitive, not permission to stop a Runtime or WSL. Fresh DDL
//! initializes the permanent row; an existing installation needs a separately
//! qualified one-time migration BEFORE replacing all writers. Missing is not
//! OPEN and must never trigger automatic bootstrap or reopen. No legacy writer
//! may remain after qualification. Physical recovery/reopen is a separate
//! consumer obligation; this module does not grant it.
use super::*;
use postgres::Transaction;

const OPEN_DIGEST: &str = "0000000000000000000000000000000000000000000000000000000000000000";

fn bare_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

pub(super) fn new_job_admission_open(tx: &mut Transaction<'_>) -> Result<bool, PgAdmissionError> {
    let row = tx.query_opt(
        "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='maintenance' FOR SHARE",
        &[],
    )?;
    Ok(row.is_some_and(|row| {
        row.get::<_, String>(0) == "ADMISSION_OPEN"
            && row.get::<_, String>(1) == OPEN_DIGEST
            && row.get::<_, bool>(2)
    }))
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgMaintenanceClosureObservation {
    /// The exact current durable closed subject was observed in one PG snapshot.
    /// This does not authorize compaction, prove all roots drained, or prove a
    /// physical effect occurred.
    ConfirmedClosed,
    /// Missing, OPEN, different/malformed subject: no closure confirmation.
    /// In particular, this is not proof a prior close/effect never happened.
    Inconclusive,
}

impl PgAdmissionStore {
    /// Read back the exact maintenance subject after a lost close acknowledgement.
    /// No mutation, bootstrap, timeout-based reopen, or physical effect.
    pub fn observe_maintenance_closure(
        &mut self,
        expected_source: &str,
        maintenance_digest: &str,
    ) -> Result<PgMaintenanceClosureObservation, PgAdmissionError> {
        if !bare_digest(expected_source)
            || !bare_digest(maintenance_digest)
            || maintenance_digest == OPEN_DIGEST
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let source = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        if source.get::<_, String>(0) != "QUALIFIED_WRITER"
            || source.get::<_, String>(1) != expected_source
            || !source.get::<_, bool>(2)
        {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, expected_source, false)?;
        let row = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='maintenance'",
            &[],
        )?;
        let exact = row.is_some_and(|row| {
            row.get::<_, String>(0) == "ADMISSION_CLOSED"
                && row.get::<_, String>(1) == maintenance_digest
                && !row.get::<_, bool>(2)
        });
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(if exact {
            PgMaintenanceClosureObservation::ConfirmedClosed
        } else {
            PgMaintenanceClosureObservation::Inconclusive
        })
    }

    /// Close new Job admission for the exact immutable maintenance digest.
    /// The operator must hold PostgreSQL UPDATE privileges on protected columns;
    /// the ordinary application role can read/lock them, not change their values.
    ///
    /// The same short admission lock serializes creation and closure; updating
    /// the permanent row makes a stale SERIALIZABLE admission fail at FOR SHARE.
    /// Writer and physical epoch qualification remain unchanged for settlement.
    /// Missing, malformed, or foreign subject cannot be overwritten. No timeout
    /// or session death reopens this durable state. Lost COMMIT is UNKNOWN.
    pub fn close_new_job_admission_for_maintenance(
        &mut self,
        expected_source: &str,
        maintenance_digest: &str,
    ) -> Result<(), PgAdmissionError> {
        if !bare_digest(expected_source)
            || !bare_digest(maintenance_digest)
            || maintenance_digest == OPEN_DIGEST
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::ReadCommitted)
            .start()?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let source = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        if source.get::<_, String>(0) != "QUALIFIED_WRITER"
            || source.get::<_, String>(1) != expected_source
            || !source.get::<_, bool>(2)
        {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, expected_source, true)?;
        let marker = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='maintenance' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = marker.get(0);
        let digest: String = marker.get(1);
        let allowed: bool = marker.get(2);
        let is_open = state == "ADMISSION_OPEN" && digest == OPEN_DIGEST && allowed;
        let exact_closed = state == "ADMISSION_CLOSED" && digest == maintenance_digest && !allowed;
        if !is_open && !exact_closed {
            return Err(PgAdmissionError::IdempotencyConflict);
        }
        // UPDATE also in the exact-closed replay branch: a read-only caller
        // cannot manufacture a new operator acknowledgement by replay.
        if tx.execute(
            "UPDATE _stage_control SET state='ADMISSION_CLOSED',source_sha256=$1,promotion_allowed=false WHERE id='maintenance'",
            &[&maintenance_digest],
        )? != 1 {
            return Err(PgAdmissionError::Unqualified);
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)
    }
}
