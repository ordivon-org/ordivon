use super::fixture::setup;
use ordivon_web_note_pg::{
    PgNoteStore,
    effect::EffectError,
    identity::{
        ChallengeObservation, ChallengePurpose, LoginObservation, PreparedChallenge,
        PreparedSession,
    },
};
#[tokio::test]
async fn native_verified_login_atomicity_and_one_completion() {
    let (store, peer) = setup("identity_login").await;
    let p = PreparedChallenge::new(
        ChallengePurpose::Login,
        "p",
        "challenge",
        "{}".into(),
        100,
        20,
    )
    .unwrap();
    store.issue_challenge(&p).await.unwrap();
    peer.execute(
        "UPDATE webauthn_credentials SET last_used_at=101 WHERE credential_id='credential'",
        &[],
    )
    .await
    .unwrap();
    let prior = store.get_active_credential("credential").await.unwrap();
    assert_eq!(prior.counter, 0);
    let s = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    assert!(matches!(
        store
            .complete_verified_login(p.record(), 101, &prior, 0, &s)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    let consumed = store
        .consume_challenge(&p.record().challenge_id, ChallengePurpose::Login, "p", 101)
        .await
        .unwrap();
    assert_eq!(
        store
            .observe_verified_login(&consumed, 101, &prior, 0, &s)
            .await
            .unwrap(),
        LoginObservation::Unobserved
    );
    let wrong = PreparedSession::new("q", 101, 20, 50, None).unwrap();
    assert!(matches!(
        store
            .complete_verified_login(&consumed, 101, &prior, 0, &wrong)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    for (table, op, body) in [
        (
            "webauthn_credentials",
            "UPDATE",
            "NEW.counter=99; RETURN NEW;",
        ),
        ("sessions", "INSERT", "RETURN NULL;"),
        (
            "webauthn_login_completions",
            "UPDATE",
            "NEW.session_id=NULL; NEW.completed_at=NULL; RETURN NEW;",
        ),
        (
            "audit_events",
            "INSERT",
            "IF NEW.event_type='session.login-completed' THEN NEW.detail_json='{}'; END IF; RETURN NEW;",
        ),
    ] {
        peer.batch_execute(&format!("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN {body} END; $$; CREATE TRIGGER fault BEFORE {op} ON {table} FOR EACH ROW EXECUTE FUNCTION fault()")).await.unwrap();
        let outcome = store
            .complete_verified_login(&consumed, 101, &prior, 0, &s)
            .await;
        assert!(
            matches!(
                outcome,
                Err(EffectError::Mismatch(_) | EffectError::Write(_))
            ),
            "unexpected login fault"
        );
        assert_eq!(
            store.get_active_credential("credential").await.unwrap(),
            prior
        );
        assert!(store.list_sessions("p").await.unwrap().is_empty());
        assert_eq!(
            store
                .observe_verified_login(&consumed, 101, &prior, 0, &s)
                .await
                .unwrap(),
            LoginObservation::Unobserved
        );
        assert_eq!(
            store.observe_challenge(&p).await.unwrap(),
            ChallengeObservation::ExactConsumed(101)
        );
        peer.batch_execute("DROP FUNCTION fault() CASCADE")
            .await
            .unwrap();
    }
    // Same challenge, zero counter, same completion timestamp, different
    // session identifiers. Only one completion and no duplicate session.
    let s2 = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    let (a, b) = tokio::join!(
        store.complete_verified_login(&consumed, 101, &prior, 0, &s),
        store.complete_verified_login(&consumed, 101, &prior, 0, &s2)
    );
    assert_eq!(usize::from(a.is_ok()) + usize::from(b.is_ok()), 1);
    let winner = if a.is_ok() { &s } else { &s2 };
    let loser = if a.is_ok() { &s2 } else { &s };
    assert!(matches!(
        store
            .complete_verified_login(&consumed, 101, &prior, 0, loser)
            .await,
        Err(EffectError::LoginCompleted)
    ));
    let sessions = store.list_sessions("p").await.unwrap();
    assert_eq!(sessions.len(), 1);
    assert_eq!(sessions[0].session_id, winner.session_id());
    assert!(matches!(
        store
            .observe_verified_login(&consumed, 101, &prior, 0, winner)
            .await
            .unwrap(),
        LoginObservation::Exact(_)
    ));
    assert_eq!(
        store
            .observe_verified_login(&consumed, 101, &prior, 0, loser)
            .await
            .unwrap(),
        LoginObservation::Mismatch
    );
    let authenticated = store
        .authenticate_session(winner.token(), 102, 20)
        .await
        .unwrap();
    assert_eq!(authenticated.principal.principal_id, "p");
    assert_eq!(
        peer.query_one(
            "SELECT count(*) FROM audit_events WHERE event_type='session.login-completed'",
            &[]
        )
        .await
        .unwrap()
        .get::<_, i64>(0),
        1
    );
    assert_eq!(
        peer.query_one(
            "SELECT session_id FROM webauthn_login_completions WHERE challenge_id=$1",
            &[&consumed.challenge_id]
        )
        .await
        .unwrap()
        .get::<_, String>(0),
        winner.session_id()
    );
    peer.execute(
        "DELETE FROM audit_events WHERE event_type='session.login-completed'",
        &[],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .complete_verified_login(&consumed, 101, &prior, 0, loser)
            .await,
        Err(EffectError::LoginCompleted)
    ));
    assert_eq!(
        store
            .observe_verified_login(&consumed, 101, &prior, 0, winner)
            .await
            .unwrap(),
        LoginObservation::Mismatch
    );
    assert_eq!(store.list_sessions("p").await.unwrap().len(), 1);
    println!(
        "trusted verified-login composition: 4 native faults rollback counter/session/completion/audits while consumed challenge stays burned; zero-counter concurrent completion exactly once; real session consumer"
    );
}
#[tokio::test]
async fn native_verified_login_ack_unknown() {
    let (store, peer) = setup("identity_login_ack").await;
    let p = PreparedChallenge::new(
        ChallengePurpose::Login,
        "p",
        "challenge",
        "{}".into(),
        100,
        20,
    )
    .unwrap();
    store.issue_challenge(&p).await.unwrap();
    let c = store
        .consume_challenge(&p.record().challenge_id, ChallengePurpose::Login, "p", 101)
        .await
        .unwrap();
    let prior = store.get_active_credential("credential").await.unwrap();
    let s = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    let socket = std::path::PathBuf::from(std::env::var_os("WEB_LOGIN_TEST_ACK_PROXY").unwrap());
    let proxy = PgNoteStore::local(
        &socket,
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "identity_login_ack",
    )
    .unwrap();
    let result = proxy.complete_verified_login(&c, 101, &prior, 1, &s).await;
    assert!(matches!(
        result,
        Err(EffectError::AuthorityCommitUnknown {
            operation: "login-complete",
            ..
        })
    ));
    let observed = store
        .observe_verified_login(&c, 101, &prior, 1, &s)
        .await
        .unwrap();
    assert!(matches!(observed,LoginObservation::Exact(ref v) if v.session_id==s.session_id()));
    assert!(matches!(
        store.complete_verified_login(&c, 101, &prior, 1, &s).await,
        Err(EffectError::LoginCompleted)
    ));
    assert_eq!(
        store
            .get_active_credential("credential")
            .await
            .unwrap()
            .counter,
        1
    );
    assert_eq!(store.list_sessions("p").await.unwrap().len(), 1);
    assert_eq!(peer.query_one("SELECT count(*) FROM audit_events WHERE event_type IN ('session.created','session.login-completed')",&[]).await.unwrap().get::<_,i64>(0),2);
    println!(
        "native verified-login COMMIT ACK loss: exact completion/session evidence, no duplicate or implicit secret release"
    );
}

#[tokio::test]
async fn native_login_v2_upgrade_keeps_legacy_challenges_closed() {
    let (store, mut peer) = setup("identity_login_migration").await;
    // Reconstruct a private V1 owner, with a previously consumed legacy
    // Challenge. V2 adds no eligibility to the existing record.
    peer.batch_execute("DROP TABLE webauthn_login_completions")
        .await
        .unwrap();
    let legacy =
        PreparedChallenge::new(ChallengePurpose::Login, "p", "old", "{}".into(), 100, 20).unwrap();
    let c = legacy.record();
    peer.execute(
        "INSERT INTO webauthn_challenges VALUES($1,'login',$2,$3,$4,$5,$6,101)",
        &[
            &c.challenge_id,
            &c.principal_id,
            &c.challenge,
            &c.payload_digest,
            &c.payload_json,
            &c.expires_at,
        ],
    )
    .await
    .unwrap();
    let before = {
        let tx = peer.transaction().await.unwrap();
        let snapshot = ordivon_web_note_pg::migration::read_snapshot(&tx)
            .await
            .unwrap();
        tx.rollback().await.unwrap();
        snapshot
    };
    peer.batch_execute(ordivon_web_note_pg::migration::LOGIN_COMPLETION_SCHEMA_V2)
        .await
        .unwrap();
    let after = {
        let tx = peer.transaction().await.unwrap();
        let snapshot = ordivon_web_note_pg::migration::read_snapshot(&tx)
            .await
            .unwrap();
        tx.rollback().await.unwrap();
        snapshot
    };
    assert_eq!(before, after);
    assert!(
        peer.batch_execute(ordivon_web_note_pg::migration::LOGIN_COMPLETION_SCHEMA_V2)
            .await
            .is_err()
    );
    assert_eq!(
        peer.query_one("SELECT count(*) FROM webauthn_login_completions", &[])
            .await
            .unwrap()
            .get::<_, i64>(0),
        0
    );
    let prior = store.get_active_credential("credential").await.unwrap();
    let session = PreparedSession::new("p", 101, 20, 50, None).unwrap();
    assert!(matches!(
        store
            .complete_verified_login(c, 101, &prior, 0, &session)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    assert_eq!(
        store.observe_challenge(&legacy).await.unwrap(),
        ChallengeObservation::Mismatch
    );
    assert!(store.list_sessions("p").await.unwrap().is_empty());
    let new =
        PreparedChallenge::new(ChallengePurpose::Login, "p", "new", "{}".into(), 100, 20).unwrap();
    store.issue_challenge(&new).await.unwrap();
    let record = store
        .consume_challenge(
            &new.record().challenge_id,
            ChallengePurpose::Login,
            "p",
            101,
        )
        .await
        .unwrap();
    assert!(
        store
            .complete_verified_login(&record, 101, &prior, 0, &session)
            .await
            .is_ok()
    );
    println!(
        "native additive V2 schema: all 11 V1 table facts identical, repeat DDL rejected, legacy consumed challenge cannot finalize; new native challenge can"
    );
}
