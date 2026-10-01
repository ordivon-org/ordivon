use super::*;
use rusqlite::{types::Value, StatementStatus};

fn fixture() -> Connection {
    let connection = Connection::open_in_memory().unwrap();
    connection
        .execute_batch(include_str!("../../../migrations/runtime/0001_runtime.sql"))
        .unwrap();
    connection.execute_batch(r#"
        WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10020)
        INSERT INTO jobs(job_id,principal,client_request_id,request_digest,operation_digest,workspace_id,workspace_snapshot_json,execution_plan_json,execution_plan_digest,created_at_ms,desired_state,resolution)
        SELECT 'j'||x,'test','r'||x,'d','d','w','{}','{}','d',CASE WHEN x<=10000 THEN 1 ELSE 100 END,'run','succeeded' FROM n;
        INSERT INTO attempts(attempt_id,job_id,attempt_number,state,termination_intent,launch_token_digest,bundle_path,unit_name,created_at_ms,finished_at_ms)
        SELECT 'a'||job_id,job_id,1,'succeeded','natural','d','/test','u'||job_id,created_at_ms,created_at_ms+10 FROM jobs;
        INSERT INTO concurrency_reservations(reservation_id,attempt_id,global_limit,state,acquired_at_ms,released_at_ms)
        SELECT 'r'||attempt_id,attempt_id,8,'released',created_at_ms,created_at_ms+10 FROM attempts;
        INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,reason_code,detail_json,detail_digest,observed_at_ms)
        SELECT job_id||'-'||s,job_id,'a'||job_id,s,t,'SYSTEM_DERIVED','PROCESS_EXIT_ZERO','{}','d',created_at_ms+s
        FROM jobs CROSS JOIN (SELECT 1 s,'DISPATCH_ISSUED' t UNION ALL SELECT 2,'RUNNER_BOUND' UNION ALL SELECT 3,'JOB_TERMINAL');
        INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,reason_code,detail_json,detail_digest,observed_at_ms)
        VALUES('extra1','j10001','aj10001',4,'DISPATCH_ISSUED','SYSTEM_DERIVED','test','{}','d',99),
              ('extra2','j10001','aj10001',5,'RECONCILIATION_FAILED','SYSTEM_DERIVED','test','{}','d',105),
              ('extra3','j10001','aj10001',6,'RECONCILIATION_CONVERGED','SYSTEM_DERIVED','test','{}','d',106),
              ('extra4','j10002','aj10002',4,'ADMIN_TERMINAL_REPAIR','SYSTEM_DERIVED','test','{}','d',104);
    "#).unwrap();
    connection
}

fn queries() -> [WindowedSummaryQuery; 8] {
    [
        SUMMARY_ATTEMPTS,
        SUMMARY_RESERVATIONS,
        SUMMARY_RECOVERY_FAILURES,
        SUMMARY_ADMIN_REPAIRS,
        SUMMARY_DISPATCHES,
        SUMMARY_DUPLICATE_DISPATCHES,
        SUMMARY_TERMINAL_REASONS,
        SUMMARY_LATENCY_EVENTS,
    ]
}

fn run(connection: &Connection, sql: &str, since_ms: u64) -> (Vec<Vec<Value>>, i32) {
    let mut statement = connection.prepare(sql).unwrap();
    let columns = statement.column_count();
    let rows = statement
        .query_map([since_ms], |row| {
            (0..columns)
                .map(|column| row.get(column))
                .collect::<rusqlite::Result<Vec<Value>>>()
        })
        .unwrap()
        .collect::<rusqlite::Result<Vec<_>>>()
        .unwrap();
    (rows, statement.get_status(StatementStatus::VmStep))
}

#[test]
fn recent_summary_queries_do_not_scan_unrelated_history() {
    let connection = fixture();
    for query in queries() {
        let (rows, steps) = run(&connection, query.sql(100), 100);
        let (baseline, _) = run(&connection, query.full_history, 100);
        assert_eq!(rows, baseline);
        assert!(
            steps < 5000,
            "recent-window query paid {steps} VM operations"
        );
    }
    assert_eq!(
        run(&connection, SUMMARY_ATTEMPTS.sql(100), 100).0,
        vec![vec![Value::Text("succeeded".into()), Value::Integer(20)]]
    );
    assert_eq!(
        run(&connection, SUMMARY_DISPATCHES.sql(100), 100).0,
        vec![vec![Value::Integer(21)]]
    );
    assert_eq!(
        run(&connection, SUMMARY_DUPLICATE_DISPATCHES.sql(100), 100).0,
        vec![vec![Value::Integer(1), Value::Integer(1)]]
    );
}

#[test]
fn full_history_summary_keeps_the_existing_query_cost() {
    let connection = fixture();
    for query in queries() {
        let (rows, steps) = run(&connection, query.sql(0), 0);
        let (baseline, baseline_steps) = run(&connection, query.full_history, 0);
        assert_eq!(rows, baseline);
        assert!(
            steps <= baseline_steps,
            "all-history query regressed {baseline_steps} -> {steps} VM operations"
        );
    }
}

#[test]
fn empty_windows_and_event_sequence_order_are_preserved() {
    let connection = fixture();
    for query in queries() {
        assert_eq!(
            run(&connection, query.sql(101), 101).0,
            run(&connection, query.full_history, 101).0
        );
    }
    let (rows, _) = run(&connection, SUMMARY_LATENCY_EVENTS.sql(100), 100);
    assert_eq!(rows.len(), 64);
    let first = rows
        .iter()
        .filter(|row| row[0] == Value::Text("j10001".into()))
        .map(|row| (row[2].clone(), row[3].clone()))
        .collect::<Vec<_>>();
    assert_eq!(
        first,
        vec![
            (Value::Text("DISPATCH_ISSUED".into()), Value::Integer(101)),
            (Value::Text("RUNNER_BOUND".into()), Value::Integer(102)),
            (Value::Text("JOB_TERMINAL".into()), Value::Integer(103)),
            (Value::Text("DISPATCH_ISSUED".into()), Value::Integer(99)),
            (
                Value::Text("RECONCILIATION_FAILED".into()),
                Value::Integer(105)
            ),
            (
                Value::Text("RECONCILIATION_CONVERGED".into()),
                Value::Integer(106)
            ),
        ]
    );
}
