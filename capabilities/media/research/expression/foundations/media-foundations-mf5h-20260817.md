# Ordivon Media Foundations — MF5-H Computational, Latent, Semantic & Abstract Spatial Standing

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 30 at start  
**Input:** MF0–MF4 frozen; MF5-A→G complete/provisional.  
**Status:** MF5-H complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-I — Space Falsification & Reconstruction.

---

# 0. Central problem

MF5-G established:

```text
Space of Representation ≠ Represented Space ≠ Enacted Virtual Space
```

MF5-H attacks the most inflationary modern use of `space`: vector space, feature space, embedding space, latent space, semantic space, probability space, state space and learned manifold.

> **When mathematics/computation gives a domain coordinates, neighborhoods, distances or interpolation, when is this merely formal structure, when does it acquire computational spatial standing, and when can it be transferred to target semantic/world spatial standing?**

Central attack:

```text
Mathematical Space ≠ Target Spatial Domain
Vector Coordinates ≠ Spatial Standing
Embedding Distance ≠ Target Distance
Visualization Geometry ≠ Latent Geometry
Latent Geometry ≠ Semantic/World Geometry
Decodability ≠ Spatiality
Smooth Interpolation ≠ Meaningful Path
Learned Metric ≠ Intrinsic Metric
Disentangled Axis ≠ True Factor
```

---

# 1. Mathematical `space` is not one ontology

Mathematics uses `space` for vector, topological, metric, probability, function, Hilbert and state spaces.

### SH-01
**Mathematical-space terminology ≠ MF5 target spatial standing.**

### SH-02
A mathematical space can have genuine formal structure without representing physical/perceptual/action space.

### SH-03
**A bare vector space is algebraic, not automatically metric.** It gives addition/scalar multiplication; norm/inner-product/metric are additional structures.

### SH-04
`Vector Space + Inner Product → Norm → Metric → Topology` is an enrichment/forgetful chain, not identity.

### SH-05
**Coordinate encodability ≠ target spatiality.** Any finite set can be encoded by tuples/one-hot vectors.

### SH-06
Representing `e` by `z(e)∈R^d` establishes a formal representation domain first.

### SH-07
**Metric definability ≠ target metric standing.** A finite set always admits trivial metrics.

### SH-08
A distance becomes meaningful through standing, invariants, task recruitment or grounded target relations—not mere definability.

---

# 2. Feature and metric geometry can be task-constructed

A feature vector is a system/model representation used for prediction/discrimination/retrieval.

### SH-09
**Feature-space geometry has formal/computational standing before target standing.**

### SH-10
Heterogeneous feature dimensions/units make raw Euclidean distance underdetermined without scaling semantics.

### SH-11
Standardization/whitening/rescaling can change nearest-neighbor geometry without changing target examples.

### SH-12
**Representation scaling change ≠ target identity change.**

Weinberger, Blitzer & Saul explicitly learn a Mahalanobis distance to optimize kNN classification, making same-class examples close and different-class examples separated.

### SH-13
**Learned metric can be objective-induced rather than target-intrinsic.**

### SH-14
Better classification ≠ proof of one natural target metric.

### SH-15
When a system actually uses a metric for retrieval/classification/planning and behavior changes counterfactually when that metric changes, the geometry acquires **computational standing**.

### SH-16
**Computational standing ≠ world/semantic intrinsic geometry.** It can be an engineered interface geometry.

---

# 3. Word embeddings: useful geometry without semantic-ontology collapse

Mikolov et al. learn continuous word vectors evaluated on syntactic/semantic similarity; GloVe learns corpus-statistical word vectors with useful relational regularities.

### SH-17
**Word-vector geometry can encode useful semantic/syntactic relations.**

### SH-18
Useful vector regularity ≠ proof that meaning is intrinsically Euclidean/vector-spatial.

### SH-19
Embedding neighborhoods depend on corpus, objective, context definition, dimension, normalization and similarity measure.

### SH-20
**Semantic embedding neighborhood ≠ context-free semantic truth.**

### SH-21
Cosine similarity is a chosen vector relation, not semantic distance by mathematical identity.

### SH-22
Its semantic standing is empirical/task-relative and relation-specific.

### SH-23
Vector-offset analogies are selected relational evidence, not proof of a globally faithful semantic manifold.

### SH-24
Local algebraic usefulness can coexist with failures on other semantic relations.

---

# 4. Latent spaces are model-relative

For `x → z → x_hat/y`, latent `z` depends on architecture, objective, prior, data and training history.

### SH-25
**Latent variable ≠ true generative/causal factor by default.**

### SH-26
**Latent geometry ≠ semantic/world geometry by default.**

A decisive reparameterization hard case is:

```text
z' = h(z)
g' = g ∘ h^-1
```

for an invertible `h`, preserving observable behavior/distribution under broad model classes while changing latent coordinates and potentially distances/angles/straightness.

### SH-27
**Observational equivalence can coexist with different latent geometries.**

### SH-28
Reconstruction/prediction success therefore does not identify latent coordinates.

Locatello et al. show unsupervised disentanglement is fundamentally impossible in their general formulation without inductive biases, and their large-scale experiments show well-disentangled solutions are not generally selectable without supervision.

### SH-29
**Clean/disentangled latent axes are not self-authenticating true factors.**

### SH-30
**Axis interpretability ≠ identifiability.**

Hyvärinen et al. and Khemakhem et al. show extra temporal/auxiliary/conditional structure can make nonlinear latent models identifiable under explicit assumptions.

### SH-31
**Non-identifiability is not universal hopelessness; added structure can restrict equivalence classes.**

### SH-32
Any latent-factor/spatial claim must name identifying assumptions and residual ambiguities.

### SH-33
Identifiable-up-to-transform ≠ exact coordinate identity.

### SH-34
Coordinate interpretation must respect permutations/componentwise transformations/other allowed equivalences.

---

# 5. Interpolation is not ontology

Linear latent interpolation:

```text
z(t)=(1-t)z0+t z1
```

is straight only in a chosen parameterization.

### SH-35
**Endpoint decodability ≠ meaningful geometry along the path.**

### SH-36
Decoder behavior in unsupported regions can be weakly constrained by data.

### SH-37
**Straight latent path ≠ target geodesic ≠ causal transition ≠ feasible action trajectory.**

### SH-38
Smooth decoded outputs show decoder continuity/learned regularity, not target-path identity.

Under nonlinear invertible `h`, straight paths can become curved.

### SH-39
**Latent straightness is coordinate-dependent unless backed by invariant geometry.**

### SH-40
Interpolation claims require declared parameterization, equivalence class and target semantics.

### SH-41
A Gaussian or other prior can impose regularity/geometry on latent coordinates.

### SH-42
**Prior-imposed geometry ≠ discovered target geometry automatically.**

---

# 6. Manifold claims are hypotheses

Representation learning often hypothesizes lower-dimensional manifold-like structure in high-dimensional observations.

### SH-43
**Manifold hypothesis ≠ proof that the target is one smooth manifold.**

Data may involve branches, singularities, mixed discrete/continuous factors, stratified structure or noise.

### SH-44
`Ambient dimension ≠ intrinsic dimension ≠ target degrees of freedom`.

### SH-45
Intrinsic dimension estimates can be local/scale/sampling/noise dependent.

### SH-46
One globally constant intrinsic dimension is not guaranteed.

---

# 7. t-SNE / UMAP / PCA: visualization is another representation layer

van der Maaten & Hinton explicitly define t-SNE as assigning high-dimensional data locations in a 2D/3D visualization map.

### SH-47
**t-SNE output is constructed visualization geometry.**

### SH-48
2D t-SNE distance ≠ source-representation distance ≠ target/world distance by identity.

### SH-49
Neighborhood preservation ≠ global metric preservation.

### SH-50
Visual cluster spacing/size is not target ontology without independent evidence.

McInnes, Healy & Melville state dimensionality reduction seeks representations preserving relevant structure, with relevance often application-dependent; UMAP constructs local manifold/neighborhood/fuzzy-topological structure and optimizes a low-dimensional representation.

### SH-51
**Dimensionality reduction preserves a selected structure profile, not `the structure` simpliciter.**

### SH-52
UMAP visualization geometry ≠ source metric geometry by identity.

### SH-53
Hyperparameters and metric choices participate in the resulting neighborhood/layout geometry.

### SH-54
Stability across reasonable settings is evidence, not constitutive truth.

### SH-55
PCA/linear projection preserves selected variance structure; it does not neutrally reveal target axes.

The full pipeline is:

```text
Target entities
 -> learned embedding z
 -> PCA/t-SNE/UMAP v(z)
 -> screen coordinates
```

### SH-56
**Target geometry ≠ latent geometry ≠ visualization geometry ≠ screen geometry.**

### SH-57
Every arrow requires its own preservation/grounding claim.

### SH-58
A visually separable cluster can remain vehicle-level evidence.

### SH-59
**Visual cluster ≠ natural target category.**

---

# 8. Neighborhood and similarity are relation-relative

### SH-60
Nearest neighbor depends on declared metric/similarity.

### SH-61
**Neighborhood is under-specified without relation/metric provenance.**

### SH-62
Similarity ≠ metric distance ≠ spatial nearness.

### SH-63
Abstract similarity can be asymmetric/context-sensitive/nonmetric.

### SH-64
Semantic similarity need not admit one global geometry.

### SH-65
Local representation geometry can have stronger evidence than global geometry.

### SH-66
**Local standing ≠ global metric standing.**

### SH-67
Topological/neighborhood structure can survive metric warping.

### SH-68
**Latent topological standing can be stronger than latent metric standing.**

---

# 9. Probability/function/state `spaces` do not transfer spatiality by name

### SH-69
**Probability space ≠ physical/perceptual spatial domain.**

### SH-70
Distribution divergences can have formal/inferential standing without physical nearness.

### SH-71
KL-like discrepancy can be asymmetric/nonmetric; information geometry ≠ world geometry by default.

### SH-72
Function-space distance ≠ distance between physical objects described by functions.

### SH-73
State-space terminology alone ≠ spatial standing.

### SH-74
MF5-F state/configuration spaces gain action-spatial standing only when grounded transitions/configurations/reachability are spatially organized.

---

# 10. Tensor and neural feature-map axes need grounding

For `X[n,c,h,w]`, batch/channel/height/width axes do not share one ontology.

### SH-75
**Tensor axis ≠ spatial axis by default.**

### SH-76
Spatial index standing is inherited through input/data semantics and system operations.

Convolutional feature positions can preserve receptive-field/input positional correspondences.

### SH-77
**Feature-map topography can have computational/representational spatial standing when positional relations are systematically preserved/recruited.**

### SH-78
Channel index does not thereby become an extra physical coordinate.

### SH-79
**Neural/feature-map neighborhood ≠ target-world neighborhood without grounding.**

---

# 11. Decodability is the central false positive

If analyst decoder/probe predicts target variable `y` from `z`, then information correlated with `y` is available under that decoder/dataset.

### SH-80
**Decodability ≠ explicit representation ≠ spatial standing.**

### SH-81
A nonlinear/linear probe can exploit distributed correlations without the system recruiting a corresponding geometry.

### SH-82
Linear decodability ≠ one semantic/spatial axis.

### SH-83
Axis claims require stronger intervention/transformation/equivalence evidence.

This directly extends frozen MF3:

```text
AnalystDecodability ≠ Representation
```

---

# 12. Coordinate identity is weaker than invariant relational structure

Orthogonal transformations can preserve Euclidean pairwise distances while changing axes.

### SH-84
**Axis semantics can be non-identifiable even when metric geometry is invariant.**

### SH-85
Distance-level standing is weaker than coordinate-axis standing.

General nonlinear invertible transforms can preserve information/reconstruction while changing geometry.

### SH-86
**Information equivalence ≠ geometric equivalence.**

### SH-87
Geometry claims require a privileged equivalence class narrower than arbitrary information-preserving transforms.

### SH-88
A meaningful object may be an equivalence/quotient class rather than one coordinate representative.

### SH-89
Subspace standing can exceed axis standing when basis rotations preserve the encoded relation.

### SH-90
**Subspace relation ≠ privileged coordinate axis.**

---

# 13. System recruitment upgrades standing

If downstream operations explicitly use nearest-neighbor, distances, directions, interpolation or transition relations, and geometry-breaking changes alter system behavior, the geometry matters to the system.

### SH-91
**Counterfactual system sensitivity to geometry is strong evidence for computational standing.**

### SH-92
System-recruited geometry still does not prove target-intrinsic geometry.

### SH-93
It can be a deliberately engineered consumer interface.

### SH-94
Cross-task stability strengthens evidence for broader standing but is not proof.

### SH-95
Cross-representation convergence under a declared equivalence is stronger evidence than one embedding's appearance.

### SH-96
Interventional direction evidence is stronger than passive probe decodability for factor/axis claims.

### SH-97
Transition-preserving latent geometry can acquire action-spatial standing when distances/paths predict real executable/low-cost transitions.

### SH-98
That establishes action/model geometry first, not physical metric identity.

### SH-99
Causal structure ≠ spatial structure.

### SH-100
Disentangled/factorized representation ≠ spatial representation.

---

# 14. Standing levels: the core MF5-H reconstruction

MF5-H distinguishes five roles:

```text
L0  nominal/metaphorical `space` language
L1  formal structured domain
L2  computationally recruited geometry
L3  grounded representational geometry for target relations
L4  target-domain spatial standing
```

### SH-101
These are not quality ranks; they are different ontological/evidential roles.

### SH-102
A domain can legitimately remain L1/L2 without being deficient.

### SH-103 — L1 Formal Standing
Coordinates/topology/metric/algebra are explicitly defined by formal construction.

### SH-104
Formal standing says nothing by itself about another target world's spatiality.

### SH-105 — L2 Computational Standing
System processes operationally recruit geometry for retrieval, transition, optimization, neighborhood, interpolation or control.

### SH-106
**Computational standing requires system recruitment, not analyst post-hoc plotting alone.**

### SH-107 — L3 Representational Target Standing
Under MF3, representation geometry stands for selected target relations through a grounded key and validated relation-specific fidelity.

### SH-108
Representational target standing can encode semantic/action relations without asserting physical spatiality.

### SH-109 — L4 Target Spatial Standing
The target domain itself satisfies MF5 standing through physical, perceptual, action, designed/formal or hybrid routes.

### SH-110
**L4 cannot be inferred solely from L1/L2/L3. Independent target evidence is required.**

### SH-111
For pure mathematics the formal construction itself can be the target domain; formal spatial standing may therefore be terminal rather than representational.

### SH-112
The anti-inflation rule concerns unjustified transfer between domains, not denial of mathematical structure.

---

# 15. Computational spaces can be genuine without being physical

A designed computational system can explicitly establish abstract loci, neighborhoods, paths and transition rules.

### SH-113
**Computational spatial standing can be genuine even when no coordinate corresponds to physical space.**

### SH-114
Material embodiment is not required; non-arbitrary formal/systemic recruitment is sufficient for L1/L2 standing.

### SH-115
An arbitrary analyst embedding does not meet this threshold merely by existing.

### SH-116
**Embedding existence ≠ computational spatial standing unless its relations are operationally or representationally recruited/grounded.**

---

# 16. Semantic regions and contextuality

A classifier or embedding can define regions/clusters.

### SH-117
**Decision region ≠ target semantic region by default.**

### SH-118
Decision regions can nonetheless have strong computational standing for the classifier.

### SH-119
A static word type need not correspond to one universal semantic locus; polysemy/context can alter represented state.

### SH-120
**Semantic location is representation/context relative.**

### SH-121
Embedding cluster ≠ natural category boundary.

### SH-122
MF5-D region standing/vagueness discipline applies to abstract spaces: region boundaries require grounding, not merely separability.

### SH-123
High latent/data density ≠ semantic naturalness ≠ physical occupancy.

### SH-124
Probability/density and region standing remain separate.

---

# 17. Uncertainty, drift and provenance

### SH-125
Embedding remoteness ≠ universal OOD/unfamiliarity; it depends on representation and metric.

### SH-126
Latent covariance/posterior uncertainty ≠ intrinsic target spatial uncertainty.

### SH-127
Retraining may rotate/warp embeddings while target semantics/task behavior remains similar.

### SH-128
**Latent coordinate drift ≠ target drift by default.**

### SH-129
Conversely stable coordinates can coexist with changing target distributions.

### SH-130
**Coordinate stability ≠ target stability.**

### SH-131
Training corpus, seed, architecture, objective and checkpoint/version are part of geometry provenance.

### SH-132
Stable relational invariants have stronger standing than exact numerical latent coordinates when training realizations vary.

---

# 18. Representation geometry is often an interface

Contrastive/metric objectives deliberately shape representations so downstream consumers can use simple operations.

### SH-133
**Representation geometry can be a consumer interface rather than a discovered world map.**

### SH-134
This can be excellent engineering while remaining task-constructed ontology.

### SH-135
Geometric usefulness ≠ geometric isomorphism to target.

### SH-136
`Latent fidelity` is under-specified without specifying preserved neighborhood/rank/topology/angle/transition/factor/intervention structure.

### SH-137
Post-hoc names such as `style axis` or `formality direction` are hypotheses, not self-grounding axis semantics.

### SH-138
**Axis naming ≠ axis standing.**

### SH-139
Representation geometry can be consumer-relative when different downstream consumers recruit different relations over the same code.

### SH-140
There need not be one universal geometry of a representation independent of use.

---

# 19. Provisional schemas

## ComputationalSpatialProfile

```text
ComputationalSpatialProfile = <
  Domain/Representation,
  FormalStructure : vector/topology/metric/graph/manifold/etc.,
  Coordinates/Parameterization,
  Equivalence/GaugeClass,
  SystemConsumers,
  RecruitedRelations : neighbor/distance/direction/path/etc.,
  Objective/TrainingOrigin,
  Transition/InterventionStructure?,
  IdentifiabilityProfile,
  Target/RepresentationKey?,
  Preserved/InferredRelations,
  StabilityAcrossReparameterization/Training?,
  Uncertainty,
  Provenance,
  StandingLevel L0-L4,
  Scope
>
```

### SH-141
Computational geometry must declare formal structure plus use/grounding route.

## LatentGeometryClaim

```text
LatentGeometryClaim = <
  Model/Layer,
  LatentDomain,
  Parameterization,
  Metric/Topology/Similarity,
  LearningObjective/Prior,
  EquivalenceClass,
  IdentifiabilityAssumptions,
  ConsumerUse,
  TargetRelationClaim?,
  Evidence : passive/probe/intervention/transition/cross-model,
  Uncertainty/Stability,
  Provenance,
  Scope
>
```

### SH-142
Bare `latent space has structure` is under-specified.

## EmbeddingRelationClaim

```text
EmbeddingRelationClaim = <
  EntityA,
  EntityB,
  EmbeddingModel,
  Relation : distance/similarity/neighborhood/direction,
  Metric/Normalization,
  TrainingData/Objectives,
  TargetInterpretation?,
  ValidationTasks,
  Stability,
  Provenance,
  Scope
>
```

### SH-143
Bare `A is close to B in embedding space` must not silently mean semantic/world nearness.

---

# 20. Final AbstractSpatialStanding criterion

MF5-H proposes:

> **A computational/abstract domain has spatial standing at its own level when loci/configurations/neighborhoods/relations are explicitly defined and non-arbitrarily recruited by formal/system processes. Transfer to a represented target requires MF3 grounding plus relation-specific fidelity. Transfer to target/world spatial ontology requires independent MF5 target-standing evidence.**

Compact:

```text
Formal Structure
 + Operational Recruitment
   => Computational Spatial Standing

Computational Spatial Standing
 + Grounded Key + Fidelity
   => Representational Spatial Standing

Representational Spatial Standing
 + Independent Target Evidence
   => Target Spatial Standing
```

### SH-144
**No implication is reversible by default.**

A useful evidence ladder is:

```text
named `space`
 < coordinates available
 < metric/topology defined
 < stable computational recruitment
 < cross-task/interventional structure
 < grounded target-relation representation
 < independent target spatial standing
```

### SH-145
Every upward step requires additional evidence; vocabulary does no evidential work.

---

# 21. Failure taxonomy

- **Space-name inflation:** technical `space` terminology treated as target ontology.
- **Coordinate inflation:** tuple encoding treated as standing loci.
- **Metric-existence inflation:** chosen metric treated as intrinsic distance.
- **Embedding-target collapse:** embedding geometry transferred directly to semantic/world geometry.
- **Visualization-latent collapse:** t-SNE/UMAP/PCA layout treated as source latent geometry.
- **Latent-world collapse:** latent coordinates treated as true factors.
- **Decodability inflation:** probe success treated as explicit/system-recruited geometry.
- **Axis reification:** basis coordinate treated as true factor despite transform ambiguity.
- **Disentanglement reification:** clean factors treated as identified truth without assumptions.
- **Interpolation reification:** straight latent path treated as causal/physical/action trajectory.
- **Manifold reification:** manifold model treated as exact target ontology.
- **Cluster reification:** visual/model cluster treated as natural category.
- **Learned-metric naturalization:** task metric treated as intrinsic target metric.
- **System/world collapse:** computational standing treated as world-intrinsic standing.
- **Consumer collapse:** one downstream geometry generalized to every consumer/task.
- **Probability/spatial collapse:** statistical discrepancy/density treated as physical/semantic distance.
- **Grid-axis collapse:** every tensor dimension treated spatially.
- **Topography transfer error:** feature/neural topology treated as target topology.
- **Drift reification:** embedding drift interpreted as target drift without alignment.

### SH-146
**Latent/computational spatial failure is a typed family, not one embedding-quality score.**

---

# 22. Strongest non-collapse stack

```text
Mathematical Space
 ≠ MF5 Target Spatial Domain
```

```text
Vector Structure
 ≠ Metric Geometry
 ≠ Target Geometry
```

```text
Feature Space
 ≠ Embedding Space
 ≠ Latent Space
 ≠ Visualization Space
 ≠ Target Semantic/World Space
```

```text
Embedding Distance
 ≠ Target Distance
 ≠ Semantic Similarity
 ≠ Action Cost
```

```text
Target Geometry
 ≠ Latent Geometry
 ≠ Visualization Geometry
 ≠ Screen Geometry
```

```text
Latent Coordinate
 ≠ Identified Factor
 ≠ Causal Factor
```

```text
Decodability
 ≠ Explicit Representation
 ≠ Spatial Standing
```

```text
Straight Latent Interpolation
 ≠ Geodesic
 ≠ Causal Path
 ≠ Feasible Action Trajectory
```

```text
Learned Metric
 ≠ Intrinsic Target Metric
```

```text
Disentanglement
 ≠ Identifiability
 ≠ Spatiality
```

```text
Computational Spatial Standing
 ≠ Representational Target Standing
 ≠ Target/World Spatial Standing
```

---

# 23. Claims rejected by MF5-H

Reject as universal foundational claims:

- anything called a mathematical `space` is spatial in the target/world sense;
- vector structure supplies one canonical metric;
- representing entities as vectors makes their target domain spatial;
- any definable distance has target standing;
- feature Euclidean distance is meaningful independent of scale/semantics;
- task-learned metric is the target's natural metric;
- word-vector distance is literal semantic distance;
- embedding regularities prove meaning is intrinsically Euclidean/vectorial;
- latent variables are true factors because reconstruction is good;
- unsupervised clean axes identify true generative factors;
- reconstruction/prediction success identifies latent coordinates;
- straight latent interpolation is a meaningful target trajectory;
- manifold assumptions prove one smooth target manifold;
- ambient dimension equals intrinsic dimension/DoF;
- t-SNE/UMAP/PCA geometry is target/source geometry by identity;
- visualization cluster distance/area has literal target meaning;
- similarity equals metric/spatial distance;
- probe/decodability proves explicit spatial representation;
- linear decodability proves one semantic axis;
- information equivalence implies geometric equivalence;
- one consumer's geometry is universal across uses;
- computationally recruited geometry is world-intrinsic geometry;
- probability/function/state-space nomenclature implies physical/perceptual spatiality;
- all tensor axes are spatial;
- neural/feature topography is target-world topography;
- disentanglement implies spatiality;
- causal structure implies spatial structure;
- embedding cluster equals natural category;
- coordinate drift equals target drift;
- coordinate stability equals target stability;
- arbitrary embedding existence establishes computational/target spatial standing.

---

# 24. Primary/authoritative anchors

- **Tomas Mikolov, Kai Chen, Greg Corrado & Jeffrey Dean (2013)**, `Efficient Estimation of Word Representations in Vector Space`, arXiv:1301.3781 — continuous word vectors validated on semantic/syntactic similarity; evidence for useful representation geometry, not intrinsic semantic spatial ontology.
- **Jeffrey Pennington, Richard Socher & Christopher Manning (2014)**, `GloVe: Global Vectors for Word Representation`, EMNLP — corpus-statistical semantic/syntactic vector representation.
- **Kilian Weinberger, John Blitzer & Lawrence Saul (2005)**, `Distance Metric Learning for Large Margin Nearest Neighbor Classification`, NeurIPS — explicit task-induced Mahalanobis geometry.
- **Laurens van der Maaten & Geoffrey Hinton (2008)**, `Visualizing Data using t-SNE`, JMLR — explicitly constructs a low-dimensional visualization map from high-dimensional data.
- **Leland McInnes, John Healy & James Melville (2018)**, `UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction`, arXiv:1802.03426 — low-dimensional representation preserving selected/application-relevant manifold/neighborhood/topological structure.
- **Yoshua Bengio, Aaron Courville & Pascal Vincent (2013/2014)**, `Representation Learning: A Review and New Perspectives`, TPAMI/arXiv:1206.5538 — representation/manifold/factor geometry as learning hypotheses/objectives.
- **Francesco Locatello et al. (2019)**, `Challenging Common Assumptions in the Unsupervised Learning of Disentangled Representations`, ICML/PMLR — unsupervised disentanglement non-identifiability without inductive biases in the general formulation studied.
- **Aapo Hyvärinen, Hiroaki Sasaki & Richard Turner (2019)**, `Nonlinear ICA Using Auxiliary Variables and Generalized Contrastive Learning`, AISTATS/PMLR — auxiliary/temporal structure can establish nonlinear latent identifiability under explicit conditions.
- **Ilyes Khemakhem, Diederik Kingma, Ricardo Monti & Aapo Hyvärinen (2020)**, `Variational Autoencoders and Nonlinear ICA: A Unifying Framework`, AISTATS/PMLR — identifiability of broad deep latent-variable families under conditional auxiliary assumptions, up to defined transformations.

---

# 25. Deep reconstruction

Naive AI-era model:

```text
Data
  ↓ train network
Latent Space R^d
  ↓ UMAP/t-SNE
Clusters / axes / distances
  ↓
True semantic/world geometry
```

MF5-H replaces it with:

```text
Target / data-generating domain
        │
        ▼
observations / sampling
        │
        ▼
learned representation z
 ├─ parameterization
 ├─ objective / prior / training history
 ├─ formal geometry
 ├─ identifiability/equivalence class
 └─ consumer-recruited relations
        │
        ├── operational recruitment
        │       ↓
        │  Computational Spatial Standing
        │
        ├── MF3 grounded key + fidelity
        │       ↓
        │  Representational Target Standing
        │
        └── independent target evidence
                ↓
            Target Spatial Standing

Separately:

z -> PCA/t-SNE/UMAP -> visualization geometry -> screen/perception
```

The decisive result:

> **Formal geometry, computationally recruited geometry, represented-target geometry and target/world spatial standing are different layers. Coordinates and metrics are cheap; standing requires operational recruitment, grounding, identifiability/equivalence discipline and claim-matched target evidence.**

---

# 26. Deepest MF5-H result

> **A computational/latent domain may possess genuine formal or system-relative spatial standing when neighborhood, metric, topology, interpolation or transition relations are explicitly defined and operationally recruited. This standing does not automatically transfer to the represented target. Transfer requires MF3 grounding and relation-specific fidelity; target/world spatial standing requires independent MF5 evidence. Learned coordinates are additionally constrained by identifiability and reparameterization equivalence, making invariant relation structure generally ontologically stronger than raw axes or coordinates.**

Compact:

```text
Coordinates are cheap.
Metrics are selectable.
Embeddings are representations.
Geometry becomes system-standing through recruitment.
Target geometry requires grounding.
Target spatiality requires independent standing.
```

---

# 27. MF5-A→H reconstructed picture

```text
MF5-A Space ontology
 = standing spatial possibility domains

MF5-B Geometry
 = typed topology/metric/invariance/equivalence structures

MF5-C Description
 = frames/charts/coordinates/transforms

MF5-D Regionalization
 = regions/boundaries/occupancy/locality

MF5-E Perceptual/embodied space
 = body/world-relative sensorimotor spatial organization

MF5-F Action space
 = configuration/state + transition/reachability/cost

MF5-G Representational/virtual space
 = vehicle↔target spatial keys + enacted designed spatial worlds

MF5-H Computational/latent space
 = formal/system-recruited geometry with strict transfer and identifiability discipline
```

MF5-H closes the largest inflation loophole: `embedding exists` can no longer bootstrap target spatial ontology.

---

# 28. No FoundationReopenCondition

MF5-H strengthens rather than falsifies frozen layers:

- MF3 `AnalystDecodability ≠ Representation` becomes central to latent-space anti-inflation.
- MF1/MF2 provenance, inverse-problem and uncertainty discipline remain intact.
- MF4 multiple valid decomposition/equivalence profiles remain compatible.
- MF5-A formal/mathematical standing is preserved but sharply separated from transfer to another target.

### SH-147
**MF1–MF4 remain frozen; no concrete FoundationReopenCondition was triggered.**

---

# 29. MF5-I handoff — Space Falsification & Reconstruction

MF5-I must now attack the complete MF5-A→H provisional model rather than add another domain.

Required falsification axes:

1. **Minimality:** can Space remain meaningful without metric, coordinates, observer, occupancy, action or representation?
2. **Over-inclusion:** does the definition classify arbitrary sets/vectors/graphs/embeddings as spatial?
3. **Under-inclusion:** does it exclude projective, graph, virtual, configuration, peripersonal, fuzzy or nonmetric spaces?
4. **Standing:** can SpatialStanding survive arbitrary embedding/metric/naming attacks?
5. **Relations:** are locus/region, topology, incidence, orientation, metric, visibility, reachability properly typed?
6. **Description/state:** do frame/chart/coordinate rules survive AR, manifold and gauge/reparameterization cases?
7. **Perception:** can physical/perceptual/action geometry diverge without multiplying `spaces` vacuously?
8. **Action:** does action-space ontology accidentally absorb all transition systems?
9. **Representation:** does virtual standing robustly distinguish enactment from depiction?
10. **Latent:** can system recruitment establish legitimate computational space without laundering task geometry into target ontology?
11. **Cross-context:** physics, maps, UI, games, robotics, biology, mathematics and ML must fit one typed framework.
12. **Equivalence:** choose the minimal constitutive primitives versus optional profiles.
13. **Uncertainty/provenance:** partial spatial claims must remain possible without ontology collapse.
14. **MF6/MF7 boundary:** ensure time/dynamics have not been silently absorbed.
15. **Freeze decision:** revise/freeze Space Foundations v1 only if no concrete counterexample survives.

Candidate final invariant to falsify:

> **Space is a scope-relative possibility/domain structure in which loci, regions or configurations and at least one genuinely standing family of spatial relations—such as neighborhood, incidence, separation, orientation, connectivity, continuity, metric, containment, reachability or related positional structure—organize distinctions among possible spatial states; coordinates, metrics, observers, occupants, representations and actions are optional enrichments, while standing must be established in the target/formal/system domain rather than supplied only by analyst embedding or terminology.**

**Next: MF5-I — Space Falsification & Reconstruction.**
