//! Historical read-projection refinement, not the production writer contract.
//! All writes are restricted to exclusively created disposable native fixtures.
use super::*;
use std::path::Path;

#[derive(Clone, Debug, Default)]
struct JobFacts {
    resolved: bool,
    terminal: bool,
    released: bool,
    recovery: u8,
    supervisor: bool,
    effect: bool,
    artifacts: u64,
    payload: u64,
}

fn fixture(path: &Path) -> Connection {
    std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    let mut db = Connection::open(path).unwrap();
    assert_eq!(
        db.query_row("PRAGMA journal_mode=WAL", [], |r| r.get::<_, String>(0))
            .unwrap(),
        "wal"
    );
    db.pragma_update(None, "synchronous", "FULL").unwrap();
    db.pragma_update(None, "foreign_keys", true).unwrap();
    for v in 1..=4 {
        migrate(&mut db, v);
    }
    for sql in AUXILIARY {
        db.execute_batch(sql).unwrap();
    }
    for i in 0..3 {
        let j = format!("j{i}");
        db.execute("INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state) VALUES(?1,'p',?1,'d','d','ws','{}','{}','d',?2,'run')",params![j,i]).unwrap();
        db.execute("INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms) VALUES(?1,?1,1,'running','natural','d','/fixture',?1,?2)",params![j,i]).unwrap();
        db.execute(
            "INSERT INTO idempotency_keys VALUES('p',?1,'d',?1,?2)",
            params![j, i],
        )
        .unwrap();
        db.execute("INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms) VALUES(?1,?1,8,'active',?2)",params![j,i]).unwrap();
    }
    db
}

fn expected_label(m: &JobFacts, old_enough: bool) -> &'static str {
    if !m.resolved {
        "unresolved"
    } else if !old_enough {
        "younger_than_minimum_age"
    } else if m.effect {
        "runtime_release_effect"
    } else if !m.terminal {
        "attempt_not_stable_terminal"
    } else if m.recovery >= 2 {
        "recovery_required_or_unknown"
    } else if !m.released {
        "active_or_held_reservation"
    } else if m.supervisor {
        "supervisor_owner_present"
    } else {
        "eligible"
    }
}

fn check(
    path: &Path,
    version: usize,
    models: &[JobFacts; 3],
    cutoff: u64,
    limit: u32,
) -> TestCaseResult {
    let r = inspect_registry_archive(
        &RuntimeInspectionConfig {
            db_path: path.to_owned(),
            busy_timeout_ms: 1000,
        },
        cutoff,
        limit,
    )
    .unwrap();
    prop_assert_eq!(r.migration_version, version as i64);
    let mut counts = BTreeMap::new();
    let mut ids = Vec::new();
    let (mut artifacts, mut payload, mut conditions) = (0, 0, 0);
    for (i, m) in models.iter().enumerate() {
        let label = expected_label(m, (i as u64) < cutoff);
        counts
            .entry(label.to_string())
            .and_modify(|n| *n += 1)
            .or_insert(1u64);
        if label == "eligible" {
            ids.push(format!("j{i}"));
            artifacts += m.artifacts;
            payload += m.payload;
            if version == 4 && m.recovery != 0 {
                conditions += 1;
            }
        }
    }
    let actual: BTreeMap<_, _> = r
        .by_classification
        .iter()
        .map(|x| (x.classification.clone(), x.jobs))
        .collect();
    prop_assert_eq!(actual, counts);
    let n = ids.len() as u64;
    prop_assert_eq!(
        serde_json::to_value(&r.eligible_closure).unwrap(),
        serde_json::json!({
            "jobs":n,"attempts":n,"idempotencyKeys":n,"reservations":n,"events":0,
            "artifacts":artifacts,"conditions":conditions,"executionProviders":0,
            "hostDependencies":0,"supervisorOwners":0,"artifactLogicalPayloadBytes":payload,
            "jobJsonLogicalBytes":4*n
        })
    );
    ids.truncate(limit as usize);
    prop_assert_eq!(
        r.eligible_sample
            .iter()
            .map(|s| s.job_id.clone())
            .collect::<Vec<_>>(),
        ids
    );
    for s in r.eligible_sample {
        prop_assert_eq!(s.job_id, s.effective_attempt_id);
    }
    Ok(())
}

fn apply(
    db: &Connection,
    version: &mut usize,
    model: &mut JobFacts,
    index: usize,
    action: u8,
    step: usize,
) {
    let j = format!("j{index}");
    match action {
        0 => {
            db.execute(
                "UPDATE attempts SET state='succeeded' WHERE attempt_id=?1",
                [&j],
            )
            .unwrap();
            model.terminal = true;
        }
        1 => {
            db.execute(
                "UPDATE jobs SET resolution='succeeded' WHERE job_id=?1",
                [&j],
            )
            .unwrap();
            model.resolved = true;
        }
        2 => {
            if *version == 4 {
                db.execute("UPDATE concurrency_reservations SET state='released',released_at_ms=10 WHERE attempt_id=?1",[&j]).unwrap();
            } else {
                db.execute("UPDATE concurrency_reservations SET state='released',released_at_ms=10,state_observed_at_ms=10 WHERE attempt_id=?1",[&j]).unwrap();
            }
            model.released = true;
        }
        3..=5 => {
            let marker = action - 2; // 1=false, 2=true, 3=unknown (legacy only)
            if *version == 4 {
                let status = ["", "false", "true", "unknown"][marker as usize];
                db.execute("INSERT INTO attempt_conditions VALUES(?1,'recovery_required',?2,'fixture','digest',10) ON CONFLICT(attempt_id,condition_type) DO UPDATE SET status=excluded.status",params![j,status]).unwrap();
                model.recovery = marker;
            } else if marker != 3 {
                db.execute("UPDATE attempts SET recovery_required=?2,recovery_reason_code='fixture',recovery_evidence_digest='digest',recovery_observed_at_ms=10 WHERE attempt_id=?1",params![j,marker-1]).unwrap();
                model.recovery = marker;
            }
        }
        6 => {
            if *version == 4 {
                db.execute("DELETE FROM attempt_conditions WHERE attempt_id=?1 AND condition_type='recovery_required'",[&j]).unwrap();
            } else {
                db.execute("UPDATE attempts SET recovery_required=NULL,recovery_reason_code=NULL,recovery_evidence_digest=NULL,recovery_observed_at_ms=NULL WHERE attempt_id=?1",[&j]).unwrap();
            }
            model.recovery = 0;
        }
        7 => {
            if model.supervisor {
                db.execute(
                    "DELETE FROM attempt_supervisor_owners WHERE attempt_id=?1",
                    [&j],
                )
                .unwrap();
            } else {
                db.execute(
                    "INSERT INTO attempt_supervisor_owners VALUES(?1,'{}','d')",
                    [&j],
                )
                .unwrap();
            }
            model.supervisor = !model.supervisor;
        }
        8 => {
            db.execute("INSERT OR IGNORE INTO job_runtime_release_effects VALUES(?1,?1,'fixture','d','ws','rev','d',0,'receipt','d')",[&j]).unwrap();
            model.effect = true;
        }
        9 => {
            let id = format!("{j}-artifact-{step}");
            let size = (step % 17) as u64;
            db.execute("INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES(?1,?2,?2,'stdout',?1,'d','text/plain',?3,0,10)",params![id,j,size]).unwrap();
            model.artifacts += 1;
            model.payload += size;
        }
        10 if *version < 6 => {
            *version += 1;
            db.execute_batch(MIGRATIONS[*version - 1]).unwrap();
            db.execute(
                "INSERT INTO schema_migrations VALUES(?1,?2,'test-sql-only',0)",
                params![*version, format!("fixture-{version}")],
            )
            .unwrap();
        }
        _ => {}
    }
}

type Step = (usize, u8, bool);
fn trace(phases: &[Vec<Step>; 3]) -> TestCaseResult {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("stateful.sqlite3");
    let mut db = fixture(&path);
    let mut models: [JobFacts; 3] = std::array::from_fn(|_| JobFacts::default());
    let mut version = 4;
    check(&path, version, &models, 3, 3)?;
    // Every trace covers both migration boundaries and actual rolled-back DDL.
    // Reserve Job 0 for the unknown-marker witness, Job 1 for the effect witness.
    let prefix = [(0, 0, true), (0, 1, true), (0, 2, true), (0, 5, true)];
    let to_five = [
        (0, 10, false),
        (0, 10, true),
        (0, 6, true),
        (0, 9, true),
        (0, 7, true),
        (0, 7, true),
    ];
    let to_six = [
        (0, 10, true),
        (1, 0, true),
        (1, 1, true),
        (1, 2, true),
        (1, 8, false),
        (1, 8, true),
    ];
    for (step, &(index, action, commit)) in prefix
        .iter()
        .chain(&phases[0])
        .chain(&to_five)
        .chain(&phases[1])
        .chain(&to_six)
        .chain(&phases[2])
        .enumerate()
    {
        let mut pending = models.clone();
        let mut next_version = version;
        let tx = db.transaction().unwrap();
        apply(
            &tx,
            &mut next_version,
            &mut pending[index],
            index,
            action,
            step,
        );
        // A different real read-only connection must see the committed model,
        // even while a transaction has changed rows or the schema.
        check(&path, version, &models, 3, 3)?;
        if commit {
            tx.commit().unwrap();
            models = pending;
            version = next_version;
        } else {
            tx.rollback().unwrap();
        }
        check(
            &path,
            version,
            &models,
            (step % 4) as u64,
            (step % 4) as u32,
        )?;
        check(&path, version, &models, 3, 3)?;
    }
    drop(db);
    check(&path, version, &models, 3, 3)?;
    let reopened = Connection::open(&path).unwrap();
    let fk: u64 = reopened
        .query_row("SELECT count(*) FROM pragma_foreign_key_check", [], |r| {
            r.get(0)
        })
        .unwrap();
    prop_assert_eq!(fk, 0);
    Ok(())
}

proptest! {
    #![proptest_config(ProptestConfig {cases:24, failure_persistence:Some(Box::new(FileFailurePersistence::WithSource("proptest-regressions"))),..ProptestConfig::default()})]
    #[test]
    fn archive_stateful_transaction_refinement(
        before_five in prop::collection::vec((2usize..3,0u8..10,any::<bool>()),1..9),
        before_six in prop::collection::vec((2usize..3,0u8..10,any::<bool>()),1..9),
        after_six in prop::collection::vec((0usize..3,0u8..10,any::<bool>()),1..9)
    ) {
        trace(&[before_five,before_six,after_six])?;
    }
}

// The child creates a new private fixture, commits a baseline, and terminates
// without running Rust destructors. No pre-existing path may be opened.
#[test]
fn archive_wal_abrupt_process_exit_refinement() {
    const CHILD: &str = "ORDIVON_ARCHIVE_WAL_TEST_CHILD";
    if let Some(path) = std::env::var_os(CHILD) {
        let path = std::path::PathBuf::from(path);
        assert_eq!(path.file_name().unwrap(), "child.sqlite3");
        let mut db = fixture(&path);
        let mut m = JobFacts::default();
        let mut v = 4;
        let tx = db.transaction().unwrap();
        for a in [0, 1, 2] {
            apply(&tx, &mut v, &mut m, 0, a, 0);
        }
        tx.commit().unwrap();
        let tx = db.transaction().unwrap();
        apply(&tx, &mut v, &mut m, 0, 8, 1);
        apply(&tx, &mut v, &mut m, 0, 9, 2);
        if std::env::var_os("ORDIVON_ARCHIVE_WAL_TEST_COMMIT").is_some() {
            tx.commit().unwrap();
        }
        std::process::exit(77);
    }
    for committed in [false, true] {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("child.sqlite3");
        let mut command = std::process::Command::new(std::env::current_exe().unwrap());
        command
            .args([
                "--exact",
                "stateful::archive_wal_abrupt_process_exit_refinement",
                "--nocapture",
            ])
            .env(CHILD, &path)
            .env_remove("ORDIVON_ARCHIVE_WAL_TEST_COMMIT");
        if committed {
            command.env("ORDIVON_ARCHIVE_WAL_TEST_COMMIT", "1");
        }
        let status = command.status().unwrap();
        assert_eq!(status.code(), Some(77));
        let mut models: [JobFacts; 3] = std::array::from_fn(|_| JobFacts::default());
        models[0] = JobFacts {
            resolved: true,
            terminal: true,
            released: true,
            effect: committed,
            artifacts: u64::from(committed),
            payload: if committed { 2 } else { 0 },
            ..JobFacts::default()
        };
        check(&path, 4, &models, 3, 3).unwrap();
        let db = Connection::open(&path).unwrap();
        let n: u64 = db
            .query_row(
                "SELECT count(*) FROM job_runtime_release_effects",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(n, u64::from(committed));
        let n: u64 = db
            .query_row("SELECT count(*) FROM artifacts", [], |r| r.get(0))
            .unwrap();
        assert_eq!(n, u64::from(committed));
        assert_eq!(
            db.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0))
                .unwrap(),
            "ok"
        );
    }
}
