//! Shared native owner write lifecycle, no automatic replay.
use crate::{OwnerError, PgNoteStore, owner_error::db};
use tokio_postgres::{IsolationLevel, Transaction};
impl PgNoteStore {
    pub(crate) async fn owner_write<T, F>(
        &self,
        unknown: impl FnOnce(tokio_postgres::Error) -> OwnerError,
        action: F,
    ) -> Result<T, OwnerError>
    where
        F: for<'a, 'b> AsyncFnOnce(&'a Transaction<'b>) -> Result<T, OwnerError>,
    {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::ReadCommitted)
            .start()
            .await
            .map_err(|e| db("begin", e))?;
        let outcome = match action(&tx).await {
            Ok(o) => o,
            Err(cause) => {
                return match tx.rollback().await {
                    Ok(()) => {
                        lease.reusable();
                        Err(cause)
                    }
                    Err(rollback) => Err(OwnerError::RollbackUnknown {
                        cause: Box::new(cause),
                        rollback,
                    }),
                };
            }
        };
        tx.commit().await.map_err(unknown)?;
        lease.reusable();
        Ok(outcome)
    }
}
