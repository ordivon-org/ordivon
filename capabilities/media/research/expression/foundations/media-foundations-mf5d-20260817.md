# Ordivon Media Foundations — MF5-D Regions, Boundaries, Occupancy, Locality & Spatial Relations

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 26 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen; MF5-A Space Ontology, MF5-B Topology/Metric/Geometry and MF5-C Frames/Coordinates/Transforms complete and provisional.  
**Status:** MF5-D complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-E — Perceptual, Body-Centered & Experienced Space.

---

# 0. Purpose

MF5-A established a spatial domain as a structured possibility domain rather than a passive container.
MF5-B separated topology, metric, geometry and action/reachability structures.
MF5-C separated spatial state from coordinate/frame description.

MF5-D attacks the next deceptively simple picture:

```text
Space is divided into regions.
Regions have edges.
Objects occupy regions.
Nearby regions are connected.
Visible regions are occupied regions.
```

Every line is too strong.

The central distinctions are:

```text
Region ≠ Occupant
Boundary ≠ Material Edge
Inside ≠ Part-of
Contact ≠ Overlap
Adjacency ≠ Connectivity
Near ≠ Reachable
Visibility ≠ Occupancy
Empty ≠ Spatially Irrelevant
Threshold Boundary ≠ Arbitrary Boundary
```

MF5-D must support crisp topology, open/closed regions, qualitative region calculi, continuous fields, configuration-space obstacles, vague/fuzzy regions, occlusion, multiscale boundaries and task-dependent locality without turning every analyst segmentation into target spatial ontology.

---

# 1. Region is not an occupant

A **region** is provisionally a spatially standing subset/extent/cell/domain-part under a declared spatial structure and granularity.

An **occupant** is an entity/state/material/process assigned to or realized over some region.

### SD-01

**Region identity ≠ occupant identity.**

A room remains the same room when empty; a grid cell remains the same address when unoccupied; a reserved zone can exist before any object enters it.

### SD-02

**Occupancy is a relation/state over a spatial domain, not the constitutive definition of regionhood.**

---

# 2. Empty region is not spatial nothingness

An unoccupied region can still have:

- topology;
- boundary;
- size/shape;
- adjacency;
- accessibility;
- ownership/permission;
- visibility;
- layout role;
- future action relevance.

### SD-03

**Empty ≠ spatially irrelevant.**

### SD-04

**Negative/empty space can carry relational structure without carrying an occupant at the declared occupancy layer.**

This preserves MF4-F whitespace/negative-space results while moving region/occupancy ontology into MF5.

---

# 3. Region is scope/granularity relative but not thereby arbitrary

The same physical substrate may be partitioned as:

- pixels;
- cells;
- rooms;
- floors;
- buildings;
- districts;
- watersheds;
- fields/zones.

### SD-05

**Region individuation requires a declared spatial scope/granularity and standing route.**

### SD-06

**Multiple grounded regionalizations can coexist; non-unique segmentation ≠ arbitrary segmentation.**

This mirrors MF4 multiple objective decompositions and MF5-B multiple grounded geometries.

---

# 4. Boundary is a topological relation, not necessarily a material edge

In point-set topology a boundary can be characterized relative to interior/closure/neighborhood structure. Egenhofer & Franzosa operationalize topological spatial relations through intersections of region interiors and boundaries rather than through material edge detectors or exact distances.

### SD-07

**Topological boundary ≠ material edge/surface.**

### SD-08

A boundary may have formal/representational/perceptual/administrative standing even where no material discontinuity exists.

Examples include property borders, map zones and designed UI regions.

---

# 5. Material discontinuity does not uniquely determine region boundary either

A physical discontinuity may be ignored under one task/region scheme, while a smooth gradient may be partitioned by a standing threshold under another.

### SD-09

**Material edge ≠ universal region boundary.**

### SD-10

**Region boundary standing depends on the target structure/practice/process, not on edge contrast alone.**

---

# 6. Interior, boundary and exterior are typed relative to a region/topology

For a region `A`, concepts such as:

```text
Int(A)
Bd(A)
Ext(A)
Cl(A)
```

are relational/topological constructions, not universal physical substances.

### SD-11

**Interior/exterior/boundary are region- and topology-relative roles.**

### SD-12

A locus can be boundary-relative to one region while interior/exterior relative to another.

---

# 7. Open versus closed membership exposes boundary inclusion discipline

Two sets can share the same geometric outline while differing in whether boundary points are included.

### SD-13

**Outline/shape appearance does not by itself specify boundary membership semantics.**

### SD-14

**Open/closed/set-membership conventions can matter mathematically or operationally even when rendered display looks identical.**

MF5 must not collapse visual edge with set-theoretic membership.

---

# 8. Contact is not overlap

Two regular regions can meet only at their boundaries while their interiors remain disjoint.

Egenhofer–Franzosa's boundary/interior intersection discipline makes this distinction explicit; RCC-8 similarly separates externally connected from partial overlap relations.

### SD-15

**Boundary contact ≠ interior overlap.**

### SD-16

**Touching can be a genuine standing spatial relation without shared interior occupancy.**

---

# 9. Overlap is not containment

Two regions may share interior points while neither contains the other.

### SD-17

**Overlap ≠ containment ≠ equality.**

### SD-18

The amount/measure of overlap is additional metric/measure information beyond the qualitative fact of overlap.

---

# 10. Containment is not parthood

A coin can be inside a box without being a component of the box.
A person can be inside a room without being a structural part of the room.

### SD-19

**Spatial containment ≠ mereological/compositional parthood.**

This preserves MF4-F/Composition separation.

---

# 11. Inside is not ownership or permission

A person can be physically inside a region without owning it or being permitted there.

### SD-20

**Inside ≠ belongs-to ≠ owns ≠ authorized-in.**

Spatial, institutional, semantic and normative relations must stay distinct until later MF10/MF13 layers.

---

# 12. Proper part can be tangential or non-tangential

RCC-style region reasoning distinguishes containment where the inner region touches the containing boundary from containment wholly within the interior.

### SD-21

**Containment has boundary-contact subtypes; `inside` is not one unqualified boolean.**

This matters for fit, collision, enclosure, margins and packing.

---

# 13. RCC shows region-based spatial reasoning need not reduce to coordinates

Randell, Cui & Cohn's Region Connection Calculus uses region and connection as a qualitative ontology and yields the well-known RCC-8 relation family under its definitions/refinements.

### SD-22

**Qualitative topological relation standing does not require exact metric coordinates.**

### SD-23

**Region-based ontology is a legitimate spatial modeling profile, not merely a degraded point-coordinate model.**

MF5 does not adopt RCC as the universal region ontology; it adopts it as a hard counterexample to point/metric necessity.

---

# 14. But RCC/Egenhofer calculi are model families, not the ontology of all space

Real spatial domains can involve:

- directed reachability;
- fields/gradients;
- fuzzy boundaries;
- projective visibility;
- dynamic occupancy;
- multiscale regions;
- semantic/administrative zones.

### SD-24

**One qualitative relation calculus cannot be elevated into universal spatial ontology.**

### SD-25

**Relation calculus adequacy is domain/query/standing relative.**

---

# 15. Adjacency is local relation; connectivity is path/global relation

`A` and `B` may not directly touch but belong to one connected component through intermediates.

### SD-26

**Adjacency/contact ≠ connectivity/path-connectedness.**

### SD-27

**Local neighborhood relation and global reachability/connectivity must be tracked separately.**

---

# 16. Connectivity itself is typed

Possible connectivity profiles include:

- topological connectedness;
- graph/path connectivity;
- traversable connectivity;
- communication connectivity;
- visual connectivity;
- fluid/material connectivity.

### SD-28

**`Connected` requires a declared relation substrate.**

### SD-29

Physical/topological connectedness does not automatically imply action/communication connectivity.

---

# 17. Near is not adjacency

Two regions can be metrically close without touching.
Two graph-adjacent locations can be physically far.

### SD-30

**Near/proximity ≠ adjacency/contact.**

### SD-31

Qualitative `near` generally requires a scale/context/tolerance or learned convention beyond raw topology.

---

# 18. Near is not reachable

A thin wall can make two physically close positions require a long route.
A portal/teleport edge can make physically remote locations action-near.

### SD-32

**Metric nearness ≠ reachability nearness.**

### SD-33

**Locality must be typed by topology, metric, interaction, action/control or information flow.**

---

# 19. MF5-D LocalityProfile

Provisionally:

```text
LocalityProfile = <
  Domain,
  RelationType : neighborhood/metric/adjacency/path/action/interaction/etc.,
  Scale/Tolerance,
  Directionality,
  Barrier/Constraint model,
  Frame/Geometry,
  StandingRoute,
  Time/State if relevant,
  Uncertainty,
  Scope
>
```

### SD-34

**There is no universal scalar locality independent of relation type.**

---

# 20. Occupancy is not accessibility

A region can be unoccupied yet inaccessible due to walls, permissions or kinematic constraints.
A region can be occupied yet traversable/shared depending entity type and policy.

### SD-35

**Occupancy ≠ accessibility ≠ traversability.**

---

# 21. Occupancy is entity- and granularity-relative

A table may occupy a room region at one level while leaving extensive free volume around/under it at another.
A fluid/field can partially fill a region.

### SD-36

**Occupancy requires occupant type, spatial extent and granularity.**

### SD-37

**Binary occupied/free is a useful profile, not a universal occupancy ontology.**

---

# 22. Configuration-space obstacles are the decisive occupancy falsifier

Lozano-Pérez maps physical collision constraints into configuration space: configurations forbidden by physical obstacles form **configuration-space obstacle regions**.

### SD-38

**A forbidden region in derived action/configuration space need not be materially occupied in that abstract space.**

### SD-39

**Obstaclehood is relation/system dependent: it can mean forbidden configuration, not material occupant.**

This decisively separates:

```text
Material Occupancy
≠ Constraint Exclusion
≠ Action Inaccessibility
```

---

# 23. One physical obstacle induces robot-dependent configuration obstacles

The forbidden configurations depend on robot/object geometry and degrees of freedom.

### SD-40

**Obstacle region is not an intrinsic property of environmental material alone; it can be a relational consequence of environment × body/configuration model.**

This prepares MF5-F action/configuration-space foundations.

---

# 24. Free space is also derived

In configuration planning:

```text
C_free = C \ C_obstacle
```

### SD-41

**Free region means admissible under a declared constraint model, not universally empty physical space.**

### SD-42

`Free ≠ Empty`.

A physically occupied or dynamically shared region may be admissible to some agent/action; an empty region may be forbidden.

---

# 25. Visibility is not occupancy

A region/object may be occupied but invisible because occluded, outside field of view, transparent/opaque relations, sensor range or illumination conditions.

### SD-43

**Occupied ≠ visible.**

### SD-44

**Visible ≠ occupied by the visible signal itself.**

Visibility is an observer/sensor/viewpoint/projection relation over spatial structure.

---

# 26. Occlusion changes visibility without changing occupancy

Move the viewpoint behind an occluder; target occupancy can remain unchanged while visible projection disappears.

### SD-45

**Occlusion/visibility state ≠ target occupancy state.**

### SD-46

**Image overlap/occlusion is a projected depth-order relation, not world-region overlap by default.**

This preserves MF4-F and MF5-C projection distinctions.

---

# 27. Occluder boundary is not target object boundary

A hidden object's image termination can be caused by another object rather than its own physical edge.

### SD-47

**Visibility boundary ≠ intrinsic object/region boundary.**

This links MF2 perceptual boundary ownership to MF5 spatial boundary ontology.

---

# 28. Boundary ownership is a distinct claim

The same geometric contour/locus can separate two regions while being attributed to one surface/object or to an administrative partition convention.

### SD-48

**Boundary locus ≠ boundary ownership/attribution.**

### SD-49

Boundary ownership can be perceptual, representational, legal/institutional or physical depending layer; MF5 records the relation type without collapsing them.

---

# 29. Continuous fields undermine crisp object-first regionalism

Consider a scalar field:

```text
f : X -> R
```

Temperature, pressure, probability, luminance, density or concentration can vary continuously.

### SD-50

**Spatial structure need not begin with crisp object regions.**

Regions may be derived from:

- level sets;
- superlevel/sublevel sets;
- gradients/ridges;
- basins;
- connected components;
- process-defined zones.

---

# 30. Threshold region is not automatically arbitrary

For threshold `τ`:

```text
R_τ = {x : f(x) >= τ}
```

Changing `τ` can change:

- boundary position;
- area;
- component count;
- holes/connectivity.

### SD-51

**Threshold-dependent boundary ≠ non-real boundary by definition.**

If `τ` is grounded by physical phase transition, safety standard, task criterion, sensor response or institutional rule, the resulting region may have target/practice standing.

### SD-52

**Analyst threshold selection requires standing/evidence; mathematical definability alone is insufficient.**

---

# 31. Small threshold change can cause topological change

Components can appear, merge, split or disappear as threshold varies.

### SD-53

**Boundary uncertainty/threshold uncertainty can produce discrete topology uncertainty, not just small metric error.**

This extends MF4-F topological aliasing.

---

# 32. Scale/coarse-graining can change region identity

A narrow channel visible at fine scale can disappear at coarse resolution, merging or separating regions depending operation.

### SD-54

**Region topology can be scale/resolution dependent.**

### SD-55

**Fine-scale and coarse-scale regionalizations can both be grounded for different queries.**

---

# 33. Pixel boundary is not necessarily target boundary

Segmentation discretizes/estimates spatial regions under a sampling and model pipeline.

### SD-56

**Raster/grid boundary ≠ target boundary.**

### SD-57

Sampling, anti-aliasing, thresholding and morphology can create/remove apparent contacts and holes.

This inherits MF1 observation/aliasing and MF2 segmentation uncertainty.

---

# 34. Vagueness is not identical to measurement uncertainty

A coastline, forest edge, neighborhood or cloud may have inherently graded/conventional membership under some concepts, while a crisp engineered wall can merely be measured uncertainly.

### SD-58

**Boundary vagueness ≠ epistemic location uncertainty.**

### SD-59

A boundary can simultaneously be conceptually vague and observationally uncertain; the two uncertainty sources should remain separable.

---

# 35. Fuzzy/vague region models are hard cases against mandatory crisp boundaries

Schockaert, Cornelis, De Cock & Kerre explicitly generalize RCC-style spatial relations to fuzzy relations because real-world regions often lack precisely defined boundaries and show how vague regions represented as fuzzy sets can support graded spatial relation reasoning.

### SD-60

**Crisp one-dimensional boundary is not universally required for region standing.**

### SD-61

**Membership/boundary can be graded or interval/broad while spatial relations remain reason-able under an appropriate model.**

MF5 does not freeze fuzzy sets as the universal vagueness model; they are a counterexample to crisp-boundary necessity.

---

# 36. Fuzzy membership is not probability

A fuzzy degree may encode graded membership/vagueness; probability may encode uncertainty over a crisp but unknown state.

### SD-62

**Fuzzy membership ≠ probability of occupancy/membership.**

### SD-63

Uncertainty representation type must match whether the phenomenon is vagueness, stochasticity, epistemic uncertainty, population frequency or mixed.

---

# 37. Probabilistic occupancy is another valid profile

Robotics/mapping systems can represent occupancy probability over cells/locations.

### SD-64

**Probabilistic occupancy ≠ fuzzy regional membership ≠ deterministic occupancy.**

MF5-D does not privilege one encoding universally.

---

# 38. Region existence and region-boundary confidence are separate

A system may be confident that a storm/forest/object region exists while uncertain about its precise boundary.

### SD-65

**Region identity confidence ≠ boundary-location confidence.**

### SD-66

Boundary uncertainty does not automatically imply no region standing.

---

# 39. Region standing and boundary standing are separate

A region may be operationally established while boundary is context-sensitive or approximate.
Conversely, a formal boundary line can be precisely drawn even when the target region concept lacks strong standing.

### SD-67

**RegionStanding ≠ BoundaryStanding.**

---

# 40. Boundary standing routes

Provisional routes include:

- **BS1 Physical/material:** material/surface/interface discontinuity.
- **BS2 Dynamical/process:** separatrix, phase/process transition, flow basin.
- **BS3 Perceptual:** segmentation/grouping/border ownership.
- **BS4 Designed/engineered:** zone, hit region, cell, geofence.
- **BS5 Representational/formal:** map polygon, topology/model boundary.
- **BS6 Institutional/conventional:** jurisdiction/property/administrative border.
- **BS7 Threshold/criterion grounded:** safety, classification, phase/task level set.
- **BS8 Hybrid.**

### SD-68

**No one boundary-standing route is universally necessary.**

---

# 41. Boundary evidence is not boundary standing

A gradient detector, segmentation model, survey record or legal document can provide evidence for different boundary claims.

### SD-69

**Boundary standing route ≠ evidence acquisition route.**

This carries MF3/MF4 evidence discipline forward.

---

# 42. Region standing requires more than analyst selection

For candidate region `R`, arbitrary subset selection is always mathematically possible.

MF5-D proposes provisional:

```text
RegionStanding(R, X | Σ)
```

when the distinction `R` versus relevant alternatives is established by physical/dynamical organization, perception/action, design/specification, representation/convention, institution, formal construction, grounded threshold/criterion or another non-arbitrary route in the target/practice.

### SD-70

**Analyst-selected subset ≠ target-standing region.**

---

# 43. Boundary anti-inflation test

A candidate boundary is stronger when changing/removing/reassigning it changes a declared spatial profile such as:

- connectivity;
- containment;
- occupancy classification;
- allowed action;
- identity;
- interpretation;
- process dynamics;
- institutional status;
- perceptual segmentation.

### SD-71

**Boundary counterfactual relevance is useful evidence but not a universal causal requirement.**

Formal/institutional/perceptual boundaries can have standing without physically blocking motion.

---

# 44. Barrier is not boundary

A painted line may be a boundary without impeding movement.
A force field/repulsive zone can block or penalize movement without a crisp material boundary.

### SD-72

**Boundary ≠ barrier.**

### SD-73

**Barrier/permeability is an action/material property layered on spatial boundary structure.**

---

# 45. Permeability is typed by entity/action

A wall blocks a person but not light, radio, heat or some fluids to the same degree.

### SD-74

**Spatial barrier/locality is entity-, modality- and process-relative.**

This will connect to MF5-E perception and MF5-F action.

---

# 46. Contact is entity/model dependent at finite resolution

Microscopic roughness, tolerance bands and soft/deformable bodies complicate exact zero-gap contact.

### SD-75

**Contact may require a declared geometric/physical tolerance/model; exact set intersection is a special formal case.**

### SD-76

Tolerance-grounded contact is not arbitrary if measurement/action conventions establish it.

---

# 47. Distance-to-boundary and signed-distance fields are representations, not boundaries themselves

A signed distance field can encode proximity/interior/exterior relative to a region.

### SD-77

**Boundary representation ≠ boundary standing.**

Different representations (polygon, mesh, level set, SDF, implicit function, raster mask) can describe the same region/boundary profile.

This is the MF5-C description/state distinction applied to regions.

---

# 48. Region representation identity is also transformation/format relative

One region may be encoded as:

- polygon vertices;
- voxel set;
- bitmap mask;
- implicit inequality;
- constructive solid geometry;
- graph component;
- probability field.

### SD-78

**Region ≠ region encoding.**

### SD-79

Cross-encoding equivalence must name preserved topology/metric/boundary/membership precision.

---

# 49. Region correspondence across transforms is not automatic

After projection, reflow, map transformation or physical deformation, a region may have a corresponding image/representation region with different metric/topological properties.

### SD-80

**Region correspondence ≠ region geometric identity.**

### SD-81

Cross-domain region mapping requires MF3 grounding plus MF5 transform/structure semantics.

---

# 50. Hole, component and boundary count are topology-level region features

A donut-like region and disk can have similar area/perimeter scales but different topology.

### SD-82

**Region identity/fidelity cannot be reduced to area/centroid/bounding box.**

### SD-83

Topological descriptors and metric descriptors are complementary, not interchangeable.

---

# 51. Bounding box is not region

Many distinct shapes/occupancies share the same bounding box.

### SD-84

**Bounding extent ≠ region topology/occupancy.**

Likewise center/centroid is not region identity.

---

# 52. Convex hull is not original region

Taking a convex hull fills concavities and may eliminate holes/gaps.

### SD-85

**Geometric envelope/approximation ≠ original region.**

### SD-86

Approximation quality must name which relations are preserved for the task.

---

# 53. Buffer/dilation changes spatial relation profile

Expanding a region by radius `r` can make formerly disjoint regions touch/overlap and can close narrow gaps.

### SD-87

**Morphological/buffer transformation can change topology and relation type, not merely numerical boundary position.**

### SD-88

Safety margins/configuration-space inflation can be intentionally conservative spatial transformations with operational standing.

---

# 54. Intersection/union do not automatically preserve semantic region identity

Formal set operations produce well-defined sets, but whether the result is a meaningful target region is a separate standing claim.

### SD-89

**Set-theoretic constructibility ≠ target region standing.**

This is another anti-inflation consequence.

---

# 55. Region overlap does not imply shared object identity

Two zones can overlap because they encode different classifications/policies.

### SD-90

**Overlapping regions can coexist as cross-cutting spatial layers without merging into one region/object.**

This mirrors MF4 overlap/polyhierarchy.

---

# 56. One locus can belong to multiple standing regions

A point can simultaneously lie in:

- a city;
- a watershed;
- a school district;
- a radio coverage cell;
- a hazard zone.

### SD-91

**Region membership is relation/layer typed; unique partition is not required.**

---

# 57. Exclusive partitions are a special case

Grid cells or administrative partitions may be designed to be mutually exclusive/exhaustive under a convention.

### SD-92

**Partition constraints are additional organizational properties, not universal region ontology.**

---

# 58. Place/territory/zone should not be collapsed into raw region

A `place` can add identity/history/experience; `territory` can add control/ownership; `zone` can add rule/function.

### SD-93

**Region ≠ Place ≠ Territory ≠ Functional/Normative Zone.**

MF5-D keeps raw spatial region ontology thin; richer concepts belong partly to later Agency/Experience/Social/Governance layers.

---

# 59. Locality can itself be field-valued or graded

Influence/proximity may decay continuously rather than switch at one neighborhood radius.

### SD-94

**Locality need not be crisp or binary.**

### SD-95

A kernel/field/proximity function is one representation of graded locality; its target standing must still be established.

---

# 60. Directional locality breaks symmetric-neighborhood intuition

Wind, traffic, control dynamics, sensing cones or network direction can make influence/reachability asymmetric.

### SD-96

**Locality can be directional/an-isotropic.**

### SD-97

**Neighborhood symmetry is a model property, not a universal spatial law.**

---

# 61. Visibility locality is viewpoint/sensor dependent

A physically nearby target can be invisible; a distant bright/transmitted signal can be visible.

### SD-98

**Perceptual/visibility locality ≠ physical metric locality.**

This is a handoff to MF5-E.

---

# 62. Region/Boundary/Occupancy standing schema

MF5-D proposes:

```text
RegionProfile = <
  Domain,
  RegionIdentity,
  Membership/Extent,
  Interior/Exterior/Boundary semantics,
  Topology/Geometry,
  StandingRoute,
  Granularity/Scale,
  Layer/Classification,
  OccupancyState,
  Accessibility/Reachability,
  VisibilityProfile,
  Encoding/Representation,
  Provenance/History,
  Uncertainty/Vagueness,
  Scope
>
```

### SD-99

**Region profile separates standing, geometry, occupancy, visibility, access and representation rather than merging them into one mask.**

---

# 63. BoundaryProfile

```text
BoundaryProfile = <
  Region(s)/Relata,
  BoundaryType : topological/material/process/perceptual/designed/formal/institutional/criterion,
  MembershipConvention,
  Contact/Ownership semantics,
  Thickness/Vagueness model,
  Geometry/Topology,
  Barrier/Permeability profile,
  Scale/Resolution,
  StandingRoute,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### SD-100

**A boundary should not be represented as a naked line/edge without type and standing where semantics matter.**

---

# 64. OccupancyProfile

```text
OccupancyProfile = <
  Region/Loci,
  Occupant/EntityType,
  OccupancyMode : material/presence/reservation/probabilistic/etc.,
  Extent/FillFraction,
  Granularity,
  Time/State,
  Collision/Exclusion semantics,
  Accessibility relation,
  Provenance,
  Uncertainty,
  Scope
>
```

### SD-101

**Occupancy is a typed relation rather than one universal binary grid bit.**

---

# 65. SpatialRelationClaim schema

```text
SpatialRelationClaim = <
  Relata,
  RelationType : disjoint/contact/overlap/inside/contains/adjacent/near/connected/visible/reachable/etc.,
  Geometry/Topology/Frame,
  Region/Boundary semantics,
  Directionality,
  Scale/Tolerance,
  StandingRoute,
  Evidence/Provenance,
  Uncertainty/Vagueness,
  Time/State if relevant,
  Scope
>
```

### SD-102

**Bare predicates like `near`, `inside`, `touching`, `connected` are under-specified without relation profile when operational consequences matter.**

---

# 66. Final provisional anti-inflation criterion for MF5-D

A candidate region/boundary/locality relation is not promoted to target spatial standing merely because:

- a subset can be mathematically selected;
- a segmentation model outputs a mask;
- a threshold can be chosen;
- pixels share a label;
- a polygon can be drawn;
- a graph can be built;
- a distance transform exists.

Stronger standing requires at least one non-arbitrary route linking the distinction to target/practice/formal organization plus a declared scope.

### SD-103

**AnalystRegion ≠ TargetStandingRegion.**

### SD-104

**AnalystBoundary ≠ TargetStandingBoundary.**

### SD-105

**AnalystNeighborhood ≠ TargetStandingLocality.**

---

# 67. Evidence profile

Useful claim-matched evidence can include:

- physical/material interface measurement;
- topology/interior-boundary intersection tests;
- construction/specification records;
- region-connection relation consistency;
- process/dynamics separation;
- action/collision/reachability tests;
- perceptual segmentation/behavior;
- institutional/legal records;
- threshold/criterion provenance;
- calibration/survey evidence;
- transformation stability;
- cross-scale persistence;
- probabilistic/fuzzy membership evidence.

### SD-106

**Evidence adequacy is relation-type specific; no one edge detector, mask IoU or coordinate error is universal boundary/region evidence.**

---

# 68. Failure taxonomy

## Region hallucination

Analyst/model subset promoted to target region without standing.

## Boundary hallucination

Sampling/segmentation/chart seam promoted to target boundary.

## Boundary erasure

Standing separation ignored/merged.

## Contact/overlap collapse

Boundary touch interpreted as shared interior.

## Containment/parthood collapse

Inside relation interpreted as component identity.

## Occupancy/obstacle collapse

Forbidden configuration/action region interpreted as material occupancy.

## Empty/free collapse

Empty physical region interpreted as actionable free region or vice versa.

## Visibility/occupancy collapse

Occluded target treated as absent/unoccupied.

## Adjacency/connectivity collapse

Path connectivity confused with direct neighborhood/contact.

## Near/reachable collapse

Metric proximity treated as action accessibility.

## Scale/topology alias

Coarse-graining changes holes/connectivity without being tracked.

## Threshold laundering

Arbitrary criterion presented as natural boundary.

## Vagueness/uncertainty collapse

Fuzzy membership and epistemic probability conflated.

## Representation/region collapse

Raster mask/polygon/SDF treated as region ontology itself.

## Boundary-ownership error

Correct separation locus assigned to wrong surface/region/authority.

## Layer collapse

Overlapping valid regionalizations forced into one unique partition.

### SD-107

**Spatial-region failure is a typed family, not one IoU/distance scalar.**

---

# 69. Strongest non-collapse stack after MF5-D

```text
Region
 ≠ Occupant
 ≠ Region Encoding
```

```text
Boundary
 ≠ Material Edge
 ≠ Barrier
 ≠ Visual Contour
 ≠ Coordinate Seam
```

```text
Interior/Inside
 ≠ Part-of
 ≠ Ownership
 ≠ Permission
```

```text
Contact
 ≠ Overlap
 ≠ Containment
 ≠ Equality
```

```text
Adjacency
 ≠ Connectivity
 ≠ Nearness
 ≠ Reachability
```

```text
Empty
 ≠ Free
 ≠ Accessible
```

```text
Occupancy
 ≠ Obstaclehood
 ≠ Exclusion
 ≠ Visibility
```

```text
Visibility
 ≠ World Occupancy
 ≠ Image Overlap
```

```text
Vagueness
 ≠ Probability
 ≠ Measurement Uncertainty
```

```text
RegionStanding
 ≠ BoundaryStanding
 ≠ OccupancyState
 ≠ BoundaryEvidence
```

```text
Analyst Segmentation
 ≠ Target Spatial Standing
```

---

# 70. Claims rejected by MF5-D

Reject as universal foundational claims:

- a region is defined by what currently occupies it;
- empty region has no spatial role;
- every region has one crisp one-dimensional boundary;
- every boundary is a material edge/barrier;
- material discontinuity uniquely determines region boundary;
- visual contour equals topological/material boundary;
- region boundary semantics are determined by rendered outline alone;
- touching/contact equals overlap;
- overlap equals containment;
- containment equals compositional parthood;
- inside equals ownership/permission;
- adjacency equals connectivity;
- metric nearness equals adjacency or reachability;
- `connected` is meaningful without specifying relation substrate;
- occupancy equals accessibility/traversability;
- occupancy is universally binary;
- obstacles are always materially occupied spatial regions;
- configuration-space obstacles are physical occupants of configuration space;
- free means physically empty;
- visible means occupied/present, or invisible means absent;
- occlusion changes world occupancy;
- visibility boundary equals object boundary;
- crisp boundary is necessary for region standing;
- fuzzy membership equals probability;
- boundary vagueness equals measurement uncertainty;
- threshold-defined boundary is necessarily arbitrary;
- any mathematically definable threshold/segmentation has target standing;
- raster mask/polygon/bounding box/convex hull is identical to target region;
- one unique region partition is required;
- a locus can belong to only one region;
- topology/metric/IoU alone gives universal region fidelity;
- one spatial relation calculus such as RCC is universal ontology;
- analyst-selected subset/graph/neighborhood automatically has target spatial standing.

---

# 71. Primary/original/authoritative anchors

- **Max J. Egenhofer & Robert D. Franzosa (1991)**, `Point-Set Topological Spatial Relations`, *International Journal of Geographical Information Systems* 5(2), 161–174, DOI 10.1080/02693799108927841. Defines topological spatial relations using boundary/interior intersections; distinguishes relations including disjointness, equality and containment without relying on exact metric coordinates.
- **David A. Randell, Zhan Cui & Anthony G. Cohn (1992)**, `A Spatial Logic based on Regions and Connection`, KR'92, 165–176. Region Connection Calculus (RCC) program uses regions/connection for qualitative spatial reasoning; Leeds identifies RCC as originating there and presents RCC-8 as the canonical relation family.
- **Tomás Lozano-Pérez (1983)**, `Spatial Planning: A Configuration Space Approach`, *IEEE Transactions on Computers* C-32(2), 108–120, DOI 10.1109/TC.1983.1676196. Characterizes object position/orientation as a point in configuration space and forbidden configurations caused by physical obstacles as configuration-space obstacle regions.
- **Steven Schockaert, Chris Cornelis, Martine De Cock & Etienne E. Kerre (2006)**, `Fuzzy Spatial Relations between Vague Regions`, IEEE Intelligent Systems Conference, 217–222. Generalizes RCC-style relations to fuzzy relations for vague regions and explicitly addresses the lack of precisely defined boundaries in many real-world regions.

---

# 72. Deep reconstruction

Naive region model:

```text
World
  ↓ divide into boxes
Regions
  ↓ objects fill boxes
Occupancy
  ↓ touching boxes are connected/near/reachable
Spatial Relations
```

MF5-D replaces it with:

```text
Spatial Domain / Geometry / Frames
              │
              ▼
      Candidate regionalization(s)
              │
      ┌───────┼────────────────────────────────────┐
      │       │                                    │
  Region   Boundary                            Locality relation
 standing  standing                            topology/metric/
      │       │                                 action/visibility
      │       ├─ material/perceptual/
      │       │  formal/institutional/
      │       │  criterion/process
      │       │
      ├───────────────┐
      │               │
 Occupancy        Accessibility/Exclusion
      │               │
      │          configuration obstacles,
      │          barriers, permissions,
      │          reachability constraints
      │
 Visibility / Occlusion / Projection
      │
 Uncertainty / Vagueness / Scale / Encoding
```

The critical change is:

> **Region, boundary, occupancy, accessibility, visibility and locality are separate typed spatial relations/profiles that can be grounded independently and can diverge on the same substrate.**

---

# 73. Deepest MF5-D result

The strongest surviving formulation is:

> **A region is a scope- and granularity-relative standing spatial distinction over a domain; its boundary is the standing interface/separation profile associated with that distinction under a declared topology/criterion, while occupancy, accessibility, visibility and locality are additional relations over the region rather than its definition.**

Compact:

```text
Region
 = Standing Spatial Distinction/Extent
 + Membership/Boundary Profile
 + Geometry/Topology
 + Scale/Scope
```

with:

```text
Occupancy, Accessibility, Visibility, Reachability, Ownership
```

as optional typed relations, not constitutive necessities.

A corresponding anti-inflation rule is:

> **Mathematical selectability or algorithmic segmentability is insufficient for target region/boundary standing.**

---

# 74. MF5-A→D reconstructed picture

```text
MF5-A Space
  = structured spatial possibility domain

MF5-B Geometry
  = typed spatial relation/invariance bundle

MF5-C Description
  = frames/charts/coordinates/transforms over spatial structure

MF5-D Regionalization
  = standing regions/boundaries + typed occupancy/locality/visibility/access relations
```

This gives a much cleaner separation than the naive:

```text
Space = XYZ grid full of objects
```

---

# 75. No MF4 FoundationReopenCondition

MF5-D does not falsify MF4 Composition Foundations.

It strengthens MF4's earlier boundary and spatial-composition results by moving the ontology of region/boundary/locality into MF5. Overlapping regionalizations, continuous fields, vague boundaries and configuration-space obstacle regions remain compatible with MF4's differentiated multiplicity, overlapping decomposition and typed organization standing.

### SD-108

**MF4 remains frozen.**

---

# 76. MF5-E handoff — Perceptual, Body-Centered & Experienced Space

MF5-A→D have deliberately remained general/formal. The next major falsifier is perception itself.

MF5-E should ask:

> **What spatial structure is actually available to an embodied perceiver, and when does perceptual/body-centered space preserve, distort, transform or reconstruct physical spatial relations?**

Required topics/hard cases:

- visual field / visual space vs physical space;
- retinal/image space vs perceived 3D space;
- egocentric/body-centered/head-centered/retinotopic frames;
- allocentric/environmental/intrinsic frames;
- depth from binocular disparity, motion, occlusion and perspective;
- peripersonal vs extrapersonal spatial organization;
- proprioceptive/body schema and reachable space;
- vestibular orientation/gravity reference;
- sensory substitution;
- multisensory spatial calibration;
- remapping/spatial updating across eye/head/body motion;
- spatial constancy and distortion;
- anisotropy/non-Euclidean perceptual geometry;
- object-relative versus world-relative position;
- active sensing;
- spatial attention vs spatial representation;
- perceptual boundaries/segmentation versus target regions;
- uncertainty and priors in depth/layout;
- navigation/place/grid/head-direction evidence without assuming a single canonical neural map.

Central anti-collapse:

```text
Retinal/Image Space ≠ Perceptual Space ≠ Physical Space
Body Space ≠ World Space
Visible ≠ Present
Perceived Distance ≠ Physical Distance
Perceptual Boundary ≠ Material Boundary
Egocentric ≠ Allocentric
Spatial Updating ≠ One Absolute Internal Coordinate Table
```

**Next: MF5-E — Perceptual, Body-Centered & Experienced Space.**
