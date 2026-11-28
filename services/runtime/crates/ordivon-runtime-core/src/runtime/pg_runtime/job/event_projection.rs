use super::*;

// The aggregate and bounded timeline must observe the SAME PostgreSQL
// statement snapshot. A timeline limit is not an episode-count limit.
pub(super) fn read_job_events(
    client: &mut postgres::Client,
    job: &str,
    created: u64,
    limit: u32,
) -> RuntimeResult<(RuntimeInspectionEpisodes, Vec<RuntimeInspectionEvent>, bool)> {
    let rows = client
        .query(
            "WITH grouped AS (
                SELECT event_type,attempt_id,count(*) AS n FROM job_events
                WHERE job_id=$1 GROUP BY event_type,attempt_id
             ), summary AS (
                SELECT
                    COALESCE(sum(n) FILTER(WHERE event_type='DISPATCH_ISSUED'),0)::bigint,
                    COALESCE(sum(n-1) FILTER(WHERE event_type='DISPATCH_ISSUED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='STOP_REQUESTED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='RECONCILIATION_FAILED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='RECONCILIATION_CONVERGED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='RUNNER_RESULT_RECOVERED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='JOB_RESOLUTION_CORRECTED'),0)::bigint,
                    COALESCE(sum(n) FILTER(WHERE event_type='ADMIN_TERMINAL_REPAIR'),0)::bigint
                FROM grouped
             )
             SELECT summary.*,e.event_sequence,e.attempt_id,e.event_type,e.origin,
                    e.previous_state,e.new_state,e.reason_code,e.observed_at_ms
             FROM summary LEFT JOIN LATERAL (
                SELECT event_sequence,attempt_id,event_type,origin,previous_state,new_state,
                       reason_code,observed_at_ms FROM job_events
                WHERE job_id=$1 ORDER BY event_sequence LIMIT $2
             ) e ON true ORDER BY e.event_sequence",
            &[&job, &(i64::from(limit) + 1)],
        )
        .map_err(pg_read_error)?;
    let summary = rows.first().ok_or_else(|| error("missing event summary"))?;
    let count = |i: usize| summary.get::<_, i64>(i) as u64;
    let episodes = RuntimeInspectionEpisodes {
        dispatches: count(0),
        duplicate_dispatches: count(1),
        stop_requests: count(2),
        reconciliation_failures: count(3),
        reconciliation_convergences: count(4),
        runner_result_recoveries: count(5),
        resolution_corrections: count(6),
        administrative_repairs: count(7),
    };
    let mut previous = created;
    let mut timeline = Vec::new();
    for row in rows.iter().take(limit as usize) {
        let Some(sequence) = row.get::<_, Option<i64>>(8) else {
            continue; // Aggregate row for a Job with no events.
        };
        let at = row.get::<_, i64>(15) as u64;
        let delta = at.saturating_sub(previous);
        previous = at;
        timeline.push(RuntimeInspectionEvent {
            sequence: sequence as u64,
            attempt_id: row.get(9),
            event_type: row.get(10),
            origin: row.get(11),
            previous_state: row.get(12),
            new_state: row.get(13),
            reason_code: row.get(14),
            observed_at_ms: at,
            elapsed_ms: at.saturating_sub(created),
            delta_ms: delta,
            detail: None,
        });
    }
    let truncated = rows.len() > limit as usize
        && rows
            .last()
            .is_some_and(|row| row.get::<_, Option<i64>>(8).is_some());
    Ok((episodes, timeline, truncated))
}

#[cfg(test)]
mod event_projection_tests {
    use super::*;

    #[test]
    #[ignore = "requires isolated native PostgreSQL fixture"]
    fn pg18_job_event_summary_is_complete_and_preserves_attempt_identity() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("disposable test PG DSN");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        // Session-local temporary relation; never write the installed Job journal.
        db.batch_execute(
            "CREATE TEMP TABLE job_events(
                job_id text, event_sequence bigint, attempt_id text, event_type text,
                origin text,previous_state text,new_state text,reason_code text,observed_at_ms bigint
             )",
        ).unwrap();
        for (sequence, attempt, event) in [
            (1_i64, None, "REQUEST_RECEIVED"),
            (2, Some("old"), "DISPATCH_ISSUED"),
            (3, Some("old"), "DISPATCH_ISSUED"),
            (4, Some("new"), "DISPATCH_ISSUED"),
            (5, Some("new"), "STOP_REQUESTED"),
            (6, Some("new"), "RECONCILIATION_FAILED"),
            (7, Some("new"), "RECONCILIATION_CONVERGED"),
            (8, Some("new"), "RUNNER_RESULT_RECOVERED"),
            (9, None, "JOB_RESOLUTION_CORRECTED"),
            (10, None, "ADMIN_TERMINAL_REPAIR"),
        ] {
            db.execute(
                "INSERT INTO job_events VALUES('job',$1,$2,$3,'SYSTEM_DERIVED',NULL,NULL,'TEST',$1::bigint+100)",
                &[&sequence, &attempt, &event],
            ).unwrap();
        }
        db.batch_execute("INSERT INTO job_events VALUES('other',1,'x','DISPATCH_ISSUED','SYSTEM_DERIVED',NULL,NULL,'TEST',101)").unwrap();
        for limit in [0, 1, 5, 10, 100] {
            let (summary, events, truncated) = read_job_events(&mut db, "job", 100, limit).unwrap();
            assert_eq!(summary.dispatches, 3);
            assert_eq!(summary.duplicate_dispatches, 1);
            assert_eq!(summary.stop_requests, 1);
            assert_eq!(summary.reconciliation_failures, 1);
            assert_eq!(summary.reconciliation_convergences, 1);
            assert_eq!(summary.runner_result_recoveries, 1);
            assert_eq!(summary.resolution_corrections, 1);
            assert_eq!(summary.administrative_repairs, 1);
            assert_eq!(events.len(), usize::try_from(limit.min(10)).unwrap());
            assert_eq!(truncated, limit < 10);
            if limit >= 1 {
                assert_eq!(events[0].attempt_id, None);
            }
            if limit >= 5 {
                assert_eq!(events[1].attempt_id.as_deref(), Some("old"));
                assert_eq!(events[3].attempt_id.as_deref(), Some("new"));
            }
        }
        let (summary, events, truncated) = read_job_events(&mut db, "missing", 100, 0).unwrap();
        assert_eq!(summary.dispatches, 0);
        assert!(events.is_empty());
        assert!(!truncated);
    }
}
