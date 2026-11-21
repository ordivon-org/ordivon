//! Scan unresolved committed PostgreSQL jobs with fair, bounded recovery epochs.
//! Does not admit new Jobs; every action returns through existing PgRuntime methods.

use super::*;

/// One reconciliation epoch has a fixed upper sort key. Fresh jobs beyond
/// this bound wait for the next epoch instead of continually extending the
/// current scan and starving an older unresolved job.
/// PostgreSQL state, not this in-memory cursor, remains the authority.
pub(super) fn latest_reconciliation_key(
    client: &mut postgres::Client,
    cancelled_only: bool,
) -> Result<Option<(i64, String)>, postgres::Error> {
    const SQL: &str = r#"
        SELECT j.created_at_ms, j.job_id
        FROM jobs j
        JOIN attempts a ON a.attempt_id = j.current_attempt_id
          AND a.job_id = j.job_id
        WHERE j.resolution IS NULL
          AND (j.desired_state = 'cancelled'
               OR (NOT $1 AND a.state IN ('starting','running','stopping','recovering')))
        ORDER BY j.created_at_ms DESC, j.job_id DESC
        LIMIT 1
    "#;
    Ok(client
        .query_opt(SQL, &[&cancelled_only])?
        .map(|row| (row.get::<_, i64>(0), row.get::<_, String>(1))))
}

/// A bounded keyset page never crosses the epoch fence. A newly inserted
/// backdated row can be observed during a later epoch; an epoch is not a
/// repeatable-read snapshot, and the key is not a PostgreSQL commit sequence.
pub(super) fn scan_reconciliation_page(
    client: &mut postgres::Client,
    limit: u32,
    cancelled_only: bool,
    cursor: Option<&(i64, String)>,
    upper_fence: &(i64, String),
) -> Result<Vec<postgres::Row>, postgres::Error> {
    const SQL: &str = r#"
        SELECT j.job_id, j.principal, j.desired_state, j.created_at_ms
        FROM jobs j
        JOIN attempts a ON a.attempt_id = j.current_attempt_id
          AND a.job_id = j.job_id
        WHERE j.resolution IS NULL
          AND (j.desired_state = 'cancelled'
               OR (NOT $2 AND a.state IN ('starting','running','stopping','recovering')))
          AND ($3::BIGINT IS NULL
               OR (j.created_at_ms, j.job_id) > ($3::BIGINT, $4::TEXT))
          AND (j.created_at_ms, j.job_id) <= ($5::BIGINT, $6::TEXT)
        ORDER BY j.created_at_ms, j.job_id
        LIMIT $1
    "#;
    let (at, id) = cursor
        .map(|(at, id)| (Some(*at), Some(id.as_str())))
        .unwrap_or((None, None));
    client.query(
        SQL,
        &[
            &i64::from(limit),
            &cancelled_only,
            &at,
            &id,
            &upper_fence.0,
            &upper_fence.1,
        ],
    )
}

/// A partial page or reaching the exact epoch upper fence completes a sweep.
/// Reset both fields together so a new epoch can include freshly arrived jobs.
type ReconciliationNextPage = (Option<(i64, String)>, Option<(i64, String)>);

pub(super) fn next_reconciliation_cursor(
    pending: &[postgres::Row],
    limit: u32,
    upper_fence: &(i64, String),
) -> ReconciliationNextPage {
    let Some(last) = pending.last() else {
        return (None, None);
    };
    let key = (last.get::<_, i64>(3), last.get::<_, String>(0));
    // Use equality, not Rust's lexical >=: a PostgreSQL text collation can
    // order job_id strings differently from Rust's bytewise String order.
    if pending.len() < limit as usize || key == *upper_fence {
        (None, None)
    } else {
        (Some(key), Some(upper_fence.clone()))
    }
}

/// Version-stamped cursor/fence progress guards against concurrent scans and
/// ABA even when an epoch wraps to an earlier row or to None.
pub(super) fn advance_reconciliation_cursor(
    slot: &mut ReconciliationCursor,
    observed_generation: u64,
    next_key: Option<(i64, String)>,
    next_upper_fence: Option<(i64, String)>,
) -> bool {
    if slot.generation != observed_generation {
        return false;
    }
    let Some(generation) = slot.generation.checked_add(1) else {
        return false;
    };
    slot.key = next_key;
    slot.upper_fence = next_upper_fence;
    slot.generation = generation;
    true
}

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
