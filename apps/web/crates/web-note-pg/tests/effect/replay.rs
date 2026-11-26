use super::fixture::setup;
use ordivon_web_note_pg::{
    effect::EffectError,
    identity::{ChallengeObservation, ChallengePurpose, PreparedChallenge},
};
use serde_json::{Value, json};

fn purpose(s: &str) -> ChallengePurpose {
    match s {
        "register" => ChallengePurpose::Register,
        "login" => ChallengePurpose::Login,
        "grant-issue" => ChallengePurpose::GrantIssue,
        "grant-revoke" => ChallengePurpose::GrantRevoke,
        "effect-approve" => ChallengePurpose::EffectApprove,
        _ => panic!("unknown purpose"),
    }
}
#[tokio::test]
async fn native_challenge_dpop_sqlite_differential() {
    let (store, peer) = setup("identity_replay_diff").await;
    let output = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/replay-reference.ts"
        ))
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let reference: Value = serde_json::from_slice(&output.stdout).unwrap();
    for v in reference["challenges"].as_array().unwrap() {
        let purpose = purpose(v["purpose"].as_str().unwrap());
        let p = PreparedChallenge::new(
            purpose,
            "p",
            "challenge",
            v["row"]["payload_json"].as_str().unwrap().into(),
            100,
            20,
        )
        .unwrap();
        assert_eq!(
            p.record().payload_digest,
            v["row"]["payload_digest"].as_str().unwrap()
        );
        assert_eq!(p.record().expires_at, v["expiresAt"].as_i64().unwrap());
        assert_eq!(
            store.observe_challenge(&p).await.unwrap(),
            ChallengeObservation::Unobserved
        );
        store.issue_challenge(&p).await.unwrap();
        assert_eq!(
            store.observe_challenge(&p).await.unwrap(),
            ChallengeObservation::ExactUnconsumed
        );
        let record = store
            .consume_challenge(&p.record().challenge_id, purpose, "p", 101)
            .await
            .unwrap();
        assert!(record == *p.record());
        assert_eq!(
            store.observe_challenge(&p).await.unwrap(),
            ChallengeObservation::ExactConsumed(101)
        );
        assert!(matches!(
            store
                .consume_challenge(&p.record().challenge_id, purpose, "p", 102)
                .await,
            Err(EffectError::ChallengeInvalid)
        ));
    }
    for v in reference["proof"].as_array().unwrap() {
        let id = v["id"].as_str().unwrap();
        let now = v["now"].as_i64().unwrap();
        let ttl = v["ttl"].as_i64().unwrap();
        let result = store.consume_dpop_proof(id, now, ttl).await;
        let outcome = match result {
            Ok(()) => "ok",
            Err(ref e) => e.code(),
        };
        assert_eq!(outcome, v["outcome"].as_str().unwrap());
        let live=peer.query("SELECT proof_hash,expires_at FROM dpop_proofs WHERE expires_at>$1 ORDER BY proof_hash",&[&now]).await.unwrap().iter().map(|r|json!([r.get::<_,String>(0),r.get::<_,i64>(1)])).collect::<Vec<_>>();
        assert_eq!(json!(live), v["live"]);
    }
    // Physical retention differs deliberately: old inline GC vs new bounded maintenance.
    assert!(store.cleanup_dpop_proofs(112, 1).await.unwrap() <= 1);
    println!(
        "5 real SQLite challenge payload byte/digest vectors and 10 DPoP logical transitions match; physical GC separated"
    );
}
#[tokio::test]
async fn native_challenge_dpop_concurrency_and_rollback() {
    let (store, mut peer) = setup("identity_replay_race").await;
    let p = PreparedChallenge::new(
        ChallengePurpose::Login,
        "p",
        "challenge",
        r#"{"z":1,"a":2}"#.into(),
        100,
        20,
    )
    .unwrap();
    store.issue_challenge(&p).await.unwrap();
    let id = &p.record().challenge_id;
    assert!(matches!(
        store
            .consume_challenge(id, ChallengePurpose::Register, "p", 101)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    assert!(matches!(
        store
            .consume_challenge(id, ChallengePurpose::Login, "q", 101)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    assert!(matches!(
        store
            .consume_challenge(id, ChallengePurpose::Login, "p", 120)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    peer.execute(
        "UPDATE webauthn_challenges SET payload_json='{}' WHERE challenge_id=$1",
        &[&id],
    )
    .await
    .unwrap();
    assert!(matches!(
        store
            .consume_challenge(id, ChallengePurpose::Login, "p", 101)
            .await,
        Err(EffectError::ChallengeCorrupt)
    ));
    assert_eq!(
        store.observe_challenge(&p).await.unwrap(),
        ChallengeObservation::Mismatch
    );
    peer.execute(
        "UPDATE webauthn_challenges SET payload_json=$2 WHERE challenge_id=$1",
        &[&id, &p.record().payload_json],
    )
    .await
    .unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.consumed_at=NULL; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE UPDATE ON webauthn_challenges FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store
            .consume_challenge(id, ChallengePurpose::Login, "p", 101)
            .await,
        Err(EffectError::Mismatch("challenge consume"))
    ));
    assert_eq!(
        store.observe_challenge(&p).await.unwrap(),
        ChallengeObservation::ExactUnconsumed
    );
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    let (a, b) = tokio::join!(
        store.consume_challenge(id, ChallengePurpose::Login, "p", 101),
        store.consume_challenge(id, ChallengePurpose::Login, "p", 101)
    );
    assert_eq!(usize::from(a.is_ok()) + usize::from(b.is_ok()), 1);
    for r in [&a, &b] {
        assert!(r.is_ok() || matches!(r, Err(EffectError::Busy | EffectError::ChallengeInvalid)))
    }
    assert_eq!(
        store.observe_challenge(&p).await.unwrap(),
        ChallengeObservation::ExactConsumed(101)
    );
    let (a, b) = tokio::join!(
        store.consume_dpop_proof("same", 100, 20),
        store.consume_dpop_proof("same", 100, 20)
    );
    assert_eq!(usize::from(a.is_ok()) + usize::from(b.is_ok()), 1);
    for r in [&a, &b] {
        assert!(r.is_ok() || matches!(r, Err(EffectError::Busy | EffectError::DpopReplayed)))
    }
    assert!(matches!(
        store.consume_dpop_proof("same", 101, 20).await,
        Err(EffectError::DpopReplayed)
    ));
    store.consume_dpop_proof("same", 120, 20).await.unwrap();
    store.consume_dpop_proof("other", 100, 1).await.unwrap();
    let tx = peer.transaction().await.unwrap();
    tx.query(
        "SELECT * FROM dpop_proofs WHERE expires_at=101 FOR UPDATE",
        &[],
    )
    .await
    .unwrap();
    // Logical proof admission on disjoint identity doesn't wait for expiry GC.
    store.consume_dpop_proof("disjoint", 120, 20).await.unwrap();
    assert_eq!(store.cleanup_dpop_proofs(120, 1).await.unwrap(), 0);
    tx.rollback().await.unwrap();
    assert_eq!(store.cleanup_dpop_proofs(120, 1).await.unwrap(), 1);
    assert_eq!(store.cleanup_dpop_proofs(120, 1).await.unwrap(), 0);
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.expires_at=0; RETURN NEW; END; $$; CREATE TRIGGER fault BEFORE INSERT ON dpop_proofs FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.consume_dpop_proof("fault", 120, 20).await,
        Err(EffectError::Mismatch("dpop claim"))
    ));
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    store.consume_dpop_proof("fault", 120, 20).await.unwrap();
    peer.batch_execute("CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$; CREATE TRIGGER fault BEFORE DELETE ON dpop_proofs FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
    assert!(matches!(
        store.cleanup_dpop_proofs(140, 1).await,
        Err(EffectError::Mismatch("dpop cleanup"))
    ));
    peer.batch_execute("DROP FUNCTION fault() CASCADE")
        .await
        .unwrap();
    assert_eq!(store.cleanup_dpop_proofs(140, 1).await.unwrap(), 1);
    assert_eq!(store.cleanup_dpop_proofs(140, 1).await.unwrap(), 1);
    assert_eq!(store.cleanup_dpop_proofs(140, 1).await.unwrap(), 1);
    assert_eq!(store.cleanup_dpop_proofs(140, 1).await.unwrap(), 0);
    println!(
        "real one-shot Challenge/DPoP races, foreign/wrong purpose/expiry/corruption rejection, three trigger faults, SKIP LOCKED bounded cleanup and disjoint progress"
    );
}

#[test]
fn generated_dpop_expiry_and_cleanup_histories() {
    use proptest::{
        prelude::*,
        test_runner::{Config, RngSeed, TestRunner},
    };
    use std::collections::BTreeMap;
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let (store, peer) = rt.block_on(setup("identity_dpop_model"));
    let hashes: Vec<String> = rt.block_on(async {
        let mut result = Vec::new();
        for id in ["a", "b", "c", "🦀"] {
            result.push(
                peer.query_one("SELECT encode(sha256(convert_to($1,'UTF8')),'hex')", &[&id])
                    .await
                    .unwrap()
                    .get(0),
            );
        }
        result
    });
    let config = Config {
        cases: 40,
        rng_seed: RngSeed::Fixed(20261126),
        max_shrink_iters: 256,
        failure_persistence: Some(Box::new(
            proptest::test_runner::FileFailurePersistence::Direct(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/dpop.regressions"
            )),
        )),
        ..Config::default()
    };
    let cases = std::cell::Cell::new(0usize);
    let steps = std::cell::Cell::new(0usize);
    let strategy = prop::collection::vec((0usize..5, 0i64..5, 0u32..5), 1..25);
    TestRunner::new(config)
        .run(&strategy, |commands| {
            rt.block_on(async {
                peer.batch_execute("TRUNCATE dpop_proofs").await.unwrap();
                let mut model: BTreeMap<String, i64> = BTreeMap::new();
                let mut now = 100i64;
                for &(kind, delta, ttl) in &commands {
                    now += delta;
                    if kind == 4 {
                        let limit = ttl + 1;
                        let mut expired: Vec<_> = model
                            .iter()
                            .filter(|(_, v)| **v <= now)
                            .map(|(k, v)| (*v, k.clone()))
                            .collect();
                        expired.sort_unstable();
                        expired.truncate(limit as usize);
                        for (_, k) in &expired {
                            model.remove(k);
                        }
                        prop_assert_eq!(
                            store.cleanup_dpop_proofs(now, limit).await.unwrap(),
                            expired.len() as u64
                        );
                    } else {
                        let id = ["a", "b", "c", "🦀"][kind];
                        let hash = &hashes[kind];
                        let expected = if ttl == 0 {
                            "dpop-proof-invalid"
                        } else if model.get(hash).is_some_and(|x| *x > now) {
                            "dpop-proof-replayed"
                        } else {
                            model.insert(hash.clone(), now + i64::from(ttl));
                            "ok"
                        };
                        let result = store.consume_dpop_proof(id, now, i64::from(ttl)).await;
                        prop_assert_eq!(
                            match result {
                                Ok(()) => "ok",
                                Err(ref e) => e.code(),
                            },
                            expected
                        );
                    }
                    let actual: BTreeMap<String, i64> = peer
                        .query("SELECT proof_hash,expires_at FROM dpop_proofs", &[])
                        .await
                        .unwrap()
                        .iter()
                        .map(|r| (r.get(0), r.get(1)))
                        .collect();
                    prop_assert_eq!(&actual, &model);
                }
                Ok::<_, proptest::test_runner::TestCaseError>(())
            })?;
            cases.set(cases.get() + 1);
            steps.set(steps.get() + commands.len());
            Ok(())
        })
        .unwrap();
    assert!(cases.get() >= 40);
    println!(
        "independent DPoP expiry/GC model seed20261126: {} histories / {} commands; exact physical rows after every step",
        cases.get(),
        steps.get()
    );
}

#[tokio::test]
async fn native_replay_ack_unknown_fails_closed() {
    use ordivon_web_note_pg::PgNoteStore;
    let (store, _peer) = setup("identity_replay_ack").await;
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
    let proxy = |key: &str| {
        let socket = std::path::PathBuf::from(std::env::var_os(key).unwrap());
        PgNoteStore::local(
            &socket,
            std::env::var("WEB_NOTE_TEST_PORT")
                .unwrap()
                .parse()
                .unwrap(),
            &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
            "identity_replay_ack",
        )
        .unwrap()
    };
    let result = proxy("WEB_CHALLENGE_TEST_ACK_PROXY")
        .consume_challenge(&p.record().challenge_id, ChallengePurpose::Login, "p", 101)
        .await;
    assert!(matches!(
        result,
        Err(EffectError::AuthorityCommitUnknown {
            operation: "challenge-consume",
            ..
        })
    ));
    assert_eq!(
        store.observe_challenge(&p).await.unwrap(),
        ChallengeObservation::ExactConsumed(101)
    );
    assert!(matches!(
        store
            .consume_challenge(&p.record().challenge_id, ChallengePurpose::Login, "p", 101)
            .await,
        Err(EffectError::ChallengeInvalid)
    ));
    assert!(matches!(
        proxy("WEB_DPOP_TEST_ACK_PROXY")
            .consume_dpop_proof("ack", 100, 20)
            .await,
        Err(EffectError::AuthorityCommitUnknown {
            operation: "dpop-consume",
            ..
        })
    ));
    assert!(matches!(
        store.consume_dpop_proof("ack", 101, 20).await,
        Err(EffectError::DpopReplayed)
    ));
    println!(
        "real Challenge and DPoP COMMIT ACK loss remains UNKNOWN; consumption stays burned and retry is denied"
    );
}
