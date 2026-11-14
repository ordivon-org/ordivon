# Ordivon Agent-native Source & Causal Graph R1 — Golden Road

Date: 2026-11-14. Status: **consumer-rooted architectural guidance plus one bounded existing-Composition source-impact improvement**; NOT a new Owner, service, registry, graph database, historical recovery guarantee, or Production approval.

## Outcome and first principle

A real Agent needs to answer three questions from *current owner facts*:

1. **What changed, and which real consumers must reconsider their result?**
2. **Why is a claim/result believed, which source/observation/version supports it, and what is still UNKNOWN?**
3. **After a crash/disconnect, which prior decisions are safe to project/replay, and which physical effects must be observed or reconciled?**

The answer is not one universal `Node`/`Edge` truth database. It is an **Agent-oriented, task-local read model** over existing source and causal authorities. A picture (SVG/Mermaid/UI) is only one projection and does not create missing relationships. One Git `SHA`, one successful Job, or one relation name never implies semantic equivalence, complete dependency closure, authorization, replayability or physical effect completion.

## Distinct projections; never conflate their truth

| Question | Grounded source authority / existing capability | Edge or temporal semantics | Non-claim |
| --- | --- | --- | --- |
| Which exact source changed? | Native Git object/tree/DAG; `tools/repo/source_history_legos.py` | exact commit ancestry, file values, namespace *member set* | Git change is not installed change |
| Which consumers are impacted? | Natural owner declares readset; Composition `verification_impact.py` | typed positive read edge, namespace-membership negative dependency, reverse transitive impact, UNKNOWN propagation | unobserved readers are not absent |
| What changed between relationships? | Composition prior/current proof obligations; Owner contract versions | added/deleted relation, changed obligation digest, cyclic dependency assumptions | source equality is not graph equality |
| Which Agent knows what / where to resume? | Host PG Work/Space/Topic/MessageRelation/attention cursors | semantic and social history, ordered consumption positions | a reference is not authenticated identity or physical effect |
| Did a command execute? | Runtime PostgreSQL Job/Attempt + native runner observations | accepted/starting/running/terminal/lost, exact local execution receipt | `starting` is dispatch intent, not a launched process |
| Did an external action take effect? | Gateway observation + natural effect owner/provider readback | operation identity, original effect observation, reconciliation state | process exit 0 does not prove provider effect |
| Which result/evidence is relevant? | Media Production/Claim/Output; Research Study/Hypothesis/experiment data; Finance investment study/ledger; Artifact native bytes | produced/consumed/supportedBy/contradictedBy edges scoped to each Owner | cross-owner references do not transfer truth authority |
| Which live environment was used? | Network, Workstation, Security, Runtime, external providers | time-scoped observation and revocation/currentness | same hash at two instants does not establish continuity |

Use `recursive-lego-calculus`, `compositional-contracts` and `design-structure-matrix` method Skills for actual substitution, unclosed assumptions and graph cycles. Keep one source of each fact with its natural owner. Use Agent-visible L0 (problem/owner/status), L1 (typed edges), L2 (cut and counterexample evidence), L3 (source implementation) views **of the same authority**, not a new independent index of truth.

## Five high-value relationship kinds

- **READS/DEPENDS_ON:** a named consumer requires a specific source, configuration, executable or provider observation. The *declared* readset must be annotated with observed/completeness status, not asserted globally complete by convention.
- **ENUMERATES_MEMBERS_OF:** a consumer reads *the membership set* of a Git directory/prefix. A newly added provider or fixture invalidates this consumer even if no previous member's bytes changed. `dependsOnScopeMembership` on Composition's existing readset bridge uses the native Git `membershipRef` rather than a custom hashing mechanism.
- **PRODUCES/SUPPORTS/REFUTES:** connects an output/claim to its real inputs and evidence; a test/proof PASS applies only to the modeled property and exact qualified SourceCut.
- **CAUSED_BY_OPERATION/OBSERVED_AS:** connects a specific effect attempt with its original native observation, keeping `UNKNOWN` after ambiguous dispatch; never turn a correlation edge into a proven effect.
- **SUPERSEDES/VALID_DURING:** records relation and assertion version changes, including historical deactivation and source version. Git ancestry is not sufficient for the mutable Host/Runtime/external-world timeline; the natural PG owner supplies that timeline.

A generic visual `RELATED_TO` is navigational only. It must never drive invalidation, retirement, recovery or authorization. Source refs and content digests are not interchangeable: stable business identity, Git object identity, literal source bytes, canonical semantic representation and attempt/effect identity are different coordinates.

## Business routine: update source -> determine minimal safe recheck

1. **Select a real consumer and two source cuts.** Require a specific Source owner and direction of ancestry for a before/after claim. For an implementation task, use the current Git cut, not an unqualified working tree.
2. **Ask Git for delta.** For example:

   ```bash
   python3 tools/repo/source_history_legos.py --repo . \
     --left f902a3f6f616d963931a35680a07b298e9aa8fb1 \
     --right 710bd0619bf3633cb8fc5b68e95e9d04bef350a4 \
     --impact-prefix platform/network/ --compact-impact
   ```

   This immutable two-cut query knows source files, byte/mode modifications and namespace additions/removals. It does not know runtime provider state.
3. **Ask the natural owner for a bounded consumer readset.** Use the existing `ordivon.source-readset-evidence` carrier and the `impact-readsets` Composition CLI. `sourcePaths` are literal selected members. Add `dependsOnScopeMembership: true` only for actual namespace enumerators (glob/discovery/all-providers) and keep `dependenciesComplete: false` for unqualified dynamic reads. Missing source/effect facts become UNKNOWN, not FALSE.
4. **Compute the impacted frontier** with existing `select_source_readset_impacts` / `select_impacted_obligations`. Priority is `RECHECK_REQUIRED`, then `UNKNOWN`, then `REUSE_CANDIDATE`. `REUSE_CANDIDATE` means **source recheck selection only**; it is NEVER a verifier PASS, an installed-current result or permission to suppress a domain test.
5. **Recheck only the necessary real consumers**, with their native tools/Skills. Record implementation/proof/physical/output acceptance separately. New or changed relation contracts count as changes even when source blobs are equal.
6. **Commit the result with the source Owner** and expose the existing natural Owner readback to Agent/Harness. Do not install another project-wide graph store or force all Owners to write rows into Host.

### Executed real Network-cut witness

SourceCut: merge of `feat/network-consumer-fault-domain-20261114-r1`, from `f902a3f6...` to `710bd061...`, compared by the original native Git reader. Four changed Network paths were observed: `Taskfile.yml`, `consumer.rules.yml`, `docs/AGENT_GUIDE.md`, and newly added `tests/fixtures/network-fault-domain-alerts.test.yml`. Native Composition R1 (with `dependsOnScopeMembership`) selected:

| Scoped task-local readset | Source impact |
| --- | --- |
| The new network fault-domain alert fixture plus consumer rule & Taskfile | `RECHECK_REQUIRED` |
| Full Network source namespace membership query | `RECHECK_REQUIRED` |
| Unchanged `config/sing-box/direct.json` *source bytes only* | `REUSE_CANDIDATE` |
| VPN provider's actual live operation relying on source config | `UNKNOWN` |

This is a real Git content/consumer-path check plus **caller-authored example readset**, not owner-certified complete installed consumption. In particular, the fourth row is not a real VPN connectivity probe. The independent direct/VPN failure-domain alarm's true cause remains outside this source graph.

## History, replay, recovery, hashes: the hard boundaries

- **History:** preserve original owner event order and validity interval. A snapshot is a projection at a cut, not proof of earlier revisions' existence once pruning has occurred. A reconstructed graph may say `NOT_OBSERVED`; it must not invent an old edge.
- **Pure replay:** deterministic inputs + code version + recorded nondeterministic decisions can replay *decisions/state projections*. LLM calls, wall-clock time, randomness, network, filesystem and database reads must be recorded or carried as separately observed Activities. Mature reference: Temporal's Workflow/Activity distinction; this is guidance to reuse existing providers, not an instruction to replace Ordivon Harness.
- **Physical recovery:** `Runtime starting` may be dispatch intent only. Never resubmit an ambiguous external effect solely because the graph lacks a terminal edge. Use original Job/Attempt observation, reconciliation, native effect owner readback, and risk-tiered retry.
- **Hashes:** reuse Git OIDs for Git blobs/trees and Artifact's selected blob digests; use canonical semantic digest only for a source-defined model/schema. Distinguish **same bytes**, **same meaning**, **same operation**, **same effect**, **same installed state**, **same approval**. Do not hash every edge, per-message thought or UI view as a new truth store.
- **Incremental correctness:** selecting the transitive downstream of changes is safe only relative to a *closed and qualified* readset. A missing dependency (or unqualified directory glob, mutable external resource, environment override) invalidates exactness; report UNKNOWN and requalify.
- **Consumer retirement:** a missing edge in a bounded search cannot justify deletion. Follow `recursive-lego-calculus` consumer closure premises and independent original source/Artifact readback before retirement.

## Q1/Q2 rollout grounded in actual consumers

| Priority | Consumer | First economical action | Acceptance boundary |
| --- | --- | --- | --- |
| Q1 | Repo/Composition | Keep the existing Git/Composition producer+selector; add namespace-member readset edge (this change) | real Git delta + negative-added-member consumer test |
| Q1 | Runtime/Gateway/Harness | Expose existing linked Run/Attempt/ToolCall/OperationRef + outcome as **read-only projections**, not a second EventStore | `starting`/`lost`/unknown-effect counterexamples, no duplicate side effects |
| Q1 | Host | Reuse PG Work/MessageRelations/Attention cursor as semantic continuity, not runtime effect truth | resume from exact cursors without invented earlier messages |
| Q1 | Network/Security | Link the actual consumer probes, source profile and credential/effect identity; separate observation from causal diagnosis | source change triggers selected rules tests; live VPN remains separately measured |
| Q1 | Media/Research/Finance | Reuse source-bound Claim→evidence→output / Study→dataset→result / investment research→paper ledger links | reject unsupported claims; preserve frozen approved outputs and financial provenance |
| Q2 | Other Owners (Artifact, Skills, Workstation, Game) | Add edges only when a concrete consumer needs incremental scope, reproducibility or collaboration | measurable reduction of redundant reads/rechecks, no new authority or global glue |
| Hold | Universal Graph DB, mandatory EventStore, monolithic Visual IR, global hash registry | No justified adoption at this cut | require cross-owner consumer counterexample and proven savings first |

## Mature foundations and business validation

- Bazel Skyframe: immutable key/value dependency graph, reverse change propagation, explicit dependency registration and change pruning. Main lesson: **an undeclared read ruins incremental correctness**.
- Nix derivations: specify executable and exact inputs before deriving outputs; provenance identity is not business semantic equality.
- OpenLineage: Run/Job/Dataset lineage and explicit per-output dependencies, avoiding false Cartesian-product edges between unrelated inputs and outputs. Use where a real Research/Media/data consumer exists.
- Temporal: deterministic Workflow history replay plus Activities for nondeterministic external effects; replay of one state machine is not a guarantee of exactly-once external-world effects.
- DSM / assume-guarantee: diagnose cyclic dependencies and consumer gaps before changing module boundaries; local correctness without discharged assumptions never promotes the whole system.

**Measurement:** at least one actual SourceCut and named real consumer per Owner; compare redundant read/verification count, false-negative recheck count, aggregate effect/scheduler resumes, and re-entry usability before/after. Do not claim productivity gains without measured baselines. Do not perform a one-shot whole-system migration or archive/cleanup solely on a diagram.
