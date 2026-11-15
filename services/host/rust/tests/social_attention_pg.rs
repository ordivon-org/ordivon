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

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn topic_create_receipts_and_participation_desired_state() {
    let mut client = connect().await;
    client
        .batch_execute("SET TIME ZONE 'Asia/Shanghai'")
        .await
        .unwrap();
    let (actor, space, _) = seed(&client, "native-topic-create-r3").await;
    let input = social::CreateTopic {
        topic_ref: "topic:host-rust-b:native-r3-new".into(),
        space_ref: space.clone(),
        title: "Native Rust discussion 🧩".into(),
        actor_ref: actor.clone(),
        client_request_id: "request:host-rust-b:r3-topic-create".into(),
    };
    let created = social::create_topic(&mut client, &input).await.unwrap();
    assert_eq!(created["admission"], "committed");
    assert_eq!(created["state"], "open");
    assert!(created["createdAt"].as_str().unwrap().ends_with("+08:00"));
    let replay = social::create_topic(&mut client, &input).await.unwrap();
    assert_eq!(replay["admission"], "existing");
    assert_eq!(replay["createdAt"], created["createdAt"]);
    let mut changed = input.clone();
    changed.title = "Different initial semantics".into();
    assert!(social::create_topic(&mut client, &changed).await.is_err());
    let mut second_request = changed.clone();
    second_request.client_request_id = "request:host-rust-b:r3-topic-create-changed".into();
    assert!(social::create_topic(&mut client, &second_request)
        .await
        .is_err());

    let joined = social::set_participation(
        &mut client,
        &space,
        &actor,
        social::ParticipationStanding::Joined,
        "same-identity",
    )
    .await
    .unwrap();
    assert_eq!(joined["standing"], "joined");
    assert!(joined["updatedAt"].as_str().unwrap().ends_with("+08:00"));
    let again = social::set_participation(
        &mut client,
        &space,
        &actor,
        social::ParticipationStanding::Joined,
        "same-identity",
    )
    .await
    .unwrap();
    assert_eq!(again, joined);
    let left = social::set_participation(
        &mut client,
        &space,
        &actor,
        social::ParticipationStanding::Left,
        "same-identity",
    )
    .await
    .unwrap();
    assert_eq!(left["standing"], "left");
    let rejoined = social::set_participation(
        &mut client,
        &space,
        &actor,
        social::ParticipationStanding::Joined,
        "same-identity",
    )
    .await
    .unwrap();
    assert_eq!(rejoined["standing"], "joined");

    let count: i64 = client
        .query_one(
            "SELECT count(*) FROM topics WHERE topic_ref=$1",
            &[&input.topic_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(count, 1);
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn space_create_get_and_reply_loss_replay_are_exact() {
    let mut client = connect().await;
    client
        .batch_execute("SET TIME ZONE 'Asia/Shanghai'")
        .await
        .unwrap();
    let actor = "actor:host-rust-b:space-create-r3";
    client
        .execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent')",
            &[&actor],
        )
        .await
        .unwrap();
    let input = social::CreateSpace {
        space_ref: "space:host-rust-b:space-create-r3".into(),
        purpose: "Rust 领域创建 Space 🧩".into(),
        actor_ref: actor.into(),
        subject_refs: vec!["topic:引用".into(), "work:backlink".into()],
        client_request_id: "request:host-rust-b:space-create-r3".into(),
    };
    let created = social::create_space(&mut client, &input).await.unwrap();
    assert_eq!(created["admission"], "committed");
    assert_eq!(created["subjectCount"], 2);
    assert_eq!(
        created["subjectRefs"],
        json!(["topic:引用", "work:backlink"])
    );
    assert_eq!(created["participantCount"], 0);
    assert_eq!(created["topicCount"], 0);
    assert!(created["createdAt"].as_str().unwrap().ends_with("+08:00"));
    // Simulate response-loss, then reconnect and re-submit same immutable receipt.
    drop(client);
    let mut client = connect().await;
    let replay = social::create_space(&mut client, &input).await.unwrap();
    assert_eq!(replay["admission"], "existing");
    assert_eq!(replay["subjectRefs"], created["subjectRefs"]);
    assert_eq!(replay["createdAt"], created["createdAt"]);
    let mut conflict = input.clone();
    conflict.subject_refs = vec!["different".into()];
    assert!(social::create_space(&mut client, &conflict).await.is_err());
    conflict.client_request_id = "request:host-rust-b:space-create-r3-changed".into();
    assert!(social::create_space(&mut client, &conflict).await.is_err());
    // Connection reopen resets the PostgreSQL session timezone. The Python
    // Host's datetime.isoformat is also session-local; a new read in UTC may
    // legitimately format the same instant differently from the receipt's +08.
    let utc_read = social::get_space(&mut client, &input.space_ref, 200, 200, 2_097_152)
        .await
        .unwrap();
    assert!(utc_read["createdAt"].as_str().unwrap().ends_with("+00:00"));
    client
        .batch_execute("SET TIME ZONE 'Asia/Shanghai'")
        .await
        .unwrap();
    let got = social::get_space(&mut client, &input.space_ref, 200, 200, 2_097_152)
        .await
        .unwrap();
    let mut expected = created.clone();
    expected.as_object_mut().unwrap().remove("admission");
    assert_eq!(got, expected);
    // Python SpaceInput strips U+001C at boundaries: Rust must not weaken it.
    let mut invalid = input.clone();
    invalid.space_ref = "space:host-rust-b:bad\u{001c}".into();
    invalid.client_request_id = "request:host-rust-b:space-create-r3-bad".into();
    assert!(social::create_space(&mut client, &invalid).await.is_err());
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, full Host Alembic schema13, HOST_RUST_TEST_DSN"]
async fn concurrent_space_creation_has_one_authoritative_subject_set() {
    let a = connect().await;
    let (actor, _, _) = seed(&a, "space-concurrent-r3").await;
    drop(a);
    let mut a = connect().await;
    let mut b = connect().await;
    let left = social::CreateSpace {
        space_ref: "space:host-rust-b:race-r3".into(),
        purpose: "same purpose".into(),
        actor_ref: actor.clone(),
        subject_refs: vec!["subject:left".into()],
        client_request_id: "request:host-rust-b:race-left".into(),
    };
    let mut right = left.clone();
    right.subject_refs = vec!["subject:right".into()];
    right.client_request_id = "request:host-rust-b:race-right".into();
    let (left_result, right_result) = tokio::join!(
        social::create_space(&mut a, &left),
        social::create_space(&mut b, &right)
    );
    assert_eq!(
        u8::from(left_result.is_ok()) + u8::from(right_result.is_ok()),
        1,
        "one unique space cannot commit two different authoritative subjects"
    );
    let chosen = left_result.ok().or(right_result.ok()).unwrap();
    let subject: String = b
        .query_one(
            "SELECT subject_ref FROM space_subjects WHERE space_ref=$1",
            &[&left.space_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(chosen["subjectRefs"], json!([subject]));
    let count: i64 = b
        .query_one(
            "SELECT count(*) FROM space_subjects WHERE space_ref=$1",
            &[&left.space_ref],
        )
        .await
        .unwrap()
        .get(0);
    assert_eq!(count, 1);
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18 Schema13"]
async fn message_read_and_unicode_search_exact_and_integrity() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "msg-search-r4").await;
    let a = input(
        "msg-search-r4-first",
        &actor,
        &space,
        &topic,
        "中文检索词 alpha evidence",
    );
    let mut b = input(
        "msg-search-r4-second",
        &actor,
        &space,
        &topic,
        "中文检索词 beta evidence",
    );
    b.message_ref = "message:msg-search-r4-second".into();
    b.client_request_id = "request:msg-search-r4-second".into();
    let first = social::post_message(&mut db, &a).await.unwrap();
    let second = social::post_message(&mut db, &b).await.unwrap();
    let read = social::get_message(&mut db, &a.message_ref, None)
        .await
        .unwrap();
    assert_eq!(read["kind"], "ordivon.host-message-read");
    assert_eq!(read["messageDigest"], first["messageDigest"]);
    assert!(
        social::get_message(&mut db, &a.message_ref, Some("sha256:wrong"))
            .await
            .is_err()
    );
    assert!(
        social::get_message(&mut db, "message:search:r4:missing", None)
            .await
            .is_err()
    );
    let mut q = social::SearchMessages {
        query: "中文检索词".into(),
        space_ref: Some(space.clone()),
        topic_ref: Some(topic.clone()),
        before_sequence: None,
        limit: 1,
        max_bytes: 131_072,
    };
    let p1 = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(p1["hasMore"], true);
    assert_eq!(p1["messages"][0]["messageRef"], second["messageRef"]);
    assert!(p1["truthBoundary"]
        .as_str()
        .unwrap()
        .starts_with("PostgreSQL CJK indexed Unicode-gram locator"));
    q.before_sequence = p1["nextBeforeSequence"].as_i64();
    let p2 = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(p2["hasMore"], false);
    assert_eq!(p2["messages"][0]["messageRef"], first["messageRef"]);
    assert!(p2["nextBeforeSequence"].is_null());
    q.before_sequence = None;
    q.limit = 100;
    q.query = "中文".into();
    let literal = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(literal["messages"].as_array().unwrap().len(), 2);
    q.query = "alpha".into();
    let fts = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(fts["messages"].as_array().unwrap().len(), 1);
    assert_eq!(fts["messages"][0]["messageRef"], first["messageRef"]);
    q.before_sequence = Some(0);
    assert!(social::search_messages(&mut db, &q).await.is_err());
    q.before_sequence = None;
    q.max_bytes = 1024;
    assert!(social::search_messages(&mut db, &q).await.is_err());
    db.execute(
        "UPDATE messages SET message_digest=$1 WHERE message_ref=$2",
        &[&format!("sha256:{}", "0".repeat(64)), &a.message_ref],
    )
    .await
    .unwrap();
    assert!(matches!(
        social::get_message(&mut db, &a.message_ref, None).await,
        Err(social::SocialError::Integrity(_))
    ));
    q.query = "中文检索词".into();
    q.max_bytes = 131_072;
    assert!(matches!(
        social::search_messages(&mut db, &q).await,
        Err(social::SocialError::Integrity(_))
    ));
}
#[tokio::test]
#[ignore = "requires disposable PostgreSQL18 Schema13"]
async fn search_byte_budget_returns_stable_cursor() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "msg-search-long-r4").await;
    let body = format!("中文检索词 {}", "汉".repeat(30_000));
    let a = input("msg-search-long-r4-one", &actor, &space, &topic, &body);
    let mut b = input("msg-search-long-r4-two", &actor, &space, &topic, &body);
    b.message_ref = "message:msg-search-long-r4-two".into();
    b.client_request_id = "request:msg-search-long-r4-two".into();
    let one = social::post_message(&mut db, &a).await.unwrap();
    let two = social::post_message(&mut db, &b).await.unwrap();
    let mut q = social::SearchMessages {
        query: "中文检索词".into(),
        space_ref: Some(space),
        topic_ref: Some(topic),
        before_sequence: None,
        limit: 2,
        max_bytes: 131_072,
    };
    let p = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(p["hasMore"], true);
    assert_eq!(p["messages"].as_array().unwrap().len(), 1);
    assert_eq!(p["messages"][0]["messageRef"], two["messageRef"]);
    q.before_sequence = p["nextBeforeSequence"].as_i64();
    let last = social::search_messages(&mut db, &q).await.unwrap();
    assert_eq!(last["hasMore"], false);
    assert_eq!(last["messages"][0]["messageRef"], one["messageRef"]);
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18 Schema13 and Python original Host"]
async fn original_python_message_read_and_search_match_native_rust_exactly() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "python-search-r4").await;
    let first = input(
        "python-search-r4-first",
        &actor,
        &space,
        &topic,
        "中文检索词 alpha evidence",
    );
    let mut second = input(
        "python-search-r4-second",
        &actor,
        &space,
        &topic,
        "中文检索词 beta evidence",
    );
    second.message_ref = "message:python-search-r4-second".into();
    second.client_request_id = "request:python-search-r4-second".into();
    social::post_message(&mut db, &first).await.unwrap();
    social::post_message(&mut db, &second).await.unwrap();
    let read = social::get_message(&mut db, &first.message_ref, None)
        .await
        .unwrap();
    let mut queries = serde_json::Map::new();
    for (text, limit) in [
        ("中文检索词", 1i64),
        ("中文", 100),
        ("alpha", 100),
        ("nonexistent_r4", 100),
    ] {
        queries.insert(
            text.to_string(),
            social::search_messages(
                &mut db,
                &social::SearchMessages {
                    query: text.into(),
                    space_ref: Some(space.clone()),
                    topic_ref: Some(topic.clone()),
                    before_sequence: None,
                    limit,
                    max_bytes: 524_288,
                },
            )
            .await
            .unwrap(),
        );
    }
    let rust = json!({"read":read,"queries":queries});
    let python = r#"
import json, os
from ordivon_host_v2.social_store import SocialStore
assert os.environ["HOST_RUST_TEST_DSN"]==os.environ["ORDIVON_HOST_V2_DSN"]
store=SocialStore(os.environ["HOST_RUST_TEST_DSN"])
first=os.environ["B_R4_MESSAGE_REF"]
space=os.environ["B_R4_SPACE_REF"]
topic=os.environ["B_R4_TOPIC_REF"]
queries={q:store.search_messages(q,space_ref=space,topic_ref=topic,limit=limit,max_bytes=524288)
 for q,limit in (("中文检索词",1),("中文",100),("alpha",100),("nonexistent_r4",100))}
print(json.dumps({"read":store.get_message(first),"queries":queries},ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", python])
        .env("B_R4_MESSAGE_REF", &first.message_ref)
        .env("B_R4_SPACE_REF", &space)
        .env("B_R4_TOPIC_REF", &topic)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "python original oracle: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let parsed: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        rust, parsed,
        "Python original and Rust native message query projections differ"
    );
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18 Schema13 and original Python SocialStore"]
async fn relation_list_python_exact_dual_direction_pagination_and_opaque_self_reference() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "relation-list-r5").await;
    let first = input("relation-r5-first", &actor, &space, &topic, "first 🔎");
    let second = input("relation-r5-second", &actor, &space, &topic, "second 🧩");
    let third = input("relation-r5-third", &actor, &space, &topic, "third 🎯");
    social::post_message(&mut db, &first).await.unwrap();
    social::post_message(&mut db, &second).await.unwrap();
    social::post_message(&mut db, &third).await.unwrap();

    // Same-row direction BOTH must not duplicate the relation when its source
    // and target message are identical; REFERENCES targets remain opaque.
    let relations = [
        (
            &second.message_ref,
            MessageRelationKind::ReplyTo,
            &first.message_ref,
        ),
        (&second.message_ref, MessageRelationKind::Mentions, &actor),
        (
            &first.message_ref,
            MessageRelationKind::References,
            &second.message_ref,
        ),
        (
            &third.message_ref,
            MessageRelationKind::References,
            &second.message_ref,
        ),
        (
            &second.message_ref,
            MessageRelationKind::References,
            &second.message_ref,
        ),
    ];
    for (i, (source, relation, target)) in relations.iter().enumerate() {
        let result = social::add_message_relation(
            &mut db,
            &AddMessageRelation {
                source_message_ref: (*source).to_string(),
                relation: *relation,
                target_ref: (*target).to_string(),
                actor_ref: actor.clone(),
            },
            &format!("request:host-r5:relation-list-{i}"),
        )
        .await
        .unwrap();
        assert_eq!(result["admission"], "committed");
    }

    let mut input = social::ListMessageRelations {
        message_ref: second.message_ref.clone(),
        direction: social::RelationDirection::Both,
        relation: None,
        after_change_sequence: 0,
        limit: 2,
        max_bytes: 262_144,
    };
    let first_page = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(first_page["kind"], "ordivon.host-message-relation-list");
    assert_eq!(first_page["relations"].as_array().unwrap().len(), 2);
    assert_eq!(first_page["hasMore"], true);
    let after_first = first_page["nextAfterChangeSequence"].as_i64().unwrap();
    input.after_change_sequence = after_first;
    let second_page = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(second_page["relations"].as_array().unwrap().len(), 2);
    assert_eq!(second_page["hasMore"], true);
    input.after_change_sequence = second_page["nextAfterChangeSequence"].as_i64().unwrap();
    let third_page = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(third_page["relations"].as_array().unwrap().len(), 1);
    assert_eq!(third_page["hasMore"], false);
    assert!(third_page["nextAfterChangeSequence"].as_i64().unwrap() > input.after_change_sequence);

    input.after_change_sequence = 0;
    input.limit = 100;
    let both = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(both["relations"].as_array().unwrap().len(), 5);
    assert_eq!(both["hasMore"], false);
    input.direction = social::RelationDirection::Incoming;
    let incoming = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(incoming["relations"].as_array().unwrap().len(), 3);
    input.direction = social::RelationDirection::Outgoing;
    let outgoing = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(outgoing["relations"].as_array().unwrap().len(), 3);
    input.relation = Some(MessageRelationKind::Mentions);
    let mentions = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(mentions["relations"].as_array().unwrap().len(), 1);
    input.direction = social::RelationDirection::Both;
    input.relation = None;
    input.after_change_sequence = both["nextAfterChangeSequence"].as_i64().unwrap();
    let empty = social::list_message_relations(&mut db, &input)
        .await
        .unwrap();
    assert_eq!(empty["relations"], json!([]));
    assert_eq!(
        empty["nextAfterChangeSequence"],
        input.after_change_sequence
    );

    input.after_change_sequence = -1;
    assert!(social::list_message_relations(&mut db, &input)
        .await
        .is_err());
    input.after_change_sequence = 0;
    input.limit = 501;
    assert!(social::list_message_relations(&mut db, &input)
        .await
        .is_err());
    input.limit = 100;
    input.max_bytes = 100;
    assert!(social::list_message_relations(&mut db, &input)
        .await
        .is_err());
    input.max_bytes = 262_144;
    input.message_ref = "message:r5:absent".into();
    assert!(matches!(
        social::list_message_relations(&mut db, &input).await,
        Err(social::SocialError::NotFound(_))
    ));

    // Independent original Python code consumes the durable rows written by
    // Rust. Compare exact JSON (including timestamps and pagination) rather
    // than copying Python fixture expectations into Rust assertions.
    let py = r#"
import json, os
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.collaboration_inputs import MessageRelationKind
assert os.environ['HOST_RUST_TEST_DSN']==os.environ['ORDIVON_HOST_V2_DSN']
store=SocialStore(os.environ['HOST_RUST_TEST_DSN'])
ref=os.environ['R5_RELATION_MESSAGE_REF']
first=store.list_message_relations(ref,limit=2)
second=store.list_message_relations(ref,after_change_sequence=first['nextAfterChangeSequence'],limit=2)
third=store.list_message_relations(ref,after_change_sequence=second['nextAfterChangeSequence'],limit=2)
all_rel=store.list_message_relations(ref)
incoming=store.list_message_relations(ref,direction='incoming')
outgoing=store.list_message_relations(ref,direction='outgoing')
mentions=store.list_message_relations(ref,direction='outgoing',relation=MessageRelationKind.MENTIONS)
empty=store.list_message_relations(ref,after_change_sequence=all_rel['nextAfterChangeSequence'])
print(json.dumps(dict(first=first,second=second,third=third,
    all=all_rel,incoming=incoming,outgoing=outgoing,mentions=mentions,empty=empty),
    ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", py])
        .env("R5_RELATION_MESSAGE_REF", &second.message_ref)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Python original SocialStore error: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    // Same default timezone and immutable PG rows; these must be identical.
    let rust = json!({
        "first":first_page, "second":second_page, "third":third_page,
        "all":both, "incoming":incoming, "outgoing":outgoing,
        "mentions":mentions, "empty":empty,
    });
    assert_eq!(
        rust, python,
        "Rust relation.list differs from original Python Host"
    );
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18 Schema13 and original Python SocialStore"]
async fn topic_inventory_python_exact_order_state_cursor_and_single_snapshot() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "topic-list-r5").await;
    let alpha = format!("{topic}:alpha");
    let beta = format!("{topic}:beta");
    for (i, reference) in [alpha.clone(), beta.clone()].iter().enumerate() {
        let created = social::create_topic(
            &mut db,
            &social::CreateTopic {
                topic_ref: reference.clone(),
                space_ref: space.clone(),
                title: format!("Research 协作 {i} 🧩"),
                actor_ref: actor.clone(),
                client_request_id: format!("request:r5:topic-list-{i}"),
            },
        )
        .await
        .unwrap();
        assert_eq!(created["admission"], "committed");
    }
    let closed = social::set_topic_state(
        &mut db,
        &alpha,
        &actor,
        TopicState::Closed,
        TopicState::Open,
        0,
        "request:r5:topic-list-close",
    )
    .await
    .unwrap();
    assert_eq!(closed["state"], "closed");
    let first_page = social::list_topics(&mut db, &space, None, 1, 262_144)
        .await
        .unwrap();
    assert_eq!(first_page["topics"].as_array().unwrap().len(), 1);
    assert_eq!(first_page["hasMore"], true);
    let c1 = first_page["nextAfterTopicRef"]
        .as_str()
        .unwrap()
        .to_string();
    let second_page = social::list_topics(&mut db, &space, Some(&c1), 1, 262_144)
        .await
        .unwrap();
    assert_eq!(second_page["topics"][0]["topicRef"], alpha);
    assert_eq!(second_page["topics"][0]["state"], "closed");
    let c2 = second_page["nextAfterTopicRef"]
        .as_str()
        .unwrap()
        .to_string();
    let final_page = social::list_topics(&mut db, &space, Some(&c2), 1, 262_144)
        .await
        .unwrap();
    assert_eq!(final_page["topics"][0]["topicRef"], beta);
    assert_eq!(final_page["hasMore"], false);
    assert!(final_page["nextAfterTopicRef"].is_null());
    let all = social::list_topics(&mut db, &space, None, 200, 262_144)
        .await
        .unwrap();
    assert_eq!(all["topics"].as_array().unwrap().len(), 3);
    let empty = social::list_topics(&mut db, &space, Some("topic:zzzzz:r5"), 200, 262_144)
        .await
        .unwrap();
    assert_eq!(empty["topics"], json!([]));
    assert!(social::list_topics(&mut db, &space, None, 0, 262_144)
        .await
        .is_err());
    assert!(social::list_topics(&mut db, &space, None, 100, 100)
        .await
        .is_err());
    assert!(matches!(
        social::list_topics(&mut db, "space:absent:r5", None, 100, 262_144).await,
        Err(social::SocialError::NotFound(_))
    ));

    // Real Python Host authoritative current-row query against the same PG18.
    let py = r#"
import json,os
from ordivon_host_v2.social_store import SocialStore
assert os.environ["HOST_RUST_TEST_DSN"] == os.environ["ORDIVON_HOST_V2_DSN"]
store=SocialStore(os.environ["HOST_RUST_TEST_DSN"])
space=os.environ["R5_TOPIC_SPACE_REF"]
p1=store.list_topics(space,limit=1)
p2=store.list_topics(space,after_topic_ref=p1["nextAfterTopicRef"],limit=1)
p3=store.list_topics(space,after_topic_ref=p2["nextAfterTopicRef"],limit=1)
all_items=store.list_topics(space,limit=200)
empty=store.list_topics(space,after_topic_ref="topic:zzzzz:r5",limit=200)
print(json.dumps(dict(p1=p1,p2=p2,p3=p3,all=all_items,empty=empty),
 ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", py])
        .env("R5_TOPIC_SPACE_REF", &space)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Python original list_topics error: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    let rust = json!({
        "p1":first_page,"p2":second_page,"p3":final_page,"all":all,"empty":empty,
    });
    assert_eq!(
        rust, python,
        "native Rust topic.list diverges from Python Host"
    );
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18/schema13 and original Python Host"]
async fn social_relation_and_topic_inventory_byte_prefix_never_skips_rows() {
    let mut db = connect().await;
    let (actor, space, topic) = seed(&db, "social-byte-prefix-r5").await;
    let source = input(
        "social-byte-prefix-r5-message",
        &actor,
        &space,
        &topic,
        "bounded",
    );
    social::post_message(&mut db, &source).await.unwrap();

    // Opaque references may be long Unicode identifiers. No fake target row
    // is created: references never certify foreign existence or authority.
    for i in 0..12 {
        let target = format!("opaque:r5:{i:02}:{}", "汉".repeat(710));
        social::add_message_relation(
            &mut db,
            &AddMessageRelation {
                source_message_ref: source.message_ref.clone(),
                relation: MessageRelationKind::References,
                target_ref: target,
                actor_ref: actor.clone(),
            },
            &format!("request:r5:long-relation:{i}"),
        )
        .await
        .unwrap();
    }
    let mut cursor = 0_i64;
    let mut seen = std::collections::BTreeSet::new();
    let mut rel_pages = 0;
    let mut relation_first = None;
    loop {
        let input = social::ListMessageRelations {
            message_ref: source.message_ref.clone(),
            direction: social::RelationDirection::Outgoing,
            relation: None,
            after_change_sequence: cursor,
            limit: 100,
            max_bytes: 16_384,
        };
        let page = social::list_message_relations(&mut db, &input)
            .await
            .unwrap();
        assert!(serde_json_canonicalizer::to_vec(&page).unwrap().len() <= 16_384);
        if rel_pages == 0 {
            relation_first = Some(page.clone());
            assert_eq!(page["hasMore"], true, "fixture must exercise byte trimming");
        }
        for item in page["relations"].as_array().unwrap() {
            let position = item["changeSequence"].as_i64().unwrap();
            assert!(position > cursor);
            assert!(
                seen.insert(position),
                "a cursor must not repeat any relation"
            );
        }
        cursor = page["nextAfterChangeSequence"].as_i64().unwrap();
        rel_pages += 1;
        if !page["hasMore"].as_bool().unwrap() {
            break;
        }
        assert!(rel_pages < 10);
    }
    assert_eq!(seen.len(), 12);
    assert!(rel_pages >= 2);

    for i in 0..15 {
        let name = format!("{topic}:extra:{i:02}");
        social::create_topic(
            &mut db,
            &social::CreateTopic {
                topic_ref: name,
                space_ref: space.clone(),
                title: format!("索引页面-{i} {}", "界".repeat(480)),
                actor_ref: actor.clone(),
                client_request_id: format!("request:r5:long-topic:{i}"),
            },
        )
        .await
        .unwrap();
    }
    let mut topic_cursor: Option<String> = None;
    let mut refs = std::collections::BTreeSet::new();
    let mut topic_pages = 0;
    let mut topic_first = None;
    loop {
        let page = social::list_topics(&mut db, &space, topic_cursor.as_deref(), 100, 16_384)
            .await
            .unwrap();
        assert!(serde_json_canonicalizer::to_vec(&page).unwrap().len() <= 16_384);
        if topic_pages == 0 {
            topic_first = Some(page.clone());
            assert_eq!(page["hasMore"], true, "fixture must trim topic prefix");
        }
        for item in page["topics"].as_array().unwrap() {
            let reference = item["topicRef"].as_str().unwrap().to_owned();
            if let Some(before) = topic_cursor.as_deref() {
                assert!(reference.as_str() > before);
            }
            assert!(refs.insert(reference));
        }
        topic_cursor = page["nextAfterTopicRef"].as_str().map(str::to_owned);
        topic_pages += 1;
        if !page["hasMore"].as_bool().unwrap() {
            break;
        }
        assert!(topic_pages < 10);
    }
    assert_eq!(refs.len(), 16);
    assert!(topic_pages >= 2);

    let python_script = r#"
import json,os
from ordivon_host_v2.social_store import SocialStore
assert os.environ['HOST_RUST_TEST_DSN']==os.environ['ORDIVON_HOST_V2_DSN']
s=SocialStore(os.environ['HOST_RUST_TEST_DSN'])
rel=s.list_message_relations(os.environ['R5_LONG_MESSAGE'],
    direction='outgoing',limit=100,max_bytes=16384)
topics=s.list_topics(os.environ['R5_LONG_SPACE'],limit=100,max_bytes=16384)
print(json.dumps(dict(rel=rel,topics=topics),ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", python_script])
        .env("R5_LONG_MESSAGE", &source.message_ref)
        .env("R5_LONG_SPACE", &space)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Python original byte budget: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let expected: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        expected,
        json!({
            "rel":relation_first.unwrap(),
            "topics":topic_first.unwrap(),
        }),
        "Rust must trim the same canonical JSON prefix as Python Host"
    );
}

#[tokio::test]
#[ignore = "requires disposable PostgreSQL18, schema13, and original Python SocialStore"]
async fn three_space_inventory_native_python_json_exact_and_negative_contracts() {
    let mut db = connect().await;
    let (actor, space, _) = seed(&db, "inventory-r6-full").await;
    for subject in [
        "subject:r6:01",
        "subject:r6:02",
        "subject:r6:03",
        "subject:r6:04",
    ] {
        db.execute(
            "INSERT INTO space_subjects(space_ref,subject_ref) VALUES($1,$2)",
            &[&space, &subject],
        )
        .await
        .unwrap();
    }
    let s1 = social::list_space_subjects(&mut db, &space, None, 2, 262_144)
        .await
        .unwrap();
    let after_s = s1["nextAfterSubjectRef"].as_str().unwrap().to_string();
    let s2 = social::list_space_subjects(&mut db, &space, Some(&after_s), 2, 262_144)
        .await
        .unwrap();
    assert_eq!(s1["subjectRefs"], json!(["subject:r6:01", "subject:r6:02"]));
    assert_eq!(s2["subjectRefs"], json!(["subject:r6:03", "subject:r6:04"]));
    assert_eq!(s1["hasMore"], true);
    assert_eq!(s2["hasMore"], false);
    assert!(s2["nextAfterSubjectRef"].is_null());
    let mut participants = vec![actor.clone()];
    for i in 1..=2 {
        let p = format!("actor:r6:inventory:{i:02}");
        db.execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent')",
            &[&p],
        )
        .await
        .unwrap();
        participants.push(p);
    }
    for (i, a) in participants.iter().enumerate() {
        let standing = match i {
            0 => social::ParticipationStanding::Joined,
            1 => social::ParticipationStanding::Observer,
            _ => social::ParticipationStanding::Left,
        };
        social::set_participation(&mut db, &space, a, standing, "request:r6:participation")
            .await
            .unwrap();
    }
    let p1 = social::list_participations(&mut db, &space, None, 2, 262_144)
        .await
        .unwrap();
    let after_p = p1["nextAfterActorRef"].as_str().unwrap().to_string();
    let p2 = social::list_participations(&mut db, &space, Some(&after_p), 2, 262_144)
        .await
        .unwrap();
    assert_eq!(p1["participants"].as_array().unwrap().len(), 2);
    assert_eq!(p2["participants"].as_array().unwrap().len(), 1);
    assert_eq!(p2["hasMore"], false);

    // Two visible spaces and one left-only space share the same Subject:
    // membership filter excludes LEFT, which is not authorization.
    let common = "subject:host-rust-b:r6-list-space-common";
    for (i, standing) in [
        social::ParticipationStanding::Joined,
        social::ParticipationStanding::Observer,
        social::ParticipationStanding::Left,
    ]
    .into_iter()
    .enumerate()
    {
        let id = format!("space:r6:inventory-filter:{i:02}");
        social::create_space(
            &mut db,
            &social::CreateSpace {
                space_ref: id.clone(),
                purpose: format!("R6 Inventory 🧩 {i}"),
                actor_ref: actor.clone(),
                subject_refs: vec![common.into()],
                client_request_id: format!("request:r6:create-space:{i}"),
            },
        )
        .await
        .unwrap();
        social::set_participation(&mut db, &id, &actor, standing, "r6-membership")
            .await
            .unwrap();
    }
    let mut input = social::ListSpaces {
        actor_ref: Some(&actor),
        subject_ref: Some(common),
        limit: 1,
        before_created_at: None,
        before_space_ref: None,
        max_bytes: 262_144,
    };
    let sp1 = social::list_spaces(&mut db, &input).await.unwrap();
    assert_eq!(sp1["spaces"].as_array().unwrap().len(), 1);
    assert_eq!(sp1["hasMore"], true);
    let timestamp = sp1["nextCursor"]["beforeCreatedAt"]
        .as_str()
        .unwrap()
        .to_owned();
    let cursor_space = sp1["nextCursor"]["beforeSpaceRef"]
        .as_str()
        .unwrap()
        .to_owned();
    input.before_created_at = Some(&timestamp);
    input.before_space_ref = Some(&cursor_space);
    let sp2 = social::list_spaces(&mut db, &input).await.unwrap();
    assert_eq!(sp2["spaces"].as_array().unwrap().len(), 1);
    assert_eq!(sp2["hasMore"], false);
    assert!(sp2["nextCursor"].is_null());
    input.before_created_at = Some(&timestamp);
    input.before_space_ref = None;
    assert!(social::list_spaces(&mut db, &input).await.is_err());
    input.before_created_at = None;
    input.before_space_ref = None;
    input.limit = 201;
    assert!(social::list_spaces(&mut db, &input).await.is_err());
    input.limit = 50;
    input.max_bytes = 1024;
    assert!(social::list_spaces(&mut db, &input).await.is_err());
    assert!(
        social::list_space_subjects(&mut db, &space, None, 501, 262_144)
            .await
            .is_err()
    );
    assert!(
        social::list_participations(&mut db, &space, None, 0, 262_144)
            .await
            .is_err()
    );
    assert!(matches!(
        social::list_space_subjects(&mut db, "space:r6:missing", None, 10, 262_144).await,
        Err(social::SocialError::NotFound(_))
    ));
    assert!(matches!(
        social::list_participations(&mut db, "space:r6:missing", None, 10, 262_144).await,
        Err(social::SocialError::NotFound(_))
    ));
    let missing = social::ListSpaces {
        actor_ref: Some("actor:r6:missing"),
        subject_ref: None,
        limit: 10,
        before_created_at: None,
        before_space_ref: None,
        max_bytes: 262_144,
    };
    assert!(matches!(
        social::list_spaces(&mut db, &missing).await,
        Err(social::SocialError::NotFound(_))
    ));
    let python_script = r#"
import json,os
from ordivon_host_v2.social_store import SocialStore
assert os.environ["HOST_RUST_TEST_DSN"]==os.environ["ORDIVON_HOST_V2_DSN"]
s=SocialStore(os.environ["HOST_RUST_TEST_DSN"])
space=os.environ["R6_SPACE"]
actor=os.environ["R6_ACTOR"]
common=os.environ["R6_COMMON"]
a=s.list_space_subjects(space,limit=2)
b=s.list_space_subjects(space,after_subject_ref=a["nextAfterSubjectRef"],limit=2)
c=s.list_participations(space,limit=2)
d=s.list_participations(space,after_actor_ref=c["nextAfterActorRef"],limit=2)
e=s.list_spaces(actor_ref=actor,subject_ref=common,limit=1)
f=s.list_spaces(actor_ref=actor,subject_ref=common,limit=1,
    before_created_at=e["nextCursor"]["beforeCreatedAt"],
    before_space_ref=e["nextCursor"]["beforeSpaceRef"])
print(json.dumps({"s1":a,"s2":b,"p1":c,"p2":d,"sp1":e,"sp2":f},ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", python_script])
        .env("R6_SPACE", &space)
        .env("R6_ACTOR", &actor)
        .env("R6_COMMON", common)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Original Python SocialStore: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    let rust = json!({"s1":s1,"s2":s2,"p1":p1,"p2":p2,"sp1":sp1,"sp2":sp2});
    assert_eq!(
        rust, python,
        "Rust 3 inventories must equal original Python JSON"
    );
}

#[tokio::test]
#[ignore = "requires disposable PG18 schema13 and original Python exact byte-prefix oracle"]
async fn three_inventory_bounded_unicode_pages_exhaust_without_duplicate_or_skip() {
    let mut db = connect().await;
    let (actor, space, _) = seed(&db, "inventory-byte-r6").await;
    for i in 0..10 {
        let subject = format!("opaque:r6:{i:02}:{}", "汉".repeat(1800));
        db.execute(
            "INSERT INTO space_subjects(space_ref,subject_ref) VALUES($1,$2)",
            &[&space, &subject],
        )
        .await
        .unwrap();
    }
    for i in 0..45 {
        let id = format!("actor:r6:stress:{i:02}:{}", "x".repeat(472));
        db.execute(
            "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent')",
            &[&id],
        )
        .await
        .unwrap();
        social::set_participation(
            &mut db,
            &space,
            &id,
            social::ParticipationStanding::Joined,
            "desired-r6",
        )
        .await
        .unwrap();
    }
    let subject_common = "subject:host-rust-b:r6-byte-common";
    for i in 0..8 {
        let id = format!("space:host-rust-b:r6-byte:{i:02}");
        social::create_space(
            &mut db,
            &social::CreateSpace {
                space_ref: id.clone(),
                purpose: format!("Unicode Inventory r6 {i} {}", "研".repeat(930)),
                actor_ref: actor.clone(),
                subject_refs: vec![subject_common.into()],
                client_request_id: format!("request:r6:create-large:{i}"),
            },
        )
        .await
        .unwrap();
        social::set_participation(
            &mut db,
            &id,
            &actor,
            social::ParticipationStanding::Joined,
            "desired-r6",
        )
        .await
        .unwrap();
    }
    let byte_cap = 16_384usize;

    let mut subject_after: Option<String> = None;
    let mut subject_seen = std::collections::BTreeSet::new();
    let mut subject_pages = 0;
    let mut first_subjects = None;
    loop {
        let out =
            social::list_space_subjects(&mut db, &space, subject_after.as_deref(), 500, byte_cap)
                .await
                .unwrap();
        assert!(serde_json_canonicalizer::to_vec(&out).unwrap().len() <= byte_cap);
        if first_subjects.is_none() {
            assert_eq!(out["hasMore"], true, "must exercise real byte trimming");
            first_subjects = Some(out.clone());
        }
        for v in out["subjectRefs"].as_array().unwrap() {
            let next = v.as_str().unwrap().to_owned();
            if let Some(ref prev) = subject_after {
                assert!(&next > prev);
            }
            assert!(subject_seen.insert(next));
        }
        subject_after = out["nextAfterSubjectRef"].as_str().map(str::to_owned);
        subject_pages += 1;
        if !out["hasMore"].as_bool().unwrap() {
            break;
        }
        assert!(subject_pages < 20);
    }
    assert_eq!(subject_seen.len(), 10);
    assert!(subject_pages >= 2);

    let mut part_after: Option<String> = None;
    let mut part_seen = std::collections::BTreeSet::new();
    let mut part_pages = 0;
    let mut first_parts = None;
    loop {
        let out =
            social::list_participations(&mut db, &space, part_after.as_deref(), 500, byte_cap)
                .await
                .unwrap();
        assert!(serde_json_canonicalizer::to_vec(&out).unwrap().len() <= byte_cap);
        if first_parts.is_none() {
            assert_eq!(out["hasMore"], true, "participation fixture must trim");
            first_parts = Some(out.clone());
        }
        for v in out["participants"].as_array().unwrap() {
            let next = v["actorRef"].as_str().unwrap().to_owned();
            if let Some(ref prev) = part_after {
                assert!(&next > prev);
            }
            assert!(part_seen.insert(next));
        }
        part_after = out["nextAfterActorRef"].as_str().map(str::to_owned);
        part_pages += 1;
        if !out["hasMore"].as_bool().unwrap() {
            break;
        }
        assert!(part_pages < 20);
    }
    assert_eq!(part_seen.len(), 45);
    assert!(part_pages >= 2);

    let mut space_timestamp: Option<String> = None;
    let mut space_ref: Option<String> = None;
    let mut space_seen = std::collections::BTreeSet::new();
    let mut space_pages = 0;
    let mut first_spaces = None;
    loop {
        let input = social::ListSpaces {
            actor_ref: Some(&actor),
            subject_ref: Some(subject_common),
            limit: 200,
            before_created_at: space_timestamp.as_deref(),
            before_space_ref: space_ref.as_deref(),
            max_bytes: byte_cap,
        };
        let out = social::list_spaces(&mut db, &input).await.unwrap();
        assert!(serde_json_canonicalizer::to_vec(&out).unwrap().len() <= byte_cap);
        if first_spaces.is_none() {
            assert_eq!(out["hasMore"], true, "Space list must trim UTF8");
            first_spaces = Some(out.clone());
        }
        for v in out["spaces"].as_array().unwrap() {
            let next = v["spaceRef"].as_str().unwrap().to_owned();
            assert!(space_seen.insert(next));
        }
        space_timestamp = out["nextCursor"]["beforeCreatedAt"]
            .as_str()
            .map(str::to_owned);
        space_ref = out["nextCursor"]["beforeSpaceRef"]
            .as_str()
            .map(str::to_owned);
        space_pages += 1;
        if !out["hasMore"].as_bool().unwrap() {
            break;
        }
        assert!(space_pages < 20);
    }
    assert_eq!(space_seen.len(), 8);
    assert!(space_pages >= 2);

    let python_script = r#"
import json,os
from ordivon_host_v2.social_store import SocialStore
assert os.environ["HOST_RUST_TEST_DSN"]==os.environ["ORDIVON_HOST_V2_DSN"]
s=SocialStore(os.environ["HOST_RUST_TEST_DSN"])
space=os.environ["R6_LARGE_SPACE"]
actor=os.environ["R6_LARGE_ACTOR"]
common=os.environ["R6_LARGE_COMMON"]
subject=s.list_space_subjects(space,limit=500,max_bytes=16384)
part=s.list_participations(space,limit=500,max_bytes=16384)
spaces=s.list_spaces(actor_ref=actor,subject_ref=common,limit=200,max_bytes=16384)
print(json.dumps({"subject":subject,"part":part,"spaces":spaces},ensure_ascii=False))
"#;
    let output = std::process::Command::new("uv")
        .current_dir(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap(),
        )
        .args(["run", "--offline", "python", "-c", python_script])
        .env("R6_LARGE_SPACE", &space)
        .env("R6_LARGE_ACTOR", &actor)
        .env("R6_LARGE_COMMON", subject_common)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "Python exact byte cap oracle: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(
        python,
        json!({
            "subject":first_subjects.unwrap(),
            "part":first_parts.unwrap(),
            "spaces":first_spaces.unwrap(),
        }),
        "three inventories must trim identical canonical response prefixes"
    );
}
