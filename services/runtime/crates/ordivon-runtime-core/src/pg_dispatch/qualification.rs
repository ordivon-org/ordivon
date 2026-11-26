use super::super::{require_pg_writer_epoch, PgAdmissionError};
use postgres::Transaction;

const ADMISSION_GLOBAL_LOCK: i64 = 79_245_017;

// The same serialization/authority fence as PgAdmissionStore::admit.
// This is an execution *precondition*, not authentication of the caller or a
// claim about already launched OS processes.
pub(super) fn require_qualified_writer(
    tx: &mut Transaction<'_>,
    expected_source: &str,
) -> Result<(), PgAdmissionError> {
    tx.query_one(
        "SELECT pg_advisory_xact_lock($1)",
        &[&ADMISSION_GLOBAL_LOCK],
    )?;
    let row = tx
        .query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control \
         WHERE id='source' FOR UPDATE",
            &[],
        )?
        .ok_or(PgAdmissionError::Unqualified)?;
    if row.get::<_, String>(0) != "QUALIFIED_WRITER"
        || row.get::<_, String>(1) != expected_source
        || !row.get::<_, bool>(2)
    {
        return Err(PgAdmissionError::Unqualified);
    }
    require_pg_writer_epoch(tx, expected_source, true)?;
    Ok(())
}
