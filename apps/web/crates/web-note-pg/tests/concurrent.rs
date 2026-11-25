#[path = "concurrent/model.rs"]
mod model;
mod support;
use model::{Call, Event, Facts, Intent, Reply, witness};
use ordivon_web_note_pg::{Note, NoteError, NoteObservation, NoteState, PgNoteStore, PreparedNote};
use proptest::{
    prelude::*,
    test_runner::{Config, TestCaseError, TestRunner},
};
use std::{cell::Cell, time::Duration};
use uuid::Uuid;

fn note_id(n: u8) -> String {
    Uuid::from_u128(0x1000 + u128::from(n)).to_string()
}
fn audit_id(n: u8) -> String {
    Uuid::from_u128(0x2000 + u128::from(n)).to_string()
}
fn principal(p: bool) -> &'static str {
    if p { "p" } else { "q" }
}
fn content(c: u8) -> String {
    format!("content-{c} 🦀")
}
fn request(i: &Intent) -> PreparedNote {
    PreparedNote::restore(
        Uuid::parse_str(&note_id(i.note)).unwrap(),
        Uuid::parse_str(&audit_id(i.audit)).unwrap(),
        principal(i.principal),
        &content(i.content),
        i.time,
    )
    .unwrap()
}
fn check_note(n: &Note, i: &Intent) {
    assert_eq!(n.note_id, note_id(i.note));
    assert_eq!(n.principal_id, principal(i.principal));
    assert_eq!(n.content, content(i.content));
    assert_eq!(n.created_at, i.time);
    assert_eq!(n.state, NoteState::Draft);
    assert_eq!(n.published_at, None);
}
async fn invoke(store: &PgNoteStore, call: &Call, universe: &[Intent]) -> Reply {
    match call {
        Call::Execute(i) => match store.execute(&request(i)).await {
            Ok(n) => {
                check_note(&n, i);
                Reply::Created(i.clone())
            }
            Err(NoteError::Database { source, .. })
                if source.code().is_some_and(|c| c.code() == "23505") =>
            {
                Reply::Collision
            }
            Err(e) => panic!("unqualified native outcome (not a model rejection): {e:?}"),
        },
        Call::Observe(i) => match store.observe(&request(i)).await.unwrap() {
            NoteObservation::Exact(n) => {
                check_note(&n, i);
                Reply::Exact
            }
            NoteObservation::Unobserved => Reply::Unobserved,
            NoteObservation::Mismatch => Reply::Mismatch,
        },
        Call::List(p) => {
            let rows = store.list(principal(*p)).await.unwrap();
            Reply::Listed(
                rows.iter()
                    .map(|n| {
                        // Match visible fields to a unique candidate; audit identity
                        // isn't visible in list, so it is projected out separately.
                        let i = universe
                            .iter()
                            .find(|i| {
                                n.note_id == note_id(i.note)
                                    && n.principal_id == principal(i.principal)
                                    && n.content == content(i.content)
                                    && n.created_at == i.time
                            })
                            .expect("list returned unexpected projection");
                        check_note(n, i);
                        let mut i = i.clone();
                        i.audit = 0;
                        i
                    })
                    .collect(),
            )
        }
    }
}
async fn run_call(
    store: &PgNoteStore,
    clock: &Cell<usize>,
    call: Call,
    universe: &[Intent],
) -> Event {
    let start = clock.get();
    clock.set(start + 1);
    let reply = invoke(store, &call, universe).await;
    let end = clock.get();
    clock.set(end + 1);
    Event {
        start,
        end,
        call,
        reply,
    }
}
async fn peer_facts(peer: &tokio_postgres::Client, universe: &[Intent]) -> Facts {
    let mut facts = Facts::default();
    let audits=peer.query("SELECT event_id,principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events",&[]).await.unwrap();
    let notes = peer
        .query(
            "SELECT note_id,principal_id,content,state,created_at,published_at FROM canary_notes",
            &[],
        )
        .await
        .unwrap();
    for r in notes {
        let i = universe
            .iter()
            .find(|i| {
                r.get::<_, String>(0) == note_id(i.note)
                    && r.get::<_, String>(1) == principal(i.principal)
                    && r.get::<_, String>(2) == content(i.content)
                    && r.get::<_, i64>(4) == i.time
                    && audits.iter().any(|a| {
                        a.get::<_, String>(0) == audit_id(i.audit)
                            && a.get::<_, String>(4) == note_id(i.note)
                    })
            })
            .expect("independent peer Note with no matching intent/Audit");
        assert_eq!(r.get::<_, String>(3), "DRAFT");
        assert_eq!(r.get::<_, Option<i64>>(5), None);
        assert!(facts.notes.insert(i.note, i.clone()).is_none());
    }
    for r in audits {
        let i = facts
            .notes
            .values()
            .find(|i| {
                r.get::<_, String>(0) == audit_id(i.audit)
                    && r.get::<_, String>(4) == note_id(i.note)
            })
            .expect("orphan peer Audit");
        assert_eq!(r.get::<_, String>(1), principal(i.principal));
        assert_eq!(r.get::<_, String>(2), "canary.note.created");
        assert_eq!(r.get::<_, String>(3), "canary-note");
        assert_eq!(r.get::<_, String>(5), "{}");
        assert_eq!(r.get::<_, i64>(6), i.time);
        assert!(facts.audits.insert(i.audit, i.clone()).is_none());
    }
    assert_eq!(
        support::counts(peer).await,
        (facts.notes.len() as i64, facts.audits.len() as i64)
    );
    facts
}
fn intent() -> impl Strategy<Value = Intent> {
    (0u8..3, 0u8..3, any::<bool>(), 0u8..3, -2i64..3).prop_map(
        |(note, audit, principal, content, time)| Intent {
            note,
            audit,
            principal,
            content,
            time,
        },
    )
}
async fn history(
    store: &PgNoteStore,
    peer: &tokio_postgres::Client,
    a: Intent,
    b: Intent,
    p: bool,
) -> Result<usize, TestCaseError> {
    support::reset(peer).await;
    let clock = Cell::new(0);
    let universe = [a.clone(), b.clone()];
    let (x, y, z) = tokio::join!(
        run_call(store, &clock, Call::Execute(a.clone()), &universe),
        run_call(store, &clock, Call::Execute(b.clone()), &universe),
        run_call(store, &clock, Call::Observe(a.clone()), &universe)
    );
    let after = run_call(store, &clock, Call::List(p), &universe).await;
    let events = vec![x, y, z, after];
    let final_facts = peer_facts(peer, &universe).await;
    // Check actual overlapping calls, not simply a sequential replay.
    prop_assert!(
        events[0].start < events[1].end && events[1].start < events[0].end,
        "no overlapping writes"
    );
    let w = witness(&events, &final_facts);
    prop_assert!(
        w.is_some(),
        "nonlinearizable history: {:?}; peer {:?}",
        events,
        final_facts
    );
    Ok(events.len())
}
#[test]
fn generated_concurrent_histories() {
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let (store, peer) = rt.block_on(support::fixture());
    let cases = Cell::new(0);
    let events = Cell::new(0);
    let seed = std::env::var("WEB_NOTE_CONCURRENT_SEED")
        .ok()
        .map(|s| s.parse::<u64>().expect("u64 seed"))
        .unwrap_or(20261126);
    let mut runner = TestRunner::new(Config {
        cases: 40,
        rng_seed: proptest::test_runner::RngSeed::Fixed(seed),
        max_shrink_iters: 128,
        failure_persistence: Some(Box::new(
            proptest::test_runner::FileFailurePersistence::Direct(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/concurrent.regressions"
            )),
        )),
        ..Config::default()
    });
    runner
        .run(&(intent(), intent(), any::<bool>()), |(a, b, p)| {
            let n = rt.block_on(history(&store, &peer, a, b, p))?;
            cases.set(cases.get() + 1);
            events.set(events.get() + n);
            Ok(())
        })
        .unwrap();
    assert!(cases.get() >= 40);
    println!(
        "concurrent generated seed={seed}, histories={}, operations={}",
        cases.get(),
        events.get()
    );
}
#[test]
fn bounded_oracle_rejects_impossible_histories() {
    let i = Intent {
        note: 0,
        audit: 0,
        principal: true,
        content: 1,
        time: 0,
    };
    let mut f = Facts::default();
    f.step(&Call::Execute(i.clone()));
    let write = Event {
        start: 0,
        end: 1,
        call: Call::Execute(i.clone()),
        reply: Reply::Created(i.clone()),
    };
    let stale = Event {
        start: 2,
        end: 3,
        call: Call::Observe(i.clone()),
        reply: Reply::Unobserved,
    };
    assert!(witness(&[write.clone(), stale], &f).is_none());
    let overlap = Event {
        start: 1,
        end: 3,
        call: Call::Observe(i.clone()),
        reply: Reply::Unobserved,
    };
    let write = Event {
        start: 0,
        end: 2,
        ..write
    };
    assert!(witness(&[write.clone(), overlap], &f).is_some());
    let duplicate = Event {
        start: 3,
        end: 4,
        call: Call::Execute(i.clone()),
        reply: Reply::Created(i),
    };
    assert!(witness(&[write, duplicate], &f).is_none());
    assert!(witness(&[], &f).is_none());
    println!(
        "oracle controls: real-time stale, overlap legal, duplicate success and wrong final state"
    );
}
#[tokio::test]
async fn coherent_snapshot_under_forced_commit() {
    let (store, peer) = support::fixture().await;
    support::reset(&peer).await;
    let i = Intent {
        note: 1,
        audit: 2,
        principal: true,
        content: 0,
        time: 10,
    };
    let op = request(&i);
    // The independent transaction locks only the Audit relation, writes both
    // facts, and commits after observe has read the old Note and reached the
    // blocked Audit SELECT. No application hooks or sleeps as evidence.
    peer.batch_execute("BEGIN; LOCK TABLE audit_events IN ACCESS EXCLUSIVE MODE")
        .await
        .unwrap();
    peer.execute(
        "INSERT INTO canary_notes VALUES ($1,'p',$2,'DRAFT',10,NULL)",
        &[&note_id(i.note), &content(i.content)],
    )
    .await
    .unwrap();
    peer.execute(
        "INSERT INTO audit_events VALUES ($1,'p','canary.note.created','canary-note',$2,'{}',10)",
        &[&audit_id(i.audit), &note_id(i.note)],
    )
    .await
    .unwrap();
    let task_store = store.clone();
    let held = op.clone();
    let task = tokio::spawn(async move { task_store.observe(&held).await });
    let mut reached = false;
    for _ in 0..100 {
        reached=peer.query_one("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event_type='Lock' AND query LIKE '%FROM audit_events%')",&[]).await.unwrap().get(0);
        if reached {
            break;
        }
        tokio::time::sleep(Duration::from_millis(10)).await;
        // pg_stat_activity is snapshot-cached within the writer transaction.
        peer.batch_execute("SELECT pg_stat_clear_snapshot()")
            .await
            .unwrap();
    }
    assert!(reached, "observe reached actual blocked Audit SELECT");
    peer.batch_execute("COMMIT").await.unwrap();
    let outcome = task.await.unwrap().unwrap();
    assert_eq!(
        outcome,
        NoteObservation::Unobserved,
        "coherent snapshot: old Note and new Audit cannot be combined"
    );
    assert!(matches!(
        store.observe(&op).await.unwrap(),
        NoteObservation::Exact(_)
    ));
    assert_eq!(support::counts(&peer).await, (1, 1));
    println!(
        "forced native snapshot interleaving: Audit lock witnessed, atomic peer COMMIT, old snapshot unobserved, fresh exact"
    );
}

#[tokio::test]
async fn native_identity_conflicts_have_one_winner() {
    let (store, peer) = support::fixture().await;
    for same_note in [true, false] {
        support::reset(&peer).await;
        // Hold the first candidate after its Note insertion, before Audit
        // insertion completes. The second candidate then reaches an actual
        // transaction-ID wait on the conflicting unique index.
        let a = Intent {
            note: 0,
            audit: 0,
            principal: true,
            content: 1,
            time: 5,
        };
        let b = Intent {
            note: if same_note { 0 } else { 1 },
            audit: if same_note { 1 } else { 0 },
            principal: false,
            content: 2,
            time: 6,
        };
        // For audit collision the first Audit must already have been inserted:
        // AFTER INSERT fires while the unique index entry is uncommitted.
        peer.batch_execute("SELECT pg_advisory_lock(681233); CREATE FUNCTION fault() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.principal_id='p' THEN PERFORM pg_advisory_xact_lock(681233); END IF; RETURN NEW; END; $$; CREATE TRIGGER hold_first AFTER INSERT ON audit_events FOR EACH ROW EXECUTE FUNCTION fault()").await.unwrap();
        let left = store.clone();
        let op = request(&a);
        let first = tokio::spawn(async move { left.execute(&op).await });
        let mut held = false;
        for _ in 0..100 {
            held=peer.query_one("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event='advisory')",&[]).await.unwrap().get(0);
            if held {
                break;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
        assert!(held, "first transaction not observed at native lock");
        let right = store.clone();
        let op = request(&b);
        let second = tokio::spawn(async move { right.execute(&op).await });
        let mut collision = false;
        for _ in 0..100 {
            collision=peer.query_one("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE application_name='ordivon-web-note-candidate' AND wait_event='transactionid')",&[]).await.unwrap().get(0);
            if collision {
                break;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
        assert!(
            collision,
            "second transaction not observed waiting on conflicting unique key"
        );
        assert_eq!(support::counts(&peer).await, (0, 0));
        peer.batch_execute("SELECT pg_advisory_unlock(681233)")
            .await
            .unwrap();
        check_note(&first.await.unwrap().unwrap(), &a);
        assert!(
            matches!(second.await.unwrap(),Err(NoteError::Database{source,..}) if source.code().is_some_and(|c|c.code()=="23505"))
        );
        let facts = peer_facts(&peer, &[a.clone(), b.clone()]).await;
        let mut expected = Facts::default();
        expected.step(&Call::Execute(a.clone()));
        assert_eq!(facts, expected);
        assert!(matches!(
            store.observe(&request(&a)).await.unwrap(),
            NoteObservation::Exact(_)
        ));
        assert_eq!(
            store.observe(&request(&b)).await.unwrap(),
            NoteObservation::Mismatch
        );
        println!(
            "native forced {} collision: actual transactionid wait, winner exact, loser 23505, no partial state",
            if same_note { "Note" } else { "Audit" }
        );
    }
}
