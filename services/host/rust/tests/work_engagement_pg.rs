//! True PostgreSQL18/schema13 consumer proof of Work intake→claim→submit→review.
//! No Runtime, extra tables, production DSN, or user-identity assumptions.
use ordivon_host_rust::work::{
    canonical_digest, commit_snapshot, create_work,
    engagement::{
        advance_engagement, list_engagements, AdvanceEngagement, EngagementAction, ListEngagements,
        Phase, ReviewDecision,
    },
    get_work, CommitSnapshot, CreateWork, WorkError, WorkSnapshot, WorkState,
};
use serde_json::{json, Value};
use tokio_postgres::{types::Json, Client, NoTls};

async fn connect() -> Client {
    let dsn = std::env::var("HOST_RUST_TEST_DSN").expect("Only disposable PG18 test DSN");
    let (client, connection) = tokio_postgres::connect(&dsn, NoTls).await.unwrap();
    tokio::spawn(async move { connection.await.unwrap() });
    client
}

fn initial_snapshot() -> WorkSnapshot {
    WorkSnapshot {
        objective: "交付一项可消费的科研成果 🌍".into(),
        frontier: "寻找自然执行者".into(),
        established: vec![],
        unresolved: vec![],
        rejected: vec![],
        constraints: vec![],
        next_actions: vec!["Claim → Submit → Consumer Review".into()],
        reference_refs: vec![],
    }
}

async fn actors(client: &Client) {
    for actor in [
        "actor:test:engagement-requester",
        "actor:test:engagement-consumer",
        "actor:test:engagement-agent-a",
        "actor:test:engagement-agent-b",
    ] {
        client
            .execute(
                "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent') \
              ON CONFLICT DO NOTHING",
                &[&actor],
            )
            .await
            .unwrap();
    }
}

async fn new_work(client: &mut Client, work_ref: &str) {
    actors(client).await;
    let initial = CreateWork {
        work_ref: work_ref.into(),
        kind: "research-deliverable".into(),
        actor_ref: "actor:test:engagement-requester".into(),
        initial_snapshot: initial_snapshot(),
        client_request_id: format!("request:test:create:{work_ref}"),
    };
    assert_eq!(
        create_work(client, &initial).await.unwrap()["admission"],
        "committed"
    );
}

fn action(
    work_ref: &str,
    revision: i64,
    actor: &str,
    suffix: &str,
    kind: EngagementAction,
) -> AdvanceEngagement {
    AdvanceEngagement {
        work_ref: work_ref.into(),
        expected_revision: revision,
        actor_ref: actor.into(),
        action: kind,
        client_request_id: format!("request:test:engagement:{suffix}"),
    }
}
fn offered() -> EngagementAction {
    EngagementAction::Offer {
        consumer_actor_ref: "actor:test:engagement-consumer".into(),
        acceptance_criteria: vec![
            "Consumer independently checks referenced result and receipt".into(),
        ],
    }
}
fn submit(epoch: i64, delivery: &str) -> EngagementAction {
    EngagementAction::Submit {
        claim_epoch: epoch,
        delivery_ref: delivery.into(),
        summary: "可复用的研究成果及独立复核".into(),
        output_refs: vec!["artifact:research:result".into()],
        evidence_refs: vec!["receipt:runtime:effect".into()],
    }
}
fn review(epoch: i64, decision: ReviewDecision) -> EngagementAction {
    EngagementAction::Review {
        claim_epoch: epoch,
        decision,
        rationale: "已核对工件、源码和实验结果".into(),
        verification_refs: vec!["evidence:consumer:review".into()],
    }
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18/schema13 HOST_RUST_TEST_DSN"]
async fn full_work_claim_return_reclaim_submit_accept_and_python_history() {
    let mut req = connect().await;
    let mut worker_a = connect().await;
    let mut worker_b = connect().await;
    let work = "work:test:engagement:lifecycle-r7";
    new_work(&mut req, work).await;

    // Offer: immutable acceptance terms, not Runtime scheduling.
    let offer = action(
        work,
        1,
        "actor:test:engagement-requester",
        "offer",
        offered(),
    );
    let offered_row = advance_engagement(&mut req, &offer).await.unwrap();
    assert_eq!(offered_row["revision"], 2);
    assert_eq!(offered_row["snapshot"]["engagement"]["phase"], "offered");
    let mut receipt = advance_engagement(&mut req, &offer).await.unwrap();
    assert_eq!(receipt["admission"], "existing");
    // Original Host signals that a durable committed response was replayed.
    receipt["admission"] = json!("committed");
    assert_eq!(
        receipt, offered_row,
        "lost response preserved exact durable effect"
    );

    // A generic Work CAS must not drop the typed engagement payload.
    let bypass = CommitSnapshot {
        work_ref: work.into(),
        expected_revision: 2,
        snapshot: initial_snapshot(),
        actor_ref: "actor:test:engagement-requester".into(),
        state: WorkState::Open,
        client_request_id: "request:test:strip-engagement".into(),
    };
    assert!(matches!(
        commit_snapshot(&mut req, &bypass).await,
        Err(WorkError::Conflict(_)),
    ));

    // Two real connections race; exactly one accountable actor wins rev3.
    let claim_a = action(
        work,
        2,
        "actor:test:engagement-agent-a",
        "claim-a",
        EngagementAction::Claim,
    );
    let claim_b = action(
        work,
        2,
        "actor:test:engagement-agent-b",
        "claim-b",
        EngagementAction::Claim,
    );
    let (left, right) = tokio::join!(
        advance_engagement(&mut worker_a, &claim_a),
        advance_engagement(&mut worker_b, &claim_b),
    );
    assert_eq!(u8::from(left.is_ok()) + u8::from(right.is_ok()), 1);
    assert!(matches!(
        left.as_ref().err().or(right.as_ref().err()),
        Some(WorkError::Conflict(_))
    ));
    let accepted_claim = left.as_ref().ok().or(right.as_ref().ok()).unwrap();
    assert_eq!(accepted_claim["snapshot"]["engagement"]["claimEpoch"], 1);
    let winner = accepted_claim["snapshot"]["engagement"]["assigneeActorRef"]
        .as_str()
        .unwrap()
        .to_owned();
    let loser = if winner.ends_with("agent-a") {
        "actor:test:engagement-agent-b"
    } else {
        "actor:test:engagement-agent-a"
    };

    // Neither a stale claimEpoch nor another actor's assertion can submit.
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                3,
                &winner,
                "stale-epoch",
                submit(0, "delivery:test:stale")
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                3,
                loser,
                "wrong-actor",
                submit(1, "delivery:test:wrong")
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));

    let delivery1 = action(
        work,
        3,
        &winner,
        "delivery-first",
        submit(1, "delivery:test:revision-first"),
    );
    let submitted = advance_engagement(&mut req, &delivery1).await.unwrap();
    assert_eq!(submitted["revision"], 4);
    assert_eq!(submitted["state"], "open");
    assert_eq!(submitted["snapshot"]["engagement"]["phase"], "submitted");
    let mut replayed = advance_engagement(&mut req, &delivery1).await.unwrap();
    assert_eq!(replayed["admission"], "existing");
    replayed["admission"] = json!("committed");
    assert_eq!(replayed, submitted);

    // Only the consumer can review, and one returned delivery isn't 'completed'.
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                4,
                &winner,
                "self-approval",
                review(1, ReviewDecision::Accepted)
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    let returned = advance_engagement(
        &mut req,
        &action(
            work,
            4,
            "actor:test:engagement-consumer",
            "consumer-return",
            review(1, ReviewDecision::Returned),
        ),
    )
    .await
    .unwrap();
    assert_eq!(returned["state"], "open");
    assert_eq!(returned["snapshot"]["engagement"]["phase"], "returned");

    // A returned task can be reclaimed, but old owner/epoch can no longer submit.
    let new_claim = advance_engagement(
        &mut req,
        &action(work, 5, loser, "reclaim", EngagementAction::Claim),
    )
    .await
    .unwrap();
    assert_eq!(new_claim["snapshot"]["engagement"]["claimEpoch"], 2);
    assert_eq!(
        new_claim["snapshot"]["engagement"]["assigneeActorRef"],
        loser
    );
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                6,
                &winner,
                "stale-submission",
                submit(1, "delivery:test:old")
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                6,
                loser,
                "duplicate-deliveryref",
                submit(2, "delivery:test:revision-first")
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    let second = advance_engagement(
        &mut req,
        &action(
            work,
            6,
            loser,
            "second-delivery",
            submit(2, "delivery:test:revision-second"),
        ),
    )
    .await
    .unwrap();
    assert_eq!(second["revision"], 7);

    let finished = advance_engagement(
        &mut req,
        &action(
            work,
            7,
            "actor:test:engagement-consumer",
            "accept",
            review(2, ReviewDecision::Accepted),
        ),
    )
    .await
    .unwrap();
    assert_eq!(finished["state"], "completed");
    assert_eq!(finished["revision"], 8);
    assert_eq!(finished["snapshot"]["engagement"]["phase"], "accepted");

    // Immutable historical delivery is distinct from current accepted state.
    let historical = get_work(&mut req, work, Some(4)).await.unwrap();
    assert_eq!(
        historical["snapshot"]["engagement"]["delivery"]["deliveryRef"],
        "delivery:test:revision-first"
    );
    assert_eq!(historical["state"], "historical_state_unknown");

    let rows = req
        .query(
            "SELECT revision,snapshot_digest,payload FROM work_snapshots \
          WHERE work_ref=$1 ORDER BY revision",
            &[&work],
        )
        .await
        .unwrap();
    assert_eq!(
        rows.len(),
        8,
        "exactly one immutable revision per accepted transition"
    );
    for (idx, row) in rows.iter().enumerate() {
        let rev: i64 = row.get("revision");
        let digest: String = row.get("snapshot_digest");
        let Json(payload): Json<Value> = row.get("payload");
        assert_eq!(rev, idx as i64 + 1);
        assert_eq!(canonical_digest(&payload).unwrap(), digest);
    }
    assert!(matches!(
        advance_engagement(
            &mut req,
            &action(
                work,
                8,
                &winner,
                "terminal-reclaim",
                EngagementAction::Claim
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    println!("R7_FULL_WORK_DELIVERY_ACCEPTANCE_LIVE_PG18_PASS");
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18/schema13 HOST_RUST_TEST_DSN"]
async fn release_reclaim_cancel_and_invalid_consumer_prove_no_phantom_success() {
    let mut client = connect().await;
    let work = "work:test:engagement:cancel-r7";
    new_work(&mut client, work).await;
    assert!(matches!(
        advance_engagement(
            &mut client,
            &action(
                work,
                1,
                "actor:test:engagement-agent-a",
                "not-requester",
                offered()
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    assert!(matches!(
        advance_engagement(
            &mut client,
            &action(
                work,
                1,
                "actor:test:engagement-requester",
                "consumer-missing",
                EngagementAction::Offer {
                    consumer_actor_ref: "actor:nonexistent-consumer".into(),
                    acceptance_criteria: vec!["Deliver proof".into()],
                }
            )
        )
        .await,
        Err(WorkError::ActorNotFound(_))
    ));
    advance_engagement(
        &mut client,
        &action(
            work,
            1,
            "actor:test:engagement-requester",
            "valid-offer",
            offered(),
        ),
    )
    .await
    .unwrap();
    advance_engagement(
        &mut client,
        &action(
            work,
            2,
            "actor:test:engagement-agent-a",
            "claim-first",
            EngagementAction::Claim,
        ),
    )
    .await
    .unwrap();
    let released = advance_engagement(
        &mut client,
        &action(
            work,
            3,
            "actor:test:engagement-agent-a",
            "release",
            EngagementAction::Release {
                reason: "Need different skill".into(),
            },
        ),
    )
    .await
    .unwrap();
    assert_eq!(released["snapshot"]["engagement"]["phase"], "offered");
    assert_eq!(released["snapshot"]["engagement"]["claimEpoch"], 1);
    let new_claim = advance_engagement(
        &mut client,
        &action(
            work,
            4,
            "actor:test:engagement-agent-b",
            "claim-after-release",
            EngagementAction::Claim,
        ),
    )
    .await
    .unwrap();
    assert_eq!(new_claim["snapshot"]["engagement"]["claimEpoch"], 2);
    let cancelled = advance_engagement(
        &mut client,
        &action(
            work,
            5,
            "actor:test:engagement-requester",
            "cancel",
            EngagementAction::Cancel {
                reason: "Consumer no longer needs output".into(),
            },
        ),
    )
    .await
    .unwrap();
    assert_eq!(cancelled["state"], "abandoned");
    assert_eq!(cancelled["snapshot"]["engagement"]["phase"], "cancelled");
    assert!(matches!(
        advance_engagement(
            &mut client,
            &action(
                work,
                6,
                "actor:test:engagement-agent-b",
                "submit-after-cancel",
                submit(2, "delivery:test:too-late")
            )
        )
        .await,
        Err(WorkError::Conflict(_))
    ));
    println!("R7_RELEASE_CANCEL_FENCING_LIVE_PG18_PASS");
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18/schema13 HOST_RUST_TEST_DSN"]
async fn offer_inventory_is_bounded_filtered_and_paginated_without_skips() {
    use std::collections::HashSet;
    let mut client = connect().await;
    actors(&client).await;
    for index in 0..23usize {
        let work_ref = format!("work:test:engagement:inventory-{index:02}");
        new_work(&mut client, &work_ref).await;
        let offering = action(
            &work_ref,
            1,
            "actor:test:engagement-requester",
            &format!("inventory-offer-{index:02}"),
            EngagementAction::Offer {
                consumer_actor_ref: "actor:test:engagement-consumer".into(),
                acceptance_criteria: vec![format!(
                    "消费者标准 index={index} {}",
                    "通过独立验收才能视为完成".repeat(50),
                )],
            },
        );
        advance_engagement(&mut client, &offering).await.unwrap();
    }
    let mut options = ListEngagements {
        phase: Some(Phase::Offered),
        consumer_actor_ref: Some("actor:test:engagement-consumer".into()),
        assignee_actor_ref: None,
        limit: 200,
        max_bytes: 16_384,
        before_updated_at: None,
        before_work_ref: None,
    };
    let mut all: HashSet<String> = HashSet::new();
    let mut pages = 0;
    loop {
        let result = list_engagements(&mut client, &options).await.unwrap();
        let bytes = serde_json_canonicalizer::to_vec(&result).unwrap().len();
        assert!(
            bytes <= options.max_bytes,
            "RFC8785 response budget must hold"
        );
        let entries = result["engagements"].as_array().unwrap();
        assert!(!entries.is_empty());
        for item in entries {
            let id = item["workRef"].as_str().unwrap().to_owned();
            assert!(
                all.insert(id.clone()),
                "duplicate or skipped cursor member {id}"
            );
            assert_eq!(item["engagement"]["phase"], "offered");
            assert_eq!(item["engagement"]["schemaVersion"], 1);
        }
        pages += 1;
        if result["hasMore"] == false {
            assert!(result["nextCursor"].is_null());
            break;
        }
        options.before_updated_at = Some(
            result["nextCursor"]["beforeUpdatedAt"]
                .as_str()
                .unwrap()
                .to_owned(),
        );
        options.before_work_ref = Some(
            result["nextCursor"]["beforeWorkRef"]
                .as_str()
                .unwrap()
                .to_owned(),
        );
        assert!(pages < 23);
    }
    assert_eq!(all.len(), 23);
    assert!(
        pages >= 2,
        "long UTF8 criteria must force bounded byte-prefix pages"
    );

    let assigned = list_engagements(
        &mut client,
        &ListEngagements {
            phase: Some(Phase::Claimed),
            ..ListEngagements::default()
        },
    )
    .await
    .unwrap();
    assert_eq!(assigned["engagements"].as_array().unwrap().len(), 0);

    assert!(matches!(
        list_engagements(
            &mut client,
            &ListEngagements {
                before_updated_at: Some("2026-11-11T00:00:00+00:00".into()),
                ..ListEngagements::default()
            }
        )
        .await,
        Err(WorkError::Invalid(_))
    ));
    assert!(matches!(
        list_engagements(
            &mut client,
            &ListEngagements {
                limit: 0,
                ..ListEngagements::default()
            }
        )
        .await,
        Err(WorkError::Invalid(_))
    ));
    assert!(matches!(
        list_engagements(
            &mut client,
            &ListEngagements {
                max_bytes: 8192,
                ..ListEngagements::default()
            }
        )
        .await,
        Err(WorkError::Invalid(_))
    ));
    println!("R7_WORK_INTAKE_DISCOVERY_RR_CURSOR_BUDGET_NO_SKIP_PASS pages={pages}");
}

/// A mature reusable consumer: Work revisions already feed the native
/// Social/Attention change projection. Do not build another task inbox.
#[tokio::test]
#[ignore = "requires disposable PostgreSQL18/schema13 HOST_RUST_TEST_DSN"]
async fn consumer_attention_receives_work_claim_delivery_and_review_without_new_bus() {
    use ordivon_host_rust::attention::{self, TargetKind, DEFAULT_COLLECTION_BYTES};
    let mut db = connect().await;
    let work = "work:test:engagement:attention-r7";
    new_work(&mut db, work).await;
    let consumer = "actor:test:engagement-consumer";
    let follow = attention::follow(
        &mut db,
        consumer,
        TargetKind::Work,
        work,
        "request:test:follow-engagement",
    )
    .await
    .unwrap();
    assert_eq!(follow["admission"], "committed");
    let horizon = follow["changeSequence"].as_i64().unwrap();

    let events = [
        (
            1,
            "actor:test:engagement-requester",
            "event-offer",
            offered(),
        ),
        (
            2,
            "actor:test:engagement-agent-a",
            "event-claim",
            EngagementAction::Claim,
        ),
        (
            3,
            "actor:test:engagement-agent-a",
            "event-submit",
            submit(1, "delivery:test:attention"),
        ),
        (
            4,
            consumer,
            "event-review",
            review(1, ReviewDecision::Accepted),
        ),
    ];
    for (rev, who, request, engagement_action) in events {
        advance_engagement(&mut db, &action(work, rev, who, request, engagement_action))
            .await
            .unwrap();
    }
    let changes = attention::delta(&mut db, consumer, horizon, 50, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    let rows = changes["events"].as_array().unwrap();
    let actual: Vec<_> = rows
        .iter()
        .filter(|row| row["eventKind"] == "work_snapshot")
        .collect();
    assert_eq!(actual.len(), 4);
    let mut last = horizon;
    for (index, event) in actual.iter().enumerate() {
        assert_eq!(event["sourceRef"], work);
        assert_eq!(event["contextRef"], format!("{}", index + 2));
        assert_eq!(event["navigationKind"], "work");
        assert_eq!(event["navigationRef"], work);
        assert!(event["reasons"]
            .as_array()
            .unwrap()
            .iter()
            .any(|x| x == "followed_work"));
        let cursor = event["changeSequence"].as_i64().unwrap();
        assert!(cursor > last);
        last = cursor;
    }
    let ack = attention::ack(
        &mut db,
        consumer,
        changes["snapshotHighSequence"].as_i64().unwrap(),
        "request:test:attention-claim-delivery-ack",
    )
    .await
    .unwrap();
    assert_eq!(ack["previousCursor"], 0);
    let empty = attention::delta(
        &mut db,
        consumer,
        ack["cursor"].as_i64().unwrap(),
        50,
        DEFAULT_COLLECTION_BYTES,
    )
    .await
    .unwrap();
    assert!(empty["events"].as_array().unwrap().is_empty());
    let saved = get_work(&mut db, work, None).await.unwrap();
    assert_eq!(saved["state"], "completed");
    println!("R7_EXISTING_ATTENTION_WORK_DELIVERY_CONSUMER_REENTRY_PASS");
}
