# LEGO Theory Wave 1 — Prospective Cross-Domain Validation R1

Date: 2026-09-18
Status: PROSPECTIVE VALIDATION COMPLETE / FOLLOW-UPS OPEN

## Purpose

Test whether the first four mature-theory lenses improve real Ordivon system analysis rather than merely renaming facts already visible in ordinary LEGO decomposition.

Wave 1 lenses:
- Systems Engineering;
- Design Structure Matrix (DSM);
- Feedback Control;
- STAMP/STPA.

The acceptance criterion was deliberately stronger than "produced a diagram". A lens must either:
1. expose an architecture-relevant fact that changes a model/decision;
2. expose a system-level hazard or experiment that ordinary component review missed; or
3. provide useful falsification/confirmation without inventing new authority.

No theory-specific fields may enter the shared LEGO schema from this trial alone.

## Case A — Ordivon Runtime

Source revision examined:
- `fbb4d17a941a88fd2c8422d91a33f07ad9f98ad7`

Lenses:
- Systems Engineering;
- DSM;
- Feedback Control.

### Systems Engineering result

The existing boundary survived review:

`admitted operation -> controlled physical execution -> durable evidence -> reconciliation`

Runtime still must not own Task meaning, domain completion, workflow priority, or generic project semantics.

Result: CONFIRMATORY.

### DSM result

The six-node planning graph is intentionally sparse and showed no evidence that a new cross-node cluster or merge would improve authority boundaries. In particular, the proposed ExactLeaseGeneration responsibility should not be collapsed into generic execution ownership merely because it targets the same physical execution.

Result: CONFIRMATORY / NO RE-CUT.

### Feedback Control result

The plan represented:

`ExecutionOwnership -> ResultArtifact -> EffectKernel`

but omitted the return control edge by which reconciliation constrains recovery/redispatch.

The missing loop is:

`T03 ExecutionOwnership -> T04 ResultArtifact -> T05 EffectKernel -> T03 ExecutionOwnership`

This was promoted into the Runtime planning projection because the T05 responsibility already explicitly owns reconciliation rather than blind redispatch.

Integrated Runtime main commit:
- `cf0e0adf118d4f143fd7117d6a9592343261d8e0`

No Runtime execution authority changed.

Result: POSITIVE MODEL CORRECTION.

## Case B — Ordivon Game

Source revision examined:
- `cb8dc640f93577b7d02e55ae3c58afb362285ea2`

Lenses:
- Systems Engineering;
- Feedback Control.

### Systems Engineering result

The current Game boundary survived review:
- ProductAuthority owns player-visible product semantics.
- MechanismLibrary remains advisory.
- ExperimentLane cannot select product direction.
- PlayerEvidence cannot fabricate Human preference.

Result: CONFIRMATORY.

### Feedback Control result

The Player Evidence Programme already defines an explicit decision-feedback cycle:

`Decision -> ClaimNeeded -> Evidence -> ScopedStanding -> Decision -> ReopenCondition`

However the project LEGO plan represented only:

`G01 ProductAuthority -> G05 PlayerEvidence`

and omitted the evidence return path into design composition.

A model correction was therefore prepared:

`G05 PlayerEvidence -> G04 CompositionPlanner [OBSERVATION]`

with the explicit non-equivalence:

`PlayerEvidence feedback != product-selection authority`

Validated detached commit:
- `3138d9157e3c933287be1cc3b1879aea7eef3593`

It was not cherry-picked into the current Game main during this trial because that local branch was clean but already `behind origin/main 1`; the analysis did not manufacture a merge/rebase decision.

Result: POSITIVE MODEL CORRECTION / INTEGRATION DEFERRED BY REPO STATE.

## Case C — Agent Service R14

Authoritative active R14 workspace was used rather than historical files on current `ordivon-next/main`.

R14 commit after its own implementation verification:
- `0721009237365ea61cd975bd187be5171f1dcd52`

R14 verification observed:
- 15 focused tests PASS;
- 5 Browserless-reader tests PASS;
- 1 receipt-structure test PASS;
- 214 full repository tests PASS.

Lenses:
- Systems Engineering;
- STAMP/STPA.

### Systems Engineering result

R14 preserves strong authority separation:
- TransportBinding owns immutable route/protocol/security-requirement identity.
- CredentialReference owns secret-free locator metadata.
- IdentityProof owns authentication evidence.
- PolicyDecision owns a historical authorization decision.
- CredentialMaterialProvider owns transient secret material.
- provider-specific ledgers retain their own effect truth.

Result: CONFIRMATORY.

### STPA result — authority lifetime / revocation ambiguity

STPA asks whether a control action can become unsafe because timing or system state changed even when each component behaves according to its local specification.

R14 binds policy/identity/credential evidence before delivery. At credential-material resolution time it re-checks:
- current IdentityProof;
- credential resource;
- required scopes;
- material issuer/resource/scopes;
- expiry.

However, the delivery path does not re-check SemanticSession state, nor does PolicyDecision currently expose a current/revoked/expired state.

A bounded no-external-side-effect characterization test was run against the R14 code using its fake Delivery adapter:

`Session OPEN -> create Delegation/PolicyDecision/TransportBinding -> close Session -> deliver(binding)`

Observed:

`SESSION_BEFORE OPEN`
`SESSION_AFTER CLOSED`
`DELIVERY_AFTER_CLOSE committed submitted True`
`POLICY_DECISION True`

Execution evidence:
- Runtime Job `job-01a0b3a6-06dc-7433-9e35-6f17093b8b29`

This does not prove a bug because the domain contract has not yet stated whether closing a Session must revoke already-created Delegation/Binding authority.

It does prove a missing system-level decision:

> Is delivery authority historical once bound, or must it remain contingent on current Session/delegation/policy standing?

Candidate unsafe control action:
- provide Delivery after the higher-level authority that originally justified the Binding is no longer intended to be current.

Candidate constraints, mutually exclusive until the semantic owner decides:
1. explicitly specify that admitted/bound delivery survives Session closure and define its lifetime independently; or
2. add an effect-time current-authority gate covering the intended revocation sources.

Result: POSITIVE HAZARD DISCOVERY / SEMANTIC CONTRACT UNRESOLVED.

No R14 production change was made by this analysis.

## Case D — Browser / Provider Security

Evidence examined:
- `knowledge/lessons/cloudflare-provider-security-boundary-r1.md`
- `knowledge/lessons/cloudflare-provider-security-exp-r5.md`

Lenses:
- Systems Engineering;
- STAMP/STPA;
- Feedback-control interpretation.

The existing design already contains a mature closed-loop diagnostic structure:

`observe -> localize -> one-variable differential -> classify -> repair/replace node -> requalify`

STPA review also found that the most important unsafe-control pattern is already explicitly blocked:
- a third-party challenge must not become a reward/oracle for repeated security-control bypass optimization;
- challenge standing must not be promoted into root-cause truth;
- consequential SEND remains behind a fail-closed effect boundary.

R5 further separates host/container effects from Browserless-control effects rather than treating all fingerprint differences as one cause.

Result: CONFIRMATORY. The mature-theory lens did not justify a new architecture node.

## Cross-domain verdict

### Systems Engineering — KEEP

Value:
- consistently protects boundary, environment, external-authority and whole-system framing.

Observed contribution:
- mostly confirmatory in this wave, but prevented false authority promotion.

Standing:
- KEEP AS OPTIONAL FOUNDATION LENS.

### DSM — KEEP, CONDITIONAL

Value:
- strongest when interaction density is high and module boundaries are disputed.

Observed contribution:
- Runtime sparse plan did not justify a re-cut.

Standing:
- KEEP AS CONDITIONAL DIAGNOSTIC.
- More dense-project evidence is required before claiming broad Ordivon value.

### Feedback Control — KEEP

Value demonstrated across two unrelated domains:
- Runtime: discovered missing reconciliation feedback edge.
- Game: discovered missing player-evidence return edge.

Standing:
- PROSPECTIVELY VALIDATED AS AN OPTIONAL DYNAMIC-SYSTEM LENS.

### STAMP/STPA — KEEP

Value:
- surfaced an Agent Service authority-lifetime question despite the implementation's full test suite passing;
- confirmed existing Browser Security unsafe-control constraints.

Standing:
- PROSPECTIVELY VALIDATED FOR HIGH-CONSEQUENCE / AUTHORITY-RICH SYSTEMS.

## Core-promotion result

No new mandatory LEGO Core field is promoted.

Specifically:
- feedback remains expressible through existing CONTROL/OBSERVATION edges;
- hazards remain derived analysis evidence;
- authority lifetime/revocation remains a candidate concern, not a universal schema field;
- DSM matrices remain derived projections;
- Systems Engineering context models remain optional lenses.

The existing project schema therefore remains unchanged.

## What Wave 1 taught the meta-method

The useful selection rule is now stronger:

`Theory usefulness != vocabulary richness`

Prefer a lens when it causes one of:
- a corrected boundary;
- a corrected edge;
- a falsifiable experiment;
- a newly exposed hazard;
- a justified no-change decision.

If none occurs, stop the lens rather than produce more documentation.

## Next theory wave admission

Wave 2 should not begin by expanding Core.

The next candidates are admitted only as optional lenses/operators:
- compositional contracts / compositionality;
- causal intervention;
- FMEA/FTA reliability analysis;
- information-flow analysis.

Their prospective acceptance must use the same cross-domain criterion applied here.
