use super::fixture::{NOW, create, grant, request, setup};
use ordivon_web_note_pg::{PgNoteStore, effect::EffectOperation};
use tokio_postgres::Client;
use uuid::Uuid;
// Independent abstract state, not the production GrantRow/Effect predicates.
#[derive(Default)]
struct Model {
    receipts: std::collections::BTreeMap<u8, (usize, bool)>,
    notes: [Option<bool>; 2],
    consumed: [bool; 2],
    used: [i64; 2],
    active: [bool; 2],
}
impl Model {
    fn fresh() -> Self {
        Self {
            active: [true, true],
            ..Self::default()
        }
    }
    fn step(
        &mut self,
        id: u8,
        g: usize,
        stale: bool,
        alternate: bool,
        foreign: bool,
    ) -> &'static str {
        if let Some(&(_, digest)) = self.receipts.get(&id) {
            return if foreign {
                "effect-actor-mismatch"
            } else if digest != alternate {
                "effect-conflict"
            } else {
                "replay"
            };
        }
        let publish = id >= 2;
        if stale || !self.active[g] || self.used[g] == 3 || (publish && alternate) {
            return if publish {
                "effect-fence-rejected"
            } else {
                "agent-grant-changed"
            };
        }
        if foreign {
            return "agent-effect-not-authorized";
        }
        let n = usize::from(id % 2);
        if publish {
            if self.notes[n] != Some(false) {
                return "canary-note-not-publishable";
            }
            self.notes[n] = Some(true);
            self.consumed[n] = true;
        } else {
            self.notes[n] = Some(false);
        }
        self.used[g] += 1;
        self.receipts.insert(id, (g, alternate));
        "new"
    }
}
type Command = (u8, usize, bool, bool, bool);
async fn model_trace(
    store: &PgNoteStore,
    peer: &Client,
    commands: &[Command],
) -> Result<(), proptest::test_runner::TestCaseError> {
    use proptest::{prop_assert, prop_assert_eq};
    peer.batch_execute("TRUNCATE agent_effects,canary_notes,audit_events; UPDATE agent_grants SET remaining_effects=3,revision=1,active=1; UPDATE effect_approvals SET consumed_at=NULL").await.unwrap();
    let mut model = Model::fresh();
    for &(id, g, stale, alternate, foreign) in commands {
        let grant_id = ["g1", "g2"][g];
        if id == 4 {
            peer.execute("UPDATE agent_grants SET active=0,revision=revision+1 WHERE grant_id=$1 AND active=1",&[&grant_id]).await.unwrap();
            model.active[g] = false;
        } else {
            let label = ["E", "F", "P", "X"][usize::from(id)];
            let n = usize::from(id % 2);
            let note = Uuid::from_u128(100 + n as u128);
            let mut req = request(label, id >= 2, note);
            if alternate {
                req.effect_digest = "alternate".into();
            }
            if foreign {
                req.agent_id = "other".into();
            }
            let op = if id >= 2 {
                EffectOperation::Publish {
                    note_id: note.to_string(),
                }
            } else {
                create(note, if alternate { "alternate" } else { "draft" })
            };
            let revision = 1 + model.used[g] + i64::from(!model.active[g]) + i64::from(stale);
            let expected = model.step(id, g, stale, alternate, foreign);
            let outcome = store
                .commit_effect(&grant(grant_id, revision), &req, &op, Uuid::new_v4(), NOW)
                .await;
            let actual = match outcome {
                Ok(o) => {
                    if o.replayed {
                        "replay"
                    } else {
                        "new"
                    }
                }
                Err(ref e) => e.code(),
            };
            prop_assert_eq!(
                actual,
                expected,
                "command {:?}",
                (id, g, stale, alternate, foreign)
            );
        }
        // Independently observe every mutable coordinate after each operation.
        let rows = peer
            .query(
                "SELECT remaining_effects,revision,active FROM agent_grants ORDER BY grant_id",
                &[],
            )
            .await
            .unwrap();
        for (g, row) in rows.iter().enumerate() {
            prop_assert_eq!(row.get::<_, i64>(0), 3 - model.used[g]);
            prop_assert_eq!(
                row.get::<_, i64>(1),
                1 + model.used[g] + i64::from(!model.active[g])
            );
            prop_assert_eq!(row.get::<_, i64>(2), i64::from(model.active[g]));
        }
        for n in 0..2 {
            let row = peer
                .query_opt(
                    "SELECT state FROM canary_notes WHERE note_id=$1",
                    &[&Uuid::from_u128(100 + n as u128).to_string()],
                )
                .await
                .unwrap();
            prop_assert_eq!(
                row.map(|r| r.get::<_, String>(0)),
                model.notes[n].map(|b| if b {
                    "PUBLISHED".into()
                } else {
                    "DRAFT".into()
                })
            );
            let row = peer
                .query_one(
                    "SELECT consumed_at FROM effect_approvals WHERE effect_id=$1",
                    &[&["P", "X"][n]],
                )
                .await
                .unwrap();
            prop_assert_eq!(
                row.get::<_, Option<i64>>(0),
                model.consumed[n].then_some(NOW)
            );
        }
        let rows = peer
            .query(
                "SELECT effect_id,grant_id,effect_digest FROM agent_effects",
                &[],
            )
            .await
            .unwrap();
        prop_assert_eq!(rows.len(), model.receipts.len());
        for row in rows {
            let name = row.get::<_, String>(0);
            let i = ["E", "F", "P", "X"]
                .iter()
                .position(|s| *s == name)
                .unwrap() as u8;
            let Some(&(g, alt)) = model.receipts.get(&i) else {
                return Err(proptest::test_runner::TestCaseError::fail(
                    "unexpected receipt",
                ));
            };
            prop_assert_eq!(row.get::<_, String>(1), ["g1", "g2"][g]);
            prop_assert_eq!(
                row.get::<_, String>(2),
                if alt {
                    "alternate".into()
                } else {
                    format!("digest-{name}")
                }
            );
            let count=peer.query_one("SELECT count(*) FROM audit_events WHERE event_type='agent.effect.committed' AND object_id=$1",&[&name]).await.unwrap().get::<_,i64>(0);
            prop_assert_eq!(count, 1);
        }
        prop_assert_eq!(
            peer.query_one("SELECT count(*) FROM audit_events", &[])
                .await
                .unwrap()
                .get::<_, i64>(0),
            model.receipts.len() as i64
        );
        prop_assert!(model.used.iter().sum::<i64>() == model.receipts.len() as i64);
    }
    Ok(())
}
#[test]
fn generated_effect_authority_histories() {
    use proptest::{
        prelude::*,
        test_runner::{Config, RngSeed, TestRunner},
    };
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let (store, peer) = rt.block_on(setup("effect_model"));
    rt.block_on(model_trace(&store, &peer, &[(2, 0, false, true, true)]))
        .unwrap();
    let seed = 20261126;
    let config = Config {
        cases: 48,
        rng_seed: RngSeed::Fixed(seed),
        max_shrink_iters: 256,
        failure_persistence: Some(Box::new(
            proptest::test_runner::FileFailurePersistence::Direct(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/effect.regressions"
            )),
        )),
        ..Config::default()
    };
    let cases = std::cell::Cell::new(0usize);
    let transitions = std::cell::Cell::new(0usize);
    let strategy = prop::collection::vec(
        (
            0u8..5,
            0usize..2,
            any::<bool>(),
            any::<bool>(),
            any::<bool>(),
        ),
        1..25,
    );
    TestRunner::new(config)
        .run(&strategy, |commands| {
            rt.block_on(model_trace(&store, &peer, &commands))?;
            cases.set(cases.get() + 1);
            transitions.set(transitions.get() + commands.len());
            Ok(())
        })
        .unwrap();
    assert!(cases.get() >= 48);
    println!(
        "independent Effect/Grant/Approval model seed {seed}, {} traces / {} commands",
        cases.get(),
        transitions.get()
    );
}
