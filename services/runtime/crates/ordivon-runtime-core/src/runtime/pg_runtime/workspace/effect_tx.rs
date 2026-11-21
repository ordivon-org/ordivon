//! Original READ COMMITTED PostgreSQL Workspace lock and qualified writer transaction.
use super::{io, PgAdmissionStore, PgRuntime, RuntimeResult};

// The advisory lock serializes Job admission, terminal/lease updates and
// Workspace effects. A PostgreSQL SERIALIZABLE snapshot is frozen when the
// lock-acquisition SELECT starts, i.e. *before* the transaction actually
// acquires a contended lock. Such a snapshot can miss newly committed leases,
// even after the holder releases the lock and this transaction later commits.
// READ COMMITTED takes the Workspace guard queries' snapshots after the lock
// is acquired, matching the existing PG scheduler's lock+isolation protocol.
// The global lock is deliberately retained across Git/FS physical effects:
// moving them outside this fence requires an independently recoverable intent.
pub(super) const WORKSPACE_EFFECT_ISOLATION: postgres::IsolationLevel =
    postgres::IsolationLevel::ReadCommitted;

impl PgRuntime {
    /// Common qualified, lock-ordered transaction for every Workspace write.
    /// Do not take a SERIALIZABLE/REPEATABLE READ snapshot while *waiting* on
    /// the global advisory lock: it can predate a completed Job admission.
    pub(in crate::runtime::pg_runtime) fn begin_workspace_effect_tx<'a>(
        &self,
        db: &'a mut PgAdmissionStore,
    ) -> RuntimeResult<postgres::Transaction<'a>> {
        let mut tx = db
            .client
            .build_transaction()
            .isolation_level(WORKSPACE_EFFECT_ISOLATION)
            .start()
            .map_err(io)?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
            .map_err(io)?;
        self.require_qualified_writer_tx(&mut tx)?;
        Ok(tx)
    }
}
