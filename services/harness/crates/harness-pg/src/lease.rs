//! One PostgreSQL v1 Run lease port. Reuses the Python Store's physical schema
//! and READ COMMITTED row-lock protocol; does not create a second Registry.
//!
//! A Run lease is an ephemeral owner/revision constraint for later Journal
//! admission, not a Tool/Provider execution permission or physical receipt.
//! This module never creates an Event, Runtime Job, or execution fence.
use std::fmt;

use postgres::{Client, Transaction};

use super::{run_projection, valid_schema, ReadError};

#[derive(Debug)]
pub enum LeaseError {
    Database(postgres::Error),
    Store(ReadError),
    InvalidSchema,
    UnsupportedSchema,
    InvalidArguments,
    ClockOrGenerationOverflow,
    MissingRun(String),
    RevisionConflict,
    TerminalConflict,
    Held,
}

impl fmt::Display for LeaseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Database(e) => write!(f, "PostgreSQL lease operation failed: {e}"),
            Self::Store(e) => write!(f, "Harness Run projection invalid: {e}"),
            Self::InvalidSchema => write!(f, "Harness schema name is invalid"),
            Self::UnsupportedSchema => write!(f, "Harness PostgreSQL schema is not v1"),
            Self::InvalidArguments => write!(f, "Harness lease owner/TTL/clock invalid"),
            Self::ClockOrGenerationOverflow => write!(f, "Harness lease bigint limit exceeded"),
            Self::MissingRun(run_id) => write!(f, "Harness Run does not exist: {run_id}"),
            Self::RevisionConflict => write!(f, "Harness Run revision changed before lease"),
            Self::TerminalConflict => write!(f, "terminal Harness Run cannot be leased"),
            Self::Held => write!(f, "Harness Run leased by another execution"),
        }
    }
}
impl std::error::Error for LeaseError {}
impl From<postgres::Error> for LeaseError {
    fn from(e: postgres::Error) -> Self {
        Self::Database(e)
    }
}
impl From<ReadError> for LeaseError {
    fn from(e: ReadError) -> Self {
        Self::Store(e)
    }
}

/// A database-observed lease tuple. Not a durable dispatch/effect grant.
/// Identity fields are private to prevent callers fabricating typed receipts.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RunLease {
    harness_run_id: String,
    owner_id: String,
    lease_revision: i64,
    run_revision: i64,
    expires_at_ms: i64,
}
impl RunLease {
    pub fn harness_run_id(&self) -> &str {
        &self.harness_run_id
    }
    pub fn owner_id(&self) -> &str {
        &self.owner_id
    }
    pub fn lease_revision(&self) -> i64 {
        self.lease_revision
    }
    pub fn run_revision(&self) -> i64 {
        self.run_revision
    }
    pub fn expires_at_ms(&self) -> i64 {
        self.expires_at_ms
    }
}

pub(crate) fn check_schema(tx: &mut Transaction<'_>, schema: &str) -> Result<(), LeaseError> {
    if !valid_schema(schema) {
        return Err(LeaseError::InvalidSchema);
    }
    // Checked one lower-case ASCII SQL identifier. Avoid untrusted SQL paths.
    tx.batch_execute(&format!("SET LOCAL search_path TO {schema}"))?;
    let version = tx.query_opt(
        "SELECT value FROM schema_info WHERE key='schema_version'",
        &[],
    )?;
    if version.map(|row| row.get::<_, String>(0)).as_deref() != Some("1") {
        return Err(LeaseError::UnsupportedSchema);
    }
    Ok(())
}

fn valid_owner(owner: &str) -> bool {
    // CPython str.strip() includes C0 U+001C..U+001F beyond Unicode White_Space.
    !owner.is_empty()
        && owner.trim_matches(|c: char| c.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&c))
            == owner
}

/// Native lease acquisition against EXISTING Python PostgreSQL schema v1.
///
/// The server's row lock on runs is acquired before run_leases, exactly as in
/// Python PostgresHarnessStore.acquire_run_lease. At a valid same-owner lease
/// this returns the OLD expiresAtMs without renewing the TTL; at exact expiry
/// the generation increments. A missing/terminal/revision-mismatched Run is
/// rejected before a lease can be created. One transaction commits both the
/// generation check and write. A failed call rolls back by dropping tx.
///
/// This is not idempotent external Tool dispatch. A future PG Journal Writer
/// must check the exact tuple under the same transaction *again*.
pub fn acquire_run_lease(
    connection: &mut Client,
    schema: &str,
    harness_run_id: &str,
    owner_id: &str,
    ttl_ms: i64,
    now_ms: i64,
    expected_run_revision: Option<i64>,
) -> Result<RunLease, LeaseError> {
    if !valid_schema(schema) {
        return Err(LeaseError::InvalidSchema);
    }
    if !valid_owner(owner_id) || ttl_ms < 1 || now_ms < 0 {
        return Err(LeaseError::InvalidArguments);
    }
    // Avoid attempting a write PG BIGINT cannot represent. This branch is a
    // native representational limit, not an assertion about physical effects.
    let expires_at_ms = now_ms
        .checked_add(ttl_ms)
        .ok_or(LeaseError::ClockOrGenerationOverflow)?;

    let mut tx = connection.transaction()?;
    check_schema(&mut tx, schema)?;
    let row = tx.query_opt(
        "SELECT * FROM runs WHERE harness_run_id=$1 FOR UPDATE",
        &[&harness_run_id],
    )?;
    let row = row.ok_or_else(|| LeaseError::MissingRun(harness_run_id.to_owned()))?;
    let run = run_projection(&row)?;
    if expected_run_revision.is_some_and(|rev| run.revision != rev) {
        return Err(LeaseError::RevisionConflict);
    }
    if matches!(run.status.as_str(), "stopped" | "completed" | "failed") {
        return Err(LeaseError::TerminalConflict);
    }

    let current = tx.query_opt(
        "SELECT owner_id,lease_revision,run_revision,expires_at_ms \
         FROM run_leases WHERE harness_run_id=$1 FOR UPDATE",
        &[&harness_run_id],
    )?;
    let lease_revision = if let Some(current) = current {
        let current_expires: i64 = current.get("expires_at_ms");
        let current_owner: String = current.get("owner_id");
        let current_run_revision: i64 = current.get("run_revision");
        let prior_lease_revision: i64 = current.get("lease_revision");
        if current_expires > now_ms {
            if current_owner != owner_id || current_run_revision != run.revision {
                return Err(LeaseError::Held);
            }
            let old = RunLease {
                harness_run_id: harness_run_id.to_owned(),
                owner_id: owner_id.to_owned(),
                lease_revision: prior_lease_revision,
                run_revision: run.revision,
                expires_at_ms: current_expires,
            };
            tx.commit()?;
            return Ok(old);
        }
        prior_lease_revision
            .checked_add(1)
            .ok_or(LeaseError::ClockOrGenerationOverflow)?
    } else {
        1
    };
    tx.execute(
        "INSERT INTO run_leases(harness_run_id,owner_id,lease_revision,run_revision,expires_at_ms) \
         VALUES($1,$2,$3,$4,$5) \
         ON CONFLICT(harness_run_id) DO UPDATE SET \
         owner_id=EXCLUDED.owner_id,lease_revision=EXCLUDED.lease_revision,\
         run_revision=EXCLUDED.run_revision,expires_at_ms=EXCLUDED.expires_at_ms",
        &[&harness_run_id, &owner_id, &lease_revision, &run.revision, &expires_at_ms],
    )?;
    let acquired = RunLease {
        harness_run_id: harness_run_id.to_owned(),
        owner_id: owner_id.to_owned(),
        lease_revision,
        run_revision: run.revision,
        expires_at_ms,
    };
    tx.commit()?;
    Ok(acquired)
}

/// Exact-tuple delete. Does not delete a later owner/lease generation.
/// Repeating release is benign false; even an expired lease can be released
/// iff its full tuple still matches the database row.
pub fn release_run_lease(
    connection: &mut Client,
    schema: &str,
    lease: &RunLease,
) -> Result<bool, LeaseError> {
    if !valid_schema(schema) {
        return Err(LeaseError::InvalidSchema);
    }
    let mut tx = connection.transaction()?;
    check_schema(&mut tx, schema)?;
    let changed = tx.execute(
        "DELETE FROM run_leases WHERE harness_run_id=$1 AND owner_id=$2 \
         AND lease_revision=$3 AND run_revision=$4 AND expires_at_ms=$5",
        &[
            &lease.harness_run_id,
            &lease.owner_id,
            &lease.lease_revision,
            &lease.run_revision,
            &lease.expires_at_ms,
        ],
    )?;
    tx.commit()?;
    Ok(changed == 1)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn owner_validation_matches_python_strip() {
        for valid in ["a", "agent:foo", "x\nz", "a\u{200b}"] {
            assert!(valid_owner(valid), "{valid:?}");
        }
        for invalid in ["", " a", "a ", "\u{001c}a", "a\u{001f}", "\nagent"] {
            assert!(!valid_owner(invalid), "{invalid:?}");
        }
    }
}
