# Ordivon Media Foundations — MF5-A Space Ontology

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 24 after checkpoint  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen.  
**Status:** MF5-A complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-B — Topology, Metric & Geometry.

---

# 1. Problem statement

MF4-F studied **spatial relations as composition-defining organization**. It did not establish an ontology of space itself.

MF5 begins below layout/media categories and asks:

> What makes a domain genuinely spatial, and what must be separated among space, locus, region, position, place, coordinate, frame, topology, metric, geometry, dimension, locality, occupancy, reachability and spatial representation?

The central anti-collapse is:

```text
Space
 ≠ Coordinate System
 ≠ Metric
 ≠ Geometry
 ≠ Map
 ≠ Configuration Space
 ≠ Generic Vector/Latent Space
```

---

# 2. `Space` is overloaded

The mathematical word `space` appears in vector spaces, probability spaces, function spaces, state spaces and embedding spaces. This linguistic use is broader than spatial ontology.

### SA-01

**A generic mathematical/state domain is not automatically a spatial domain in the MF5 sense.**

Calling something a `space` is not evidence that its coordinates/distances have target-level spatial standing.

---

# 3. Container ontology is too strong

The intuitive picture `empty Euclidean box + occupants` works in many ordinary contexts but fails across physical relativity, perceptual space, map/diagram space, robot configuration space and virtual space.

### SA-02

**Space is not universally a passive Euclidean container.**

### SA-03

**Space is not identical to its current occupants.**

Unoccupied regions/configurations remain admissible.

---

# 4. Locus, position, coordinate, place and region

MF5-A separates:

- **Locus:** a position-like element/cell/region/configuration under a spatial structure.
- **Position:** a relation locating an entity/state relative to a spatial domain/frame.
- **Coordinate:** a code/parameter assignment for a locus/position under a chart/frame.
- **Place:** a locus/region with re-identifiable contextual/semantic/history-bearing identity; not frozen as a minimal spatial primitive.
- **Region:** an extended/substructured subset/part of a spatial domain under a declared granularity.

### SA-04

`Locus ≠ Position ≠ Coordinate ≠ Place`.

### SA-05

**Point is not frozen as the universal atom of physical/perceptual/action space.** Loci may be cells, regions, configurations or other position-bearing elements.

---

# 5. Coordinate discipline

The same locus can receive different coordinate tuples under different charts/frames; the same tuple can denote different loci under different frames.

### SA-06

**Coordinate tuple ≠ position identity.**

### SA-07

**Coordinate system/chart is representational/parametric infrastructure for spatial structure, not the structure itself.**

### SA-08

**No canonical global coordinate system is required by the minimal Space ontology.**

Local/multiple charts and multiple reference frames are admissible.

---

# 6. Reference frame discipline

A frame provides the relational context needed to interpret position, direction or orientation: origin, orientation/basis, observer/body/object/environment relation and/or other reference structure.

### SA-09

`Reference Frame ≠ Coordinate Tuple`.

### SA-10

**Frame transformation can change coordinates while preserving selected spatial relations/invariants.**

---

# 7. Topology, metric and geometry must not be collapsed

Riemann's 1854 lecture already separates general manifold/region relations from possible measure-relations and rejects treating one Euclidean measure structure as logically forced by the concept of manifoldness.

### SA-11

`Topology/Neighborhood Structure ≠ Metric/Measure Structure`.

### SA-12

**Metric structure is optional and typed.** Not every useful proximity, action cost or reachability relation is a mathematical metric.

### SA-13

**Geometry is broader than one Euclidean metric.** Projective, affine, Euclidean, Riemannian, graph/action and other structures preserve different relation families.

---

# 8. Spatial relation family

At minimum MF5 must keep distinct:

```text
Distance
Direction
Orientation
Adjacency
Incidence
Containment
Betweenness
Connectivity
Continuity
Visibility
Reachability
```

### SA-14

**No universal reduction of all spatial relations to one distance scalar is accepted.**

---

# 9. Locality is typed

Physical closeness, perceptual closeness, map/display nearness, action cost/reachability and latent-vector similarity can diverge.

### SA-15

```text
PhysicalNear
 ≠ PerceptualNear
 ≠ RepresentationalNear
 ≠ ActionNear
 ≠ LatentSimilarityNear
```

### SA-16

**Locality is indexed to a neighborhood/adjacency/interaction/cost structure, not universally to small Euclidean distance.**

---

# 10. Position, orientation, pose and configuration

A system configuration may include position, orientation, joint states and other degrees of freedom.

### SA-17

`Position ≠ Orientation ≠ Pose ≠ Configuration`.

Lozano-Pérez's configuration-space formulation is a decisive hard case: a whole object's position/orientation configuration can be treated as one point in a configuration space, while forbidden/collision-producing configurations become regions of that derived domain.

### SA-18

**A point in a spatialized configuration domain need not correspond to one physical-world point.**

### SA-19

**Configuration/action space ≠ physical space.** It is a derived possibility space whose structure is grounded in degrees of freedom, constraints and action/reachability relations.

---

# 11. Dimensionality is typed

MF5-A separates:

```text
Coordinate Dimension
Intrinsic/Local Dimension
Embedding Dimension
Configuration/DOF Dimension
```

### SA-20

**Number of stored coordinates does not by itself determine intrinsic dimension.**

### SA-21

**Embedding geometry/dimension is not automatically intrinsic geometry/dimension.**

---

# 12. Physical, perceptual and representational space

MF2 already established that perception produces task/body-relative structured discriminability rather than a complete world replica. Neural spatial systems also separate location, heading and reference-frame relations.

### SA-22

**Perceptual space ≠ physical space.**

Under MF3, a map/diagram can preserve selected topology/order/connectivity while distorting distance/angle/scale.

### SA-23

**Representational/map space ≠ target physical space.** Spatial fidelity is typed by the representational key and preserved relation family.

---

# 13. Virtual and computational spaces

A designed virtual world can instantiate locations, adjacency, collision, orientation, navigation and occupancy without one-to-one physical extension.

### SA-24

**Virtual space can possess designed/computational spatial standing without being a second physical spacetime.**

A latent/vector domain, however, is not target-spatial merely because coordinates and Euclidean/cosine operations are available.

### SA-25

**Latent/vector geometry ≠ target spatial standing.**

---

# 14. Occupancy, accessibility and reachability

### SA-26

`Occupancy ≠ Accessibility ≠ Reachability`.

A locus may be unoccupied yet spatially defined; physically near regions may be action-inaccessible; a configuration-space obstacle is a forbidden state region rather than a material object occupying that abstract domain.

---

# 15. Spatial uncertainty

Position, boundary, frame, metric relation, topology or correspondence can be uncertain/probabilistic.

### SA-27

**Uncertainty is compatible with spatial standing and must be typed by spatial relation/profile.**

---

# 16. Spatial equivalence is transformation-relative

Translation, rotation, reflection, deformation, reparameterization, projection and reflow preserve different relation families.

### SA-28

**Spatial identity/equivalence must name the transformation class and preserved invariants.**

---

# 17. Spatial standing

MF5-A introduces the provisional constitutive notion:

```text
SpatialStanding(S | X, Σ)
```

A candidate relation structure `S` has spatial standing when its loci/region/configuration relations belong to the target domain/practice/system/formal construction under scope, rather than arising only from an analyst's arbitrary coordinate assignment/embedding.

Possible standing routes:

- SS1 Physical/measurement/dynamical.
- SS2 Perceptual/sensorimotor.
- SS3 Action/configuration/reachability.
- SS4 Representational/designed.
- SS5 Formal/mathematical construction.
- SS6 Hybrid.

### SA-29

**Analyst embedding/coordinate assignment ≠ target spatial structure.**

### SA-30

**Formal spatial standing and represented-target spatial standing are separate under MF3.**

---

# 18. Provisional Space ontology

> **A spatial domain is a scope-relative structured possibility domain of loci, regions or configurations in which one or more positional, neighborhood, incidence, separation, orientation, connectivity, continuity, metric or related spatial-relation families have standing through physical organization, perception/action, formal construction, configuration constraints, representation/design or combinations thereof.**

Compact candidate:

```text
Space
 ≈ Possibility Domain
 + Loci / Regions / Configurations
 + Spatial Standing
 + Typed Spatial Relation Structure
 + Scope
```

Coordinates, metrics, global frames, Euclidean geometry, occupancy, representation and physical realization are optional/typed additions.

---

# 19. Provisional SpaceProfile

```text
SpaceProfile = <
  X     : domain,
  L     : loci/regions/configurations,
  R     : spatial relation families,
  T     : topology/neighborhood profile,
  G     : metric/geometric profile,
  F     : reference-frame profile,
  C     : charts/coordinates,
  D     : dimensionality profile,
  O     : occupancy,
  A     : accessibility/action/reachability,
  U     : uncertainty,
  S     : spatial-standing route,
  Σ     : scope/granularity,
  H     : provenance/history
>
```

Not every field is required for every spatial domain.

---

# 20. Provisional non-collapse stack

```text
Space ≠ Coordinate System
Locus ≠ Position ≠ Coordinate ≠ Place
Point ≠ Region
Position ≠ Orientation ≠ Pose ≠ Configuration
Topology ≠ Metric ≠ Geometry
Distance ≠ Adjacency ≠ Connectivity ≠ Reachability
Coordinate Dimension ≠ Intrinsic Dimension ≠ Embedding Dimension ≠ DOF Dimension
Physical Space ≠ Perceptual Space ≠ Representational Space ≠ Configuration Space ≠ Latent Space
Mathematical Space ≠ Target Spatial Standing
```

---

# 21. Claims rejected by MF5-A

Reject as universal foundational claims:

- space is an empty three-dimensional Euclidean container;
- space is identical to occupants or requires occupancy;
- point/coordinate tuple is the universal primitive of every space;
- coordinate system is identical to space;
- coordinate equality implies position identity across frames;
- every space has one canonical global coordinate system;
- topology, metric and geometry are interchangeable;
- every spatial relation reduces to Euclidean distance;
- every useful cost/similarity/reachability relation is a metric;
- physical/perceptual/representational/action/latent spaces share one geometry by default;
- distorted-distance maps fail to represent space;
- vectors/embeddings are spatial merely because they have coordinates/similarity functions;
- configuration-space points are physical point locations;
- dimension equals coordinate count;
- embedding dimension equals intrinsic dimension;
- locality always means small physical metric distance;
- physical proximity implies reachability;
- reference-frame dependence makes spatial structure arbitrary;
- one absolute neural coordinate frame is required;
- MF4-F already solved space ontology.

---

# 22. Literature anchors

- Bernhard Riemann (1854/1867), *Über die Hypothesen, welche der Geometrie zu Grunde liegen*; William K. Clifford translation, *Nature* 8 (1873). General manifoldness and separation of region/measure relations.
- Albert Einstein (1916), *Die Grundlage der allgemeinen Relativitätstheorie*. Coordinate labels versus metric/spacetime structure; coordinate-independent physical formulation.
- Taube, Muller & Ranck (1990), head-direction cell experiments. Context/environment anchored directional coding.
- Duhamel, Colby & Goldberg (1992), spatial updating in parietal cortex across eye movements.
- Lozano-Pérez (1983), *Spatial Planning: A Configuration Space Approach*, IEEE Transactions on Computers 32(2), 108–120. Configuration as a point in a derived planning space.

---

# 23. MF5-B handoff

MF5-A leaves the decisive structural problem unresolved:

> Which relation structures define topology, uniformity, metric and geometry; how do they induce/forget one another; which are incomparable; and what makes one chosen topology/metric/geometry have target spatial standing rather than being an analyst convenience?

Required hard cases:

- sphere/manifold and local charts;
- same topology under different metrics;
- topological/subway maps;
- graph/network shortest paths;
- projective camera geometry;
- affine vs projective vs Euclidean invariants;
- Riemannian intrinsic geometry;
- asymmetric action costs;
- configuration spaces.

**Next: MF5-B — Topology, Metric & Geometry.**
