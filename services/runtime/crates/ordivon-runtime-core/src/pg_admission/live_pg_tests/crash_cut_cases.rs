//! Native COMMIT interruption, using a private deferred trigger as a causal
//! barrier. No production fault hook, network simulation or OS process claim.
use super::*;
use crate::PgJobReadback;
use std::time::{Duration, Instant};

// A session lock held by the fixture blocks the deferred trigger at COMMIT.
// The second advisory key is the actual fixture backend PID, not a fixed
// cross-test lock. Only the writer PID created by this test is terminated.
fn interrupt_commit<T: Send>(
    scratch: &mut Scratch,
    dsn: &str,
    event: &str,
    effect: impl FnOnce(&mut PgAdmissionStore) -> Result<T, PgAdmissionError> + Send,
    observe_before_commit: impl FnOnce(&mut Scratch),
) -> Result<T, PgAdmissionError> {
    assert!(matches!(event, "ATTEMPT_CREATED" | "JOB_TERMINAL"));
    let controller: i32 = scratch
        .admin
        .query_one("SELECT pg_backend_pid()", &[])
        .unwrap()
        .get(0);
    let key = 20261126_i32;
    let mut writer = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
    writer
        .client
        .batch_execute("SET statement_timeout='20s'")
        .unwrap();
    let victim: i32 = writer
        .client
        .query_one("SELECT pg_backend_pid()", &[])
        .unwrap()
        .get(0);
    assert_ne!(controller, victim);
    scratch
        .admin
        .query_one("SELECT pg_advisory_lock($1,$2)", &[&key, &controller])
        .unwrap();
    scratch
        .admin
        .batch_execute(&format!(
            "CREATE FUNCTION fixture_commit_barrier() RETURNS trigger LANGUAGE plpgsql AS $$
         BEGIN PERFORM pg_advisory_xact_lock({key},{controller}); RETURN NEW; END; $$;
         CREATE CONSTRAINT TRIGGER fixture_commit_cut AFTER INSERT ON job_events
         DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (NEW.event_type='{event}')
         EXECUTE FUNCTION fixture_commit_barrier();"
        ))
        .unwrap();
    let result =
        thread::scope(|scope| {
            let worker = scope.spawn(move || effect(&mut writer));
            let deadline = Instant::now() + Duration::from_secs(8);
            loop {
                let blocked: bool = scratch.admin.query_one(
                "SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE pid=$1 AND state='active'
                  AND upper(trim(query))='COMMIT' AND $2=ANY(pg_blocking_pids(pid)))",
                &[&victim,&controller],
            ).unwrap().get(0);
                if blocked {
                    break;
                }
                assert!(
                    Instant::now() < deadline,
                    "never observed exact writer blocked in COMMIT"
                );
                thread::sleep(Duration::from_millis(10));
            }
            // An observer not participating in the uncommitted transaction must
            // still see the preceding committed cut, including event counts.
            observe_before_commit(scratch);
            let terminated: bool = scratch
                .admin
                .query_one("SELECT pg_terminate_backend($1,5000)", &[&victim])
                .unwrap()
                .get(0);
            assert!(
                terminated,
                "exact fixture writer backend was not terminated"
            );
            let absent: bool = scratch
                .admin
                .query_one(
                    "SELECT NOT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=$1)",
                    &[&victim],
                )
                .unwrap()
                .get(0);
            assert!(absent, "terminated fixture writer backend still present");
            worker.join().unwrap()
        });
    let unlocked: bool = scratch
        .admin
        .query_one("SELECT pg_advisory_unlock($1,$2)", &[&key, &controller])
        .unwrap()
        .get(0);
    assert!(unlocked);
    scratch
        .admin
        .batch_execute(
            "DROP TRIGGER fixture_commit_cut ON job_events; DROP FUNCTION fixture_commit_barrier()",
        )
        .unwrap();
    result
}

fn assert_admission_counts(scratch: &mut Scratch, jobs: i64, events: i64) {
    for table in [
        "jobs",
        "attempts",
        "idempotency_keys",
        "concurrency_reservations",
    ] {
        assert_eq!(scratch.count(table), jobs, "unexpected committed {table}");
    }
    assert_eq!(scratch.count("job_events"), events);
    assert_eq!(scratch.count("job_allocations"), 0);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_admission_connection_terminated_at_commit_is_unknown_and_atomic() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let input = payload(
        "commit-cut-admit",
        "commit-cut-job",
        "commit-cut-workspace",
        2,
    );
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let result = interrupt_commit(
        &mut scratch,
        &dsn,
        "ATTEMPT_CREATED",
        |writer| writer.admit(&input),
        |scratch| {
            assert_admission_counts(scratch, 0, 0);
            assert_eq!(
                observer.observe_admission(&input).unwrap(),
                PgAdmissionObservation::Inconclusive
            );
        },
    );
    assert!(
        matches!(result, Err(PgAdmissionError::UnknownCommit)),
        "COMMIT interruption must remain UNKNOWN: {result:?}"
    );
    // The private controller knows it terminated a blocked pre-commit
    // transaction. The public readback still cannot claim nonexistence.
    assert_admission_counts(&mut scratch, 0, 0);
    assert_eq!(
        observer.observe_admission(&input).unwrap(),
        PgAdmissionObservation::Inconclusive
    );
    let mut retry = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        retry.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(input.job_id.clone())
    );
    assert_eq!(
        observer.observe_admission(&input).unwrap(),
        PgAdmissionObservation::Confirmed(input.job_id.clone())
    );
    assert_eq!(
        retry.admit(&input).unwrap(),
        PgAdmissionOutcome::Existing(input.job_id.clone())
    );
    assert_admission_counts(&mut scratch, 1, 3);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_terminal_connection_terminated_at_commit_preserves_original_reservation() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    let input = payload(
        "commit-cut-terminal",
        "commit-cut-terminal-job",
        "commit-cut-workspace",
        2,
    );
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    observer.admit(&input).unwrap();
    let receipt = PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: 0,
        terminal_state: "orphaned".into(),
        result_digest: "sha256:commit-cut-terminal-fixture".into(),
        reason_code: "TEST_ONLY_TERMINAL_RECEIPT".into(),
        exit_code: None,
        finished_at_ms: input.created_at_ms + 1,
        expected_source_sha256: input.expected_source_sha256.clone(),
    };
    let mut accepted = |scratch: &mut Scratch| {
        assert_admission_counts(scratch, 1, 3);
        let PgJobReadback::Observed(snapshot) = observer
            .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
            .unwrap()
        else {
            panic!("preceding committed admission is not observable");
        };
        assert_eq!(
            snapshot.current_attempt_id.as_deref(),
            Some(input.attempt_id.as_str())
        );
        assert_eq!(snapshot.resolution, None);
        assert_eq!(snapshot.attempt_state, "accepted");
        assert_eq!(snapshot.reservation_state, "active");
        assert_eq!(snapshot.attempt_row_version, 0);
        assert_eq!(snapshot.result_digest, None);
    };
    let result = interrupt_commit(
        &mut scratch,
        &dsn,
        "JOB_TERMINAL",
        |writer| writer.commit_terminal_no_artifacts(&receipt),
        &mut accepted,
    );
    assert!(
        matches!(result, Err(PgAdmissionError::UnknownCommit)),
        "terminal COMMIT interruption must remain UNKNOWN: {result:?}"
    );
    accepted(&mut scratch);
    let mut retry = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        retry.commit_terminal_no_artifacts(&receipt).unwrap(),
        PgTerminalOutcome::Committed(input.job_id.clone())
    );
    assert_eq!(
        retry.commit_terminal_no_artifacts(&receipt).unwrap(),
        PgTerminalOutcome::Existing(input.job_id.clone())
    );
    let PgJobReadback::Observed(snapshot) = observer
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap()
    else {
        panic!("committed terminal receipt is not observable");
    };
    assert_eq!(snapshot.attempt_id, input.attempt_id);
    assert_eq!(snapshot.current_attempt_id, None);
    assert_eq!(snapshot.resolution.as_deref(), Some("orphaned"));
    assert_eq!(snapshot.reservation_state, "held_orphaned");
    assert_eq!(
        snapshot.result_digest.as_deref(),
        Some(receipt.result_digest.as_str())
    );
    assert_eq!(snapshot.attempt_row_version, 1);
    assert_admission_counts(&mut scratch, 1, 5);
}
