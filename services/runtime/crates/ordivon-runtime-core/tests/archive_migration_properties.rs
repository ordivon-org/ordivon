#![cfg(feature = "operator-tools")]

use ordivon_runtime_core::{inspect_registry_archive, RuntimeInspectionConfig};
use proptest::prelude::*;
use proptest::test_runner::{FileFailurePersistence, TestCaseResult};
use rusqlite::{params, Connection};
use serde_json::Value;
use std::collections::BTreeMap;

const MIGRATIONS: [&str; 6] = [
    include_str!("../migrations/runtime/0001_runtime.sql"),
    include_str!("../migrations/runtime/0002_orphan_recovery.sql"),
    include_str!("../migrations/runtime/0003_terminal_repair.sql"),
    include_str!("../migrations/runtime/0004_orphan_reclaim.sql"),
    include_str!("../migrations/runtime/0005_condition_retirement.sql"),
    include_str!("../migrations/runtime/0006_workspace_patch_retirement.sql"),
];
const AUXILIARY: [&str; 4] = [
    include_str!("../src/runtime/execution_provider_storage.sql"),
    include_str!("../src/runtime/attempt_supervisor_owner_storage.sql"),
    include_str!("../src/runtime/host_dependency_storage.sql"),
    include_str!("../src/runtime/runtime_release_storage.sql"),
];
const CUTOFF: u64 = 100;

// 0: absent, 1: explicit false, 2: true, 3: unrecognized historical status.
// Native schema 4 permits arbitrary status text; migration 5 can leave a
// NULL flag with non-NULL evidence. Neither representation means clearance.
type Fact = (u8, u8, bool, bool, u8, String);

fn migrate(db: &mut Connection, version: usize) {
    let tx = db.transaction().unwrap();
    tx.execute_batch(MIGRATIONS[version - 1]).unwrap();
    tx.execute(
        "INSERT INTO schema_migrations VALUES (?1,?2,'test-sql-only',0)",
        params![version, format!("fixture-{version}")],
    )
    .unwrap();
    tx.commit().unwrap();
}

fn observe(facts: &[Fact]) -> TestCaseResult {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("archive.sqlite3");
    let mut db = Connection::open(&path).unwrap();
    db.pragma_update(None, "foreign_keys", true).unwrap();
    for v in 1..=4 {
        migrate(&mut db, v);
    }
    for sql in AUXILIARY {
        db.execute_batch(sql).unwrap();
    }
    let mut classifications = BTreeMap::new();
    let mut expected_ids = Vec::new();
    let mut expected_bytes = 0u64;
    let mut expected_events = 0u64;
    let mut expected_artifacts = 0u64;
    let mut expected_payload = 0u64;
    let mut expected_conditions = 0u64;
    for (i, (older, latest, held, young, fanout, unicode)) in facts.iter().enumerate() {
        let job = format!("j{i:03}");
        let plan = serde_json::json!({"args": [unicode]}).to_string();
        let snapshot = serde_json::json!({"workspace": "路径"}).to_string();
        let created = if *young { CUTOFF } else { i as u64 };
        db.execute("INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution) VALUES(?1,'p',?1,'d','d','ws',?2,?3,'d',?4,'run','succeeded')",params![job,snapshot,plan,created]).unwrap();
        db.execute(
            "INSERT INTO idempotency_keys VALUES('p',?1,'d',?1,?2)",
            params![job, created],
        )
        .unwrap();
        for (n, marker) in [(1, *older), (2, *latest)] {
            let attempt = format!("{job}-{n}");
            db.execute("INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms) VALUES(?1,?2,?3,'succeeded','natural','d','/fixture',?1,?4)",params![attempt,job,n,created]).unwrap();
            let is_held = *held && n == 1;
            db.execute("INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,released_at_ms) VALUES(?1,?1,8,?2,?3,?4)",params![attempt,if is_held {"held_orphaned"} else {"released"},created,if is_held {None} else {Some(created+1)}]).unwrap();
            if marker != 0 {
                let status = ["", "false", "true", "unknown"][usize::from(marker)];
                db.execute("INSERT INTO attempt_conditions VALUES(?1,'recovery_required',?2,'fixture','digest',?3)",params![attempt,status,created]).unwrap();
            }
        }
        for n in 0..*fanout {
            let id = format!("{job}-extra-{n}");
            let attempt = format!("{job}-1");
            db.execute("INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,reason_code,detail_json,detail_digest,observed_at_ms) VALUES(?1,?2,?3,?4,'FIXTURE','SYSTEM_DERIVED','fixture','{}','d',?5)",params![id,job,attempt,u64::from(n)+1,created]).unwrap();
            db.execute("INSERT INTO artifacts(artifact_id,job_id,attempt_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms) VALUES(?1,?2,?3,'stdout',?1,'d','text/plain',?4,0,?5)",params![id,job,attempt,n,created]).unwrap();
        }
        // Oracle from fixture facts, not SQL predicates or output.
        let label = if *young {
            "younger_than_minimum_age"
        } else if *older >= 2 || *latest >= 2 {
            "recovery_required_or_unknown"
        } else if *held {
            "active_or_held_reservation"
        } else {
            "eligible"
        };
        *classifications.entry(label.to_string()).or_insert(0u64) += 1;
        if label == "eligible" {
            expected_ids.push(job);
            expected_bytes += (plan.len() + snapshot.len()) as u64;
            expected_events += u64::from(*fanout);
            expected_artifacts += u64::from(*fanout);
            expected_payload += (0..u64::from(*fanout)).sum::<u64>();
            expected_conditions += u64::from(*older != 0) + u64::from(*latest != 0);
        }
    }
    for version in 4..=6 {
        if version > 4 {
            migrate(&mut db, version);
        }
        let fk_errors: u64 = db
            .query_row("SELECT count(*) FROM pragma_foreign_key_check", [], |r| {
                r.get(0)
            })
            .unwrap();
        prop_assert_eq!(fk_errors, 0);
        let before = std::fs::read(&path).unwrap();
        let report = inspect_registry_archive(
            &RuntimeInspectionConfig {
                db_path: path.clone(),
                busy_timeout_ms: 1000,
            },
            CUTOFF,
            100,
        )
        .unwrap();
        let actual: BTreeMap<_, _> = report
            .by_classification
            .iter()
            .map(|r| (r.classification.clone(), r.jobs))
            .collect();
        prop_assert_eq!(&actual, &classifications, "schema {}", version);
        let ids: Vec<_> = report
            .eligible_sample
            .iter()
            .map(|r| r.job_id.clone())
            .collect();
        prop_assert_eq!(&ids, &expected_ids);
        for sample in report.eligible_sample {
            prop_assert_eq!(sample.effective_attempt_id, format!("{}-2", sample.job_id));
            prop_assert_eq!(sample.job_current_attempt_id, None);
        }
        let actual = serde_json::to_value(report.eligible_closure).unwrap();
        let n = expected_ids.len() as u64;
        let expected: Value = serde_json::json!({
            "jobs": n,"attempts": n*2,"idempotencyKeys": n,"reservations": n*2,
            "events":expected_events,"artifacts":expected_artifacts,
            "conditions":if version==4 {expected_conditions} else {0},
            "executionProviders":0,"hostDependencies":0,"supervisorOwners":0,
            "artifactLogicalPayloadBytes":expected_payload,"jobJsonLogicalBytes":expected_bytes
        });
        prop_assert_eq!(actual, expected);
        prop_assert_eq!(std::fs::read(&path).unwrap(), before);
    }
    Ok(())
}

#[test]
fn migrated_unknown_recovery_cannot_become_absent() {
    observe(&[(3, 0, false, false, 1, "中😀".into())]).unwrap();
}

proptest! {
    #![proptest_config(ProptestConfig { cases: 48, failure_persistence: Some(Box::new(FileFailurePersistence::WithSource("proptest-regressions"))), ..ProptestConfig::default() })]
    #[test]
    fn real_migration_archive_refinement(
        facts in prop::collection::vec((0u8..4,0u8..4,any::<bool>(),any::<bool>(),0u8..4,
            prop::collection::vec(prop::sample::select(vec!['a','中','😀','é','\0']),0..10)
                .prop_map(|s|s.into_iter().collect::<String>())),1..12)
    ) {
        observe(&facts)?;
    }
}
