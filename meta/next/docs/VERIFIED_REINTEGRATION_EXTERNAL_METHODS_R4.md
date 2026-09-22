# Verified Reintegration External Methods R4

Date: 2026-09-22
Status: **SELECTIVE EXTERNAL-OWNER ADOPTION / CORE REMAINS THIN**

## Decision

Verified Reintegration R1/R2/R3.1 is not promoted into a private Ordivon formal-methods
universe. Its residual mechanics remain a thin task-local waist. Mature external owners are
selected by problem class:

```text
R1/R2 thin composition waist
        |
        +-- formalizable assume/guarantee algebra -> Pacti
        +-- temporal refinement / LTL             -> OCRA reference
        +-- assurance interchange                 -> SACM
        +-- human assurance projection            -> GSN
        +-- semantic provenance                   -> W3C PROV
        +-- operational lineage                   -> OpenLineage
        +-- software attestations                 -> in-toto / SLSA
```

No external tool becomes a universal owner merely because it is mature.

## Local standing before R4

`packages/composition` contains R1 Cognitive Circuit and R2 Interface Contract only. It is
pinned to CPython 3.14.7 and depends only on jsonschema. R1 gate assumptions and guarantees
remain bounded text rather than a hidden proprietary formal language.

The repository already has substantial real adoption of W3C PROV, OpenLineage, in-toto and
SLSA in their natural domains. R4 therefore keeps those owners rather than duplicating them
inside Composition.

## Pacti 0.3.1 — ADOPT_OPTIONAL_PROVIDER

Pacti is a Python package for assume-guarantee contract algebra. Its current 0.3.1 release
provides polyhedral and SMT contract forms and operations including composition, quotient,
merge and refinement.

Ordivon ran an isolated, non-lockfile pilot under the exact Next interpreter:

```text
CPython = 3.14.7
Pacti   = 0.3.1

compose                         PASS
quotient                        PASS
quotient + existing refines top TRUE
stronger refines weaker         TRUE
weaker refines stronger         FALSE
```

The quotient pilot derived:

```text
inputs      = [o]
outputs     = [o_p]
assumptions = [|o| <= 2]
guarantees  = [-o + o_p = 1]
```

This is direct evidence that Pacti can cover a class of LEGO problems that Ordivon should not
reimplement: system contract composition, missing-component contract synthesis and
substitutability/refinement checks.

### Boundary

Pacti is **not** added to `packages/composition` dependencies in R4.

Use it only when a real seam has an explicit formal contract representable by Pacti.
Natural-language R1 gates stay opaque to Pacti. Dependency admission requires a recurring
real consumer, not a toy example.

## OCRA 1.1.2 — ADAPT_REFERENCE_DEFER_BINARY

OCRA is an FBK tool for logic-based contract refinement and compositional verification,
including temporal contracts. FBK's current material continues to use OCRA in 2026 work on
asynchronous LTL composition.

This makes OCRA a stronger reference than inventing an Ordivon temporal-contract calculus.

### Boundary

R4 does not install/admit the OCRA binary. The current need is not yet a temporal seam.
When one appears, first translate that seam into OCRA-style proof obligations and verify
packaging/licensing/toolchain constraints independently.

## SACM 2.3 — ADOPT_ASSURANCE_INTERCHANGE_TARGET

OMG SACM is the external metamodel owner for structured assurance cases.

R1/R3 claims, evidence, assumptions and verifier-bounded arguments can later be projected
into SACM when interchange or an assurance consumer requires it.

### Boundary

SACM is a projection/interchange target. It does not become R1 gate truth, does not own
domain acceptance, and does not require a new Ordivon assurance database.

## GSN v3 — ADOPT_HUMAN_ARGUMENT_PROJECTION

GSN is the current SCSC community standard for human-readable assurance arguments. It
supports goals/claims, strategies, solutions/evidence, context, assumptions and
justifications; Version 3 also includes dialectical/challenge structures.

This is a natural visualization for an R1/R3 argument graph.

### Boundary

GSN depicts an assurance argument. A well-formed GSN graph is not proof that its top claim is
true. Ordivon should generate GSN only as a disposable projection from owner-native evidence.

## Existing standards retained

### W3C PROV

Use for semantic provenance of entities, activities, agents, derivations and responsibility.
Do not create a private Ordivon provenance ontology.

### OpenLineage

Use for operational Job/Run/Dataset lineage. Keep it separate from semantic claim/evidence
argumentation.

### in-toto / SLSA

Use for software artifact attestations and supply-chain provenance/verification claims.
Composition may consume verified attestations but must not synthesize provenance it does not
own.

## What R4 changes conceptually

Before:

```text
R1 Gate strings
  -> seam verifier
  -> evidence
```

Selective future path:

```text
R1 bounded obligation
        |
        +-- informal/domain semantic seam
        |      -> owner-native verifier
        |
        +-- formal algebraic seam
        |      -> Pacti contract provider
        |
        +-- temporal behavioral seam
        |      -> OCRA-style temporal refinement provider
        |
        v
R1 gate result
        |
        +-- PROV semantic provenance
        +-- SACM assurance interchange
        +-- GSN human projection
        +-- in-toto/SLSA artifact attestations where applicable
```

The R1 gate carrier remains generic. External methods own specialized semantics.

## Adoption matrix

| Candidate | Decision | Owns | Does not own |
|---|---|---|---|
| Pacti 0.3.1 | ADOPT_OPTIONAL_PROVIDER | algebraic assume-guarantee operations | all R1 gates / domain truth |
| OCRA 1.1.2 | ADAPT_REFERENCE_DEFER_BINARY | temporal refinement model | generic composition runtime |
| SACM 2.3 | ADOPT_ASSURANCE_INTERCHANGE_TARGET | assurance-case metamodel | gate truth |
| GSN v3 | ADOPT_HUMAN_ARGUMENT_PROJECTION | human argument structure | proof/domain acceptance |
| W3C PROV | KEEP_EXISTING_OWNER | semantic provenance | execution lineage |
| OpenLineage | KEEP_EXISTING_OWNER | operational lineage | semantic assurance |
| in-toto/SLSA | KEEP_EXISTING_OWNER | software attestations/provenance | arbitrary domain evidence |

## Explicit non-decisions

R4 does not:

- add Pacti or OCRA to the Composition runtime dependency graph;
- translate every natural-language gate into SMT;
- introduce a universal contract language;
- introduce a universal assurance ontology;
- replace R1 gate results with SACM/GSN;
- conflate provenance with proof;
- infer domain acceptance from formal refinement;
- build automatic Goal -> Circuit synthesis.

## Next trigger conditions

A new generic LEGO may be added only after real consumers establish one of these repeated
pressures:

1. **formal algebra pressure** — two or more real seams need composition/refinement/quotient;
2. **temporal pressure** — a real stateful protocol seam cannot be captured by static
   interface/evidence checks;
3. **assurance interchange pressure** — a consumer requires SACM/GSN export;
4. **incremental invalidation pressure** — provenance graph changes make full gate
   revalidation materially expensive.

Until then, external owners remain optional providers around the thin waist.
