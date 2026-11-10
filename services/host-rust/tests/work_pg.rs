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

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn work_create_identity_and_initial_content_survive_replay() {
    use ordivon_host_rust::work::{create_work, CreateWork};
    let mut first = connect().await;
    let mut second = connect().await;
    let actor = "actor:test:rust-migration";
    first
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ($1,'agent') ON CONFLICT DO NOTHING",
            &[&actor],
        )
        .await
        .unwrap();
    let work_ref = "work:test:rust:create-replay";
    let new = CreateWork {
        work_ref: work_ref.into(),
        kind: "rust-migration-test".into(),
        actor_ref: actor.into(),
        initial_snapshot: snapshot("create-first"),
        client_request_id: "request:test:rust:create-replay".into(),
    };
    let original = create_work(&mut first, &new).await.unwrap();
    assert_eq!(original["revision"], 1);
    assert_eq!(original["admission"], "committed");
    assert_eq!(original["snapshot"]["frontier"], "create-first");

    let replay = create_work(&mut second, &new).await.unwrap();
    assert_eq!(replay["admission"], "existing");
    let mut normalized = replay.clone();
    normalized["admission"] = json!("committed");
    assert_eq!(normalized, original);

    let mut same_semantics = new.clone();
    same_semantics.client_request_id = "request:test:rust:create-new-id".into();
    let matched = create_work(&mut second, &same_semantics).await.unwrap();
    assert_eq!(matched["admission"], "existing");

    let mut changed = new.clone();
    changed.initial_snapshot = snapshot("different-initial");
    assert!(matches!(
        create_work(&mut second, &changed).await,
        Err(WorkError::Conflict(_))
    ));
    changed.client_request_id = "request:test:rust:create-conflict".into();
    assert!(matches!(
        create_work(&mut second, &changed).await,
        Err(WorkError::Conflict(_))
    ));
    let count: i64 = first
        .query_one(
            "SELECT count(*) FROM work_snapshots WHERE work_ref=$1",
            &[&work_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(count, 1);
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn concurrent_create_is_linearizable() {
    use ordivon_host_rust::work::{create_work, CreateWork};
    let mut a = connect().await;
    let mut b = connect().await;
    a.execute(
        "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ('actor:test:rust-migration','agent') ON CONFLICT DO NOTHING",
        &[],
    ).await.unwrap();
    let base = CreateWork {
        work_ref: "work:test:rust:parallel-create".into(),
        kind: "rust-migration-test".into(),
        actor_ref: "actor:test:rust-migration".into(),
        initial_snapshot: snapshot("same-create"),
        client_request_id: "request:test:rust:parallel-1".into(),
    };
    let mut other = base.clone();
    other.client_request_id = "request:test:rust:parallel-2".into();
    let (left, right) = tokio::join!(create_work(&mut a, &base), create_work(&mut b, &other));
    let left = left.unwrap();
    let right = right.unwrap();
    assert_ne!(left["admission"], right["admission"]);
    assert_eq!(left["snapshotDigest"], right["snapshotDigest"]);
    let n: i64 = a
        .query_one(
            "SELECT count(*) FROM work_snapshots WHERE work_ref=$1",
            &[&base.work_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(n, 1);
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn list_works_state_cursor_and_order_are_exact() {
    use ordivon_host_rust::work::{create_work, list_works, CreateWork, ListWorks};
    let mut client = connect().await;
    let actor = "actor:test:rust-migration";
    client
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ($1,'agent') ON CONFLICT DO NOTHING",
            &[&actor],
        )
        .await
        .unwrap();
    let mut refs = Vec::new();
    for n in 1..=3 {
        let work_ref = format!("work:test:rust:list-{n}");
        let c = CreateWork {
            work_ref: work_ref.clone(),
            kind: "list-fixture".into(),
            actor_ref: actor.into(),
            initial_snapshot: snapshot(&format!("page-{n}")),
            client_request_id: format!("request:test:rust:list-{n}"),
        };
        create_work(&mut client, &c).await.unwrap();
        let timestamp = format!("2099-01-0{n}T01:00:00+00:00");
        client
            .execute(
                "UPDATE works SET updated_at=$1::text::timestamptz WHERE work_ref=$2",
                &[&timestamp, &work_ref],
            )
            .await
            .unwrap();
        refs.push(work_ref);
    }

    let mut input = ListWorks {
        state: Some(WorkState::Open),
        limit: 2,
        ..Default::default()
    };
    let page_one = list_works(&mut client, &input).await.unwrap();
    assert_eq!(page_one["works"].as_array().unwrap().len(), 2);
    assert_eq!(page_one["works"][0]["workRef"], refs[2]);
    assert_eq!(page_one["works"][1]["workRef"], refs[1]);
    assert_eq!(page_one["hasMore"], true);
    let cursor = &page_one["nextCursor"];
    input.before_updated_at = Some(cursor["beforeUpdatedAt"].as_str().unwrap().into());
    input.before_work_ref = Some(cursor["beforeWorkRef"].as_str().unwrap().into());
    let page_two = list_works(&mut client, &input).await.unwrap();
    assert_eq!(page_two["works"][0]["workRef"], refs[0]);
    assert_ne!(
        page_two["works"][0]["workRef"],
        page_one["works"][1]["workRef"]
    );
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn list_works_canonical_byte_budget_never_skips_rows() {
    use ordivon_host_rust::work::{canonical_digest, list_works, ListWorks};
    use std::collections::HashSet;
    let mut client = connect().await;
    let actor = "actor:test:rust-migration";
    client
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES ($1,'agent') ON CONFLICT DO NOTHING",
            &[&actor],
        )
        .await
        .unwrap();
    let payload = serde_json::to_value(snapshot("list-limit")).unwrap();
    let digest = canonical_digest(&payload).unwrap();
    let mut expected = HashSet::new();
    for n in 0..38 {
        let work_ref = format!("work:test:rust:bytes:{n:03}:{}", "x".repeat(800));
        expected.insert(work_ref.clone());
        client
            .execute(
                "INSERT INTO works(work_ref,kind,state,current_revision,current_snapshot_digest,created_by_actor_ref,updated_at) \
                 VALUES ($1,'test','abandoned',1,$2,$3, '2099-02-01T00:00:00+00'::timestamptz)",
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
    let mut seen = HashSet::new();
    let mut input = ListWorks {
        state: Some(WorkState::Abandoned),
        limit: 100,
        max_bytes: 16_384,
        ..Default::default()
    };
    for _ in 0..12 {
        let result = list_works(&mut client, &input).await.unwrap();
        let canonical = serde_json_canonicalizer::to_vec(&result).unwrap();
        assert!(canonical.len() <= 16_384);
        let page = result["works"].as_array().unwrap();
        assert!(!page.is_empty());
        for row in page {
            let name = row["workRef"].as_str().unwrap().to_string();
            if expected.contains(&name) {
                assert!(seen.insert(name), "pagination repeated an item");
            }
        }
        if seen.len() == expected.len() {
            break;
        }
        let cursor = &result["nextCursor"];
        assert_eq!(result["hasMore"], true);
        input.before_updated_at = Some(cursor["beforeUpdatedAt"].as_str().unwrap().into());
        input.before_work_ref = Some(cursor["beforeWorkRef"].as_str().unwrap().into());
    }
    assert_eq!(
        seen, expected,
        "the canonical byte budget must not skip rows"
    );
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
