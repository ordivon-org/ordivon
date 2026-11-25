//! Real overlapping two-operation histories, with an independent finite
//! sequential oracle. Only committed PG lifecycle effects are modeled.
use super::*;
use crate::PgJobReadback;
use std::time::{Duration, Instant};

const LOCK: i64 = 79_245_017;

#[derive(Clone, Copy, Debug)]
enum Op {
    Cancel(i64),
    Terminal(&'static str),
}

const OPS: [Op; 6] = [
    Op::Cancel(10),
    Op::Cancel(11),
    Op::Terminal("failed"),
    Op::Terminal("cancelled"),
    Op::Terminal("lost"),
    Op::Terminal("orphaned"),
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Reply {
    Recorded,
    Committed,
    Existing,
    Conflict,
    Blocked,
    Aborted,
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
struct Model {
    cancel_at: Option<i64>,
    terminal: Option<&'static str>,
    events: Vec<(&'static str, i64)>,
}

impl Model {
    fn version(&self) -> i64 {
        i64::from(self.cancel_at.is_some()) + i64::from(self.terminal.is_some())
    }

    fn apply(&mut self, op: Op) -> Reply {
        match op {
            Op::Cancel(at) => {
                if self.cancel_at.is_some()
                    || self.terminal.is_some_and(|state| state != "orphaned")
                {
                    return Reply::Existing;
                }
                self.cancel_at = Some(at);
                self.events.push(("STOP_REQUESTED", at));
                Reply::Recorded
            }
            Op::Terminal(state) => {
                if let Some(winner) = self.terminal {
                    return if state == winner {
                        Reply::Existing
                    } else {
                        Reply::Conflict
                    };
                }
                // Every terminal proposal in this experiment was issued
                // against version zero, before any cancellation committed.
                if self.cancel_at.is_some() {
                    return Reply::Blocked;
                }
                self.terminal = Some(state);
                self.events.push(("PROCESS_EXITED", 100));
                self.events.push(("JOB_TERMINAL", 100));
                Reply::Committed
            }
        }
    }
}

// Actual known server aborts have no effect in a sequential history;
// UnknownCommit is deliberately not in the accepted response alphabet.
fn histories(ops: [Op; 2], replies: [Reply; 2]) -> Vec<Model> {
    let mut candidates = Vec::new();
    for order in [[0, 1], [1, 0]] {
        let mut model = Model::default();
        if order.into_iter().all(|index| {
            replies[index] == Reply::Aborted || model.apply(ops[index]) == replies[index]
        }) {
            candidates.push(model);
        }
    }
    candidates
}

#[test]
fn concurrent_history_oracle_rejects_two_terminal_winners_and_stale_cas() {
    let failure = Op::Terminal("failed");
    let orphan = Op::Terminal("orphaned");
    assert!(histories([failure, orphan], [Reply::Committed, Reply::Committed]).is_empty());
    let valid = histories([Op::Cancel(10), failure], [Reply::Recorded, Reply::Blocked]);
    assert_eq!(valid.len(), 1);
    assert_eq!(valid[0].cancel_at, Some(10));
    assert_eq!(valid[0].terminal, None);
    assert!(histories(
        [Op::Cancel(10), failure],
        [Reply::Recorded, Reply::Committed]
    )
    .is_empty());
    assert_eq!(
        histories([failure, failure], [Reply::Committed, Reply::Existing]).len(),
        1
    );
}

fn invoke(store: &mut PgAdmissionStore, input: &PgAdmissionInput, op: Op) -> Reply {
    let result = match op {
        Op::Cancel(at) => store
            .request_cancel_intent(&PgCancelIntent {
                job_id: input.job_id.clone(),
                observed_at_ms: input.created_at_ms + at,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .map(|outcome| match outcome {
                PgCancelOutcome::IntentRecorded(job) => {
                    assert_eq!(job, input.job_id);
                    Reply::Recorded
                }
                PgCancelOutcome::Existing(job) => {
                    assert_eq!(job, input.job_id);
                    Reply::Existing
                }
            }),
        Op::Terminal(state) => store
            .commit_terminal_no_artifacts(&PgTerminalNoArtifacts {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: 0,
                terminal_state: state.into(),
                result_digest: format!("sha256:history-{state}"),
                reason_code: "TEST_ONLY_HISTORY_RECEIPT".into(),
                exit_code: None,
                finished_at_ms: input.created_at_ms + 100,
                expected_source_sha256: input.expected_source_sha256.clone(),
            })
            .map(|outcome| match outcome {
                PgTerminalOutcome::Committed(job) => {
                    assert_eq!(job, input.job_id);
                    Reply::Committed
                }
                PgTerminalOutcome::Existing(job) => {
                    assert_eq!(job, input.job_id);
                    Reply::Existing
                }
            }),
    };
    match result {
        Ok(reply) => reply,
        Err(PgAdmissionError::Blocked) => Reply::Blocked,
        Err(PgAdmissionError::IdempotencyConflict) => Reply::Conflict,
        Err(PgAdmissionError::Database(error))
            if error.code() == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) =>
        {
            Reply::Aborted
        }
        other => panic!("unqualified history result: {op:?} {other:?}"),
    }
}

fn check(
    scratch: &mut Scratch,
    reader: &mut PgAdmissionStore,
    input: &PgAdmissionInput,
    model: &Model,
) {
    let PgJobReadback::Observed(snapshot) = reader
        .observe_job_readonly(&input.job_id, &input.expected_source_sha256)
        .unwrap()
    else {
        panic!("valid sequential model state must remain readable: {model:?}");
    };
    assert_eq!(snapshot.job_id, input.job_id);
    assert_eq!(snapshot.attempt_id, input.attempt_id);
    assert_eq!(snapshot.resolution.as_deref(), model.terminal);
    assert_eq!(snapshot.attempt_state, model.terminal.unwrap_or("accepted"));
    assert_eq!(
        snapshot.current_attempt_id.as_deref(),
        model
            .terminal
            .is_none()
            .then_some(input.attempt_id.as_str())
    );
    assert_eq!(snapshot.job_row_version, model.version());
    assert_eq!(snapshot.attempt_row_version, model.version());
    assert_eq!(
        snapshot.desired_state,
        if model.cancel_at.is_some() {
            "cancelled"
        } else {
            "run"
        }
    );
    assert_eq!(
        snapshot.termination_intent,
        if model.cancel_at.is_some() {
            "stop_requested"
        } else {
            "natural"
        }
    );
    assert_eq!(
        snapshot.reservation_state,
        match model.terminal {
            None => "active",
            Some("orphaned") => "held_orphaned",
            Some(_) => "released",
        }
    );
    assert_eq!(
        snapshot.result_digest,
        model
            .terminal
            .map(|state| format!("sha256:history-{state}"))
    );
    assert_eq!(snapshot.started_at_ms, None);
    assert_eq!(
        snapshot.finished_at_ms,
        model.terminal.map(|_| input.created_at_ms + 100)
    );
    let rows = scratch.admin.query(
        "SELECT event_sequence,event_type,observed_at_ms FROM job_events WHERE job_id=$1 ORDER BY event_sequence",
        &[&input.job_id],
    ).unwrap();
    assert_eq!(rows.len(), 3 + model.events.len());
    for (i, row) in rows.iter().enumerate() {
        assert_eq!(row.get::<_, i64>(0), i as i64 + 1);
    }
    for (row, (kind, offset)) in rows.iter().skip(3).zip(&model.events) {
        assert_eq!(row.get::<_, String>(1), *kind);
        assert_eq!(row.get::<_, i64>(2), input.created_at_ms + offset);
    }
    for table in [
        "jobs",
        "attempts",
        "concurrency_reservations",
        "idempotency_keys",
    ] {
        assert_eq!(scratch.count(table), 1);
    }
}

fn observed_events(scratch: &mut Scratch, input: &PgAdmissionInput) -> Vec<(String, i64)> {
    scratch.admin.query(
        "SELECT event_type,observed_at_ms FROM job_events WHERE job_id=$1 AND event_sequence > 3 ORDER BY event_sequence",
        &[&input.job_id],
    ).unwrap().iter().map(|r| (r.get(0), r.get::<_, i64>(1) - input.created_at_ms)).collect()
}

fn race(dsn: &str, ops: [Op; 2]) -> (usize, usize) {
    let mut scratch = Scratch::new(dsn);
    scratch.qualify();
    let input = payload("history-key", "history-job", "history-ws", 1);
    let mut reader = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
    let mut setup = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
    assert_eq!(
        setup.admit(&input).unwrap(),
        PgAdmissionOutcome::Created(input.job_id.clone())
    );
    check(&mut scratch, &mut reader, &input, &Model::default());

    let mut workers: Vec<_> = ops
        .into_iter()
        .map(|op| {
            let mut store = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
            store
                .client
                .batch_execute("SET statement_timeout='15s'")
                .unwrap();
            let pid: i32 = store
                .client
                .query_one("SELECT pg_backend_pid()", &[])
                .unwrap()
                .get(0);
            (op, store, pid)
        })
        .collect();
    let pids: Vec<i32> = workers.iter().map(|(_, _, pid)| *pid).collect();
    // Positive database barrier, not sleep-based scheduling. The actual
    // production transactions acquire this same advisory xact lock.
    scratch
        .admin
        .query_one("SELECT pg_advisory_lock($1)", &[&LOCK])
        .unwrap();
    let handles: Vec<_> = workers
        .drain(..)
        .map(|(op, mut store, _)| {
            let input = input.clone();
            thread::spawn(move || invoke(&mut store, &input, op))
        })
        .collect();
    let deadline = Instant::now() + Duration::from_secs(5);
    let overlap = loop {
        let count: i64 = scratch.admin.query_one(
            "SELECT count(DISTINCT pid) FROM pg_locks WHERE pid=ANY($1) AND locktype='advisory' AND classid=0 AND objid=$2::oid AND objsubid=1 AND NOT granted",
            &[&pids, &(LOCK as u32)],
        ).unwrap().get(0);
        if count == 2 {
            break true;
        }
        if Instant::now() >= deadline {
            break false;
        }
        thread::sleep(Duration::from_millis(5));
    };
    let before = scratch.count("job_events");
    let unlocked: bool = scratch
        .admin
        .query_one("SELECT pg_advisory_unlock($1)", &[&LOCK])
        .unwrap()
        .get(0);
    let replies: Vec<Reply> = handles
        .into_iter()
        .map(|handle| handle.join().unwrap())
        .collect();
    assert!(
        overlap && unlocked,
        "both actual writer transactions must overlap at the PG lock"
    );
    assert_eq!(before, 3, "no committed effect before release of barrier");
    let replies = [replies[0], replies[1]];
    assert!(
        replies.contains(&Reply::Committed) || replies.contains(&Reply::Recorded),
        "at least one original operation must commit"
    );
    let actual_events = observed_events(&mut scratch, &input);
    let mut model = histories(ops, replies)
        .into_iter()
        .find(|candidate| {
            candidate
                .events
                .iter()
                .map(|(kind, at)| (kind.to_string(), *at))
                .collect::<Vec<_>>()
                == actual_events
        })
        .unwrap_or_else(|| {
            panic!("no legal serial history: {ops:?} {replies:?} {actual_events:?}")
        });
    check(&mut scratch, &mut reader, &input, &model);

    // Retrying is explicit and only for an observed, server-aborted SQL
    // transaction. Never retry UnknownCommit or a physical OS operation.
    let mut aborts = 0;
    for (op, reply) in ops.into_iter().zip(replies) {
        if reply == Reply::Aborted {
            aborts += 1;
            let expected = model.apply(op);
            assert_eq!(
                invoke(&mut setup, &input, op),
                expected,
                "exact replay after known abort"
            );
            check(&mut scratch, &mut reader, &input, &model);
        }
    }
    // Guaranteed stale-version negative control after a cancel-only pair.
    if model.cancel_at.is_some() && model.terminal.is_none() {
        let stale = Op::Terminal("failed");
        assert_eq!(model.apply(stale), Reply::Blocked);
        assert_eq!(
            invoke(&mut setup, &input, stale),
            Reply::Blocked,
            "stale CAS cannot resolve current Job"
        );
        check(&mut scratch, &mut reader, &input, &model);
    }
    (1, aborts)
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_concurrent_cancel_terminal_histories_match_independent_model() {
    let dsn = physical_pg_test_dsn();
    let mut overlaps = 0;
    let mut aborted = 0;
    // Exhaust finite operation identities instead of relying on random coverage.
    for left in OPS {
        for right in OPS {
            let (overlap, aborts) = race(&dsn, [left, right]);
            overlaps += overlap;
            aborted += aborts;
        }
    }
    assert_eq!(overlaps, 36);
    println!("PG_HISTORY_PASS overlaps={overlaps} known_aborts={aborted}");
}
