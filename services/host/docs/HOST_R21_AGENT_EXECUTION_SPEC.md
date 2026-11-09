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


## 10. 2026-11-10 independent theoretical and consumer cross-audit (SourceCut 8346863)

This section *refines the existing Host Owner spec*, not the canonical cross-Owner `docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md`, nor a new global policy or control plane. The former source header `3b43977...` remains historical authoring provenance; the current code/evidence SourceCut for this review is `8346863be965da34371944679d063fd9fd0358ac`. Last verified GitHub: #1976 MERGED, #1992 MERGED, #1993 OPEN with overlapping global-doc work. Do not reopen already merged slices.

### 10.1 Theory selection with exact applicability boundaries

**Systems engineering / NASA V&V.** The system of interest is *continuity for real consuming agents*, not a database-table count. Technical verification (SQL FK/CAS/Doctor, Work.get, Space/Message navigation) and final validation (owner-native preservation of useful Goal/outcome) are separate. The actual stakeholder measure is re-entry into live obligations without false terminal completion; raw reduction in Work rows is an incidental process measure. Adopt NASA Verification/Validation trace matrices only as small requirement→native-test mappings, not as a universal document bureaucracy. Sources: https://www.nasa.gov/reference/2-0-fundamentals-of-systems-engineering/ and https://www.nasa.gov/reference/system-engineering-handbook-appendix/.

**Compositional contracts and refinement.** Let `W` be Host Work identity; `Hist(w)` the *retained partial map* `Revision ↦ (payload,digest)`; `Nav` be persisted Space Subject and Message Relation references; `Goal` be foreign-domain standing. The distinct predicates are `WorkIdentityReachable(w)`, `CurrentSnapshotReadable(w)`, and `HistoricalRevisionAvailable(w,r)`. No two are definitionally equivalent. Under same input/observation universe, a replacement assume–guarantee contract may not strengthen required assumptions or weaken guarantees; spell the set inclusion directions `A_old ⊆ A_new`, `G_new ⊆ G_old` only under the same behavior-universe/contract semantics. `Obs(Traces(Impl)) ⊆ Obs(Traces(Spec))` needs a *concrete* model→Python/SQL→installed consumer simulation; an abstract Lean theorem is not a bridge. Source: Abadi and Lamport, LICS 1988, https://www.microsoft.com/en-us/research/publication/the-existence-of-refinement-mappings/.

**Logic / history.** Under the present full-history contract,
`CompleteHistory(w) := dom(Hist(w)) = {1,...,currentRevision(w)}`.
The production states `Hist(Linux)={17,18}`, `Hist(Windows)={46,47}`, `Hist(HostE2E)={3}` refute this predicate; all current revision digests remain valid. Therefore `HistoryDoctorHealthy=false` is correct, not a checker bug. A retained suffix does **not** prove there was a lawful historical retention policy. Without a verifiable old revision source, rewriting `Hist(w,1)` is prohibited. Typed `UNKNOWN` applies to why historical snapshots disappeared and whether an authorized retention basis existed. For `work.get(w,r)`, missing revision returns current typed conflict; do not silently fabricate another representation.

**Database science.** Production readset used one PG `REPEATABLE READ READ ONLY` transaction; the default `READ COMMITTED` could produce different observations across multiple SELECTs. PG `ON DELETE RESTRICT` preserves explicit FKs, but opaque `Nav` references and body mentions lack comprehensive Work FK. Therefore a successful SQL DELETE (if otherwise possible) never proves all consumer effects preserved. Sources: https://www.postgresql.org/docs/18/transaction-iso.html and https://www.postgresql.org/docs/18/ddl-constraints.html.

**STPA and organizational control.** Hazard H1: clearing a Work identity destroys collaboration re-entry to a still-relevant Goal. H2: synthetic old history makes false epistemic authority. H3: leaving a warning falsely treated as a global effect veto prevents unrelated valid work. Unsafe controls are *provided prematurely* (abandon/delete based on 4h idle), *omitted when needed* (consumer navigation), *wrong order* (delete before reference migration), and *applied too long* (indefinite busywork/hold). Use STPA's system control diagram to choose native boundary and test, not add a risk approval board. Source: https://www.mit.stamp-institute.com/handbooks.

**Management / constraint focus.** The improvement target is the *rate of verified consumer-valid outcomes*, not the total number of files, proofs, deleted rows or green labels. The bottleneck here was missing live consumer relation readsets. Once discovered, a 3-row deletion is not worth a 63-body historical rewrite. Avoid Goodhart-style proxy optimization, repeated plans and extra actor roles. A precise stop decision that preserves known live consumers can be a valid engineering outcome; it is not proof that production history is healed.

### 10.2 Actual source and database evidence

Owner-only Host production PostgreSQL inspection was performed through an explicit `BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY`; no UPDATE/DELETE, no printed DSN/credentials, no Host Work terminal mutation. Result:

| Work ref short name | Host state/current rev | retained revisions | Space Subject | MessageRelation targeting Work | Message body WorkRef mentions |
| --- | --- | --- | ---: | ---: | ---: |
| Linux PG cutover old | abandoned / 18 | 17, 18 | 2 | 2 | 27 |
| Windows PG cutover old | abandoned / 47 | 46, 47 | 2 | 5 | 34 |
| Host SourceCut E2E | completed / 3 | 3 | 1 | 0 | 2 |

Total 5 structural Space Subject references, 7 structural Message relations, and 63 raw text matches. The 63 body matches prove *persisted reference traces*, not 63 independent active consumers. No `work_relations`, `coordination_intents` or Work `subscriptions` were found for these three refs in that read snapshot. Exact full readset and consumer liveness beyond these sources remain UNKNOWN. Production `host.status(detail=history)` continues to report `invalidWorks=3`; it is not an installed fix. A follow-on read-only investigation of whether earlier command receipts contain recoverable snapshots was blocked by platform safety, not worked around. Authentic historical recovery basis stays UNKNOWN.

### 10.3 Independent cross-audit, source-bound

Existing Space `space:ordivon-task-portfolio-and-proof-gates-r1:20261101`, topic `topic:ordivon-task:agent-text-contract-cross-audit:20261109`:
- request seq 25818: six-dimensional theoretical/method/authority/conservatism/representation/negative-oracle review;
- first independent Agent findings seq 25823: R2.1 coordinates present, H03 closure UNKNOWN; reject Doctor-greenwashing and excess approvals;
- independent production reference witness seq 25843;
- second independent Agent verdict seq 25845: **A=REVISE** (do not start with retainedFromRevision persistent schema), **B=REJECT** (don't rewrite 63 historical mentions to delete 3 identity rows), **C=CONDITIONAL ACCEPT** (keep navigated Work identities/current payloads, old rev typed unavailable, Doctor truthful); production cleanup needs separate real consumer closure proof;
- implementation response seq 25855.
These are independent *reviews and counterexample proposals*, not code proofs or service permissions.

### 10.4 Ten mandatory questions, scoped to this concrete decision (audit verdict)

| Question | Verdict | Falsifier or repair |
| --- | --- | --- |
| Theory strictly matches semantics? | CONDITIONAL | Full-history and partial-history are not the same predicate; don't infer recovery/retention authorization from current suffix |
| R2.1 eleven typed coordinates? | DECLARED H01/H02/H03 | H03 `c`, `epsilon` and consumer closure still scoped UNKNOWN; no unearned ADMITTED or MODEL_PROVED |
| A/G assumptions and ψ→φ refinement? | UNPROVED for installed outcome | Need native source/public seam + PG consumer; no formal model PASS alone |
| Matt Skill method use? | YES scoped | Public Work.get, Social navigation and Doctor; one vertical slice not private-method mocking |
| ECC Skill method use? | YES scoped | Change impact and independent regression evidence; do not copy its hooks as authority |
| Superpowers method use? | YES scoped | Exact native command, verification-before-completion; not mandatory multiple trackers |
| Is this overly conservative? | NO for 3 referenced IDs, YES if blocking unrelated work | Don't delete low-volume but consumed identities; also don't block independent progress due to Doctor failure |
| Is this mere surface work? | Doctor-only would be | Test actual navigation while history absent; next material goal is history policy/real effects |
| Is representation adequate? | REVISED | Separate Identity/CurrentSnapshot/RevisionAvailability/Navigation/Goal; no global minimum-representation claim |
| Duplication and real consumer? | REVISED | Existing global Spec #1992; only Host Owner spec and public PG test, no duplicate registry/calculus |

### 10.5 Chosen decision and next admissible action

**Decision C: retain these three historically linked Work identities, preserve existing current snapshots and references, explicitly keep full-history Doctor red.** Do not assert “retention repair accomplished” and do not implement a new retained floor schema. This avoids unnecessary destructive rewrite while preserving current navigation. Only a truly *unreferenced* terminal Work with closed/current consumer observation may enter set-based PG cleanup; else remain UNKNOWN for retirement, not global development HOLD.

Native implementation boundary is `services/host/tests/test_host_history_doctor_postgres.py`: a disposable PG18 test creates a completed Work with Space Subject and structured Message reference, removes only its old revision in *disposable testing*, checks Work.get current PASS / previous revision typed CONFLICT / Social navigation PASS / integrity & history Doctor ERROR. This is preservation coverage, not a previously failing production bug fix; do not claim RED→GREEN where the source already behaves correctly.

Sources remain: current Host full-history source, current Git SHA, current work.get/space.subject.list/message.relation.list and actual production readback. Model proof, source acceptance, merge, installed currentness and external Goal acceptance are distinct statuses.
