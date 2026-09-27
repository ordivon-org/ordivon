# Capability Science R1

Status: **R1 EXPERIMENTAL STUDY / NON-AUTHORITATIVE**

Capability Science studies how heterogeneous black-box digital systems can be actively observed, assigned empirical semantic affordances, composed, and compared by executable observational witnesses.

This directory is a research owner. It is **not** a Runtime, capability registry, permission service, planner, workflow engine, semantic-completion authority, or deployed security control plane.

## Research question

Can an autonomous system:

1. infer stable semantic capabilities from black-box interaction;
2. grow its semantic vocabulary when existing predicates are insufficient;
3. explore typed capability compositions without a predefined task objective;
4. admit a new capability only when an executable observation context distinguishes it from existing equivalence classes; and
5. identify bounded, evidence-backed computational-model lifts while returning `UNKNOWN` outside the supported proof/model boundary?

## R0-R8

| LEGO | Responsibility |
| --- | --- |
| R0 Observation Semantics | Define what an observer may see and what remains hidden. |
| R1 Active Capability Identification | Bind black-box experiments to behavior/effect evidence. |
| R2 Vocabulary Invention | Admit new semantic predicates only when existing language fails to explain stable distinctions. |
| R3 Typed Composition | Reuse existing Ordivon Cognitive Circuit/interface contracts for legal composition; do not create a second workflow/composition engine. |
| R4 Closure Exploration | Use external QD/empowerment/search providers as candidate generators, never as semantic authority. |
| R5 Semantic Novelty | Require observational distinguishability witnesses against the admitted library. |
| R6 Causal Validation | Separate repeatable causal intervention evidence from correlation or one-off traces. |
| R7 Computational Lift | Use stratified model classes and three-valued standing: certified lift, certified no-lift within class, or unknown. |
| R8 Evidence & Reproduction | Preserve exact observations, witness contexts, assumptions, digests, and non-claims. |

Security is cross-cutting: effect, authority, information flow, sandboxing, and provenance remain distinct dimensions and remain owned by their natural owners.

## Mature external LEGO policy

R1 intentionally does not reimplement mature engines. Expected adapters include:

- active automata learning: LearnLib / AALpy / RALib;
- causal discovery and inference: PyWhy / causal-learn / Tetrad;
- quality-diversity/open-ended candidate search: QDax / pyribs;
- process semantics and behavioral equivalence: mCRL2;
- probabilistic model checking: PRISM / Storm;
- synthesis: cvc5 SyGuS;
- distributed/system invariants: TLA+ / TLC / Apalache;
- compositional syntax: Catlab / wiring-diagram formalisms;
- provenance/lineage: existing Ordivon W3C PROV / OpenLineage / Runtime evidence substrate.

R1 only implements the thin residual needed to connect evidence and distinguishability contracts inside Ordivon.

## Local artifacts

- `schemas/observation-trace-v1.schema.json`
- `schemas/semantic-capability-v1.schema.json`
- `schemas/novelty-witness-v1.schema.json`
- `schemas/computational-lift-certificate-v1.schema.json`
- `scripts/semantic_novelty_oracle_r1.py`
- `scripts/check_capability_science_r1.py`
- `fixtures/` bounded synthetic observations and model-lift examples
- `integration/COMPOSITION_HANDOFF_R1.md`
- `planning/lego-plan-r1.json`
- `evidence/` generated acceptance evidence

## Truth hierarchy

R1 keeps these standings distinct:

```text
OBSERVED_AFFORDANCE
    -> INFERRED_SEMANTIC_CAPABILITY
    -> CERTIFIED_NOVEL_CAPABILITY
    -> CERTIFIED_COMPUTATIONAL_LIFT (optional, stronger claim)
```

A stronger standing never follows from naming, embedding distance, model confidence, or tool metadata alone.

## Non-authority laws

1. Capability discovery is not authority grant.
2. A semantic capability does not imply execution permission.
3. Effect, authority, and information flow are separate fields.
4. A novelty witness is relative to an explicit observation policy and compared library.
5. Bounded tests do not prove unbounded computational power.
6. `UNKNOWN` is a valid and required result when the chosen model/checker cannot certify a claim.
7. Composition remains with existing `packages/composition` contracts; Capability Science may propose a candidate circuit but cannot silently create workflow or domain truth.
8. Scientific/domain acceptance remains external to this study.

## R1 acceptance

R1 is accepted only when:

- JSON contracts parse and preserve the non-authority boundary;
- `INFERRED_SEMANTIC_CAPABILITY` and stronger standings bind repeatability plus causal/interventional evidence;
- a bounded positive fixture produces a distinguishing witness against every admitted baseline;
- a candidate not distinguished from an admitted baseline within the explicit bounded policy is not admitted as novel;
- witness output binds the exact observation policy, context, candidate/baseline observations, and digests;
- computational-lift certificates represent `CERTIFIED_LIFT`, `CERTIFIED_NO_LIFT_WITHIN_MODEL_CLASS`, and `UNKNOWN` without collapsing them;
- native tests pass without adding a new dependency;
- the handoff to Cognitive Circuit explicitly does not grant authority or execution rights.

## R1 external-provider pilot standing

R1 now has bounded owner-native pilots without adding permanent dependencies:

| LEGO | Provider | Bounded result | Authority boundary |
| --- | --- | --- | --- |
| R1 Active Identification | AALpy 1.6.2 | L* learned a hidden 4-state Mealy model; 255 traces replayed through depth 7 with no mismatch | provider inference is evidence, not semantic admission |
| R2 Vocabulary Invention | cvc5 1.4.1 SyGuS | synthesized a bounded predicate candidate | candidate only; promotion still requires grounding/repeatability/causal evidence |
| R4 Closure Exploration | pyribs 0.12.0 | 800 candidates filled 64/64 synthetic behavior cells | behavior coverage is not semantic novelty |
| R6 Causal Validation | DoWhy 0.14 | randomized synthetic ATE 2.0 estimated as 1.9899 | causal estimate is not novelty, permission, or authority |

All four providers were invoked through isolated `uv --with` environments. No provider was added to the repository dependency graph. Exact Runtime Job/Artifact bindings are in `evidence/external-provider-pilots-r1.json`.

The study reuses `meta/next/docs/VERIFIED_REINTEGRATION_EXTERNAL_METHODS_R4.md`, `meta/next/docs/EXPERIMENTAL_EPISODE_R1.md`, and existing `packages/composition` contracts instead of creating a provider registry, experiment scheduler, or second Composition waist.
