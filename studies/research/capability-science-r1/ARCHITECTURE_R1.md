# Capability Science Architecture R1

Date: 2026-09-27
Status: **EXPERIMENTAL / BOUNDED SEMANTIC SUBSTRATE**

## 1. Separation of concerns

Capability Science treats a digital component as an open interactive system rather than a label attached to a tool.

```text
provider/tool/service
      |
      v
active intervention + observation
      |
      v
behavior/effect evidence
      |
      v
semantic capability hypothesis
      |
      v
observational equivalence class
```

The capability hypothesis is empirical and observation-policy-relative. The external provider remains the physical owner of its behavior and authority.

## 2. Core semantic object

Conceptually a capability is:

```text
C = <I, O, Pre, Act, T, Eff, Req, Auth, Flow, Persist, Obs, Evidence>
```

where:

- `I/O`: typed interfaces;
- `Pre`: preconditions;
- `Act`: controllable interventions;
- `T`: learned/declared transition model;
- `Eff`: world-state effects;
- `Req`: environmental/resource requirements;
- `Auth`: required/delegated/attenuated/created authority claims;
- `Flow`: information sources/transforms/sinks;
- `Persist`: lifetime/state persistence semantics;
- `Obs`: observer projection;
- `Evidence`: exact observations/interventions/witnesses.

R1 serializes a conservative subset of this object. It does not claim to supply a universal effect system or IAM model.

## 3. Observation-relative semantics

Given observation policy `O` and legal contexts `K_O`, two candidate capabilities are equivalent when:

```text
forall K in K_O: Obs(K[C1]) == Obs(K[C2])
```

A bounded R1 novelty claim requires a distinguishing context:

```text
exists K*: Obs(K*[candidate]) != Obs(K*[baseline])
```

The emitted `NoveltyWitness` stores that concrete `K*`, both observations, and their canonical digests.

A candidate is admitted as novel against a finite library only if a witness exists against every compared baseline equivalence-class representative. Failure to distinguish even one representative prevents a novelty claim.

This is intentionally stronger than embedding or lexical distance and intentionally weaker than universal contextual equivalence.

## 4. Equivalence spectrum

Future adapters may support different relations depending on the model and research question:

- trace equivalence;
- may/must testing equivalence;
- simulation preorder;
- bisimulation;
- contextual equivalence.

R1 implements only exact comparison of canonical observations over an explicit bounded context universe. The relation is therefore named `bounded-observational-distinguishability-r1`; it must not be described as universal contextual equivalence.

## 5. Candidate generation versus semantic authority

Search systems such as QD, empowerment, novelty search, program synthesis, or LLM hypothesis generation may propose circuits or experiments. Their outputs are candidates only.

```text
candidate generator
      !=
semantic novelty authority
```

A candidate becomes a `CERTIFIED_NOVEL_CAPABILITY` only through evidence-backed distinguishability under an explicit policy.

## 6. Vocabulary growth

R1 defines the admission pressure for future predicate invention but does not implement a custom predicate-invention learner.

A vocabulary extension is justified only when:

1. repeatable observations remain unexplained or collapsed by the current vocabulary;
2. an external/mature learner or bounded synthesis step proposes a new predicate;
3. the predicate improves explanatory/distinguishing power on held-out or counterexample contexts;
4. the resulting capability still carries evidence and non-claims.

## 7. Composition boundary

`packages/composition` already owns task-local Cognitive Circuit manifests, typed ports, interface contracts, authority obligations, and verification obligations.

Capability Science must not duplicate those facilities.

Its allowed handoff is:

```text
validated semantic capability candidate
        + exact evidence
        + owner/truth-boundary proposal
        + unresolved assumptions
        v
caller/Agent/domain resolves whether to bind it
        v
existing Cognitive Circuit manifest
```

No automatic binding, authority grant, scheduler state, or workflow state is created by this study.

## 8. Computational-lift ladder

R1 uses a stratified vocabulary rather than a single `turing_complete` boolean:

```text
L0 STATELESS_RELATION
L1 FINITE_STATE_TRANSDUCER
L2 REGISTER_DATA_AUTOMATON
L3 VISIBLY_PUSHDOWN_PROCEDURAL
L4 PETRI_VAS_COUNTERLIKE
L5 FIFO_MULTISTACK_MINSKY_LIKE
L6 GENERAL_INTERACTIVE_COMPUTATION
```

A certificate records both lower and higher model classes and one of:

- `CERTIFIED_LIFT`;
- `CERTIFIED_NO_LIFT_WITHIN_MODEL_CLASS`;
- `UNKNOWN`.

A bounded trace suite alone cannot certify an unbounded lift. Strong claims require an appropriate constructive mapping, simulation/refinement relation, model-check result, or other owner-native proof artifact.

## 9. Evidence hierarchy

```text
raw observation
  < repeated observation
  < intervention-supported effect
  < inferred semantic capability
  < distinguishing witness
  < model-lift certificate
```

This ordering is about claim strength, not business/scientific acceptance.

## 10. R1 safety boundary

Synthetic fixtures are deliberately non-networked and non-targeted. They model benign capability composition and distinguishability. Future security experiments must use explicitly authorized/sandboxed environments and preserve the existing Ordivon Security authority boundary.

## 11. External-owner execution rule

Capability Science does not own mature learners, optimizers, causal engines, or formal solvers. A provider may propose a behavior model, predicate, candidate circuit, causal estimate, or proof artifact. The study binds the exact provider result to Runtime evidence and then applies its own bounded admission contract.

```text
external owner/provider
        -> owner-native result
        -> exact Runtime evidence binding
        -> Capability Science bounded admission rule
        -> semantic standing (or UNKNOWN)
```

Provider success never implies semantic admission. Provider failure never silently weakens the target claim. No provider is made a permanent dependency until repeated real workloads establish that pressure.

For `CERTIFIED_NO_LIFT_WITHIN_MODEL_CLASS`, ordinary absence of a stronger witness is insufficient: R1 requires explicit model-check basis, checked bounds, and completeness evidence for the claimed bounded model class. For `UNKNOWN`, positive/negative witness and completeness evidence must remain absent.
