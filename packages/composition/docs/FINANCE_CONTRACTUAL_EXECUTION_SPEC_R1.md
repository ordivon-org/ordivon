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
