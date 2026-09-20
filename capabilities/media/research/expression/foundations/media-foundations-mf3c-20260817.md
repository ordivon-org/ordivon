# Ordivon Media Foundations — MF3-C Format, Code & Geometry

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 6 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A Representation Ontology and MF3-B Content/Correctness/Misrepresentation complete/provisional.  
**Status:** MF3-C complete as a provisional Representation round; Representation Foundations remain UNFROZEN.  
**Next:** MF3-D — Structural Representation & Models.

---

# 1. Problem statement

MF3-A established:

`Vehicle ≠ Content ≠ Format ≠ Geometry ≠ Mapping/Code ≠ Target ≠ Meaning`.

MF3-B then reconstructed content as a typed grounded proxy relation rather than a property readable directly from a vector or activation.

MF3-C asks what the vehicle-side distinctions actually are:

- What is a representational **code**?
- What is a **format**?
- What is a representation's **geometry**?
- Which properties are intrinsic and which are coordinate/basis dependent?
- When do two differently parameterized spaces count as the same representation?
- What does linear/nonlinear decodability show?
- Are sparse, localist or disentangled representations inherently better?
- How should invariance and equivariance be treated?
- What can representational-similarity metrics legitimately establish?

The central danger is a category error:

> observing a useful regularity in vehicle geometry and silently promoting it into representational content.

MF3-C therefore treats geometry as **one relational structure on a representation vehicle**, not as content itself.

---

# 2. Refined vehicle-side decomposition

Let a representation vehicle have a state space `Z`.

## 2.1 Vehicle

A physical/computational/biological realization capable of occupying states `z ∈ Z`.

Examples:

- spike-count vectors;
- temporal spike patterns;
- neural population activity;
- transformer residual-stream vectors;
- one-hot tokens;
- pixels in a map/image;
- probability vectors;
- graph states;
- symbolic strings;
- trajectories.

`Z` by itself has no representational content under MF3-A/B. Grounding and recruitment remain required.

## 2.2 Code

Provisional definition:

> **Code is the systematic assignment/relation by which content-relevant distinctions are associated with vehicle distinctions under a particular grounding and use context.**

A code can be deterministic or stochastic:

`z = E(c,h)`

or

`Z ~ p(z | c,h)`.

But `c` here means a content-relevant condition under an already grounded representational relation, not merely an arbitrary source variable.

A code can involve:

- codebooks;
- tuning curves;
- distributed population patterns;
- compositional token rules;
- probability-parameter mappings;
- learned encoders;
- spatial correspondences.

## 2.3 Format

Provisional definition:

> **Format is the organization of representational distinctions together with the primitive relations/operations by which a relevant consumer can use them.**

Format is therefore not equivalent to storage datatype.

A floating-point vector may implement:

- a one-hot categorical code;
- coordinates;
- logits;
- a probability simplex;
- a distributed feature code;
- coefficients in a basis;
- a sampled trajectory state.

The same physical/numerical datatype can host different representational formats because consumer operations and grounding differ.

Candidate format profiles include:

- discrete/categorical;
- scalar/ordinal;
- vector/distributed;
- spatial/topographic;
- temporal/trajectory;
- relational/graph;
- probabilistic/distributional;
- symbolic/compositional;
- generative/model-state;
- mixed/hybrid.

These are profiles, not mutually exclusive natural kinds.

## 2.4 Geometry

Provisional definition:

> **Geometry is selected relational structure over vehicle states—distance, angle, neighborhood, topology, subspace, manifold, similarity, transformation orbit or other relational organization—used or measured for some purpose.**

There is no guarantee of one unique geometry.

A representation may admit several relevant geometries depending on:

- chosen metric;
- noise model;
- readout family;
- consumer operations;
- local vs global scale;
- task;
- intervention structure.

## 2.5 Coordinates / basis

Coordinates are a parametrization of states in `Z`.

This must be separated from the abstract relational structure.

The same abstract state/geometry can have multiple coordinate descriptions; conversely, actively transforming vehicle states while keeping a fixed Euclidean metric or fixed downstream consumer can genuinely change geometry/use.

### MF3-C foundational separation

`Vehicle ≠ Code ≠ Format ≠ Geometry ≠ Coordinates ≠ Content`.

---

# 3. Passive coordinate change vs active representation transform

This distinction is essential and is commonly blurred in representation analysis.

Suppose `z ∈ R^d` and let `A` be invertible.

## Passive coordinate change

We are redescribing the **same abstract state** using new coordinates:

`z' = A z`.

If all tensors/metrics/operators are transformed covariantly, this is merely a change of coordinates. The underlying abstract geometry/function need not change.

## Active vehicle transform

We instead replace the actual state delivered to the consumer by:

`z' = A z`

while keeping the old metric/readout/consumer fixed.

Now behavior, distances, sparsity and usability may change.

## Compensated active transform

If the downstream linear consumer was

`y = W z`

and we replace it with

`W' = W A^{-1}`,

then

`W'z' = W A^{-1} A z = Wz`.

The complete input-output function can remain unchanged even though internal coordinates and many geometric statistics differ.

### Result

**RC-01 — Coordinate equivalence, geometric equivalence and functional equivalence are distinct.**

This is the first major reconstruction of MF3-C.

---

# 4. Invertibility preserves information, not every representational property

MF1 already established that invertible transforms can preserve information while radically changing visible structure.

MF3-C extends this into representation.

For an invertible map `f`:

`z' = f(z)`

an ideal decoder with access to `f^{-1}` loses no distinctions in `z`.

Therefore `z` and `z'` can be **information-equivalent**.

But arbitrary invertibility does not imply:

- equal Euclidean distances;
- equal angles;
- equal sparsity;
- equal local neighborhoods under a fixed metric;
- equal linear accessibility;
- equal computational cost;
- equal robustness to noise;
- equal accessibility to a fixed biological/technical consumer;
- equal causal role if the rest of the system is unchanged.

For a nonlinear invertible `f`, even simple linear separability/readout properties can change while total information remains recoverable in principle.

### Result

**RC-02 — Information-preserving equivalence is weaker than geometry-, readout-, consumer- and function-preserving equivalence.**

Therefore:

`invertible transform ≠ automatically same representation`.

Whether content is preserved is a relational question: if grounding/proxy recruitment and consumer role are correspondingly transformed, content may be preserved; if the transformed state is no longer used as the same proxy, it may not be.

**RC-03 — Representational equivalence cannot be decided from vehicle invertibility alone.**

---

# 5. A hierarchy of representation-equivalence claims

MF3-C introduces typed equivalence rather than one `same representation` predicate.

## E0 — Distinction / information equivalence

There exists a bijection/invertible mapping between relevant vehicle states.

Question:

`Can all distinctions be recovered in principle?`

## E1 — Topological equivalence

Relevant neighborhood/continuity structure is preserved under a homeomorphic relation.

Question:

`Are continuity and neighborhood relations preserved?`

## E2 — Geometric equivalence

A selected geometry is preserved, e.g. distances/angles under an isometry or specified distortion bound.

Question:

`Are the relational structures used by the analysis/consumer preserved?`

## E3 — Readout-class equivalence

The same family of content distinctions remains accessible to a restricted class of readouts, perhaps after parameter re-identification.

Example: invertible linear transforms preserve the existence of linear readouts when downstream weights may be transformed correspondingly.

## E4 — Consumer-functional equivalence

Relevant downstream behavior/computation remains equivalent under explicit consumer compensation or stitching.

Question:

`Can one representation substitute for another without changing the relevant system function beyond allowed adapters?`

## E5 — Causal-role equivalence

Interventions on corresponding states produce equivalent changes in downstream variables/behavior under a specified causal abstraction.

## E6 — Content equivalence

Both vehicles instantiate the same grounded proxy content/mode/evaluation role for the relevant system/practice.

This may coexist with large coordinate or geometric differences.

### Result

**RC-04 — Representation equivalence is typed; information, topology, geometry, readout, function, causal role and content must not be collapsed.**

---

# 6. Representational similarity metrics encode an invariance hypothesis

Representational similarity is never neutral.

A similarity metric implicitly says:

> transformations in some class should be ignored as irrelevant, while differences outside that class should count.

Examples from artificial-network analysis:

- CCA/SVCCA-type comparisons intentionally ignore broad linear/affine coordinate variation;
- linear CKA is invariant to orthogonal transformations and isotropic scaling but not arbitrary invertible linear transformations;
- RSA compares second-order dissimilarity structures rather than requiring unit-to-unit correspondence.

Kornblith et al. show a decisive limit: a similarity statistic invariant to **all invertible linear transformations** can become too permissive in high-dimensional settings, failing to provide meaningful discrimination when representation dimension exceeds sample count. CKA was introduced partly to avoid this excessive invariance while retaining useful cross-network comparison.

Ding, Denain & Steinhardt later ground similarity measures against functional criteria—sensitivity to changes affecting behavior and specificity against changes that do not—and show commonly used metrics disagree and fail in different regimes.

Therefore there is no ontology-level universal representation-similarity metric.

**RC-05 — Every representation similarity measure commits to an equivalence/invariance class; its scientific validity is task/question dependent.**

**RC-06 — More invariance is not automatically a better representation-similarity measure.**

---

# 7. RSA: geometry without unit correspondence

Kriegeskorte, Mur & Bandettini introduced Representational Similarity Analysis (RSA), characterizing a region/model through a representational dissimilarity matrix over conditions rather than matching individual measurement channels/units.

This demonstrates an important abstraction:

> representation-level relational structure can be compared even when coordinates/units are not aligned.

But RSA does not establish content by itself.

An RDM depends on:

- stimulus/condition set;
- chosen dissimilarity measure;
- preprocessing;
- sampling noise;
- representational state used.

Two systems can share an RDM over one condition set while differing in untested conditions, causal use or grounding.

### Result

**RC-07 — Second-order similarity structure can be a useful representation signature without being identical to content or causal role.**

---

# 8. Linear decodability — what it proves and what it does not

Suppose a property `T` is linearly decodable from `z`:

`T ≈ Wz+b`.

This is stronger than arbitrary nonlinear decodability because the consumer class is restricted.

It tells us that distinctions relevant to `T` are arranged so that a simple linear readout can extract them under the tested distribution.

It does NOT prove:

- the actual system uses that readout;
- `T` is the grounded content rather than a correlated property;
- the relevant geometry is causal;
- the encoding generalizes under intervention/distribution shift;
- an individual direction/unit has semantic privilege.

Hewitt & Manning's structural probe supplies a positive example: a learned linear transform of ELMo/BERT states can expose parse-tree distance/depth geometry. Hewitt & Liang's control-task work then supplies the necessary caution: probe success can partly reflect probe capacity, and high probe accuracy needs controls/selectivity analysis.

### Linear-transform invariance

If `z' = Az` with invertible linear `A`, then a linear readout remains possible:

`Wz = W A^{-1} z'`.

Thus the **existence** of a linear decoder is invariant to invertible linear coordinate mixing when decoder parameters may change.

But a particular semantic axis is not.

A sparse/local axis can become a dense mixture while the same linearly decodable relation survives.

### Result

**RC-08 — Linear decodability is a restricted accessibility property, not a sufficient content criterion.**

**RC-09 — Linear axes are basis-dependent even when the class of linearly decodable distinctions is preserved under invertible linear mixing.**

---

# 9. Localist vs distributed representation is partly basis-relative

Consider a one-hot code:

`z = e_i`.

In the canonical basis, content looks maximally localist/sparse.

Apply a dense invertible rotation `A`:

`z' = A e_i`.

Every content state may now activate many coordinates, despite preserving all distinctions and linear recoverability.

Therefore a naive statement such as:

> concept C is represented by neuron/unit/dimension j

is not basis-invariant.

## But physical coordinates can be privileged

In a biological or engineered implementation, coordinates may correspond to actual neurons, channels, wires or modules. Changing basis would require physically mixing signals and altering downstream connectivity, energy use, noise propagation and learning.

Therefore locality is neither fully intrinsic nor fully meaningless.

It is typed:

- **coordinate-locality:** sparse with respect to an analyst-selected basis;
- **implementation-locality:** localized in physically privileged units/channels;
- **consumer-locality:** accessible by restricted downstream connectivity/readout;
- **causal-locality:** intervention on a small subset has selective downstream effects.

### Result

**RC-10 — Localist/distributed and sparse/dense are meaningless without specifying the privileged basis/implementation/consumer.**

**RC-11 — Basis dependence does not erase implementation significance when coordinates correspond to physically distinct causal channels.**

---

# 10. Population codes falsify unit-centric representation

Neural population coding makes the previous point concrete.

Ma, Beck, Latham & Pouget show one model family in which populations of noisy neurons can encode probability distributions and support Bayesian-like combination through population operations. The ontology lesson is not that all cortex literally uses probabilistic population codes; it is that content-relevant structure may reside in the **joint population pattern and tuning/noise model**, not in individual units treated independently.

Hence:

- one neuron need not correspond to one content;
- a unit can contribute to several content distinctions;
- content can be encoded in population relations;
- downstream decoding assumptions matter.

### Result

**RC-12 — Representation may be genuinely population/distributed; single-unit semantic labeling is not an ontology requirement.**

---

# 11. Dimensionality ≠ number of represented factors

Representation analysis often reports:

- ambient dimension;
- rank;
- participation ratio/effective dimension;
- manifold dimension;
- number of principal components;
- number of linearly decodable variables.

These are not equivalent.

A low-dimensional nonlinear manifold can occupy many ambient coordinates.

A high-rank code can represent a small number of task variables with redundancy.

Many correlated target variables can be decodable from one low-dimensional underlying factor.

Conversely one semantic variable may require a high-dimensional robust code due to noise, uncertainty or nonlinear structure.

Therefore:

**RC-13 — Representation dimensionality is typed and does not directly count semantic/content factors.**

---

# 12. Disentanglement — strong universal form falsified

A common representation-learning ideal says independent generative factors should occupy separate latent dimensions.

This is attractive because it can support:

- modular intervention;
- simple readout;
- factor recombination;
- interpretability.

But the strong universal form fails.

Locatello et al. theoretically show that unsupervised disentanglement is fundamentally unidentifiable without inductive biases about models/data. Their large empirical study also finds that higher disentanglement does not necessarily reduce sample complexity on downstream tasks.

The deeper reason is gauge/non-identifiability:

if latent factors `s` generate observations through `x=g(s)`, many alternative invertible reparameterizations of the latent space can explain the same observed distribution unless additional constraints privilege one factorization.

Therefore `the true semantic axes` do not emerge from observational data alone in general.

### Reconstruction

Disentanglement must be typed relative to:

- chosen factor family;
- supervision/inductive bias;
- intervention structure;
- symmetry/equivalence group;
- downstream operation class;
- desired modularity.

A representation can be highly useful while entangled under one basis, and a factorized representation can be inefficient for a task that depends on mixed combinations.

**RC-14 — Disentanglement is not a universal intrinsic quality of representation.**

**RC-15 — Factorization is identifiable only relative to additional structural, supervisory, interventional or symmetry-breaking assumptions.**

**RC-16 — A useful notion of disentanglement is task/factor/intervention relative, not merely axis alignment.**

---

# 13. Invariance and equivariance at the representation layer

Let input/domain transformations form a group/action `g`.

For encoder `f`:

## Invariance

`f(g·x) = f(x)`.

The transformation is collapsed in the representation.

This is useful when `g` is nuisance for the represented content/task.

## Equivariance

`f(g·x) = ρ(g) f(x)`

for a structured action `ρ(g)` in representation space.

The transformation is preserved in a predictable form.

Cohen & Welling's group-equivariant CNNs provide a clean engineered example where translations/rotations/reflections can be built into transformation laws of feature maps.

### Ontology result

Invariance and equivariance are **typed transformation properties of a code/format**, not synonyms for representational quality or semantic meaning.

Maximum invariance destroys distinctions that may matter to another task; equivariance can preserve transformation structure while enabling downstream canonicalization or control.

This mirrors MF2's perceptual result that maximum invariance is not generally optimal.

**RC-17 — Invariance is deliberate distinction collapse relative to a transformation class; equivariance preserves transformation structure predictably.**

**RC-18 — Whether invariance or equivariance is preferable depends on content/task/consumer, not an ontology-wide ranking.**

---

# 14. Geometry can be causally important without being content

The fact that geometry ≠ content does not make geometry epiphenomenal.

Geometry can determine:

- which distinctions are linearly accessible;
- margin/robustness under noise;
- sample efficiency of a restricted reader;
- interpolation/extrapolation behavior;
- nearest-neighbor behavior;
- update dynamics;
- ease of compositional operations;
- capacity of local/simple downstream circuitry.

Therefore the correct statement is:

> **Geometry is a vehicle/consumer interface constraint that can make grounded content more or less usable under particular operations.**

This avoids two errors:

1. `geometry = semantics`;
2. `geometry is arbitrary because invertible transforms exist`.

**RC-19 — Representation geometry is operationally real when downstream mechanisms privilege particular metrics/operations, even though geometry does not by itself fix content.**

---

# 15. Function can stay same while representation changes — and vice versa

Network-stitching and similarity work shows a deeper nonidentity.

Csiszárik et al. demonstrate that layers from separately trained networks can often be connected with a simple affine stitching layer while retaining substantial task performance. This supports treating some internal differences as adapter-removable for the task.

Ding et al. show representation similarity metrics can disagree even when judged against concrete functional changes.

Braun, Grant & Saxe analytically show in deep linear networks that functional similarity and representational similarity can dissociate in both directions: similar function need not imply similar internal representations, and similar representations need not imply identical function.

### Result

**RC-20 — System function and internal representation are related but non-identical equivalence notions.**

A representation metric should not be chosen by intuition about geometry alone; the scientific question must specify what differences are meant to matter.

---

# 16. Representational geometry is stimulus-set and distribution relative

A geometry is observed through sampled states.

Suppose we calculate pairwise distances over dataset `X_test`.

Two models may have nearly identical geometry on this finite support while diverging sharply:

- off-distribution;
- under adversarial perturbation;
- under active intervention;
- in rarely sampled regions;
- along counterfactual directions.

Therefore:

**RC-21 — Empirical representational geometry is conditional on the sampled domain/distribution and cannot automatically be promoted to a global state-space claim.**

This is the representation-level analogue of MF1 sampling and MF2 observation dependence.

---

# 17. Geometry requires a metric/noise/operation model

Euclidean distance is often used by default, but it is not ontologically privileged.

Alternative relevant relations may include:

- cosine/angular similarity;
- Mahalanobis distance;
- Fisher information geometry;
- geodesic/manifold distance;
- Hamming/edit distance;
- KL or other divergences over distributions;
- graph shortest paths;
- task-defined distortion;
- causal/interventional distance;
- decoder-induced similarity.

The appropriate geometry depends on which perturbations and operations matter to the consumer/system.

Thus:

**RC-22 — A metric is an additional modeling/functional commitment, not a free property of a vector representation.**

---

# 18. Probabilistic format is not a point estimate with error bars attached

MF3-B already established probabilistic representations have distributional evaluation profiles.

MF3-C adds a format distinction.

A system can represent uncertainty through:

- explicit probability vectors;
- distribution parameters;
- samples/particle populations;
- population activity whose likelihood family encodes uncertainty;
- ensembles;
- implicit generative distributions.

These formats can carry similar distributional content while having radically different vehicle geometry and primitive operations.

Therefore:

**RC-23 — Probabilistic content does not imply one canonical probabilistic vehicle format.**

And the reverse:

**RC-24 — Normalized activations or stochastic states are not automatically probability representations; grounding/use must establish distributional content.**

---

# 19. Code redundancy revisited at the representation layer

MF1 established redundancy is not inherently waste.

Representation makes this more specific.

Multiple vehicle dimensions/states can redundantly support the same grounded distinction for:

- noise robustness;
- error correction;
- graceful degradation;
- multiple downstream consumers;
- compositional reuse;
- distributed intervention tolerance.

Thus low-dimensional minimal codes are not universally better.

Sparsity, compression and dimensionality reduction trade against robustness, accessibility and optionality depending on consumer/task.

**RC-25 — Representational redundancy is a typed resource, not evidence of poor representation by itself.**

---

# 20. Code degeneracy and multiple realization

The reverse is also important:

The same content can be realized by different codes/formats:

- Celsius vs Fahrenheit;
- Cartesian vs polar coordinates;
- one-hot vs distributed category code;
- map projections;
- different neural population bases;
- different learned embedding spaces.

If grounding and downstream proxy role are preserved, representational content may remain equivalent despite code/format changes.

Therefore:

**RC-26 — Content admits multiple vehicle/code realizations; no canonical coordinate system follows from content alone.**

This is a representation-level gauge freedom.

---

# 21. A representation gauge perspective

MF3-C introduces a useful but carefully limited abstraction:

> **Gauge freedom = transformations of representation vehicle/parameters that change descriptive coordinates or some non-functional statistics while preserving a specified representational/systemic equivalence class.**

The key phrase is **specified equivalence class**.

Different gauges may preserve different things:

- all information;
- linear readout family;
- task output;
- causal abstraction;
- content;
- metric structure.

There is no universal gauge group for all representations.

### Result

**RC-27 — Representation analysis must state what transformation group is treated as gauge/irrelevant and justify it from the scientific or consumer-level question.**

This prevents accidental reification of arbitrary axes.

---

# 22. Revised Representation ontology after MF3-C

MF3-B's episode:

```text
RepEpisode = <
  V : vehicle,
  D : target/domain,
  Φ : represented condition/structure,
  M : representational mode,
  G : frame/granularity,
  U : proxy recruitment/use,
  B : grounding basis/provenance,
  E : evaluation profile,
  H : history/context,
  S : system/practice/consumer-role
>
```

MF3-C now expands the vehicle side:

```text
VehicleProfile(V) = <
  Z : vehicle state space,
  K : code / assignment relation,
  F : format / primitive organization & operations,
  Γ : selected geometry/geometries,
  Q : coordinates/basis/parameterization,
  A : accessible readout/operation classes,
  Ω : noise/resource/implementation constraints
>
```

Representation analysis therefore requires both:

`Grounded Content Profile × Vehicle/Consumer Profile`.

Neither side alone defines the complete representation.

---

# 23. MF3-C provisional axioms

**RC-01** Coordinate, geometric and functional equivalence are distinct.

**RC-02** Invertible information preservation is weaker than preservation of geometry, readout accessibility, consumer function or causal role.

**RC-03** Vehicle invertibility alone cannot establish representational/content equivalence.

**RC-04** Representation equivalence is typed: information, topology, geometry, readout, function, causal role and content are separate claims.

**RC-05** A representation-similarity metric encodes an invariance/equivalence hypothesis; no universal metric is ontology-mandated.

**RC-06** Greater invariance of a similarity measure is not automatically better.

**RC-07** Second-order similarity/RDM structure can compare representations without unit alignment but is not itself proof of equal content or causal role.

**RC-08** Linear decodability is restricted accessibility, not sufficient evidence of grounded content.

**RC-09** Particular semantic axes/directions are basis dependent even where linear readout existence is preserved under invertible linear mixing.

**RC-10** Localist/distributed and sparse/dense claims require a specified basis, implementation or consumer.

**RC-11** Physical coordinates can be causally privileged, so basis dependence does not make locality operationally meaningless.

**RC-12** Representational content may reside in population/distributed patterns; one-unit/one-content mapping is not required.

**RC-13** Ambient dimension, rank, intrinsic/manifold dimension, effective dimension and number of semantic factors are distinct.

**RC-14** Disentanglement is not a universal intrinsic representation quality.

**RC-15** Factorization/disentanglement requires inductive bias, supervision, intervention, symmetry-breaking or other structural assumptions for identifiability.

**RC-16** Useful disentanglement is relative to chosen factors, operations and interventions, not merely alignment with coordinate axes.

**RC-17** Invariance collapses distinctions relative to a transformation class; equivariance preserves transformation structure under a predictable representation-space action.

**RC-18** Invariance and equivariance are task/content/consumer-relative properties, not universally ranked virtues.

**RC-19** Geometry can be causally/operationally important for accessibility, robustness and computation without determining semantic content by itself.

**RC-20** Functional similarity and representational similarity are non-identical and can dissociate.

**RC-21** Empirical representation geometry is conditional on the sampled state/domain distribution.

**RC-22** Choice of metric/geometry is a modeling or consumer-level commitment; Euclidean geometry is not automatic merely because the vehicle is a vector.

**RC-23** Similar probabilistic content can be implemented in multiple probabilistic formats.

**RC-24** Stochastic or normalized vehicle states do not automatically possess probabilistic content.

**RC-25** Representational redundancy is a typed resource and can improve robustness/accessibility; minimal dimensionality is not universally optimal.

**RC-26** The same content can have multiple code/format/coordinate realizations.

**RC-27** Any claimed representational gauge/equivalence must explicitly specify the transformations considered irrelevant and what they preserve.

**RC-28** Format is defined partly by consumer-accessible primitive relations/operations, not raw datatype alone.

**RC-29** Code is the grounded systematic assignment between content-relevant distinctions and vehicle distinctions; code is not identical to content.

**RC-30** Geometry is one relational organization over vehicle states and may be plural; representation need not possess one privileged global geometry.

---

# 24. Claims rejected by MF3-C

Reject as universal foundational claims:

- content is the geometry of the embedding;
- a vector has one intrinsic Euclidean semantic geometry;
- any invertible transform produces the same representation in every relevant sense;
- two representations with the same information are representationally identical;
- functional equivalence implies identical internal representation;
- representational similarity implies identical system function;
- CCA/CKA/RSA or any one metric is the universal measure of representation similarity;
- invariance to more transformations always makes a similarity metric better;
- linear decodability proves that the system represents the decoded variable;
- a linear semantic direction is a basis-independent ontological feature;
- sparse/localist codes are inherently more meaningful;
- dense/distributed codes are inherently more powerful;
- one neuron/unit corresponds to one represented concept by default;
- ambient dimensionality counts semantic factors;
- disentanglement can be learned uniquely from observational data without inductive assumptions;
- disentangled representations are universally more useful or sample efficient;
- maximum invariance is universally desirable;
- every content should occupy an invariant axis;
- representation geometry is arbitrary/meaningless merely because invertible transformations exist;
- Euclidean distance is privileged for every vector representation;
- probabilistic content requires one particular probability-vector format;
- normalized activations automatically represent probabilities;
- redundancy is representational waste;
- there exists one canonical coordinate system determined by content alone.

---

# 25. Hard cross-domain examples

## 25.1 Temperature

Same content can use:

- Celsius scalar;
- Fahrenheit scalar;
- binary thermometer code;
- analog needle angle;
- neural population code.

Content equivalence does not require vehicle/metric equivalence.

## 25.2 Map

Cartesian coordinate lists and a distorted metro topology map can represent overlapping spatial domains while preserving different relations. Geometry must be typed by what relations the map is designed/recruited to preserve.

## 25.3 Word embedding

A word vector may make a property linearly decodable. Rotating the entire embedding by an invertible orthogonal transform destroys named coordinate directions but preserves Euclidean dot products/distances and linear readout capacity after reader rotation. Therefore individual axes are not semantic primitives.

## 25.4 Transformer residual stream

A residual vector's coordinates are tied to actual learned matrices, so arbitrary basis changes require conjugate transformations of connected weights to preserve function. This gives a concrete example of representation gauge freedom that is real only when the whole connected computation transforms consistently.

## 25.5 Neural population

Population activity can support content inaccessible from individual neurons. The physical neuron basis matters causally because synaptic wiring and noise are not freely rotated by an analyst, even though abstract code analysis may use alternative bases.

## 25.6 Probability forecast

A categorical probability vector and a generative sampler can implement distributional content with different primitive operations. Equal content does not imply equal code/format.

---

# 26. Primary/original literature anchors

- Kriegeskorte, N., Mur, M. & Bandettini, P. (2008), `Representational similarity analysis – connecting the branches of systems neuroscience`, *Frontiers in Systems Neuroscience* 2:4. Introduces RSA/RDM comparison across brain, behavior and computational models without requiring unit-wise correspondence.
- Raghu, M., Gilmer, J., Yosinski, J. & Sohl-Dickstein, J. (2017), `SVCCA: Singular Vector Canonical Correlation Analysis for Deep Learning Dynamics and Interpretability`, arXiv:1706.05806. Representation comparison designed to abstract over affine transformations and identify shared subspaces.
- Kornblith, S., Norouzi, M., Lee, H. & Hinton, G. (2019), `Similarity of Neural Network Representations Revisited`, ICML/PMLR 97. Shows limits of similarity measures invariant to arbitrary invertible linear transformations and introduces/grounds CKA for neural representation comparison.
- Hewitt, J. & Manning, C. D. (2019), `A Structural Probe for Finding Syntax in Word Representations`, NAACL. Tests whether parse-tree distance/depth structure is accessible after a linear transformation of ELMo/BERT representation spaces.
- Hewitt, J. & Liang, P. (2019), `Designing and Interpreting Probes with Control Tasks`, EMNLP-IJCNLP. Shows probe accuracy can reflect probe capacity and introduces control tasks/selectivity.
- Locatello, F. et al. (2019), `Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations`, ICML/PMLR 97. Proves general unsupervised disentanglement non-identifiability without inductive biases and provides a large-scale empirical falsification of common disentanglement assumptions.
- Cohen, T. & Welling, M. (2016), `Group Equivariant Convolutional Networks`, ICML/PMLR 48. Explicit engineered example of equivariant representation transformations under group actions.
- Ma, W. J., Beck, J. M., Latham, P. E. & Pouget, A. (2006), `Bayesian inference with probabilistic population codes`, *Nature Neuroscience* 9, 1432–1438. Demonstrates a model family where population activity represents probability distributions and supports Bayesian combination.
- Roeder, G., Metz, L. & Kingma, D. (2021), `On Linear Identifiability of Learned Representations`, ICML/PMLR 139. Shows broad classes of discriminative learned representations can be identifiable up to linear indeterminacy under sufficient conditions.
- Ding, F., Denain, J.-S. & Steinhardt, J. (2021), `Grounding Representation Similarity Through Statistical Testing`, NeurIPS 34. Evaluates similarity measures by sensitivity/specificity relative to functional changes and exposes metric disagreement/failure cases.
- Csiszárik, A. et al. (2021), `Similarity and Matching of Neural Network Representations`, NeurIPS 34. Uses affine stitching between separately trained networks to operationalize task-level interchangeability of internal representations.
- Braun, L., Grant, E. & Saxe, A. M. (2025), `Not all solutions are created equal: An analytical dissociation of functional and representational similarity in deep linear neural networks`, ICML/PMLR 267. Analytically demonstrates dissociation between function and representation similarity.

---

# 27. MF3-C reconstruction

The most important result is that `geometry` is neither semantic truth nor arbitrary decoration.

A better layered picture is:

```text
Grounded Content
       │
       │ systematic code / proxy mapping
       ▼
Vehicle State Space Z
       │
       ├─ coordinates / basis
       ├─ code assignment
       ├─ format / primitive operations
       ├─ geometry / topology / metric
       ├─ accessibility to reader classes
       ├─ implementation/noise/resource constraints
       └─ transformation/gauge freedoms
                │
                ▼
          Consumer computation
```

Content does not determine one unique geometry.

Geometry does not determine content.

But geometry can determine **how cheaply, robustly and causally a particular consumer can use grounded content**.

Thus:

> **Representation geometry is a typed interface between code and consumer, not the content itself.**

---

# 28. Deep synthesis

MF3-C replaces a vague idea of `representation space` with five explicit questions:

1. **What distinctions exist in the vehicle?**
2. **Which content-relevant distinctions are systematically coded into them?**
3. **What relations/operations define the relevant format and geometry?**
4. **Which consumers/readouts can actually exploit those relations under physical/computational constraints?**
5. **Which transformations are merely gauge/coordinate changes, and which alter function, causal role or content?**

This yields the compact non-collapse:

`Content ≠ Code ≠ Format ≠ Geometry ≠ Coordinates ≠ Readout ≠ Function`.

And the equivalence non-collapse:

`Information equivalence ≠ Geometric equivalence ≠ Readout equivalence ≠ Functional equivalence ≠ Causal-role equivalence ≠ Content equivalence`.

---

# 29. MF3-D handoff — Structural Representation & Models

MF3-C deliberately stops before declaring when a structural correspondence itself becomes a model.

MF3-D should now attack:

- what makes a map/model structurally represent a target rather than merely share a pattern;
- homomorphism/isomorphism/simulation relations;
- selective structural preservation and distortion;
- models as representations of possibility spaces rather than single states;
- diagrams, maps, images, graphs and scientific models;
- generative models/world models;
- simulation vs prediction vs representation;
- causal models and counterfactual structure;
- model fidelity vs task sufficiency;
- structural misrepresentation;
- when a model has multiple valid interpretations;
- whether world models represent latent causes, predictive sufficient statistics or task-relative state variables;
- how model structure is grounded and evaluated.

This is **MF3-D — Structural Representation & Models**.

---

# Final MF3-C handoff

MF3-C establishes that representation analysis needs an explicit **transformation/equivalence discipline**.

A vector's coordinates, sparsity, axes and Euclidean distances are not semantic primitives. Yet internal geometry is not arbitrary when real consumers, metrics, noise, wiring and operations privilege particular relations.

The correct question is no longer:

> `What does this embedding geometry mean?`

but:

> `Which grounded distinctions are encoded, what relational structure over vehicle states is preserved, which operations/readouts exploit it, and under what transformation class should two realizations count as equivalent?`

**Next: MF3-D — Structural Representation & Models.**
