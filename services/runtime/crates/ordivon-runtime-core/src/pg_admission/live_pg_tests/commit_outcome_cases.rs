//! Native COMMIT-phase server-error injection, not an emulated connection.
use super::*;

fn deferred_commit_error(scratch: &mut Scratch, sqlstate: &str, attempts: i64) {
    // Sequences are deliberately nontransactional test witnesses: they record
    // how many real COMMIT attempts reached this deferred constraint trigger.
    assert!(matches!(sqlstate, "40001" | "23505"));
    scratch.admin.batch_execute(&format!(
        "CREATE SEQUENCE commit_probe_count;
         CREATE FUNCTION commit_probe_error() RETURNS trigger LANGUAGE plpgsql AS $probe$
         BEGIN
           IF NEW.event_type='ATTEMPT_CREATED' THEN
             IF nextval('commit_probe_count') <= {attempts} THEN
               RAISE EXCEPTION USING ERRCODE='{sqlstate}', MESSAGE='controlled COMMIT-phase failure';
             END IF;
           END IF;
           RETURN NEW;
         END;
         $probe$;
         CREATE CONSTRAINT TRIGGER commit_probe
         AFTER INSERT ON job_events DEFERRABLE INITIALLY DEFERRED
         FOR EACH ROW EXECUTE FUNCTION commit_probe_error();"
    )).unwrap();
}

fn attempted_commits(scratch: &mut Scratch) -> i64 {
    scratch
        .admin
        .query_one("SELECT last_value FROM commit_probe_count", &[])
        .unwrap()
        .get(0)
}

fn no_partial_admission(scratch: &mut Scratch) {
    for table in [
        "jobs",
        "attempts",
        "idempotency_keys",
        "concurrency_reservations",
        "job_events",
        "job_allocations",
    ] {
        assert_eq!(
            scratch.count(table),
            0,
            "partial admission escaped rollback: {table}"
        );
    }
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_admission_commit_serialization_abort_retries_same_identity_once() {
    let dsn = physical_pg_test_dsn();
    let mut scratch = Scratch::new(&dsn);
    scratch.qualify();
    deferred_commit_error(&mut scratch, "40001", 1);
    let input = payload("commit-ssi", "commit-ssi-job", "commit-ssi-ws", 1);
    let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    let mut observer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
    assert_eq!(
        writer.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(input.job_id.clone()),
        "server-confirmed COMMIT serialization abort is known rollback"
    );
    assert_eq!(
        attempted_commits(&mut scratch),
        2,
        "only one retry after the known abort"
    );
    assert_eq!(
        observer.observe_admission(&input).unwrap(),
        PgAdmissionObservation::Confirmed(input.job_id.clone())
    );
    assert_eq!(
        writer.admit(&input).unwrap(),
        PgAdmissionOutcome::Existing(input.job_id.clone())
    );
    for table in [
        "jobs",
        "attempts",
        "idempotency_keys",
        "concurrency_reservations",
    ] {
        assert_eq!(scratch.count(table), 1);
    }
    assert_eq!(scratch.count("job_events"), 3);
    assert_eq!(scratch.count("job_allocations"), 0);
    assert_eq!(attempted_commits(&mut scratch), 2);
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_admission_commit_serialization_abort_is_bounded_and_other_errors_remain_unknown() {
    let dsn = physical_pg_test_dsn();
    for (state, expected_attempts) in [("40001", 8), ("23505", 1)] {
        let mut scratch = Scratch::new(&dsn);
        scratch.qualify();
        deferred_commit_error(&mut scratch, state, 100);
        let input = payload(
            "commit-bounded",
            "commit-bounded-job",
            "commit-bounded-ws",
            1,
        );
        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.name).unwrap();
        let result = writer.admit(&input);
        if state == "40001" {
            assert!(
                matches!(result, Err(PgAdmissionError::Database(ref e)) if e.code() == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE)),
                "exact bounded server abort required: {result:?}"
            );
        } else {
            assert!(
                matches!(result, Err(PgAdmissionError::UnknownCommit)),
                "unclassified COMMIT errors remain UNKNOWN: {result:?}"
            );
        }
        assert_eq!(attempted_commits(&mut scratch), expected_attempts);
        no_partial_admission(&mut scratch);
    }
}
