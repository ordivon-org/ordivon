//! Exact-PG18-only migration checks. Never uses ORDIVON_HOST_V2_DSN;
//! intended to run only with a disposable isolated database.
//! Invoke with HOST_RUST_TEST_DSN=... cargo test --test work_pg -- --ignored.
use ordivon_host_rust::work::{
    canonical_digest, commit_snapshot, get_work, CommitSnapshot, WorkError, WorkSnapshot, WorkState,
};
use serde_json::{json, Value};
use tokio_postgres::{types::Json, Client, NoTls};

async fn connect() -> Client {
    let dsn = std::env::var("HOST_RUST_TEST_DSN")
        .expect("HOST_RUST_TEST_DSN must target a disposable PostgreSQL 18 test database");
    let (client, connection) = tokio_postgres::connect(&dsn, NoTls).await.unwrap();
    tokio::spawn(async move {
        if let Err(error) = connection.await {
            panic!("test PostgreSQL connection error: {error}");
        }
    });
    client
}

fn snapshot(frontier: &str) -> WorkSnapshot {
    WorkSnapshot {
        objective: "Rust Host CAS integration".into(),
        frontier: frontier.into(),
        established: vec!["已验证的事实 🌍".into()],
        unresolved: vec![],
        rejected: vec![],
        constraints: vec![],
        next_actions: vec!["检查提交回执".into()],
        reference_refs: vec![],
    }
}

async fn seed_work(client: &Client, work_ref: &str) {
    let actor = "actor:test:rust-migration";
    client
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ($1,'agent') ON CONFLICT DO NOTHING",
            &[&actor],
        )
        .await
        .unwrap();
    let payload: Value = serde_json::to_value(snapshot("revision-one")).unwrap();
    let digest = canonical_digest(&payload).unwrap();
    client
        .execute(
            "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref) \
             VALUES ($1,'test','open',1,$2,$3)",
            &[&work_ref, &digest, &actor],
        )
        .await
        .unwrap();
    client
        .execute(
            "INSERT INTO work_snapshots(work_ref,revision,snapshot_digest,payload,writer_actor_ref) \
             VALUES ($1,1,$2,$3,$4)",
            &[&work_ref, &digest, &Json(&payload), &actor],
        )
        .await
        .unwrap();
}

fn command(work_ref: &str, frontier: &str, request_id: &str, state: WorkState) -> CommitSnapshot {
    CommitSnapshot {
        work_ref: work_ref.into(),
        expected_revision: 1,
        snapshot: snapshot(frontier),
        actor_ref: "actor:test:rust-migration".into(),
        state,
        client_request_id: request_id.into(),
    }
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn sequential_cas_replay_and_historical_state() {
    let mut client = connect().await;
    let work_ref = "work:test:rust:cas-sequential";
    seed_work(&client, work_ref).await;

    let initial_command = command(
        work_ref,
        "revision-two",
        "request:test:rust:seq",
        WorkState::Completed,
    );
    let committed = commit_snapshot(&mut client, &initial_command)
        .await
        .unwrap();
    assert_eq!(committed["admission"], "committed");
    assert_eq!(committed["state"], "completed");
    assert_eq!(committed["revision"], 2);
    assert_eq!(committed["snapshot"]["frontier"], "revision-two");

    // Reconnection + lost response: same identity returns original committed effect.
    drop(client);
    let mut client = connect().await;
    let replay = commit_snapshot(&mut client, &initial_command)
        .await
        .unwrap();
    assert_eq!(replay["admission"], "existing");
    let mut sanitized = replay.clone();
    sanitized["admission"] = json!("committed");
    assert_eq!(sanitized, committed);

    // Changed request content with the same request id is a conflict.
    let altered = command(
        work_ref,
        "different",
        "request:test:rust:seq",
        WorkState::Completed,
    );
    assert!(matches!(
        commit_snapshot(&mut client, &altered).await,
        Err(WorkError::Conflict(_))
    ));

    let prior = get_work(&mut client, work_ref, Some(1)).await.unwrap();
    assert_eq!(prior["state"], "historical_state_unknown");
    assert_eq!(prior["revision"], 1);
    let current = get_work(&mut client, work_ref, None).await.unwrap();
    assert_eq!(current["state"], "completed");
    let missing = get_work(&mut client, work_ref, Some(3)).await;
    assert!(matches!(missing, Err(WorkError::Conflict(_))));

    let mut reopen = command(
        work_ref,
        "revision-three",
        "request:test:rust:new",
        WorkState::Open,
    );
    reopen.expected_revision = 2;
    assert!(matches!(
        commit_snapshot(&mut client, &reopen).await,
        Err(WorkError::Conflict(_))
    ));
    let snapshots: i64 = client
        .query_one(
            "SELECT count(*) FROM work_snapshots WHERE work_ref=$1",
            &[&work_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(snapshots, 2);
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn simultaneous_cas_has_single_winner() {
    let mut a = connect().await;
    let mut b = connect().await;
    let work_ref = "work:test:rust:cas-race";
    seed_work(&a, work_ref).await;
    let left = command(work_ref, "left", "request:test:rust:left", WorkState::Open);
    let right = command(
        work_ref,
        "right",
        "request:test:rust:right",
        WorkState::Open,
    );
    let (l, r) = tokio::join!(
        commit_snapshot(&mut a, &left),
        commit_snapshot(&mut b, &right)
    );
    let wins = u8::from(l.is_ok()) + u8::from(r.is_ok());
    assert_eq!(
        wins, 1,
        "two different snapshots cannot win the same revision"
    );
    assert!(l
        .as_ref()
        .err()
        .is_none_or(|e| matches!(e, WorkError::Conflict(_))));
    assert!(r
        .as_ref()
        .err()
        .is_none_or(|e| matches!(e, WorkError::Conflict(_))));
    let current = get_work(&mut a, work_ref, None).await.unwrap();
    assert_eq!(current["revision"], 2);
    assert!(
        current["snapshot"]["frontier"] == "left" || current["snapshot"]["frontier"] == "right"
    );
    let snapshots: i64 = b
        .query_one(
            "SELECT count(*) FROM work_snapshots WHERE work_ref=$1",
            &[&work_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(snapshots, 2);
}
