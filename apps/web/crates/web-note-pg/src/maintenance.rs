//! Explicit bounded maintenance consumer. No hidden detached task or retry.
//! The caller chooses cadence, trusted time and consumes the result.
use crate::{OwnerError, PgNoteStore};

#[derive(Debug, Clone, Copy)]
pub struct ReplayMaintenance {
    batch_size: u32,
    max_batches: u32,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MaintenanceReport {
    pub deleted: u64,
    pub batches: u32,
    // A short batch may mean locked rows, not proven absence.
    pub short_batch: bool,
}
#[derive(Debug, thiserror::Error)]
#[error(
    "maintenance stopped after {committed_deleted} confirmed deletes in {committed_batches} batches: {cause}"
)]
pub struct MaintenanceFailure {
    pub committed_deleted: u64,
    pub committed_batches: u32,
    #[source]
    pub cause: OwnerError,
}
impl ReplayMaintenance {
    pub fn new(batch_size: u32, max_batches: u32) -> Result<Self, OwnerError> {
        if !(1..=10_000).contains(&batch_size) || !(1..=100).contains(&max_batches) {
            return Err(OwnerError::Invalid);
        }
        Ok(Self {
            batch_size,
            max_batches,
        })
    }
    pub async fn run_once(
        self,
        store: &PgNoteStore,
        now: i64,
    ) -> Result<MaintenanceReport, MaintenanceFailure> {
        let mut report = MaintenanceReport {
            deleted: 0,
            batches: 0,
            short_batch: false,
        };
        for _ in 0..self.max_batches {
            let n = store
                .cleanup_dpop_proofs(now, self.batch_size)
                .await
                .map_err(|cause| MaintenanceFailure {
                    committed_deleted: report.deleted,
                    committed_batches: report.batches,
                    cause,
                })?;
            report.deleted += n;
            report.batches += 1;
            if n < u64::from(self.batch_size) {
                report.short_batch = true;
                break;
            }
        }
        Ok(report)
    }
}
