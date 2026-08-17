# Ordivon Media Foundations — MF4-C Relations, Binding, Dependency & Constraint

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 14 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4-A Composition Ontology and MF4-B Parts/Units/Boundaries complete and provisional.  
**Status:** MF4-C complete and PROVISIONAL. Composition Foundations remain UNFROZEN.  
**Next:** MF4-D — Hierarchy, Recursion, Modularity & Scale.

---

# 1. Problem statement

MF4-A established that composition requires more than plurality:

`Composition = Plurality + Typed Constitutive Relations/Constraints + Whole-level Organization + Scope`.

MF4-B then showed that even the parts themselves are not pre-given atoms:

`Boundary hypotheses ↔ Unit identities ↔ Whole/composition hypotheses`.

MF4-C now attacks the remaining black box:

> **What exactly are the relations and constraints that make candidate units belong together as one composition, and how do binding, dependency, causation, synchronization, interface contracts and global consistency differ?**

The naive picture is:

`parts --edges--> whole`.

This is too weak because:

- not all relations are pairwise;
- not all dependencies are causal;
- not all correlations are dependencies relevant to composition;
- not all constraints are active interactions;
- binding requires role/ownership assignment, not mere association;
- local consistency need not imply one globally coherent whole;
- relations can be standing, dynamic, probabilistic, directional, asymmetric, higher-order or negative;
- the same components can participate simultaneously in several relation systems.

The core target is therefore the collapse:

`Relation = Correlation = Dependency = Causation = Binding = Constraint = Coupling`.

MF4-C rejects that collapse.

---

# 2. Relation is the broadest category

A relation is any typed connection/predicate/constraint among one or more relata under a scope.

Examples:

- `left-of(A,B)`;
- `before(A,B)`;
- `same-source(A,B)`;
- `binds(role, filler)`;
- `depends-on(moduleA,moduleB)`;
- `causes(A,B)`;
- `must-differ(x,y)`;
- `phase-locked(A,B)`;
- `allowed-call(A,B)`.

### Result

**CC-01 — Relation is an umbrella ontology. Correlation, binding, dependency, causation, constraint and coupling are typed relation profiles, not synonyms.**

---

# 3. Relation identity requires type

Saying only:

`R(A,B)`

is insufficient.

Different relation types can connect the same units simultaneously:

- A is spatially left of B;
- A temporally precedes B;
- A calls B;
- A and B share a data dependency;
- A and B are statistically correlated.

### Result

**CC-02 — Relation identity is type-indexed; the same relata can participate in multiple non-equivalent relations at once.**

---

# 4. Relata identity and relation role are distinct

For a directional relation:

`R(A,B)`

A and B can occupy distinct argument roles.

Swapping them can change the relation:

`before(A,B) ≠ before(B,A)`.

### Result

**CC-03 — Relation arguments have typed roles/positions; constituent presence alone does not specify relational structure.**

This generalizes MF3-E role–filler binding beyond symbols.

---

# 5. Symmetry is relation-specific

Some relations are symmetric:

`adjacent(A,B) = adjacent(B,A)`.

Others are asymmetric:

`contains(A,B) ≠ contains(B,A)`.

Others have explicit converses:

`before(A,B) ↔ after(B,A)`.

### Result

**CC-04 — Symmetry, asymmetry and converse structure are typed properties of relations, not assumptions about all composition edges.**

---

# 6. Reflexivity/transitivity are also typed

Examples:

- equality is reflexive/transitive;
- adjacency is usually not transitive;
- temporal precedence is transitive under suitable definitions;
- causal influence can be indirect/transitive at one abstraction but not identical to direct causation.

### Result

**CC-05 — Reflexivity/transitivity must be declared per relation; path closure must not be inferred from graph connectivity alone.**

---

# 7. Pairwise relations are not universal

A relation may involve more than two participants:

- `between(A,B,C)`;
- `gives(agent, object, recipient)`;
- three-note chord relation;
- parity constraint over many bits;
- database tuple with several role fields;
- synchronization among an ensemble.

### Result

**CC-06 — Composition relations can be n-ary. Universal reduction to ordinary pairwise edges risks losing role and joint-constraint structure.**

---

# 8. Reification can encode n-ary relations, but changes ontology level

An n-ary relation can often be transformed into a node/event object connected pairwise to participants.

Example:

`GIVE(Alice,Book,Bob)`

becomes event node `e` with:

- agent(e,Alice)
- theme(e,Book)
- recipient(e,Bob)

This can be useful computationally.

But the added relation-token/event node is itself a new unit at another level.

### Result

**CC-07 — N-ary relations can be reified into relation/event units, but reification is a representational transformation, not proof that the underlying ontology was intrinsically pairwise.**

---

# 9. Factor graphs provide a hard formal falsifier of pairwise-only thinking

Kschischang, Frey & Loeliger formalize a global function as a product of local functions, each local factor depending on a subset of variables.

A factor node can therefore constrain several variables jointly.

### Result

**CC-08 — Global composition can factor through multi-variable local constraints; a variable–factor incidence structure is often more faithful than a simple object–object edge graph.**

---

# 10. Mathematical graph representation ≠ relation ontology

Graph, hypergraph, factor graph, tensor, relation table and category-like diagram are alternative representational formalisms.

Each foregrounds different structure.

### Result

**CC-09 — A useful mathematical representation of relations should not be mistaken for the ontology of relation itself.**

---

# 11. Correlation is a statistical relation

Statistical correlation/dependence says observed/random variables co-vary under a distribution.

It does not by itself state:

- which causes which;
- whether either constrains the other mechanistically;
- whether the relation is composition-defining;
- whether a common cause explains both;
- whether intervention transfers.

### Result

**CC-10 — Statistical correlation/dependence is not sufficient for causal, functional or composition-defining dependency.**

---

# 12. Independence is model/distribution-relative

Two variables can be marginally independent but conditionally dependent, or vice versa.

### Result

**CC-11 — Statistical dependence requires a declared distribution/conditioning context; `depends on` should not be used without typing.**

---

# 13. Causal dependence requires stronger semantics

Pearl's causal-diagram framework explicitly combines statistical information with causal assumptions to identify intervention effects.

An observational association alone does not determine what would happen under intervention.

### Result

**CC-12 — Causal relation is an intervention/counterfactual-capable dependency profile, not reducible to observational correlation.**

---

# 14. Causation is not universally composition-defining

A cause can affect something without the two being parts of one relevant composition.

Example:

- lightning causes a distant power outage;
- one event causes another years later.

### Result

**CC-13 — Causal influence alone does not imply common-whole membership. Composition still requires a scope-specific whole criterion.**

---

# 15. Composition can exist without active causation

A printed sentence has standing syntactic/semantic relations without its words actively causing one another.

A saved graph has edges while no traversal occurs.

### Result

**CC-14 — Active causal interaction is not necessary for standing relational composition.**

---

# 16. Dependency is broader than causation

A component may depend on another through:

- logical precondition;
- build/import dependency;
- data availability;
- resource requirement;
- temporal ordering;
- reference;
- shared invariant;
- causal influence.

### Result

**CC-15 — `Dependency` is a family of typed necessity/availability/constraint relations; causal dependency is only one subtype.**

---

# 17. Dependency direction must be explicit

If A imports B:

`A depends on B`.

That does not imply:

`B depends on A`.

### Result

**CC-16 — Dependency direction is part of the relation, not metadata that can be omitted.**

---

# 18. Shared cause/resource does not imply mutual dependency

Two services may both require database D.

Then:

`A <- D -> B`

can create observed/common failure correlation without A depending on B.

### Result

**CC-17 — Shared dependency/common cause must be distinguished from direct dependency between components.**

---

# 19. Enabling condition ≠ Causal driver

Oxygen enables combustion but does not by itself select when a match is struck.

A library API enables a call but may not initiate it.

### Result

**CC-18 — Enabling/precondition relations and triggering/causal-driving relations are distinct.**

---

# 20. Resource dependency ≠ Information dependency

A process can depend on another for:

- CPU/memory/power;
- data;
- authority;
- timing;
- physical support.

### Result

**CC-19 — Dependency should be typed by what is required/transferred: resource, information, control, authority, state, timing or structure.**

---

# 21. Binding is assignment, not generic association

Binding answers a stronger question:

> Which feature/filler/value belongs in which role/unit relation?

Examples:

- red belongs to object A, not B;
- John fills agent role, Mary fills patient role;
- value 42 fills variable x;
- audio source belongs to visual event E.

### Result

**CC-20 — Binding is an assignment relation between units/features/fillers and roles/owners/slots; it is stronger than co-occurrence or similarity.**

---

# 22. Misbinding proves parts + features are insufficient

Treisman & Schmidt's illusory conjunctions show that constituent features can all be present yet recombined incorrectly.

### Result

**CC-21 — Binding correctness is an independent composition dimension; correct constituents do not guarantee correct role/ownership assignment.**

---

# 23. Symbolic role–filler binding generalizes cleanly

Smolensky's tensor-product method explicitly represents variable/value or role/filler bindings and permits fully distributed realization.

MF4-C abstracts this beyond symbolic systems:

`Bind(role, filler | context)`.

### Result

**CC-22 — Binding is role-structured and can be realized locally, distributedly, spatially, temporally or through interfaces; no one substrate is constitutive.**

---

# 24. Binding is not necessarily permanent

Temporary bindings occur in:

- working memory;
- object tracking;
- variable assignment;
- user-interface focus;
- transaction/session state.

### Result

**CC-23 — Binding has a persistence/lifetime profile independent of filler and role identity.**

---

# 25. One filler can occupy multiple roles

Example:

`SELF-LOVES(A,A)`

or one service simultaneously acts as producer and consumer in different channels.

### Result

**CC-24 — Binding does not require one-to-one role–filler matching. Cardinality constraints are composition-specific.**

---

# 26. One role can admit multiple fillers

Examples:

- chorus members;
- replicas;
- recipients list;
- multi-valued field.

### Result

**CC-25 — Role cardinality is typed; one-to-many and many-to-many bindings are admissible.**

---

# 27. Binding and identity tracking interact

If a moving object's track identity switches, feature bindings can remain locally plausible but attach to the wrong persistent token.

### Result

**CC-26 — Binding correctness can depend on token identity continuity, linking MF4-C to MF4-B tracking.**

---

# 28. Relation uncertainty and unit uncertainty are distinct

A system can know A and B exist while being uncertain whether:

`R(A,B)`.

Or be certain some relation holds but uncertain which token occupies one role.

### Result

**CC-27 — Uncertainty over relata identity, relation type, relation existence and role assignment are separate dimensions.**

---

# 29. Constraint is a restriction on admissible joint states

Let variables/parts have joint state space:

`S = S_1 × ... × S_n`.

A constraint specifies an admissible subset:

`Ω ⊆ S`.

### Result

**CC-28 — Constraint is naturally understood as restricting admissible joint configurations under a scope.**

---

# 30. Constraints may be positive or negative

Positive:

- values must agree;
- parts must connect;
- timing must align.

Negative:

- two resources cannot overlap;
- fields cannot both be true;
- collision prohibited;
- role cannot bind to that filler.

### Result

**CC-29 — Exclusion/forbidden-state relations are first-class composition constraints, not absence of relation.**

---

# 31. Constraint ≠ Active force

A grammar rule constrains well-formed sentences but is not a physical force between words.

An API contract constrains valid messages while idle.

### Result

**CC-30 — Constraint can have standing/normative/logical status without active causal coupling.**

---

# 32. Active coupling can realize a constraint dynamically

Examples:

- mechanical linkage;
- feedback controller;
- phase-locking oscillator;
- active synchronization protocol.

### Result

**CC-31 — A constraint may be statically specified or dynamically enforced/maintained; specification and realization are distinct.**

---

# 33. Hard vs soft constraint

Hard constraint:

`x ∈ Ω` required.

Soft constraint:

configurations receive costs/energies/probabilities/preferences.

### Result

**CC-32 — Constraint strength can be hard, soft, probabilistic, energetic or normative; `constraint` does not imply binary validity only.**

---

# 34. Local constraint ≠ Global solution

Mackworth's constraint-network framework explicitly distinguishes node/arc/path consistency checks from constructing a complete solution.

Local consistency pruning can eliminate impossible assignments but need not alone guarantee one globally satisfying assignment in general CSPs.

### Result

**CC-33 — Local relational consistency is not equivalent to global compositional coherence.**

---

# 35. Constraint propagation is an operation on relational possibilities

When a constraint rules out values for one variable, those removals can propagate to connected constraints and reduce possibilities elsewhere.

### Result

**CC-34 — Constraint propagation is a mechanism for transmitting admissibility consequences through a relational network; it is not itself the ontology of relation.**

---

# 36. Global coherence can emerge from many local constraints

A globally valid line drawing, schedule, codeword or layout may result from mutually compatible local constraints.

### Result

**CC-35 — Whole-level coherence can arise from distributed constraint compatibility without one central relation node.**

---

# 37. Local coherence can still hide global contradiction

A network can pass weaker local checks while remaining globally unsatisfiable.

### Result

**CC-36 — Composition validation needs a declared consistency level; `locally coherent` and `globally realizable` are distinct claims.**

---

# 38. Constraint redundancy is not necessarily waste

Multiple constraints may overlap in what they rule out.

Redundancy can:

- increase robustness;
- accelerate inference;
- support error detection;
- preserve organization under failure.

### Result

**CC-37 — Constraint redundancy can be a compositional resource rather than inefficiency.**

---

# 39. Constraint conflict is typed

Two constraints may be:

- logically inconsistent;
- physically incompatible;
- temporally unschedulable;
- policy-conflicting;
- resource-conflicting.

### Result

**CC-38 — Constraint conflict requires type/scope; not all violations are the same failure.**

---

# 40. Relation sets can themselves define units

If a subset of components has dense/strong internal relations and weak external relations, it can become a candidate module/unit.

### Result

**CC-39 — Relations help individuate parts as well as connect pre-existing parts; MF4-B/C remain reciprocal.**

---

# 41. Relations can become relata

Example:

- `because(A,B)` relation becomes the subject of a claim;
- an edge/contract is versioned/annotated;
- a marriage relation is legally terminated;
- a database relationship has metadata.

### Result

**CC-40 — Relations can be reified as first-class units in higher-order compositions. Relation and relatum roles are level-relative.**

---

# 42. Higher-order relations are admissible

Relations can relate other relations:

- one constraint overrides another;
- one causal path mediates another;
- two interface contracts are compatible;
- one temporal relation constrains another.

### Result

**CC-41 — Composition ontology must admit higher-order relations and constraints over relations.**

---

# 43. Relation persistence can outlive component tokens

A role/interface pattern can remain while one component implementation is replaced.

### Result

**CC-42 — Relation/type continuity and endpoint-token continuity are distinct.**

---

# 44. Component replacement can preserve relation structure

Replica B replaces replica A but the service dependency remains:

`client -> service-role`.

### Result

**CC-43 — Whole/composition identity may preserve role-level relations across token substitution.**

---

# 45. Relation can change while parts remain fixed

Same people:

- strangers → teammates → opponents.

Same software modules:

- call direction changes after refactor.

### Result

**CC-44 — Part identity does not determine relation identity.**

---

# 46. Static adjacency ≠ Dynamic coupling

Two modules may be spatially adjacent on a board yet not interact.

Two distant oscillators may be strongly coupled.

### Result

**CC-45 — Spatial proximity/adjacency and causal/dynamic coupling are distinct relation types.**

---

# 47. Coupling is reciprocal influence profile

Dynamic coupling concerns how states/processes constrain or influence each other's evolution.

It may be:

- unidirectional;
- bidirectional;
- delayed;
- nonlinear;
- state-dependent.

### Result

**CC-46 — Coupling is a dynamical relation profile, not synonymous with generic dependency or composition.**

---

# 48. Strong coupling does not automatically define one unit

Two adversaries can interact strongly while remaining distinct actors.

### Result

**CC-47 — Coupling magnitude alone does not determine unit fusion/common-whole identity. Boundary/autonomy/scope remain relevant.**

---

# 49. Weak coupling can still be composition-defining

A sparse coordination message may be enough to keep distributed modules in one protocol/system.

### Result

**CC-48 — Composition relevance is not monotonic in raw coupling strength.**

---

# 50. Synchronization is a temporal relation

Synchrony constrains relative timing/phase among dynamic units.

### Result

**CC-49 — Synchronization/phase relation is one dynamic composition mechanism/profile, not a universal binding primitive.**

---

# 51. Gray et al. make synchrony a real binding candidate

Gray, König, Engel & Singer observed synchronization among spatially separate visual-cortical columns, modulated by global stimulus properties, motivating temporal-correlation/binding hypotheses.

### Result

**CC-50 — Neural synchrony can carry/realize relational organization across distributed feature-selective populations in some conditions.**

---

# 52. Thiele & Stoner falsify synchrony as universal binding ontology

In MT plaid-motion experiments, perceptual coherence did not covary in the predicted way with neuronal synchrony; coherent plaids could produce less synchrony than non-coherent ones.

### Result

**CC-51 — Synchrony is neither necessary nor sufficient for all perceptual binding; mechanism evidence must remain domain/circuit specific.**

---

# 53. Synchrony itself requires tolerance/window definition

Exact simultaneity is rarely the operative notion.

Systems use:

- temporal windows;
- phase tolerances;
- clock offsets;
- jitter bounds.

### Result

**CC-52 — Synchronization is parameterized by tolerance/reference frame; `simultaneous` is not a context-free binary relation.**

---

# 54. Temporal relations are richer than before/after

Allen's interval-based temporal logic models interval relations and uses constraint propagation over them rather than reducing all temporal organization to point timestamps.

### Result

**CC-53 — Temporal composition should support interval relation types such as precedence, meeting, overlap, containment/start/finish/equality profiles rather than one scalar timestamp ordering.**

---

# 55. Temporal relation uncertainty can be disjunctive

A system may know only that event A is either before or overlaps B, not which exactly.

### Result

**CC-54 — Relation states may be sets/distributions of possible relation types rather than one known edge label.**

---

# 56. Temporal relation composition is relational inference

If A precedes B and B precedes C, some relation about A and C can be inferred; other relation combinations yield disjunctive possibilities.

### Result

**CC-55 — Relations can compose to constrain other relations, but relation composition is type-specific and may produce uncertainty sets rather than one relation.**

---

# 57. Relation composition ≠ Whole composition

Composing relation predicates along paths is a reasoning operation.

It is not identical to composing the underlying media/parts into a whole.

### Result

**CC-56 — Algebraic relation composition and ontological whole composition are distinct uses of `composition`.**

---

# 58. Spatial relations also require reference frames

`left-of(A,B)` can mean:

- viewer-centered;
- object-centered;
- map/world-centered.

### Result

**CC-57 — Relation content can be reference-frame dependent; the frame is part of the relation profile.**

---

# 59. Relation can be metric or qualitative

Spatial/temporal relations may use:

- exact distances/timestamps;
- topological adjacency;
- qualitative before/overlap/inside.

### Result

**CC-58 — Relation precision/format is typed; qualitative and metric relations can describe the same relata at different granularities.**

---

# 60. Interface contracts are standing constraints over cross-boundary relations

An interface can specify:

- allowed calls;
- schemas;
- timing;
- ownership;
- errors;
- authority.

### Result

**CC-59 — Interface composition is defined less by physical proximity than by typed allowed/required cross-boundary relations.**

---

# 61. Interface compatibility ≠ Implementation similarity

Two implementations can differ radically but satisfy the same contract.

### Result

**CC-60 — Relation/contract identity can be preserved under component implementation substitution.**

---

# 62. Contract ≠ Traffic

An API relation can exist while no request is occurring.

### Result

**CC-61 — Standing relation specification and active relation realization/interaction are distinct.**

---

# 63. Active interaction can violate standing relation specification

A malformed/unauthorized call crosses the boundary but violates contract.

### Result

**CC-62 — Actual coupling/traffic and valid compositional relation are distinct; activity does not imply constraint satisfaction.**

---

# 64. Constraint satisfaction does not imply use

Two components can be mutually compatible but never interact.

### Result

**CC-63 — Compatibility is weaker than active dependency/use.**

---

# 65. Relation affordance ≠ Relation realization

A socket allows a plug connection; no plug may be inserted.

### Result

**CC-64 — Potential/afforded relations and instantiated relations are distinct standing states.**

---

# 66. Ownership relation is composition-defining in many domains

Examples:

- feature belongs to object;
- edge belongs to figure side;
- data field belongs to record;
- event step belongs to plan.

### Result

**CC-65 — Ownership/attribution relations are a major binding subtype connecting MF4-B boundaries to MF4-C organization.**

---

# 67. Containment ≠ Ownership

A file can be physically stored in a directory without semantically belonging to a project.

An object can lie inside another object's bounding box without being its part.

### Result

**CC-66 — Spatial/container inclusion and compositional ownership/parthood are distinct.**

---

# 68. Co-location ≠ Same-source

Audio/video features can occur at the same location/time but come from different causes/sources.

### Result

**CC-67 — Co-location/coincidence is a cue to relation, not relation identity itself.**

---

# 69. Common fate is a dynamic grouping cue, not universal dependency

Elements moving together can be grouped perceptually.

But coordinated movement may be imposed externally rather than indicate one causal unit.

### Result

**CC-68 — Shared dynamics can support composition inference but do not uniquely determine underlying relation type.**

---

# 70. Relation provenance matters

A relation can be:

- physically realized;
- inferred;
- designed;
- conventional;
- statistically estimated;
- institutionally assigned.

### Result

**CC-69 — Relation provenance/evidence source is distinct from relation type/content.**

---

# 71. Relation evidence ≠ Relation ontology

A correlation coefficient, causal intervention, synchronization measure or interface declaration can be evidence for different relation claims.

### Result

**CC-70 — Measurement/inference method and relation ontology must remain separate.**

---

# 72. Relation confidence is first-class

A system may assign:

`P(R_type(A,B) | E)`.

### Result

**CC-71 — Relation existence/type/direction can be uncertain independently of unit/boundary uncertainty.**

---

# 73. One relation can be multi-layered

Example: A database foreign key can simultaneously be:

- a symbolic reference;
- schema constraint;
- dependency;
- navigation affordance;
- integrity relation.

### Result

**CC-72 — Relation roles can be multiplexed across representational, operational and normative layers without identity collapse.**

---

# 74. Whole-to-part constraints are admissible

A global grammar, rhythm, layout or conservation law can constrain local part states.

### Result

**CC-73 — Cross-level/top-down constraints are legitimate composition relations; causality need not be interpreted naively as a mysterious whole-object force.**

The constraint may be implemented through distributed local mechanisms while still being succinctly described at whole level.

---

# 75. Part-to-whole influence and whole-level constraint are different descriptions

A whole-level law can summarize many lower-level interactions.

### Result

**CC-74 — Cross-level description and microphysical implementation must not be conflated; whole-level constraints can be explanatorily real without requiring separate ontic forces.**

---

# 76. Global relation may be nonlocal in representation

A document's consistency can depend on references between distant sections.

A musical key constrains notes across long spans.

### Result

**CC-75 — Composition-defining relations need not be spatially/temporally local.**

---

# 77. Dependency cycles are admissible

Examples:

- feedback systems;
- mutually recursive modules;
- conversational interaction;
- recurrent networks.

### Result

**CC-76 — Directed dependency structure need not be acyclic; DAGs are specialized formalisms, not universal composition ontology.**

---

# 78. Causal DAG usefulness does not imply all causation is represented as a DAG

Pearl-style DAGs are powerful under their modeling assumptions.

Dynamic feedback may require time-indexing or richer cyclic models.

### Result

**CC-77 — Causal graph formalism is scope/model dependent; do not infer ontological acyclicity from one representation language.**

---

# 79. Relation paths can create indirect dependency

If A depends on B and B depends on C, A may have an indirect dependency on C.

But the semantics of the path depend on relation types.

### Result

**CC-78 — Path reachability is not automatically a meaningful composed relation; path semantics require typed composition rules.**

---

# 80. Mixed-relation paths are especially dangerous

Example:

A `located-in` B and B `owns` C does not imply A `located-in` C.

### Result

**CC-79 — Heterogeneous relation chains cannot be collapsed into generic connectivity.**

---

# 81. Relation normalization can destroy semantics

Turning every relation into an unlabeled undirected edge loses:

- direction;
- role;
- arity;
- modality;
- provenance;
- constraint polarity;
- time.

### Result

**CC-80 — Graph simplification is an information-losing transformation unless the discarded relation distinctions are irrelevant to scope.**

---

# 82. Constraint polarity matters

`must-connect(A,B)` and `must-not-connect(A,B)` are not represented by edge presence/absence alone if unknown/no-constraint is also possible.

### Result

**CC-81 — Positive relation, negative relation and absence/unknown relation are three distinct states.**

---

# 83. Unknown ≠ False

If no relation is observed, this may mean:

- absent;
- unknown;
- unmeasured;
- out of scope;
- deliberately hidden.

### Result

**CC-82 — Open-world uncertainty and negative constraints must not be collapsed into missing edges.**

---

# 84. Relation scope can be local in time

A dependency/binding may hold only during one phase/session.

### Result

**CC-83 — Relations have temporal validity/lifetime profiles independent of endpoint persistence.**

---

# 85. Relation versioning matters

Interface/schema relation at version v1 can differ from v2 while component names remain.

### Result

**CC-84 — Relation identity may require version/history, not only endpoint/type labels.**

---

# 86. Relation repair is distinct from part replacement

A broken dependency can be restored by changing routing/contracts without changing endpoint components.

### Result

**CC-85 — Composition repair can operate on relation structure independently of part/unit repair.**

---

# 87. Relation deletion can decompose a whole

Removing one critical constraint/link can split a system into independent components.

### Result

**CC-86 — Whole boundaries can change through relation change alone, reinforcing that parts/relations/whole identity are mutually dependent.**

---

# 88. Relation addition can merge wholes

Connecting two previously independent systems through a binding/interface/coordination relation may create a larger composition.

### Result

**CC-87 — Composition can emerge through new relations without material merger.**

---

# 89. Minimal relation profile

MF4-C proposes:

```text
RelationProfile = <
  RType : relation type,
  Args  : relata + argument roles,
  Arity : number/structure of roles,
  Dir   : direction/converse/symmetry,
  Mode  : structural/statistical/causal/functional/normative/temporal/...,
  Constr: admissibility/constraint semantics,
  Weight: strength/cost/probability/tolerance if applicable,
  Frame : reference frame/context,
  Life  : temporal validity/persistence,
  Prov  : provenance/evidence,
  Active: standing vs actively realized/enforced,
  Conf  : uncertainty/confidence,
  Scope : granularity/question/whole
>
```

### Result

**CC-88 — Relation attribution needs more than an edge label; argument roles, arity, direction, mode, constraints, frame, lifetime and evidence can be first-class.**

---

# 90. Minimal binding profile

```text
Binding = <
  Role/Owner,
  Filler/Feature/Unit,
  Context,
  Cardinality,
  Lifetime,
  Realization,
  Confidence,
  Evaluation
>
```

### Result

**CC-89 — Binding is a typed role-assignment episode/standing relation with its own cardinality, persistence and error conditions.**

---

# 91. Minimal dependency profile

```text
Dependency = <
  Dependent,
  Prerequisite/Source,
  DependencyType,
  Direction,
  Condition,
  Strength/Necessity,
  FailurePropagation,
  Lifetime,
  Scope
>
```

### Result

**CC-90 — Dependency claims should specify what is required, under which conditions, and what fails when the prerequisite is unavailable.**

---

# 92. Minimal constraint profile

```text
Constraint = <
  Scope/Variables,
  Allowed/Forbidden joint states,
  Hard/Soft semantics,
  Weight/Cost/Probability,
  Provenance,
  Enforcement mechanism,
  Consistency level,
  Lifetime
>
```

### Result

**CC-91 — Constraint ontology separates admissibility structure from enforcement and inference mechanism.**

---

# 93. Composition relation set

A composition can now be modeled provisionally as:

`W = <U, B, R, Ω, Σ>`

where:

- `U` = individuated units;
- `B` = boundary/unitization profiles;
- `R` = typed relation/binding/dependency structure;
- `Ω` = joint constraints/admissible configurations;
- `Σ` = scope/granularity/context.

This is still not a final MF4 definition because hierarchy, recursion, dynamics, multimodality and whole-level coherence remain to be attacked.

---

# 94. Relation failure taxonomy

MF4-C proposes distinct errors:

## Missing relation

Required relation absent.

## Spurious relation

Relation asserted/realized when irrelevant/false.

## Wrong relation type

Correct endpoints, incorrect relation semantics.

## Wrong direction

A→B substituted for B→A.

## Wrong role assignment / misbinding

Correct entities, wrong argument roles/ownership.

## Wrong arity/cardinality

Missing/extra participants or fillers.

## Constraint violation

Joint state outside admissible set.

## Inconsistency

Constraint set has no globally valid assignment under scope.

## Dependency omission

A real prerequisite not modeled.

## False dependency

Spurious prerequisite inserted.

## Common-cause confusion

Correlation mistaken for direct dependency.

## Causal-direction error

Association interpreted with wrong intervention direction.

## Synchronization error

Timing/phase tolerance violated.

## Interface incompatibility

Standing cross-boundary relation specifications mismatch.

## Relation staleness

Version/lifetime no longer valid.

### Result

**CC-92 — Relation/composition errors form a typed family; generic `edge error` is under-specified.**

---

# 95. Evidence profile for opaque relations

For biological/AI/social systems, relation attribution may need evidence dimensions:

- co-occurrence/correlation;
- invariance/generalization;
- temporal precedence;
- intervention;
- downstream use;
- constraint violation effects;
- role-swap tests;
- synchronization analysis;
- interface/documented contract;
- provenance/history;
- counterfactual substitution.

### Result

**CC-93 — Relation evidence should be typed to the claimed relation; no one test universally proves binding/dependency/causation.**

---

# 96. Role-swap is a strong binding falsifier

If a system truly represents/uses `R(A,B)`, swapping A/B should produce the behavior predicted by role reversal rather than merely preserving constituent presence.

### Result

**CC-94 — Role/filler swap and interchange interventions are strong tests of genuine relational binding.**

---

# 97. Dependency ablation is a strong but incomplete test

Removing prerequisite B and observing A fail supports dependency.

But failure could arise from collateral damage/shared resource effects.

### Result

**CC-95 — Ablation supports dependency only under contrastive controls separating direct prerequisite from shared infrastructure/collateral disruption.**

---

# 98. Constraint violation is diagnostic

Intentionally placing system state outside `Ω` and observing detection/failure can reveal whether a supposed constraint is operationally real.

### Result

**CC-96 — Controlled constraint-violation tests can distinguish standing formal rules from actively enforced/used constraints.**

---

# 99. Correlation can still be useful evidence

Rejecting correlation = dependency does not make correlation irrelevant.

Stable correlation can generate hypotheses and support relation inference when combined with temporal, causal, structural or design evidence.

### Result

**CC-97 — Correlation is evidence, not semantic closure.**

---

# 100. Constraint network as composition substrate

Mackworth's network consistency work shows a useful general pattern:

- variables/units;
- relations/constraints;
- local propagation;
- search/case analysis;
- global solution/coherence.

MF4-C abstracts this pattern beyond classical CSPs.

### Result

**CC-98 — Composition can be viewed as maintaining/realizing a structured network of relational constraints, but composition is broader than finite-domain CSP formalism.**

---

# 101. Factorization as compositional compression

If a global compatibility/function can be factored into local relations/functions, the composition can be represented/processed more efficiently than enumerating all global states.

### Result

**CC-99 — Factorization is a representation/computation strategy for exploiting compositional structure; it does not imply reality itself is uniquely factored that way.**

---

# 102. Factorization choice can be non-unique

The same global function/distribution may admit different factorizations or auxiliary variables.

### Result

**CC-100 — Factor graph structure can reveal/use compositional dependencies without proving one unique ontological decomposition.**

---

# 103. Relation granularity matters

`depends-on` may be too coarse.

At finer scale:

- reads state from;
- waits for;
- receives authority from;
- shares resource with.

### Result

**CC-101 — Relation type granularity should match explanatory/task scope; overly coarse relation vocabularies hide failure mechanisms.**

---

# 104. Overly fine relation ontology also has cost

If every token interaction gets a unique relation type, compositional regularity disappears.

### Result

**CC-102 — Relation abstraction trades detail against reusable structure; finer relation taxonomies are not universally better.**

---

# 105. Relation schemas/types can precede token instances

An API schema defines possible relations before any request occurs.

A grammar defines roles before a sentence token is generated.

### Result

**CC-103 — Relation types/specifications can have standing existence before relation-token instantiation.**

---

# 106. Relation tokens can violate their type

An actual attempted call can violate contract or a sentence can violate grammar.

### Result

**CC-104 — Relation type/specification and relation episode/token are distinct, mirroring MF3 standing representation and MF4 standing composition.**

---

# 107. Composition-defining relation criterion

Not every relation among units should count.

MF4-C proposes a relation is composition-defining under scope `Σ` if changing/removing/reassigning that relation would change at least one relevant whole-level property such as:

- identity;
- admissibility/coherence;
- role organization;
- operation;
- causal capability;
- represented content;
- persistence;
- evaluation;
- coordination.

### Result

**CC-105 — Composition-defining relations are those whose typed alteration changes the relevant whole profile under scope, not merely any true relation among parts.**

---

# 108. This criterion is counterfactual but not necessarily causal

Changing a grammatical relation changes sentence content even if printed symbols are causally inert.

### Result

**CC-106 — Counterfactual constitutive relevance is broader than active causal influence.**

---

# 109. Relation dependence can be constitutive

A triangle's three-sided closure is constitutive of the shape type.

A database row's foreign-key relation can be constitutive of a logical record profile.

### Result

**CC-107 — Some relations are constitutive of whole identity, not merely external interactions between independently complete units.**

---

# 110. Relation dependence can be operational only

Two components can remain the same units while a runtime dependency determines whether a service works.

### Result

**CC-108 — Constitutive and operational relations are distinct composition roles.**

---

# 111. Relation dependence can be interpretive

Montage order or caption–image relation can change whole interpretation without changing physical component identity.

### Result

**CC-109 — Interpretive/representational relations can be composition-defining even when physical mechanism is unchanged.**

---

# 112. Relation dependence can be normative

A valid transaction/document may require signatures/fields in specified relations.

### Result

**CC-110 — Normative/institutional validity constraints are genuine composition relations where the whole's status depends on them.**

---

# 113. Relation dependence can be probabilistic

A generative model may constrain co-occurrence probabilistically rather than absolutely.

### Result

**CC-111 — Probabilistic compatibility can be a composition relation without deterministic binding.**

---

# 114. Binding can be probabilistic

A perceptual system can maintain:

`P(feature f belongs to object o)`.

### Result

**CC-112 — Binding need not be all-or-none at inference time; uncertainty over ownership/role assignment is admissible.**

---

# 115. Binding ambiguity can persist

Some scenes/sentences are genuinely ambiguous under available evidence.

### Result

**CC-113 — Composition theory must admit multiple competing relation structures rather than forcing premature unique binding.**

---

# 116. Global relation structure can disambiguate local relations

Sentence grammar, scene context or protocol state can resolve a locally ambiguous binding.

### Result

**CC-114 — Relation inference can be top-down/global as well as local; MF4's reciprocal organization survives.**

---

# 117. Local relations can constrain global whole identity

A single critical role reversal can change sentence/event/protocol identity.

### Result

**CC-115 — Small local relational changes can have large whole-level consequences; component amount is not a proxy for compositional importance.**

---

# 118. Relation centrality is scope-specific

A relation can be critical for one output and irrelevant for another.

### Result

**CC-116 — Relation importance/centrality should be task/query typed rather than treated as one global scalar.**

---

# 119. Relation redundancy enables graceful degradation

Multiple paths/constraints can preserve whole function after one link fails.

### Result

**CC-117 — Redundant relational organization can increase robustness and optionality.**

---

# 120. Relation redundancy can also create conflict/cycles

Redundant rules/paths can disagree or amplify feedback.

### Result

**CC-118 — Redundancy is not inherently beneficial; its value depends on consistency, independence and failure modes.**

---

# 121. Relation topology affects propagation

Path length, cycles, bottlenecks and factorization influence how perturbations/information/constraints propagate.

### Result

**CC-119 — Relational topology is a whole-level property distinct from individual relation semantics.**

---

# 122. Topology ≠ Semantics

Two graphs with the same topology can use different edge types/roles and implement different compositions.

### Result

**CC-120 — Relation topology and relation meaning/type are separate dimensions.**

---

# 123. Provisional relation ontology

MF4-C retains the following major profiles:

## R0 — Structural/spatial/topological

Position, containment, adjacency, geometric relation.

## R1 — Temporal

Before/after/overlap/meet/during/synchrony/phase.

## R2 — Binding/ownership/role

Feature-to-unit, filler-to-role, token-to-slot assignment.

## R3 — Statistical

Association/conditional dependence under a distribution.

## R4 — Causal/dynamical

Intervention-sensitive influence/coupling.

## R5 — Functional/operational dependency

Required state/resource/data/control/interface availability.

## R6 — Constraint/normative

Allowed/forbidden/required joint configurations.

## R7 — Interface/protocol

Cross-boundary contract/message/action relations.

## R8 — Representational/interpretive

Relations whose structure contributes to MF3 content/model/symbolic organization.

## R9 — Higher-order/meta-relation

Relations/constraints over other relations.

These profiles may overlap.

---

# 124. Provisional relation non-collapse stack

```text
Relation
  ≠ Correlation
  ≠ Dependency
  ≠ Causation
  ≠ Binding
  ≠ Constraint
  ≠ Coupling
  ≠ Synchronization
  ≠ Interface Contract
```

and:

```text
Co-occurrence
  ≠ Co-location
  ≠ Same-source
  ≠ Ownership
  ≠ Common-whole Membership
```

and:

```text
Standing Relation
  ≠ Active Interaction
  ≠ Constraint Enforcement
  ≠ Relation Evidence
```

---

# 125. Provisional axioms CC-01→CC-120 — compressed core

**CC-01–09** Relations are typed, role/arity/direction structured, can be n-ary/higher-order; graph/formalism ≠ ontology.

**CC-10–19** Statistical correlation/dependence, causal influence, enabling and typed operational dependencies must remain distinct.

**CC-20–27** Binding is role/ownership assignment with cardinality/lifetime/identity dependence; misbinding and relation uncertainty are first-class.

**CC-28–38** Constraints restrict joint possibilities; hard/soft, positive/negative, standing/active enforcement and local/global consistency are distinct.

**CC-39–44** Relations individuate units, can become relata, persist across component replacement and change independently of parts.

**CC-45–52** Spatial adjacency, dynamic coupling and synchronization are distinct; synchrony is a mechanism candidate, not universal binding criterion.

**CC-53–58** Temporal interval relations and relation composition are richer than timestamps; algebraic relation composition ≠ whole composition.

**CC-59–69** Interfaces, compatibility, traffic, affordance, ownership, containment, co-location, common fate and provenance are typed relation dimensions.

**CC-70–77** Evidence, uncertainty, whole-to-part constraints, nonlocality, cycles and causal formalisms must be separated from ontology.

**CC-78–87** Path semantics, missing/negative/unknown edges, lifetime/versioning and relation-level repair/decomposition are first-class.

**CC-88–93** Relation/binding/dependency/constraint schemas and typed failure/evidence profiles are established provisionally.

**CC-94–104** Role-swap, ablation and violation tests provide evidence; factorization/CSP structure is useful but non-unique; relation types and tokens differ.

**CC-105–120** Composition-defining relations are counterfactually constitutive/operationally relevant to whole profile; constitutive, operational, interpretive, normative and probabilistic roles differ; ambiguity, redundancy and topology are first-class.

---

# 126. Claims rejected by MF4-C

Reject as universal foundational claims:

- all relations are equivalent generic edges;
- pairwise graphs can represent every composition without loss;
- graph formalism is relation ontology;
- correlation equals dependency;
- statistical dependence equals causation;
- causal influence implies common-whole membership;
- all composition requires active causation;
- dependency means only causation;
- shared cause/resource means direct mutual dependency;
- enabling condition equals trigger/cause;
- binding equals association/co-occurrence;
- correct constituents guarantee correct binding;
- binding must be localist or symbolic;
- binding is always one-to-one/permanent;
- relation uncertainty equals unit uncertainty;
- constraints are always physical forces;
- constraints are always binary/hard;
- active enforcement is required for constraint standing;
- local consistency guarantees global coherence;
- constraint propagation is relation ontology;
- relation redundancy is always waste or always good;
- relation cannot itself become a unit;
- relations are fixed if parts are fixed;
- spatial adjacency equals dynamic coupling;
- stronger coupling always means stronger common-unit composition;
- synchrony universally defines perceptual binding;
- simultaneity is context-free/exact;
- temporal relations reduce to timestamps/before-after;
- algebraic relation composition equals whole composition;
- interface compatibility equals implementation similarity;
- contract existence equals active traffic;
- active traffic implies valid contract satisfaction;
- containment equals ownership/parthood;
- co-location equals same source;
- common fate uniquely determines causal organization;
- one evidence method defines relation ontology;
- all dependency graphs are acyclic;
- path reachability automatically yields meaningful dependency;
- missing edge means false/negative relation;
- relation identity requires endpoint-token identity;
- composition repair always requires part replacement;
- factorization is unique/ontologically privileged;
- finer relation vocabulary is always better;
- one scalar edge weight captures relation importance;
- topology equals semantics.

---

# 127. Primary/original literature anchors

- Mackworth, A. K. (1977), `Consistency in Networks of Relations`, *Artificial Intelligence* 8(1), 99–118. DOI: 10.1016/0004-3702(77)90007-8. Establishes node/arc/path consistency and constraint propagation as local network-consistency operations distinct from constructing complete global solutions.
- Kschischang, F. R., Frey, B. J. & Loeliger, H.-A. (2001), `Factor Graphs and the Sum-Product Algorithm`, *IEEE Transactions on Information Theory* 47(2), 498–519. DOI: 10.1109/18.910572. Represents a global function as a product of local factors over subsets of variables, providing a clean formal counterexample to universal pairwise-edge thinking.
- Pearl, J. (1995), `Causal Diagrams for Empirical Research`, *Biometrika* 82(4), 669–688. DOI: 10.1093/biomet/82.4.669. Uses causal assumptions plus graphical structure to distinguish observational/statistical relations from intervention-identifiable causal effects.
- Allen, J. F. (1983), `Maintaining Knowledge About Temporal Intervals`, *Communications of the ACM* 26(11), 832–843. DOI: 10.1145/182.358434. Interval-based temporal relation system with constraint propagation, demonstrating richer temporal relation structure than point timestamp ordering.
- Treisman, A. & Schmidt, H. (1982), `Illusory Conjunctions in the Perception of Objects`, *Cognitive Psychology* 14(1), 107–141. DOI: 10.1016/0010-0285(82)90006-8. Features can be present yet recombined incorrectly, establishing binding as an independent organization problem.
- Smolensky, P. (1990), `Tensor Product Variable Binding and the Representation of Symbolic Structures in Connectionist Systems`, *Artificial Intelligence* 46(1–2), 159–216. DOI: 10.1016/0004-3702(90)90007-M. Formal distributed role/value binding and recursive structured representations; binding does not require localist symbolic units.
- Gray, C. M., König, P., Engel, A. K. & Singer, W. (1989), `Oscillatory responses in cat visual cortex exhibit inter-columnar synchronization which reflects global stimulus properties`, *Nature* 338, 334–337. DOI: 10.1038/338334a0. Synchronization across spatially separated feature-selective cortical columns motivates synchrony as one possible binding/relational mechanism.
- Thiele, A. & Stoner, G. (2003), `Neuronal synchrony does not correlate with motion coherence in cortical area MT`, *Nature* 421, 366–370. DOI: 10.1038/nature01285. Direct experimental falsifier of universal binding-by-synchrony in the tested MT motion-coherence setting.

---

# 128. Deep reconstruction

The naive composition model after MF4-B might still be written:

```text
Units
  |
 generic edges
  |
Whole
```

MF4-C replaces it with:

```text
Individuated Units / Roles
          │
          ├─ structural/spatial relations
          ├─ temporal relations
          ├─ role/ownership bindings
          ├─ statistical associations
          ├─ causal/dynamical coupling
          ├─ functional/resource dependencies
          ├─ interface/protocol contracts
          ├─ positive/negative constraints
          ├─ higher-order/meta-relations
          └─ uncertainty/provenance/lifetime
          │
          ▼
   Joint admissibility / interaction / interpretation structure
          │
          ├─ local consistency
          ├─ global coherence
          ├─ whole-level operations
          ├─ causal capabilities
          ├─ representational content
          └─ failure propagation
```

No one relation subtype is universally fundamental across all composition domains.

---

# 129. Deepest MF4-C conclusion

The strongest surviving candidate is:

> **Composition-defining relations are typed relations or constraints whose assignment, removal, alteration or violation changes the relevant identity, admissibility, operation, causal capability, interpretation, persistence or evaluation of the whole under a declared scope.**

This is deliberately broader than causality and narrower than arbitrary true relations.

Compactly:

`CompDef(R,W|Σ) iff ΔR ⇒ ΔRelevantProfile(W|Σ)`

where `Δ` is a counterfactual typed change, not necessarily a physical causal intervention.

---

# 130. Cross-round MF4 state after C

MF4 now provisionally has three mutually dependent layers:

```text
MF4-A
Whole-level composition criterion
      ▲            ▼
MF4-B
Unit / boundary individuation
      ▲            ▼
MF4-C
Relation / binding / dependency / constraint
```

No layer is universally prior.

This is now closer to a reciprocal constraint system than to bottom-up atom assembly.

---

# 131. MF4-D handoff — Hierarchy, Recursion, Modularity & Scale

MF4-C reveals a new question.

Once relations define wholes, those wholes often become units in larger wholes.

But hierarchy is not always tree-like, and multiple relation systems can cross-cut.

MF4-D must ask:

- When does a whole become a reusable unit?
- Strict hierarchy vs overlap/heterarchy.
- Recursive embedding.
- Near-decomposability and coupling timescales.
- Modularity vs mere clustering.
- Interface-stabilized modules.
- Encapsulation/information hiding.
- Part replacement and module identity.
- Cross-cutting hierarchies.
- Scale/granularity transitions.
- Coarse-graining and renormalization-like ideas without overclaim.
- Micro/macro relation preservation.
- Emergent macro variables.
- When macro-level constraints are autonomous/useful.
- Recursive symbolic composition vs physical hierarchy.
- Scene/object/part hierarchies.
- Narrative/event hierarchies.
- Software package/module/function hierarchies.
- Multi-level temporal organization.
- Whether hierarchy reduces coordination/computation cost.
- Failure propagation across module boundaries.
- Local/global optimization conflict.
- Hierarchy evidence vs hierarchy ontology.

**Next: MF4-D — Hierarchy, Recursion, Modularity & Scale.**

---

# Final MF4-C handoff

MF4-C rejects `edge soup` as a composition ontology.

A composition does not merely contain parts that are connected.

It contains **typed relational organization**:

- who occupies which role;
- what depends on what and in what sense;
- which joint states are allowed;
- which relations are causal versus statistical;
- what is standing specification versus active coupling;
- which relations are local versus global;
- which are pairwise versus n-ary;
- which persist across replacement;
- which are uncertain or ambiguous;
- and which relations actually matter counterfactually to the whole under scope.

The provisional core therefore becomes:

`Composition = Units/Boundaries + Composition-Defining Typed Relations/Constraints + Whole-level Organization + Scope`.

Composition Foundations remain UNFROZEN.

**Next: MF4-D — Hierarchy, Recursion, Modularity & Scale.**
