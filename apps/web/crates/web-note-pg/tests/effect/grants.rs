use super::fixture::{NOW, create, request, setup};
use ordivon_web_note_pg::{
    PgNoteStore,
    effect::{EffectError, GrantCreate, GrantObservation, PreparedGrant},
};
use serde_json::{Value, json};
use uuid::Uuid;

fn input(id: &str) -> GrantCreate {
    GrantCreate {
        grant_id: id.into(),
        principal_id: "p".into(),
        agent_id: "new-agent".into(),
        audience: "web".into(),
        allowed_actions: vec!["canary.note.create".into()],
        resource_prefixes: vec!["/canary/notes".into()],
        expires_at_epoch_seconds: 200,
        max_risk_class: "R4".into(),
        step_up_at_or_above: "R4".into(),
        remaining_effects: 2,
    }
}
fn prepared(id: &str) -> PreparedGrant {
    PreparedGrant::new(input(id), Uuid::new_v4(), NOW).unwrap()
}
#[tokio::test]
async fn native_grant_digest_and_projection_differential() {
    let (store, peer) = setup("grant_digest").await;
    let out = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/grant-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let vectors: Vec<Value> = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(vectors.len(), 32);
    for v in vectors {
        let input: GrantCreate = serde_json::from_value(v["input"].clone()).unwrap();
        let op = PreparedGrant::new(input, Uuid::new_v4(), NOW).unwrap();
        assert_eq!(json!(op.snapshot()), v["snapshot"]);
        assert_eq!(
            op.snapshot().grant_digest,
            v["withoutQuota"].as_str().unwrap()
        );
        assert_eq!(
            store.observe_grant_issuance(&op).await.unwrap(),
            GrantObservation::Unobserved
        );
        let snap = store.issue_grant(&op).await.unwrap();
        assert_eq!(json!(snap), v["snapshot"]);
        let row=peer.query_one("SELECT allowed_actions_json,resource_prefixes_json FROM agent_grants WHERE grant_id=$1",&[&snap.grant_id]).await.unwrap();
        assert_eq!(
            row.get::<_, String>(0),
            v["row"]["allowed_actions_json"].as_str().unwrap()
        );
        assert_eq!(
            row.get::<_, String>(1),
            v["row"]["resource_prefixes_json"].as_str().unwrap()
        );
        assert_eq!(
            peer.query_one(
                "SELECT detail_json FROM audit_events WHERE event_id=$1",
                &[&op.audit_id()]
            )
            .await
            .unwrap()
            .get::<_, String>(0),
            v["audit"]["detail_json"].as_str().unwrap()
        );
        assert_eq!(store.get_grant(&snap.grant_id).await.unwrap(), snap);
        assert_eq!(
            store.observe_grant_issuance(&op).await.unwrap(),
            GrantObservation::Exact(Box::new(snap))
        );
    }
    assert_eq!(store.list_grants("p").await.unwrap().len(), 34);
    assert!(store.list_grants("q").await.unwrap().is_empty());
    println!(
        "32 real SQLite Grant digests, normalized UTF16 arrays, projections and original audit JSON bytes match"
    );
}
#[tokio::test]
async fn native_grant_selection_and_effect_consumer() {
    let (store, peer) = setup("grant_selection").await;
    let a = prepared("a");
    let snap = store.issue_grant(&a).await.unwrap();
    let mut b = input("b");
    b.remaining_effects = 0;
    let b = PreparedGrant::new(b, Uuid::new_v4(), NOW).unwrap();
    let b_snap = store.issue_grant(&b).await.unwrap();
    let resolve = || {
        store.resolve_grant(
            "new-agent",
            "web",
            "canary.note.create",
            "/canary/notes",
            NOW,
        )
    };
    assert!(matches!(resolve().await, Err(EffectError::GrantAmbiguous)));
    assert!(matches!(
        store
            .resolve_grant(
                "new-agent",
                "web",
                "canary.note.create",
                "/canary/notes-other",
                NOW
            )
            .await,
        Err(EffectError::GrantUnavailable)
    ));
    assert!(matches!(
        store
            .resolve_grant(
                "new-agent",
                "web",
                "canary.note.create",
                "/canary/notes/../secret",
                NOW
            )
            .await,
        Err(EffectError::GrantUnavailable)
    ));
    assert!(matches!(
        store
            .resolve_grant(
                "new-agent",
                "web",
                "canary.note.create",
                "/canary/notes",
                200
            )
            .await,
        Err(EffectError::GrantUnavailable)
    ));
    assert!(matches!(
        store.get_grant("absent").await,
        Err(EffectError::GrantNotFound)
    ));
    store
        .revoke_grant("p", "b", &b_snap.grant_digest, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    assert_eq!(resolve().await.unwrap(), snap);
    let id = Uuid::from_u128(500);
    let mut req = request("grant-consumer", false, id);
    req.agent_id = "new-agent".into();
    assert!(
        !store
            .commit_effect(
                &snap.fence(),
                &req,
                &create(id, "native grant"),
                Uuid::new_v4(),
                NOW
            )
            .await
            .unwrap()
            .replayed
    );
    let current = store.get_grant("a").await.unwrap();
    assert_eq!((current.remaining_effects, current.revision), (1, 2));
    assert_eq!(
        store.observe_grant_issuance(&a).await.unwrap(),
        GrantObservation::Exact(Box::new(current.clone()))
    );
    assert!(matches!(
        store
            .commit_effect(
                &snap.fence(),
                &{
                    let mut r = req.clone();
                    r.effect_id = "new".into();
                    r
                },
                &create(Uuid::from_u128(501), "stale"),
                Uuid::new_v4(),
                NOW
            )
            .await,
        Err(EffectError::GrantChanged)
    ));
    store
        .revoke_grant("p", "a", &current.grant_digest, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    let current = store.get_grant("a").await.unwrap();
    assert!(!current.active);
    assert_eq!(
        store.observe_grant_issuance(&a).await.unwrap(),
        GrantObservation::Exact(Box::new(current))
    );
    assert!(matches!(
        resolve().await,
        Err(EffectError::GrantUnavailable)
    ));
    // A corrupt candidate is rejected even when its action does not match.
    let c = prepared("c");
    store.issue_grant(&c).await.unwrap();
    peer.execute(
        "UPDATE agent_grants SET allowed_actions_json='[1]' WHERE grant_id='c'",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .resolve_grant("new-agent", "web", "other", "/canary/notes", NOW)
            .await,
        Err(EffectError::Corrupt)
    ));
    assert!(matches!(
        store.get_grant("c").await,
        Err(EffectError::Corrupt)
    ));
    assert!(matches!(
        store.list_grants("p").await,
        Err(EffectError::Corrupt)
    ));
    println!(
        "actual issuance -> ambiguous scope incl exhausted quota -> revoke -> Effect -> revision -> revoke; corrupt candidate fails closed"
    );
}
#[tokio::test]
async fn native_grant_issuance_faults_and_identity_race() {
    let (store, peer) = setup("grant_faults").await;
    let a = prepared("a");
    for (table, body) in [
        ("agent_grants", "RETURN NULL;"),
        ("agent_grants", "NEW.remaining_effects=99; RETURN NEW;"),
        ("audit_events", "NEW.detail_json='{}'; RETURN NEW;"),
        (
            "audit_events",
            "UPDATE agent_grants SET active=0 WHERE grant_id='a'; RETURN NEW;",
        ),
    ] {
        peer.batch_execute(&format!("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {body} END; $$; CREATE TRIGGER fault BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION fault()")).await.unwrap();
        assert!(matches!(
            store.issue_grant(&a).await,
            Err(EffectError::Write(_) | EffectError::Mismatch(_))
        ));
        assert_eq!(
            store.observe_grant_issuance(&a).await.unwrap(),
            GrantObservation::Unobserved
        );
        peer.batch_execute("DROP FUNCTION fault() CASCADE")
            .await
            .unwrap();
    }
    let b = prepared("a");
    let (x, y) = tokio::join!(store.issue_grant(&a), store.issue_grant(&b));
    assert_eq!(usize::from(x.is_ok()) + usize::from(y.is_ok()), 1);
    let (winner, loser) = if x.is_ok() { (&a, &b) } else { (&b, &a) };
    assert!(matches!(
        store.observe_grant_issuance(winner).await.unwrap(),
        GrantObservation::Exact(_)
    ));
    assert_eq!(
        store.observe_grant_issuance(loser).await.unwrap(),
        GrantObservation::Mismatch
    );
    assert_eq!(peer.query_one("SELECT count(*) FROM audit_events WHERE event_type='agent.grant.issued' AND object_id='a'",&[]).await.unwrap().get::<_,i64>(0),1);
    peer.execute("INSERT INTO audit_events SELECT 'duplicate',principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events WHERE event_id=$1",&[&winner.audit_id()]).await.unwrap();
    assert_eq!(
        store.observe_grant_issuance(winner).await.unwrap(),
        GrantObservation::Mismatch
    );
    let mut invalid = input("invalid");
    invalid.resource_prefixes = vec!["/a/../b".into()];
    assert!(matches!(
        PreparedGrant::new(invalid, Uuid::new_v4(), NOW),
        Err(EffectError::InvalidGrantScope)
    ));
    let mut invalid = input("invalid");
    invalid.remaining_effects = i64::MAX;
    assert!(matches!(
        PreparedGrant::new(invalid, Uuid::new_v4(), NOW),
        Err(EffectError::Invalid)
    ));
    println!(
        "four native trigger faults atomic; competing identical Grant ID one winner; duplicate evidence mismatch; invalid inputs refused"
    );
}
#[tokio::test]
async fn native_grant_issuance_ack_unknown() {
    let (store, peer) = setup("grant_ack").await;
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_GRANT_TEST_ACK_PROXY").unwrap());
    let proxy = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "grant_ack",
    )
    .unwrap();
    let op = prepared("a");
    let result = proxy.issue_grant(&op).await;
    assert!(
        matches!(result,Err(EffectError::AuthorityCommitUnknown{operation:"grant-issuance",ref coordinate,..}) if coordinate==op.audit_id()),
        "{result:?}"
    );
    assert_eq!(
        store.observe_grant_issuance(&op).await.unwrap(),
        GrantObservation::Exact(Box::new(op.snapshot()))
    );
    assert!(store.issue_grant(&op).await.is_err());
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM audit_events WHERE event_id=$1",
            &[&op.audit_id()]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        1
    );
    println!(
        "native Grant COMMIT acknowledgement lost; original prepared identity observed, no duplicate"
    );
}

#[tokio::test]
async fn native_revocation_ack_and_authority_observation() {
    use ordivon_web_note_pg::effect::{ApprovalWrite, EffectOperation, RevocationObservation};
    let (store, peer) = setup("grant_revoke_ack").await;
    let op = prepared("a");
    let issued = store.issue_grant(&op).await.unwrap();
    let g = issued.fence();
    let audit = Uuid::new_v4();
    assert_eq!(
        store
            .observe_grant_revocation(&g, audit, NOW)
            .await
            .unwrap(),
        RevocationObservation::Unobserved
    );
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_REVOKE_TEST_ACK_PROXY").unwrap());
    let proxy = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "grant_revoke_ack",
    )
    .unwrap();
    let result = proxy
        .revoke_grant("p", "a", &g.grant_digest, audit, NOW)
        .await;
    assert!(
        matches!(result,Err(EffectError::AuthorityCommitUnknown{operation:"grant-revocation",ref coordinate,..}) if coordinate==&audit.to_string()),
        "{result:?}"
    );
    let revoked = store.get_grant("a").await.unwrap();
    assert_eq!(
        store
            .observe_grant_revocation(&g, audit, NOW)
            .await
            .unwrap(),
        RevocationObservation::Exact(Box::new(revoked))
    );
    assert_eq!(
        store
            .observe_grant_revocation(&g, audit, NOW + 1)
            .await
            .unwrap(),
        RevocationObservation::Mismatch
    );
    let id = Uuid::from_u128(601);
    let e = request("E", false, id);
    store
        .commit_effect(
            &super::fixture::grant("g1", 1),
            &e,
            &create(id, "authority observation"),
            Uuid::new_v4(),
            NOW,
        )
        .await
        .unwrap();
    let p = request("P", true, id);
    let publish = EffectOperation::Publish {
        note_id: id.to_string(),
    };
    // Original synthetic fixture has P approval. Remove it to test absence.
    peer.execute("DELETE FROM effect_approvals WHERE effect_id='P'", &[])
        .await
        .unwrap();
    let before = store.observe_authority("p", &p).await.unwrap();
    assert!(before.pending.is_none() && before.approval.is_none() && before.receipt.is_none());
    store
        .register_pending_approval(&super::fixture::grant("g1", 2), &p, &publish, NOW, 150)
        .await
        .unwrap();
    let approval = ApprovalWrite {
        effect_id: p.effect_id.clone(),
        effect_digest: p.effect_digest.clone(),
        principal_id: "p".into(),
        credential_id: "credential".into(),
        verified_at: NOW,
        expires_at: 140,
    };
    store.put_verified_approval(&approval).await.unwrap();
    let current = store.observe_authority("p", &p).await.unwrap();
    assert_eq!(current.pending.unwrap().expires_at, 150);
    assert_eq!(current.approval.unwrap().consumed_at, None);
    assert!(current.receipt.is_none());
    assert!(matches!(
        store.observe_authority("q", &p).await,
        Err(EffectError::ApprovalBinding)
    ));
    let committed = store
        .commit_effect(
            &super::fixture::grant("g1", 2),
            &p,
            &publish,
            Uuid::new_v4(),
            NOW + 1,
        )
        .await
        .unwrap();
    let terminal = store.observe_authority("p", &p).await.unwrap();
    assert_eq!(terminal.approval.unwrap().consumed_at, Some(NOW + 1));
    assert_eq!(terminal.receipt, Some(committed.receipt));
    println!(
        "real revoke ACK loss observed exact audit and inactive Grant; coherent pending/approval/receipt current facts and cross-principal rejection"
    );
}

#[tokio::test]
async fn native_authority_snapshot_under_forced_commit() {
    let (store, mut peer) = setup("grant_observe_snapshot").await;
    let p = request("P", true, Uuid::from_u128(602));
    peer.execute(
        "INSERT INTO pending_effect_approvals VALUES('P','digest-P','p',150,90)",
        &[],
    )
    .await
    .unwrap();
    let before = store.observe_authority("p", &p).await.unwrap();
    assert_eq!(before.pending.as_ref().unwrap().expires_at, 150);
    assert_eq!(before.approval.as_ref().unwrap().verified_at, 90);
    // Native AccessExclusive lock blocks only the second observation query.
    // Its first query has already established the snapshot.
    let tx = peer.transaction().await.unwrap();
    tx.batch_execute("LOCK TABLE effect_approvals IN ACCESS EXCLUSIVE MODE")
        .await
        .unwrap();
    let reader = tokio::spawn({
        let store = store.clone();
        let p = p.clone();
        async move { store.observe_authority("p", &p).await }
    });
    let deadline = tokio::time::Instant::now() + std::time::Duration::from_secs(5);
    loop {
        tx.query_one("SELECT pg_stat_clear_snapshot()", &[])
            .await
            .unwrap();
        let waiting:bool=tx.query_one("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() AND wait_event_type='Lock' AND query LIKE 'SELECT * FROM effect_approvals WHERE effect_id=%')",&[]).await.unwrap().get(0);
        if waiting {
            break;
        }
        assert!(
            tokio::time::Instant::now() < deadline,
            "native second read did not reach lock"
        );
        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
    }
    tx.batch_execute("UPDATE pending_effect_approvals SET expires_at=160 WHERE effect_id='P'; UPDATE effect_approvals SET verified_at=91,expires_at=201 WHERE effect_id='P'").await.unwrap();
    tx.commit().await.unwrap();
    let observed = tokio::time::timeout(std::time::Duration::from_secs(5), reader)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    assert_eq!(observed, before, "mixed snapshot across peer commit");
    let after = store.observe_authority("p", &p).await.unwrap();
    assert_eq!(after.pending.unwrap().expires_at, 160);
    assert_eq!(after.approval.unwrap().verified_at, 91);
    println!(
        "native observation second read lock witnessed; peer atomic commit; old complete snapshot then new complete snapshot"
    );
}
