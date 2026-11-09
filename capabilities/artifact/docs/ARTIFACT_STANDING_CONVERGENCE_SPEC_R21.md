# Artifact Standing Convergence — R2.1 Implementation Spec

**Authority:** Artifact Owner, with independent Domain consumers. **SourceCut:** \`3b43977e682d8c7668f6371ffd998c7821e4312a\` (remote main at 2026-11-09 21:38 +08). **Status:** implementation contract / first vertical slice in progress. **Method suppliers:** Matt Pocock Skills (to-spec, to-tickets, implement, tdd, code-review), obra/superpowers (writing-plans, TDD, isolated worktree, verify-before-completion), affaan-m/ECC (selective feedback/hook discipline, NOT wholesale harness installation). Upstream commits: Matt \`4ae2317ddb22b046e26455e4f9c9b3aaaf62212d\`, Superpowers \`22f0b463e7a5e579904dd6211a520321035526f7\`, ECC \`d2ef2680594f9a17526a6e1a2e18b3d242c5d17b\`. Upstream method source is not Ordivon execution authority.

## Problem statement

Artifact has two verification backbones: \`artifact_verification/stage.py\` for v1 Build/Delivery and \`scripts/artifact_verify.py\` for v2 profile-bound native verification. The two paths do not consume one canonical decision semantics. A native aggregate PASS may be true while profile-required evidence is incomplete; older release snapshots and LOCAL_LIVE_PROVEN are not current runtime authority. Historical \`planning/prototypes/standing_decision_r1.py\` is not production. The aim is NOT to manufacture a third workflow, registry, owner, policy, or verifier.

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

Formal archetype: \`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)\`.

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

Safety law, under well-formed inputs: \`complete => all_required_supported_by_nonself_matching_native_evidence AND no_identity_contradiction\`. Also \`DOMAIN_ACCEPTED\` cannot be derived by this evaluator. No theorem about actual native tool honesty, toolchain closure, transport effects, or target applications is claimed.

### Compatibility and negative controls

- v1 stage \`status=PASS\` may mean all *executed* gates passed while \`profileVerificationComplete=false\`; preserve this distinction until consumer migration, never promote missing gates.
- v2 native \`status=PASS\` may be legacy compatible while \`profileVerificationComplete=false\`; preserve existing consumers and add scoped Standing, never reinterpret as full acceptance.
- FLAC/WAVE/PNG claim-complete routes require explicit claimResults/native status pointers; do not weaken.
- v1 and v2 profile definitions are NOT globally equivalent. Prove each common axis or mark UNKNOWN.
- No full snapshot guarantee for sidecar formats until dependency closure is bound.
- Negative cases: absent claim, NOT_EVALUATED claim, explicit FAIL, conflicting native pointer, missing required gate, mismatched native identity, tool identity drift, source rebind, fake consumer success.
- Keep old API/schema working while expand–migrate–contract is in progress.

## Implementation decisions

1. Reuse \`artifact_verification/claim_coverage.py\`, \`native_identity.py\` and current v1 receipt format. Prefer a pure shared coverage/decision helper only if two real consumers justify it; no registry/service.
2. Keep raw observations and existing compatibility statuses; expose a new explicit Standing projection only where required.
3. The first unit of change cuts vertically through the v1 stage and existing v2 verification service, with one shared deterministic requirement-coverage operation and caller-visible negative tests.
4. Next migrate old standing prototype tests to the production contract; retire the prototype if no producer/consumer still needs it.
5. Preserve current profile authority, snapshot policy, tool identity and all required non-claims.
6. Refactor DirectPython/OCI only after shared semantic integration proves removal of duplicate responsibility; delete obsolete branches rather than adding shims permanently.
7. Use existing natural Owner tasks and GitHub CI, not imported ECC hook sets or a new approval/agent runtime.
8. No weak-model trials, performance-score game, or unnecessary universal Work schema. Wider Host/Harness adoption is a separate, consumer-proven change.

## Testing decisions

Use existing public entrypoints \`execute_verify_stage\` (through DirectPython provider) and \`scripts/artifact_verify.verify_request\` plus the pure Standing API. TDD red-green-refactor on counterexamples; independent expected values from Profile declarations and raw native receipts; avoid mock-only tests and self-certified snapshots. Use owner-native \`mise run verify\` and focused \`pytest\`. Run current finite model checks; property checks must cite the production function actually checked. At least one real native and one independent consumer readback before a final production promotion. Never call a unit-test PASS a deployed-consumer PASS.

## Tickets and blocking edges (Matt tracer bullets / Superpowers small steps)

| Ticket | Blocked by | Consumer-visible delivery | Exact seam / tests |
|---|---|---|---|
| T1 Shared coverage semantics | none | Both v1 and v2 publish the same bounded coverage vector; legacy statuses preserved | \`artifact_verification/claim_coverage.py\`, \`stage.py\`, \`artifact_verify.py\`, new cross-entrypoint test |
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

## Out of scope

Building another Runtime/Host/Harness, universal file taxonomy, custom CAS, second LEGO registry, generic OCI Registry, universal trust policy, weak-model experiments, mandatory heavyweight audits for routine work, or all-family profile-v2 production promotion.

## References

- Existing Ordivon \`AGENTS.md\`, \`.agents/skills/recursive-lego-calculus/SKILL.md\`, \`capabilities/artifact/README.md\`.
- Matt Pocock \`skills/engineering/to-spec\`, \`to-tickets\`, \`implement\`, \`tdd\`, \`code-review\`.
- obra/superpowers \`writing-plans\`, \`test-driven-development\`, \`verification-before-completion\`, \`using-git-worktrees\`.
- affaan-m/ECC \`hooks\`, \`rules\`, \`skills\`: selective reuse of quality gate semantics, without wholesale installation.
