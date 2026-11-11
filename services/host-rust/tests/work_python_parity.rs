//! A separate opt-in real Python↔Rust Work compatibility test.
//! Run only after services/host-rust/tests/python_oracle.py seeds its
//! expected JSON in an isolated PostgreSQL 18 database.
use ordivon_host_rust::work::{commit_snapshot, get_work, CommitSnapshot, WorkSnapshot, WorkState};
use serde_json::{json, Value};
use tokio_postgres::{Client, NoTls};

async fn connect() -> Client {
    let dsn = std::env::var("HOST_RUST_TEST_DSN").expect("disposable PG18 DSN required");
    let (client, connection) = tokio_postgres::connect(&dsn, NoTls).await.unwrap();
    tokio::spawn(async move {
        if let Err(error) = connection.await {
            panic!("test PostgreSQL connection error: {error}");
        }
    });
    client
}

#[tokio::test]
#[ignore = "requires PG18 + Python Host fixture in HOST_RUST_PYTHON_ORACLE_PATH"]
async fn real_python_to_rust_work_wire_and_receipt_parity() {
    use ordivon_host_rust::work::{create_work, list_works, CreateWork, ListWorks};
    let oracle_path = std::env::var("HOST_RUST_PYTHON_ORACLE_PATH")
        .expect("set HOST_RUST_PYTHON_ORACLE_PATH to Python fixture JSON");
    let oracle: Value = serde_json::from_slice(&std::fs::read(oracle_path).unwrap()).unwrap();
    let mut client = connect().await;
    let work_ref = "work:test:python:rust-parity";

    let current = get_work(&mut client, work_ref, None).await.unwrap();
    assert_eq!(current, oracle["current"], "current Work wire parity");
    let prior = get_work(&mut client, work_ref, Some(1)).await.unwrap();
    assert_eq!(prior, oracle["revisionOne"], "historical Work wire parity");

    let snapshot_one = WorkSnapshot {
        objective: "跨语言 Work 语义".into(),
        frontier: "Python 首次提交".into(),
        established: vec!["Python 源校验".into()],
        unresolved: vec![],
        rejected: vec![],
        constraints: vec![],
        next_actions: vec!["审查 Rust Work".into()],
        reference_refs: vec![],
    };
    let replay_create = create_work(
        &mut client,
        &CreateWork {
            work_ref: work_ref.into(),
            kind: "python-rust-wire".into(),
            actor_ref: "actor:test:python-rust-parity".into(),
            initial_snapshot: snapshot_one,
            client_request_id: "request:test:python:create-parity".into(),
        },
    )
    .await
    .unwrap();
    let mut python_created = oracle["create"].clone();
    python_created["admission"] = json!("existing");
    assert_eq!(
        replay_create, python_created,
        "Python receipt -> Rust replay"
    );

    let replay_commit = commit_snapshot(
        &mut client,
        &CommitSnapshot {
            work_ref: work_ref.into(),
            expected_revision: 1,
            snapshot: WorkSnapshot {
                objective: "跨语言 Work 语义".into(),
                frontier: "Python 第二修订".into(),
                established: vec!["Python 源校验".into(), "事务 CAS".into()],
                unresolved: vec![],
                rejected: vec![],
                constraints: vec![],
                next_actions: vec!["审查 Rust Work".into()],
                reference_refs: vec![],
            },
            actor_ref: "actor:test:python-rust-parity".into(),
            state: WorkState::Completed,
            client_request_id: "request:test:python:commit-parity".into(),
        },
    )
    .await
    .unwrap();
    let mut python_committed = oracle["commit"].clone();
    python_committed["admission"] = json!("existing");
    assert_eq!(
        replay_commit, python_committed,
        "Python committed receipt -> Rust exact replay"
    );

    let listing = list_works(
        &mut client,
        &ListWorks {
            state: Some(WorkState::Completed),
            limit: 1,
            ..Default::default()
        },
    )
    .await
    .unwrap();
    assert_eq!(
        listing, oracle["list"],
        "Python -> Rust list response parity"
    );
}
