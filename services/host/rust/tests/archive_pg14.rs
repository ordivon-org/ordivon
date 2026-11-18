//! HST07: schema14 logical archive is observable through normal Rust consumer
//! methods and must not weaken the two-step Topic lifecycle.
use ordivon_host_rust::{
    mcp::{TopicListRequest, TopicStateWire},
    pg::{HostPg, REQUIRED_SCHEMA},
    social::{self, MessageKind, PostMessage, TopicState},
};
use serde_json::json;
use tokio_postgres::NoTls;

#[test]
fn archive_mcp_tool_input_is_explicit_and_defaults_hidden() {
    let omitted: TopicListRequest =
        serde_json::from_value(json!({"spaceRef":"space:r46:archive"})).unwrap();
    assert!(!omitted.include_archived);
    let explicit: TopicListRequest =
        serde_json::from_value(json!({"spaceRef":"space:r46:archive","includeArchived":true}))
            .unwrap();
    assert!(explicit.include_archived);
    let state: TopicStateWire = serde_json::from_value(json!("archived")).unwrap();
    assert_eq!(format!("{state:?}"), "Archived");
}

#[tokio::test]
#[ignore = "requires disposable PG18 migrated from real Python Host schema0014"]
async fn archived_topic_hidden_by_default_but_readable_and_lifecycle_guarded() {
    let dsn = std::env::var("HOST_RUST_TEST_DSN").expect("disposable loopback PG required");
    assert!(
        dsn.contains("127.0.0.1") || dsn.contains("localhost"),
        "refuse non-loopback DSN"
    );
    let db_api = HostPg::try_new(dsn.clone()).unwrap();
    assert_eq!(REQUIRED_SCHEMA, 14);
    assert_eq!(db_api.check_schema().await.unwrap(), 14);
    let (mut db, connection) = tokio_postgres::connect(&dsn, NoTls).await.unwrap();
    tokio::spawn(async move {
        connection.await.unwrap();
    });

    let actor = "actor:host-rust-r46:archive";
    let space = "space:host-rust-r46:archive";
    let archived = "topic:host-rust-r46:archive-a";
    let active = "topic:host-rust-r46:archive-z";
    db.execute(
        "INSERT INTO actor_refs(actor_ref,actor_kind) VALUES($1,'agent')",
        &[&actor],
    )
    .await
    .unwrap();
    db.execute(
        "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES($1,'R46 archive',$2)",
        &[&space, &actor],
    )
    .await
    .unwrap();
    for topic in [archived, active] {
        db.execute(
            "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref)              VALUES($1,$2,'R46 archive oracle','open',$3)",
            &[&topic, &space, &actor],
        )
        .await
        .unwrap();
    }
    let posted = social::post_message(
        &mut db,
        &PostMessage {
            message_ref: "message:host-rust-r46:archive".into(),
            client_request_id: "request:host-rust-r46:archive:message".into(),
            space_ref: space.into(),
            topic_ref: archived.into(),
            author_actor_ref: actor.into(),
            message_kind: MessageKind::Finding,
            body: "durable before archive".into(),
            recorded_at_ms: 1_795_012_000_000,
        },
    )
    .await
    .unwrap();
    let high = posted["sequence"].as_i64().unwrap();

    // Python Schema14 requires open->closed->archived, with a matching
    // high watermark; forbidden transitions must not alter the state.
    assert!(social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Archived,
        TopicState::Open,
        high,
        "request:host-rust-r46:invalid-direct-archive"
    )
    .await
    .is_err());
    let current: String = db
        .query_one("SELECT state FROM topics WHERE topic_ref=$1", &[&archived])
        .await
        .unwrap()
        .get(0);
    assert_eq!(current, "open");

    let closed = social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Closed,
        TopicState::Open,
        high,
        "request:host-rust-r46:close",
    )
    .await
    .unwrap();
    assert_eq!(closed["state"], "closed");
    let archived_result = social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Archived,
        TopicState::Closed,
        high,
        "request:host-rust-r46:archive",
    )
    .await
    .unwrap();
    assert_eq!(archived_result["state"], "archived");

    let hidden = social::list_topics(&mut db, space, None, 10, 262_144)
        .await
        .unwrap();
    assert_eq!(hidden["topics"].as_array().unwrap().len(), 1);
    assert_eq!(hidden["topics"][0]["topicRef"], active);
    let explicit = social::list_topics_with_archive(&mut db, space, None, 10, 262_144, true)
        .await
        .unwrap();
    assert_eq!(explicit["topics"].as_array().unwrap().len(), 2);
    assert_eq!(explicit["topics"][0]["topicRef"], archived);
    assert_eq!(explicit["topics"][0]["state"], "archived");
    assert_eq!(explicit["topics"][1]["topicRef"], active);

    let page1 = social::list_topics_with_archive(&mut db, space, None, 1, 262_144, true)
        .await
        .unwrap();
    assert_eq!(page1["hasMore"], true);
    assert_eq!(page1["topics"][0]["topicRef"], archived);
    let after = page1["nextAfterTopicRef"].as_str().unwrap();
    let page2 = social::list_topics_with_archive(&mut db, space, Some(after), 1, 262_144, true)
        .await
        .unwrap();
    assert_eq!(page2["topics"][0]["topicRef"], active);
    assert_eq!(page2["hasMore"], false);

    // Explicit reference remains addressable even when default listing hides it.
    let resumed = social::resume_topic(&mut db, archived, 0, 10, 262_144)
        .await
        .unwrap();
    assert_eq!(resumed["messages"].as_array().unwrap().len(), 1);
    assert_eq!(resumed["messages"][0]["messageRef"], posted["messageRef"]);

    assert!(social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Open,
        TopicState::Archived,
        high,
        "request:host-rust-r46:invalid-direct-reopen"
    )
    .await
    .is_err());
    let still_archived: String = db
        .query_one("SELECT state FROM topics WHERE topic_ref=$1", &[&archived])
        .await
        .unwrap()
        .get(0);
    assert_eq!(still_archived, "archived");
    let restored = social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Closed,
        TopicState::Archived,
        high,
        "request:host-rust-r46:restore-closed",
    )
    .await
    .unwrap();
    assert_eq!(restored["state"], "closed");
    let default_after_restore = social::list_topics(&mut db, space, None, 10, 262_144)
        .await
        .unwrap();
    assert_eq!(default_after_restore["topics"].as_array().unwrap().len(), 2);
    let latest = social::set_topic_state(
        &mut db,
        archived,
        actor,
        TopicState::Open,
        TopicState::Closed,
        high,
        "request:host-rust-r46:reopen-after-restore",
    )
    .await
    .unwrap();
    assert_eq!(latest["state"], "open");
}
