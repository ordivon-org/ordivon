# Representation-first triage (Meta-Thinking R1)

Use this reference with the existing method-router. It is a **selection aid**, not a new registry, policy engine, skill collection, scheduler, or source of domain truth.

## First ask what can disappear

Given goal G and its actual consumers, ask in order:

1. Can a false or obsolete goal, redundant implementation, or unnecessary distinction be **eliminated**?
2. Can contextually equivalent cases be **quotiented** (merged) without changing required consumer-observable behavior?
3. Can invalid configurations or transitions be made **unrepresentable** or excluded by constraints?
4. Can independent parts be **decoupled**, with explicit contracts and smaller dependency closures?
5. Which remaining unknown can be **resolved** by the cheapest discriminating observation, solver, or counterexample?

Do not create a routing task for a simple known operation. If one method suffices, stop. `UNKNOWN` is never evidence for compatibility or safe deletion.

## Ten representation lenses

| Lens | Distinct failure symptom | Smallest existing method / native tool | Counterexample or acceptance check |
| --- | --- | --- | --- |
| Type-driven | Invalid state or mismatched input can be constructed | Owner language type system (Rust enum/newtype/typestate or native schema) | Compile-fail/negative schema test plus runtime edge check |
| Constraint-first | Compatibility conditions scattered across imperative branches | compositional-contracts; owner native schema/solver; CUE only if justified | Explicit assumption/guarantee mismatch rejected |
| Graph-first | Unknown consumers, hidden dependencies, risky retirement | design-structure-matrix; owner-native Git/import/trace facts; Datalog only at sufficient scale | Root reachability with dynamic/unknown edges kept visible |
| State-machine-first | Lifecycle, cancellation, retry or concurrent ordering is ambiguous | Existing owner state model and `services/runtime/formal` when relevant; TLA+ for state-space questions | Forbidden transition counterexample; safety and conditional liveness checked separately |
| Algebra-first | Each LEGO variant needs a handwritten generator | Native generics/constructors/combinators; compositional-contracts for composition laws | Property tests: identity, associativity, closure only where mathematically valid |
| Equivalence-first | Multiple implementations offer apparently same behavior | compositional-contracts and consumer-level differential/property tests | Contextual substitutability includes effects, assumptions, version, authority |
| Declarative-first | Depends on implicit installation/order/env/PATH | Owner-native lockfile, environment declaration and reproducible task | Same declared input/environment yields equivalent result; environmental unknowns listed |
| Abstraction-first | LEGO compositions explode or an abstract property has infeasible traces | existing Owner model checker; Counterexample-Guided Abstraction Refinement (CEGAR) if justified | Concretize counterexample: real violation repairs Owner, spurious trace refines the model, UNKNOWN stays unproved |
| Causal-first | Repeated fixes target correlations rather than root cause | causal-intervention; independent telemetry and controlled A/B or fault injection | A contrasting intervention separates competing failure hypotheses |
| Compression-first | Notes/models replicate stale global advice ignoring context | Existing `meta/next/knowledge` lessons with source, context, consumer and applicability window | Retrieved claim is reproducible and invalid outside declared context |

These lenses are neither a priority score nor mandatory data fields for every LEGO. Pick a native tool/Skill because its **problem semantics** match, not because it has the same keyword.

## Formal-first and LEGO-first bind every lens

- **LEGO** means a replaceable, consumer-conditioned responsibility with input, output, behavior, and acceptance, not a package, file, skill, or agent.
- **Formal** identifies checkable obligations: `Assumption -> Guarantee`, valid composition, reachable states, transition properties and concrete counterexamples.
- `ToolDiscovered != Authorized`; `SkillRead != Executed`; `JobSucceeded != ConsumerAccepted`; `IndividualLEGOValid != CompositionValid`.
- Do not create universal owners or require a universal LEGO registry. Git, Runtime, Host and actual consumer/domain owners keep their respective truth.
- A type check is not a proof of distributed execution; bounded model checking does not prove implementation equivalence; passing examples do not establish universal equivalence.

## Bind the observation before explaining the failure

A system-state observation is meaningful only relative to its actual subject:
the node, service instance, effective execution identity, namespace or
endpoint, source/configuration, observation time, and consumer wherever
these affect its semantics. This is a diagnostic selection aid, not a
mandatory field list for every LEGO.

Use the constraint **Observation.Subject == Claim.Subject** with current,
independent Owner evidence. If the binding is absent or differs, preserve
UNKNOWN rather than converting another instance's negative observation into
a remediation permission. Probe the exact consumer-bound instance before
changing a live service.

Independent counterexamples to unscoped inferences:

- Default 'tailscale status' can fail while separate userspace Tailnet
  instances are Running via independently named Unix sockets. Bind the
  intended --socket and consumer; process-name presence does not prove the
  default control-plane endpoint is healthy.
- The Windows Runtime service identity may not resolve Python/Cargo/gh on
  PATH while the supported active-user execution identity can. Bind the
  execution token and executable path before declaring tools missing.
- Cached Git origin/main may differ from GitHub's current protected tip.
  Runtime Workspace opening sourceRevision can differ from
  currentHeadRevision. Bind the exact SourceCut and admission-time source
  state before inferring which bytes were executed.

This is an **Agent reasoning guard**, not evidence that a live Owner enforces
the relation. Safety-critical operations still require native admission gates
and independent negative consumer checks. Reuse owner APIs/CLIs rather than
creating a second identity registry or global observation service.

## Property-scoped CEGAR only when there is an actual verification consumer

Start from the existing coarse model. Check the property, then classify its
abstract counterexample as real, spurious or UNKNOWN by comparing with Owner
transitions and physical effects. Repair real failures; refine only the
predicate or time distinction missing from spurious traces; preserve UNKNOWN
when the abstract-to-concrete relation cannot be justified. Passing a bounded
model does not prove the implementation. Do not request a global minimality
or sufficiency proof, or create a new solver, registry or workflow.

## Minimal evidence for an actual reform

`(goal, observed problem, source cut, natural owner/consumer, hypotheses+unknowns, chosen representation, proposed subtraction, expected invariant, native check, independent counterexample, outcome)`.

No record needed when an existing deterministic tool directly resolves the issue. Prefer deleting an obsolete mechanism over preserving it as a compatibility layer, **after** proving the consumer-visible requirement is met. Stop once the decision is evidence-backed; delete this reference if it does not improve real reform decisions.

Read `meta/next/docs/META_THINKING_REPRESENTATION_R1.md` for authority boundaries and targeted pilots. For mature method disambiguation use `method-map.md`.
