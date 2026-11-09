# Ordivon Agent Outcome Realization — R2.1 Formal-first Execution SPEC

Status: IMPLEMENTATION SPEC / phased delivery, not deployed acceptance
Date: 2026-11-09 (Asia/Shanghai)
Baseline SourceCut: ordivon-org/ordivon main @ 05fec3688cf1ae1f091a2dd080784249becbc18a
Primary issue: an Agent can perform planning or cleanup and report success while the final consumer objective remains unmet.
Owner of this document: repo architecture (non-authoritative coordination). Natural Owners retain every durable truth and effect.
Scope: Agent execution and evidence composition, Host Work integrity, Harness completion proposals, Runtime Windows PG supervision, domain consumer acceptance, lifecycle and GitHub delivery.
Non-goal: a new Ordivon orchestrator, database, generic obligation registry, universal verifier, mandatory model reviewer, bulk installation of upstream Skills, or weak-model evaluations.

## 1. Problem statement and user-visible goal

Users delegate objectives, not the minutiae of implementation. Agents have repeatedly made local substitutes for outcomes: a Work was closed before the obligation was resolved; an executable finished without domain completion; a service returned healthy without protected consumer proof; a documentation cleanup removed historical references; Windows succeeded on SQLite while PostgreSQL-only was still undelivered. The user should be able to delegate engineering work and receive a verified result or a precise blocking fact without being asked to adjudicate ordinary technical choices.

Whole-system requirement: for every consequential goal G with consumer C, an Agent-produced plan, completion text or Host terminal state must not be sufficient to establish domain fulfillment. At the same time, ordinary authorized and executable operations should continue without inventing approvals or infinite planning. This is a safety plus liveness problem, not solely Prompt Engineering.

## 2. Source authority and external adoption

Exact sampled upstream references:
- Matt Pocock skills @ 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d: to-spec, to-tickets, implement/implement-spec, tdd, code-review, domain-modeling. Adopt consumer-first spec and blocker DAG of independent vertical tracer bullets. Do not adopt duplicate issue trackers, unlimited subagent spawning or mandatory interviews when context is already settled.
- affaan-m/ECC @ d2ef2680594f9a17526a6e1a2e18b3d242c5d17b: verification-loop, selective standards and durable handoff. Adopt fresh source-/consumer-qualified verification and context economy; do not install ECC's parallel agents, hook/memory authority or an unconditional six-phase pipeline across all Owners.
- obra/superpowers @ 22f0b463e7a5e579904dd6211a520321035526f7: writing-plans, test-driven-development, verification-before-completion, systematic-debugging. Adopt explicit commands, red/green at actual seam and readback before a claim; do not impose always-on interview/review/stop workflows on already specified, ordinary operations.
- Ordivon canonical source: .agents/skills/recursive-lego-calculus/SKILL.md and compositional-contracts/SKILL.md, root AGENTS.md, Owner-native tools/tests. The upstream procedures are reference material, not permission or effect authority.

Source precedence: actual connected service/source + locked upstream refs > current Owner-native contract > approved skill procedure > historical notes. Every adoption is scoped to one verified consumer. No third-party executable/Skill package is installed by this spec.

## 3. User stories

1. As a delegating user, I request a business or engineering outcome without choosing each internal operation.
2. As an engineering Agent, I see the current source, natural Owner, final consumer and objective before choosing an implementation.
3. As an Agent, I can DELETE unnecessary work, REUSE mature mechanisms or COMPOSE components without mandatory scaffolding.
4. As an Agent, I cannot declare the domain task complete solely from a successful Runtime Job, PR or Host Work.
5. As an Agent, when a legal next operation exists, I execute it or produce an observed, typed constraint rather than invent a policy approval.
6. As a returning Agent, I recover the exact committed request and external-effect standing before submitting a new side effect.
7. As a Host consumer, a broken Work history cannot be hidden by the default integrity report claiming healthy.
8. As an operator, I can explicitly distinguish intentional, provenance-backed history compaction from unexplained missing revisions.
9. As a Windows Runtime consumer, PG is the real persistent Job/Attempt authority and native Job Objects supervise the process.
10. As a Security/Gateway consumer, a running PDP is insufficient; protected artifact delivery and meaningful denial must be observed.
11. As a maintainer, only consumer-free or reconstructible physical state can be removed by its natural Owner lifecycle.
12. As a reviewer, every improvement has falsifying initial evidence, scoped proof/consumer acceptance and an exact SourceCut.
13. As a future Agent, my accessible methods remain small and the entrypoint points to the next real operation rather than a giant ceremony.
14. As a researcher, inconclusive evidence stays UNKNOWN with a scope and next test, not falsely FAIL or PASS.

## 4. Representation and authority boundaries

An unmet obligation is a view of existing authorities, not a new stored entity:

O = (G, C, P, N, S, E)
G=user/domain goal; C=final consumer; P=consumer property; N=natural Owner; S=source/installed cut; E=provenance-bound evidence.

The consumer property P is satisfied only when a qualified consumer can read and check E against the actual S and environmental assumptions. Host Work is a revisioned semantic narrative and may be abandoned or completed independently; Harness completion is a proposal; Runtime is physical Job/Attempt/effect evidence; Git is source and merge authority; Security owns policy decisions; domain Owner owns domain acceptance. No component is allowed to assert a fact outside its natural authority.

An ordinary effect does not wait for another Agent's philosophical consent: a concrete authorization denial is evidence of a BLOCKED operation, while unsupported safety speculation is a candidate thought, not a policy verdict. Unknown physical side effects must be reconciled before a retry; liveness never permits blind effect replay.

### R2.1 capability / thought LEGOs

A. Goal-to-consumer-contract method LEGO:
- I: user G, natural Owner identification, current SourceCut, consumer observations.
- O: scoped P, tests and unresolved preconditions, not a global task registration.
- S: temporary reasoning/context plus existing Git issue/Host Work if handoff requires it.
- pre: real consumer can be named or its absence is UNKNOWN.
- post: every claimed success has a target consumer or explicit analysis-only scope.
- inv: no planning text can promote itself to effect or domain truth.
- eff: no effect authority; no new registry.
- c: UNKNOWN until real overhead measured.
- epsilon: UNKNOWN for open-world semantic completeness.
- prov: this spec + current Owner contracts + Git and consumer revisions.
- unfold: goal → consumer/property → natural Owner → candidate action.

B. Harness completion proposal capability LEGO (existing source, refine only at caller seam):
- I: exact HarnessRunContract, model conclusion, Tool receipts.
- O: bounded Run completion proposal or typed recovery/unfinished result.
- S: existing Harness PG Run journal.
- pre: run identity, lease, provider/tool receipt contracts admitted.
- post: Run may terminate without creating domain acceptance.
- inv: physical success does not imply semantic success; UNKNOWN is not FALSE.
- eff: existing Harness/Runtime calls only.
- c, epsilon: UNKNOWN beyond measured consumer scope.
- prov: Harness completion.py/agent_run.py and native tests.
- unfold: caller contract → Provider/Tool Run → outcome proposal → caller/consumer readback.

C. Host Work-integrity capability LEGO (first immediately implementable tracer bullet):
- I: Host status(detail), current PG Work rows and immutable snapshot rows.
- O: integrity report with exact Work continuity check; full digest rehash only in history mode.
- S: same Host PG schema and existing HostV2.status, no new table.
- pre: initialized Host PG schema v13.
- post: an incomplete revision sequence produces healthy=false for both integrity and history; summary remains light.
- inv: a missing revision cannot be silently reported as healthy in the standard integrity view; ordinary active Work is not automatically domain-completed.
- eff: read-only SQL; none.
- c: small extra grouped SQL query; quantify only if significant to operator.
- epsilon: defined only for missing revision detection on the queried PG snapshot, not for historical obligations that were deleted entirely.
- prov: Host service.py / PostgreSQL integration tests / live host.status.
- unfold: status integrity → shared revision-contiguity SQL → check aggregation. Exact red/green test at the public Host API.

D. Native execution supervision LEGO:
- I: PG Job admission, runtime request, platform-native execution settings.
- O: Job/Attempt/Artifact/release/cancel/recovery evidence.
- S: PostgreSQL Registry; Linux native cgroup/systemd or Windows native Job Object.
- pre: installed PG writer and verified platform provider.
- post: physical outcome and resources reflect actual native evidence.
- inv: no SQLite fallback in PG-only admitted path; no manufactured success from timeout/lost; exact idempotent request binding.
- eff: PG transaction plus OS-native process effect.
- c, epsilon: UNKNOWN until Windows native measurement.
- prov: Runtime Core pg_runtime and platform modules, PG integration and installed Windows canary.
- unfold: durable PG admission → native supervision → observe/stop/recover → PG terminal commit → Artifact consumer.

E. Native retention and verification thinking LEGO:
- I: exact resource identity, durable consumer, active-effect state and source provenance.
- O: owner-native discard/retention decision and receipt.
- S: current Git/Runtime/PG and referenced Artifact, no parallel lifecycle truth.
- pre: right Owner effect tool, current source/consumer readback.
- post: physical reclaim cannot assert a semantic task completion.
- inv: active or unique-unpreserved consumer material is not silently deleted; terminal garbage is not retained only because a stale prose reference exists.
- eff: Git worktree remove/prune, Runtime workspace.close, systemd, PG owner migrations as appropriate.
- c, epsilon: UNKNOWN until local workload measurement.
- prov: Runtime lifecycle.py, Git/source, Host PG; test separate physical and semantic facts.
- unfold: source/consumer observation → owner-native reclaim → exact readback.

## 5. Formal properties and explicit limits

S1 (safety, claim authority):
G (DOMAIN_ACCEPTED(g) -> ConsumerAccepted(g, P, SourceCut, Evidence)).
This predicate belongs to the domain consumer; a text assertion cannot substitute.

S2 (safety, no category error):
G (RuntimeSucceeded(j) -> NOT necessarily DomainAccepted(g)).
In executable models, never add an implication from RuntimeSucceeded or HostCompleted to DomainAccepted.

S3 (safety, Host integrity):
G (HostIntegrityHealthy -> ForAllCurrentWorks(ContiguousSnapshotHistory)).
This is valid for a full consistent SQL read snapshot; no claim of preserving deleted Works.

S4 (safety, effects):
G (RequestReplay(identity) -> NoDuplicateDurableJob(identity)).
External side effects require separate idempotency or reconciliation contracts.

S5 (safety, removal):
G (Retired(resource) -> NoLiveConsumer(resource) AND NotActiveEffect(resource) AND PreservedUniqueValue(resource)).
The scope of consumer discovery must be explicit; mere age/dirty flag does not prove these predicates.

L1 (conditional liveness):
G ((Actionable AND fair opportunity to run AND available external Owners)
   -> F (ExecutedOrObservedBlocker)).
This requires a real caller/scheduler. A checklist or model conclusion cannot guarantee liveness, and no fairness is promised for unavailable tools or unbounded external work.

R1 (refinement): An implementation that claims these contracts must map the real source and effects to the property; a TLA+/Lean/Z3/Python model that is not bound to actual source proves only its model. Verification families are selected by the responsible Owner (Host SQL tests; Runtime bounded Kani/TLC + real PG/native tests; Security OPA/Rego + actual Gateway PDP consumer).

R2 (epistemic): UNKNOWN(reason,scope,requiredObservation) is not FALSE or PASS. Artifacts specify SourceCut, authority, result, and currentness.

No theorem in this document is claimed machine-proven. Model obligations graduate only through actual Owner-native proof and implementation/consumer evidence.

## 6. Architecture decisions

D01. Do not add new mandatory Root workflows. Adopt selected Matt/Superpowers/ECC procedures at existing issue/PR/Owner seams; document them as references and optional Skills. No bulk vendoring.

D02. Keep domain outcome ownership outside Host/Harness/Runtime. A domain completion claim needs a consumer-qualified acceptance predicate; a bounded Harness Run may finish while G remains open.

D03. Use the issue/PR tracker for code-delivery blocking DAGs; a long cross-owner programme is a spec with consumer-verifiable vertical slices. Do not create one Host Work per tiny step.

D04. Host integrity must no longer report healthy when known existing Work revision history is incomplete. Retain full per-payload digest hashing in history mode so the default integrity view remains bounded.

D05. Do not change or manually fabricate Host historical Revision rows to make a checker green. Investigate missing PG rows and existing archive/delete events first. If future intentional history compaction is desired, design a separate explicit, provable compaction baseline and change the invariant transparently.

D06. For Windows PG use native Windows process supervision; do not remove cfg(target_os=linux) until actual Windows provider, PG writer and recovery are qualified. Use one shared PG Job/Attempt state-machine identity and no dual write.

D07. For progress, reuse existing domain caller and Harness Run continuation; do not build another polling orchestrator in Host. A model's unsupported permission objection must not become a true denial without a current Owner policy/effect receipt.

D08. Source, merged, installed, loaded, executed, consumed and DOMAIN_ACCEPTED are distinct evidence coordinates. Do not make one global Boolean; demand only the coordinates needed by the actual user objective.

D09. Retirement adopts an expand→migrate consumers→contract(delete) sequence for broad replacements, except explicit user-authorized cold-cutover with no old-data consumer. Do not preserve defunct duplicate implementations out of caution.

D10. Keep tests selected and native; no fixed 80% coverage target, all-Skills activation or six mandatory ECC phases. Existing external tools are considered methods/evidence, not instruction or authority escalation.

## 7. Tracer-bullet delivery DAG

Each ticket is a consumer-verifiable vertical slice, not a layer or a document-only ceremony. Spec itself is T00. Natural Owner can work on independent ready frontier branches.

T00 (architecture, ready): Freeze this SPEC with exact SourceCut and cited upstream revisions. Acceptance: reviewed scope, explicit consumer and native verification for each nontrivial ticket; no extra registry. Output: this committed spec.

T01 (Host, no blockers, first execution): Make Host detail=integrity surface missing Work snapshot revisions, using the existing SQL history check; retain detailed digest verification in detail=history. Acceptance: a real PostgreSQL-backed Host with an intentionally missing middle revision returns doctor.healthy=false from detail=integrity; healthy fresh Host returns true; summary remains lightweight. Test: focused pytest and PostgreSQL native test; read exact SourceCut.

T02 (Host, blocked by T01): Investigate production three-contiguity-failures under read-only SQL and any recorded bulk cleanup; retain or explicitly migrate necessary live obligations, and either reconstruct authentic snapshots from trusted backups or formally introduce a bounded, auditable compaction boundary with its own contract. Acceptance: history is honest, no fabricated gaps; production history health and unfulfilled consumer audit separately evidenced. Do not bulk undo legitimate user-authorized deletions.

T03 (Runtime Windows, independent ready): Port shared PG admission/execution to Windows native supervisor and build a real PG-only Windows binary. First compile failure already observed in Linux-only libc and platform/linux.rs when using Windows Rust target; compile+native Windows tests must replace this failure. Acceptance: Windows PG workspace→exec→observe→Artifact→replay→cancel→restart/recover against real Windows PG endpoint, not a Linux proxy, and SourceCut/installed identity verified.

T04 (Runtime/Gateway consumers, blocked by T03): Switch installed Windows Runtime/Gateway to PG writer through existing deployment mechanisms, prove PG rows and protected Gateway Artifact readback; stop the SQLite writer, then delete exact retired Ordivon Runtime SQLite artifacts with native owner tools. Acceptance: no SQLite fallback; real same-request replay, cancellation and external-effect uncertainty are distinct.

T05 (Harness + domain callers, independent after T00): At an existing caller seam, ensure completion proposal cannot itself commit DOMAIN_ACCEPTED; add consumer-specific contract binding and real readback for one actual domain flow, using the existing PG Run and Tool receipt. Acceptance: an invalid local completion proposal cannot cause the actual domain acceptance transition; valid current consumer evidence can. No generic acceptance service.

T06 (Root/GitHub, blocked by T00 and one of T01/T05): For the affected code-delivery flow, use native GitHub branch protections, issue/PR blocking edges, Owner-native checks and installed/consumer receipts instead of model-authored completion prose. Acceptance: the named PR cannot be called released based on CI alone; readback names exact deployed SHA. Must not alter default required checks without provenance.

T07 (Runtime lifecycle, independent after T00): Remove stale named retention pins and redundant unused lifecycle wrappers after current active consumer readback, preserving the production 4h policy as an operator deployment choice. Acceptance: expired consumer-free Workspace/carrier can be reclaimed by existing Runtime/Git operations; active Job and unique unpreserved bytes remain protected; no stale pin survives source readback.

T08 (cross-owner final, blocked by T01,T02,T04,T05,T06,T07): Run native Owner checks and real consumer acceptance, review the diff against this spec, retire superseded custom paths, and close only the actually met obligations. Acceptance: no new global registry/broker and no equivalence/production claims beyond their evidence; remaining UNKNOWNs have natural Owner, exact action and scope.

Task edges are explicit:
T00→T02,T05,T06,T07,T08;
T01→T02,T08;
T03→T04→T08;
T05→T08;
T06→T08;
T07→T08.
T01 and T03 may start independently. No ticket waits on a user interview for decisions already in this specification.

## 8. Immediate T01 implementation steps (Matt/Superpowers red-green)

1. At services/host/tests/test_mcp_surface.py, add a regression test using the official MCP client, a dedicated throwaway PostgreSQL schema, and authentic Work snapshots. After creating Work revisions 1/2/3, delete only revision 2 inside the disposable test schema. Assert detail=integrity returns healthy=false and work.snapshot_history_contiguous error; detail=history agrees. Compare to a fresh uncorrupted record where both pass. A non-PG mock cannot substitute for the SQL history property.
2. Run the named test before code modification and observe a failing assertion (RED); do not skip PostgreSQL unless the test environment is unavailable, in which case report ENV_BLOCKED and do not claim qualification.
3. Update services/host/src/ordivon_host_v2/service.py by reusing the same grouped SQL check for both integrity and history; keep per-row digest hashing conditional on history. No new schema, SQL table or generic verifier.
4. Re-run test (GREEN), existing focused Host tests, native PostgreSQL qualification and style checks; inspect diff and original symptom.
5. Commit separate source change and reference exact test/evidence and consumer. Publishing a branch/PR is distinct from merged or installed production standing.

## 9. Test/verification and counterexample matrix

- Host revision gap: initial 3 revisions, remove exactly middle rev on disposable PostgreSQL (must make integrity report unhealthy). Genuine clean history passes. Retired Work not falsely resurrected.
- Domain claim: model says complete but downstream consumer lacks receipt; caller cannot mark domain accepted. Valid receipt on same SourceCut can.
- Scope: a successful Runtime stdout is not a business fulfillment verdict.
- SourceCut drift: local test PASS does not imply remote main merge or production install.
- Windows PG: process exit=0 on SQLite is not evidence PG; SQL rows + native process identity mandatory.
- Native recovery: Runtime canceled/lost does not imply work succeeded or that external side effects were undone.
- GC: stale named pins and reconstructible cache eligible; active and unique-value cases protected.
- Security: protected Gateway read succeeds for exact qualified request and rejects an invalid identity; PDP service health alone is insufficient.
- Progress: existing caller observes ACTIONABLE or real BLOCKED. Do not run artificial weak-model experiments; rely on contract/refinement, source tests, native consumer verification and fault/recovery tests that the Owner already supports.

## 10. Stop rules, rollback, removal

- Stop only for a real current blocker, bounded uncertainty requiring an unavailable capability, or verified consumer fulfillment. Arbitrary model caution, stale status notes and approval theater are not blockers.
- Do not blind-retry non-idempotent external effects after timeout; resolve by exact request identity first.
- Review actual Git diff, test output and independent installed version before every production completion claim.
- Every new line/abstraction must have a named real consumer or remove an obsolete implementation; delete custom duplication by default.
- On failed Host T01, leave the integration branch unmerged; no production SQL mutation. On Windows PG, use existing service release/rollback and no legacy Registry data deletion until PG consumer proof.
- Preserve already existing PR/concurrent Agent branches. Never reset or overwrite another Agent's work.
- Do not use Weak-Model tests or model-specific skill-score experiments; this programme verifies real contracts and consumers.

## 11. Evidence / progress ledger

The sole source of code-delivery progress is Git branches/PRs and Owner evidence; no new Host Work is created merely for this spec. A partial ticket reports status SOURCE_CHANGED, TESTED, MERGED, INSTALLED, CONSUMED or DOMAIN_ACCEPTED only where independently observed.

As-of this spec baseline:
- Existing Host status(detail=integrity) can report healthy while detail=history reports 3 invalid revision histories (observed on live host 2026-11-09). This is a reproducible read-only baseline, not a diagnosis of who removed historical rows.
- Windows PG-only Runtime not installed: earlier cross-target Rust compilation failed in runtime/platform/linux.rs. Other work may advance concurrently; reverify current main before source or service changes.
- Linux PG-native was independently demonstrated in Gateway→Runtime→PG SQL and a redundant candidate instance retired; this prior success is not a Windows claim.
- This SPEC is only an implementation plan until exact branch commit/CI/consumer evidence is reported.


## 12. Mathematical and computer-science foundations — source-bound addendum

Date: 2026-11-09, after merge of #1975/#1980/#1981.
Current examined source cut: a7d70e83945b7418f41b9636f0803d1544e84355.
This section refines the SAME T00–T08 execution plan; it is not a new SPEC, Skill, standard, verifier, or delivery Owner. The existing Root and Owner contracts take precedence on actual effects.

### 12.1 Precise system-of-interest and proof boundary

A user goal is not a program postcondition until a named consumer has defined an observable property. For a scoped goal g, define the obligation as

O_g = (g, C, phi, A, N, S, E)

where C is the accepting consumer, phi the observable acceptance predicate, A the environmental assumptions, N the natural Owner of relevant facts/effects, S the precise source+installed cut, and E evidence collected under those assumptions. This is a mathematical view over existing Owner records; do not persist it in a second task table.

The important distinctions are:

- Plan(g) is a candidate derivation, not evidence of phi.
- RunTerminal(r) is a bounded Harness fact, not a domain proposition.
- JobTerminal(j) is a Runtime physical fact; neither it nor ExitCode=0 proves phi.
- Merged(commit), Installed(commit) and Loaded(commit) refer to different authorities and may differ.
- Accepted_C(g, phi, S, E) requires C to consume evidence E matching S and its assumptions. If C is not defined or its observation unavailable, the resulting scoped standing is UNKNOWN, not failure and not success.

This prevents Goodhart-like replacement of the user goal by a convenient proxy such as WorkCount, clean Git tree, or CI green. It cannot guarantee that the original user goal was correctly elicited: specification adequacy is an independent domain question.

### 12.2 Hoare logic, weakest preconditions and native effect semantics

For each actual Owner operation a, use the native precondition, postcondition and effect footprint:

{Pre_N(a, S, A)} a {Post_N(a, S', E)}.

For irreversible or non-idempotent effects, derive the weakest precondition wp(a, Post) relative to the concrete provider. Examples: a post-retry guarantee requires the original request identity and outcome reconciliation; a release claim requires the installed SHA and a consumer readback. Writing a stronger postcondition in prose does not strengthen the executable guarantee.

A proposed action from a model is an untrusted candidate. A native Owner tool is the effect admission and receipt authority. In particular:

ToolReceipt_N(a) does not entail Accepted_C(g).

An agent is allowed to select a different implementation or mature upstream provider if it discharges the same consumer contract. Do not impose global weakest-precondition proofs on trivial actions; use existing Rust/SQL/Python validation where actually required.

Foundations: Hoare (1969), https://doi.org/10.1145/363235.363259 ; Dijkstra (1975), https://doi.org/10.1145/360933.360975 .

### 12.3 Safety, liveness and the limits of runtime monitoring

Separate an unacceptable finite bad prefix from eventual progress.

Safety:
□(Accepted_C(g) => QualifiedReceipt_C(g, phi, S, E)).
□(RuntimePhysicalSuccess(j) does_not_promote_to DomainAccepted(g)).
□(Retired(x) => NotLiveConsumer(x) AND NotActiveEffect(x) AND PreservedUniqueValue(x)).

Conditional liveness:
□((Unfulfilled(g) AND Executable_N(a) AND OwnerAvailable(N) AND FairOpportunity)
  => ◇(ObservedExecution(a) OR ObservedCurrentBlocker(a))).

The liveness statement is conditional: an Agent that never runs, an unavailable provider, an unfair scheduler, or a goal whose acceptance is undecidable does not satisfy its premises. No static Skill or safety monitor by itself proves this eventuality. Schneider's enforceability analysis is an important warning: monitoring can reject recognized violations, but cannot force arbitrary open-world outcomes to happen.

At the natural Owner's state transition, prefer complete mediation of domain-acceptance *claims* and policy decisions, not universal interception of arbitrary shell calls. Broad privileged shells and unmodeled side effects are explicit gaps in any stronger claim. The correct response is to place the trust boundary at the already authoritative consumer, not add another global supervisor.

Foundations: Lamport (1977), https://www.microsoft.com/en-us/research/publication/proving-correctness-multiprocess-programs/ ; Schneider (1999), https://ecommons.cornell.edu/entities/publication/73f44364-f45e-40b5-b581-301a42619b0d ; Saltzer–Schroeder (1975), https://web.mit.edu/Saltzer/www/publications/protection/index.html .

### 12.4 Refinement: the bridge from mathematical model to installed behavior

An abstract R2.1 LEGO specification M and a concrete Owner implementation P need a state correspondence alpha. For each observable concrete transition s →_P s', require a matching abstract transition (possibly with stuttering steps):

alpha(s) →*_M alpha(s'),

under the stated environment and transport assumptions. Observable identity, effect, retry, timing, and consumer-visible results must be preserved. Model checking M alone does not establish this relation; unit tests, source review and native consumer observation are different evidence levels.

An Owner may use existing Lean, TLA+, Z3, CrossHair, Rust/Kani or native PostgreSQL tests as appropriate; none should be required globally. Existing Host DAG Z3 evidence does not prove the Host integrity SQL, and Linux Runtime cgroup evidence does not prove Windows Job Object recovery.

Foundation: Abadi–Lamport (1991), https://doi.org/10.1016/0304-3975(91)90224-P .

### 12.5 Assume–guarantee composition and the minimal authority cut

Let each natural Owner N_i expose a guarantee G_i under assumption A_i. Cross-Owner composition is valid only when the actual producer guarantee discharges the consumer assumption:

G_producer |= A_consumer.

The whole-system domain claim needs the final C-owned predicate. If every individual component's local check passes but a cross-Owner assumption is UNKNOWN, the composition standing stays UNKNOWN. Cyclic assumptions cannot prove themselves.

Define an authority-flow graph with edges for candidate decision, tool execution, evidence receipt, release, and consumer acceptance. Every path by which model-authored text could become an authoritative Accepted_C claim must cross a consumer-owned verification edge. This is a graph-cut / complete-mediation design principle, not a new universal graph registry; inspect existing actual Tool and caller call sites. An uncontrolled direct write to the acceptance store would be a counterexample to a claimed closed cut.

For a replacement provider P' to refine P, the consumer's assumptions must not become stronger and its required guarantees must not become weaker. The data representation can change without preserving redundant source structure when consumer obligations still hold.

### 12.6 Abstraction refinement, counterexample discipline and typed uncertainty

CEGAR: start with the smallest consumer-relevant abstraction; when model checking finds a counterexample, test whether it maps to a feasible concrete trace. If real, repair specification or implementation; if spurious, refine the abstraction. Never patch away a counterexample simply to make a formal test pass.

Evidence standing is indexed by (proposition, source cut, environment, consumer):
- VERIFIED only within the exact qualified observation/proof scope;
- FALSIFIED only for the checked proposition and counterexample scope;
- UNKNOWN when the necessary observation/refinement is absent or stale.

UNKNOWN is not FALSE and not PASS. It does not block unrelated independent actions. An evidence receipt at source S does not automatically transport to S' after dependency/policy/installed-generation drift.

Foundation: Clarke–Grumberg–Jha–Lu–Veith (2000), https://web.stanford.edu/class/cs357/cegar.pdf .

### 12.7 Control/observability and event-sourced recovery

The relevant feedback variable is the *difference between consumer-required and currently observed capability*, not the count of Work records. Existing natural Owners observe their native state and apply bounded effect actions. Re-entry uses the original immutable operation identity; if its external effect is UNKNOWN, resolve/reconcile before any new dispatch.

Temporal's event history and deterministic replay explain why replayed control decisions must not re-execute external Activities. Adopt the proven event/receipt semantics through existing Harness PG and Runtime APIs; do not install another workflow engine or claim all existing effects are idempotent.

Kubernetes's pattern of small independent controllers illustrates local reconciliation by natural Owner; it does not justify a universal Ordivon Agent controller. Its TTL-after-finished semantics likewise distinguishes terminal execution from subsequent reclaimability.

Primary references:
- https://docs.temporal.io/workflows
- https://kubernetes.io/docs/concepts/architecture/controller/
- https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/

### 12.8 Existing method-to-owner mapping; no new mandatory mechanism

| Real need | Existing thinking LEGO / mature procedure | Actual artifact and consumer seam |
| --- | --- | --- |
| Find right goal and assumption | systems-engineering + Matt to-spec | natural Owner plus final C's acceptance property |
| Choose the smallest useful implementation | method-router + project-kernel-decomposition | reuse/delete/compose decision, not a new registry |
| Split cross-Owner changes | compositional-contracts + Matt to-tickets | GitHub Issue/PR blockers and native Owner tests |
| Prove legal transitions | recursive-lego-calculus + Hoare/refinement | existing TLA+/Lean/SMT/Rust/SQL where supported |
| Repair a real defect | Superpowers systematic-debugging/TDD | real failing consumer input → code → recheck |
| Publish or declare complete | Superpowers verification-before-completion + ECC scoped verification-loop | SourceCut, PR/CI, installed binary, final readback |
| Handle persisted effects/reentry | feedback-control + Temporal event/replay pattern | existing Harness PG, Runtime Job and exact receipts |
| Retire physical garbage | consumer-rooted-retirement + Kubernetes/Git lifecycle | native workspace.close/worktree and current consumer query |

Upstream sampled cuts (fixed in section 2) are method provenance; do not vendor their hooks, agent identity, CLI bootstrap or task registries. No weak-model testing or universal Agent scoring is in this programme. Verification uses the existing Owner's real contract, source refinement, test and production consumer.

### 12.9 Next executable frontier and observed acceptance (not a new ticket DAG)

The earlier T00–T08 dependency graph remains controlling. As observed on 2026-11-09 after the main merge:

- T00: merged source SPEC #1975; this appendix adds source-bound theoretical obligations without a new authority.
- T01: source and PostgreSQL consumer already qualified via 441 Host tests in an isolated PG18 fixture. This turn additionally installed merged source a7d70e83945b7418f41b9636f0803d1544e84355 as immutable /opt/ordivon/host-v2 release and restarted the existing service. Live Host MCP detail=integrity now reports the previously hidden history gap: healthy=false, invalidWorks=3. The separate history detail also reports invalidWorks=3 and snapshot digest checks OK. This closes the false-healthy product behavior, NOT the historical-data gap.
- T02: read-only production PG census found three incomplete terminal Works: legacy Windows PG Work revision 47 retained 46–47 only; legacy Linux PG Work revision 18 retained 17–18 only; Host source-cut Work revision 3 retained only revision 3. The first two are abandoned and the third completed, so none is itself an active executing Work. They still have actual Host social references (2,2,1 Space subjects; 5,2,0 Message relations respectively), and each has retained command receipts. Do not equate those references with an active business consumer, but do not silently break their integrity either. Decide between genuine historical recovery from reliable evidence and complete natural-Owner terminal retirement with coherent reference disposal; absent an authenticated compaction proof, never invent intermediate snapshot payloads or silently redefine a broken chain as healthy.
- T03→T04: Windows PG-native Source/PG writer/Supervisor remains the independent actual consumer frontier; no inference from the successful Linux PG path or Windows SQLite Job.
- T05: use one real domain caller and its existing Harness completion-proposal path to establish a consumer-owned acceptance transition; do not make Harness the domain judge.
- T06: compare exact PR merge, release and installed/consumed SourceCuts with existing GitHub Merge Queue and Owner-native CI.
- T07: already merged relevant native Runtime retention/formal progress work; re-read current PG installed and source consumer before proposing additional lifecycle code.
- T08: only after the dependent actual consumer receipts, remove duplicated custom adapters, stale snapshots and outdated methods.

Exit criteria for this addendum itself: it changes a named Owner decision, contract or consumer acceptance strategy; its formulas are specifications with explicit assumptions, not claims of a new machine-checked theorem. Each additional persistent mechanism must replace an existing one or serve an observed failing consumer.
