# LEGO 2.1 — four-owner transition-system seam

**Status:** bounded formal model and falsification evidence, not a deployed owner implementation, a universal LEGO registry, or a new mathematical engine.

## Mature mathematical core

LEGO 2.1 treats a LEGO as a **consumer-conditioned replaceable responsibility**, rather than automatically a file, Tool, Skill or Agent. Its familiar coordinates `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` are optional semantic views: minimize them to the question being answered.

For this owner boundary, reuse the standard typed transition-system model `(S, Init, Next)`, invariant checking by TLC, and **assume–guarantee** contracts on its seams. The existing `packages/composition` Cognitive Circuit, JSON Schema and Verification Obligation remain responsible for typed ports, caller-authored gate requirements, exact digests and bound verifier identities. This model is not their replacement.

- **Host:** maintains Work continuity; it may record verified acceptance, but does not create the domain verdict.
- **Harness:** proposes a bounded Agent action, not physical dispatch authority.
- **Network:** observes route readiness, not effect permission.

- **Runtime:** owns physical admission, dispatch, ambiguity and terminal standing.
- **Consumer/domain:** supplies an independent outcome witness; `ConsumerObserve` is an abstract oracle in this model.

**Contract composition is conditional**, not a requirement to invoke every owner.
A direct deterministic Runtime Tool may have no Harness Run, and a local contained
job may have no Network route consumer. `RequiresHarness` and `RequiresNetwork`
are *abstract model parameters*, not production flags or policy. An Owner seam
must discharge only assumptions actually demanded by that task. The four TLC
configs cover direct-local, direct-egress, Harness-local, and Harness-egress.
All still require Runtime-owned dispatch and separate Consumer evidence for
Host semantic acceptance. A passing mode says nothing about an authority
grant at live admission.

In `Lego21OwnerBoundary.tla`, TLC checks at-most-once physical dispatch, that neither a ready route nor Harness proposal alone grants physical execution, that ambiguity never implies success, and that Host acceptance requires a consumer witness. `dispatchCount ∈ 0..2` deliberately permits the invalid value 2 in `TypeOK`, so at-most-once is an independently falsifiable invariant.

## Reuse the existing native checker

The Composition Owner native verify now requires the Formal task and checks all four Harness/Network optionality configurations using the existing Runtime public SHA-verified upstream TLA+ toolchain. The exact tool-only cross-Owner dependency is admitted in the canonical dependency contracts. No Runtime Job/Attempt internals or execution authority are imported. A model, tool integrity, or configuration failure now blocks Owner acceptance.

The Runtime owner pins both TLA+ tools digests in `services/runtime/formal/toolchain.lock.json`. Use the digest-verified tool; **no extra formal checker or package is introduced**.

```bash
export ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools-v1.7.4.jar
services/runtime/scripts/tla-formal verify
(
  cd packages/composition/formal
  java -cp "$ORDIVON_TLA_TOOLS_JAR" tla2sany.SANY Lego21OwnerBoundary.tla
  for cfg in Lego21OwnerBoundary.cfg Lego21OwnerBoundary.direct-local.cfg Lego21OwnerBoundary.direct-egress.cfg Lego21OwnerBoundary.harness-local.cfg; do
    java -cp "$ORDIVON_TLA_TOOLS_JAR" tlc2.TLC -workers 1 -config "$cfg" Lego21OwnerBoundary.tla
  done
)
```

**2026-10-25 original model:** pinned TLC 2.19, 12 generated states,
10 distinct states, complete graph depth 8, zero invariant violations.

**Conditional-assumption model:** the same pinned TLC checked all four
independent Boolean configurations with zero invariant violations:

| Required input pair | Model configuration | Distinct states |
| --- | --- | ---: |
| Harness + Network | `Lego21OwnerBoundary.cfg` | 10 |
| Neither (direct-local) | `Lego21OwnerBoundary.direct-local.cfg` | 28 |
| Network only (direct-egress) | `Lego21OwnerBoundary.direct-egress.cfg` | 16 |
| Harness only (Harness-local) | `Lego21OwnerBoundary.harness-local.cfg` | 16 |

A transient negative oracle disabled both proposal and Network observation.
The direct-local model still reached dispatch (a TLC counterexample to the
intentionally false `NoDispatchEver` claim); the other three could not
dispatch without their required input. This rejects an **unconditional**
all-owner prerequisite without weakening the required ones. Independent temporary mutations (remove the Host consumer-evidence guard; remove the Runtime Network-readiness guard) each triggered the intended TLC invariant violation. These mutations were not committed.

**R2.1 type refinement — consumer witness scope.** The previous
`consumerEvidence: BOOLEAN` could not express the concrete error class
"a terminal result carries evidence belonging to another Work/consumer".
The existing model now uses the *same single variable* with the finite
standing `{"none", "matching", "foreign"}`. The abstract
`ConsumerObserve` can report either matching or foreign evidence after
terminal observation; only matching evidence can authorize the existing
`HostAccept` transition. A foreign observation remains visible as
non-admissible evidence rather than being silently treated as `TRUE`.

A deliberate RED mutation broadened `HostAccept` to any non-none
evidence. The already configured `NoHostAcceptanceFromRuntimeAlone`
invariant then produced a real TLC counterexample: terminal Runtime,
`consumerEvidence="foreign"`, `host="accepted"`. Restoring the exact
matching guard and retaining the concurrently selected admission-time
Network degradation model produced four GREEN TLC finite-state exhaustions
under the upstream digest-verified tool: **18, 32, 32 and 18** distinct
states for Harness+Network, direct-local, direct-egress and Harness-local.
The committed native non-vacuity probe for post-admission Network
degradation remains PASS. This is a typed abstract source/consumer
contract and
does **not** establish that a deployed Host checks provenance; the
actual Owner verifier remains responsible for binding evidence to
the correct Work and SourceCut. This replacement needs no new proof
engine, global registry or test framework.

**Non-vacuity admission:** the existing Composition native Formal task now
requires the *opposite* reachability witness as a standalone negative TLC
configuration. The intentionally false
`ForeignEvidenceIsUnreachable` invariant must produce a real TLC
counterexample with `consumerEvidence="foreign"`; an exit status by
itself never qualifies. If future simplification accidentally makes
foreign evidence unrepresentable, owner verification fails instead of
silently reporting an easy safety PASS. This reuses the same digest-verified
TLC and the existing expected-counterexample gate structure used for
post-admission Network degradation.

**Claims explicitly excluded:** implementation refinement for Rust/Host/Harness/Network, current network availability, authorization, identity, consumer evidence authenticity, domain success, retries, liveness, unbounded safety and deadlock freedom. `CHECK_DEADLOCK FALSE` is intentional for terminal stuttering; no fairness property is included. Real acceptance needs existing natural-owner native tests mapping abstract transitions to their physical and semantic effects. Do not promote model PASS into reality PASS.

Foundations: Leslie Lamport's TLA+/TLC, established assume–guarantee contracts (e.g., Pacti), and existing JSON Schema Draft 2020-12 port contracts.

**R2.1 follow-up (2026-10-25):** distinguish *actual consumer obligations* from indiscriminate all-owner participation. Original network-and-Harness-required model is preserved as one of four profiles. Other configurations remove only the optional prerequisite, not any owned effect or consumer-evidence invariant. A TLC invariant counterexample against an intentionally false `dispatchCount=0` assertion for direct-local is the reachability witness that modeling optional modes is not vacuous.

## Admission-time evidence and mutable readiness (2026-10-25)

In the four-owner bounded model, Network may change from ready to unknown
after Runtime admission. An admission witness is latched only by RuntimeAdmit,
and the existing dispatch invariant checks that historical witness rather
than claiming a mutable route always stays ready.

The four TLC configurations explored 16, 28, 28 and 16 distinct states,
respectively, with no invariant violations. Negative controls showed
that freezing the old live-readiness invariant gives a counterexample,
and removing Network's admission guard produces an unwitnessed dispatch.

This is bounded model evidence, not live Runtime/Network refinement.
The native `formal:verify` task also checks the model is **non-vacuous**:
a dedicated expected-counterexample config must make TLC find an admitted
Network degradation. A missing transition or incorrectly restricted model
therefore fails owner verification instead of silently yielding four PASSes.

## R2.1 COMP-TERM-01: committed terminal evidence is independent of observed terminal (2026-10-25)

**Typed problem LEGO:** COMP-TERM-01 = {class: STATE / EVIDENCE_QUALIFICATION / CROSS_OWNER, naturalOwner: Composition Formal, consumers: Host Work acceptance and Runtime terminal-result source, standing: FINITE_MODEL_VERIFIED; IMPLEMENTATION_REFINEMENT_UNKNOWN}. Registered here in the existing owner-owned Formal README and native tests; no new global issue registry, scheduler, verifier or proof language.

**Counterexample-guided question.** The former four-Owner composition model represented a terminal Runtime and matching domain evidence, but did not separately represent the durability of the terminal result. A matching Consumer observation does not automatically establish a committed Runtime receipt. Runtime's existing RuntimeDispatchR1 model has a distinct TerminalEvidenceIsCommitted obligation: reuse its assumed meaning at the Composition boundary without copying Runtime private Registry code.

**Refinement.** Add a finite variable terminalReceipt in {none, pending, committed}. RuntimeObserveTerminal marks pending; RuntimeCommitTerminal independently marks committed. HostAccept needs consumerEvidence=matching AND terminalReceipt=committed. Admission/dispatch Network and Harness optionality are unchanged. Safety invariant NoHostAcceptanceWithoutCommittedTerminalReceipt requires host=accepted => terminalReceipt=committed.

**Concrete bounded evidence (native SHA-256-verified TLA+ Tools v1.7.4, TLC 2.19):** Harness+Network 24 distinct / 52 generated states; direct-local 44 / 124; direct-egress 44 / 118; Harness-local 24 / 54. No admitted safety invariant violation. A deliberately false PendingMatchedTerminalReceiptIsUnreachable condition produced an actual TLC trace RuntimeAdmit -> RuntimeDispatch -> RuntimeObserveTerminal -> ConsumerObserve, with terminalReceipt=pending, consumerEvidence=matching, host=open. In a temporary RED copy, removing only HostAccept's committed-receipt guard yielded a named NoHostAcceptanceWithoutCommittedTerminalReceipt violation with host=accepted, terminalReceipt=pending. The temporary mutation was not committed. The existing native formal:verify task now requires the named reachable counterexample as a non-vacuity gate.

**Proof boundary.** This is a finite abstract state-machine result, NOT a machine proof that live Host/Runtime always preserve the invariant. Model RuntimeCommitTerminal is an abstract owner guarantee, not proof of physical database commit. Concrete follow-up requires exact Work, Attempt, SourceCut, Runtime committed result, and independent domain-acceptance witnesses from their native owners. Semantic task success, fairness/liveness, bounded completion, real network authority, exact-once external effects and Rust-to-TLA refinement remain UNKNOWN. No automatic promotion from a model PASS to production PASS. No generic Minimum Sufficient Representation assumption.

Mathematical LEGO reused: Lamport TLA+ transition systems and TLC; assume-guarantee contract composition; counterexample-guided abstraction refinement (Clarke et al., CAV 2000, DOI 10.1007/10722167_15). No new math engine.
