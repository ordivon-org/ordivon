//! PostgreSQL Runtime Workspace identity, mutation and inventory.
//! Consumer-safe retirement is isolated in workspace/retirement.rs.
use super::*;
mod retirement;

// The advisory lock serializes Job admission, terminal/lease updates and
// Workspace effects. A PostgreSQL SERIALIZABLE snapshot is frozen when the
// lock-acquisition SELECT starts, i.e. *before* the transaction actually
// acquires a contended lock. Such a snapshot can miss newly committed leases,
// even after the holder releases the lock and this transaction later commits.
// READ COMMITTED takes the Workspace guard queries' snapshots after the lock
// is acquired, matching the existing PG scheduler's lock+isolation protocol.
// The global lock is deliberately retained across Git/FS physical effects:
// moving them outside this fence requires an independently recoverable intent.
const WORKSPACE_EFFECT_ISOLATION: postgres::IsolationLevel =
    postgres::IsolationLevel::ReadCommitted;

// Reuse the existing legacy Runtime bounded-Git-probe pattern (452e0c):
// the PG-only page already batches SQL and still needs current Git truth.
const WORKSPACE_LIST_LIVE_GIT_PARALLELISM: usize = 4;

// The same PG consumer definition must govern Workspace mutation/close
// admission AND workspace.get/list projections. A resolved Job can still own
// an active or held_orphaned Attempt reservation: projecting only unresolved
// Jobs would incorrectly report activeJobIds=[] while close remains blocked.
// Build only trusted static query fragments; values remain PostgreSQL bind args.
const WORKSPACE_ACTIVE_OR_HELD: &str = "(
    j.resolution IS NULL OR j.job_id IN (
        SELECT a.job_id FROM attempts a
        JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
        WHERE r.state IN ('active','held_orphaned')
    )
)";

fn workspace_consumer_sql(select: &str, scope: &str, order_by: &str) -> String {
    format!("SELECT {select} FROM jobs j WHERE {scope} AND {WORKSPACE_ACTIVE_OR_HELD}{order_by}")
}

mod inventory;
mod mutation;
mod opening;
mod transaction;

#[cfg(test)]
mod workspace_active_consumer_tests {
    use super::*;

    /// Check actual PostgreSQL joins, not a mock predicate. A terminal Job
    /// with an orphaned/held reservation must appear in both consumer read
    /// projections because Workspace.close and mutate still own that lease.
    /// No production tables are touched; all fixture tables are TEMP.
    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_held_terminal_job_is_visible_to_workspace_reads_and_guards() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster required");
        let mut pg = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        pg.batch_execute(
            "CREATE TEMP TABLE jobs (
                job_id TEXT PRIMARY KEY, workspace_id TEXT, resolution TEXT,
                execution_plan_json TEXT, created_at_ms BIGINT
            );
            CREATE TEMP TABLE attempts (attempt_id TEXT PRIMARY KEY, job_id TEXT);
            CREATE TEMP TABLE concurrency_reservations (attempt_id TEXT, state TEXT);
            INSERT INTO jobs VALUES
                ('pending','ws-contract',NULL,'pending-plan',30),
                ('held-terminal','ws-contract','succeeded','held-plan',20),
                ('released-terminal','ws-contract','succeeded','released-plan',10);
            INSERT INTO attempts VALUES ('a-held','held-terminal'),('a-released','released-terminal');
            INSERT INTO concurrency_reservations VALUES
                ('a-held','held_orphaned'),('a-released','released');",
        )
        .unwrap();

        let exact = pg
            .query(
                &workspace_consumer_sql(
                    "j.job_id",
                    "j.workspace_id=$1",
                    " ORDER BY j.created_at_ms DESC",
                ),
                &[&"ws-contract"],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(0))
            .collect::<Vec<_>>();
        let ids = vec!["ws-contract".to_string()];
        let list = pg
            .query(
                &workspace_consumer_sql(
                    "j.workspace_id,j.job_id",
                    "j.workspace_id = ANY($1::TEXT[])",
                    " ORDER BY j.created_at_ms DESC",
                ),
                &[&ids],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(1))
            .collect::<Vec<_>>();
        let close_count: i64 = pg
            .query_one(
                &workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
                &[&"ws-contract"],
            )
            .unwrap()
            .get(0);
        let plans = pg
            .query(
                &workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
                &[&"ws-contract"],
            )
            .unwrap()
            .iter()
            .map(|row| row.get::<_, String>(0))
            .collect::<Vec<_>>();
        assert_eq!(exact, vec!["pending", "held-terminal"]);
        assert_eq!(list, exact, "get/list must not hide PG-held consumers");
        assert_eq!(
            close_count, 2,
            "close must protect every projected consumer"
        );
        assert_eq!(plans.len(), 2, "mutate must see the same PG consumers");
        assert!(plans.contains(&"held-plan".to_string()));
        assert!(!plans.contains(&"released-plan".to_string()));
    }

    #[test]
    fn workspace_consumer_sql_reuses_one_pg_ownership_predicate() {
        for query in [
            workspace_consumer_sql("count(*)", "j.workspace_id=$1", ""),
            workspace_consumer_sql("j.execution_plan_json", "j.workspace_id=$1", ""),
            workspace_consumer_sql("j.job_id", "j.workspace_id=$1", ""),
            workspace_consumer_sql(
                "j.workspace_id,j.job_id",
                "j.workspace_id = ANY($1::TEXT[])",
                "",
            ),
        ] {
            assert!(query.contains(WORKSPACE_ACTIVE_OR_HELD));
            assert!(query.contains("r.state IN ('active','held_orphaned')"));
            assert!(query.contains("j.resolution IS NULL"));
            // PostgreSQL can hash this ownership set once for the bounded
            // Workspace page; a correlated EXISTS can degenerate into one
            // nested-loop probe per historical Job under a large ledger.
            assert!(query.contains("j.job_id IN ("));
        }
    }
}

#[cfg(test)]
mod workspace_lock_snapshot_tests {
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
}
