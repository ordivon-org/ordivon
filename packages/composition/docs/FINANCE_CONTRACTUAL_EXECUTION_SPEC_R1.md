# Finance Contractual Execution — R1 specification and implementation plan

Status: IMPLEMENTATION SPEC / scoped source-contract adoption, not a deployed acceptance service.
Baseline: Ordivon Git `3b43977e682d8c7668f6371ffd998c7821e4312a` (2026-11-09). Currentness must be checked when each ticket starts.
Natural responsibility: Finance owns economic meaning; Composition owns task-local obligation compilation; Harness owns Run continuity; Runtime owns physical effects; Artifact owns evidence carriers; Host owns Work collaboration. No new orchestration, verifier registry, agent database or domain completion authority.

## 1. Problem statement

The Finance program has seven source owners, runnable contribution/Paper/research consumers, mathematical contracts, and isolated candidate tools. However, an agent can replace a requested economic or code effect with a report, conflate test PASS with consumer success, misinterpret UNKNOWN as global refusal, or retain historical self-referential tools as if they were live consumers. Text in AGENTS.md cannot by itself enforce the goal.

The objective is to make domain acceptance depend on independently checkable actual consumer outcomes and preserve a progress path whenever safe work remains. A model may propose and execute freely inside existing authority, but its Completion Proposal is not a domain verdict.

## 2. Solution / user experience

A Finance task starts from a concrete consumer and an outcome contract, not a workflow-template. Existing Goal/SourceCut evidence is bound to a task-local Cognitive Circuit and the existing Composition Gate → Verification Obligation projection. Finance-native verification supplies the domain facts; Composition only checks gate identities and scopes. Agents follow short method pointers and use native Owner tools. A task is accepted only by its real consumer; eligible no-change results require independent evidence. A qualified unknown blocks *dependent claims/effects only*, while unrelated allowed work proceeds.

No new generalized `FinanceTask` engine, persistent task-status taxonomy, permission service, weak-model benchmarking, or redundant skill bundle is introduced.

## 3. User stories

1. As a user, I ask Finance to create an economic outcome and receive the actual produced artifact/evidence or an exact unresolved consumer obligation, not an activity report.
2. As an Agent, I obtain a task-local consumer, Scope/SourceCut and the next executable step without reconstructing the whole Ordivon architecture.
3. As an independent reviewer, I can tell MODEL, CODE, CONSUMER, INSTALLED and EXTERNAL facts apart.
4. As Finance, I may complete pure read-only research and Paper settlement without pretending to have Live broker authority.
5. As a maintainer, I delete historical self-justifying tool chains when no live consumer remains, without retaining a shadow compatibility registry.
6. As a reviewer, a stale manifest, missing gate, mismatched owner, fabricated success standing or substituted data identity cannot be silently promoted.
7. As a maintainer, I can replace a custom algorithm with an admitted mature provider while keeping the same external consumer contract.
8. As the task caller, I can distinguish justified NO_CHANGE, BLOCKED, and actual delivered outcomes using Owner-owned facts, not model narrative.
9. As a developer, I use existing `mise`, `uv`, pytest, Lean/Z3/TLC and GitHub queue rather than a second build system.
10. As the system, I do not convert arbitrary text, a hook warning or an Agent completion statement into effect or acceptance authority.

## 4. Mature sources and adoption decisions

- **Matt Pocock Skills**: `to-spec` for outcome-first requirements; `to-tickets` for narrow tracer-bullet blocking edges; `codebase-design` for deep modules/small seams; `writing-for-agents` for short trigger pointers; `implement`/`code-review` for two-axis acceptance. Adapt practices, do not install a duplicate workflow manager.
- **Everything Claude Code (ECC)**: repo-native hooks/quality gates and TDD cycle as precedents; use existing CI/Owner-native enforcement, not ECC's Claude-only hooks as a privileged universal gate; avoid copying global coverage targets or applying Node scripts to Python/Lean owners.
- **obra/superpowers**: `writing-plans` specifies exact files/test/expected outcome; `executing-plans` maintains real task checkpoints; `test-driven-development`, `systematic-debugging`, `verification-before-completion` demand observed RED→GREEN and fresh verification. No per-task subagent overhead or simulation of inferior models.
- **Established theory**: Design by Contract / assume–guarantee refinement, TLA+ safety versus conditional liveness, non-vacuity counterexamples, and CEGAR driven by *observed* violations.
- Sources: https://github.com/mattpocock/skills ; https://github.com/affaan-m/everything-claude-code ; https://github.com/obra/superpowers

## 5. Representation and formal contract

The existing R2.1 representation is binding: `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`; no extra LEGO registry.

### F01. Finance task acceptance seam (composition of existing responsibilities)

- `I`: task-local immutable objective/source identity, live Finance consumer identity, actual consumer input, existing required gate obligations and verifier-owned evidence.
- `O`: domain-owned outcome/evidence or precise pending obligation; Composition produces only mechanical-gate projection.
- `S`: immutable SourceCut plus existing Work/Run/Job/Artifact/Accounting projections, not a new state machine.
- `pre`: actual consumer is named, required gate binding has exact source identity, correct Owner and support scope; execution eligibility is established at the effect owner.
- `post`: when a domain outcome is accepted, the claimed consumer predicates have independent current evidence; no other output is silently elevated.
- `inv`: `DOMAIN_ACCEPTED => consumer_evidence_current && required_domain_predicates_met`; `COMPOSITION_GATES_SATISFIED != DOMAIN_ACCEPTED`; `RESEARCH_ONLY => !externalWriteAllowed`; external contribution != investment profit.
- `eff`: existing task/Source/Work/Run/Artifact effects; Finance research is read-only, Paper writes dedicated simulated PostgreSQL only; no Live effects from this spec.
- `c`: native current consumer and verifier costs; `UNKNOWN(scope=general task complexity, obligation=measure at the real workload)`.
- `epsilon`: exact integer-cent allocations for the bounded contribution consumer; financial price/authenticity and quantitative forecast uncertainty remain explicitly `UNKNOWN`.
- `prov`: exact Git source and tool revisions, input/evidence identities, native consumer output and verifier scopes.
- `unfold`: goal → actual consumer → existing task-local Circuit → obligation → native verifier → scoped projection → domain acceptance under Finance owner.

### Safety / progress properties

`S1: [](domainAccepted => currentConsumerEvidence && domainPredicatesSatisfied)`.
`S2: [](researchStanding != brokerEffectAuthority)`.
`S3: [](unknown(X) => !claimVerified(X))` while unrelated verified read-only work is not denied.
`S4: [](compositionMechanicalClosure => !automaticDomainAcceptance)`.
`L1` is a *conditional operational obligation*, not an already-proved scheduler theorem: when a named non-effectful task remains runnable and is given fair opportunities, the task must yield an observable consumer effect or a qualified blocker. No unconditional eventual-termination claims.

A mere report is a valid artifact only when the task itself requests a report. A regression suite success is source evidence, not a live Finance outcome.

## 6. Concrete decision seams

1. **Task-local composition seam**: reuse `Cognitive Circuit R1`, `compile_verification_obligations` and `evaluate_gate_results` as the only cross-owner mechanical contract APIs; the finance-specific predicate remains with Finance.
2. **Finance read-only exemplar**: use existing `strategic_contribution` executable as a real output, not an invented portfolio manager. Verify independently observable asset/cash conservation, reserve preservation, no sell, no authority and accurate caller-supplied-data standing.
3. **Research exemplar**: use `finance_lego freeze-experiment/assess-holdout`, bind versioned experiment identity, preserve missing holdout as UNKNOWN.
4. **Paper exemplar**: use the existing PG Paper close/readback and Risk consumers against disposable PG and admitted snapshot evidence. No production DB or broker effect.
5. **Retirement exemplar**: select one truly unconsumed legacy chain by actual consumer scan and native replay/acceptance, then delete scripts, tests, configuration, and stale docs together; do not delete merely because a file is old.
6. **Trusted completion**: an Agent/Harness proposal is never a Finance domain verdict. For high-consequence changes the acceptance source cannot be downgraded by the same unreviewed candidate diff.

## 7. Testing decisions and release gates

- Use the highest existing real consumer seam first; independent expected outputs must not call the implementation under test to manufacture expectations.
- Finance native verification: `cd domains/capital && mise run verify`; Composition native verification: `cd packages/composition && mise run verify`; root CI/merge queue for a cross-owner change.
- Positive: a real bounded contribution input produces deterministic allocations and preserves exact cash/reserve. Negative: an unknown/forged/empty result does not become completed economic advice or authorized order; altered SourceCut/gate owner/scope fails; research result without holdout stays UNKNOWN.
- Proof: use established Capital Lean/Z3 and Composition TLC only where they express relevant laws. If a new theorem is added, include reachable counterexamples and distinguish mathematical abstraction from implementation refinement.
- Proof carrier: output SourceCut, command, observed result and real consumer; do not mark skipped provider tests PASS.
- Completion: implementation, fresh native test, cross-owner integration, and review against BOTH the spec and source standards. Record SOURCE / MERGED / INSTALLED / CONSUMED separately.
- No weak-model trials or artificial model-performance benchmarks.

## 8. Tickets — tracer bullet dependency graph

**T01 — Bind Spec and real consumer (no blockers).** Publish this spec. Reuse the already existing Finance-native `test_strategic_contribution.py` without duplicating its optimizer tests. Add a cross-Owner test-only Composition consumer of the actual Finance CLI: exact read-only output invariants, non-vacuous negative controls, and no domain-acceptance promotion. Do not introduce a production Finance verifier service.

**T02 — Research frozen-outcome consumer (blocked by T01).** Connect the existing Finance freeze/assess CLI to its real artifact/consumer checks. Missing prospective evidence remains UNKNOWN; false capital authorization cannot pass. No alternate Research CLI.

**T03 — Cross-owner verification binding (blocked by T01 and T02).** Advance the T01 test-only source consumer into an owner-native, source-current verifier result if a real Finance consumer needs it. Bind it to the existing Composition Gate and Verification Obligation identities; keep `domainAcceptanceEstablished=false` in Composition while Finance owns the real economic verdict. Test stale cuts, mismatched owners, unknown gates and correct positive result. Do not treat T01 test fixtures as authenticated verifier ownership.

**T04 — Conditional progress and blocker contract (blocked by T03).** At the existing caller/Work consumer, make meaningful progress or qualified blockers inspectable without adding a second Work state machine. A missing optional proof must not block unrelated read-only work; external unknown effects must still be reconciled. Do not assert an unproven liveness theorem.

**T05 — Delete one historical tool island (blocked by T01).** Consumer-rooted delete of an old Finance/LEAN/FIX/Nautilus qualification chain after migrating its actual live consumers. Verify source and CI remain green; deletion is the delivered effect, not a plan.

**T06 — Paper end-to-end ownership (blocked by T02 and T03).** Freeze data → Portfolio decision → Risk → dedicated PG Paper write → Accounting readback → economic comparison. Keep provider/rights and financial live effects UNKNOWN unless separately admitted.

**T07 — Integrate and retire scaffolding (blocked by T03–T06).** Two-axis code review, root/Owner CI, merge-queue acceptance, remove superseded docs/config/tests, avoid parallel verifier or action framework, inspect actual consumer output. Success is source+CI convergence; installed external behavior requires separate evidence.

## 9. Implementation sequence — Superpowers-style per-ticket execution

For each ticket: read exact SourceCut, objective and consumers → identify existing seam and expected observable result → write failing consumer/contract test → observe RED for intended reason → implement minimal correction/reuse → run focused GREEN → run affected Owner verification → compare output to expected → inspect diff for duplicate mechanisms and changed authority → commit → produce concise evidence/provenance. Plan deviations are written as explicit rulings, not silent changes. Do not pre-build all seven tickets as disconnected layers.

## 10. Scope exclusions and guards

- No separate `FinanceAgent`, scheduler, general verifier, method registry, status database, broad ECC hooks installation, language migration, superpowers clone or Skill copy.
- No automatic Live trading, broker effect, capital grant, custom optimizer, artificial future return or invented provider availability.
- No requirement that every file have an eleven-coordinate LEGO record.
- No per-change universal checklist of all formal tools; verify the affected owner and actual consumer.
- No weak-model experiment. Use normal business-domain contract tests and independent negative controls.

## 11. Acceptance criteria for whole R1 program

A1. Current Finance consumer produces a reproducible, independently checked output under a frozen SourceCut.
A2. Missing evidence, stale binding, fake broker authority and completion-by-report cannot be counted as the intended consumer result.
A3. Required Composition obligations bind to actual verifier owners without granting financial effect authority.
A4. Finance Paper/native Accounting reality can be read back and economically compared; all live capabilities remain separate.
A5. At least one obsolete historical implementation chain is physically retired with no broken live consumers.
A6. Source change, owner verifier, GitHub merge acceptance and installed truth are reported separately.
A7. No duplicate global Agent workflow, orphan registry or copied skills are introduced.

Decision rule: a ticket stays OPEN until its exact native consumer acceptance is observed. A model-generated completion statement never overrides those outcomes.

## 12. First-principles theory: existing mathematical and CS foundations

This section maps *adopted theories* to already existing Ordivon method LEGOs.
It is not a new universal proof system. The observed task is Finance and the
same principles may be reused elsewhere only with actual consumers.

### T12.1 Hoare logic and weakest preconditions — task effects have contracts

Hoare's partial-correctness triple `{P} K {Q}` states: if `P` holds and
program `K` terminates, then `Q` holds. It does **not** by itself establish
termination, external market authenticity, or user value. Dijkstra's
`wp(K,Q)` instead asks what is required *before* selecting an action
to establish `Q` and terminate. Adopt this to bind task-local code/edit/
financial effects to a named consumer postcondition.

Application: a Finance clean-up agent cannot satisfy a deletion task with a
document because the postcondition is `unconsumed_implementation_absent`
and `live_consumer_unchanged`; a research-only step cannot satisfy an external
order postcondition. Each necessary effect is verified at its real owner.

### T12.2 Contract algebra and refinement — local PASS is not whole-system PASS

For a component contract `C_i=(A_i,G_i)`, `A_i` defines environmental
assumptions and `G_i` its promises under `A_i`. Real composition requires
the actual environment and peer guarantees to discharge those assumptions
in the correct behavioral universe, not merely compatible JSON shapes.
For an accepted implementation `M`, discharge `M |= (A => G)`.
A replacement requires a declared observational/refinement relation and
corresponding proof or independent consumer evidence.

R2.1 is the already adopted application profile. Map its eleven typed
coordinates to the exact problem-specific semantics: `I/O` are the typed
interface; `S,pre,post,inv` the state and behavioral obligation; `eff`
the effect boundary; `c,epsilon` scoped cost and approximation;
`prov` the evidence/source identity; `unfold` the permitted
realization/decomposition. The profile is **not** eleven new schemas.
A declared tuple is not a checked mathematical proof.

Application: Portfolio's conservation proof does not establish Broker fill,
Accounting reconciliation, or investment utility; compose only at the
Finance-native owner boundaries with an explicit support scope.

### T12.3 Representation and verification refinement — protect the original goal

Let the domain's actual specification be `phi(x)`, while a checker encodes
`psi(x)`. A local `PASS` only establishes `psi` under the checker's
qualification; a Finance domain claim requires an argued bridge
`B: psi(x) => phi(x)` for the precise support scope. If the bridge is
missing, `DOMAIN_ACCEPTED` is not established even if `psi` passes.

For a representation `rho`, accepted abstract solutions must have a
nonempty concrete realization. Choose and record the valid refinement mode:
universal-safe or concrete-witness preserving. A vacuously true implication
over an empty realization set is not a successful implementation.

Application: exact byte digests authenticate *identity of bytes* only; a
caller-supplied historical source is not authenticated market data. A local
Composition test proves a bounded gate, not the Finance economic target.

### T12.4 Temporal logic and fairness — avoid the do-nothing solution

Alpern/Schneider and Lamport distinguish safety ('nothing bad happens')
from liveness ('something good eventually happens'). A no-op can satisfy
all state-preservation properties while failing the task. Adopt **both**:

- Safety: `[](DomainAccepted => ConsumerEvidenceCurrent /\ DomainPredicates)`.
- Safety: `[](SourceMechanicalClosure => ~AutomaticDomainAcceptance)`.
- Safety: `[](ResearchOnly => ~BrokerEffectAuthority)`.
- Progress: under sustained Runnable eligibility, fair execution opportunity,
  permitted resources and an achievable domain predicate, the selected
  execution path must eventually yield a concrete consumer effect **or a
  genuinely supported blocker**. This is a specification obligation, not a
  theorem about the currently deployed scheduler.

A stable, qualifying `NO_CHANGE` is a possible positive result when a
genuine independent consumer proves that no effect is needed. Unknown order
effects instead require authoritative readback, not blind replay.

Application: use the current Runtime/Host/Harness/Composition evidence and
native TLC model checks if their actual state machines need a refinement.
Do not create a second lifecycle database to 'prove' eventual completion.

### T12.5 Three-valued evidence and monotone truth — UNKNOWN has no false verdict

Model the epistemic standing as an information partial order:

`UNKNOWN <= SATISFIED`, `UNKNOWN <= UNSATISFIED`,
and `SATISFIED` and `UNSATISFIED` are incomparable (not a numeric score).

This is **only** an information-order model for a fixed question and
SourceCut, not an implication that new evidence can never retract a previous
claim. When the subject, source, provider, scope or assumptions change,
invalidate/requalify rather than silently reuse prior standing.

Application: when a prospective holdout is not yet available, mark the
economic validity gate UNKNOWN, while proving the independent fact that
the research CLI has not authorized a broker effect. Neither outcome should
block a separable read-only work slice.

### T12.6 Separation of ownership / noninterference — contracts require independent authority

Parnas information hiding places volatile implementation decisions behind
small stable interfaces. Separation logic inspires explicit ownership
boundaries; information-flow analysis differentiates `Data`, `Authority`
and `Effect`. A producer's own metadata is not an independent witness.

Application: Finance Research cannot elevate `independentReproduction=true`
from an untrusted JSON payload into verification or trading permission.
Harness Completion Proposal and Composition Gate closure remain
mechanical claims. Real financial effects require the existing authorized
Trading and external provider admission/readback, with Accounting facts
reconciled separately.

### T12.7 Feedback control, systems engineering, STPA and DSM — keep whole-system value

- **Systems Engineering**: name the real output, system/environment boundary,
  stakeholder needs, non-owned external financial authorities and interfaces.
- **Feedback Control**: distinguish observed state, decision, effect,
  measurement delay, disturbances, controller ownership and feedback.
  A conceptual state map is not proof of stability.
- **STPA**: analyze unsafe provided, omitted, mistimed or prolonged control
  actions, including refusal-to-act when an authorized safe step exists;
  target concrete boundary/verification changes rather than paper gates.
- **DSM**: derive typed dependency edges from actual source and consumers,
  detect needless cycles and false owner-wide coupling. Never equate
  clustering with architecture authority.
- **CEGAR**: check a coarse *sound* model; concretize a candidate
  counterexample; refine only if it is proved spurious; use the native
  checker, not a proprietary CEGAR runtime.
- **GQM**: start from economic capability/customer result, then formulate
  verification questions and measurements. Avoid 'number of tests',
  'number of policies' and 'no-effect rate' as optimization targets.

### T12.8 Decision-method selection (existing thinking LEGOs)

| Real problem | Activate existing method | Derived decision artifact | Native consumer |
| --- | --- | --- | --- |
| Finance goal/authority unclear | `systems-engineering` | boundary, roles, non-owned facts | Capital README and source owners |
| Whether a custom financial tool deserves to exist | `recursive-lego-calculus`, `project-kernel-decomposition` | delete/reuse/compose choice | current Capital CLI or test |
| Finance–Data–Research changes affect too many owners | `design-structure-matrix` | typed consumer impact, candidate narrower seam | `tools/repo/convergence_plan.py` |
| Paper result diverges over time | `feedback-control` | state/observation/effect trace | Capital Accounting / Paper readback |
| Agent pretends to have market/broker authority | `information-flow-analysis`, `stpa` | authority/effect boundary, negative test | Security/Trading, no general gate |
| Performance/alpha claim rests only on historical association | `causal-intervention` where causal question exists | explicit assumptions and identified comparison or UNKNOWN | Finance Research |
| Historical tool retirements need negative-consumer proof | `recursive-lego-calculus` retirement reference | source-current closed-consumer or UNKNOWN | existing Git/Owner test |
| Data/provider changes break experimental reproducibility | `fmea-fta`, native CEGAR when warranted | concrete failure/counterexample | existing Research validators |

Selection is **conditional**; the table is not an instruction to invoke
every method on every task. Each method remains advisory and cannot
substitute for a native owner-owned verdict.

## 13. Real Finance system argument and ownership

`Mandate -> Markets(PIT) -> Research(evidence/unknown) -> Portfolio(conditional decision)
-> Risk(feasibility) -> Governance(effect admission) -> Trading(provider intent/effect/readback)
-> Accounting(cash/positions/settlement) -> independent economic outcome comparison`.

This is a *dependency and evidence argument*, not a proposed service mesh.
Specify independent objectives across strategic and tactical levels:

1. **Strategic consumer**: capital needs and liabilities over time; verified
   economic output from the actual Finance goal, not investor-sounding prose.
2. **Tactical contracts**: each cross-owner interface admits typed data,
   known assumptions, scope and the exact effect owner.
3. **Implementation effects**: existing CLI, PostgreSQL, Runtime and
   provider mechanisms; scripts are implementers, not goal authorities.
4. **Evidence boundary**: SourceCut, algorithm input, result readback,
   checker target and verifier-owned witness; projection/test/model are separate.
5. **Evolution**: evidence-driven replacement of weak local mechanisms with
   mature packages, retaining consumer contracts and removing obsolete glue.

The Capital live-broker surface is out of scope. A simulated portfolio
improvement is not real-world investment alpha. The 2026-11-08 SPY/SHY
research sample still has prospective holdout `UNKNOWN`; no available
forward window is invented by this spec.

## 14. Implementable refinements and task acceptance matrix

| Slice | Required observable result | Negative / non-vacuity evidence | Exact owner check |
| --- | --- | --- | --- |
| T01 consumer | existing Finance contribution CLI produces exact, read-only economic projection | forged `externalWriteAllowed`, cash error, mismatched holdings, no result | Composition test + Capital native suite |
| T02 research | existing freeze and assess CLI produces frozen plan and scoped UNKNOWN/REVIEW_REQUIRED evidence | absent holdout must keep economic gate open, self-declared independent replication must not certify investment edge, extra authority rejected | Finance Research CLI + Composition gate consumer |
| T03 binding | exact manifest/obligation/source/binding and real verifier-owner result | stale/mismatched owner/scope/digest fails; no fake Owner truth | Composition R1 native tests, scoped domain verifier |
| T04 progress | actual Work/caller sees verifiable output or qualified blocker | pure inaction/report under executable change cannot be 'done'; uncertain external effect never retried blindly | existing Host/Harness/Runtime native state |
| T05 retirement | old unconsumed tool and linked historical scaffolding physically removed | current native CLI and CI unaffected, proof assumptions not fabricated | Capital, affected Owner closure and Git |
| T06 Paper | frozen research -> policy/risk -> PG Paper ledger -> readback and economic comparison | duplicate effects, unbalanced money, missing market/booking provenance | Capital Paper EOD and Accounting |
| T07 integration | latest Git/CI merge queue accepted | check changes in trust source; regression, stale source, fake installed truth | root CI / CodeQL / merge queue |

A checker changing alongside its implementation cannot self-declare that its
acceptance semantics were preserved. Existing repository owner-boundary and
SourceCut/CI closure are part of the independent challenge, not optional text.

## 15. Test seam engineering and first implementation decisions

**Matt deep-module rule**: reuse the *highest existing test seam*, not
five new helper classes. For T01/T02 it is the real Finance CLI plus a
task-local Composition gate; for T06 it is the existing Paper close and
PostgreSQL readback; for T05 it is the native source/dependency closure.

**Superpowers plan rule**: each vertical ticket has exact source paths,
expected output and a fresh RED/negative witness followed by GREEN; a
test run made before the current SourceCut cannot be reused as current proof.

**ECC engineering rule**: quality is enforced by the installed native
`mise`/pytest/Ruff/formal checker and GitHub CI, not by copied
Claude-specific hooks or a blanket coverage percentage.

T02 exact implementation site:
`packages/composition/tests/test_finance_research_frozen_consumer.py`;
real CLI at `domains/capital/scripts/finance_lego.py`; Finance source
`domains/capital/src/ordivon_capital/research/experiment_protocol.py`.
Record those exact test-only consumer paths using the existing
`TEST_ONLY_SOURCE_CONTRACT` `selection_scope=PATH` mechanism (no owner-wide
coupling). A frozen plan with a missing holdout must yield a SATISFIED
*read-only protocol integrity* gate but an UNKNOWN *economic prospective
validity* gate, so whole-circuit mechanical closure remains OPEN. Both
claims remain separate from Domain Acceptance.

T03 implements a real source-current verifier/result bridge only when
the Finance owner exposes one; do not present test fixture signatures
as trusted identity attestation. T04–T07 follow the dependency frontier,
not a huge speculative 'agent reform' horizontal rewrite.

## 16. Decision & proof review checklist

Before marking a ticket complete, compare its actual result to four
independent statements (provide paths and native commands, not opinion):

1. **Problem:** is the demanded Finance outcome still the original
   problem predicate `phi`, not just a convenient checker `psi`?
2. **Mechanism:** was the minimal needed custom responsibility retained
   after mature-provider search and delete/reuse/compose consideration?
3. **Evidence:** did the real SourceCut, verifier, consumer and
   external authority (where applicable) actually support the exact claim?
4. **Progress:** is there actual business/code effect or verified
   no-change/blocker, and did unrelated eligible work avoid being frozen?

Any missing fact is scoped UNKNOWN, not a fabricated theorem, PASS or
global refusal. The checkpoint is a **domain result**, not a word count.
Do not require human approval of every ordinary Finance analysis decision.

## 17. Citable technical foundations (official papers / primary sources)

- Hoare, *An Axiomatic Basis for Computer Programming* (1969):
  https://doi.org/10.1145/363235.363259
- Dijkstra, *Guarded Commands, Nondeterminacy and a Calculus for the Derivation
  of Programs*: https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD418.html
- Benveniste et al., *Contracts for System Design* (2018):
  https://doi.org/10.1561/1000000053
- Pacti's existing contract algebra and I/O/G/A semantics:
  https://www.pacti.org/docs/getting_started/
- Lamport, *Safety, Liveness, and Fairness*:
  https://lamport.org/tla/safety-liveness.pdf
- Alpern and Schneider, *Defining Liveness* (1985):
  https://doi.org/10.1016/0020-0190(85)90056-0
- Parnas, *On the Criteria to Be Used in Decomposing Systems into Modules*:
  https://doi.org/10.1145/361598.361623
- O'Hearn, Yang and Reynolds, *Separation and Information Hiding*:
  https://doi.org/10.1145/1498926.1498929
- Clarke et al., *Counterexample-Guided Abstraction Refinement*:
  https://doi.org/10.1007/10722167_15
- Basili, *Goal Question Metric*: https://hdl.handle.net/1903/7538
- Leveson / MIT STPA Handbook:
  https://psas.scripts.mit.edu/home/get_file.php?name=STPA_handbook.pdf
- Matt Pocock Skills (source): https://github.com/mattpocock/skills
- Everything Claude Code (source): https://github.com/affaan-m/everything-claude-code
- Superpowers (source): https://github.com/obra/superpowers

These sources justify *methods*, not factual installed-system behavior.
The exact local source cut, executables and native owner tests establish
that separately.
