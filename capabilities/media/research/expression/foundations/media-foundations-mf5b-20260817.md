# Ordivon Media Foundations — MF5-B Topology, Metric & Geometry

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 24 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen; MF5-A Space Ontology complete and provisional.  
**Status:** MF5-B complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-C — Frames, Coordinates, Charts & Transformations.

---

# 0. Purpose

MF5-A rejected `Space = coordinates` and proposed a spatial domain as a scoped possibility domain of loci/regions/configurations with spatial-standing relation structure.

MF5-B attacks the next tempting collapse:

```text
Topology → Metric → Geometry
```

as though these were merely stronger versions of one scalar idea.

The central questions are:

1. What exactly does topology add?
2. What does uniform structure add beyond topology?
3. What does a metric add beyond topology/uniformity?
4. Why are projective, affine, Euclidean and Riemannian structures not one simple linear ladder?
5. How should graph/action/configuration geometries fit?
6. What invariants define `same geometry`?
7. What makes an analyst-chosen topology/metric/geometry have **target spatial standing**?

The strongest emerging answer is:

> **Spatial structure is a typed bundle of relation/equivalence/invariance structures. Some structures induce weaker ones through forgetful maps, but no single total ordering captures topology, incidence/projective structure, affine structure, metric structure, differential structure and action/reachability geometry.**

---

# 1. A set/domain is not yet a topology

Let `X` be a collection of possible loci/configurations.

`X` alone gives identity/membership only.

It does not determine:

- neighborhood;
- continuity;
- connectedness;
- boundary/interior;
- distance;
- direction;
- straightness;
- angle;
- reachability.

### SB-01

**Underlying domain/set ≠ spatial organization.**

---

# 2. Incidence/adjacency can precede topology

A domain may have primitive relations such as:

```text
Adjacent(x,y)
Incident(point,line)
Between(x,y,z)
ConnectedByEdge(x,y)
```

without first being presented by real-valued coordinates or distances.

### SB-02

**Spatial standing can begin from qualitative/incidence/neighborhood relations rather than a metric.**

### SB-03

**Incidence, adjacency and betweenness are not interchangeable and need not be reducible to one numeric distance.**

---

# 3. Topology captures qualitative neighborhood/continuity structure

A topological structure specifies which subsets behave as open/neighborhood regions and thereby determines notions such as continuity, connectedness, interior, closure and boundary.

Historically, Hausdorff's 1914 *Grundzüge der Mengenlehre* systematized general topological spaces; the exact modern axiomatization evolved, but the foundation-level lesson is structural rather than historical terminology.

### SB-04

**Topology supplies qualitative local/global neighborhood structure without supplying a numerical scale by itself.**

---

# 4. Topology does not determine distance

A topology can distinguish:

- continuous vs discontinuous maps;
- connected vs disconnected sets;
- open/closed neighborhoods;

while remaining silent about exact length, angle or travel cost.

### SB-05

**Topology ≠ metric geometry.**

### SB-06

**Topological equivalence preserves a weaker relation profile than metric/isometric equivalence.**

---

# 5. Homeomorphism is not isometry

Two spaces can have the same topological structure under a continuous bijection with continuous inverse while distances are heavily distorted.

A rubber-sheet deformation is the standard intuitive case: neighborhood/connectedness can survive while lengths/angles change.

### SB-07

`Homeomorphic ≠ Isometric`.

### SB-08

**Same topology does not imply same metric, geodesics, angles, curvature or action cost.**

---

# 6. Metric structure adds quantitative separation

A mathematical metric `d(x,y)` supplies a scalar separation relation satisfying the usual identity, symmetry and triangle constraints.

From `d`, metric balls induce a topology.

### SB-09

**A metric can generate a topology, but the generated topology forgets quantitative distance information.**

### SB-10

`Metric -> Topology` is a forgetful/inducing relation, not an identity.

---

# 7. Same topology can support many metrics

On the same underlying set, multiple metrics can induce the same open-set topology while disagreeing on quantitative separation, boundedness, completeness or geodesic behavior.

Concrete example on `R`:

```text
d1(x,y) = |x-y|
d2(x,y) = |arctan(x)-arctan(y)|
```

Both induce the ordinary topology because `arctan` is a homeomorphism from `R` onto an open interval, but the second metric is bounded and has different Cauchy/completeness behavior.

### SB-11

**Topology underdetermines metric structure.**

### SB-12

**Metric-dependent claims cannot be inferred from topology alone.**

---

# 8. Same topology can support task-different spatial geometries

On `R^2`, Euclidean `L2` and Manhattan `L1` metrics generate the same standard topology, yet their balls, shortest paths and distance values differ.

### SB-13

**Topological sameness does not imply the same navigation/action geometry.**

### SB-14

**Which compatible metric is spatially relevant depends on standing: physical length, street/grid constraint, control cost, perceptual discrimination, representation convention, etc.**

---

# 9. Uniformity exposes a missing layer between topology and metric

Topology tells whether points can be locally separated/approached and which maps are continuous, but it does not by itself provide a global notion of `equally close` across different locations.

André Weil's 1937 uniform-space program explicitly generalized metric-space structure through entourages/neighborhood comparison without requiring a real-valued distance function.

### SB-15

**Uniform structure ≠ topology and ≠ metric.**

### SB-16

A uniformity can support notions such as uniform continuity and Cauchy/completeness behavior even when no particular scalar distance is selected.

---

# 10. Metric induces uniformity; uniformity induces topology

For a metric space, entourages of the form `d(x,y)<ε` generate a uniform structure, and that uniform structure induces the usual topology.

```text
Metric
  -> Uniformity
  -> Topology
```

But the reverse arrows are not unique in general.

### SB-17

**The topology forgets part of the uniform/metric structure.**

### SB-18

**The minimal spatial ontology must not assume that every meaningful notion of closeness/completion comes from one canonical distance scalar.**

---

# 11. Pseudometric and quotient structure

A pseudometric may assign distance zero to distinct states/loci.

This can be meaningful when the consumer/task regards several realizations as equivalent.

### SB-19

**Zero task/spatial separation need not imply token identity unless the chosen structure requires identity of indiscernibles.**

### SB-20

A quotient by the zero-distance equivalence classes can yield a metric domain, illustrating that unit individuation and metric structure can be mutually adjusted.

---

# 12. Asymmetric costs are not metrics

One-way roads, uphill/downhill energy, irreversible control dynamics or wind/current can yield:

```text
Cost(x,y) != Cost(y,x)
```

or even one-way reachability.

### SB-21

**Action cost/reachability geometry can be spatially meaningful without being a symmetric metric.**

### SB-22

`Distance ≠ DirectedCost ≠ Reachability`.

This keeps action geometry broader than metric-space geometry.

---

# 13. Graphs demonstrate topology/metric/action separation cleanly

A graph can begin with only vertices and edges. Edges establish adjacency/connectivity standing.

If positive edge lengths are added, shortest-path length can define a metric on a connected undirected graph; Dijkstra's 1959 paper is a canonical constructive case for minimum path length in positively weighted graphs.

### SB-23

**Graph adjacency is not itself metric distance.**

### SB-24

**Graph distance is derived from edge/path structure plus weights.**

### SB-25

Directed graphs can support reachability and directed path cost without satisfying metric symmetry.

---

# 14. `Graph geometry` is not canonical without edge semantics

An analyst can connect arbitrary nodes and assign arbitrary weights.

### SB-26

**The existence of graph-theoretic distance does not establish target spatial standing.**

Target-level claims require the edges/weights to be grounded in actual adjacency, interaction, travel, similarity, design or another declared spatial relation.

This is the MF5 analogue of MF4's `analyst-created edge ≠ composition standing`.

---

# 15. Incidence/projective structure forms another axis

Projective geometry is not simply `topology + a weaker metric`.

Its core relations concern points, lines/planes, incidence, collinearity and projective transformations; metric properties such as Euclidean distance/angle are not generally invariant under projective transformations.

Klein's Erlangen program explicitly framed projective and other geometries through different transformation groups and their invariants.

### SB-27

**Projective structure and metric/topological structure are conceptually orthogonal axes; a pure incidence/projective geometry need not begin from a metric topology.**

---

# 16. Projective equivalence preserves less Euclidean structure

Under projective transformations:

- incidence/collinearity remain meaningful;
- general parallelism need not be preserved;
- Euclidean length and angle need not be preserved.

### SB-28

`ProjectiveEquivalence ≠ AffineEquivalence ≠ EuclideanIsometry`.

### SB-29

**A spatial representation can be projectively valid while metrically indeterminate.**

---

# 17. Camera geometry is a hard projective falsifier

Uncalibrated multi-view reconstruction provides an engineering case where image constraints can determine scene/camera structure only up to projective equivalence under the stated assumptions. Hartley & Schaffalitzky's projective reconstruction work generalizes reconstruction from projections and explicitly characterizes uniqueness up to projectivity in the relevant generic settings.

### SB-30

**Image/projective evidence can establish incidence/projective spatial structure without establishing Euclidean metric structure.**

### SB-31

**Recovering more metric geometry requires additional calibration/constraints; projective structure is not failed Euclidean geometry but a different information level.**

---

# 18. Affine structure adds a distinguished class of relations

Affine geometry supports meaningful straight lines, affine combinations, parallelism and ratios along collinear lines without selecting a Euclidean origin-dependent position vector or a length/angle measure.

### SB-32

**Affine structure ≠ Euclidean metric structure.**

### SB-33

A coordinate origin is a representational convenience in an affine space; displacements/affine combinations can be meaningful without one privileged global origin.

---

# 19. Projective → affine → Euclidean can be a strengthening chain under selected formalization

One useful formal view is:

```text
Projective structure
 + distinguished hyperplane at infinity
 -> Affine structure
 + inner-product/metric structure
 -> Euclidean structure
```

But this is only one axis of enrichment.

### SB-34

**This chain must not be confused with the independent topological/smooth/uniform axes.**

A projective structure over real coordinates can coexist with topology/smoothness, but pure incidence projective geometry does not derive from topology alone.

---

# 20. Klein supplies an invariance discipline, not the final ontology of geometry

Klein's 1872 program proposes studying properties invariant under a chosen transformation group and notes that enlarging the allowed transformation group leaves fewer properties invariant.

This strongly supports MF5's transformation-relative equivalence discipline.

### SB-35

**`Same geometry` is shorthand for `same under a declared structure-preserving transformation/equivalence family`.**

### SB-36

**More permissive transformation families preserve fewer distinctions.**

However modern Riemannian/differential/local geometry is not exhausted by one global group action.

### SB-37

**`Geometry = invariants of one global transformation group` is retained as a powerful model family, not frozen as universal geometry ontology.**

---

# 21. Euclidean structure adds lengths and angles

A Euclidean structure can be viewed as affine/vector structure plus a positive-definite inner product, from which norm, distance and angle follow.

### SB-38

**Inner product ≠ norm ≠ metric ≠ topology.**

There is a directed implication under suitable structure:

```text
Inner Product -> Norm -> Metric -> Topology
```

but not every norm comes from an inner product, and not every metric comes from a norm/vector structure.

### SB-39

**Each arrow forgets structure; the reverse is non-unique or impossible in general.**

---

# 22. Similarity and isometry preserve different profiles

A uniform scale transformation preserves angles and ratios but not absolute lengths.

Rigid motions/isometries preserve distances.

### SB-40

**Congruence/isometry, similarity, affine equivalence, projective equivalence and topological equivalence are different spatial identity claims.**

---

# 23. Riemann's hard lesson: manifoldness does not force one measure relation

Riemann's 1854 lecture explicitly argues that a multiply extended magnitude can admit different measure-relations and develops measure structure only after the manifold notion.

### SB-41

**Manifold/local positional structure and metric measure structure are separable commitments.**

### SB-42

**Euclidean geometry is not logically forced by dimension or continuity alone.**

---

# 24. Topological manifold, smooth manifold and Riemannian manifold are distinct layers

A useful modern chain is:

```text
Topological manifold
 + differentiable atlas/transition structure
 -> Smooth manifold
 + smoothly varying positive-definite inner product on tangent spaces
 -> Riemannian manifold
```

### SB-43

**Local Euclidean topology ≠ smooth structure ≠ Riemannian geometry.**

### SB-44

A smooth manifold can support many different Riemannian metrics.

Thus the underlying manifold again underdetermines quantitative geometry.

---

# 25. `Riemannian metric` is not the same primitive as a metric-space distance

A Riemannian metric is a smoothly varying inner product tensor on tangent spaces. It can be integrated along curves to define length and geodesic distance.

### SB-45

**Riemannian metric tensor ≠ metric-space distance function, although the former can induce the latter under standard conditions.**

This terminology collision is important for MF5.

---

# 26. Curvature is additional geometric structure, not topology

Two surfaces can share topology while carrying different metric tensors/curvatures.

### SB-46

**Curvature cannot be inferred from topological equivalence alone.**

### SB-47

**Topology classifies a weaker organization profile than Riemannian metric geometry.**

---

# 27. Sphere hard case: coordinates are not geometry

A sphere can be covered by local charts, but one ordinary longitude/latitude chart has coordinate singularities even though the sphere itself is geometrically regular there.

### SB-48

**Coordinate singularity ≠ spatial/geometric singularity.**

### SB-49

**Global geometric identity can require an atlas of local coordinate descriptions rather than one global chart.**

This prepares MF5-C.

---

# 28. Sphere hard case: intrinsic vs extrinsic distance

For points on a sphere, one may compare:

- Euclidean chord distance through the ambient `R^3`;
- geodesic distance along the sphere.

They can induce the same local/topological organization while expressing different geometry/operational meaning.

### SB-50

**Intrinsic geometry ≠ embedding/ambient geometry.**

### SB-51

**Embedding a spatial domain into a higher-dimensional space does not make the ambient metric the target's intrinsic metric by default.**

---

# 29. Subway/topological maps show selective spatial fidelity

A transit map may preserve station identity, adjacency/connectivity and route order while deliberately distorting physical distance, angle and scale.

### SB-52

**Topological/relational spatial fidelity can be high while metric fidelity is low.**

### SB-53

**`Distorted geometry` is underspecified: which geometry/relations were intended to be preserved?**

This is a direct application of MF3 keyed representation.

---

# 30. Metric truth is scope/consumer typed

For the same city:

- straight-line physical distance;
- walking path distance;
- travel time;
- monetary cost;
- accessibility cost;

can all order candidate destinations differently.

### SB-54

**No universal `true distance` exists across physical, navigation, control and utility scopes.**

This does not make distance arbitrary: each relation requires its own standing/measurement/action grounding.

---

# 31. Shortest-path distance can be derived without Euclidean embedding

Dijkstra's graph problem starts from vertices and positive edge lengths and seeks minimal path length; no planar/Euclidean embedding is needed for the optimization problem itself.

### SB-55

**Metric/path geometry can arise from relational network structure without ambient physical Euclidean coordinates.**

---

# 32. Configuration space strengthens the same lesson

Lozano-Pérez's configuration-space approach maps whole-object position/orientation degrees of freedom into a derived configuration domain where obstacles become forbidden regions.

### SB-56

**Geometric operations over a derived space can be operationally real for planning even when its points are whole configurations rather than physical locations.**

### SB-57

The relevant geometry can be shaped by kinematic constraints, collision sets and control costs rather than raw physical distance alone.

---

# 33. Geometry is not universally one metric

A spatial domain may simultaneously support:

- topology/neighborhood;
- incidence/projective structure;
- affine relations;
- one or more metrics;
- differential structure;
- orientation;
- measure/volume;
- visibility;
- action/reachability/cost structure.

### SB-58

**`Geometry` should be treated as a typed structure profile, not one scalar distance matrix.**

---

# 34. The structure picture is a partial order / bundle, not one ladder

Useful inducing/forgetful chains include:

```text
Metric -> Uniformity -> Topology
```

```text
Inner Product -> Norm -> Metric -> Topology
```

```text
Riemannian -> Smooth Manifold -> Topological Manifold
```

and, under a selected projective formalization:

```text
Euclidean -> Affine -> Projective
```

where arrows mean `forget some structure`, not `become less spatial`.

But these chains are not one universal total order.

### SB-59

**Topology, projective/incidence, affine, differential and metric structures occupy partially independent axes.**

---

# 35. Spatial Structure Lattice candidate

MF5-B proposes the following non-total organization:

```text
                         Spatial Domain X
                                │
          ┌─────────────────────┼─────────────────────────┐
          │                     │                         │
   Incidence/Order         Neighborhood/Topology     Action/Reachability
          │                     │                         │
     Projective             Uniformity                 Cost/Policy
          │                     │                         │
       Affine                Metric                     Quasi-metric /
          │                     │                       directed graph
          │              ┌──────┴──────┐
          │              │             │
          └────────── Euclidean     Geodesic/other
                         │
                  Smooth/Riemannian
             (when differential structure is present)
```

This diagram is explanatory, not a complete category-theoretic lattice.

### SB-60

**Different spatial structures can coexist on one domain and induce different equivalence classes.**

---

# 36. Spatial equivalence profile

MF5-B now distinguishes at least:

```text
Topological equivalence      : homeomorphism / topology-preserving
Uniform equivalence          : uniform-structure preserving
Metric equivalence           : isometry
Similarity equivalence       : metric up to common scale / angle-ratio profile
Affine equivalence           : affine structure/parallelism/barycentric relations
Projective equivalence       : incidence/projective invariants
Smooth equivalence           : diffeomorphism
Riemannian equivalence       : metric-tensor/isometry profile
Graph equivalence            : graph/isomorphism/weighted-path profile
Action equivalence           : reachability/cost/policy-relevant profile
```

### SB-61

**`Same space` is underspecified unless the preserved structure/equivalence family is named.**

---

# 37. Transformation family and structure jointly define what matters

Klein's key methodological insight survives in generalized form:

> To say which geometric properties count, specify which transformations are admissible and which relations/invariants must survive.

MF5 generalizes `group` to a broader **admissible transformation/equivalence family**, because local charts, diffeomorphisms, partial maps, constrained controls and representation projections need not form one simple global group in every application.

### SB-62

**Spatial identity = declared structure + admissible transformation/equivalence profile, not coordinate equality.**

---

# 38. Stronger invariance is not automatically better

If we permit a larger transformation family, fewer distinctions survive.

Projective invariance can intentionally ignore Euclidean length/angle; topological invariance ignores even more metric shape.

### SB-63

**More invariance can erase task-relevant spatial distinctions.**

### SB-64

**Spatial abstraction trades specificity for transformation robustness.**

This mirrors MF2 invariance and MF3 representation geometry.

---

# 39. Fine geometry is not always better either

Exact metric detail can be unnecessary or actively harmful for:

- transit navigation;
- symbolic diagrams;
- topology-based planning;
- responsive layout;
- coarse spatial reasoning.

### SB-65

**The appropriate spatial structure is query/task/consumer relative, not maximally detailed by default.**

---

# 40. But task-relativity is not analyst arbitrariness

A metric/topology/geometry needs standing in the target/practice/system.

MF5-B sharpens MF5-A `SpatialStanding` into:

```text
SpatialStructureStanding(S, X | Σ)
```

where `S` may be topological, metric, affine, projective, Riemannian, graph/action, etc.

### SB-66

**The mere mathematical definability of `S` on `X` does not establish target spatial standing.**

---

# 41. Metric-existence inflation is especially dangerous

Any finite set can be given the discrete metric:

```text
d(x,x)=0
d(x,y)=1 for x != y
```

This proves that `a metric exists` is almost content-free as a target-domain claim.

### SB-67

**Existence of an analyst-defined metric is not evidence that the target possesses that geometry.**

---

# 42. Embedding inflation is the same error in another form

An analyst can embed items in `R^n`, choose a distance and draw neighborhoods.

### SB-68

**Embedding geometry has standing first as a formal/representational geometry. Transfer to target geometry requires MF3 grounding plus MF5 spatial-structure evidence.**

This directly constrains `semantic space`, `social space`, `feature space` and `latent space` claims.

---

# 43. Target geometry evidence must be relation-typed

Possible evidence routes include:

## Physical/measurement

Distances, angles, trajectories, local neighborhood/continuity measurements.

## Transformation invariance

Predicted relations survive the transformations claimed irrelevant.

## Intervention/action

Reachability/cost/trajectory changes follow the proposed spatial relation structure.

## Calibration/projection

Known camera/sensor transformations support projective/metric reconstruction claims.

## Design/specification

A virtual/layout/protocol domain explicitly defines its geometry.

## Perception/behavior

Discrimination, navigation or grouping systematically follows the candidate spatial structure.

## Formal construction

The structure has exact standing in a mathematical object itself.

### SB-69

**Evidence route must match the asserted geometry type.**

---

# 44. Evidence for topology is not evidence for metric

Observing stable connectivity or continuity does not determine exact distance.

### SB-70

**Do not promote topological evidence into metric geometry without additional constraints.**

Likewise projective calibration does not automatically establish Euclidean metric calibration.

---

# 45. Evidence for a metric is not evidence for unique geometry

A measured or operational metric can coexist with other task-valid metrics on the same domain.

### SB-71

**Spatial standing is relation/profile specific; one valid geometry does not invalidate all alternative grounded geometries.**

This is the MF5 counterpart of MF4's multiple valid decompositions.

---

# 46. Non-uniqueness ≠ arbitrariness

Two structures may both be objectively grounded:

- Euclidean physical distance;
- street-network travel distance.

They answer different spatial questions.

### SB-72

**Plural grounded geometries are admissible when their standing routes/scopes differ explicitly.**

---

# 47. Geometry can be local

Riemannian geometry and manifold charts show that a spatial domain can have well-defined local geometry without one global Euclidean coordinate system.

### SB-73

**Local spatial structure does not require global flattenability.**

### SB-74

**Local charts/metrics and global topology must remain separate levels of description.**

---

# 48. Local Euclidean appearance does not imply global Euclidean topology

A sphere is locally plane-like in sufficiently small neighborhoods but globally closed and topologically distinct from a plane.

### SB-75

**Local geometry/topology does not uniquely determine global spatial organization.**

---

# 49. Global topology can constrain possible coordinates/geometries

A space's global topology can prevent one smooth global chart of a simple coordinate type or constrain fields/structures definable globally.

### SB-76

**Topology is not merely a low-resolution metric; it can impose qualitatively different global constraints.**

---

# 50. Topological error and metric error remain distinct

A small bridge/gap change can alter connectivity while having tiny coordinate magnitude; a large smooth deformation can preserve topology while strongly changing distances.

### SB-77

**Error magnitude in coordinates is not a reliable proxy for topological correctness.**

This carries forward MF4-F's spatial failure discipline.

---

# 51. Metric error and action error remain distinct

A physically accurate distance map can still be useless for a robot/person if obstacles, directionality or control constraints dominate travel.

### SB-78

**Metric fidelity ≠ reachability/control fidelity.**

---

# 52. Spatial representation should name preserved structure

Instead of saying:

> `This map accurately represents the space.`

prefer:

- preserves station adjacency/order;
- approximates travel distance;
- preserves angle locally;
- preserves projective incidence;
- preserves collision-free reachability;
- preserves topology but not scale.

### SB-79

**Spatial fidelity is a typed preserved-structure claim.**

---

# 53. Geometry can itself be represented

A map, coordinate chart, graph or mesh is a representation under MF3.

The represented target geometry and the vehicle/display geometry can differ.

### SB-80

`Vehicle Geometry ≠ Represented Geometry`.

This is crucial for diagrams, maps, UI and simulations.

---

# 54. Geometry can also be computationally enacted

A game/virtual world or planning system can define adjacency, collision, metric/cost, portals, topology and reachability in code.

### SB-81

**Designed computational rules can establish genuine formal/operational spatial structure even when display geometry is only one realization.**

This remains a later MF5 specialization, not a reason to collapse simulation/runtime with Space ontology.

---

# 55. `Geometry` provisional ontology

MF5-B proposes:

> **A geometry is a typed enrichment of a domain's spatial-standing relation structure that determines additional spatial distinctions/equivalences—such as incidence, collinearity, parallelism, distance, angle, smoothness, curvature, geodesic/reachability or other relation families—together with a declared class of admissible transformations under which selected properties are preserved.**

This is deliberately broader than metric geometry and deliberately weaker than `geometry = one transformation group`.

Compact:

```text
GeometryProfile
 = Spatial Domain
 + Added Typed Structure
 + Admissible Transformations/Equivalences
 + Preserved Invariants
 + Standing
 + Scope
```

---

# 56. Provisional TopologyProfile

```text
TopologyProfile = <
  Domain,
  Open/Neighborhood Structure,
  Connectedness/Components,
  Interior/Closure/Boundary,
  Continuity Class,
  Separation/Identifiability assumptions,
  Standing,
  Scope
>
```

---

# 57. Provisional MetricProfile

```text
MetricProfile = <
  Domain,
  Distance Function,
  Metric/Pseudometric/Quasi-metric Type,
  Induced Topology/Uniformity,
  Geodesic/Path Structure,
  Scale/Units,
  Symmetry/Directionality,
  Completeness/Boundedness where relevant,
  Standing,
  Evidence,
  Scope
>
```

---

# 58. Provisional GeometryProfile

```text
GeometryProfile = <
  Domain,
  Base Topological/Incidence Structure?,
  Added Structure : projective/affine/metric/differential/Riemannian/graph/action/etc.,
  Transformation/Equivalence Family,
  Preserved Invariants,
  LocalVsGlobal Structure,
  IntrinsicVsExtrinsic Status,
  Coordinates/Charts as optional representation,
  Standing Route,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

Question marks are intentional: not every formal geometry requires the same prerequisites.

---

# 59. Final provisional structure map after MF5-B

```text
                         DOMAIN / LOCI
                              │
           ┌──────────────────┼───────────────────┐
           │                  │                   │
     Incidence/order     Neighborhood         Action/reachability
           │                  │                   │
      Projective          Topology             Directed cost
           │                  │                   │
        Affine            Uniformity           Control geometry
           │                  │
           │               Metric
           │                  │
           └──────┬───────────┘
                  │
             Euclidean-like
                  │
       Smooth / Riemannian enrichment
```

This is not a total lattice and does not imply every domain follows every arrow.

---

# 60. Strongest non-collapse stack

```text
Set/Domain
 ≠ Incidence Structure
 ≠ Topology
 ≠ Uniformity
 ≠ Metric
 ≠ Geometry
```

```text
Topology
 ≠ Metric
 ≠ Geodesic Distance
 ≠ Action Cost
```

```text
Metric Space Metric
 ≠ Riemannian Metric Tensor
```

```text
Homeomorphism
 ≠ Uniform Equivalence
 ≠ Isometry
 ≠ Similarity
 ≠ Affine Equivalence
 ≠ Projective Equivalence
```

```text
Projective
 ≠ Affine
 ≠ Euclidean
 ≠ Riemannian
```

```text
Intrinsic Geometry
 ≠ Embedding/Ambient Geometry
```

```text
Graph Adjacency
 ≠ Graph Distance
 ≠ Directed Reachability
```

```text
Formal/Embedding Geometry
 ≠ Target Spatial Geometry
```

```text
Vehicle Geometry
 ≠ Represented Geometry
```

---

# 61. Claims rejected by MF5-B

Reject as universal foundations:

- a set/domain is spatial once coordinates are assigned;
- topology is merely an imprecise metric;
- topology uniquely determines a metric;
- every topology has one canonical metric;
- metric and topology are interchangeable;
- uniformity is unnecessary because every useful closeness notion is a metric;
- every distance-like cost must be symmetric;
- graph adjacency is the same as graph distance;
- any graph metric proves target spatial geometry;
- projective geometry is simply inaccurate Euclidean geometry;
- projective reconstruction automatically recovers Euclidean metric structure;
- affine structure requires absolute origin or metric length;
- Euclidean/projective/affine/topological equivalence are one identity relation;
- geometry is universally reducible to one scalar distance matrix;
- geometry is universally nothing but invariants of one global transformation group;
- local Euclidean charts imply global Euclidean space;
- manifold dimension determines metric geometry;
- smooth structure determines a unique Riemannian metric;
- Riemannian metric tensor is literally the same object as a metric-space distance function;
- same topology implies same curvature/geodesics;
- embedding metric is automatically intrinsic;
- physical distance is always the right navigation/control metric;
- `a metric exists` establishes spatial standing;
- a learned embedding's Euclidean/cosine metric automatically belongs to the target domain;
- one objectively valid geometry excludes all other grounded geometries;
- spatial fidelity can be summarized without naming which structure is preserved.

---

# 62. Primary/original literature anchors

- **Bernhard Riemann (1854; published 1867)**, *Über die Hypothesen, welche der Geometrie zu Grunde liegen*; W. K. Clifford translation, *Nature* 8 (1873), 14–17, 36–37. Separates manifold/region relations from possible measure-relations and rejects Euclidean measure structure as logically forced by dimension/manifoldness.
- **Felix Klein (1872)**, *Vergleichende Betrachtungen über neuere geometrische Forschungen* (Erlangen Program). Frames geometries through transformation groups and invariants; enlarging the transformation group preserves fewer properties.
- **Maurice Fréchet (1906)**, *Sur quelques points du calcul fonctionnel*, Rendiconti del Circolo Matematico di Palermo 22, 1–72, DOI 10.1007/BF03018603. Foundational abstraction of metric-like distance structure beyond ordinary Euclidean domains.
- **Felix Hausdorff (1914)**, *Grundzüge der Mengenlehre*. Foundational general topological-space/neighborhood work.
- **André Weil (1937)**, *Sur les espaces à structure uniforme et sur la topologie générale*, Actualités scientifiques et industrielles 551. Uniform structure generalizes metric-style global closeness/completeness structure without requiring one scalar metric.
- **E. W. Dijkstra (1959)**, *A note on two problems in connexion with graphs*, Numerische Mathematik 1, 269–271, DOI 10.1007/BF01386390. Minimum path length over positively weighted graph edges; hard case for relational path geometry without Euclidean embedding.
- **Tomas Lozano-Pérez (1983)**, *Spatial Planning: A Configuration Space Approach*, IEEE Transactions on Computers 32(2), 108–120, DOI 10.1109/TC.1983.1676196. Whole object position/orientation becomes a point in configuration space; obstacles become forbidden configuration regions.
- **Richard Hartley & Frederik Schaffalitzky (2004)**, *Reconstruction from Projections using Grassmann Tensors*, ECCV. General projective reconstruction and uniqueness up to projectivity under generic conditions; hard case separating projective structure from Euclidean metric reconstruction.

---

# 63. Deep reconstruction

Naive picture:

```text
Coordinates
  ↓
Distances
  ↓
Geometry
  ↓
Space
```

MF5-B replaces it with:

```text
Spatially standing domain/loci
        │
        ├─ incidence/order relations
        ├─ topology/neighborhood/continuity
        ├─ uniform closeness
        ├─ metric/pseudometric/quasi-metric separation
        ├─ projective/affine structure
        ├─ inner-product/Euclidean structure
        ├─ smooth/Riemannian local geometry
        ├─ graph/path/reachability/action structure
        └─ multiple grounded structures may coexist
        │
        ▼
Admissible transformations/equivalences
        │
        ▼
Preserved spatial invariants under declared scope
```

The key shift is:

> **Geometry is not `numbers attached to coordinates`; it is a declared spatial structure plus its invariant/equivalence profile and standing.**

---

# 64. Deepest MF5-B result

The strongest surviving formulation is:

```text
Topology tells which local/global neighborhood-continuity distinctions survive.
Uniformity adds point-independent comparison of closeness/Cauchy structure.
Metric adds quantitative separation.
Projective/Affine structures add different incidence/line/parallelism invariants.
Euclidean/Riemannian structures add stronger length/angle/local metric structure.
Graph/action structures can define their own path/reachability/cost geometry.
None of these is spatially privileged merely because an analyst can define it.
```

Therefore:

> **A target geometry exists, for MF5 purposes, only when the relevant relation/invariance structure has spatial standing in the target system/practice/physics/perception/action/formal construction under scope.**

---

# 65. MF5-C handoff — Frames, Coordinates, Charts & Transformations

MF5-B now makes the next problem unavoidable.

Once a domain may have topology/metric/projective/affine/Riemannian/action structures, how are those structures *described* without confusing the description with the structure?

MF5-C must study:

- reference frame vs basis vs coordinate system vs chart;
- point/locus vs coordinate tuple;
- active vs passive transformations;
- change of coordinates vs physical transformation;
- local charts and atlases;
- chart overlap/transition maps;
- singular coordinates vs singular geometry;
- Euclidean frame / body frame / camera frame / world frame;
- egocentric, allocentric, intrinsic/object-centered frames;
- homogeneous/projective coordinates;
- covariance/contravariance at the conceptual level;
- gauge/reparameterization freedom;
- coordinate-invariant quantities;
- frame-dependent quantities;
- pose transformations;
- calibration and provenance;
- uncertain frames/transforms;
- when a coordinate system is merely analyst convenience versus systemically recruited representation;
- transform composition/order and noncommutativity where relevant;
- cross-frame correspondence failures.

Central attack:

```text
Locus ≠ Coordinate
Frame ≠ Basis ≠ Chart ≠ Coordinate System
Coordinate Change ≠ Physical Change
Same Coordinates ≠ Same Position
Different Coordinates ≠ Different Position
Coordinate Singularity ≠ Geometric Singularity
```

**Next: MF5-C — Frames, Coordinates, Charts & Transformations.**
