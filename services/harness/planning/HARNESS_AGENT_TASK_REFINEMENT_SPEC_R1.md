# Harness R2.1 Agent-Task Refinement — Execution Spec R1.1

Status: **implementation-bound proposal**. This is a task specification, not a new authority, admitted runtime LEGO, universal evaluator, or proof of deployed behavior.
As-of: 2026-11-09 (Asia/Shanghai). Current integration SourceCut: `ordivon-org/ordivon@c88a7f22738417c0e7517fafb8ed8999806c29e3`; earlier T1/T2 cuts are preserved in execution evidence. Refresh origin/main before further implementation.
Natural Owner: `services/harness/`; cross-owner effects remain with their original Owner.
Target consumer: a caller-bound Agent Run that must progress from a real engineering objective to verified owner-consumer evidence **without** allowing the model to certify its own completion.

## 1. Goal, not a framework

Enable any Agent to propose alternatives while existing native contracts, tool authority, independent tests, fault injection, and actual consumers determine admission and acceptance. In particular, a local success or model conclusion cannot silently replace the original objective or claim a physical effect. Make falsifiable defects mechanically non-acceptable; unknown domain quality remains empirical rather than a false theorem.

Concrete launch task: finish Harness PG-only production API and operational-guide currentness by reusing the existing PR chain and owner tests; qualify the actual PG consumer and source-to-model assumptions. We explicitly DO NOT run weak-model, model-A/B, or instruction-only experiments: mature methods are adopted directly, and relevant negative examples are code/contract regressions.

### Non-goals

- No second global goal/LEGO registry, approval service, evaluator Agent, execution orchestrator, task tracker, memory/retriever, or universal rubric.
- No Owner truth transfer: Host Work remains social task collaboration; Runtime owns Job/Attempt and actual effects; Gateway owns routing; Harness owns a bounded Agent Run; domain Owner accepts its outcome.
- No treating a Skill instruction, JSON Schema, green model check, CI pass, PR merge, or local Runtime success as domain completion.
- No mandatory mathematical proofs for ordinary edits, arbitrary 80% blanket coverage gate, front-loaded strategy-review ceremony, or weak-model evaluation/experiment campaign.
- No destructive legacy data cleanup without checking the actual current consumer. Test-only and mutually self-referential consumers do not automatically justify indefinite retention.

## 2. Mature method adaptation

| Candidate method | What to adopt | Existing Ordivon carrier | Explicit rejection |
| --- | --- | --- | --- |
| Matt Pocock `to-spec` / `to-tickets` | Conversation -> test-seamed spec -> blocked, vertical ticket DAG | This file, existing GitHub issues/PR and Host Work where useful | New issue tracker, compulsory interview of an already resolved goal |
| ECC `tdd-workflow` / `verification-loop` | Test-first negative controls, build/lint/test/diff/currentness evidence | Harness `mise.toml`, tests, existing owner CI | Copy 300+ Skills, hooks and universal 80% rule |
| Superpowers `writing-plans` / `executing-plans` | Explicit exact paths/expected results; RED -> GREEN -> REFACTOR; isolated worktree; verifiable task handoff | Runtime Workspace, exact Git SourceCut, owner test scripts | New continuous agent supervisor or mandatory multi-agent review |
| TLA+/TLC / CrossHair | Property-scoped model and actual source refinement, counterexample probes | `services/harness/formal/`, `mise run formal:verify`, `mise run formal:source-refinement` | Proof-by-document or universal correctness claim |
| Assume-guarantee / CEGAR | Discharge each component assumption; retain real counterexamples | `.agents/skills/compositional-contracts` and `recursive-lego-calculus` | Each file becomes a LEGO; abstract correctness substitutes for actual effect |

External method references (uninstalled, not executable authority): https://github.com/mattpocock/skills ; https://github.com/affaan-m/ECC ; https://github.com/obra/superpowers . Qualify a pinned upstream executable before any future install, per `external-capability-evaluation` and `skill-supply-chain-audit`.

## 3. Semantic boundaries and outcome

```text
Caller/Domain: goal and acceptance; Host optionally carries Work
  -> HarnessRunContract: one exact bounded Run, Tools, budget, privacy, Provider
  -> Harness: construct WorkingView, generate candidate, admit cognition/Tool intent,
      persist Journal/claims, reconcile/record concrete receipts
  -> Gateway/Runtime/Provider: routing, real execution, external observations
  -> independent Owner-native tests/formal/consumer-readback
  -> domain accepts, rejects, or returns scoped UNKNOWN / next counterexample
```

Four non-negotiable distinctions:
1. Canonical History != Agent Cognition.
2. Tool Intent != Physical Effect.
3. Physical Effect != Semantic Success.
4. UNKNOWN != FALSE, SUCCESS, or permission to retry.

Progress matters too: a trace of more model turns is not progress. When there is a bounded consumer-improving experiment, execute it; otherwise report an exact unknown with a falsifying next observation. Neither endlessly restating uncertainty nor blindly applying changes counts as completion.

### Typed Recursive LEGO R2.1 contract: existing Harness Run persistence responsibility

**Not an additional LEGO registry entry.** This is the target effective contract of the existing `HarnessAgentRun` -> `HarnessStore` production composition and must be checked against real implementation.

- `I`: `(HarnessRunContract, ExactSourceCut, PostgresDSN, Schema, ProviderAdapter, OptionalRuntimeBinding)`.
- `O`: `(CommittedRunRevision, Provider/ToolReceipts, WorkingView, CompletionProposal | RecoveryRequired[UNKNOWN])`.
- `S`: `(run_id, revision, journal_events, leases, cas_objects, claims, working_set, budgets)`; PostgreSQL is the target durable writer; Domain/Runtime facts remain external.
- `pre`: Exact Contract digest, qualified PG schema and caller binding, valid state revision/lease and current effect grant.
- `post`: Atomic Run event admission with revision fence; exact returned receipts/recovery state; **never** a domain-completion guarantee.
- `inv`: target properties PG1–PG6 below; all have explicit assumptions and negative controls.
- `eff`: Harness PG transaction for own Run state; Provider/Runtime tool effects only via already-admitted external ports.
- `c`: typed resource cost (wall time, actual Provider tokens, transaction/IO count) is `UNKNOWN(cost, production-performance-measurement)` until measured on a named consumer; never fabricate zero.
- `epsilon`: consumer/observer-indexed behavioral-equivalence or approximation obligation; `UNKNOWN(epsilon, exact PG/SQLite observable equivalence and production context)`. Source↔model refinement has its own independent standing and is not silently represented by a scalar error.
- `prov`: exact source commit above, `src/ordivon_harness/{agent_run,postgres_store,sqlite_store,cli}.py`, `formal/ProviderClaimR1.tla`, `tests/test_postgres_harness_store.py`, actual Job/consumer receipts.
- `unfold`: bounded spec -> TLA+/TLC model -> source/type/refinement checks -> real PG recovery/fault tests -> installed and caller-consumed Run; each level has independent evidence standing.

### Properties and falsifying cases

| ID | Required property | Counterexample to reject | Verification level |
| --- | --- | --- | --- |
| PG1 | Supported first-party CLI exposes only executable PG commands | CLI help advertises a command that always rejects, or docs invoke a rejected flag | parser + documentation consumer test (T1) |
| PG2 | Supported production Python Run composition cannot silently write SQLite | `HarnessAgentRun.create/open` opens SQLite on an admitted production path | import/call-graph + real PG tests (T2) |
| PG3 | New Run transaction is atomic and exact-replay/revision fenced | competing writers both commit same claim, or partial event batch | real two-connection PG + fault injection (T3) |
| PG4 | Response loss cannot trigger blind duplicate physical Tool execution | UNKNOWN dispatch becomes fresh execution without reconciliation | existing TLA+/TLC + bridge and Runtime tests (T4) |
| PG5 | Run candidate completion is not domain acceptance | successful Runtime Job or final model text becomes task accepted | independent domain/consumer evaluator (T5) |
| PG6 | Exact SourceCut, model, code, wheel, installed and actual consumer witnesses remain distinct, with no vacuous verification | simulated/green model proof upgrades an untested binary or missing production DSN to DOMAIN_ACCEPTED | independent source-bound receipt and falsifying native consumer (T6) |

PG1–PG6 are desired obligations, not currently all proven. Independent proof of `PgRunSourceAuthority` must not be inferred from docs, even if the complete eleven-coordinate declaration exists.

## 3A. Adopted mathematical / computer-science foundations (theory -> native obligation)

These are established methods, not a claim that Ordivon invented a new calculus. Use only the smallest theory that changes an actual implementation decision. The full eleven-coordinate R2.1 declaration is a **declaration**, not a theorem or a runtime permission.

### A. Hoare logic, weakest preconditions, and type-safe admission

For an action C and postcondition Q, Dijkstra's weakest precondition wp(C,Q) is the least restrictive input condition that guarantees Q (under the specified semantics). The useful engineering pattern is to derive admission conditions backward from the required outcome. For example, atomic Run event+projection commit requires a correct schema, exact revision, valid lease, canonical object identity and single-transaction admission. Simply asserting Q in an Agent message does not discharge wp(C,Q).

A bounded correctness statement has shape {P} C {Q}; neither parser correctness nor a unit test proves the entire effectful C without the external assumptions. Illegal operation variants should be structurally unrepresentable where practical, then rejected by the actual Owner at invocation.

### B. Assume–Guarantee, algebraic composition and substitutability

For two real semantic responsibilities L1 and L2, adopt contracts (A1,G1), (A2,G2). In the consuming environment, demonstrate that the producer's guarantee and the environment discharge the consumer's assumptions. The direct sufficient example G1 => A2 must be considered with effect/authority, timing, state, identity, rollback and UNKNOWN semantics, not just JSON shape.

A replacement is eligible only if it does not strengthen assumptions required of existing consumers and does not weaken guarantees already relied upon. In contract notation with A as admissible-environment set and G as required behavior set: A_new should include A_old, and G_new should satisfy each old required guarantee under A_old. Circular assumptions require independent grounding; naming the same invariant in both modules is not composition proof.

For Harness, the Runtime bridge supplies a request identity and receipt interface, **not** a guarantee of domain semantic success. PG Store owns Run Journal transaction facts, **not** Tool physical effects. Domain acceptance remains the caller's oracle. This is the primary law for DELETE -> REUSE -> COMPOSE.

### C. Refinement mapping, simulation and evidence-product standing

Define an abstraction map alpha : S_concrete -> S_abstract. Under proven invariant Inv, a concrete transition must simulate an allowed abstract transition or an observable stutter:

    Inv(s) ∧ Step_concrete(s,s') =>
       Step_abstract(alpha(s),alpha(s')) OR alpha(s)=alpha(s').

Also establish initial-state correspondence, correct observations and the relevant fairness/environment conditions before making a liveness claim. TLC reaching all states of its *bounded model* does not alone establish this source-level simulation.

The verification standing is a product of independently justified claims:
    E = (DECLARED, MODEL_CHECKED, SOURCE_REFINED, REAL_PG_CONSUMER, INSTALLED_CURRENT, DOMAIN_ACCEPTED).
Each coordinate requires its own source/digest/tool/environment/negative-observer evidence. Do not treat E as a single linear grade in which one green step auto-upgrades the rest.

### D. Safety/liveness, concurrency and exactly-once misconceptions

Safety invariant example: at most one effective lease owner admits an identical Provider dispatch at a time; a receipt cannot be forged by a local model result; an UNKNOWN effect cannot be blindly redispatched. Liveness/progress properties require fairness and environmental capacity assumptions; a model may safely pause or return an honest UNKNOWN rather than inventing completion.

Use current Harness `formal/ProviderClaimR1.tla` plus owner-native TLA+/TLC and PostgreSQL concurrency tests, not a new model checker. Faults should include claim races, lost response after committed effect, lease expiry, idempotent replay, crash before/after receipt, cancellation races and contradictory Gateway projection.

### E. CEGAR/CEGIS and Alloy-style bounded relational checking

Counterexample-guided refinement is adopted as a **method of engineering falsification**, not as a new Agent-training program: collect one real counterexample, choose a better abstraction/implementation, rerun the same owner test and retain the regression. The model/abstraction, search grammar and oracle remain separate. When consumer/dependency relations are the problem, Alloy-style relational modeling may be useful to check a bounded graph. Before adding a solver dependency, prefer existing `rg`/AST/owner graph/test primitives; formalize only a high-value property they cannot check.

### F. Information hiding and economics of replacement

Parnas-style modularization is by changeable decision/observable contract, not arbitrary class/file size. A useful deep module hides considerable complexity behind a small stable consumer interface. A natural Owner keeps its own source of truth; duplicate metadata/services merely increase invalidation and repair burden. Retire a legacy Store only when its real downstream consumer closure is established; do not preserve mutually referential dead code or historic test-only compatibility forever.

### Source reference anchors (not executable dependencies)

- Henzinger, Qadeer, Rajamani, *Decomposing refinement proofs using assume-guarantee reasoning* (ICCAD 2000), https://www.microsoft.com/en-us/research/publication/decomposing-refinement-proofs-using-assume-guarantee-reasoning/
- Lamport, *Specifying Systems* and *Safety, Liveness and Fairness*, https://lamport.azurewebsites.net/tla/book.html and https://lamport.azurewebsites.net/tla/safety-liveness.pdf
- Lamport, *Specifying Concurrent Systems with TLA+*, refinement mappings, https://lamport.org/pubs/lamport-spec-tla-plus.pdf
- Dijkstra's weakest-precondition calculus, https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD401.html
- Alur et al., *Syntax-Guided Synthesis* (FMCAD 2013), https://dspace.mit.edu/entities/publication/bf74e326-5c4c-4a29-867a-cb0bd67fcc9f
- Daniel Jackson, *Software Abstractions* / Alloy, https://mitpress.ublish.com/book/software-abstractions
- Matt Skills `to-spec`/`to-tickets`/`implement-spec`, https://github.com/mattpocock/skills
- ECC `tdd-workflow`/`verification-loop`, https://github.com/affaan-m/ECC
- Superpowers `writing-plans`/`executing-plans`/`systematic-debugging`/`verification-before-completion`, https://github.com/obra/superpowers


## 4. Implementation tickets: tracer-bullet DAG

Each ticket has exactly one consumer-visible outcome, a RED witness, GREEN acceptance, and an explicit predecessor. Native tests and mechanisms are reused; never add a duplicate framework.

### T0 — Bind source, owner and negative baseline [unblocked]
- Inputs: exact current `origin/main`, existing Harness README/ARCHITECTURE, Owner AGENTS, `mise.toml`, production API and direct consumers.
- Steps: refresh Git; inspect active cross-owner callers and SQLite/PG surfaces; capture CLI/docs contradictions, skipped real PG tests, already-merged documentation retirements.
- Evidence: exact commit, current diffs, `rg` results, affected tests. Do not re-delete already-merged paths.
- Exit: unambiguous PG1..PG6 obligations with owner and test seam.

### T1 — First vertical slice: executable CLI and current-guide contract [depends T0]
- Files: `src/ordivon_harness/cli.py`, `src/ordivon_harness/independent_cli.py`, `scripts/check_docs.py`; `tests/test_cli_currentness.py`; `README.md`, `docs/{QUICKSTART,OPERATIONS,STATUS,DATA_AND_PRIVACY}.md`; existing directly affected tests.
- RED: test parses public CLI help and current operator examples; deprecated CLI flags or dead backup commands and present-tense misleading SQLite claims fail. Test itself must fail on the old source.
- GREEN: remove dead command parser entries and docs examples, keep actionable native PG backup reference; update one existing document checker (do not create a second validator); prove the real Python parsing and docs check, not a grep-only pass.
- Verification: `uv run --locked pytest -q tests/test_cli_currentness.py`, `python scripts/check_docs.py`, `uv run --locked ruff check src tests scripts`, affected CLI tests, `git diff --check`.
- Stop/accept: no unsupported CLI command publicly offered; exact current docs supported without claiming Python library PG-only completion.

### T2 — One supported Python PG path [depends T1]
- Files: `src/ordivon_harness/{agent_run,api,sqlite_store,object_store,postgres_store}.py`; direct production consumers and wheel/test exports as needed.
- RED: negative test invokes each public production create/open path with an unusable PG DSN, verifying **no** SQLite file creation and an explicit failure; positive test proves actual PG Run/resume across two connections.
- GREEN: move production API to PG-only, remove old SQLite writer references from supported entrypoints; migrate real directly importing scripts. Retire obsolete writer/CAS only after consumer-equivalent source and installed readback.
- Tests: `mise run pg:verify` with isolated `HARNESS_PG_TEST_DSN`, relevant existing Agent Run tests, wheel export verification. No fake/mock PASS replacing real PG tests.
- Stop/accept: public production write path genuinely PG-only; unqualified real PG is UNKNOWN, never PASS.

### T3 — One Run state/PG refinement seam [depends T2]
- Files: current `formal/` ProviderClaim and existing Store integration tests; add no second formal engine.
- Properties: contiguous atomic event admission, lease/revision safety, exact replay identity, persistence/recovery continuity; state every environmental assumption.
- RED: make one deliberate violating implementation/negative test or bounded model probe fail.
- GREEN: TLA+/TLC model and failure probe as applicable; Python/SQL source correspondence and real PG multi-connection negative tests.
- Stop/accept: report `MODEL_VERIFIED`, `SOURCE_REFINED`, `PG_CONSUMER_VERIFIED`, `INSTALLED` individually.

### T4 — Effect/UNKNOWN contract refinement [depends T2; independent of T3]
- Files: existing `ordivon/{run_continuity,provider_lifecycle,runtime_bridge}.py`, ToolProgram and recovery tests, `formal/ProviderClaimR1.tla`.
- RED: response loss, ambiguous Tool effect, conflicting receipts, cancellation race and replay perturbations.
- GREEN: no blind redispatch; truth from real external Owner; semantic candidate cannot upgrade execution disposition.
- Stop/accept: run a direct Runtime-bound negative and positive consumer path, with exact effect identity.

### T5 — Goal-to-result independent acceptance [depends T3,T4]
- Do **not** add completion authority inside Harness. Bind one real caller/domain task with accepted goal, expected consumer and existing owner verifier.
- RED: forged model `completed`, success-shaped Job receipt, unverifiable claimed artifact; none can satisfy domain criterion.
- GREEN: exact artifact/source/consumer readback reaches original objective under current SourceCut; if actual acceptance is not implementable, mark UNKNOWN rather than invent a judge.
- Stop/accept: one end-to-end real task from intent to owner-readback.

### T6 — Independent source-to-consumer refinement and code review [depends T2,T3,T4; may run in parallel with T5]
- NO weak-model studies or Agent-vs-Agent A/B trials. Reuse established contract tests, bounded model checking, existing source-refinement checkers, independent code review and real consumer readback.
- Native proof/observation carrier: each critical property records the exact abstract state, mapping to the concrete Python/SQL/Runtime state, environment assumptions and negative mutant/fault test. Preserve typed UNKNOWN when a bridge cannot be proved.
- Explicit falsifiers: model green with invalid/obsolete source; no real PG DSN despite pytest PASS with skips; forged/contradictory Runtime receipt; model-only physical delivery; wheel from wrong revision; effect success incorrectly promoted to domain acceptance.
- Review two orthogonal axes per Superpowers and Matt: specification conformity (goal, needed consumer, assumption discharge) and engineering quality (simplification, maintained native Owner tools, no duplicate authority); review evidence against actual SourceCut and current Git main.
- Stop/accept: an owner-native proof/test/consumer-evidence chain with limitations, independent review findings resolved or recorded, and zero unsupported promotion of evidence grade. A formal model alone NEVER marks source or installed behavior verified.

### T7 — Integrate, retire, and generalize only proven method [depends T5,T6]
- Native owner CI/merge queue; exact SourceCut and installed readback. Confirm old modules/docs/tests and optional historical branches are retired without losing final consumers.
- Only update existing `.agents/skills/recursive-lego-calculus` or method-router where the exact T5/T6 consumer reveals a missing reusable method; otherwise keep methods as source references, not a new registry.
- Do not propagate a new global gate or copy Matt/ECC/Superpowers wholesale.
- Stop/accept: merged SHA, installed/consumed state separately observed and original objective discharged.

## 5. Workflow / failure policy

1. Every task starts with current SourceCut, a real consumer, an existing owner-native test seam, and the exact negative example; avoid discovery loops if already established.
2. Tests first: observe RED for the intended defect, implement minimally, run GREEN; retain the specific false-positive/falsifying check when it prevents recurrence.
3. One candidate may be rejected without deleting beneficial cognition. If an Agent cannot progress, report an exact blocked assumption and route to a suitable tool/Agent; *doing nothing* is not a PASS.
4. Before accepting a replacement: check assumptions are discharged and guarantees not weakened. Physical effect evidence is not semantic evidence. No increase of authority from a method Skill.
5. For retired components: trace through real production consumers and independent receipts, not dated file existence, reference graph alone or self-referential tests.
6. Any conclusion must name which stage it reached: `SOURCE`, `TESTED`, `FORMAL`, `MERGED`, `INSTALLED`, `CONSUMED`, `DOMAIN_ACCEPTED`; UNKNOWN at one stage cannot be silently upgraded.

## 6. Immediate execution ledger / acceptance

- [x] T0: exact source-bound baseline and native method/tool inventory.
- [x] T1: CLI/current-guide correction, native test + wheel/queue verified, merged PR #1979 at 2026-11-09T15:32:16Z.
- [ ] T2–T7: successive independent, consumer-rooted tickets. T2 implementation already exists as stacked PRs #1859 -> #1867 -> #1875; do NOT generate a competing implementation. Real PG tests are independently qualified below, but publication and installed acceptance remain UNKNOWN.
- No GitHub issue creation or shared-branch push is implied by this local spec. Existing GitHub/Host systems own that action when deliberately invoked.
- This plan is source-bound and disposable after adoption; keep current tests/contracts, not a permanent duplicate planning hierarchy.


## 7. Execution evidence for T0/T1 — 2026-11-09

**SourceCut:** `3b43977e682d8c7668f6371ffd998c7821e4312a`; local isolated Runtime Workspace `ws-gpt6-harness-lego-spec-20261109-r1`. Not a statement about current installed production source.

- **RED #1:** `tests/test_cli_currentness.py` rejected old CLI parser surface, unsupported `capabilities` Quickstart command, and the false SQLite-writer status statement. Original run: 3 failed, 33 subtests passed.
- **GREEN #1:** current CLI has no old `--state-root` flag or SQLite backup/restore verbs; current README, Quickstart, Status, Operations and Data/Privacy revised; supported `create_postgres/open_postgres` Python snippet is explicit while legacy `create/open` is truthfully marked unretired.
- **RED #2:** synthetic documentation regression (`ordivon-harness capabilities`) failed when `validate_live_cli_examples` was missing. Reused existing `check_docs.py` instead of adding a checker service.
- **RED #3 (real native consumer):** `mise run queue` failed in isolated wheel verification because `scripts/check_wheel.py` still demanded retired `store-backup` and related verbs.
- **GREEN #2:** updated native wheel gate and added direct parser↔wheel set contract test. Targeted test set: `16 passed, 30 subtests passed`; `scripts/check_docs.py` and Ruff passed.
- **Complete non-node test evidence:** `1397 passed, 86 skipped, 2 deselected, 290 subtests passed`. Skipped cases require real PostgreSQL and are NOT production qualification.
- **Native verifier:** `mise run queue` exit 0 after repair, including lock, Ruff, source refinement, TLA+/TLC model/counterexample checks, unit tests, hashed dependency audit, docs/evidence checks and isolated wheel+MCP-extra installation. Wheel smoke reported `cliCommandsVerified=10`, `hostFreeHarnessVerified=true`, `mcpAdapterExtraVerified=true`.
- **Independent bounded formal check:** `mise run formal:source-refinement` confirmed two existing CrossHair postconditions; `mise run formal:verify` passed existing Provider/Conversation Binding model/probes. These are retained formal obligations, **not** proofs of PG2–PG6 or installed source.
- **Result standing:** T1 `SOURCE+NATIVE_TESTS+WHEEL_CONSUMER_VERIFIED`; T2 and real PG integration `UNKNOWN`; no shared PR merge, installed production deployment, or domain acceptance claimed.
- **Ruling:** the wheel checker was a forgotten consumer of retired CLI grammar. Extend the same source-native contract seam rather than restoring obsolete commands to satisfy its old check.

Next executable ticket: **T2** — reconcile the existing stacked PR chain #1859 -> #1867 -> #1875 with current main and T1, rerun native verification/isolated PG tests, and migrate the final real consumers before deleting the old public write route. Do NOT open a duplicate T2 PR.

## 8. Independent PG source qualification and existing-PR coordination — 2026-11-09

- Current source comparison: observed main at `a7d70e83945b7418f41b9636f0803d1544e84355`. Existing T2 public API PR #1859 HEAD `d1b78a4a0cabea6f277096747c887edd1f5f11c9` (OPEN, not merged), stacked #1867 Scale (base #1859), #1875 Adaptive/Runner (base #1867). The #1859 diff already implements removal of legacy public `create/open` state-root API, retains PG Run entrypoints, and changes native consumers. Reuse it; no competing PG-only implementation branch.
- Independent environment: installed PostgreSQL 18.6 binaries bootstrapped a temporary socket-only local cluster and FIVE separate disposable test databases; all stopped/removed after test. This was NOT the production PostgreSQL instance.
- Run: `uv run --locked python -m pytest -q tests/test_postgres_harness_store.py tests/test_postgres_cli.py tests/test_r3_supported_agent_run.py tests/test_postgres_conversation_binding.py tests/test_postgres_turn_effects.py tests/test_postgres_wake_turn_map.py --tb=short -ra` with each module's exact test DSN. Actual result **98 passed, 0 skipped**, Runtime Job `job-01a1c0ed-7db1-7570-8128-403e30c6c073` succeeded on exact PR #1859 SourceCut. This is REAL_PG_TESTED for the selected source consumers, NOT installed/deployed or all-Harness queue qualification.
- Posted independent review and two integration hazards to PR #1859: https://github.com/ordivon-org/ordivon/pull/1859#issuecomment-6743984927 . Check CI portability of `check_harness_without_host.py` requiring a test DSN inside isolated wheel smoke; and avoid restoring obsolete mainline documents from historical PR branch.
- Host Space collaboration committed with seq 25749 (T2/Owner planning), seq 25750 (independent Formal review), seq 25758 (existing PR DAG dedup) in `space:ordivon-capability-task-forum-r1:20261101`. These messages are social collaboration evidence, NOT authorized execution or peer acknowledgements.
- T6 revised from weak-model A/B trials to independent model/source/runtime/consumer refinement review as expressly requested. Native tests/fault injection serve real engineering obligations rather than experimentally judging models.
- Current outstanding: T2 PR #1859 and descendants, PG production installed SourceCut, separate model↔code refinement, and domain acceptance. All are explicit UNKNOWN until exact observations.
