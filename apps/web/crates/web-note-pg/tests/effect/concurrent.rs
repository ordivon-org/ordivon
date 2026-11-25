use super::fixture::{NOW, create, grant, request, setup};
use ordivon_web_note_pg::effect::{EffectError, EffectOperation};
use uuid::Uuid;
#[tokio::test]
async fn native_effect_grant_and_approval_contention() {
    let (store, mut peer) = setup("effect_locks").await;
    let id = Uuid::from_u128(3);
    let e = request("E", false, id);
    let op = create(id, "locked");
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT pg_advisory_xact_lock(hashtextextended('web-r1:'||$1,0))",
        &[&e.effect_id],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .commit_effect(&grant("g2", 1), &e, &op, Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Busy)
    ));
    assert!(store.observe_effect(&e).await.unwrap().is_none());
    let other = request("F", false, id);
    assert!(
        !store
            .commit_effect(
                &grant("g1", 1),
                &other,
                &create(Uuid::from_u128(4), "independent"),
                Uuid::new_v4(),
                NOW
            )
            .await
            .unwrap()
            .replayed
    );
    tx.rollback().await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT * FROM agent_grants WHERE grant_id='g2' FOR UPDATE",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .commit_effect(&grant("g2", 1), &e, &op, Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Busy)
    ));
    tx.rollback().await.unwrap();
    let first = store
        .commit_effect(&grant("g2", 1), &e, &op, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    let replay = store
        .commit_effect(&grant("g1", 1), &e, &op, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    assert!(replay.replayed);
    assert_eq!(first.receipt, replay.receipt);
    let p = request("P", true, id);
    let publish = EffectOperation::Publish {
        note_id: id.to_string(),
    };
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT * FROM effect_approvals WHERE effect_id='P' FOR UPDATE",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .commit_effect(&grant("g2", 2), &p, &publish, Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Busy)
    ));
    tx.rollback().await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT * FROM canary_notes WHERE note_id=$1 FOR UPDATE",
        &[&id.to_string()],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .commit_effect(&grant("g2", 2), &p, &publish, Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Busy)
    ));
    tx.rollback().await.unwrap();
    assert!(
        !store
            .commit_effect(&grant("g2", 2), &p, &publish, Uuid::new_v4(), NOW)
            .await
            .unwrap()
            .replayed
    );
    assert_eq!(
        peer.query_one(
            "SELECT consumed_at FROM effect_approvals WHERE effect_id='P'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, Option<i64>>(0),
        Some(NOW)
    );
    assert_eq!(
        peer.query_one("SELECT count(*) FROM agent_effects", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        3
    );
    println!(
        "actual identity, grant, approval and note locks: typed BUSY; disjoint progress; exact replay and one approval consumption"
    );
}
#[tokio::test]
async fn native_effect_two_writer_histories() {
    let (store, peer) = setup("effect_two_writer").await;
    let note = Uuid::from_u128(7);
    for wave in 0..16 {
        for same_identity in [true, false] {
            peer.batch_execute("TRUNCATE agent_effects,canary_notes,audit_events; UPDATE agent_grants SET remaining_effects=3,revision=1,active=1; UPDATE effect_approvals SET consumed_at=NULL").await.unwrap();
            let r1 = request("E", false, note);
            let r2 = request(if same_identity { "E" } else { "F" }, false, note);
            let g1 = grant("g1", 1);
            let g2 = grant(if same_identity { "g2" } else { "g1" }, 1);
            let op1 = create(note, "left");
            // Same identity refers to exactly the same admitted content.
            let op2 = if same_identity {
                create(note, "left")
            } else {
                create(Uuid::from_u128(8), "right")
            };
            let a = store.commit_effect(&g1, &r1, &op1, Uuid::new_v4(), NOW);
            let b = store.commit_effect(&g2, &r2, &op2, Uuid::new_v4(), NOW);
            let (a, b) = if wave % 2 == 0 {
                tokio::join!(a, b)
            } else {
                let (b, a) = tokio::join!(b, a);
                (a, b)
            };
            let mut winners = 0;
            for outcome in [&a, &b] {
                match outcome {
                    Ok(o) if !o.replayed => winners += 1,
                    Ok(o) => {
                        assert!(same_identity && o.replayed);
                    }
                    Err(EffectError::Busy) => {}
                    Err(EffectError::GrantChanged) if !same_identity => {}
                    other => panic!("unexpected concurrent outcome: {other:?}"),
                }
            }
            assert_eq!(winners, 1, "wave {wave}");
            let winner = if let Ok(o) = &a {
                if !o.replayed { o } else { b.as_ref().unwrap() }
            } else {
                b.as_ref().unwrap()
            };
            let observed = peer
                .query_one("SELECT count(*),min(effect_id) FROM agent_effects", &[])
                .await
                .unwrap();
            assert_eq!(observed.get::<_, i64>(0), 1);
            assert_eq!(observed.get::<_, String>(1), winner.receipt.effect_id);
            assert_eq!(
                peer.query_one(
                    "SELECT sum(remaining_effects)::bigint FROM agent_grants",
                    &[]
                )
                .await
                .unwrap()
                .get::<_, i64>(0),
                5
            );
            assert_eq!(peer.query_one("SELECT (SELECT count(*) FROM canary_notes),(SELECT count(*) FROM audit_events)",&[]).await.unwrap().get::<_,i64>(0),1);
            assert_eq!(
                peer.query_one("SELECT count(*) FROM audit_events", &[])
                    .await
                    .unwrap()
                    .get::<_, i64>(0),
                1
            );
        }
    }
    println!(
        "32 two-writer histories / 64 actual calls: same identity across grants and disjoint identity shared Grant, exactly one new receipt/quota decrement"
    );
}
