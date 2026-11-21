//! Fair bounded PostgreSQL reconciliation epochs, independent of native effect execution.
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

#[cfg(test)]
mod scan_fairness_tests {
    use super::*;

    #[test]
    fn stale_scan_cannot_regress_fence_after_concurrent_advance_and_aba() {
        let x = (10, "job-010".to_string());
        let y = (110, "job-110".to_string());
        let z = (210, "job-210".to_string());
        let mut cursor = ReconciliationCursor {
            key: Some(x.clone()),
            upper_fence: Some(z.clone()),
            generation: 0,
        };
        let stale = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            0,
            Some(y.clone()),
            Some(z.clone())
        ));
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            1,
            Some(z.clone()),
            Some(z.clone())
        ));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            stale.generation,
            None,
            None
        ));
        assert_eq!(cursor.key, Some(z.clone()));
        assert_eq!(cursor.upper_fence, Some(z.clone()));

        // Exact fence reached: the next epoch starts at the oldest row.
        assert!(advance_reconciliation_cursor(&mut cursor, 2, None, None));
        let old_reset = cursor.clone();
        assert!(advance_reconciliation_cursor(
            &mut cursor,
            3,
            Some(x.clone()),
            Some(z.clone())
        ));
        assert!(advance_reconciliation_cursor(&mut cursor, 4, None, None));
        assert!(!advance_reconciliation_cursor(
            &mut cursor,
            old_reset.generation,
            Some(y),
            Some(z)
        ));
        assert!(cursor.key.is_none());
        assert!(cursor.upper_fence.is_none());
    }

    /// CurrentAttempt is a committed Job pointer: a newer numbered attempt
    /// can exist without owning the current native Runner / terminal decision.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_recovery_requires_current_attempt_not_highest_attempt_number() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
               job_id text PRIMARY KEY, current_attempt_id text,
               execution_plan_json text, operation_digest text);
             CREATE TEMP TABLE attempts (
               attempt_id text PRIMARY KEY, job_id text,
               attempt_number bigint, state text, termination_intent text,
               launch_token_digest text, bundle_path text, unit_name text,
               created_at_ms bigint, row_version bigint, bundle_digest text);
             INSERT INTO jobs VALUES
               ('job-a','attempt-current','{}','operation-a');
             INSERT INTO attempts VALUES
               ('attempt-current','job-a',4,'running','natural','launch-a',
                '/tmp/current','unit-current',10,9,NULL),
               ('attempt-future','job-a',5,'failed','natural','launch-b',
                '/tmp/future','unit-future',20,10,NULL);",
        )
        .unwrap();
        let selected = db
            .query_one(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert_eq!(
            selected.get::<_, String>(0),
            "attempt-current",
            "recovery must never substitute a higher-numbered Attempt"
        );
        assert_eq!(selected.len(), 12, "real AttemptNumber must be selected");
        assert_eq!(selected.get::<_, i64>(11), 4);
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='job-a'",
            &[],
        )
        .unwrap();
        let absent = db
            .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert!(
            absent.is_none(),
            "missing authoritative current Attempt must not fall back to history"
        );
        let unresolved = require_recovery_current_attempt(absent, "job-a").unwrap_err();
        assert_eq!(unresolved.code, RuntimeErrorCode::ReconciliationRequired);
        assert_eq!(unresolved.field.as_deref(), Some("currentAttemptId"));
        db.execute(
            "UPDATE jobs SET current_attempt_id='attempt-alien' WHERE job_id='job-a'",
            &[],
        )
        .unwrap();
        db.execute(
            "INSERT INTO jobs VALUES ('job-other','attempt-alien','{}','operation-other')",
            &[],
        )
        .unwrap();
        db.execute(
            "INSERT INTO attempts VALUES ('attempt-alien','job-other',1,'running',
               'natural','alien','/tmp/alien','unit-alien',30,0,NULL)",
            &[],
        )
        .unwrap();
        let foreign = db
            .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"job-a"])
            .unwrap();
        assert_eq!(
            require_recovery_current_attempt(foreign, "job-a")
                .unwrap_err()
                .code,
            RuntimeErrorCode::ReconciliationRequired,
            "foreign current Attempt must be reconciliation-required, not registry unavailable"
        );
    }

    /// A terminal Job commits resolution and *clears* current_attempt_id.
    /// Only the already verified snapshot Attempt may be shown to readers.
    /// Generic native release/reconcile effects must still require current.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_terminal_verified_readback_does_not_reauthorize_historical_effects() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, current_attempt_id text,
                resolution text, row_version bigint, execution_plan_json text,
                operation_digest text);
             CREATE TEMP TABLE job_runtime_release_effects (job_id text PRIMARY KEY);
             INSERT INTO job_runtime_release_effects VALUES ('terminal-a');
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text,
                attempt_number bigint, state text, termination_intent text,
                launch_token_digest text, bundle_path text, unit_name text,
                created_at_ms bigint, row_version bigint, bundle_digest text);
             INSERT INTO jobs VALUES
                ('terminal-a',NULL,'succeeded',8,'{}','op-a'),
                ('accepted-b','attempt-b',NULL,2,'{}','op-b');
             INSERT INTO attempts VALUES
                ('terminal-verified','terminal-a',4,'succeeded','natural',
                    'launch-a','/tmp/a','unit-a',10,7,NULL),
                ('later-unverified','terminal-a',5,'running','natural',
                    'launch-future','/tmp/future','unit-future',11,0,NULL),
                ('attempt-b','accepted-b',1,'accepted','natural',
                    'launch-b','/tmp/b','unit-b',12,0,NULL);",
        )
        .unwrap();

        // The existing dispatch/reconciliation entry must not try to
        // reauthorize a terminal ReleaseEffect after its PG current pointer
        // was atomically cleared. Unresolved accepted work still requires
        // strict current identity and stays eligible for normal reconciliation.
        let release_terminal = db
            .query_one(RECONCILIATION_STAGE_SQL, &[&"terminal-a"])
            .unwrap();
        assert_eq!(
            release_terminal.get::<_, Option<String>>(0).as_deref(),
            Some("succeeded")
        );
        assert!(release_terminal.get::<_, bool>(1));
        let unresolved_stage = db
            .query_one(RECONCILIATION_STAGE_SQL, &[&"accepted-b"])
            .unwrap();
        assert!(unresolved_stage.get::<_, Option<String>>(0).is_none());
        assert!(!unresolved_stage.get::<_, bool>(1));

        // In this fixture, the lifecycle/event verifier has already
        // established exact terminal-verified; a later historical Attempt
        // must not silently become the effect or readback authority.
        let verified: Option<String> = Some("succeeded".into());
        let row = db
            .query_one(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &8_i64,
                    &7_i64,
                    &verified,
                ],
            )
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "terminal-verified");
        assert_eq!(row.get::<_, i64>(11), 4);
        assert!(
            db.query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&"terminal-a"])
                .unwrap()
                .is_none(),
            "cleared terminal pointer must remain ineligible for native effects"
        );

        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"later-unverified",
                    &8_i64,
                    &0_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "later historical running Attempt cannot be projected as terminal"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"accepted-b",
                    &"terminal-verified",
                    &2_i64,
                    &7_i64,
                    &None::<String>
                ],
            )
            .unwrap()
            .is_none(),
            "Attempt must belong to requested Job"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &7_i64,
                    &7_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "stale Job row-version is inconclusive"
        );
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &"terminal-a",
                    &"terminal-verified",
                    &8_i64,
                    &6_i64,
                    &verified
                ],
            )
            .unwrap()
            .is_none(),
            "stale Attempt row-version is inconclusive"
        );

        let pending: Option<String> = None;
        let current = db
            .query_one(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[&"accepted-b", &"attempt-b", &2_i64, &0_i64, &pending],
            )
            .unwrap();
        assert_eq!(current.get::<_, String>(0), "attempt-b");
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='accepted-b'",
            &[],
        )
        .unwrap();
        assert!(
            db.query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[&"accepted-b", &"attempt-b", &2_i64, &0_i64, &pending],
            )
            .unwrap()
            .is_none(),
            "unresolved missing current remains fail closed"
        );
    }

    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_release_effect_uses_current_attempt_for_dispatch_boundary() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, current_attempt_id text);
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text,
                attempt_number bigint, state text);
             INSERT INTO jobs VALUES ('release-a','release-current');
             INSERT INTO attempts VALUES
                ('release-current','release-a',1,'accepted'),
                ('release-future','release-a',2,'running');",
        )
        .unwrap();
        let row = db
            .query_one(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&"release-a"])
            .unwrap();
        assert_eq!(row.get::<_, String>(0), "accepted");
        db.execute(
            "UPDATE jobs SET current_attempt_id=NULL WHERE job_id='release-a'",
            &[],
        )
        .unwrap();
        assert!(
            db.query_opt(RELEASE_CURRENT_ATTEMPT_STATE_SQL, &[&"release-a"])
                .unwrap()
                .is_none(),
            "missing release current pointer cannot borrow a historical Attempt"
        );
    }

    /// PostgreSQL allows current_attempt_id to refer to an Attempt belonging
    /// to another Job; a foreign key on attempts.job_id does not close this
    /// inverse identity edge. Recovery must not borrow another Job's state.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_recovery_rejects_cross_job_attempt_binding() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id text PRIMARY KEY, principal text, desired_state text,
                resolution text, current_attempt_id text, created_at_ms bigint
             );
             CREATE TEMP TABLE attempts (
                attempt_id text PRIMARY KEY, job_id text NOT NULL, state text
             );
             INSERT INTO jobs VALUES
               ('job-a','owner','run',NULL,'attempt-a',1),
               ('job-b','owner','run',NULL,'attempt-a',2);
             INSERT INTO attempts VALUES ('attempt-a','job-a','running');",
        )
        .unwrap();
        // The adversarial job-b references a real Attempt, but it belongs to
        // job-a; both the epoch fence and the page selector must reject it.
        let newest = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(newest.1, "job-a");
        let page = scan_reconciliation_page(&mut db, 100, false, None, &newest).unwrap();
        assert_eq!(page.len(), 1);
        assert_eq!(page[0].get::<_, String>(0), "job-a");
        db.execute(
            "UPDATE jobs SET desired_state='cancelled' WHERE job_id='job-b'",
            &[],
        )
        .unwrap();
        let cancelled = latest_reconciliation_key(&mut db, true).unwrap();
        assert!(
            cancelled.is_none(),
            "cancelled lane also requires attempt ownership"
        );
    }

    /// Real SQL and >100 unresolved Jobs in an explicitly disposable PG.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_scan_advances_beyond_blocked_oldest_page() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (job_id text, principal text, desired_state text, \
                resolution text, current_attempt_id text, created_at_ms bigint); \
             CREATE TEMP TABLE attempts (attempt_id text, job_id text, state text); \
             INSERT INTO jobs \
                SELECT 'job-' || lpad(n::text,3,'0'), 'owner', 'run', NULL, \
                       'attempt-' || n, n::bigint \
                FROM generate_series(1,101) n; \
             INSERT INTO attempts \
                SELECT 'attempt-' || n, 'job-' || lpad(n::text,3,'0'), 'running' \
                FROM generate_series(1,101) n;",
        )
        .unwrap();
        let upper = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(upper.1, "job-101");
        let first = scan_reconciliation_page(&mut db, 100, false, None, &upper).unwrap();
        assert_eq!(first.len(), 100);
        assert_eq!(first.last().unwrap().get::<_, String>(0), "job-100");
        let (next, same_fence) = next_reconciliation_cursor(&first, 100, &upper);
        assert_eq!(same_fence.as_ref(), Some(&upper));
        let second = scan_reconciliation_page(&mut db, 100, false, next.as_ref(), &upper).unwrap();
        assert_eq!(second.len(), 1);
        assert_eq!(second[0].get::<_, String>(0), "job-101");
        assert_eq!(
            next_reconciliation_cursor(&second, 100, &upper),
            (None, None)
        );

        db.batch_execute(
            "INSERT INTO jobs VALUES ('job-102','owner','run',NULL,'attempt-102',102);
             INSERT INTO attempts VALUES ('attempt-102','job-102','running');",
        )
        .unwrap();
        let fresh_upper = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        let revisited = scan_reconciliation_page(&mut db, 100, false, None, &fresh_upper).unwrap();
        assert_eq!(revisited[0].get::<_, String>(0), "job-001");

        db.execute(
            "UPDATE jobs SET desired_state='cancelled' WHERE job_id IN ('job-004','job-101')",
            &[],
        )
        .unwrap();
        let cancelled_upper = latest_reconciliation_key(&mut db, true).unwrap().unwrap();
        let cancelled =
            scan_reconciliation_page(&mut db, 100, true, None, &cancelled_upper).unwrap();
        assert_eq!(cancelled.len(), 2);
        assert_eq!(cancelled[0].get::<_, String>(0), "job-004");
        assert_eq!(cancelled[1].get::<_, String>(0), "job-101");
    }

    /// Every tick admits MORE than a full page of newer eligible Jobs.
    /// The previous short-page solution never wraps in this workload.
    #[test]
    #[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_sustained_full_pages_cannot_starve_oldest_epoch() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("use a dedicated disposable PostgreSQL cluster");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        db.batch_execute(
            "CREATE TEMP TABLE jobs (job_id text, principal text, desired_state text, \
                resolution text, current_attempt_id text, created_at_ms bigint); \
             CREATE TEMP TABLE attempts (attempt_id text, job_id text, state text); \
             INSERT INTO jobs \
                SELECT 'job-' || lpad(n::text,4,'0'), 'owner', 'run', NULL, \
                       'attempt-' || n, n::bigint \
                FROM generate_series(1,300) n; \
             INSERT INTO attempts \
                SELECT 'attempt-' || n, 'job-' || lpad(n::text,4,'0'), 'running' \
                FROM generate_series(1,300) n;",
        )
        .unwrap();
        let original_fence = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(original_fence.1, "job-0300");
        let mut cursor: Option<(i64, String)> = None;
        for page in 0..3 {
            let rows =
                scan_reconciliation_page(&mut db, 100, false, cursor.as_ref(), &original_fence)
                    .unwrap();
            assert_eq!(rows.len(), 100, "all three original epoch pages are full");
            assert_eq!(
                rows[0].get::<_, String>(0),
                format!("job-{:04}", 1 + page * 100)
            );
            let (next, fence) = next_reconciliation_cursor(&rows, 100, &original_fence);
            assert_eq!(fence.is_some(), page != 2);
            cursor = next;
            // A fresh 150 eligible Jobs after EVERY full page. Their sort
            // keys exceed original_fence and cannot prolong this epoch.
            let start = 301 + page * 150;
            let end = start + 149;
            db.batch_execute(&format!(
                "INSERT INTO jobs SELECT 'job-' || lpad(n::text,4,'0'), \
                    'owner','run',NULL,'attempt-' || n,n::bigint \
                   FROM generate_series({start},{end}) n; \
                 INSERT INTO attempts SELECT 'attempt-' || n, \
                      'job-' || lpad(n::text,4,'0'),'running' \
                   FROM generate_series({start},{end}) n;"
            ))
            .unwrap();
        }
        assert!(cursor.is_none(), "the full last page closes the epoch");
        // Directly falsify the old unbounded keyset behaviour in this same
        // real PostgreSQL: its next page would follow freshly admitted Jobs,
        // instead of revisiting the unresolved oldest row.
        let old_next: String = db
            .query_one(
                "SELECT j.job_id FROM jobs j JOIN attempts a                  ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id                  WHERE j.resolution IS NULL AND a.state='running'                  AND (j.created_at_ms,j.job_id) > (300,'job-0300')                  ORDER BY j.created_at_ms,j.job_id LIMIT 1",
                &[],
            )
            .unwrap()
            .get(0);
        assert_eq!(old_next, "job-0301");
        let fresh_fence = latest_reconciliation_key(&mut db, false).unwrap().unwrap();
        assert_eq!(fresh_fence.1, "job-0750");
        let revisited = scan_reconciliation_page(&mut db, 100, false, None, &fresh_fence).unwrap();
        assert_eq!(
            revisited[0].get::<_, String>(0),
            "job-0001",
            "continuous >=limit arrivals cannot prevent the oldest retry"
        );
    }
}
