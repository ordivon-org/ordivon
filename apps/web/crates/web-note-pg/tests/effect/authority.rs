use super::fixture::{NOW, create, grant, request, setup};
use ordivon_web_note_pg::{
    effect::{EffectError, EffectOperation, EffectRequest},
    migration::Snapshot,
};
use tokio_postgres::Client;
use uuid::Uuid;
fn approval_write(effect: &EffectRequest, now: i64) -> ordivon_web_note_pg::effect::ApprovalWrite {
    ordivon_web_note_pg::effect::ApprovalWrite {
        effect_id: effect.effect_id.clone(),
        effect_digest: effect.effect_digest.clone(),
        principal_id: "p".into(),
        credential_id: "credential".into(),
        verified_at: now,
        expires_at: now + 40,
    }
}
#[tokio::test]
async fn native_authority_writer_lifecycle_and_terminal_replay() {
    use ordivon_web_note_pg::effect::PendingOutcome;
    let (store, mut peer) = setup("effect_authority_lifecycle").await;
    let id = Uuid::from_u128(9);
    let e = request("E", false, id);
    let op = create(id, "lifecycle");
    store
        .commit_effect(&grant("g1", 1), &e, &op, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    let p = request("P", true, id);
    let publish = EffectOperation::Publish {
        note_id: id.to_string(),
    };
    let input = approval_write(&p, NOW);
    assert!(matches!(
        store.put_verified_approval(&input).await,
        Err(EffectError::PendingNotFound)
    ));
    assert!(matches!(
        store
            .register_pending_approval(&grant("g1", 1), &p, &publish, NOW, 140)
            .await,
        Err(EffectError::GrantChanged)
    ));
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT pg_advisory_xact_lock(hashtextextended('web-r1:'||$1,0))",
        &[&p.effect_id],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .register_pending_approval(&grant("g1", 2), &p, &publish, NOW, 140)
            .await,
        Err(EffectError::Busy)
    ));
    assert!(matches!(
        store.put_verified_approval(&input).await,
        Err(EffectError::Busy)
    ));
    tx.rollback().await.unwrap();
    let first = store
        .register_pending_approval(&grant("g1", 2), &p, &publish, NOW, 140)
        .await
        .unwrap();
    assert!(
        matches!(first,PendingOutcome::Registered(ref x) if x.created_at==NOW&&x.expires_at==140)
    );
    let mut wrong = p.clone();
    wrong.effect_digest = "other".into();
    assert!(matches!(
        store
            .register_pending_approval(&grant("g1", 2), &wrong, &publish, NOW, 145)
            .await,
        Err(EffectError::PendingConflict)
    ));
    let renewed = store
        .register_pending_approval(&grant("g1", 2), &p, &publish, NOW + 1, 150)
        .await
        .unwrap();
    assert!(
        matches!(renewed,PendingOutcome::Registered(ref x) if x.created_at==NOW&&x.expires_at==150)
    );
    let wrong = approval_write(&wrong, NOW);
    assert!(matches!(
        store.put_verified_approval(&wrong).await,
        Err(EffectError::ApprovalBinding)
    ));
    let expired = approval_write(&p, 150);
    assert!(matches!(
        store.put_verified_approval(&expired).await,
        Err(EffectError::PendingNotFound)
    ));
    peer.batch_execute("INSERT INTO webauthn_credentials VALUES('foreign-credential','q',decode('00','hex'),0,'[]','singleDevice',0,1,1,NULL)").await.unwrap();
    let mut foreign = input.clone();
    foreign.credential_id = "foreign-credential".into();
    assert!(matches!(
        store.put_verified_approval(&foreign).await,
        Err(EffectError::ApprovalBinding)
    ));
    store.put_verified_approval(&input).await.unwrap();
    let refresh = approval_write(&p, NOW + 2);
    store.put_verified_approval(&refresh).await.unwrap();
    let row = peer
        .query_one(
            "SELECT verified_at,expires_at,consumed_at FROM effect_approvals WHERE effect_id='P'",
            &[],
        )
        .await
        .unwrap();
    assert_eq!(
        (
            row.get::<_, i64>(0),
            row.get::<_, i64>(1),
            row.get::<_, Option<i64>>(2)
        ),
        (102, 142, None)
    );
    let audit = Uuid::new_v4();
    assert!(matches!(
        store.revoke_grant("q", "g2", "digest-g2", audit, NOW).await,
        Err(EffectError::GrantPrincipalMismatch)
    ));
    assert!(matches!(
        store.revoke_grant("p", "g2", "wrong", audit, NOW).await,
        Err(EffectError::GrantChanged)
    ));
    let revoke = store
        .revoke_grant("p", "g2", "digest-g2", audit, NOW)
        .await
        .unwrap();
    assert_eq!(revoke.revision, 2);
    // Explicit repeated operation with the same audit identity cannot commit twice.
    assert!(
        matches!(store.revoke_grant("p","g2","digest-g2",audit,NOW).await,Err(EffectError::Database{ref source,..}) if source.code().is_some_and(|c|c.code()=="23505"))
    );
    assert_eq!(
        peer.query_one("SELECT revision FROM agent_grants WHERE grant_id='g2'", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        2
    );
    assert_eq!(
        peer.query_one(
            "SELECT detail_json FROM audit_events WHERE event_id=$1",
            &[&audit.to_string()]
        )
        .await
        .unwrap()
        .get::<_, String>(0),
        r#"{"agentId":"agent"}"#
    );
    assert!(matches!(
        store
            .register_pending_approval(&grant("g2", 2), &p, &publish, NOW + 3, 150)
            .await,
        Err(EffectError::GrantChanged)
    ));
    let committed = store
        .commit_effect(&grant("g1", 2), &p, &publish, Uuid::new_v4(), NOW + 3)
        .await
        .unwrap();
    assert!(matches!(
        store.put_verified_approval(&refresh).await,
        Err(EffectError::ApprovalClosed)
    ));
    let outcome = store
        .register_pending_approval(&grant("g2", 1), &p, &publish, NOW + 4, 160)
        .await
        .unwrap();
    assert!(matches!(outcome,PendingOutcome::AlreadyCommitted(ref r) if *r==committed.receipt));
    let row = peer
        .query_one(
            "SELECT consumed_at FROM effect_approvals WHERE effect_id='P'",
            &[],
        )
        .await
        .unwrap();
    assert_eq!(row.get::<_, Option<i64>>(0), Some(103));
    assert_eq!(
        peer.query_one(
            "SELECT expires_at FROM pending_effect_approvals WHERE effect_id='P'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        150
    );
    println!(
        "pending/verified approval/revocation actual writers: stale/mismatched/expired/foreign bindings rejected, refresh preserves identity, no terminal reopening"
    );
}

async fn exact_snapshot(peer: &mut Client) -> Snapshot {
    let tx = peer
        .build_transaction()
        .isolation_level(tokio_postgres::IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .await
        .unwrap();
    let snapshot = ordivon_web_note_pg::migration::read_snapshot(&tx)
        .await
        .unwrap();
    tx.rollback().await.unwrap();
    snapshot
}
#[tokio::test]
async fn native_authority_writer_faults_and_races() {
    use ordivon_web_note_pg::effect::PendingOutcome;
    let (store, mut peer) = setup("effect_authority_races").await;
    let id = Uuid::from_u128(10);
    let e = request("E", false, id);
    let op = create(id, "race");
    store
        .commit_effect(&grant("g1", 1), &e, &op, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    let p = request("P", true, id);
    let publish = EffectOperation::Publish {
        note_id: id.to_string(),
    };
    let before = exact_snapshot(&mut peer).await;
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN UPDATE agent_grants SET remaining_effects=0 WHERE grant_id='g1'; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE INSERT ON pending_effect_approvals FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store
            .register_pending_approval(&grant("g1", 2), &p, &publish, NOW, 160)
            .await,
        Err(EffectError::Mismatch("pending grant"))
    ));
    assert_eq!(exact_snapshot(&mut peer).await, before);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    store
        .register_pending_approval(&grant("g1", 2), &p, &publish, NOW, 160)
        .await
        .unwrap();
    let before = exact_snapshot(&mut peer).await;
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.effect_digest='mutated'; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE UPDATE ON effect_approvals FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.put_verified_approval(&approval_write(&p, NOW)).await,
        Err(EffectError::Mismatch("approval"))
    ));
    assert_eq!(exact_snapshot(&mut peer).await, before);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$; CREATE TRIGGER fault BEFORE INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store
            .revoke_grant("p", "g2", "digest-g2", Uuid::new_v4(), NOW)
            .await,
        Err(EffectError::Write("revocation audit"))
    ));
    assert_eq!(exact_snapshot(&mut peer).await, before);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    // Race actual refresh vs publish. If refresh wins, publication may
    // conservatively report BUSY; explicit new call rechecks current state.
    let g = grant("g1", 2);
    let refresh = approval_write(&p, NOW + 1);
    let (a, b) = tokio::join!(
        store.put_verified_approval(&refresh),
        store.commit_effect(&g, &p, &publish, Uuid::new_v4(), NOW + 2)
    );
    assert!(
        a.is_ok() || matches!(a, Err(EffectError::Busy | EffectError::ApprovalClosed)),
        "{a:?}"
    );
    let receipt = match b {
        Ok(o) => o.receipt,
        Err(EffectError::Busy) => {
            store
                .commit_effect(&g, &p, &publish, Uuid::new_v4(), NOW + 2)
                .await
                .unwrap()
                .receipt
        }
        other => panic!("unexpected publish race {other:?}"),
    };
    assert!(matches!(
        store.put_verified_approval(&refresh).await,
        Err(EffectError::ApprovalClosed)
    ));
    assert_eq!(store.observe_effect(&p).await.unwrap(), Some(receipt));
    assert_eq!(
        peer.query_one(
            "SELECT consumed_at FROM effect_approvals WHERE effect_id='P'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, Option<i64>>(0),
        Some(102)
    );
    // Race actual revocation vs distinct new Effect using same Grant.
    let r = request("G", false, Uuid::from_u128(11));
    let op = create(Uuid::from_u128(11), "grant race");
    let g = grant("g2", 1);
    let audit = Uuid::new_v4();
    let (a, b) = tokio::join!(
        store.revoke_grant("p", "g2", "digest-g2", audit, NOW + 3),
        store.commit_effect(&g, &r, &op, Uuid::new_v4(), NOW + 3)
    );
    match a {
        Ok(_) => {}
        Err(EffectError::Busy) => {
            store
                .revoke_grant("p", "g2", "digest-g2", audit, NOW + 3)
                .await
                .unwrap();
        }
        other => panic!("unexpected revoke race {other:?}"),
    }
    assert!(
        b.is_ok() || matches!(b, Err(EffectError::Busy | EffectError::GrantChanged)),
        "{b:?}"
    );
    assert_eq!(
        peer.query_one("SELECT active FROM agent_grants WHERE grant_id='g2'", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let new = request("H", false, id);
    assert!(matches!(
        store
            .commit_effect(
                &grant("g2", 2),
                &new,
                &create(Uuid::from_u128(12), "denied"),
                Uuid::new_v4(),
                NOW + 4
            )
            .await,
        Err(EffectError::GrantChanged)
    ));
    let closed = store
        .register_pending_approval(&grant("g2", 1), &p, &publish, NOW + 4, 160)
        .await
        .unwrap();
    assert!(matches!(closed, PendingOutcome::AlreadyCommitted(_)));
    println!(
        "3 native authority writer faults rollback all 11-table facts; real refresh/publish and revoke/commit races preserve terminal state"
    );
}
