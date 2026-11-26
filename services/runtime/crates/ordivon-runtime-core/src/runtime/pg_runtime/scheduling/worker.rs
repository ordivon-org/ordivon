//! Original single LISTEN/notify/pressure wake loop; no new scheduler service.
use super::PgRuntime;
use std::{thread, time::Duration};

impl PgRuntime {
    /// One dedicated PG notification connection; a bounded timeout re-observes
    /// kernel pressure even when no database transition produces a notification.
    pub fn serve_scheduler(&self, shutdown: std::sync::Arc<std::sync::atomic::AtomicBool>) {
        use postgres::fallible_iterator::FallibleIterator;
        while !shutdown.load(std::sync::atomic::Ordering::Acquire) {
            if let Ok(mut db) = self.store() {
                if db
                    .client
                    .batch_execute("LISTEN ordivon_runtime_schedule")
                    .is_ok()
                {
                    while !shutdown.load(std::sync::atomic::Ordering::Acquire) {
                        if let Err(error) = self.reconcile_issued_jobs(100) {
                            eprintln!("PG native reconciliation error: {:?}", error.code);
                        }
                        if let Err(error) = self.schedule_pending_jobs() {
                            eprintln!("PG resource scheduling error: {:?}", error.code);
                        }
                        if db
                            .client
                            .notifications()
                            .timeout_iter(Duration::from_secs(1))
                            .next()
                            .is_err()
                        {
                            break;
                        }
                    }
                }
            }
            thread::sleep(Duration::from_secs(1));
        }
    }
}
