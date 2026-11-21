//! PG keyset recovery epochs and ABA-safe cursor advancement, not a second state store.
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
