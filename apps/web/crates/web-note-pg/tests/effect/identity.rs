use super::fixture::{NOW, setup};
use ordivon_web_note_pg::{
    PgNoteStore,
    effect::EffectError,
    identity::{Credential, PreparedSession, Principal, SessionCreationObservation},
};
use serde_json::{Value, json};
use uuid::Uuid;

fn principal() -> Principal {
    Principal {
        principal_id: "new-p".into(),
        user_name: "new-user".into(),
        display_name: "新用户 🦀".into(),
    }
}
fn credential() -> Credential {
    Credential {
        credential_id: "new-c".into(),
        principal_id: "new-p".into(),
        public_key: vec![0, 255, 128, 1],
        counter: 1,
        transports: vec!["internal".into(), "hybrid".into()],
        device_type: "multiDevice".into(),
        backed_up: true,
        created_at: NOW,
        last_used_at: NOW,
        revoked_at: None,
    }
}
fn normalize(s: &ordivon_web_note_pg::identity::SessionView) -> Value {
    let mut v = json!(s);
    v["sessionId"] = json!("normalized");
    v
}

#[tokio::test]
async fn native_identity_session_sqlite_differential() {
    let (store, peer) = setup("identity_diff").await;
    let output = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/identity-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let reference: Value = serde_json::from_slice(&output.stdout).unwrap();
    let p = principal();
    assert_eq!(
        json!(
            store
                .ensure_principal(&p, Uuid::new_v4(), NOW)
                .await
                .unwrap()
        ),
        reference["principal"]
    );
    assert_eq!(
        store
            .ensure_principal(&p, Uuid::new_v4(), 101)
            .await
            .unwrap(),
        p
    );
    assert_eq!(store.find_principal("new-user").await.unwrap(), p);
    let c = credential();
    store.register_credential(&c, Uuid::new_v4()).await.unwrap();
    let initial = store.get_active_credential("new-c").await.unwrap();
    assert_eq!(json!(initial), reference["initial"]);
    let advanced = store.advance_credential(&initial, 2, 101).await.unwrap();
    assert_eq!(json!(advanced), reference["advanced"]);
    assert_eq!(
        store.list_credentials("new-p").await.unwrap(),
        vec![advanced]
    );
    let prepared = PreparedSession::new("new-p", NOW, 20, 50, Some("browser".into())).unwrap();
    assert_eq!(
        store.observe_session_creation(&prepared).await.unwrap(),
        SessionCreationObservation::Unobserved
    );
    let created = store.issue_session(&prepared).await.unwrap();
    assert_eq!(normalize(&created), reference["created"]);
    let auth = store
        .authenticate_session(prepared.token(), 110, 50)
        .await
        .unwrap();
    assert_eq!(auth.principal, p);
    assert_eq!(normalize(&auth.session), reference["before"]);
    // Independent Node crypto hash of the newly generated actual token. Secret
    // is sent to local process stdin, not command line, stdout or artifact.
    use std::io::Write;
    let mut node=std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap()).args(["-e","const c=require('node:crypto');const fs=require('node:fs');const t=fs.readFileSync(0);process.stdout.write(c.createHash('sha256').update(t).digest('hex'))"]).stdin(std::process::Stdio::piped()).stdout(std::process::Stdio::piped()).spawn().unwrap();
    node.stdin
        .take()
        .unwrap()
        .write_all(prepared.token().as_bytes())
        .unwrap();
    let hash = node.wait_with_output().unwrap();
    assert!(hash.status.success());
    assert_eq!(auth.token_hash, String::from_utf8(hash.stdout).unwrap());
    assert!(reference["hashExact"].as_bool().unwrap());
    assert_eq!(
        json!(
            store
                .revoke_session("new-p", prepared.session_id(), Uuid::new_v4(), 111)
                .await
                .unwrap()
        ),
        reference["revoked"]
    );
    assert_eq!(
        json!(
            store
                .revoke_session("new-p", prepared.session_id(), Uuid::new_v4(), 112)
                .await
                .unwrap()
        ),
        reference["repeated"]
    );
    assert_eq!(
        json!(
            store
                .revoke_all_sessions("new-p", Uuid::new_v4(), 113)
                .await
                .unwrap()
        ),
        reference["bulk"]
    );
    let final_sessions = store.list_sessions("new-p").await.unwrap();
    assert_eq!(
        json!(final_sessions.iter().map(normalize).collect::<Vec<_>>()),
        reference["final"]
    );
    let audits=peer.query("SELECT event_type,detail_json,created_at FROM audit_events WHERE principal_id='new-p' ORDER BY created_at,event_type",&[]).await.unwrap().iter().map(|r|json!([r.get::<_,String>(0),r.get::<_,String>(1),r.get::<_,i64>(2)])).collect::<Vec<_>>();
    let mut expected = reference["audits"].as_array().unwrap().clone();
    expected.sort_by(|a, b| {
        a[2].as_i64()
            .cmp(&b[2].as_i64())
            .then(a[0].as_str().cmp(&b[0].as_str()))
    });
    assert_eq!(audits, expected);
    assert_eq!(
        store.observe_session_creation(&prepared).await.unwrap(),
        SessionCreationObservation::Exact(Box::new(final_sessions[0].clone()))
    );
    assert!(matches!(
        store.authenticate_session(prepared.token(), 114, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    println!(
        "actual old SQLite Principal/Credential/Session lifecycle, raw key bytes, independent token hash, projections/audit bytes match"
    );
}

#[tokio::test]
async fn native_identity_concurrent_assertions_and_session_fences() {
    let (store, mut peer) = setup("identity_races").await;
    let p = principal();
    let a = Uuid::new_v4();
    let b = Uuid::new_v4();
    let (x, y) = tokio::join!(
        store.ensure_principal(&p, a, NOW),
        store.ensure_principal(&p, b, NOW)
    );
    assert_eq!(x.unwrap(), p);
    assert_eq!(y.unwrap(), p);
    assert_eq!(peer.query_one("SELECT count(*) FROM audit_events WHERE event_type='principal.created' AND object_id='new-p'",&[]).await.unwrap().get::<_,i64>(0),1);
    // Both PK and independent username unique indexes can arbitrate the
    // native race. Repeat against fresh coordinates, not the same cached row.
    for i in 0..24 {
        let same = Principal {
            principal_id: format!("same-{i}"),
            user_name: format!("same-user-{i}"),
            display_name: "same".into(),
        };
        let (x, y) = tokio::join!(
            store.ensure_principal(&same, Uuid::new_v4(), NOW),
            store.ensure_principal(&same, Uuid::new_v4(), NOW)
        );
        assert_eq!(x.unwrap(), same);
        assert_eq!(y.unwrap(), same);
        assert_eq!(peer.query_one("SELECT count(*) FROM audit_events WHERE event_type='principal.created' AND object_id=$1",&[&same.principal_id]).await.unwrap().get::<_,i64>(0),1);
        let left = Principal {
            principal_id: format!("left-{i}"),
            user_name: format!("shared-user-{i}"),
            display_name: "left".into(),
        };
        let right = Principal {
            principal_id: format!("right-{i}"),
            user_name: left.user_name.clone(),
            display_name: "right".into(),
        };
        let (x, y) = tokio::join!(
            store.ensure_principal(&left, Uuid::new_v4(), NOW),
            store.ensure_principal(&right, Uuid::new_v4(), NOW)
        );
        assert_eq!(usize::from(x.is_ok()) + usize::from(y.is_ok()), 1);
        assert!(
            matches!(x, Err(EffectError::PrincipalConflict))
                || matches!(y, Err(EffectError::PrincipalConflict))
        );
    }
    let mut wrong = p.clone();
    wrong.display_name = "different".into();
    assert!(matches!(
        store.ensure_principal(&wrong, Uuid::new_v4(), NOW).await,
        Err(EffectError::PrincipalConflict)
    ));
    let c = credential();
    store.register_credential(&c, Uuid::new_v4()).await.unwrap();
    let (x, y) = tokio::join!(
        store.advance_credential(&c, 2, 101),
        store.advance_credential(&c, 3, 101)
    );
    assert_eq!(usize::from(x.is_ok()) + usize::from(y.is_ok()), 1);
    for result in [&x, &y] {
        assert!(
            result.is_ok()
                || matches!(
                    result,
                    Err(EffectError::Busy | EffectError::CredentialConflict)
                )
        )
    }
    let current = store.get_active_credential("new-c").await.unwrap();
    assert!(matches!(
        store.advance_credential(&c, 4, 102).await,
        Err(EffectError::CredentialConflict)
    ));
    assert!(matches!(
        store.advance_credential(&current, 5, 99).await,
        Err(EffectError::CredentialConflict)
    ));
    let s = PreparedSession::new("new-p", 100, 20, 50, None).unwrap();
    store.issue_session(&s).await.unwrap();
    let foreign = PreparedSession::new("q", 100, 20, 50, None).unwrap();
    store.issue_session(&foreign).await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT * FROM principals WHERE principal_id='new-p' FOR NO KEY UPDATE",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store.authenticate_session(s.token(), 101, 20).await,
        Err(EffectError::Busy)
    ));
    assert!(matches!(
        store
            .revoke_session("new-p", s.session_id(), Uuid::new_v4(), 101)
            .await,
        Err(EffectError::Busy)
    ));
    let other = PreparedSession::new("new-p", 100, 20, 50, None).unwrap();
    assert!(matches!(
        store.issue_session(&other).await,
        Err(EffectError::Busy)
    ));
    assert!(
        store
            .authenticate_session(foreign.token(), 101, 20)
            .await
            .is_ok()
    );
    tx.rollback().await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query_one(
        "SELECT * FROM principals WHERE principal_id='new-p' FOR SHARE",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .revoke_all_sessions("new-p", Uuid::new_v4(), 102)
            .await,
        Err(EffectError::Busy)
    ));
    tx.rollback().await.unwrap();
    assert!(
        !store
            .revoke_session("q", s.session_id(), Uuid::new_v4(), 102)
            .await
            .unwrap()
    );
    store.issue_session(&other).await.unwrap();
    assert_eq!(
        store
            .revoke_all_sessions("new-p", Uuid::new_v4(), 103)
            .await
            .unwrap(),
        2
    );
    assert!(matches!(
        store.authenticate_session(s.token(), 104, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    assert!(matches!(
        store.authenticate_session(other.token(), 104, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    assert!(
        store
            .authenticate_session(foreign.token(), 104, 20)
            .await
            .is_ok()
    );
    println!(
        "actual competing principal creation (48 fresh two-call histories across both unique constraints)/counter updates; native principal SHARE/NO KEY UPDATE fences, bulk revoke and foreign independence"
    );
}

#[tokio::test]
async fn native_identity_session_faults_expiry_and_ack() {
    let (store, peer) = setup("identity_faults").await;
    let p = principal();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.detail_json='[]'; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.ensure_principal(&p, Uuid::new_v4(), NOW).await,
        Err(EffectError::Mismatch("identity audit"))
    ));
    assert!(matches!(
        store.get_principal("new-p").await,
        Err(EffectError::PrincipalNotFound)
    ));
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    store
        .ensure_principal(&p, Uuid::new_v4(), NOW)
        .await
        .unwrap();
    let c = credential();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.public_key=decode('01','hex'); RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE INSERT ON webauthn_credentials FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.register_credential(&c, Uuid::new_v4()).await,
        Err(EffectError::Mismatch("credential"))
    ));
    assert!(matches!(
        store.get_active_credential("new-c").await,
        Err(EffectError::CredentialNotFound)
    ));
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    store.register_credential(&c, Uuid::new_v4()).await.unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.counter=OLD.counter; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE UPDATE ON webauthn_credentials FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.advance_credential(&c, 2, 101).await,
        Err(EffectError::Mismatch("credential counter"))
    ));
    assert_eq!(store.get_active_credential("new-c").await.unwrap(), c);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    peer.execute("UPDATE webauthn_credentials SET public_key=decode('0123','hex') WHERE credential_id='new-c'",&[]).await.unwrap();
    assert!(matches!(
        store.advance_credential(&c, 2, 101).await,
        Err(EffectError::CredentialConflict)
    ));
    peer.execute(
        "UPDATE webauthn_credentials SET public_key=$1 WHERE credential_id='new-c'",
        &[&c.public_key],
    )
    .await
    .unwrap();
    let s = PreparedSession::new("new-p", 100, 20, 50, None).unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.idle_expires_at=999; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE INSERT ON sessions FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.issue_session(&s).await,
        Err(EffectError::Mismatch("session"))
    ));
    assert_eq!(
        store.observe_session_creation(&s).await.unwrap(),
        SessionCreationObservation::Unobserved
    );
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.event_type='session.created' AND NEW.event_id NOT LIKE 'duplicate:%' THEN INSERT INTO audit_events VALUES('duplicate:'||NEW.event_id,NEW.principal_id,NEW.event_type,NEW.object_type,NEW.object_id,NEW.detail_json,NEW.created_at); END IF; RETURN NEW; END; $$; CREATE TRIGGER fault AFTER INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.issue_session(&s).await,
        Err(EffectError::Mismatch("identity audit"))
    ));
    assert_eq!(
        store.observe_session_creation(&s).await.unwrap(),
        SessionCreationObservation::Unobserved
    );
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_SESSION_TEST_ACK_PROXY").unwrap());
    let proxy = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "identity_faults",
    )
    .unwrap();
    assert!(
        matches!(proxy.issue_session(&s).await,Err(EffectError::AuthorityCommitUnknown{operation:"session-create",ref coordinate,..}) if coordinate==s.audit_id())
    );
    assert!(matches!(
        store.observe_session_creation(&s).await.unwrap(),
        SessionCreationObservation::Exact(_)
    ));
    let before = store.list_sessions("new-p").await.unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.revoked_at=NULL; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store
            .revoke_all_sessions("new-p", Uuid::new_v4(), 105)
            .await,
        Err(EffectError::Mismatch("session set"))
    ));
    assert_eq!(store.list_sessions("new-p").await.unwrap(), before);
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    assert!(matches!(
        store.authenticate_session(s.token(), 120, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    assert!(matches!(
        store.authenticate_session(s.token(), 150, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    let auth = store
        .authenticate_session(s.token(), 110, 100)
        .await
        .unwrap();
    assert_eq!(auth.session.idle_expires_at, 150);
    assert!(matches!(
        store.authenticate_session(s.token(), 109, 20).await,
        Err(EffectError::SessionStale)
    ));
    assert!(matches!(
        store.authenticate_session(s.token(), 150, 20).await,
        Err(EffectError::SessionInvalid)
    ));
    assert!(PreparedSession::new("p", i64::MAX, 1, 2, None).is_err());
    println!(
        "six native fault rollback cases, real session issuance ACK loss, expiry boundaries and stale time rejection"
    );
}
