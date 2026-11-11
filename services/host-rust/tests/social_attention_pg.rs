//! Real PostgreSQL 18/schema13 qualification; never accepts the production DSN.
//! Run only with HOST_RUST_TEST_DSN pointing at a disposable instance:
//! cargo test --offline --test social_attention_pg -- --ignored
use ordivon_host_rust::{
    attention::{self, TargetKind, DEFAULT_COLLECTION_BYTES},
    social::{self, AddMessageRelation, MessageKind, MessageRelationKind, PostMessage, TopicState},
};
use serde_json::json;
use tokio_postgres::{Client, NoTls};

async fn connect() -> Client {
    let dsn = std::env::var("HOST_RUST_TEST_DSN")
        .expect("HOST_RUST_TEST_DSN is REQUIRED; never use production Host DSN");
    assert!(
        dsn.contains("127.0.0.1") || dsn.contains("localhost"),
        "PG migration integration test DSN must be loopback-only"
    );
    let (client, connection) = tokio_postgres::connect(&dsn, NoTls).await.unwrap();
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            panic!("postgres connection: {e}");
        }
    });
    client
}
async fn seed(client: &Client, suffix: &str) -> (String, String, String) {
    let actor = format!("actor:host-rust-b:{suffix}");
    let space = format!("space:host-rust-b:{suffix}");
    let topic = format!("topic:host-rust-b:{suffix}");
    client
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent')",
            &[&actor],
        )
        .await
        .unwrap();
    client.execute(
        "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES($1,'Rust B test',$2)",
        &[&space,&actor],
    ).await.unwrap();
    client
        .execute(
            "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) \
         VALUES($1,$2,'Attention test','open',$3)",
            &[&topic, &space, &actor],
        )
        .await
        .unwrap();
    (actor, space, topic)
}
fn input(suffix: &str, actor: &str, space: &str, topic: &str, body: &str) -> PostMessage {
    PostMessage {
        message_ref: format!("message:host-rust-b:{suffix}"),
        client_request_id: format!("request:host-rust-b:{suffix}"),
        space_ref: space.to_owned(),
        topic_ref: topic.to_owned(),
        author_actor_ref: actor.to_owned(),
        message_kind: MessageKind::Finding,
        body: body.to_owned(),
        recorded_at_ms: 1_794_300_000_001,
    }
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn subscribed_message_delta_ack_reentry_and_late_relation() {
    let mut db = connect().await;
    db.batch_execute("SET TIME ZONE 'Asia/Shanghai'")
        .await
        .unwrap();
    let (actor, space, topic) = seed(&db, "attention-flow").await;
    let sub = attention::follow(
        &mut db,
        &actor,
        TargetKind::Topic,
        &topic,
        "request:follow:1",
    )
    .await
    .unwrap();
    assert_eq!(sub["admission"], "committed");
    assert!(
        sub["createdAt"].as_str().unwrap().ends_with("+08:00"),
        "{sub}"
    );
    assert_eq!(sub["targetKind"], "topic");
    let sub_replay = attention::follow(
        &mut db,
        &actor,
        TargetKind::Topic,
        &topic,
        "request:follow:2",
    )
    .await
    .unwrap();
    assert_eq!(sub_replay["admission"], "existing");
    let listed =
        attention::list_subscriptions(&mut db, &actor, None, None, 100, DEFAULT_COLLECTION_BYTES)
            .await
            .unwrap();
    assert_eq!(listed["subscriptions"].as_array().unwrap().len(), 1);
    assert_eq!(listed["hasMore"], false);
    let message1 = input(
        "attention-message-a",
        &actor,
        &space,
        &topic,
        "📣 first 汉字",
    );
    let message2 = input("attention-message-b", &actor, &space, &topic, "second 🚀");
    let first = social::post_message(&mut db, &message1).await.unwrap();
    assert_eq!(first["admission"], "committed");
    assert!(first["createdAt"].as_str().unwrap().ends_with("+08:00"));
    let second = social::post_message(&mut db, &message2).await.unwrap();
    let page1 = attention::delta(&mut db, &actor, 0, 1, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    assert_eq!(page1["events"].as_array().unwrap().len(), 1);
    assert_eq!(page1["hasMore"], true);
    assert_eq!(page1["events"][0]["sourceRef"], first["messageRef"]);
    let after = page1["nextAfterSequence"].as_i64().unwrap();
    let page2 = attention::delta(&mut db, &actor, after, 100, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    assert_eq!(page2["hasMore"], false);
    assert!(page2["events"]
        .as_array()
        .unwrap()
        .iter()
        .any(|event| event["sourceRef"] == second["messageRef"]));
    let nav = attention::reentry(&mut db, &actor, Some(0), 100, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    assert_eq!(nav["items"].as_array().unwrap().len(), 1);
    assert_eq!(nav["items"][0]["navigationRef"], topic);
    assert_eq!(nav["items"][0]["eventCount"], 2);
    let high = page2["snapshotHighSequence"].as_i64().unwrap();
    let ack = attention::ack(&mut db, &actor, high, "request:attention:ack:1")
        .await
        .unwrap();
    assert_eq!(ack["cursor"], high);
    assert_eq!(ack["previousCursor"], 0);
    // Response loss and reconnection cannot allocate a new ACK effect.
    drop(db);
    let mut db = connect().await;
    let replay = attention::ack(&mut db, &actor, high, "request:attention:ack:1")
        .await
        .unwrap();
    assert_eq!(replay["admission"], "existing");
    assert_eq!(replay["cursor"], high);
    assert!(attention::ack(
        &mut db,
        &actor,
        high + 1_000_000,
        "request:attention:ack:bad"
    )
    .await
    .is_err());
    let empty = attention::get(&mut db, &actor, 100, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    assert_eq!(empty["events"], json!([]));
    // A relation added *after* message creation retains its own later change coordinate.
    let rel = social::add_message_relation(
        &mut db,
        &AddMessageRelation {
            source_message_ref: message1.message_ref.clone(),
            relation: MessageRelationKind::Mentions,
            target_ref: actor.clone(),
            actor_ref: actor.clone(),
        },
        "request:late-mention",
    )
    .await
    .unwrap();
    assert_eq!(rel["admission"], "committed");
    let relation_replay = social::add_message_relation(
        &mut db,
        &AddMessageRelation {
            source_message_ref: message1.message_ref.clone(),
            relation: MessageRelationKind::Mentions,
            target_ref: actor.clone(),
            actor_ref: actor.clone(),
        },
        "request:late-mention",
    )
    .await
    .unwrap();
    assert_eq!(relation_replay["admission"], "existing");
    let late = attention::delta(&mut db, &actor, high, 100, DEFAULT_COLLECTION_BYTES)
        .await
        .unwrap();
    assert_eq!(late["events"].as_array().unwrap().len(), 1);
    assert_eq!(late["events"][0]["eventKind"], "message_relation");
    assert!(late["events"][0]["reasons"]
        .as_array()
        .unwrap()
        .contains(&json!("mentioned")));
    let gone = attention::unfollow(
        &mut db,
        &actor,
        TargetKind::Topic,
        &topic,
        "request:follow:1",
    )
    .await
    .unwrap();
    assert_eq!(gone["admission"], "committed");
    let absent = attention::unfollow(
        &mut db,
        &actor,
        TargetKind::Topic,
        &topic,
        "request:follow:1",
    )
    .await
    .unwrap();
    assert_eq!(absent["admission"], "existing");
    // Desired state, NOT an exact historical receipt: old follow can re-enable target.
    let restored = attention::follow(
        &mut db,
        &actor,
        TargetKind::Topic,
        &topic,
        "request:follow:1",
    )
    .await
    .unwrap();
    assert_eq!(restored["admission"], "committed");
    assert!(restored["changeSequence"].as_i64().unwrap() > sub["changeSequence"].as_i64().unwrap());
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn social_message_receipt_topic_cas_and_cursor() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "social-flow").await;
    let message = input("social-flow-a", &actor, &space, &topic, "持续消息 😄");
    let posted = social::post_message(&mut db, &message).await.unwrap();
    assert!(posted["sequence"].as_i64().unwrap() > 0);
    assert_eq!(posted["admission"], "committed");
    let message_ref = posted["messageRef"].as_str().unwrap().to_string();
    let expected_digest = posted["messageDigest"].as_str().unwrap().to_string();
    // Golden from Python Host 0.8.0 rfc8785, same exact Unicode + 64-bit timestamp.
    assert_eq!(
        expected_digest,
        "sha256:3ff99039396e3d6ff16ff699ff4b303ba1daf3594c6768e31394d44cbf3d40f2"
    );
    let stored_digest: String = db
        .query_one(
            "SELECT request_digest FROM command_receipts WHERE client_request_id=$1",
            &[&message.client_request_id],
        )
        .await
        .unwrap()
        .get("request_digest");
    assert_eq!(
        stored_digest,
        "sha256:4744c7a560c877403e9fa21f86662a54ec0f1c59907810adc64edbc63bd4f598"
    );
    let receipt = db
        .query_one(
            "SELECT response FROM command_receipts WHERE client_request_id=$1",
            &[&message.client_request_id],
        )
        .await
        .unwrap()
        .get::<_, tokio_postgres::types::Json<serde_json::Value>>(0)
        .0;
    assert_eq!(receipt["kind"], "ordivon.host-message-post-receipt-ref");
    assert!(
        receipt.get("body").is_none(),
        "receipt must NOT duplicate 64kiB body"
    );
    drop(db);
    let mut db = connect().await;
    let replay = social::post_message(&mut db, &message).await.unwrap();
    assert_eq!(replay["admission"], "existing");
    assert_eq!(replay["messageRef"], message_ref);
    assert_eq!(replay["messageDigest"], expected_digest);
    assert_eq!(replay["sequence"], posted["sequence"]);
    let mut tampered = message.clone();
    tampered.body = "different".into();
    assert!(social::post_message(&mut db, &tampered).await.is_err());
    let seq = posted["sequence"].as_i64().unwrap();
    let acknowledged = social::ack_topic_cursor(&mut db, &actor, &topic, seq, "request:topic:ack")
        .await
        .unwrap();
    assert_eq!(acknowledged["cursor"], seq);
    assert_eq!(acknowledged["topicHighSequence"], seq);
    let replay_ack = social::ack_topic_cursor(&mut db, &actor, &topic, seq, "request:topic:ack")
        .await
        .unwrap();
    assert_eq!(replay_ack["admission"], "existing");
    assert!(
        social::ack_topic_cursor(&mut db, &actor, &topic, seq - 1, "request:topic:ack:old")
            .await
            .is_err()
    );
    assert!(
        social::ack_topic_cursor(&mut db, &actor, &topic, seq + 1, "request:topic:ack:beyond")
            .await
            .is_err()
    );
    let closed = social::set_topic_state(
        &mut db,
        &topic,
        &actor,
        TopicState::Closed,
        TopicState::Open,
        seq,
        "request:topic:close",
    )
    .await
    .unwrap();
    assert_eq!(closed["state"], "closed");
    assert_eq!(closed["admission"], "committed");
    let close_replay = social::set_topic_state(
        &mut db,
        &topic,
        &actor,
        TopicState::Closed,
        TopicState::Open,
        seq,
        "request:topic:close",
    )
    .await
    .unwrap();
    assert_eq!(close_replay["admission"], "existing");
    let second = input(
        "social-flow-b",
        &actor,
        &space,
        &topic,
        "must not post after close",
    );
    assert!(social::post_message(&mut db, &second).await.is_err());
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn concurrent_post_and_close_have_one_linearization() {
    let seed_db = connect().await;
    let (actor, space, topic) = seed(&seed_db, "social-race").await;
    drop(seed_db);
    let mut a = connect().await;
    let mut b = connect().await;
    let message = input("social-race-message", &actor, &space, &topic, "racy body");
    let (posted, closed) = tokio::join!(
        social::post_message(&mut a, &message),
        social::set_topic_state(
            &mut b,
            &topic,
            &actor,
            TopicState::Closed,
            TopicState::Open,
            0,
            "request:topic:race:close"
        ),
    );
    let wins = u8::from(posted.is_ok()) + u8::from(closed.is_ok());
    assert_eq!(
        wins, 1,
        "post and close cannot both win same pre-high horizon"
    );
    let row = b
        .query_one("SELECT state FROM topics WHERE topic_ref=$1", &[&topic])
        .await
        .unwrap();
    let state: String = row.get("state");
    let count: i64 = b
        .query_one(
            "SELECT COUNT(*) AS n FROM messages WHERE topic_ref=$1",
            &[&topic],
        )
        .await
        .unwrap()
        .get("n");
    assert!((state == "open" && count == 1) || (state == "closed" && count == 0));
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn topic_resume_pagination_and_consumption_cursor_match_python_contract() {
    let mut db = connect().await;
    db.batch_execute("SET TIME ZONE 'Asia/Shanghai'")
        .await
        .unwrap();
    let (actor, space, topic) = seed(&db, "resume-r2").await;
    let msg1 = input("resume-r2-first", &actor, &space, &topic, "第一页 🧩");
    let msg2 = input("resume-r2-second", &actor, &space, &topic, "第二页 🧭");
    let first = social::post_message(&mut db, &msg1).await.unwrap();
    let second = social::post_message(&mut db, &msg2).await.unwrap();

    let cursor_before = social::get_topic_cursor(&mut db, &actor, &topic)
        .await
        .unwrap();
    assert_eq!(cursor_before["cursor"], 0);
    assert_eq!(cursor_before["topicHighSequence"], second["sequence"]);

    let first_page = social::resume_topic(&mut db, &topic, 0, 1, 131_072)
        .await
        .unwrap();
    assert_eq!(first_page["hasMore"], true);
    assert_eq!(first_page["messages"].as_array().unwrap().len(), 1);
    assert_eq!(first_page["messages"][0]["messageRef"], first["messageRef"]);
    assert_eq!(
        first_page["messages"][0]["messageDigest"],
        first["messageDigest"]
    );
    assert_eq!(first_page["messages"][0]["body"], "第一页 🧩");
    assert!(first_page["messages"][0]["createdAt"]
        .as_str()
        .unwrap()
        .ends_with("+08:00"));
    let next = first_page["nextAfterSequence"].as_i64().unwrap();
    let last_page = social::resume_topic(&mut db, &topic, next, 50, 524_288)
        .await
        .unwrap();
    assert_eq!(last_page["hasMore"], false);
    assert_eq!(last_page["messages"][0]["messageRef"], second["messageRef"]);
    assert_eq!(last_page["nextAfterSequence"], second["sequence"]);

    let ack = social::ack_topic_cursor(
        &mut db,
        &actor,
        &topic,
        next,
        "request:host-rust-b:resume-r2-ack",
    )
    .await
    .unwrap();
    assert_eq!(ack["previousCursor"], 0);
    let cursor_after = social::get_topic_cursor(&mut db, &actor, &topic)
        .await
        .unwrap();
    assert_eq!(cursor_after["cursor"], next);
    assert_eq!(cursor_after["topicHighSequence"], second["sequence"]);

    assert!(social::resume_topic(&mut db, &topic, 0, 0, 524_288)
        .await
        .is_err());
    assert!(social::resume_topic(&mut db, &topic, 0, 1, 131_071)
        .await
        .is_err());
    assert!(social::resume_topic(&mut db, &topic, -1, 1, 524_288)
        .await
        .is_err());

    let exhausted = social::resume_topic(
        &mut db,
        &topic,
        second["sequence"].as_i64().unwrap(),
        50,
        524_288,
    )
    .await
    .unwrap();
    assert_eq!(exhausted["messages"], json!([]));
    assert_eq!(exhausted["hasMore"], false);
}
#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn topic_resume_detects_corruption_in_fetched_but_byte_trimmed_message() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "digest-trim-r2").await;
    let first = input(
        "digest-trim-r2-first",
        &actor,
        &space,
        &topic,
        "small first",
    );
    let second = input(
        "digest-trim-r2-second",
        &actor,
        &space,
        &topic,
        &"汉".repeat(50_000),
    );
    social::post_message(&mut db, &first).await.unwrap();
    social::post_message(&mut db, &second).await.unwrap();
    // Deliberate isolated-database corruption: Python verifies all fetched
    // SQL rows before applying response byte trimming. Rust must do the same.
    db.execute(
        "UPDATE messages SET message_digest=$1 WHERE message_ref=$2",
        &[&format!("sha256:{}", "0".repeat(64)), &second.message_ref],
    )
    .await
    .unwrap();
    let result = social::resume_topic(&mut db, &topic, 0, 2, 131_072).await;
    assert!(matches!(result, Err(social::SocialError::Integrity(_))));
}
