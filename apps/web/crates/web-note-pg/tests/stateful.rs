//! Generated native trajectories; the oracle is independent maps of facts,
//! never production PreparedNote internals or SQL used by the implementation.
mod support;
use ordivon_web_note_pg::{NoteError, NoteObservation, NoteState, PreparedNote};
use proptest::{
    prelude::*,
    test_runner::{Config, TestCaseError, TestRunner},
};
use std::collections::BTreeMap;
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Eq)]
struct Intent {
    n: u8,
    a: u8,
    p: bool,
    c: String,
    t: i64,
}
impl Intent {
    fn principal(&self) -> &str {
        if self.p { "p" } else { "q" }
    }
    fn request(&self) -> PreparedNote {
        PreparedNote::restore(
            note_id(self.n),
            audit_id(self.a),
            self.principal(),
            &self.c,
            self.t,
        )
        .unwrap()
    }
}
fn note_id(x: u8) -> Uuid {
    Uuid::from_u128(0x1000 + u128::from(x))
}
fn audit_id(x: u8) -> Uuid {
    Uuid::from_u128(0x2000 + u128::from(x))
}
fn intent() -> impl Strategy<Value = Intent> {
    (
        0u8..4,
        0u8..4,
        any::<bool>(),
        prop::sample::select(vec!["", "text", "🦀 汉字", "a\n\t'", "other"])
            .prop_map(str::to_string),
        prop_oneof![
            Just(0),
            Just(-9_007_199_254_740_991i64),
            Just(9_007_199_254_740_991i64),
            -3i64..4
        ],
    )
        .prop_map(|(n, a, p, c, t)| Intent { n, a, p, c, t })
}
#[derive(Debug, Clone)]
enum Command {
    Execute(Intent),
    Observe(Intent),
    ObserveKnown(u8),
    Publish(u8),
    RemoveAudit(u8),
    CorruptAudit(u8),
    InsertOrphan(Intent),
    List(bool),
}
fn command() -> impl Strategy<Value = Command> {
    prop_oneof![
      5=>intent().prop_map(Command::Execute),3=>intent().prop_map(Command::Observe),
      3=>(0u8..4).prop_map(Command::ObserveKnown),
      2=>(0u8..4).prop_map(Command::Publish),
      2=>(0u8..4).prop_map(Command::RemoveAudit),
      2=>(0u8..4).prop_map(Command::CorruptAudit),
      2=>intent().prop_map(Command::InsertOrphan),
      1=>any::<bool>().prop_map(Command::List),
    ]
}
#[derive(Debug, Clone, PartialEq, Eq)]
struct NoteFact {
    intent: Intent,
    published: bool,
}
#[derive(Debug, Clone, PartialEq, Eq)]
struct AuditFact {
    intent: Intent,
    corrupt: bool,
}
#[derive(Default)]
struct Model {
    notes: BTreeMap<u8, NoteFact>,
    audits: BTreeMap<u8, AuditFact>,
}
impl Model {
    fn observation(&self, i: &Intent) -> u8 {
        let note = self.notes.get(&i.n);
        let related: Vec<_> = self
            .audits
            .values()
            .filter(|a| a.intent.a == i.a || a.intent.n == i.n)
            .collect();
        if note.is_none() && related.is_empty() {
            0
        } else if note.is_some_and(|n| {
            !n.published
                && n.intent.n == i.n
                && n.intent.p == i.p
                && n.intent.c == i.c
                && n.intent.t == i.t
        }) && related.len() == 1
            && related[0].intent.a == i.a
            && related[0].intent.n == i.n
            && related[0].intent.p == i.p
            && related[0].intent.t == i.t
            && !related[0].corrupt
        {
            1
        } else {
            2
        }
    }
}
async fn compare(
    store: &ordivon_web_note_pg::PgNoteStore,
    peer: &tokio_postgres::Client,
    m: &Model,
) -> Result<(), TestCaseError> {
    prop_assert_eq!(
        support::counts(peer).await,
        (m.notes.len() as i64, m.audits.len() as i64)
    );
    for p in [false, true] {
        let principal = if p { "p" } else { "q" };
        let actual = store
            .list(principal)
            .await
            .map_err(|e| TestCaseError::fail(format!("list: {e}")))?;
        let mut expected: Vec<_> = m.notes.values().filter(|n| n.intent.p == p).collect();
        expected.sort_by_key(|n| (std::cmp::Reverse(n.intent.t), n.intent.n));
        prop_assert_eq!(actual.len(), expected.len());
        for (a, b) in actual.iter().zip(expected) {
            prop_assert_eq!(&a.note_id, &note_id(b.intent.n).to_string());
            prop_assert_eq!(&a.principal_id, principal);
            prop_assert_eq!(&a.content, &b.intent.c);
            prop_assert_eq!(a.created_at, b.intent.t);
            prop_assert_eq!(
                a.state,
                if b.published {
                    NoteState::Published
                } else {
                    NoteState::Draft
                }
            );
            prop_assert_eq!(a.published_at, if b.published { Some(77) } else { None });
        }
    }
    // Native independent observations, not the implementation's list/observe.
    let notes=peer.query("SELECT note_id,principal_id,content,state,created_at,published_at FROM canary_notes ORDER BY note_id",&[]).await.unwrap();
    prop_assert_eq!(notes.len(), m.notes.len());
    for (r, n) in notes.iter().zip(m.notes.values()) {
        prop_assert_eq!(r.get::<_, String>(0), note_id(n.intent.n).to_string());
        prop_assert_eq!(r.get::<_, String>(1), n.intent.principal());
        prop_assert_eq!(r.get::<_, String>(2), n.intent.c.clone());
        prop_assert_eq!(
            r.get::<_, String>(3),
            if n.published { "PUBLISHED" } else { "DRAFT" }
        );
        prop_assert_eq!(r.get::<_, i64>(4), n.intent.t);
        prop_assert_eq!(
            r.get::<_, Option<i64>>(5),
            if n.published { Some(77) } else { None }
        );
    }
    let audits=peer.query("SELECT event_id,principal_id,event_type,object_type,object_id,detail_json,created_at FROM audit_events ORDER BY event_id",&[]).await.unwrap();
    prop_assert_eq!(audits.len(), m.audits.len());
    for (r, a) in audits.iter().zip(m.audits.values()) {
        prop_assert_eq!(r.get::<_, String>(0), audit_id(a.intent.a).to_string());
        prop_assert_eq!(r.get::<_, String>(1), a.intent.principal());
        prop_assert_eq!(r.get::<_, String>(2), "canary.note.created");
        prop_assert_eq!(r.get::<_, String>(3), "canary-note");
        prop_assert_eq!(r.get::<_, String>(4), note_id(a.intent.n).to_string());
        prop_assert_eq!(r.get::<_, String>(5), if a.corrupt { "[]" } else { "{}" });
        prop_assert_eq!(r.get::<_, i64>(6), a.intent.t);
    }
    Ok(())
}
async fn observe(
    store: &ordivon_web_note_pg::PgNoteStore,
    m: &Model,
    i: &Intent,
) -> Result<(), TestCaseError> {
    let actual = store
        .observe(&i.request())
        .await
        .map_err(|e| TestCaseError::fail(format!("observe: {e}")))?;
    let kind = match actual {
        NoteObservation::Unobserved => 0,
        NoteObservation::Exact(n) => {
            prop_assert_eq!(n.note_id, note_id(i.n).to_string());
            prop_assert_eq!(n.principal_id, i.principal());
            prop_assert_eq!(n.content, i.c.clone());
            prop_assert_eq!(n.created_at, i.t);
            prop_assert_eq!(n.state, NoteState::Draft);
            prop_assert_eq!(n.published_at, None);
            1
        }
        NoteObservation::Mismatch => 2,
    };
    prop_assert_eq!(kind, m.observation(i), "intent {:?}", i);
    Ok(())
}
async fn check_trace(
    store: &ordivon_web_note_pg::PgNoteStore,
    peer: &tokio_postgres::Client,
    commands: &[Command],
) -> Result<(), TestCaseError> {
    // Reset fixture between cases without rebuilding PG or consuming
    // old database state as the oracle.
    support::reset(peer).await;
    let mut m = Model::default();
    for cmd in commands {
        match cmd {
            Command::Execute(i) => {
                let occupied = m.notes.contains_key(&i.n) || m.audits.contains_key(&i.a);
                let related = m.audits.values().any(|a| a.intent.n == i.n);
                let result = store.execute(&i.request()).await;
                if occupied {
                    prop_assert!(
                        matches!(result,Err(NoteError::Database{ref source,..}) if source.code().is_some_and(|c|c.code()=="23505")),
                        "collision {:?}",
                        result
                    );
                } else if related {
                    prop_assert!(
                        matches!(result, Err(NoteError::AuditMismatch)),
                        "orphan conflict {:?}",
                        result
                    );
                } else {
                    let note = result.map_err(|e| TestCaseError::fail(format!("execute: {e}")))?;
                    prop_assert_eq!(note.note_id, note_id(i.n).to_string());
                    m.notes.insert(
                        i.n,
                        NoteFact {
                            intent: i.clone(),
                            published: false,
                        },
                    );
                    m.audits.insert(
                        i.a,
                        AuditFact {
                            intent: i.clone(),
                            corrupt: false,
                        },
                    );
                }
                observe(store, &m, i).await?;
            }
            Command::Observe(i) => observe(store, &m, i).await?,
            Command::ObserveKnown(n) => {
                if let Some(f) = m.notes.get(n) {
                    observe(store, &m, &f.intent).await?;
                }
            }
            Command::Publish(n) => {
                peer.execute(
                    "UPDATE canary_notes SET state='PUBLISHED',published_at=77 WHERE note_id=$1",
                    &[&note_id(*n).to_string()],
                )
                .await
                .unwrap();
                if let Some(f) = m.notes.get_mut(n) {
                    f.published = true;
                }
            }
            Command::RemoveAudit(a) => {
                peer.execute(
                    "DELETE FROM audit_events WHERE event_id=$1",
                    &[&audit_id(*a).to_string()],
                )
                .await
                .unwrap();
                m.audits.remove(a);
            }
            Command::CorruptAudit(a) => {
                peer.execute(
                    "UPDATE audit_events SET detail_json='[]' WHERE event_id=$1",
                    &[&audit_id(*a).to_string()],
                )
                .await
                .unwrap();
                if let Some(f) = m.audits.get_mut(a) {
                    f.corrupt = true;
                }
            }
            Command::InsertOrphan(i) => {
                if let std::collections::btree_map::Entry::Vacant(entry) = m.audits.entry(i.a) {
                    peer.execute("INSERT INTO audit_events VALUES ($1,$2,'canary.note.created','canary-note',$3,'{}',$4)",&[&audit_id(i.a).to_string(),&i.principal(),&note_id(i.n).to_string(),&i.t]).await.unwrap();
                    entry.insert(AuditFact {
                        intent: i.clone(),
                        corrupt: false,
                    });
                }
                observe(store, &m, i).await?;
            }
            Command::List(p) => {
                let _ = p; /* compare checks both principals */
            }
        }
        compare(store, peer, &m).await?;
    }
    Ok(())
}

// Shrink-derived concrete regressions remain stable even if the generator
// evolves and persisted random seeds yield different traces.
#[tokio::test]
async fn known_model_counterexamples() {
    let (store, peer) = support::fixture().await;
    let make = |n, a| Intent {
        n,
        a,
        p: false,
        c: "".into(),
        t: 0,
    };
    let traces = [
        vec![Command::Execute(make(0, 0))],
        vec![Command::Execute(make(0, 2)), Command::Execute(make(1, 2))],
        vec![
            Command::InsertOrphan(make(3, 2)),
            Command::Execute(make(3, 0)),
        ],
    ];
    for trace in traces {
        check_trace(&store, &peer, &trace).await.unwrap();
    }
    println!("three shrink-derived concrete regressions replayed");
}

#[test]
fn generated_native_trajectories() {
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let (store, peer) = runtime.block_on(support::fixture());
    let cases = std::cell::Cell::new(0usize);
    let transitions = std::cell::Cell::new(0usize);
    let seed = std::env::var("WEB_NOTE_TEST_SEED")
        .ok()
        .map(|s| s.parse::<u64>().expect("u64 seed"))
        .unwrap_or(20261126);
    println!("generated native model seed: {seed}");
    let config = Config {
        rng_seed: proptest::test_runner::RngSeed::Fixed(seed),
        failure_persistence: Some(Box::new(
            proptest::test_runner::FileFailurePersistence::Direct(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/stateful.regressions"
            )),
        )),
        cases: 48,
        max_shrink_iters: 256,
        source_file: Some(file!()),
        test_name: Some("generated_native_trajectories"),
        ..Config::default()
    };
    let mut runner = TestRunner::new(config);
    let outcome = runner.run(&prop::collection::vec(command(), 1..33), |commands| {
        runtime.block_on(async { check_trace(&store, &peer, &commands).await })?;
        cases.set(cases.get() + 1);
        transitions.set(transitions.get() + commands.len());
        Ok(())
    });
    match outcome {
        Ok(()) => {}
        Err(proptest::test_runner::TestError::Fail(reason, input)) => panic!(
            "model counterexample: {reason}; minimal failing input (bounded shrink): {input:?}"
        ),
        Err(other) => panic!("property runner failed: {other:?}"),
    }
    let cases = cases.get();
    let transitions = transitions.get();
    println!(
        "generated native model: {cases} successful traces, {transitions} transitions; both principal projections and exact peer Note/Audit after each"
    );
    assert!(cases >= 48 && transitions >= 48);
}
