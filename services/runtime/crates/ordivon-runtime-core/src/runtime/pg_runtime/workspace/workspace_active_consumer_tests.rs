//! Native business tests retained under semantic Workspace API; test source file name is not a contract.
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
