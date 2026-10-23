# Verified Reintegration External-owner Convergence R1

Date: 2026-09-22
Status: **PLANNING / EXTERNAL-OWNER-FIRST / NO NEW CONTROL PLANE**

## Decision

Verified Reintegration R1/R2/R3.1 stays structurally intact.

The next optimization step is not a new Ordivon R4 runtime. It is a selective replacement
and projection programme that pushes each reusable semantic role toward a mature external
owner when that owner is actually suitable.

The governing rule is:

```text
EXTERNAL OWNER OR DELETE
```

with one important refinement:

```text
external theory/tool is admitted only for the semantic slice it actually owns;
it does not become a universal Ordivon authority.
```

## Current baseline

Existing Ordivon Verified Reintegration already owns only thin task-local composition glue:

- Cognitive Circuit R1: task-local composition IR + mechanical validation;
- Interface Contract R2: compatibility/currentness/admissibility projection;
- Cross-domain Verification R3.1: task-local binding + seam-specific verifier;
- R1 Composition Gate: bounded assumption discharge;
- mechanical closure never upgrades itself into domain acceptance.

The repository already contains real standards-native provenance/attestation substrates:

- W3C PROV-O for semantic derivation;
- OpenLineage for operational Job/Run/Dataset lineage;
- in-toto Statement / SLSA provenance and VSA where applicable;
- Sigstore/Cosign trust verification in Artifact.

Therefore no new generic Evidence service, Evidence DB, lineage ontology, or attestation
envelope is justified by this programme.

## External-owner disposition

| External owner | Semantic role | Disposition | Ordivon rule |
| --- | --- | --- | --- |
| Pacti | assume-guarantee algebra, composition, refinement, quotient, incompatibility diagnosis | **SHADOW_CANDIDATE** | evaluate only on machine-expressible seams; no dependency until a real pilot proves value |
| OCRA | temporal-contract refinement/model checking | **DEFER_TEMPORAL** | evaluate only after repeated trace/state-machine obligations exceed existing owner-native tests |
| OMG SACM 2.3 | structured assurance claims/argument/evidence interchange | **ACTIVATE_AS_PROJECTION_CANDIDATE** | export/import projection only; no SACM service/store or domain authority |
| GSN v3 | human-readable assurance argument notation | **VIEW_ONLY** | derive on demand from assurance projection; never canonical runtime truth |
| W3C PROV-O | semantic provenance/derivation | **KEEP_EXISTING_OWNER** | reuse current implementation; do not wrap in a second Ordivon provenance model |
| OpenLineage | runtime Job/Run/Dataset lineage | **KEEP_EXISTING_OWNER** | reuse current emitters/events; do not use it for semantic claim truth |
| SLSA/in-toto | artifact/build provenance and attestations | **KEEP_EXISTING_OWNER** | reuse Artifact substrate only where its semantics apply |
| Sigstore/Cosign | attestation/signature verification | **KEEP_EXISTING_OWNER** | retain Artifact trust ownership; no duplicate signing/trust layer |

## Why Pacti is not installed yet

Pacti is a particularly strong fit for three operations that Ordivon currently performs only
informally or manually:

```text
composition
refinement / substitutability
quotient / missing-component derivation
```

However current R1 Gate assumptions and guarantees are often semantic natural-language
statements with explicit owner/evidence boundaries. Such claims cannot be truthfully encoded
as a polyhedral or SMT contract merely to obtain a formal-looking result.

Therefore:

```text
free-text semantic Gate
        !=
Pacti contract
```

A Pacti adapter is earned only when a real seam already has typed machine variables and
machine-interpretable assumptions/guarantees.

The existing R1 edge `contractRef` and R1/R3 evidence references are sufficient attachment
points. No new generic formal-contract field is required before a real pilot demonstrates a
missing representation.

## Why OCRA is deferred

OCRA is a mature fit for temporal-contract refinement, especially stateful interaction
protocols. The current Web <-> Security dogfood already contains trace-like obligations
(replay, revocation, historical replay, step-up, approval), but today those obligations are
owned and tested by the native Web/Security implementations.

Introducing temporal logic is justified only when:

1. the same temporal obligation appears across multiple seams;
2. state-space bugs survive owner-native E2E tests;
3. an external temporal verifier can reduce—not duplicate—the trusted reasoning surface.

Until then OCRA remains an external reference, not a dependency.

## SACM / GSN role

SACM is the best current candidate for standardized assurance interchange around:

```text
Claim
Argument / inference
Evidence / artifact
Assumption / context
relationships
```

But SACM must not become:

- the source of domain truth;
- a new Ordivon assurance database;
- a replacement for Runtime/Host/Artifact evidence ownership;
- a prerequisite for every task.

The desired direction is a disposable projection:

```text
Circuit + Gate requirements + Gate results + Evidence refs
        |
        v
SACM-compatible assurance projection
        |
        +--> optional GSN view
```

The projection is useful only if another tool/person consumes it. No consumer means no
persistent projection service.

## Existing provenance split remains authoritative

```text
semantic derivation        -> W3C PROV-O
runtime dataflow lineage   -> OpenLineage
artifact/build provenance  -> in-toto + SLSA
signature/trust            -> Sigstore/Cosign
task-local composition     -> Ordivon R1/R2/R3.1 thin glue
```

These scopes are intentionally not collapsed into a universal graph.

## Optimization target A — contract algebra

Desired capability:

```text
System contract S
Existing contracts A + B
        |
        v
quotient
        |
        v
Missing contract C
```

This is the mature version of the LEGO question:

> What exact obligation/component is still missing?

Acceptance requires:

- typed inputs/outputs;
- machine-readable assumptions/guarantees;
- exact external tool/version identity;
- quotient result independently checked by compose + refinement;
- no semantic claim encoded more strongly than its evidence supports;
- result remains advisory until the natural owner supplies a concrete implementation/evidence.

## Optimization target B — substitutability

Desired capability:

```text
candidate contract
        |
        v
refines(existing contract)?
        |
        +--> yes: substitution candidate
        `--> no: incompatibility evidence
```

This supports Build-last / Reuse-first without requiring an Agent to judge every replacement
from prose.

Refinement never grants execution or effect authority.

## Optimization target C — assurance projection

Desired output is a standards-native argument projection, not another Ordivon truth store.

At minimum, an exported argument must preserve:

- exact Circuit/manifest identity;
- claim/gate identity;
- assumption and guarantee;
- verifier owner;
- supporting evidence references;
- support scope;
- unresolved assumptions;
- explicit non-claims;
- current standing.

A round trip must not convert `UNKNOWN` into `SATISFIED`, remove non-claims, or expand the
support scope.

## Optimization target D — defeaters

R1 currently emphasizes supporting evidence and explicit unresolved assumptions. Mature
assurance practice also benefits from explicit defeaters/counter-evidence.

Do not add a generic R1 schema field yet.

First collect at least three real cases where:

```text
supporting evidence remains valid
but a new defeater invalidates the claim/gate
```

If repeated, model defeaters through the selected assurance owner (prefer SACM/GSN
projection semantics) before adding an Ordivon-native primitive.

## Optimization target E — incremental revalidation

As evidence graphs grow, full revalidation should evolve toward dependency-driven
invalidation:

```text
changed evidence
      |
      v
affected Gate(s)
      |
      v
affected Circuit closure only
```

Reuse existing PROV/OpenLineage dependencies where they already describe the relevant edge.
Do not build a new global scheduler or lineage store for this purpose.

## Waves

### W0 — Freeze current owner boundaries

- no R1/R2/R3.1 redesign;
- no global contract registry;
- no new Evidence service;
- preserve mechanicalClosure != domainAcceptance.

Exit: current tests and repo architecture gates remain green.

### W1 — Formal-contract shadow selection

Find one real seam with machine-expressible variables. Prefer a bounded numeric/resource or
protocol-shape obligation over scientific/business semantic claims.

Run a pinned external formal-contract tool in shadow mode.

Exit criteria:

- compose/refinement result reproduces an existing accepted result;
- at least one deliberate incompatibility is detected;
- no authority changes;
- no production dependency is added.

### W2 — Quotient LEGO experiment

For the same or another typed seam, define:

- required system contract;
- known component contract(s);
- compute missing contract through quotient;
- compose the quotient back and verify refinement.

Exit:

```text
compose(known, quotient) refines(required)
```

and the quotient describes only an obligation, not an invented implementation.

### W3 — Assurance interchange shadow

Create one disposable SACM-compatible projection for an existing R3.1 Circuit/Gate package.

Round-trip and compare exact bounded semantics.

Exit:

- claim/gate identity preserved;
- evidence references preserved;
- support scope and non-claims preserved;
- no standing upgrade;
- no new SACM DB/service.

### W4 — Optional GSN view

Only if a Human review consumer exists, derive a GSN view from W3.

Exit: visualization adds no authority and can be regenerated from the assurance projection.

### W5 — Temporal-contract pressure test

Only after repeated temporal seams exist, compare owner-native E2E against OCRA or another
mature temporal-contract/model-checking owner.

Exit: adopt only if it finds defects or reduces duplicated bespoke verification.

### W6 — Admission decision

For each candidate:

```text
ADOPT_EXTERNAL
KEEP_SHADOW
DEFER
DELETE_EXPERIMENT
```

Only ADOPT_EXTERNAL candidates may be added to the current external-ownership policy.

## Kill criteria

Stop an experiment if any of the following is true:

- semantic prose must be falsely converted into numeric/formal predicates;
- the external model loses owner identity, support scope, or non-claims;
- a projection becomes a second source of truth;
- a new service/database is required before a real consumer exists;
- the external tool duplicates owner-native tests without finding new defects;
- the tool requires weakening current Python/toolchain policy for no demonstrated value;
- round-trip changes claim standing;
- a generic abstraction is justified only by one seam.

## Result

The desired architecture is not:

```text
Ordivon Universal Formal Methods Platform
```

It is:

```text
R1/R2/R3.1 thin composition waist
        +
external formal/assurance/provenance owners
        +
task-local adapters/projections
```

The long-term criterion is simple:

> every reusable semantic operation should have an external owner or repeated evidence that
> a thin Ordivon residual is irreducible.
