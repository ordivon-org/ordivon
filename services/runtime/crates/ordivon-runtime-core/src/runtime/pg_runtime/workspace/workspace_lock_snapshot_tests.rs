//! Native business tests retained under semantic Workspace API; test source file name is not a contract.
use super::effect_tx::WORKSPACE_EFFECT_ISOLATION;
use super::*;
use std::sync::mpsc;

/// Reproduce the actual PostgreSQL advisory-lock MVCC order, not an
/// in-memory model. All writes are confined to an explicitly disposable
/// ORDIVON_PG_TEST_DSN. A Job inserted by the preceding lock owner MUST
/// be visible to Workspace.close/mutate after acquiring that same lock.
#[test]
#[ignore = "requires explicit disposable ORDIVON_PG_TEST_DSN"]
fn native_pg_workspace_lock_wait_observes_newly_committed_job_lease() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("dedicated disposable PostgreSQL cluster required");
    let mut admin = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    let table = format!("runtime_workspace_lock_{}", uuid::Uuid::now_v7().simple());
    admin
        .batch_execute(&format!("CREATE TABLE {table} (job_id TEXT PRIMARY KEY)"))
        .unwrap();
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        for (legacy, expected) in [(true, 0_i64), (false, 1_i64)] {
            admin
                .batch_execute(&format!("TRUNCATE TABLE {table}"))
                .unwrap();
            let mut holder = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
            let mut waiter = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
            let waiter_pid: i32 = waiter
                .query_one("SELECT pg_backend_pid()", &[])
                .unwrap()
                .get(0);
            let mut holder_tx = holder
                .build_transaction()
                .isolation_level(postgres::IsolationLevel::Serializable)
                .start()
                .unwrap();
            holder_tx
                .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
                .unwrap();
            holder_tx
                .execute(
                    &format!("INSERT INTO {table} VALUES ('admitted-before-release')"),
                    &[],
                )
                .unwrap();

            let (started, observed) = mpsc::sync_channel::<()>(1);
            let selected = table.clone();
            let thread = std::thread::spawn(move || {
                let mut waiting_tx = waiter
                    .build_transaction()
                    .isolation_level(if legacy {
                        postgres::IsolationLevel::Serializable
                    } else {
                        WORKSPACE_EFFECT_ISOLATION
                    })
                    .start()
                    .unwrap();
                started.send(()).unwrap();
                waiting_tx
                    .query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
                    .unwrap();
                let count: i64 = waiting_tx
                        .query_one(
                            &format!(
                                "SELECT count(*) FROM {selected} WHERE job_id='admitted-before-release'"
                            ),
                            &[],
                        )
                        .unwrap()
                        .get(0);
                waiting_tx.commit().unwrap();
                count
            });
            observed
                .recv_timeout(std::time::Duration::from_secs(2))
                .unwrap();
            let deadline = std::time::Instant::now() + std::time::Duration::from_secs(4);
            loop {
                let waiting = admin
                    .query_one(
                        "SELECT wait_event_type='Lock' AND wait_event='advisory' \
                         FROM pg_stat_activity WHERE pid=$1",
                        &[&waiter_pid],
                    )
                    .unwrap();
                if waiting.get::<_, Option<bool>>(0) == Some(true) {
                    break;
                }
                assert!(
                    std::time::Instant::now() < deadline,
                    "second PG transaction never waited on the actual advisory lock"
                );
                std::thread::sleep(std::time::Duration::from_millis(20));
            }
            // Only now may the prior Job admission complete. SERIALIZABLE
            // already pinned its MVCC snapshot before this COMMIT;
            // READ COMMITTED takes its next snapshot after this COMMIT.
            holder_tx.commit().unwrap();
            let seen = thread.join().unwrap();
            assert_eq!(
                    seen, expected,
                    "Workspace SQL must see a newly committed Job after lock acquisition; legacy SERIALIZABLE is a negative control"
                );
        }
    }));
    admin.batch_execute(&format!("DROP TABLE {table}")).unwrap();
    if let Err(panic) = result {
        std::panic::resume_unwind(panic);
    }
}
