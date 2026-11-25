//! Generated, shrinkable traces against a real private PG writer and independent reader.
//! This models only admission, accepted cancellation, and durable terminal receipt
//! commits; it does not simulate or prove native process effects.
use super::*;
use crate::PgJobReadback;
use proptest::prelude::*;
use proptest::test_runner::{Config, RngSeed, TestRunner};
use std::cell::Cell;

const CASES: u32 = 32;
const SEED: u64 = 0x2026_1126_0014;

#[derive(Clone, Debug, Default)]
struct Model {
    cancel_at: Option<i64>,
    outcome: Option<&'static str>,
}

impl Model {
    fn version(&self) -> i64 {
        i64::from(self.cancel_at.is_some()) + i64::from(self.outcome.is_some())
    }

    fn reservation(&self) -> &'static str {
        match self.outcome {
            None => "active",
            Some("orphaned") => "held_orphaned",
            Some(_) => "released",
        }
    }

    fn events(&self) -> i64 {
        3 + i64::from(self.cancel_at.is_some()) + 2 * i64::from(self.outcome.is_some())
    }
}

const OUTCOMES: [&str; 4] = ["failed", "cancelled", "lost", "orphaned"];

fn receipt(input: &PgAdmissionInput, model: &Model, outcome: &str) -> PgTerminalNoArtifacts {
    PgTerminalNoArtifacts {
        attempt_id: input.attempt_id.clone(),
        expected_row_version: model.version(),
        terminal_state: outcome.into(),
        result_digest: format!("sha256:fixture-{outcome}"),
        reason_code: "MODEL_TEST_RECEIPT".into(),
        exit_code: None,
        finished_at_ms: input.created_at_ms + 100,
        expected_source_sha256: input.expected_source_sha256.clone(),
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
        panic!("valid model state must be readable: {model:?}");
    };
    assert_eq!(snapshot.job_id, input.job_id);
    assert_eq!(snapshot.attempt_id, input.attempt_id);
    assert_eq!(snapshot.resolution.as_deref(), model.outcome);
    assert_eq!(snapshot.attempt_state, model.outcome.unwrap_or("accepted"));
    assert_eq!(
        snapshot.current_attempt_id.as_deref(),
        model.outcome.is_none().then_some(input.attempt_id.as_str())
    );
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
    assert_eq!(snapshot.reservation_state, model.reservation());
    assert_eq!(snapshot.attempt_row_version, model.version());
    assert_eq!(snapshot.job_row_version, model.version());
    assert_eq!(snapshot.started_at_ms, None);
    assert_eq!(
        snapshot.finished_at_ms,
        model.outcome.map(|_| input.created_at_ms + 100)
    );
    assert_eq!(
        snapshot.result_digest,
        model
            .outcome
            .map(|outcome| format!("sha256:fixture-{outcome}"))
    );
    let events = scratch.admin.query(
        "SELECT event_sequence,event_type FROM job_events WHERE job_id=$1 ORDER BY event_sequence",
        &[&input.job_id],
    ).unwrap();
    assert_eq!(events.len() as i64, model.events());
    for (i, row) in events.iter().enumerate() {
        assert_eq!(row.get::<_, i64>(0), i as i64 + 1);
    }
    let kinds: Vec<String> = events.iter().map(|row| row.get(1)).collect();
    assert_eq!(
        kinds.iter().filter(|k| *k == "STOP_REQUESTED").count(),
        usize::from(model.cancel_at.is_some())
    );
    for kind in ["PROCESS_EXITED", "JOB_TERMINAL"] {
        assert_eq!(
            kinds.iter().filter(|k| k.as_str() == kind).count(),
            usize::from(model.outcome.is_some())
        );
    }
}

fn run_trace(dsn: &str, trace: &[(usize, u8, usize)]) {
    let mut scratch = Scratch::new(dsn);
    scratch.qualify();
    let mut writer = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
    let mut reader = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
    let inputs: Vec<_> = (0..3)
        .map(|i| {
            payload(
                &format!("model-key-{i}"),
                &format!("model-job-{i}"),
                "model-workspace",
                3,
            )
        })
        .collect();
    let mut models = [Model::default(), Model::default(), Model::default()];
    for input in &inputs {
        assert_eq!(
            writer.admit(input).unwrap(),
            PgAdmissionOutcome::Created(input.job_id.clone())
        );
    }
    // Every trace has a cancellation before resolution, a stale CAS, and a
    // replay. Generated actions then explore orderings across three Jobs.
    let prefix = [(0, 2, 0), (1, 4, 0), (2, 0, 0)];
    // Ensure orphan and terminal branches are reached even for a shrunk trace.
    let suffix = [(1, 3, 3), (1, 2, 0), (0, 3, 1), (2, 3, 0), (2, 5, 0)];
    for (step, &(index, action, variant)) in prefix.iter().chain(trace).chain(&suffix).enumerate() {
        let input = &inputs[index];
        let model = &mut models[index];
        let outcome = OUTCOMES[variant];
        let context = (step, index, action, variant);
        match action {
            0 => assert_eq!(
                writer.admit(input).unwrap(),
                PgAdmissionOutcome::Existing(input.job_id.clone()),
                "{context:?}"
            ),
            1 => {
                let mut conflict = input.clone();
                conflict.request_digest = "sha256:different-request".into();
                assert!(
                    matches!(
                        writer.admit(&conflict),
                        Err(PgAdmissionError::IdempotencyConflict)
                    ),
                    "{context:?}"
                );
            }
            2 => {
                let time = input.created_at_ms + step as i64 + 1;
                let cancel = PgCancelIntent {
                    job_id: input.job_id.clone(),
                    observed_at_ms: time,
                    expected_source_sha256: input.expected_source_sha256.clone(),
                };
                let first =
                    model.cancel_at.is_none() && matches!(model.outcome, None | Some("orphaned"));
                let actual = writer.request_cancel_intent(&cancel).unwrap();
                if first {
                    assert_eq!(
                        actual,
                        PgCancelOutcome::IntentRecorded(input.job_id.clone()),
                        "{context:?}"
                    );
                    model.cancel_at = Some(time);
                } else {
                    assert_eq!(
                        actual,
                        PgCancelOutcome::Existing(input.job_id.clone()),
                        "{context:?}"
                    );
                }
                let expected = if model.cancel_at == Some(time) {
                    PgCancelObservation::Confirmed(input.job_id.clone())
                } else {
                    PgCancelObservation::Inconclusive
                };
                assert_eq!(
                    reader.observe_cancel_intent(&cancel).unwrap(),
                    expected,
                    "{context:?}"
                );
            }
            3 => {
                let result = writer.commit_terminal_no_artifacts(&receipt(input, model, outcome));
                match model.outcome {
                    None => {
                        assert_eq!(
                            result.unwrap(),
                            PgTerminalOutcome::Committed(input.job_id.clone()),
                            "{context:?}"
                        );
                        model.outcome = Some(outcome);
                    }
                    Some(existing) if existing == outcome => assert_eq!(
                        result.unwrap(),
                        PgTerminalOutcome::Existing(input.job_id.clone()),
                        "{context:?}"
                    ),
                    Some(_) => assert!(
                        matches!(result, Err(PgAdmissionError::IdempotencyConflict)),
                        "{context:?}"
                    ),
                }
            }
            4 => {
                // Only unresolved Jobs have a fresh CAS to reject.
                if model.outcome.is_none() {
                    let mut stale = receipt(input, model, outcome);
                    stale.expected_row_version += 1;
                    assert!(
                        matches!(
                            writer.commit_terminal_no_artifacts(&stale),
                            Err(PgAdmissionError::Blocked)
                        ),
                        "{context:?}"
                    );
                }
            }
            5 => {
                if let Some(winner) = model.outcome {
                    let mut replay = receipt(input, model, winner);
                    replay.expected_row_version = 0;
                    assert_eq!(
                        writer.commit_terminal_no_artifacts(&replay).unwrap(),
                        PgTerminalOutcome::Existing(input.job_id.clone()),
                        "{context:?}"
                    );
                    replay.result_digest = "sha256:foreign-receipt".into();
                    assert!(
                        matches!(
                            writer.commit_terminal_no_artifacts(&replay),
                            Err(PgAdmissionError::IdempotencyConflict)
                        ),
                        "{context:?}"
                    );
                }
            }
            6 => {
                // Reconnect; never reissue an ambiguous physical command.
                writer = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
                reader = PgAdmissionStore::connect(dsn, &scratch.name).unwrap();
            }
            _ => unreachable!(),
        }
        for (input, model) in inputs.iter().zip(&models) {
            check(&mut scratch, &mut reader, input, model);
        }
        for table in [
            "jobs",
            "attempts",
            "idempotency_keys",
            "concurrency_reservations",
        ] {
            assert_eq!(scratch.count(table), 3, "{context:?} {table}");
        }
    }
}

#[test]
#[ignore = "requires explicit ORDIVON_PG_TEST_DSN physical PostgreSQL qualification"]
fn pg18_stateful_admission_cancel_terminal_matches_independent_reference() {
    let dsn = physical_pg_test_dsn();
    let completed = Cell::new(0u32);
    let config = Config {
        cases: CASES,
        rng_seed: RngSeed::Fixed(SEED),
        failure_persistence: None,
        ..Config::default()
    };
    let mut runner = TestRunner::new(config);
    let actions = proptest::collection::vec((0usize..3, 0u8..7, 0usize..4), 8..20);
    runner
        .run(&actions, |trace| {
            run_trace(&dsn, &trace);
            completed.set(completed.get() + 1);
            Ok(())
        })
        .unwrap();
    assert_eq!(completed.get(), CASES, "no empty or partial property run");
    eprintln!(
        "PG_STATEFUL_REFERENCE_PASS cases={} seed={SEED:#x}",
        completed.get()
    );
}
