# Artifact Standing Convergence — R2.1 Implementation Spec

**Authority:** Artifact Owner, with independent Domain consumers. **SourceCut:** `3b43977e682d8c7668f6371ffd998c7821e4312a` (remote main at 2026-11-09 21:38 +08). **Status:** implementation contract / first vertical slice in progress. **Method suppliers:** Matt Pocock Skills (to-spec, to-tickets, implement, tdd, code-review), obra/superpowers (writing-plans, TDD, isolated worktree, verify-before-completion), affaan-m/ECC (selective feedback/hook discipline, NOT wholesale harness installation). Upstream commits: Matt `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`, Superpowers `22f0b463e7a5e579904dd6211a520321035526f7`, ECC `d2ef2680594f9a17526a6e1a2e18b3d242c5d17b`. Upstream method source is not Ordivon execution authority.

## Problem statement

Artifact has two verification backbones: `artifact_verification/stage.py` for v1 Build/Delivery and `scripts/artifact_verify.py` for v2 profile-bound native verification. The two paths do not consume one canonical decision semantics. A native aggregate PASS may be true while profile-required evidence is incomplete; older release snapshots and LOCAL_LIVE_PROVEN are not current runtime authority. Historical `planning/prototypes/standing_decision_r1.py` is not production. The aim is NOT to manufacture a third workflow, registry, owner, policy, or verifier.

## Solution / user outcome

One small, pure, provenance-aware Standing qualification semantics shared by existing entrypoints. Source and artifact identities remain commitments from existing modules; family-specific verifiers provide observations; Standing derives only bounded supported claims; Runtime owns execution, domain consumers own application acceptance, Distribution/Network own transport, installed owner owns currentness. Replace duplicated decision logic and retire obsolete experimental carriers when their tests and consumers have migrated.

## User stories

1. As a Game consumer, I can distinguish format verification from successful engine loading.
2. As a Publication consumer, I can distinguish an executed Office gate from verified visual/target readback.
3. As a Research consumer, I can distinguish syntactically valid Parquet from validated dataset semantics.
4. As a production operator, I can identify exact profile/subject/provider versions used.
5. As a reviewer, I can reproduce a Standing decision from frozen inputs without contacting tools.
6. As an Agent, I can invoke either existing entrypoint without inventing a new top-level framework.
7. As a maintainer, I can replace one native verifier while preserving existing consumer requirements.
8. As a verifier author, I cannot promote absent or contradictory evidence to complete.
9. As a release consumer, trust and distribution remain independent from format qualification.
10. As an Artifact maintainer, I can remove old duplicate decisions after all live consumers migrate.
11. As an Ordivon operator, I can distinguish SOURCE, MERGED, INSTALLED, EXECUTED, VERIFIED, CONSUMED and DOMAIN_ACCEPTED.
12. As an architecture reviewer, I can reject a refactor that adds another authority layer rather than reducing duplication.

## Semantics and scope

A Standing **claim** is a bounded assertion, not an overall success bit. A **Profile** supplies required claims. An **Observation** supplies an identified native result, including explicit PASS/FAIL/NOT_EVALUATED and independent evidence pointers where required. A **Decision** derives no stronger assertion than what evidence supports. A **Consumer Acceptance** is external to the Artifact kernel. A historical or shadow capability binding is not present-node availability evidence.

Formal archetype: `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`.

- I: immutable Subject/Profile commitments; already-admitted native observations; required claim keys; optional explicitly bound consumer requirement.
- O: typed ClaimCoverage and scoped Standing vector; no domain success assertion.
- S: Unit (pure evaluator, no durable state).
- pre: canonical Profile is checked; input evidence identities/bindings are verified by their natural Owner; malformed inputs report explicit error, not PASS.
- post: decision explicitly identifies missing, failed, not-evaluated, contradictory and supported claims.
- inv: missing/unknown/failed/self-witnessed or contradictory required claims cannot yield complete qualification; no authority derived from aggregate native PASS; no implicit trust, install or consumer success.
- eff: empty for pure kernel; all I/O stays in existing adapters.
- c: computational cost upper-bound UNKNOWN until measured; no fabricated constant.
- epsilon: approximation 0 for deterministic local projection under its explicit assumptions; semantic adequacy of native observations remains an independent obligation.
- prov: exact SourceCut + profile/subject/native observation identity + checked validator and consumer evidence where available.
- unfold: L0 decision and non-claims; L1 required keys and statuses; L2 raw observations/provenance and counterexamples; L3 native adapter internals, only when needed.

Safety law, under well-formed inputs: `complete => all_required_supported_by_nonself_matching_native_evidence AND no_identity_contradiction`. Also `DOMAIN_ACCEPTED` cannot be derived by this evaluator. No theorem about actual native tool honesty, toolchain closure, transport effects, or target applications is claimed.

### Compatibility and negative controls

- v1 stage `status=PASS` may mean all *executed* gates passed while `profileVerificationComplete=false`; preserve this distinction until consumer migration, never promote missing gates.
- v2 native `status=PASS` may be legacy compatible while `profileVerificationComplete=false`; preserve existing consumers and add scoped Standing, never reinterpret as full acceptance.
- FLAC/WAVE/PNG claim-complete routes require explicit claimResults/native status pointers; do not weaken.
- v1 and v2 profile definitions are NOT globally equivalent. Prove each common axis or mark UNKNOWN.
- No full snapshot guarantee for sidecar formats until dependency closure is bound.
- Negative cases: absent claim, NOT_EVALUATED claim, explicit FAIL, conflicting native pointer, missing required gate, mismatched native identity, tool identity drift, source rebind, fake consumer success.
- Keep old API/schema working while expand–migrate–contract is in progress.

## Implementation decisions

1. Reuse `artifact_verification/claim_coverage.py`, `native_identity.py` and current v1 receipt format. Prefer a pure shared coverage/decision helper only if two real consumers justify it; no registry/service.
2. Keep raw observations and existing compatibility statuses; expose a new explicit Standing projection only where required.
3. The first unit of change cuts vertically through the v1 stage and existing v2 verification service, with one shared deterministic requirement-coverage operation and caller-visible negative tests.
4. Next migrate old standing prototype tests to the production contract; retire the prototype if no producer/consumer still needs it.
5. Preserve current profile authority, snapshot policy, tool identity and all required non-claims.
6. Refactor DirectPython/OCI only after shared semantic integration proves removal of duplicate responsibility; delete obsolete branches rather than adding shims permanently.
7. Use existing natural Owner tasks and GitHub CI, not imported ECC hook sets or a new approval/agent runtime.
8. No weak-model trials, performance-score game, or unnecessary universal Work schema. Wider Host/Harness adoption is a separate, consumer-proven change.

## Testing decisions

Use existing public entrypoints `execute_verify_stage` (through DirectPython provider) and `scripts/artifact_verify.verify_request` plus the pure Standing API. TDD red-green-refactor on counterexamples; independent expected values from Profile declarations and raw native receipts; avoid mock-only tests and self-certified snapshots. Use owner-native `mise run verify` and focused `pytest`. Run current finite model checks; property checks must cite the production function actually checked. At least one real native and one independent consumer readback before a final production promotion. Never call a unit-test PASS a deployed-consumer PASS.

## Tickets and blocking edges (Matt tracer bullets / Superpowers small steps)

| Ticket | Blocked by | Consumer-visible delivery | Exact seam / tests |
|---|---|---|---|
| T1 Shared coverage semantics | none | Both v1 and v2 publish the same bounded coverage vector; legacy statuses preserved | `artifact_verification/claim_coverage.py`, `stage.py`, `artifact_verify.py`, new cross-entrypoint test |
| T2 Prove no false completeness | T1 | Missing/failed/contradictory/self-witnessing claims cannot become complete via either route | source-bound model checker, negative owner tests |
| T3 Migrate prototype & contract | T1,T2 | The pressure prototype no longer decides a second kind of Standing | prototype consumers/tests migrate or are retired |
| T4 Exact dependency closure | T2 | Qualified sidecar-dependent input identity is explicit, else UNKNOWN | Runtime input commitment, native format & consumer tests |
| T5 Existing consumer readback | T2,T4 where needed | Game/Publication/Data readback binds exact verified Subject | real target adapters, consumer acceptance |
| T6 Retire old logic and glue | T3,T5 | One Standing authority, with duplicate branch paths removed | source graph + owner tests + actual caller checks |
| T7 Owner-level work handoff | T5,T6 | Task reports separate execution from consumer success | existing Host/Runtime/Harness contracts; no new registry |
| T8 Independent release and cleanup | T6,T7 | verified merged source, installed readback where relevant, obsolete history removed | CI, Code Review, consumer evidence |

## Delivery gates and stop conditions

- P0 merge gate: all new negative tests and owner queue verification; no complete status from unknown or contradictory required claims; old entrypoints still runnable.
- P1 migration gate: consumer-led integration tests and evidence identity, no unproved v1↔v2 equivalence.
- P2 contraction gate: actual duplicate decision logic deleted and no live callers remain.
- Public result must separate code committed, PR opened, merged, deployed, executed and consumed.
- Stop architecture expansion whenever an extra class/schema/check has no independently testable consumer responsibility; do the smallest reversible change instead.
- Every ticket must end in an actual changed capability or justified subtraction, native verification and concrete remaining blockers. A plan/document is not completion of any implementation ticket.

## Mathematical adoption and source-to-consumer obligations (2026-11-09)

This section is a scoped decision record, not a second mathematics/Skill
registry. Reuse the existing Ordivon R2.1 formal-thinking reference at
.agents/skills/recursive-lego-calculus/references/formal-thinking-legos-human-agent.md
and its formal-model.md. Each method is activated only for a real unsatisfied
consumer/property pair.

### A. Abstract interpretation: separate evidence from its projection

Use Cousot & Cousot (POPL 1977) to distinguish native concrete verification
state s from abstract evidence alpha(s). Our current abstract values represent
missing, not evaluated, explicit PASS, explicit FAIL and invalid evidence.
UNKNOWN is less informative than a supported PASS or a supported FAIL. PASS
and FAIL are incomparable: neither is an alternative spelling of UNKNOWN.
The production v2 adapter now distinguishes an explicitly witnessed required
FAIL from a failed/inconsistent observation: native FAIL plus a matching
required-claim pointer may yield scoped FAIL; native aggregate PASS contradicted
by a required FAIL yields UNKNOWN. This avoids both false-positive qualification
and over-conservative suppression of actually supported falsification.
Raw contradictions stay in evidenceIssues; the currently exposed Standing
status is UNKNOWN, not a new universal four-valued result type.

For nonempty required claim set R, native observations E and independently
validated witness predicate W:

  Complete(R,E) implies
    (R != empty) and
    (for all r in R: E(r)=PASS and W(r)) and
    not Contradictory(E).

The production pure assessor checks explicit status/coverage only, conditional
on callers having validated W; it does not itself perform native attestation.
The v2 caller retains strict nativePointers and exact profile/subject/
contract checks; v1 retains its actual gate receipts. A model of the pure
assessor alone is not a model of the tools' real-world behavior.

### B. Assume–guarantee composition and representation-preserving refinement

An actual producer P may satisfy consumer C only if the producer guarantee
implies C's precondition under a qualified environment and effect/identity
boundary:

  G_P(output,effects) and Current(provenance) => A_C(output).

This is a scoped assume–guarantee interpretation of the existing
R2.1 pre/post/inv/eff/prov coordinates; a claim of domain acceptance must
still originate from the actual consumer, not from the Artifact kernel.

Let N1 and N2 map v1/v2 raw observations to their legitimately shared
claims and let F be the common status projection. The conditional obligation
is:

  ValidEvidence(x,y) and CommonClaimsEquivalent(N1(x),N2(y))
    => F(N1(x)) = F(N2(y)) on common claims.

Equivalent identifiers or schema fields do not establish arbitrary v1/v2
behavioral equivalence. Retain typed UNKNOWN for unbridged requirements and
for native dependency closure not yet established.

### C. Counterexample-guided abstraction refinement (CEGAR)

Use the existing finite checker and native entrypoint negative controls,
then check whether a reported model counterexample is physically realizable.
If the counterexample is spurious, refine only the responsible abstraction
rather than adding a global framework. The earlier 289008 states and the
new 50-case shared-Standing state enumeration are exhaustive only in their
declared finite abstract state spaces; they do not prove arbitrary JSON
inputs, native verifier honesty, filesystem races or target application
acceptance. This is formal-method refinement, not a weak-model trial.

### D. Safety, liveness, effect bounds and incremental invalidation

Safety: no missing/invalid/unsupported required claim becomes complete.
Liveness, when a task is actually schedulable and its dependencies remain
available under stated fairness conditions: the verification either reaches
a scoped conclusion or emits an actionable blocked state. Do not assert that
all external tasks always terminate successfully.

Proof and test evidence remain valid only for their source/environment/tool/
consumer readsets; if a material dependency changes, evidence must be
requalified. Reuse existing Git, Runtime and Owner-native change/receipt
mechanisms. Do not install another proof cache, scheduler or status authority.

### E. Verification-guided engineering and actual consumers

Follow the Cedar VGD separation of an executable model, exact production
function and independent differential/property tests. Use existing GitHub
checks and Owner tests for SOURCE review, and native Game/Publication/Data
readback for real domain acceptance. Do not turn source CI into an
installed-currentness or consumer-domain assertion. Google CAV 2026
network model checking further demonstrates why reproducing actual bugs in
finite models is more informative than inventing endless proof templates.

The implementation process uses Matt to-spec, to-tickets and implement-spec
as a dependency DAG; Superpowers isolated-worktree, TDD and verify-before-
completion; and ECC's selective plan/test/review discipline. These are
existing methodology suppliers, not three new mandatory control planes.
No weak-model evaluation, duplicated hook system, or blanket ECC install.

### F. Proof obligations and effect owners

| Obligation | Existing carrier | Required external evidence |
| --- | --- | --- |
| Non-vacuous required claims | Profile registry and shared assessor | schema/index and negative tests |
| No native aggregate-PASS laundering | v1 Stage and v2 Verify | output-contract tests |
| Native evidence pointer and identity | v2 native/identity assessors | source-bound finite model + native checks |
| Conflicting failure is not proved false | shared status checker | negative contradicting-native test |
| Old prototype no longer decides Standing | Artifact Git source | remove old prototype, migrate its tests |
| Complete dependency closure | native Artifact/Runtime owners | T4 exact input readset, not established here |
| Independent domain acceptance | Game/Publication/Data owners | T5 real readback, not established here |
| Duplicate old production policy removed | Artifact owner | T6 true source subtraction |
| Accepted merge and live deployment | Git/Workstation/domain owners | T8 independent source and installed receipts |

### Primary literature and industry implementations

- Cousot & Cousot, Abstract Interpretation, POPL 1977:
  https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml
- de Alfaro & Henzinger, Interface Automata, FSE 2001:
  https://doi.org/10.1145/503271.503226
- Clarke et al., Counterexample-Guided Abstraction Refinement:
  https://web.stanford.edu/class/cs357/cegar.pdf
- Leslie Lamport, Safety, Liveness and Fairness:
  https://lamport.azurewebsites.net/tla/safety-liveness.pdf
- Amazon, How We Built Cedar: A Verification-Guided Approach, 2024:
  https://www.amazon.science/publications/how-we-built-cedar-a-verification-guided-approach
- Google, Model Checking for Flexible Networking Protocols, CAV 2026:
  https://research.google/pubs/model-checking-for-flexible-networking-protocols/
- Exact method suppliers: https://github.com/mattpocock/skills ,
  https://github.com/obra/superpowers ,
  https://github.com/affaan-m/ECC .

## Independent cross-audit and exact next obligation (2026-11-10)

Current candidate: PR #1974 HEAD 9e0797afcb28de920abb7aeac1f11e1d4065f4e8; T1–T3 already implemented and GitHub checks passed, but PR not merged at audit time. Reuse existing Spec and source functions; do not open competing Agent governance plans. Host Space: space:ordivon-capability-task-forum-r1:20261101 topic 03-refinement, peer findings seq25763 (generic witness counterexample), seq25779 (legitimate shared structured witness), seq25789 (T3 native handoff), seq25795 (formal audit), seq25800 (v1 supported-FAIL counterexample). Our pre-execution cross-audit request seq25807 asks peers for competing counterexamples; discussion is not source authority.

### Six independent review axes and pre-implementation decisions

1. **Theory:** R2.1 eleven-coordinate archetype, not an extra service. A required claim must be supported by a semantically applicable native observation under source/identity assumptions. Generic aggregate PASS without claim semantics violates the intended assume–guarantee contract. Verdict: FAIL at v2 pointer seam.
2. **Skill method:** Matt public seam TDD/dual-axis review; Superpowers RED/GREEN/fresh verification; ECC selected review only, not global hooks. Existing seams: v1 execute_verify_stage, v2 verify_request and assess_required_evidence. Verdict: selected, no new workflow.
3. **Overconservatism:** v1 executed_failures are appended to a general integrity issues list; the common evaluator reports UNKNOWN even for a witnessed required gate FAIL. Verdict: FAIL; recover scoped falsification.
4. **Surface-only:** new status names, comments, a standalone plan, or a duplicate evaluator cannot fix either counterexample. Verdict: REJECT; require production behavior changed at existing seam.
5. **Representation:** required Claim -> semantically covered Native Witness, not just ClaimStatus == NativeStatus. Distinguish supported falsification from evidence-integrity errors. Do NOT demand global pointer uniqueness: explicit structured shared witnesses may cover multiple named claims. Verdict: minimal decision-relevant representation.
6. **Existing consumer and mature alternative:** FLAC/WAVE/PNG native verifiers, profile registry and evidence receipts remain natural providers. PNG legitimate metadata alias /metadata must remain supported via an explicit claim coverage annotation; generic /verification must not impersonate arbitrary claims. Verdict: REUSE, no new registry.

### Immediate public acceptance and proof duties

- v1 required structural FAIL with a stage receipt and no evidence-integrity defect => standingCoverage.verificationStatus=FAIL; profileVerificationComplete=false; legacy status=FAIL.
- v1 legacy PASS but missing required gate => standing UNKNOWN, legacy PASS preserved.
- v2 two different required claims both pointing to generic /verification.status=PASS => requiredEvidenceAssessment.complete=false; no Profile complete.
- v2 a status-matching native witness named by claim or explicitly declaring coverage of several claim IDs may support those claims. One witness need not be unique to one claim; this is only structured native evidence, not independent assurance of native tool honesty.
- Required FAIL with mismatched pointer => UNKNOWN; witnessed FAIL with native aggregate FAIL => scoped FAIL; aggregate PASS with required FAIL => UNKNOWN.
- Native PNG metadata observation using /metadata must remain valid via explicit claim tag. FLAC/WAVE and other PNG native pointers retain their source-defined meaning.
- Extend the existing finite model checker with claim-specific states only after the production seam is implemented. A finite model of syntax is not a proof of deployed tool or target application.

Scope restriction: These are small repairs to existing T1–T3 code; T4–T8 remain consumer-led. No weak-model evaluation, new Registry/Host Work schema, universal policy engine or duplicate Spec.

### Cross-disciplinary selection: the minimum necessary set

- **Mathematics — Cousot abstract interpretation:** report a bounded abstract status as a sound projection under explicit native-evidence assumptions, not as an exhaustive truth about format or application. Missing/contradictory evidence is UNKNOWN; a witnessed required FAIL is a real scoped falsifier. Source: https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml .
- **Computer science — Parnas information hiding and contract refinement:** keep claim-specific witness semantics within the existing Artifact Owner and native verifier seam; do not add a second cross-owner Governor, evidence registry or observer. A replacement must preserve consumer-observable guarantees under the same environment. Source: https://doi.org/10.1145/361598.361623 .
- **Systems engineering — NASA V&V/traceability:** attach required claims to source-native observations, exact test witnesses and separate Game/Publication/Data acceptance. Unit/native test PASS verifies bounded technical requirements, not fitness for domain use. Source: https://www.nasa.gov/reference/system-engineering-handbook-appendix/ .
- **Management science — Goldratt Theory of Constraints:** spend the next implementation slice on the real bottleneck (incorrect qualification at the Artifact seam), rather than optimizing the count of checks, drafting a new plan or making every Owner await blanket approvals. Limit simultaneous work to proven dependency frontiers; do not impose an arbitrary global WIP threshold. Source: https://www.tocinstitute.org/theory-of-constraints.html .
- **Process engineering — Matt/Superpowers/ECC:** public-seam RED/GREEN, separate Standards/Spec review, fresh native full verification, targeted audit evidence and subtractive code cleanup. Skills guide procedure, never change project authority.

**Strict separation:** This is a management and software-engineering choice; the finite proof checks represent bounded abstract source properties only. No claim of a proof that all real native tools are truthful, no new public service, and no secret "success" status owned by an Agent.

## Out of scope

Building another Runtime/Host/Harness, universal file taxonomy, custom CAS, second LEGO registry, generic OCI Registry, universal trust policy, weak-model experiments, mandatory heavyweight audits for routine work, or all-family profile-v2 production promotion.

## References

- Existing Ordivon `AGENTS.md`, `.agents/skills/recursive-lego-calculus/SKILL.md`, `capabilities/artifact/README.md`.
- Matt Pocock `skills/engineering/to-spec`, `to-tickets`, `implement`, `tdd`, `code-review`.
- obra/superpowers `writing-plans`, `test-driven-development`, `verification-before-completion`, `using-git-worktrees`.
- affaan-m/ECC `hooks`, `rules`, `skills`: selective reuse of quality gate semantics, without wholesale installation.
