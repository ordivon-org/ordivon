//! Shared qualified PG read-committed transaction and Workspace effect fence.
//! One existing PG authority, no second lock/lease database.
use super::*;
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
