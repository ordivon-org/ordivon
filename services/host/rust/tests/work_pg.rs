//! Exact-PG18-only migration checks. Never uses ORDIVON_HOST_V2_DSN;
//! intended to run only with a disposable isolated database.
//! Invoke with HOST_RUST_TEST_DSN=... cargo test --test work_pg -- --ignored.
use ordivon_host_rust::work::{
    canonical_digest, commit_snapshot, declare_actor, get_work, ActorDeclare, ActorKind,
    CommitSnapshot, WorkError, WorkSnapshot, WorkState,
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

fn declaration(actor_ref: &str, actor_kind: ActorKind, request_id: &str) -> ActorDeclare {
    ActorDeclare {
        actor_ref: actor_ref.into(),
        actor_kind,
        client_request_id: request_id.into(),
    }
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn declare_actor_receipt_replay_matches_python_contract() {
    let mut first = connect().await;
    let mut second = connect().await;
    let actor = "actor:test:rust:actor-declare";
    let command = declaration(actor, ActorKind::Agent, "request:test:actor:declare-v1");
    let committed = declare_actor(&mut first, &command).await.unwrap();
    assert_eq!(committed["admission"], "committed");
    assert_eq!(committed["schemaVersion"], 1);
    assert_eq!(committed["kind"], "ordivon.host-actor-ref");
    assert_eq!(committed["actorRef"], actor);
    assert_eq!(committed["actorKind"], "agent");
    assert_eq!(
        committed["truthBoundary"],
        "Host-stored stable actor reference only; not authenticated identity or authorization"
    );
    assert!(committed["createdAt"].as_str().unwrap().ends_with("+00:00"));

    // Simulate lost response and reconnect: durable receipt, not a second actor.
    let replay = declare_actor(&mut second, &command).await.unwrap();
    assert_eq!(replay["admission"], "existing");
    assert_eq!(replay["createdAt"], committed["createdAt"]);
    let mut normalized = replay.clone();
    normalized["admission"] = json!("committed");
    assert_eq!(normalized, committed);

    let second_id = declaration(actor, ActorKind::Agent, "request:test:actor:declare-v2");
    let existing = declare_actor(&mut second, &second_id).await.unwrap();
    assert_eq!(existing["admission"], "existing");
    assert_eq!(existing["createdAt"], committed["createdAt"]);

    // Same request id + changed semantic payload cannot hijack a receipt.
    let changed = declaration(actor, ActorKind::Human, &command.client_request_id);
    assert!(matches!(
        declare_actor(&mut second, &changed).await,
        Err(WorkError::Conflict(_))
    ));
    let changed_id = declaration(actor, ActorKind::Human, "request:test:actor:kind-change");
    assert!(matches!(
        declare_actor(&mut second, &changed_id).await,
        Err(WorkError::Conflict(_))
    ));
    let rows: i64 = first
        .query_one(
            "SELECT count(*) FROM actor_refs WHERE actor_ref=$1",
            &[&actor],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(rows, 1);
    let receipts: i64 = first
        .query_one(
            "SELECT count(*) FROM command_receipts WHERE client_request_id IN ($1,$2,$3)",
            &[
                &command.client_request_id,
                &second_id.client_request_id,
                &changed_id.client_request_id,
            ],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(receipts, 2);
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn declare_actor_concurrent_insert_has_one_winner() {
    let mut left_client = connect().await;
    let mut right_client = connect().await;
    let actor = "actor:test:rust:actor-race";
    let left = declaration(
        actor,
        ActorKind::Organization,
        "request:test:actor:race-left",
    );
    let right = declaration(
        actor,
        ActorKind::Organization,
        "request:test:actor:race-right",
    );
    let (first, second) = tokio::join!(
        declare_actor(&mut left_client, &left),
        declare_actor(&mut right_client, &right)
    );
    let first = first.unwrap();
    let second = second.unwrap();
    assert_ne!(first["admission"], second["admission"]);
    assert_eq!(first["createdAt"], second["createdAt"]);
    let count: i64 = left_client
        .query_one(
            "SELECT count(*) FROM actor_refs WHERE actor_ref=$1",
            &[&actor],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(count, 1);
}

#[tokio::test]
#[ignore = "requires HOST_RUST_TEST_DSN pointing to disposable full schema13 PG18"]
async fn actor_declare_rejects_non_namespaced_or_control_identifiers() {
    let mut client = connect().await;
    let cases = [
        ("human", ActorKind::Human),
        (" actor:whitespace", ActorKind::Agent),
        ("actor:control\u{001d}", ActorKind::Agent),
        ("actor:bad\n", ActorKind::Agent),
        ("actor:wide\u{00a0}", ActorKind::Agent),
    ];
    for (actor, kind) in cases {
        let candidate = declaration(actor, kind, "request:invalid");
        assert!(
            matches!(
                declare_actor(&mut client, &candidate).await,
                Err(WorkError::Invalid(_))
            ),
            "{actor:?} must fail before PostgreSQL effect"
        );
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
