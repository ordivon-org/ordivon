# Ordivon Architecture Re-Anchor R1

Date: 2026-09-28
Status: **CURRENT ARCHITECTURE CONSTITUTION**

Machine-readable companion: `docs/architecture/architecture-constitution-r1.json`.

## One sentence

**Ordivon is a verified-composition system: it binds real problems to replaceable knowledge, capabilities, Agents and providers, makes authority and verification obligations explicit, and leaves execution, durable state and semantic truth with their natural owners.**

## Truth order

No architecture document is runtime, provider, Git, domain, or scientific truth. Present-tense claims must be re-established from the natural owner.

```text
CURRENT PHYSICAL TRUTH
  > CANONICAL SOURCE / CONFIGURATION
  > LIVE OWNER STATE / PROVIDER READ-BACK
  > DURABLE REGISTRY / RECEIPT
  > TEST / VERIFICATION EVIDENCE
  > CURRENT DOCUMENTATION
  > PLANNING ARTIFACT
  > HISTORICAL CHAT / MEMORY
```

The natural owner for the exact claim still decides which physical source is authoritative. A provider effect is not established by Git; a source contract is not established by a runtime projection.

## Minimal semantic kernel

The smallest cross-domain Ordivon kernel is deliberately narrow:

1. **Cognitive Circuit** — exact task-local composition of already selected roles/components.
2. **Interface Contract** — compatibility/currentness expectations at a seam.
3. **Authority Obligation** — which authority must permit a consequential transition.
4. **Verification Obligation** — which verifier/evidence must establish a claim.

`Successor Contract` and `Agent Run Binding` are conditional kernel extensions activated only when a successor/improvement transition or Agent cognition is actually required.

The kernel does not execute work, own workflow state, host collaboration, store universal evidence, or decide domain success.

## Standard substrate owners

These are important Ordivon substrates, but they are not the semantic kernel:

| Concern | Natural owner |
| --- | --- |
| bounded Agent cognition/run continuity | Harness |
| physical local execution | Runtime |
| semantic work continuity/collaboration | Host |
| northbound routing/projection/protocol adaptation | Gateway |
| durable timers/retries/orchestration | Temporal or provider-native workflow |
| provider effect/acceptance | provider |
| authentication | identity provider |
| authorization decision/enforcement | provider IAM / AuthZEN-class PDP+PEP / scoped policy owner |
| telemetry | OpenTelemetry ecosystem |
| operational lineage | OpenLineage |
| research provenance/package | W3C PROV / RO-Crate and Study owner |
| build provenance | SLSA/provider build authority |
| discovery/advisory procedure | Catalogs / Agent Skills |

A task may bypass Harness, Runtime, Host, Gateway or Temporal when the natural provider directly satisfies the required contract.

## Owner-local lifecycle model

There is no global Ordivon `Task -> Run -> Session -> Attempt` tree.

```text
Host:       Work -> WorkSnapshot / Social / Attention
Harness:    HarnessRun -> Turn -> ProviderCall / ToolStep -> CompletionProposal
Runtime:    Workspace -> Job -> Attempt -> Runtime Artifact
Temporal:   Workflow -> Event History / Activity
Provider:   provider-native effect identity -> provider read-back
Domain:     domain-native state/result/verdict
```

Cross-owner continuation uses explicit references. Identical words in different owners do not create one ontology. In particular, `Session`, `Run`, `Artifact`, `Profile`, `Evidence` and `Checkpoint` must be owner-qualified whenever ambiguity is possible.

## Recovery law

Response loss must not imply work loss. Re-entry composes existing owner-local recovery contracts:

```text
WorkRef
  -> caller/HarnessRun reference when cognition exists
  -> durable Harness snapshot + unresolved Tool intents
  -> deterministic requestId / provider effect reference
  -> Runtime Job or provider read-back
  -> reconcile uncertain effects
  -> resume cognition / collaboration
```

Do not create a global `RecoveryManager`, Session database or Checkpoint service to implement this path.

## Evidence law

Evidence is claim-relative, not a central subsystem.

```text
Observation != Evidence != Claim != Verification != Decision
```

Runtime terminal evidence can establish physical execution. It cannot establish domain completion. Telemetry can establish an observation. It cannot grant authority. Provider read-back may establish a provider effect. It cannot by itself establish the consuming domain's success criterion.

## Repository placement law

Repository placement is navigation and build locality only. It is not semantic type.

Current roots such as `services/`, `platform/`, `capabilities/`, and `domains/` may remain while their owner seams are clear and independently verified. Moving them into `packages/` solely to make the root visually uniform is not architecture progress.

Structure R2 successfully extracted Composition, canonical Skills, the portable control Plugin, catalogs, profiles and selected studies. Its remaining path-only relocation waves S3, S4, S6, S7 and S9 are cancelled by this re-anchor. S5 continues only as targeted `meta/next` residual disposition; S8 continues only as evidence-driven fitness/contract guards.

## ORDIVON IS NOT

Ordivon is not a workflow engine, database, IAM system, provider-status registry, universal evidence store, universal Task system, global Session system, message broker, network stack, model provider, mega-Agent, mega-Gateway, domain ontology, or replacement for Temporal/PostgreSQL/GitHub/provider-native truth.

## Architecture Constitution

1. Physical truth outranks architecture documentation.
2. Every durable truth has one natural owner.
3. Repository placement never transfers semantic authority.
4. Composition never mints execution or effect authority.
5. Capability, provider and authority are separate concepts.
6. Authentication, authorization, semantic actor identity and provenance labels are separate concepts.
7. Observation, evidence, verification and decision remain distinct.
8. There is no Universal Task, Session, Profile, Bundle, Evidence or Registry.
9. Harness owns one bounded Agent Run; it does not own Work, workflow or domain truth.
10. Runtime owns physical execution; it never judges semantic completion.
11. Host owns semantic continuity/collaboration; it never owns physical execution truth.
12. Gateway routes/projects/adapts protocols; it owns no downstream owner truth.
13. Durable workflow remains external unless a concrete workload proves an irreducible gap.
14. Unknown external effects are reconciled and fenced; they are never blindly replayed.
15. DELETE CUSTOM BY DEFAULT. Historical investment grants no architectural privilege.

## Admission rule for new core abstractions

A proposed new cross-domain abstraction is rejected unless it can show all of:

- at least two independent real consumers;
- no mature external owner/standard already owns the semantic;
- a unique natural owner and durable-state boundary;
- a stable public contract independent of one provider/domain;
- an independently testable failure/recovery contract;
- measurable reduction of coupling, failure domain or repeated irreducible duplication.

A new `Manager`, `Registry`, `Service`, database table, middleware layer or framework is not evidence of architectural progress.

## Growth direction

Future capability grows through the stable seam:

```text
real problem
  -> task-local composition
  -> authority + verification obligations
  -> natural owner/provider
  -> owner-native result/evidence
  -> claim-specific verification
  -> domain verdict
```

Horizon 1 is convergence and deletion. Horizon 2 is composition/substitution. Horizon 3 is expansion through the stable seam, including multi-model cognitive circuits, larger Agent societies and cross-machine execution providers.
