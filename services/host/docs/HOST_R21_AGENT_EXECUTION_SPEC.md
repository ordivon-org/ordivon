# Host R2.1 Contract-Driven Execution — Specification

Status: execution specification; source-bound, not installed policy or new authority
SourceCut: `3b43977e682d8c7668f6371ffd998c7821e4312a` (GitHub main, 2026-11-09 20:50 CST)
Natural owner: `services/host`
First consumer: Host Work continuation, Host `host.status` Doctor, Gateway Host tools, Host PostgreSQL tests
Method sources: local `matt-native/domain-modeling`, `matt-native/tdd`, `ecc-native/ai-regression-testing`, `ecc-native/blueprint`, `obra-superpowers/writing-plans`, `obra-superpowers/verification-before-completion`; Ordivon `recursive-lego-calculus`.
Truth boundary: Source declarations below are not Runtime jobs, installed Host releases, or domain completion.

## 1. Problem and non-goals

Live Host demonstrated an actual semantic contract conflict: `host.status(detail=integrity)` reported healthy, but `detail=history` reported `work.snapshot_history_contiguous invalidWorks=3`. Some Work historical revisions returned CONFLICT. A time-based backlog hygiene action also terminalized an unfinished Windows PostgreSQL production-cutover Work; a replacement Work had to carry its live goal. These are **two different faults**: history storage/read contract drift and Work/Goal lifecycle confusion.

Goal: permit low-context Agents to implement useful Host changes without redefining the work's external goal, losing real consumers, fabricating evidence, or hiding a necessary next action under generic caution.

The kernel is already present: R2.1 contracts, Owner-native APIs, PostgreSQL transactions, the normal Git/CI flow and official Skills. Do not install a new universal contract compiler, agent policy engine, history service, ORM, task router, safety approval queue, cross-owner Goal database or synthetic evaluation framework. Do not run weak-model comparisons. Do not mutate production Host Work merely to make Doctor green.

## 2. Domain language and ownership

- `Goal`: desired external/domain effect; truth and lifecycle owned by the actual Goal/domain system, **not Host**. Host references do not establish a Goal's existence, progress or termination.
- `Work`: versioned Host-local semantic continuity record; `open/completed/abandoned` represent Host continuity disposition, not effect, Git merge or Goal standing.
- `WorkSnapshot`: immutable payload at a revision with SHA-256 of canonical JSON. Current revision requires a matching payload/digest.
- `History`: actual retained revisions. Availability and integrity are distinct: no fabricated revision or silent backfill.
- `Retention`: storage decision for Host-owned records. A four-hour idle threshold is **only a candidate observation**, never authority to call `work.snapshot.commit(continuityDisposition=abandon)`.
- `Reference`: foreign owner navigation/correlation only. Native readback is required to assert its actual effect.
- `Verified`: evidence for exactly a stated property, source revision and environment; not general completion.
- `UNKNOWN`: scoped absence of enough evidence, not a substitute for PASS or FAIL.

The actual owner graph is Host(Work/Social/Attention), Runtime(Job/Attempt), Git(Source), Artifact(Content), Security(authorization), domain Owner(Goal/outcome), Gateway(routing), Harness(agent cognition). No second database of their truths.

## 3. R2.1 contract obligations (three independently contractable responsibilities)

A formal `DECLARED` LEGO must include all eleven coordinates; typed UNKNOWN blocks only the dependent proof.

### H01 — WorkContinuityCAS (existing implementation; preserve)

`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`

- `I`: typed `(workRef, expectedRevision: int64, snapshot: WorkSnapshotInput, actorRef, clientRequestId, continuityDisposition)`.
- `O`: committed/existing typed Work response or typed conflict.
- `S`: Host PostgreSQL `works`, `work_snapshots`, `command_receipts`.
- `pre`: validated actor/payload; new mutation expects open Work at exact expected revision, with increment within signed BIGINT.
- `post`: new mutation increments exactly one revision, stores canonical digest, current pointer matches, returns authoritative Host result; replay returns historical receipt.
- `inv`: revision strictly monotone; current snapshot readable; terminal Host state cannot be reopened through normal CAS; **no implication** about Goal outcome.
- `eff`: Host-only transactional row mutation; no Runtime or domain effects.
- `c`: `UNKNOWN(performance, database/workload, require measured plan)`.
- `epsilon`: zero for exact discrete CAS postcondition *conditional on committed PostgreSQL transaction*; environmental availability remains `UNKNOWN`.
- `prov`: `work_store.py`, `work_queries.py`, PostgreSQL integration/consumer tests; installed outcome separately read back.
- `unfold`: Pydantic inputs -> MCP adapter -> `WorkStore.commit_snapshot` -> native PG transaction.

### H02 — HistoryObservability (existing contract; make it coherent)

- `I`: `(detail: summary|integrity|history, Work read revision: optional int64)`.
- `O`: Host status health/checks and exact Work read or typed missing-revision conflict.
- `S`: Host PG `works`, `work_snapshots`, current pointer.
- `pre`: schema version verified; read at one appropriate PG consistency boundary.
- `post`: current pointer checks never assert full history; a full history check reports its actual result; no missing historical revision is fabricated.
- `inv`: detail=history detects incomplete historical sequences under **current full-history contract**; canonical JSON digest errors remain detectable; detail=integrity may not conceal full-history corruption when it claims that property.
- `eff`: read-only SQL/projection.
- `c`: `UNKNOWN(latency, size of PG history)`; keep full payload rehash under explicit `detail=history`.
- `epsilon`: zero for evaluated exact PG predicate within snapshot scope; installed-currentness UNKNOWN unless native readback.
- `prov`: `service.py`, `work_queries.py`, `test_social_work_fabric_postgres.py`, `host.status(detail=history)`.
- `unfold`: status query -> grouped sequence predicate -> typed Doctor check. Histories are not implicitly pruned by a changed Doctor query.

### H03 — Consumer-RootedRetention (design contract; not yet deployed)

- `I`: Host candidate IDs, bounded stable snapshot/consumer edges, observed last-activity, explicit approved retention mode.
- `O`: candidate set and (only after independent consumer validation) Host-only deletion/compaction receipts, or UNKNOWN.
- `S`: Host-owned Work/Snapshot/Social relations; foreign owners' actual references read via native interfaces.
- `pre`: candidate classification and consumer closure/currentness witnesses; active Goal state never inferred from age.
- `post`: approved obsolete Host records cease occupying active scope without changing domain Goal or Runtime Job.
- `inv`: `HostRetentionEffect ∩ ForeignGoalRuntimeEffect = ∅`; terminal `abandon` never triggered solely by age; missing proof leads to UNKNOWN not fabricated `no consumer`.
- `eff`: bounded Host PG mutations only; production mutation is outside this initial source slice.
- `c`: `UNKNOWN(cost by affected rows/locks)`; prefer native PG set operations; no per-record bureaucracy.
- `epsilon`: exact non-interference under verified effect/frame boundary; consumer-observation completeness remains `UNKNOWN` until independently established.
- `prov`: existing `tools/formal/RecursiveLegoRefinement.lean` conditional retirement theorem; PostgreSQL FKs; native owners' evidence; future retention integration tests.
- `unfold`: candidate query -> real consumer/owner readback -> transaction/dry-run -> retention realization -> native owner re-read.

H03 is **DECLARED** only. Its implementation, consumer closure and production effect are explicitly not proven.

## 4. Acceptance properties and falsifiers

| ID | Requirement / observable outcome | Real seam | Negative control |
| --- | --- | --- | --- |
| R01 | `mise run test:focused` executes an actual checked-in default test file | Host mise task | Missing filename fails with exit !=0 |
| R02 | README default test pointer exists | current filesystem + native entrypoint | stale path rejected |
| R03 | `host.status(detail=history)` reports missing 1..revision history as unhealthy | Host public status + disposable PostgreSQL | current snapshot valid but prior missing |
| R04 | No Doctor mode advertises **full history** healthy while relevant checked history is incomplete | Host status | inject omitted historical revision |
| R05 | Work CAS remains atomic/idempotent and revision increments only under current open Work | Host PG Work API | stale expectedRevision / concurrent writer |
| R06 | Four-hour inactivity alone never calls terminal Host abandon nor asserts Goal cancellation | actual cleanup consumer, once identified | live P0 Work older than four hours |
| R07 | Host retention does not own foreign Runtime Job or domain Goal effects | real owner and effect SQL | fake reference, Job still running |
| R08 | any altered retention/historical contract keeps exact old-revision read/error semantics, without fabricated history | Work.get | known-missing revision |
| R09 | Source tests and formal obligations never substitute for installed/consumed proof | CI + deployment readback | non-installed source PASS |
| R10 | no redundant registry, owner table, universal safety engine, extra skill copy or pointless doc consumer | Git diff + architecture checks | self-referential-only carrier |

## 5. Implementation choices and constraints

1. Preserve `services/host` as natural Owner; new tests only against its public Host/MCP/PG behavior, with existing internal pure proofs only where appropriate.
2. Fix the already-proven focused-test path bug first as an immediate production-engineering benefit.
3. Make the history defect visible and provide regression coverage, **not** a fake PASS by weakening Doctor or manufacturing deleted revisions. First source slice must leave production PG unchanged.
4. Before choosing a bounded-history design, explicitly inspect all revisioned-read consumers. If no consumer needs full historical sequence, introduce a genuine native retention policy with explicit retained floor and typed unavailable history; changes to old API/schema require separate PG migration and consumer qualification, not an unannounced Doctor relaxation.
5. Under no circumstances treat idle Work as authority to abandon a live Goal. Cleanup of an inactive *view* and terminal Work semantic update are distinct operations.
6. Delete obsolete plans/docs once their actual consumers are migrated. A test referencing an old file does not alone confer business value; preserve active Alembic migration chain.
7. Respect `SKIP != PASS`, `UNKNOWN != FAIL`, no invented production-readback, independent specification/standards review, exact Git/Artifact evidence.
8. Do not introduce model-tier benchmark, model holdout, or model capability experiment.

## 6. Delivery split, dependencies and acceptance

- **Slice A (immediately executable):** correct broken focused-test entrypoint and consumer documentation; run RED on current task, apply fix, run GREEN, Ruff/check. SourceOnly until merge.
- **Slice B:** read-only Doctor history completeness visibility and regression on disposable PG. No database rows edited. This is a code/PG correctness repair, not history cleanup.
- **Slice C:** actual historical consumer graph, retention-floor design decision, and **only if earned** schema/Work.get adaptation with dedicated tests; otherwise retain full-history contract and restore only provable authoritative history.
- **Slice D:** separate Host garbage-collection from Goal standing, adopt set-based PG cleanup with explicit plan & current-closure proof, no accidental external effect; measure actual consumers.
- **Slice E:** retire stale docs and parallel representations; replay Gateway/Host consumers, run owner native verify, formal source proofs, PG disposable integration, and installed Host readback.
- **Slice F:** merge and observe actual deployment; no fabricated SOURCE→INSTALLED→CONSUMED transition.

Dependency graph: `A -> B -> C -> D -> E -> F`. Independent doc consumer cleanups may proceed after A, but may not rewrite contracts outside Host. Every slice has its own acceptance, failure mode and rollback (Git revert for source, native Alembic plan for schema, PG transaction rollback for uncommitted effect).

## 7. Current known evidence and status (source-bound)

- In a previous Host online readback (2026-11-09), `integrity` passed while `history` failed with three incomplete Works; current production status must be read again at closure.
- `mise run test:focused` **failed** on SourceCut with exit code 4: `tests/test_canonical_property.py` does not exist; the actual file is `tests/test_canonical_json_property.py`.
- Source code's `work_snapshot_history_contiguous` predicate remains current full-history contract. This spec does not authorize silently weakening it.
- Exact Git source and local Skill digest identify inputs; no production delete, terminal update, deployment or domain acceptance has yet been performed by this document.

## 8. Upstream methods used

- Matt Pocock Skills: Domain Modeling, TDD, To-Spec/To-Tickets, Code Review — https://github.com/mattpocock/skills
- Everything Claude Code: Blueprint, AI Regression Testing — https://github.com/affaan-m/ECC
- obra/superpowers: Writing Plans, TDD, Verification Before Completion — https://github.com/obra/superpowers
- PostgreSQL: MVCC / transaction constraints — https://www.postgresql.org/docs/current/mvcc.html
- Ordivon Recursive LEGO Calculus R2.1: `.agents/skills/recursive-lego-calculus/SKILL.md`.

The upstream Skill is a **method**: installed Skill provenance, actual source, and Owner native effect remain separate.

## 9. Mathematical foundations and proof boundary (2026-11-09 refinement)

This section **refines H01–H03**, not a new LEGO calculus or Agent controller. The existing R2.1 `ell` eleven-coordinate tuple is the semantic carrier; each theorem or test has an exact owner, hypothesis and witness. The notation describes *obligations to discharge*, not already proved implementation facts.

### 9.1 Safety and conditional liveness (Lamport)

Let `S` be Host state, `F` foreign Goal/Runtime state, `T` an observed transition and `Retain` a Host-local cleanup action. Desired safety:

```text
S1 (direct frame):   Retain(S,F) = (S',F')  =>  F' = F
S2 (no inference):   Work.state = abandoned  -/-> Goal.standing = cancelled
S3 (read truth):     work.get(w,r)=success   =>  snapshot(w,r) exists and digest matches
S4 (no fabrication): missing(w,r)  =>  no success projection of revision r
```

S1 can be proven locally only when implementation effect/readset boundaries are actually closed; a process-level `Host` claim does not establish absence of downstream consumers that might react to an abandoned Work. The **cross-owner** S2 is a consumer contract and requires actual Goal/Runtime readback. Source and tests do not prove installed/current behavior.

Liveness is not `every unfinished Goal eventually succeeds`. Under an explicitly named scheduler/environment fairness assumption `A_fair`, require that each *admitted, executable* Host task either makes an observable owner-grounded transition or returns an actionable, evidence-bound block. No fair scheduler has been proved for this Host; claiming unconditional `<>Success` is invalid. Existing Runtime/Harness, not Host, owns execution progress. Lamport's safety/liveness distinction therefore prevents both false success and inert overconservatism without forcing a universal policy engine.

### 9.2 Abstract-to-implementation refinement (Abadi–Lamport)

Define abstract `H = (WorkRef, Revision, SnapshotAvailable, HostState, ForeignRefs)`; concrete `P` is the actual PostgreSQL tables. A candidate abstraction `alpha: P -> H` maps current Work and committed revisions to the abstract state. Each observed mutating PG transaction must simulate exactly one admitted abstract Host action or an allowed stutter transition; missing revisions must not be mapped to invented snapshots.

```text
P0 in ConcreteValid
PG_Transaction(P0, P1) and Refined(P0)
   => (AbstractStep(alpha(P0), alpha(P1)) or alpha(P0) = alpha(P1))
```

Necessary but not sufficient: model invariants, SQL transaction behavior, consumer interface readback, installed code currentness and assumption currentness. Historical `work.get(r)` needs a separate observation refinement to actual stored rows. A model-checking PASS alone cannot prove the implementation.

### 9.3 Assume–guarantee and effect/frame conditions

For composed `Host H`, `Runtime R`, `Gateway G` and `Domain D`:

```text
A_H: caller supplies a valid Work revision and known principal
G_H: returned Work identity + digest are Host-local, not domain completion
A_G: Host interface really bound to installed Owner and current tool contract
G_G: routes/transport do not translate Host completion into domain success
A_R: native Job identity and attempt readback available
G_R: process execution disposition, not semantic success
A_D: domain-specific outcome oracle available
G_D: actual accepted outcome or typed UNKNOWN/FAIL
```

Composition is justified only with compatible assumptions/guarantees and actual effect/authority boundaries (interface shape alone is insufficient). In particular, Gateway transport success does not strengthen `G_H` into `G_D`. The relevant mature theory is de Alfaro–Henzinger interface automata and contract-based composition.

### 9.4 Consumer closure is a *conditional* theorem, not age-based deletion

Let `R(w)` be *all* reachable consumer edges for a Work and `L` the set of live/required consumers. An empty observed query cannot establish `R(w) ∩ L = ∅`. The existing `tools/formal/RecursiveLegoRefinement.lean` theorem may be reused only if all of the following are evidenced for the affected scope:

```text
closed(ObservedEdges, ReachableEdges)
AND CurrentEdges ⊆ SnapshotEdges
AND CurrentLiveConsumers ⊆ SnapshotLiveConsumers
AND no observed reachable live consumer
=> no actual reachable live consumer within this closed scope
```

A Work older than four hours supplies none of these hypotheses. When any closure/currentness premise is unknown, the appropriate output is `UNKNOWN(scope, missing-proof)`, not `DELETE` or `ABANDON`. This is a mathematical refusal of a bad inference, **not** a demand to manually inspect every garbage row: for truly Host-only records, native FK constraints and a single bounded SQL transaction may efficiently establish/execute a set-based retirement after ownership is known.

### 9.5 History semantics: explicit policy, not Doctor greenwashing

Current source `HostV2.status` defines full-contiguous history (`1..currentRevision`) for each persisted Work. The observed production five Work IDs yield three `revision=1` conflicts: the two abandoned legacy Runtime cutover Works and completed Host SourceCut acceptance Work. The two continuation Works retain revision 1. Thus `work.current_snapshot=ok` and `work.snapshot_history_contiguous=error invalidWorks=3` are compatible facts, not a contradiction in PG implementation.

Two consistent long-term options:
- **A: Full history.** Keep the current exact contract; restore *only authentic* missing snapshots if there is a valid authority, otherwise retire whole obsolete Work after real consumer closure. Do not backfill fabricated historical values.
- **B: Explicit bounded retained history.** Version the Work read/Doctor contract so each persisted Work exposes a provenance-backed `retainedFromRevision`; exact retained suffix is contiguous, historical absence below that floor is typed *unavailable* (not success, not corrupted), and all existing revisioned-read consumers remain correct. This requires actual native PG schema migration, read contract changes and consumer qualification; it cannot be implemented by changing the Doctor predicate alone.

Current decision: **retain exact full-history diagnostics until the consumer and migration basis is established**. Both options have different preservation and backward-compatibility assumptions. Neither should be selected merely to produce a green status.

### 9.6 Why these sources rather than a new framework?

- Lamport, *Proving the Correctness of Multiprocess Programs* (1977) — https://www.microsoft.com/en-us/research/publication/proving-correctness-multiprocess-programs/
- Lamport, *The Temporal Logic of Actions* (1994) — https://lamport.azurewebsites.net/tla/papers.html
- Abadi & Lamport, *The Existence of Refinement Mappings* (1988) — https://www.microsoft.com/en-us/research/publication/the-existence-of-refinement-mappings/
- de Alfaro & Henzinger, *Interface Automata* (2001) — https://doi.org/10.1145/503209.503226
- AWS, *How Amazon Web Services Uses Formal Methods* (2015) — https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods
- Existing Ordivon `.agents/skills/recursive-lego-calculus/SKILL.md` and `tools/formal/RecursiveLegoRefinement.lean`.
- Engineering workflow: Matt Pocock to-spec/domain-modeling/TDD; ECC Blueprint/AI Regression Testing; obra Superpowers writing-plans/verification-before-completion. Existing tests and clean PR deltas are the execution substrate.

No weak-model experiment, benchmark matrix, model-tier ranking or new universal orchestrator is part of this project.

### 9.7 Abstract interpretation, information order and CEGAR

Cousot–Cousot abstract interpretation explains how a tractable abstraction may soundly overapproximate concrete behaviors, but its uncertainty cannot be interpreted as evidence of falsehood. For any proposition `p` about a consumer, define an **epistemic** information order:

```text
                   VERIFIED_TRUE       FALSIFIED
                         ^                 ^
                         |                 |
                         +------UNKNOWN----+
```

This is a partial order of *evidence precision*, **not** a numerical risk score or a new database state machine. If an observation is insufficient, `UNKNOWN` remains a first-class result. Fresh counterevidence may invalidate a previous proof by changing its source/assumptions; do not turn stale `VERIFIED_TRUE` into timeless truth.

A CEGAR-inspired *engineering* loop is only:
`model property → look for concrete counterexample → reject spurious counterexamples using exact assumptions → refine the narrowest owner contract → re-run implementation readback`.
It does not require building a generic abstract interpreter. In this Host case, the concrete counterexample is `current_snapshot=ok` while `historical_revision_1=CONFLICT`; the smallest justified refinement is scope-correct Doctor and typed missing-history behavior, rather than a second Host history authority.

- Cousot & Cousot, *Abstract Interpretation* (POPL 1977) — https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml
- Clarke et al., *Counterexample-Guided Abstraction Refinement* (CAV 2000) — https://web.stanford.edu/class/cs357/cegar.pdf
- Herlihy & Wing, *Linearizability: A Correctness Condition for Concurrent Objects* (TOPLAS 1990) — https://www.cs.cmu.edu/~wing/publications/HerlihyWing90.pdf

### 9.8 Bounded complexity and mathematical engineering selection

Select the smallest sound representation **per actual responsibility**:
- Work CAS/receipt: typed Hoare contract + PostgreSQL transaction/concurrency tests (linearisability required where concurrent API is claimed).
- History availability: simple relational predicate, exact digest readback and negative tests; no event sourcing rewrite by default.
- Cross-owner composition: assume–guarantee contract and explicit authority/effect frames; no invented global Goal table.
- Data retirement: conditional graph-reachability closure and native PG/FK set operations; no atom-by-atom manual garbage bureaucracy.
- Execution liveness: only actual Runtime/Harness fairness/availability facts; no Host scheduler added.
- Pure transitive/DAG properties: existing Lean theorem/Z3 counterexamples, with scoped source refinement and installed behavior separately.
- Agent implementation: Matt TDD at existing public seam → ECC counterexample regression → Superpowers completion evidence. No requirement that all three skills execute as nested workflows.

Before adding a new theorem, field, tool, migration, or Skill, state an actual owner/consumer counterexample that the present implementation does not handle. Otherwise prefer DELETE/REUSE rather than adding another formal obligation.
