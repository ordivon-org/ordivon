//! Bounded, fair reconciliation sweep of already committed PostgreSQL Jobs.
use super::*;

impl PgRuntime {
    /// Service-owned recovery path. Does not admit commands or consume Job capacity.
    /// Each cancellation retains its original principal and exact durable Job identity.
    pub fn reconcile_cancelled_jobs(&self, limit: u32) -> RuntimeResult<serde_json::Value> {
        self.reconcile_committed_jobs(limit, true)
    }
    /// Reconcile already issued native work, never dispatch an unissued Job.
    pub fn reconcile_issued_jobs(&self, limit: u32) -> RuntimeResult<serde_json::Value> {
        self.reconcile_committed_jobs(limit, false)
    }
    fn reconcile_committed_jobs(
        &self,
        limit: u32,
        cancelled_only: bool,
    ) -> RuntimeResult<serde_json::Value> {
        if limit == 0 || limit > 100 {
            return Err(RuntimeError::invalid("limit must be 1..100", "limit"));
        }
        let mut db = self.store()?;
        // The oldest unresolved jobs can stay blocked on uncertain native
        // evidence indefinitely. A fixed LIMIT on the oldest rows prevents
        // later jobs from ever being reconciled. Use finite upper-fenced
        // keyset epochs, with independent cursors for cancellation and
        // general recovery; never let newly arriving Jobs extend an epoch. Never hold a cursor mutex across DB or
        // native OS calls.
        let previous = {
            let cursors = self
                .reconciliation_cursors
                .lock()
                .map_err(|_| error("reconciliation cursor mutex poisoned"))?;
            if cancelled_only {
                cursors.cancelled.clone()
            } else {
                cursors.issued.clone()
            }
        };
        // Only the first page of each epoch takes a new upper bound. The
        // subsequent bounded pages use that same fence even if new Jobs
        // arrive continuously; stale concurrent scans cannot rewrite it.
        let upper_fence = match previous.upper_fence.clone() {
            Some(key) => Some(key),
            None => {
                latest_reconciliation_key(&mut db.client, cancelled_only).map_err(pg_read_error)?
            }
        };
        let pending = match upper_fence.as_ref() {
            Some(upper) => scan_reconciliation_page(
                &mut db.client,
                limit,
                cancelled_only,
                previous.key.as_ref(),
                upper,
            )
            .map_err(pg_read_error)?,
            None => Vec::new(),
        };
        let (next_key, next_upper_fence) = match upper_fence.as_ref() {
            Some(upper) => next_reconciliation_cursor(&pending, limit, upper),
            None => (None, None),
        };
        let mut cursors = self
            .reconciliation_cursors
            .lock()
            .map_err(|_| error("reconciliation cursor mutex poisoned"))?;
        let slot = if cancelled_only {
            &mut cursors.cancelled
        } else {
            &mut cursors.issued
        };
        let _ =
            advance_reconciliation_cursor(slot, previous.generation, next_key, next_upper_fence);
        drop(cursors);
        drop(db);
        let mut terminal = 0_u32;
        let mut errors = 0_u32;
        for row in &pending {
            let request = JobCancelRequest {
                schema_version: 1,
                job_id: row.get(0),
            };
            let outcome = if row.get::<_, String>(2) == "cancelled" {
                self.cancel(&row.get::<_, String>(1), &request)
            } else {
                self.observe(
                    &row.get::<_, String>(1),
                    &JobObserveRequest {
                        schema_version: 1,
                        job_id: request.job_id,
                        wait_ms: 0,
                        wait_until: JobObserveWaitUntil::Terminal,
                        stdout_tail_bytes: 0,
                        stderr_tail_bytes: 0,
                        stdout_offset: None,
                        stderr_offset: None,
                    },
                )
            };
            match outcome {
                Ok(value) if value.execution_terminal => terminal += 1,
                Ok(_) => (),
                Err(_) => errors += 1,
            }
        }
        Ok(json!({"inspected":pending.len(),"terminal":terminal,"errors":errors}))
    }
}
