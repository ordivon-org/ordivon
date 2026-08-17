# Ordivon Media Foundations — MF4-D Hierarchy, Recursion, Modularity & Scale

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 15 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4-A Composition Ontology, MF4-B Parts/Units/Boundaries/Segmentation and MF4-C Relations/Binding/Dependency/Constraint complete and provisional.  
**Status:** MF4-D complete and PROVISIONAL. Composition Foundations remain UNFROZEN.  
**Next:** MF4-E — Temporal Composition, Sequence, Rhythm & Synchronization.

---

# 1. Problem statement

MF4-A→C now provide a reciprocal provisional composition model:

```text
Whole criterion
     ↕
Unit / Boundary individuation
     ↕
Typed Relation / Constraint structure
```

But complex media and systems rarely stop at one compositional level.

A whole can itself become a unit:

- letters → words → phrases → sentences → documents;
- pixels/edges → surfaces → objects → groups → scenes;
- notes → motifs → phrases → sections → works;
- actions → events → episodes → narratives;
- functions → modules → packages → services → systems;
- cells → tissues → organs → organisms;
- local state variables → macro variables.

This creates a tempting universal picture:

`micro parts → tree hierarchy → modules → macro whole`.

MF4-D attacks that picture.

Questions:

1. When does a composed whole become a reusable unit?
2. Is hierarchy always a tree?
3. What distinguishes hierarchy from containment, recursion, abstraction and dependency layering?
4. What makes a module more than a dense cluster?
5. What exactly is Simon's near-decomposability?
6. Can modules overlap?
7. Can several hierarchies cross-cut one substrate?
8. How can module identity survive internal replacement?
9. What is scale/granularity rather than simply `more detail`?
10. What makes a coarse-grained macro variable legitimate rather than arbitrary information destruction?
11. Can macro organization add explanatory/predictive/causal usefulness without invoking mysterious extra forces?
12. How do local and global organization constrain one another?

The target collapses are:

`Hierarchy = Tree = Containment = Recursion = Modularity = Clustering = Scale`.

and:

`Micro = Real / Macro = Convenient Approximation`.

Both are rejected.

---

# 2. Hierarchy is a relation among levels/wholes, not a shape by definition

A hierarchy minimally introduces some ordered relation among compositional units/wholes such that one level/unit is organized relative to another.

Possible relations include:

- part-of;
- contains;
- controls;
- abstracts;
- instantiates;
- depends-on;
- refines/coarsens;
- represents;
- temporal subdivision.

### Result

**CD-01 — `Hierarchy` must be typed by its ordering/relation. Hierarchy is not one universal unlabeled parent–child tree.**

---

# 3. Containment hierarchy ≠ Dependency hierarchy

A source file may be contained in package A while depending on library B outside that package.

A scene object can be spatially contained in a room while causally controlled by an external actor.

### Result

**CD-02 — Containment, ownership, dependency, control and abstraction hierarchies can diverge on the same components.**

---

# 4. Part–whole hierarchy ≠ Abstraction hierarchy

`engine part-of car`

is different from:

`car instance-of vehicle type`.

Likewise:

`pixel part-of image`

is distinct from:

`specific image instance-of photograph`.

### Result

**CD-03 — Mereological/organizational hierarchy and type/abstraction/classification hierarchy are distinct.**

---

# 5. Hierarchy ≠ Order alone

A total ranking `A>B>C` can be hierarchical in one formal sense but need not express nested compositional wholes.

MF4-D concerns **compositional hierarchy**, where lower-level units/wholes participate in higher-level organization.

### Result

**CD-04 — Ordered precedence/rank is not sufficient for compositional hierarchy.**

---

# 6. Whole-to-part reuse

A composed whole W can become a unit in a larger composition W' when W has enough standing identity/boundary/interface/role stability to be addressed at the higher scale.

### Result

**CD-05 — Hierarchical composition requires reification/reuse of a lower-level whole as a higher-level unit under a declared interface/identity profile.**

---

# 7. Reuse does not require hiding all internals

A phrase can function as one constituent while its words remain accessible.

A software service can be treated as one dependency while exposing diagnostics.

### Result

**CD-06 — Higher-level unitization can selectively abstract lower-level detail without ontologically erasing lower-level parts.**

---

# 8. Recursive reuse ≠ Hierarchy

Recursion means a composition/schema/process can invoke or contain another instance of the same or related compositional form.

Examples:

- expression contains expression;
- directory contains directory;
- function calls itself;
- narrative contains story-within-story.

A hierarchy can be non-recursive, and recursion can generate cyclic/dynamic structures rather than one static tree.

### Result

**CD-07 — Recursion is self-/same-schema reapplication, not synonymous with hierarchy.**

---

# 9. Structural recursion ≠ Process recursion

A recursive data structure can have a standing nested specification.

A recursive algorithm dynamically calls itself during execution.

### Result

**CD-08 — Recursive structure/specification and recursive process/execution are distinct.**

---

# 10. Recursive syntax does not require infinite realized depth

A grammar can permit unbounded recursive embedding even though any token/document has finite depth.

### Result

**CD-09 — Recursive generative capacity and realized hierarchy depth are distinct.**

---

# 11. Hierarchy is not necessarily a tree

Tree hierarchy assumes:

- one parent per node at a level;
- disjoint siblings;
- no cross-level/cross-branch overlap.

Real systems violate these assumptions.

### Result

**CD-10 — Tree structure is one hierarchy profile, not the universal ontology of hierarchy.**

---

# 12. Overlapping communities are a hard falsifier

Palla et al. find significant overlapping cohesive groups in collaboration, word-association and protein-interaction networks.

One node can therefore belong to multiple communities.

### Result

**CD-11 — Module/community membership can overlap; disjoint partitioning is not universally required for modular organization.**

---

# 13. Overlap can be role-specific rather than boundary failure

A person belongs to:

- research team;
- family;
- institution;
- social circle.

A software component can participate in:

- security concern;
- storage subsystem;
- observability pipeline.

### Result

**CD-12 — Overlap can reflect genuine cross-cutting composition dimensions rather than ambiguous segmentation.**

---

# 14. Heterarchy

Some systems organize through multiple intersecting authority/dependency/functional relations without one globally privileged top.

### Result

**CD-13 — Heterarchical/cross-cutting organization is admissible; compositional organization need not induce one global parent relation.**

---

# 15. Polyhierarchy

One unit can have multiple higher-level parents under the same general relation family.

Example: one media asset participates in multiple collections/products.

### Result

**CD-14 — Polyhierarchy is distinct from both strict tree hierarchy and unrelated overlapping relation systems.**

---

# 16. Hierarchical cycles require typing

A strict part-of relation should not ordinarily contain a direct cycle at one scale:

`A part-of B part-of A`.

But dependency/control/reference relations can cycle.

### Result

**CD-15 — Acyclicity is relation-type specific. Do not infer universal DAG structure from hierarchical language.**

---

# 17. Simon's hierarchy insight survives in a weaker form

Simon argues that complex systems frequently exhibit hierarchic organization: systems composed of subsystems that themselves contain subsystems.

MF4-D retains the empirical/architectural insight, but not `all complexity = hierarchy`.

### Result

**CD-16 — Hierarchy is a recurrent complexity architecture, not a universal law or minimal composition condition.**

---

# 18. Stable intermediate forms matter

Simon's watchmaker/parabolic assembly argument shows why systems assembled through stable intermediate subassemblies can be much more robust to disruption than systems requiring all elementary parts to remain assembled continuously until completion.

### Result

**CD-17 — Stable intermediate wholes can reduce assembly/recovery burden and enable recursive reuse; hierarchy can be a resource for construction and robustness.**

---

# 19. Stability is typed

A module can be stable in:

- physical persistence;
- interface/API;
- role;
- output behavior;
- semantic identity;
- organizational membership.

### Result

**CD-18 — `Stable module` requires a declared invariant; no one stability notion is universal.**

---

# 20. Near-decomposability

Simon's near-decomposable systems have relatively stronger/faster interactions within subsystems and weaker/slower interactions among subsystems.

In matrix form this can appear as approximate block structure with small off-block couplings.

### Result

**CD-19 — Near-decomposability is a relative coupling/timescale profile, not absolute independence of modules.**

---

# 21. Decomposable ≠ Near-decomposable

Perfectly decomposable:

subsystems can evolve independently.

Nearly decomposable:

cross-subsystem effects remain but can be weaker/slower than internal effects.

### Result

**CD-20 — Modularity does not require zero inter-module interaction.**

---

# 22. Near-decomposability is timescale-sensitive

On short timescales, within-module dynamics may dominate.

On long timescales, weak cross-module couplings may become decisive.

### Result

**CD-21 — A system can appear modular at one timescale and strongly integrated at another.**

---

# 23. Coupling type matters as much as magnitude

Low-volume control signals can be globally decisive.

High-volume telemetry can be functionally noncritical.

### Result

**CD-22 — Modularity cannot be inferred from raw interaction count/weight alone; relation type, direction, latency and failure impact matter.**

---

# 24. Module ≠ Dense graph cluster

A dense cluster may be statistically visible while lacking:

- stable interface;
- autonomous role;
- reusable function;
- change isolation;
- independent evaluability.

Conversely, a functionally coherent module may have sparse internal communication.

### Result

**CD-23 — Network clustering is evidence/candidate discovery for modularity, not modularity ontology.**

---

# 25. Parnas supplies a non-topological module criterion

Parnas shows the same software system can be decomposed by different criteria and argues for hiding design decisions likely to change behind module boundaries.

### Result

**CD-24 — Engineered modularity can be defined by responsibility/change isolation/information hiding rather than interaction density or physical containment.**

---

# 26. Encapsulation ≠ Isolation

A module can hide internal design while exposing a stable interface.

### Result

**CD-25 — Encapsulation is controlled visibility/permeability of internal distinctions, not absence of external relations.**

---

# 27. Information hiding ≠ Data secrecy only

Parnas-style information hiding concerns hiding design decisions likely to change, not merely security confidentiality.

### Result

**CD-26 — `Information hiding` in modularity is a change-dependency boundary, distinct from access-control secrecy.**

---

# 28. Module identity can be interface-stabilized

If implementation A is replaced with B while the declared interface/role/evaluation remains stable, higher-level compositions can preserve module identity.

### Result

**CD-27 — Module-token implementation and module role/interface identity are distinct.**

---

# 29. Replaceability is strong module evidence

A component that can be replaced without requiring widespread changes outside its boundary exhibits one form of modular autonomy.

### Result

**CD-28 — Controlled substitutability is strong evidence for module standing, though not a universal necessary condition.**

---

# 30. Nonreplaceable modules can still be modules

Historical artifacts, unique organs or tightly adapted components may be modularly individuated without easy replacement.

### Result

**CD-29 — Replaceability supports modularity but does not define it universally.**

---

# 31. Modularity is multidimensional

Candidate dimensions:

- internal cohesion;
- external coupling;
- interface stability;
- state autonomy;
- independent addressability;
- replaceability;
- change isolation;
- failure containment;
- reusable role;
- independent test/evaluation;
- timescale separation.

### Result

**CD-30 — Modularity is a profile, not one scalar property.**

---

# 32. Community modularity score is not module truth

A network quality function can rank partitions under its objective.

That does not establish one canonical natural decomposition.

### Result

**CD-31 — Algorithmic modularity score/optimization and ontological/functional modularity are distinct.**

---

# 33. Resolution limit is a decisive falsifier

Fortunato & Barthélemy show modularity maximization can fail to identify modules below a scale depending on global network size/interconnection, even when small modules are otherwise well-defined.

### Result

**CD-32 — Detected module boundaries can depend on the resolution/scale of the method; failure to detect a module at one resolution does not prove it lacks standing.**

---

# 34. Module scale cannot be globally inferred from one objective

If one quality function has a resolution threshold, different meaningful structures can appear at different scales.

### Result

**CD-33 — Multi-scale modular analysis is often necessary; one globally optimal partition is not universally meaningful.**

---

# 35. Scale ≠ Physical size

Scale may refer to:

- spatial extent;
- temporal duration;
- number of elementary units;
- representational granularity;
- abstraction depth;
- interaction timescale;
- organizational scope.

### Result

**CD-34 — Scale is a typed parameter family, not synonymous with spatial size.**

---

# 36. Granularity ≠ Scale exactly

Granularity concerns resolution of distinctions/units.

Scale can concern domain extent or dynamics even at fixed granularity.

### Result

**CD-35 — Granularity/resolution and scale/extent/timescale must be separated.**

---

# 37. Micro and macro are relational terms

A module is macro relative to its internal functions but micro relative to a distributed product.

### Result

**CD-36 — `Micro` and `macro` require a declared level relation; they are not absolute ontological categories.**

---

# 38. Level ≠ Scale automatically

Two descriptions can be at similar spatial scale but different organizational levels.

### Result

**CD-37 — Compositional level, spatial scale, temporal scale and abstraction level can vary independently.**

---

# 39. Coarse-graining is a mapping

Let micro state space be `X` and macro state space `M`.

A coarse-graining is roughly:

`π: X -> M`

which groups distinctions judged equivalent at the macro level.

### Result

**CD-38 — Coarse-graining is an explicit equivalence/mapping over lower-level states, not merely `looking from farther away`.**

---

# 40. Coarse-graining is usually many-to-one

Multiple microstates map to one macrostate.

### Result

**CD-39 — Coarse-graining typically collapses lower-level distinctions and is therefore information-losing relative to exact micro reconstruction.**

---

# 41. Information loss does not imply uselessness

If collapsed distinctions do not matter for target queries/operations, macro variables may be more tractable and robust.

### Result

**CD-40 — Reconstruction loss and task/explanatory adequacy are distinct; coarse representations can outperform fine ones for declared purposes.**

---

# 42. Kadanoff block variables provide the canonical constructive case

Kadanoff's Ising scaling argument divides a system into cells that are microscopically large but smaller than the coherence length, then uses aggregate magnetization as a collective variable.

### Result

**CD-41 — A macro variable can summarize many micro degrees of freedom while preserving structure relevant to a scale-specific regularity.**

---

# 43. Coarse-graining choice is not automatically unique

Different mappings can preserve:

- topology;
- mean state;
- causal predictability;
- task value;
- symmetry;
- information.

### Result

**CD-42 — Macro variables must declare what invariants/query family justify their grouping; many possible coarse-grainings can exist.**

---

# 44. Coarse-graining ≠ Averaging

Macro mappings can use:

- sums/means;
- majority states;
- equivalence classes;
- learned latent variables;
- event categories;
- interface-level state machines.

### Result

**CD-43 — Averaging is one coarse-graining operation, not the definition of macro description.**

---

# 45. Macro variable ≠ Mere statistic

A statistic can be computed from microstates without being dynamically closed/useful as a state variable.

### Result

**CD-44 — A macro variable gains stronger compositional status when it supports stable prediction, control, constraints, interfaces or reusable operations at its scale.**

---

# 46. Closure is graded/typed

A macro state may approximately predict its own future without requiring all micro details.

### Result

**CD-45 — Macro autonomy can be operationalized through approximate closure/sufficiency under a declared dynamics/query scope rather than metaphysical independence.**

---

# 47. Macro autonomy ≠ Micro independence

Macro states are realized by microstates.

Useful macro dynamics need not float free from lower-level implementation.

### Result

**CD-46 — Higher-level explanatory autonomy is compatible with supervenience/implementation by lower-level states.**

---

# 48. Hoel et al. provide one explicit macro-causal metric

Hoel, Albantakis & Tononi construct micro and coarse-grained macro causal models and measure effective information; in their simple systems EI can peak at a macro spatiotemporal scale when coarse-graining increases determinism and/or decreases degeneracy enough to offset smaller state-space size.

### Result

**CD-47 — Under at least one explicit intervention-based causal metric, a coarse macro model can outperform its micro description in causal effectiveness despite being determined by it.**

---

# 49. Hoel's result is measure/model conditional

MF4-D does not freeze:

`macro causal emergence = effective information`.

The result depends on:

- causal model;
- intervention semantics;
- coarse-graining;
- chosen metric.

### Result

**CD-48 — Macro causal/explanatory superiority must be typed to a criterion; one measure does not establish universal ontological emergence.**

---

# 50. Macro can be better because micro has irrelevant distinctions

If micro distinctions are noisy/degenerate relative to a query, grouping them can produce a cleaner macro transition structure.

### Result

**CD-49 — More microscopic distinctions do not guarantee more usable causal/explanatory information for every scope.**

---

# 51. Macro can also be worse

Coarse-graining can destroy decisive distinctions.

### Result

**CD-50 — Coarse-graining quality is task/model dependent; macro is not universally superior to micro.**

---

# 52. Effective level can be intermediate

The most useful scale need not be maximal micro or maximal macro.

### Result

**CD-51 — Composition can have privileged mesoscales relative to a query, without implying one globally privileged scale.**

---

# 53. Mesoscale modularity is a distinct concept

Modules often occupy intermediate scales:

micro units → module → global system.

### Result

**CD-52 — Modularity is frequently mesoscale organization, but `mesoscale` itself is relation/scope dependent.**

---

# 54. Macro state can become a unit for higher-level composition

If macro state `M` has stable identity/interface/transition relevance, higher-level systems can compose over `M` without querying all microstate details.

### Result

**CD-53 — Coarse-graining can create operationally reusable higher-level units.**

---

# 55. Abstraction boundary acts like an interface

Higher levels often access only selected properties of lower-level wholes.

### Result

**CD-54 — Abstraction can be modeled as selective permeability across levels, analogous to module interfaces.**

---

# 56. Hierarchy can reduce coordination complexity

When lower-level details are encapsulated and only aggregate/interface states propagate upward, every part need not coordinate directly with every other part.

### Result

**CD-55 — Hierarchical/module interfaces can reduce cross-component coordination/search burden under appropriate decomposability assumptions.**

---

# 57. But hierarchy can add overhead

Additional layers can create:

- latency;
- bureaucracy;
- duplicated state;
- translation cost;
- stale abstraction;
- local/global mismatch.

### Result

**CD-56 — Hierarchy/modularity are resources with costs, not universally optimal architecture.**

---

# 58. Local optimization can harm global whole

A module can optimize its own metric while degrading cross-module coherence.

### Result

**CD-57 — Local module objective and global composition objective are distinct; modularity creates coordination/governance problems as well as tractability benefits.**

---

# 59. Global optimization can destroy local autonomy

Excessive global coupling/control can make modules unable to evolve independently.

### Result

**CD-58 — Composition must balance local autonomy and global constraint; maximal integration is not universally optimal.**

---

# 60. Failure containment is a modular capability

A boundary can limit propagation of faults.

### Result

**CD-59 — Failure containment is one dimension of modularity distinct from interaction density and replaceability.**

---

# 61. Fault containment ≠ Semantic independence

Two modules may fail independently but remain tightly semantically coupled.

### Result

**CD-60 — Failure autonomy, state autonomy, semantic autonomy and deployment autonomy are distinct.**

---

# 62. Failure propagation reveals hidden hierarchy/dependency

A supposedly local fault causing global collapse can falsify claimed near-decomposability.

### Result

**CD-61 — Perturbation/failure propagation is useful evidence for effective module boundaries but does not alone define module ontology.**

---

# 63. Hierarchy can be standing or active

A document outline is a standing hierarchy.

An organizational command chain may be actively exercised only occasionally.

### Result

**CD-62 — Hierarchical relation standing and active cross-level operation are distinct.**

---

# 64. Structural hierarchy ≠ Processing order

A phrase-tree constituent can be nested structurally without being processed strictly bottom-up.

### Result

**CD-63 — Hierarchical organization and temporal processing sequence are distinct.**

---

# 65. Navon's global-precedence result is a falsifier of universal local-first processing

Navon's hierarchical-letter experiments found stronger/faster global-level effects in the tested conditions and interference from global information on local judgments.

### Result

**CD-64 — The existence of lower-level constituents does not imply perceptual/cognitive processing must first construct them and only then the global whole.**

---

# 66. Global precedence is not universal hierarchy ontology

Stimulus/task conditions can change global/local processing advantages.

MF4-D keeps only the stronger falsifier:

`structural lower-level priority ≠ universal temporal processing priority`.

### Result

**CD-65 — Ontological/compositional level and processing precedence must remain separate.**

---

# 67. Macro constraints can alter part role without changing micro substrate

A note's harmonic role changes with key/chord.

A word's syntactic role changes with sentence structure.

### Result

**CD-66 — Higher-level context can change lower-level functional/representational role while lower-level token identity remains.**

---

# 68. `Downward causation` language must be typed carefully

A macro constraint may be shorthand for distributed lower-level interactions plus boundary conditions.

### Result

**CD-67 — MF4-D prefers `cross-level constraint / macro-level difference-making` over unqualified downward-causation claims unless intervention semantics are explicitly defined.**

---

# 69. Macro-to-micro intervention can be implemented by many micro interventions

To set a macro state often requires selecting one among multiple micro realizations consistent with it.

### Result

**CD-68 — Cross-level intervention semantics require a realization policy; macro intervention is not automatically one unique micro manipulation.**

---

# 70. Multiple realizability is ordinary

Many different micro configurations can implement the same macro role/state.

Examples:

- different server instances provide same service;
- different glyph shapes instantiate same letter;
- different performances instantiate same score structure.

### Result

**CD-69 — Higher-level identity can be many-to-one over lower-level realizations under declared invariants.**

---

# 71. Multiple realizability ≠ No lower-level constraint

Not every microstate realizes the same macrostate.

### Result

**CD-70 — Macro identity still constrains an equivalence class of admissible micro realizations.**

---

# 72. Macro identity requires an equivalence relation/profile

`x ~_Σ y` if x and y count as the same macro state/unit under scope Σ.

### Result

**CD-71 — Higher-level identity is defined relative to retained invariants and collapsed distinctions, not vague similarity.**

---

# 73. Hierarchical identity can persist through turnover

A team/company/service/document can preserve higher-level identity while members/internal sections change.

### Result

**CD-72 — Whole identity can be history/interface/role continuous rather than token-part invariant.**

---

# 74. Excessive turnover can still break identity

If interfaces, roles, history or continuity all change, claiming same whole becomes unjustified.

### Result

**CD-73 — Persistence across replacement is graded/profiled, not guaranteed by a name/ID alone.**

---

# 75. Hierarchy depth is not complexity by itself

A deeply nested trivial chain can be simple.

A shallow dense recurrent network can be complex.

### Result

**CD-74 — Hierarchy depth, system complexity and integration are independent dimensions.**

---

# 76. More modules ≠ More modularity

Splitting every function into tiny units can increase coupling/coordination burden.

### Result

**CD-75 — Module count/fineness does not measure modular quality.**

---

# 77. Module boundary quality is purpose-relative

A decomposition optimized for:

- change isolation;
- latency;
- team ownership;
- failure containment;
- security;

may differ.

### Result

**CD-76 — One substrate can support several legitimate modular decompositions because modularity is relation/purpose typed.**

---

# 78. Purpose-relative ≠ Arbitrary

Each decomposition must demonstrate the relevant invariants/tradeoffs it preserves.

### Result

**CD-77 — Competing modular decompositions are constrained hypotheses, not free analyst choices.**

---

# 79. Cross-cutting modules are structurally expensive but sometimes real

When one concern spans many containment modules, interfaces/dependencies can cross hierarchical boundaries.

### Result

**CD-78 — Cross-cutting composition is genuine and can expose limitations of one decomposition axis.**

---

# 80. Multi-view architecture is often unavoidable

Software example:

- containment tree;
- call graph;
- data-flow graph;
- deployment topology;
- ownership structure.

### Result

**CD-79 — Complex compositions often require a family of coordinated hierarchical/relational views rather than one canonical architecture diagram.**

---

# 81. Cross-view consistency is itself a composition problem

A logical module may map to several deployment nodes; deployment change must preserve logical interface relations.

### Result

**CD-80 — Relationships between architectural views require explicit cross-level mappings/constraints.**

---

# 82. Hierarchical segmentation can be probabilistic

A narrative scene may plausibly belong to two acts; an event boundary can have coarse/fine alternatives.

### Result

**CD-81 — Hierarchical membership/level boundaries can be uncertain/overlapping rather than one crisp tree.**

---

# 83. Nested perceptual units can coexist

Navon-style global/local stimuli show one percept can support simultaneously meaningful whole and constituent levels.

### Result

**CD-82 — Presence of a global unit does not erase local units; multiple active levels can coexist.**

---

# 84. Attention can select level

A system can operate on local or global distinctions depending task.

### Result

**CD-83 — Level accessibility/use is context-dependent; hierarchical standing and active level selection are distinct.**

---

# 85. Recursive representation can preserve relational roles across depth

Nested syntax, code ASTs and scene graphs can reuse relation schemas recursively.

### Result

**CD-84 — Recursion can provide compositional reuse of schemas/roles across scales, but recursive capability is not required for all hierarchy.**

---

# 86. Recursive embedding can create scope/context stacks

An embedded quotation, function call or subscene introduces local scope while residing in a larger scope.

### Result

**CD-85 — Recursive hierarchy often requires explicit context/scope inheritance and shadowing rules.**

---

# 87. Scope leakage is a hierarchy failure

A local variable/configuration affecting unrelated parent/sibling scopes unexpectedly is analogous to boundary leakage.

### Result

**CD-86 — Hierarchical composition has scope/interface failure modes beyond missing parts or relations.**

---

# 88. Abstraction leak

Higher-level consumer unexpectedly depends on supposedly hidden lower-level detail.

### Result

**CD-87 — Abstraction leakage falsifies strong module independence/encapsulation claims.**

---

# 89. Macro aliasing

Two microstates grouped as one macrostate may produce importantly different future behavior.

### Result

**CD-88 — Coarse-graining can fail by collapsing distinctions that are not dynamically/task equivalent.**

---

# 90. Macro fragmentation

Microstates that are effectively equivalent may be unnecessarily split into several macro states.

### Result

**CD-89 — Overly fine macro state spaces can preserve irrelevant distinctions and reduce tractability/generalization.**

---

# 91. Scale mismatch

A unit/relation valid at one scale can be misleading at another.

Example:

- molecular detail for ecosystem policy;
- service-level latency hiding request-level tail failures;
- coarse narrative summary hiding causal event distinction.

### Result

**CD-90 — Scale mismatch is a typed compositional failure distinct from ordinary factual error.**

---

# 92. Cross-scale relation distortion

Aggregation can change apparent:

- correlation;
- causation;
- topology;
- synchrony;
- dependency.

### Result

**CD-91 — Relations do not automatically commute with coarse-graining; macro relation inference requires explicit validation.**

---

# 93. Coarse-graining may create apparent interactions

Two macro variables can appear strongly related because each aggregates many micro interactions.

### Result

**CD-92 — Macro relation strength/type must not be inferred as a literal one-to-one micro interaction.**

---

# 94. Coarse-graining may hide feedback

A macro transition can look feed-forward while micro realization contains recurrent dynamics.

### Result

**CD-93 — Macro causal/functional architecture and micro implementation topology can differ.**

---

# 95. Coarse-graining can preserve selected invariants

Useful macro mappings may preserve:

- outcome probabilities;
- topology;
- causal response;
- value/policy;
- interface behavior;
- symmetries.

### Result

**CD-94 — Macro adequacy is invariant/query typed, not reconstruction-completeness typed.**

---

# 96. Scale-specific lawfulness

Some regularities become simpler or more stable only at particular scales.

Kadanoff's block-variable reasoning is the canonical physical example.

### Result

**CD-95 — A higher level can reveal stable regularities obscured by microscopic detail without implying that micro reality is false.**

---

# 97. Compression ≠ Explanation

A short macro summary can compress data without supporting prediction/intervention/understanding.

### Result

**CD-96 — Compression length alone does not establish a meaningful macro variable/module.**

---

# 98. Prediction ≠ Explanation ≠ Control

A macro state can be predictive but not causally manipulable; a control abstraction can omit reconstructive detail.

### Result

**CD-97 — Macro usefulness must be profiled across prediction, intervention/control, reconstruction, interpretation and future optionality.**

---

# 99. Macro variables can be public/design constructs

Software API state, institutional roles or document sections can be macro units created by conventions/design rather than discovered natural clusters.

### Result

**CD-98 — Macro organization can be designed/conventional/functional as well as emergent from physical/statistical structure.**

---

# 100. Emergence ≠ Macro existence

A macro unit can simply be specified by design.

### Result

**CD-99 — Higher-level composition does not require emergence; emergence is one possible relation between levels.**

---

# 101. Emergence requires a criterion

Possible meanings include:

- novel property;
- unpredictability;
- irreducibility;
- causal effectiveness;
- autonomous lawfulness;
- observer surprise.

### Result

**CD-100 — `Emergence` is under-specified unless the failure/relation to lower-level description is named.**

---

# 102. Weak novelty is cheap

Almost any relational whole can have properties not attributable to one isolated part.

### Result

**CD-101 — Whole-level novelty alone is too weak to establish strong emergence.**

---

# 103. Strong irreducibility claims require stronger evidence

If macro behavior is fully implemented by micro interactions, claiming ontological independence requires more than practical explanatory utility.

### Result

**CD-102 — MF4-D does not adopt metaphysical strong emergence as a foundation.**

---

# 104. Explanatory level can still be objectively better for a question

If a macro description yields better invariance, prediction, intervention specificity or compression under scope, this is not merely subjective convenience.

### Result

**CD-103 — Scale-relative explanatory superiority can be objective under declared criteria without implying metaphysical independence.**

---

# 105. Modulehood can itself be emergent/learned

Repeated interaction/learning can create stable coalitions/interfaces that were not designed initially.

### Result

**CD-104 — Module provenance can be designed, evolved, learned, self-organized or conventional.**

---

# 106. Module provenance ≠ Module quality

Designed modules can be poor; emergent clusters can be useful or unstable.

### Result

**CD-105 — Origin and modular capability are separate dimensions.**

---

# 107. Hierarchy can reorganize dynamically

Teams, neural coalitions, software orchestration and narratives can form temporary higher-level units.

### Result

**CD-106 — Hierarchy need not be permanent; dynamic/reconfigurable hierarchical composition is admissible.**

---

# 108. Temporary hierarchy ≠ No hierarchy

A temporary task force can still have genuine role/authority/dependency levels during its lifetime.

### Result

**CD-107 — Persistence duration is independent of hierarchical standing during the valid interval.**

---

# 109. Flat appearance can hide hierarchy

A uniform API surface may conceal internal multi-level modules.

### Result

**CD-108 — External interface flatness does not imply internal structural flatness.**

---

# 110. Hierarchical appearance can hide dense cross-coupling

An org chart/tree can exist while actual communication/dependencies cross levels heavily.

### Result

**CD-109 — Declared hierarchy and effective interaction hierarchy are distinct.**

---

# 111. Formal hierarchy vs effective hierarchy

Examples:

- documented module tree;
- runtime call graph;
- social authority chart;
- actual influence network.

### Result

**CD-110 — Designed/formal hierarchy and effective/operational organization must be separately measured.**

---

# 112. Hierarchy failure taxonomy

MF4-D proposes:

## Wrong level assignment

Unit placed at inappropriate compositional level.

## Wrong parent/containment

Incorrect higher-level membership.

## Cross-level role confusion

Micro property attributed directly to macro unit or vice versa.

## Abstraction leak

Higher level unexpectedly depends on hidden lower-level detail.

## Interface instability

Internal change propagates across boundary.

## Over-modularization

Excess fragmentation increases coordination cost.

## Under-modularization

Excessive coupling prevents independent evolution/failure isolation.

## Resolution mismatch

Real modules missed/merged/split because analysis scale is wrong.

## Cross-cutting conflict

Different legitimate hierarchy views impose incompatible boundaries.

## Macro aliasing

Distinct relevant microstates collapsed.

## Macro fragmentation

Equivalent microstates unnecessarily distinguished.

## Scale mismatch

Model/question operates at inappropriate scale.

## Hierarchy staleness

Standing structure no longer matches effective runtime/organization.

### Result

**CD-111 — Hierarchy/modularity/scale failure is a typed family, not one `bad architecture` score.**

---

# 113. Hierarchy evidence profile

Possible evidence:

- nesting/containment;
- interaction-density/timescale separation;
- interface contracts;
- perturbation confinement;
- replaceability;
- recursive reuse;
- independent testability;
- coarse-grained predictive closure;
- cross-scale invariance;
- task-level addressability.

### Result

**CD-112 — No single clustering coefficient or diagram proves hierarchy/modularity.**

---

# 114. Modularity evidence should include intervention/failure tests

If changing internals while preserving interface leaves other modules stable, that supports modular change isolation.

### Result

**CD-113 — Controlled internal replacement/change is strong evidence for interface-stabilized module boundaries.**

---

# 115. Near-decomposability evidence should vary timescale

A system that looks block-diagonal over milliseconds may integrate strongly over minutes.

### Result

**CD-114 — Near-decomposability claims require interaction strength × relation type × timescale profiles.**

---

# 116. Macro-state evidence should include contrastive microstates

If microstates grouped into one macrostate generate systematically different relevant outcomes, macrostate is too coarse.

### Result

**CD-115 — Within-macro counterfactual heterogeneity is a key falsifier of proposed coarse-graining.**

---

# 117. Macro-state sufficiency is query-relative

A state can be sufficient for navigation but insufficient for reconstruction.

### Result

**CD-116 — Macro validity must name the supported query/action/evaluation family.**

---

# 118. Coarse-graining can improve robustness

By collapsing nuisance variation, macro states may remain stable across micro perturbations.

### Result

**CD-117 — Invariance to irrelevant micro variation is a positive macro-variable property, not merely information loss.**

---

# 119. Coarse-graining can improve transfer

A higher-level relation may generalize across different substrates/implementations.

### Result

**CD-118 — Substrate/implementation invariance can make macro representations/modules reusable across contexts.**

---

# 120. But invariance can over-collapse

If substrate variation changes capability in some contexts, abstracting it away loses future optionality.

### Result

**CD-119 — Macro invariance and future optionality trade off; robust abstraction can hide distinctions needed by future tasks.**

---

# 121. Hierarchy and resource allocation

Higher-level modules can allocate resources to subunits without representing every internal detail.

### Result

**CD-120 — Hierarchical composition can support selective delegation/resource allocation through coarse interface states.**

---

# 122. Delegation requires responsibility boundaries

If higher level delegates a function, the subordinate module needs an evaluation/contract boundary.

### Result

**CD-121 — Hierarchical delegation depends on role/interface/evaluation structure, not merely physical nesting.**

---

# 123. Delegation can create hidden failure modes

Local module reports can conceal internal fragility.

### Result

**CD-122 — Abstraction reduces cognitive/coordination load while potentially hiding risk; observability is a modular design dimension.**

---

# 124. Module observability ≠ Encapsulation

A module can expose health/evidence without exposing implementation authority.

### Result

**CD-123 — Encapsulation and observability can coexist; visibility of evidence need not violate change/interface boundaries.**

---

# 125. Hierarchy can support error localization

Failures can be isolated to a subtree/module if boundaries and contracts are explicit.

### Result

**CD-124 — Hierarchical organization can improve diagnosis when failure/evidence interfaces preserve causal provenance.**

---

# 126. Hierarchy can also obscure provenance

Aggregates can hide which lower-level part caused a macro anomaly.

### Result

**CD-125 — Coarse hierarchy creates attribution-loss risk; macro anomalies need not uniquely localize micro causes.**

---

# 127. Relation aggregation ≠ Relation preservation

A macro edge `A→B` may summarize many heterogeneous lower-level paths.

### Result

**CD-126 — Macro relation provenance should retain enough information to avoid treating aggregated relation as one elementary mechanism.**

---

# 128. Recursive hierarchy can explode combinatorially

Unbounded recursive composition can create enormous possibility spaces.

### Result

**CD-127 — Recursive generativity increases compositional capacity but also search/validation burden.**

---

# 129. Modularity can control recursive complexity

Reusable validated substructures let systems reason/build at chunk level.

### Result

**CD-128 — Stable modules can turn recursive composition into tractable reuse by compressing validated internal complexity behind interfaces.**

---

# 130. Chunking ≠ Module automatically

A cognitive/computational chunk may be convenient for memory without having strong operational autonomy/interfaces.

### Result

**CD-129 — Chunking is one coarse-unitization strategy, not equivalent to robust modularity.**

---

# 131. Hierarchy can have mixed relation types across levels

A document might use:

- containment at chapter level;
- temporal narrative dependency across chapters;
- hyperlink relations across hierarchy.

### Result

**CD-130 — Multi-level compositions can combine different relation semantics; parent–child links need not share one universal type.**

---

# 132. Cross-level relation typing prevents category errors

Example:

`module A calls function f`

and

`package P contains module A`

do not imply `package P calls f` in the same operational sense unless abstraction semantics define it.

### Result

**CD-131 — Relations do not automatically lift from micro to macro; cross-level lifting requires explicit semantics.**

---

# 133. Macro properties may be relational rather than additive

Team coordination quality is not sum of individual coordination values.

### Result

**CD-132 — Higher-level properties often depend on relation topology/constraint organization, not aggregation of part attributes.**

---

# 134. Macro state may require relational pattern

A `traffic jam` or `chord` is not identified by one element but by collective configuration.

### Result

**CD-133 — Macro units can be relational-pattern units rather than aggregate-value units.**

---

# 135. Relational macro patterns can move across members

A wave pattern persists while individual particles differ over time.

### Result

**CD-134 — Macro identity can track organization/pattern continuity rather than constituent identity.**

---

# 136. Pattern continuity ≠ Substance continuity

A processual whole can persist by dynamic replacement.

### Result

**CD-135 — Hierarchical composition must support process/pattern wholes, not only nested material containers.**

---

# 137. Scale transition can change unit type

At micro level units may be particles/events; at macro level the appropriate unit may be field/module/phase.

### Result

**CD-136 — Coarse-graining need not merely bundle same-type units; level transitions can introduce different unit ontologies.**

---

# 138. Level transition can change relation vocabulary

Micro collision relations may become macro pressure/flow relations.

### Result

**CD-137 — Macro relation types need not be simple renamings of micro relations; cross-level semantics requires justified mapping.**

---

# 139. New vocabulary does not imply new fundamental force

Macro relational language can summarize organized lower-level behavior.

### Result

**CD-138 — Ontological/semantic novelty at macro description does not automatically imply new fundamental physical causation.**

---

# 140. Coarse-graining and representation interact

A map intentionally omits details while preserving route topology.

### Result

**CD-139 — Representational abstraction is one specialized coarse-graining whose adequacy follows MF3 content/query/evaluation criteria.**

---

# 141. Coarse-graining and perception interact

Perception can represent groups/ensembles/textures without individuating each member.

### Result

**CD-140 — Perceptual macro-unit formation can bypass explicit fine-grained constituent representation.**

---

# 142. Coarse-graining and signal interact

Downsampling/filtering aggregates signal distinctions, but does not by itself establish semantic macro units.

### Result

**CD-141 — Signal-scale transformation and compositional macro-unit formation are distinct.**

---

# 143. Scale changes can introduce aliasing

If discarded micro distinctions affect macro observations/futures, coarse representation can become non-identifiable.

### Result

**CD-142 — Coarse-graining has an aliasing problem analogous to MF1: grouped microstates must be equivalent relative to intended macro queries/dynamics.**

---

# 144. Exact lumpability is a strong special case, not universal requirement

A coarse process is especially clean when macro transition behavior is independent of which microstate within a macro class realizes it.

Approximate macro models can still be useful when this holds only approximately.

### Result

**CD-143 — Exact dynamical closure/lumpability is a strong macro criterion, but useful hierarchy can rely on approximate sufficiency.**

---

# 145. Approximation requires error profile

A macro model should report where within-class micro differences matter.

### Result

**CD-144 — Approximate coarse-graining needs scoped distortion/error bounds rather than binary valid/invalid status.**

---

# 146. Multi-scale representation can preserve optionality

A system can maintain macro summaries plus drill-down access to micro detail.

### Result

**CD-145 — Hierarchical representations can trade efficiency and future optionality by retaining links between scales instead of discarding lower-level evidence entirely.**

---

# 147. Drill-down relation is not same as part-of

A dashboard metric may link to raw traces, but trace records are not necessarily mereological parts of the displayed number.

### Result

**CD-146 — Cross-scale provenance/navigation relations are distinct from composition/parthood relations.**

---

# 148. Scale interfaces need provenance

If a macro conclusion is derived from micro evidence, the mapping/history should be recoverable when fidelity matters.

### Result

**CD-147 — Cross-scale provenance is a distinct quality dimension supporting audit/reconstruction without being constitutive of all macro composition.**

---

# 149. Multi-scale contradictions are possible

Macro summary can say `healthy` while micro trace contains severe anomaly hidden by aggregation.

### Result

**CD-148 — Cross-scale coherence must be tested; valid macro statement under one metric may conflict with micro-critical evidence under another.**

---

# 150. Hierarchy evaluation is profile-based

Possible dimensions:

- compositional clarity;
- interface stability;
- near-decomposability;
- replaceability;
- failure containment;
- cross-scale fidelity;
- coordination cost;
- query sufficiency;
- future optionality;
- provenance;
- adaptation/evolvability.

### Result

**CD-149 — No universal scalar `hierarchy quality` or `modularity score` is frozen.**

---

# 151. Provisional HierarchyProfile

```text
HierarchyProfile = <
  Levels     : level identities,
  Rel        : cross-/within-level relation types,
  Nest       : containment/part organization,
  Overlap    : overlap/polyhierarchy/heterarchy profile,
  Recur      : recursive reuse/schema profile,
  Bound      : module boundaries/interfaces,
  Coupling   : within/between coupling by type/timescale,
  Invariant  : identity/equivalence retained per level,
  Map        : micro↔macro/coarse-graining mappings,
  Scope      : task/question/granularity,
  Active     : standing vs active realization,
  History    : replacement/version/reorganization,
  Evidence   : hierarchy/module evidence profile
>
```

---

# 152. Provisional ModuleProfile

```text
ModuleProfile = <
  U          : constituent units,
  Role       : whole-level role/function,
  Boundary   : functional/interface boundary,
  Cohesion   : internal relation profile,
  Coupling   : external relation profile,
  Interface  : exposed contract/state,
  Hidden     : abstracted design/internal distinctions,
  Identity   : persistence invariant,
  Replace    : substitutability profile,
  Failure    : containment/propagation profile,
  Change     : change-isolation profile,
  Test       : independent evaluability,
  Timescale  : near-decomposability profile,
  Scope      : decomposition purpose
>
```

---

# 153. Provisional CoarseGrainingProfile

```text
CoarseGrainingProfile = <
  X_micro   : micro state/unit space,
  M_macro   : macro state/unit space,
  Pi        : mapping/equivalence relation,
  Keep      : preserved distinctions/invariants,
  Collapse  : discarded distinctions,
  Dynamics  : macro transition/closure model,
  Query     : target query/action family,
  Error     : within-class distortion/aliasing,
  Provenance: micro↔macro traceability,
  Scale     : spatial/temporal/organizational scale,
  Optionality: retained drill-down/future distinctions
>
```

---

# 154. Provisional hierarchy/modularity capability profiles

## H0 — Nested grouping

Wholes contain/reuse lower-level units.

## H1 — Interface hierarchy

Higher level interacts through stabilized lower-level interfaces.

## H2 — Near-decomposable modular hierarchy

Within-module interaction stronger/faster/more consequential than between-module interaction under a timescale/profile.

## H3 — Recursive hierarchy

Composition schemas/wholes can recur inside themselves/instances.

## H4 — Overlapping/polyhierarchical organization

Units can participate in multiple higher wholes.

## H5 — Multi-scale coarse-grained organization

Stable macro variables/relations support useful higher-level operations.

## H6 — Cross-scale adaptive hierarchy

Levels/modules can reorganize while preserving selected higher-level identities/interfaces.

These are not a mandatory scalar progression.

---

# 155. Provisional non-collapse stack

```text
Hierarchy
 ≠ Tree
 ≠ Containment
 ≠ Dependency Layering
 ≠ Abstraction
 ≠ Recursion
 ≠ Modularity
 ≠ Clustering
 ≠ Scale
```

and:

```text
Module
 ≠ Dense Cluster
 ≠ Package/Directory
 ≠ Deployment Unit
 ≠ Team
 ≠ Interface
```

although one object may occupy several of these roles.

and:

```text
Micro
 ≠ More Real
Macro
 ≠ Mere Convenience
```

while also:

```text
Macro usefulness
 ≠ Metaphysical independence
```

---

# 156. Provisional axioms CD-01→CD-149 — compressed core

**CD-01–09** Hierarchy must be relation-typed; containment/abstraction/order/recursion and realized depth are distinct.

**CD-10–15** Tree/disjoint hierarchy is not universal; overlap, polyhierarchy, heterarchy and relation-specific cycles are admissible.

**CD-16–22** Simon-style hierarchy/stable intermediate forms/near-decomposability survive as architectural profiles; stability, coupling and timescale must be typed.

**CD-23–33** Module ≠ dense cluster; Parnas-style information hiding/change isolation and Palla/Fortunato overlap/resolution results defeat one canonical partition/modularity-score ontology.

**CD-34–43** Scale, granularity, level and coarse-graining are distinct; coarse-graining is an explicit often-many-to-one mapping and averaging is only one form.

**CD-44–54** Macro variables gain standing through stable query/prediction/control/interface roles; macro autonomy is compatible with lower-level realization; Hoel-style macro causal superiority is criterion/model conditional.

**CD-55–65** Hierarchy can reduce coordination but add overhead; local/global objectives conflict; standing hierarchy ≠ active processing; structural level ≠ processing order; Navon falsifies universal local-first processing.

**CD-66–73** Cross-level constraints, intervention realization, multiple realizability and persistence require typed equivalence/invariants rather than mysterious downward causation or token identity.

**CD-74–87** Depth/module count do not equal complexity/quality; competing modular views can be legitimate; cross-view mappings, probabilistic levels, recursion/scope and abstraction leaks are first-class.

**CD-88–103** Macro aliasing/fragmentation/scale mismatch/cross-scale relation distortion are distinct; emergence must be criterion-typed and strong metaphysical emergence is not adopted.

**CD-104–119** Modules can be learned/dynamic; formal/effective hierarchy differ; error/evidence profiles, robustness, transfer and optionality tradeoffs matter.

**CD-120–138** Delegation, responsibility, observability, provenance, recursive complexity, relation lifting and pattern/process macro units extend hierarchy beyond static containers.

**CD-139–149** Signal/perception/representation coarse-graining remain distinct; macro aliasing, closure/lumpability, approximation error, multi-scale drill-down/provenance and profile-based evaluation are first-class.

---

# 157. Claims rejected by MF4-D

Reject as universal foundational claims:

- hierarchy equals one unlabeled parent–child tree;
- compositional hierarchy equals containment, dependency, abstraction or ranking;
- recursion equals hierarchy;
- recursive capacity requires infinite realized depth;
- hierarchy requires disjoint siblings/one parent;
- every complex system is hierarchical;
- modularity means zero external interaction;
- module equals dense network cluster;
- one modularity/community-detection objective discovers the true modules;
- module boundaries are globally scale-invariant;
- one globally optimal partition exists;
- physical size equals scale;
- scale equals granularity equals compositional level;
- micro/macro are absolute categories;
- coarse-graining means averaging;
- any computed statistic is a legitimate macro variable;
- information loss implies macro uselessness;
- macro description is merely subjective convenience;
- macro description is universally superior;
- one causal-emergence metric defines emergence ontology;
- hierarchy always reduces complexity/cost;
- more layers/modules means better architecture;
- local module optimization guarantees global quality;
- failure independence equals semantic autonomy;
- structural hierarchy implies bottom-up processing order;
- macro constraint requires mysterious new downward force;
- macro intervention maps to one unique micro manipulation;
- multiple realizability means no lower-level constraints;
- hierarchy depth equals system complexity;
- one modular decomposition serves every purpose;
- purpose-relative decomposition is arbitrary;
- formal/deployed hierarchy equals effective interaction hierarchy;
- emergence is required for macro units;
- whole-level novelty alone proves strong emergence;
- coarse-grained relation automatically preserves micro relation semantics;
- module identity requires fixed component tokens;
- recursive composition is always beneficial/tractable;
- chunk equals module;
- relations automatically lift across levels;
- macro properties must be additive aggregates;
- scale transition preserves unit/relation ontology unchanged;
- signal downsampling equals compositional coarse-graining;
- exact lumpability is required for every useful macro model;
- one scalar hierarchy/modularity quality score is universal.

---

# 158. Primary/original literature anchors

- Simon, H. A. (1962), `The Architecture of Complexity`, *Proceedings of the American Philosophical Society* 106(6), 467–482. Hierarchic systems, stable intermediate forms and near-decomposability; MF4-D retains these as recurring architectural profiles rather than universal composition laws.
- Parnas, D. L. (1972), `On the Criteria To Be Used in Decomposing Systems into Modules`, *Communications of the ACM* 15(12), 1053–1058. DOI: 10.1145/361598.361623. Demonstrates decomposition criterion matters and motivates information hiding/change isolation rather than mere workflow/physical grouping.
- Palla, G., Derényi, I., Farkas, I. & Vicsek, T. (2005), `Uncovering the overlapping community structure of complex networks in nature and society`, *Nature* 435, 814–818. DOI: 10.1038/nature03607. Empirical/algorithmic evidence that cohesive communities can overlap substantially.
- Fortunato, S. & Barthélemy, M. (2007), `Resolution limit in community detection`, *PNAS* 104(1), 36–41. DOI: 10.1073/pnas.0605965104. Shows modularity optimization can miss small well-defined modules at scale-dependent resolution, falsifying naive `best partition = true modules` assumptions.
- Kadanoff, L. P. (1966), `Scaling laws for Ising models near Tc`, *Physics Physique Fizika* 2, 263. DOI: 10.1103/PhysicsPhysiqueFizika.2.263. Constructs collective block variables by grouping microscopically large cells and retaining aggregate magnetization, a canonical coarse-graining example.
- Hoel, E. P., Albantakis, L. & Tononi, G. (2013), `Quantifying causal emergence shows that macro can beat micro`, *PNAS* 110(49), 19790–19795. DOI: 10.1073/pnas.1314922110. Under an explicit effective-information intervention metric, some coarse-grained macro models outperform the micro model in causal effectiveness despite supervening on it; retained as criterion-specific evidence rather than universal emergence ontology.
- Navon, D. (1977), `Forest before trees: The precedence of global features in visual perception`, *Cognitive Psychology* 9(3), 353–383. DOI: 10.1016/0010-0285(77)90012-3. Global-level processing/interference in hierarchical visual stimuli provides a direct falsifier of universal local-first processing from structural hierarchy.

---

# 159. Deep reconstruction

The naive hierarchy picture is:

```text
micro atoms
   ↓ grouping
modules
   ↓ grouping
macro whole
   ↓
one true tree
```

MF4-D replaces it with:

```text
Micro / lower-level organizations
        │
        ├─ selected invariants / equivalence relation
        ├─ boundaries / interfaces
        ├─ typed within/between relations
        ├─ timescale separation
        ├─ role / responsibility
        └─ query / scope
        │
        ▼
Candidate module / macro unit
        │
        ├─ can overlap with other modules
        ├─ can be reused recursively
        ├─ can participate in several hierarchies
        ├─ can preserve identity across token turnover
        └─ can expose a selective interface
        │
        ▼
Higher-level compositions
        │
        ├─ coarse-grained dynamics
        ├─ macro constraints
        ├─ cross-level mappings
        └─ drill-down provenance
```

Hierarchy is therefore not a single graph but often a **family of typed cross-scale organization relations**.

---

# 160. Deepest MF4-D conclusion

The strongest surviving claim is:

> **A hierarchical/module level becomes compositionally real under a scope when a lower-level organization can be treated as a reusable higher-level unit because selected invariants, boundaries/interfaces and relations make its internal distinctions partly abstractable while preserving whole-relevant operations, constraints, identity or evaluation.**

And:

> **A legitimate macro/coarse-grained level is not justified by coarseness itself, but by an explicit mapping that collapses lower-level distinctions while preserving or improving declared invariants, predictive/control/causal structure, interpretive adequacy or operational interfaces within bounded error.**

This makes higher levels neither metaphysically magical nor merely arbitrary convenience.

---

# 161. Cross-round MF4 state after D

MF4 now has four provisional layers:

```text
MF4-A — Whole / composition criterion
          ↕
MF4-B — Units / boundaries / segmentation
          ↕
MF4-C — Relations / binding / dependency / constraints
          ↕
MF4-D — Hierarchy / modularity / scale / coarse-graining
```

The direction is not purely bottom-up.

Higher-level organizations can constrain lower-level role/unitization; lower-level perturbations can falsify claimed macro closure/modules.

---

# 162. Why MF4 is still unfrozen

Several major composition dimensions remain underdeveloped:

- time/sequence/rhythm beyond generic temporal relations;
- simultaneous vs sequential organization;
- synchronization and event continuity;
- multimodal/cross-medium integration;
- spatial/layout composition;
- narrative/montage/scene organization;
- interaction/agency/feedback composition;
- global coherence and gestalt;
- final cross-domain falsification.

MF4-D therefore does not freeze Composition Foundations.

---

# 163. MF4-E handoff — Temporal Composition, Sequence, Rhythm & Synchronization

MF4-C typed temporal relations and synchrony; MF4-D established timescale/hierarchy. But temporal composition itself still needs its own ontology.

MF4-E should attack:

- sequence vs mere succession;
- order vs timing;
- duration;
- interval relations;
- rhythm/meter/periodicity;
- phase;
- synchronization;
- simultaneity tolerance;
- tempo/rate;
- event continuity;
- temporal grouping/chunking;
- temporal hierarchy;
- predictive continuity;
- interruption/resumption;
- repetition/recurrence;
- anticipation/retrospection;
- temporal binding windows;
- montage/editing cuts;
- asynchronous multimodal streams;
- real-time deadlines;
- causal order vs presentation order vs narrative order;
- reversible vs irreversible sequence;
- loops/recurrence;
- temporal aliasing/resampling;
- temporal composition failure taxonomy.

The core question becomes:

> **When does a succession of states/events become one temporal composition, and which temporal relations survive retiming, interruption, synchronization and reordering?**

**Next: MF4-E — Temporal Composition, Sequence, Rhythm & Synchronization.**

---

# Final MF4-D handoff

MF4-D removes the assumption that complex composition naturally converges to one true tree.

The stronger picture is:

`Hierarchy = typed cross-level organization`.

`Module = scope-relative reusable whole with a boundary/interface/autonomy profile`.

`Coarse-graining = explicit distinction-collapsing mapping preserving declared invariants under error`.

`Macro usefulness ≠ metaphysical independence ≠ mere subjective convenience`.

And:

`Hierarchy ≠ Tree ≠ Recursion ≠ Modularity ≠ Clustering ≠ Scale`.

Composition Foundations remain UNFROZEN.

**Next: MF4-E — Temporal Composition, Sequence, Rhythm & Synchronization.**
