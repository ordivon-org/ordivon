# Ordivon Media Foundations — MF5-C Frames, Coordinates, Charts & Transformations

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 25 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen; MF5-A Space Ontology and MF5-B Topology, Metric & Geometry complete and provisional.  
**Status:** MF5-C complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-D — Regions, Boundaries, Occupancy, Locality & Spatial Relations.

---

# 0. Purpose

MF5-A established that `Space ≠ coordinates`.
MF5-B established that spatial structure is a typed bundle of topology/metric/projective/affine/Riemannian/action structures rather than one scalar geometry.

MF5-C attacks the next source of collapse:

```text
Locus = Coordinate
Frame = Basis = Chart = Coordinate System
Coordinate Change = Physical Change
Frame Transform = Object Motion
Coordinate Singularity = Geometric Singularity
Pose = Pose Parameter Vector
```

The core problem is epistemic and operational as much as mathematical:

> **How can one spatial state admit multiple valid descriptions, and how do we distinguish a transformation of the description from a transformation of the represented/physical spatial state itself?**

MF5-C uses hard cases from manifolds, Gaussian coordinates, camera geometry, robotics SE(2)/SE(3), homogeneous/projective coordinates and sensorimotor spatial updating.

---

# 1. Locus is not its coordinate tuple

Let `p` be one locus in a spatial domain `X`.
A coordinate description under chart/frame `C` is:

```text
Coord_C(p) = c
```

The same `p` can receive another tuple under another valid description `C'`:

```text
Coord_C'(p) = c'
```

with `c != c'`.

### SC-01

**Locus identity ≠ coordinate-tuple identity.**

### SC-02

**A coordinate is a representation/parameterization of a locus under a declared description system.**

---

# 2. Same coordinate tuple can denote different loci under different systems

The tuple `(1,0)` may mean:

- Cartesian x=1,y=0 relative to one origin;
- Cartesian x=1,y=0 relative to a shifted/rotated frame;
- polar r=1,theta=0;
- a grid cell index;
- an arbitrary map/texture coordinate.

### SC-03

**Coordinate values are semantically incomplete without coordinate-system/frame provenance.**

---

# 3. Coordinate system is not spatial structure

A coordinate system provides a rule for assigning tuples/parameters to loci.
The underlying topology/metric/incidence/action structure can remain fixed while coordinates change.

Einstein's exposition of Gaussian coordinates makes the distinction explicit: arbitrary numerical labels can be assigned to continuum points subject to local continuity conditions, while metric/size relations are encoded separately.

### SC-04

**Coordinate assignment and spatial geometry are separate structures.**

### SC-05

**Coordinate freedom does not imply geometry freedom; many descriptions can refer to one grounded geometry.**

---

# 4. Cartesian vs polar coordinates: simplest hard case

For a locus in the plane:

```text
x = r cos(theta)
y = r sin(theta)
```

The same physical/geometric locus has two different coordinate descriptions.

### SC-06

**Different coordinates ≠ different position.**

Conversely, polar parameters have redundancy/singularity unless domains are restricted:

```text
(r, theta) and (r, theta + 2π)
```

represent the same locus, and at `r=0` the angle is not uniquely defined.

### SC-07

**A raw parameterization need not be globally one-to-one.**

### SC-08

**Parameter singularity/redundancy ≠ spatial singularity.**

The origin of the plane is regular even though polar angle is undefined there.

---

# 5. A chart is stronger/more specific than an arbitrary coordinate code

For manifold-level work, a **chart** is provisionally treated as a local coordinate map:

```text
φ : U ⊂ X -> V ⊂ R^n
```

that is one-to-one with an appropriate inverse and regularity for the structure claimed (homeomorphic for topological manifolds; smoothly compatible for smooth manifolds).

### SC-09

**Chart ≠ arbitrary coordinate feature vector.**

### SC-10

**A valid chart establishes local coordinate access; it does not make `R^n` the intrinsic global identity of the manifold.**

---

# 6. Atlas: global structure can require multiple local descriptions

An atlas is a compatible family of charts whose domains cover the manifold.
On overlaps, transition maps relate coordinate descriptions:

```text
φ_j ∘ φ_i^{-1}
```

### SC-11

**One spatial domain can require multiple coordinate charts without fragmentation of the underlying space.**

### SC-12

**Chart overlap/transition structure is about compatibility of descriptions, not duplication of loci.**

---

# 7. Sphere: coordinate seam/pole ≠ geometric boundary/singularity

Longitude/latitude is useful over much of the sphere but degenerates at the poles and introduces a conventional longitude seam.

The poles are not singular points of the sphere's intrinsic geometry simply because longitude becomes undefined there; the seam is not a physical tear.

### SC-13

**Coordinate singularity ≠ geometric singularity.**

### SC-14

**Coordinate seam ≠ spatial boundary.**

### SC-15

**Failure of one chart does not imply failure of the spatial structure; another chart may cover the locus.**

---

# 8. Frame, basis and chart are distinct

MF5-C uses the following provisional distinctions.

## Basis

An ordered set of vectors spanning a vector/tangent space and providing component decomposition.
A basis by itself need not specify an affine origin.

## Affine frame

An origin/anchor plus a basis/direction structure, sufficient to coordinate affine locations.

## Reference frame

A broader relational scaffold relative to which positions/orientations/poses are expressed. It may be physically attached to a body/sensor, environmentally anchored, representationally designed or conventionally established. It can include origin, orientation, handedness, units, attachment and semantic authority.

## Chart

A local coordinate map from a manifold region to a numerical domain.

## Coordinate system

A broader engineering/mathematical convention assigning coordinates, potentially global or local, and not necessarily identical to a single manifold chart.

### SC-16

```text
Basis ≠ Affine Frame ≠ Reference Frame ≠ Chart ≠ Coordinate System
```

They can coincide operationally in simple Cartesian cases but are not ontologically identical.

---

# 9. Observer is not a reference frame

A human, robot or camera can use several frames:

- retinal/camera frame;
- body frame;
- tool frame;
- object-centered frame;
- local map frame;
- world/environment frame.

A frame can also persist as a standing convention when no observer is currently using it.

### SC-17

**Observer/agent ≠ frame.**

### SC-18

**One observer/system may recruit multiple spatial frames simultaneously or sequentially.**

---

# 10. Reference-frame standing is typed

A frame can gain standing through:

- physical attachment to a body/sensor;
- engineered design/specification;
- environmental landmarks;
- perceptual/sensorimotor organization;
- representational convention;
- formal construction.

### SC-19

**Reference-frame dependence does not make spatial claims arbitrary.**

### SC-20

**A frame need not be physically privileged to be operationally or conventionally objective.**

---

# 11. Coordinate choice can be arbitrary while the spatial claim remains objective

One may choose Cartesian or polar coordinates merely for convenience while making claims about the same grounded Euclidean plane.

### SC-21

**Analyst coordinate convenience ≠ analyst creation of the underlying target geometry.**

This sharpens MF5-A/B anti-inflation:

```text
Target spatial structure standing
        ≠
standing of one coordinate description
```

---

# 12. Passive transformation: same locus/state, different description

Suppose the same geometric point is expressed in frames `A` and `B`:

```text
p_B = T_BA p_A
```

Here the represented point need not move. We changed the coordinates used to describe the same point relative to another frame.

### SC-22

**Passive coordinate/frame transformation can change all component values while leaving the underlying locus unchanged.**

---

# 13. Active transformation: spatial state changes relative to fixed frame

If a rigid body/point is actually rotated/translated while a chosen frame remains fixed:

```text
p'_A = T_active p_A
```

then the underlying relative spatial relation changes.

### SC-23

**Active spatial transformation ≠ passive change of description.**

---

# 14. Same algebra can support active/passive interpretations

Rotation/rigid-transform matrices can appear in both active and passive formulas. Depending notation/convention, the matrix used to rotate an object and the matrix used to express coordinates in a rotated frame are inverses/transposes of one another or otherwise dual descriptions.

### SC-24

**Matrix shape/values alone do not specify transformation semantics.**

Every transform claim must declare:

- source frame;
- target frame;
- mapped entity type;
- active/passive semantics;
- direction;
- convention.

---

# 15. OpenCV camera geometry is a hard engineering case

OpenCV's calibration model distinguishes object/world/camera frames and uses homogeneous transforms of the form:

```text
X_c = ^cT_o X_o
^cT_o = [ ^cR_o  ^ct_o
           0        1  ]
```

The same 3D point receives different coordinates in object and camera frames. OpenCV also explicitly treats `(R,t)` as a change of basis while noting its pose interpretation.

### SC-25

**Frame transform ≠ point identity change.**

### SC-26

**Pose relation and coordinate-change operator are tightly dual but must not be conflated without a declared convention.**

---

# 16. Position, orientation and pose remain separate

A rigid-body pose combines translation/position and orientation.

```text
Pose ∈ SE(3)
```

in a common robotics formulation, while orientation alone lies in a rotation group such as `SO(3)`.

### SC-27

`Position ≠ Orientation ≠ Pose` remains frozen provisionally from MF5-A and is strengthened here.

### SC-28

**Pose is a relation between frames/configurations, not merely a six-number vector.**

---

# 17. SE(3) gives a rigorous composition structure for rigid poses

A homogeneous rigid transformation can be written:

```text
T = [R t
     0 1]
```

with `R ∈ SO(3)` and translation `t`.

Solà, Deray & Atchuthan explicitly treat `SO(3)` and `SE(3)` as Lie groups/manifolds and distinguish group elements from tangent-space/vector coordinates used for local increments and uncertainty.

### SC-29

**Rigid pose manifold/group element ≠ local tangent/vector parameterization.**

### SC-30

**A 6-DoF pose does not imply one globally canonical `R^6` coordinate representation.**

---

# 18. Group action differs from group element identity

A pose/rotation element can act on points/vectors:

```text
T · p
```

The group element and the transformed point are different ontological roles.

### SC-31

**Transformation operator ≠ transformed spatial entity.**

This prevents `pose matrix = point coordinates` collapse.

---

# 19. Transform composition is ordered

For frame chain:

```text
X_w = ^wT_c ^cT_o X_o
```

the intermediate frame semantics and multiplication order matter.

Rigid transformations in 3D are generally noncommutative:

```text
T1 T2 != T2 T1
```

### SC-32

**Transform composition order is constitutive of the resulting spatial relation.**

### SC-33

**A frame graph/path is not an unordered bag of transforms.**

---

# 20. Inverse transform reverses frame direction

If:

```text
X_B = ^BT_A X_A
```

then:

```text
X_A = (^BT_A)^-1 X_B
```

### SC-34

**Transform direction is first-class semantic content.**

Many engineering errors arise not from bad numbers but from applying a correct transform in the wrong direction.

---

# 21. Points and free vectors transform differently under translation

An affine point position changes under translation; a free direction vector does not acquire the same translation offset.

For rigid transformations:

```text
point:    p' = R p + t
direction: v' = R v
```

### SC-35

**Point ≠ displacement/direction vector.**

### SC-36

**Homogeneous-coordinate conventions must preserve entity type; appending `1` versus `0` encodes different affine roles.**

---

# 22. Basis change and vector change must be separated

A geometric vector can remain the same while its components change because the basis changes.

Conversely, components can change because the vector itself changes while basis stays fixed.

### SC-37

**Vector-component change ≠ geometric-vector change.**

### SC-38

**Coordinate/component invariance is not required for geometric invariance.**

---

# 23. Covariance/contravariance is fundamentally a bookkeeping discipline for geometric identity

Without freezing full tensor calculus into MF5, the foundational point survives:

> Components of geometric objects transform according to their role so that coordinate-independent relations remain well-defined.

### SC-39

**Transformation law is part of the representational type of a coordinate quantity.**

A scalar, vector, covector, tensor, point and pose do not all transform the same way.

---

# 24. Coordinate-invariant and frame-dependent quantities are distinct

Examples:

- a vector's coordinate components are frame/basis dependent;
- Euclidean norm is invariant under rigid rotation;
- `left of` may depend on viewer/body frame;
- incidence may survive projective transform;
- metric length does not survive arbitrary affine/projective transforms.

### SC-40

**`Invariant` is always relative to a transformation family and quantity type.**

This directly inherits MF5-B.

---

# 25. Homogeneous projective coordinates break coordinate uniqueness by design

In projective geometry, nonzero scalar multiples can represent one projective point:

```text
P_h ~ λ P_h, λ != 0
```

OpenCV's projective camera model explicitly uses homogeneous coordinates and scale ambiguity in projection.

### SC-41

**Coordinate vector uniqueness is not universal; some coordinate systems deliberately encode equivalence classes.**

### SC-42

**Homogeneous coordinate representation ≠ ordinary injective manifold chart.**

This is an important type distinction.

---

# 26. Projection maps can be many-to-one

A pinhole camera maps all 3D points on the same camera ray to the same normalized image direction before depth/scale is recovered.

### SC-43

**Projected image coordinates underdetermine 3D locus without additional depth/scene constraints.**

This carries MF1 aliasing/non-identifiability into frame/coordinate geometry.

---

# 27. Camera intrinsics and extrinsics are different transformation layers

Extrinsics relate coordinate frames/poses:

```text
world/object -> camera
```

Intrinsics map camera-frame geometry to image/pixel coordinates under a camera model.

### SC-44

**Frame transformation/extrinsics ≠ projection/intrinsics.**

### SC-45

**Image coordinate frame ≠ camera 3D frame ≠ world/object frame.**

---

# 28. Calibration is evidence for a transformation, not the transformation's ontology

A camera-to-body transform may be:

- physically fixed by construction;
- specified by CAD/design;
- estimated by calibration;
- updated online;
- uncertain.

### SC-46

**True/standing frame relation ≠ estimated transform ≠ calibration procedure.**

### SC-47

**Calibration quality is epistemic evidence about a transform claim, not the constitutive definition of frame relation.**

This parallels MF3/MF4 ontology/evidence separation.

---

# 29. Transform provenance is first-class

A numeric transform without provenance can be dangerously ambiguous.

MF5-C requires transform evidence to track, where relevant:

- source frame;
- target frame;
- timestamp/validity interval;
- authority/provider;
- calibration/design source;
- units/convention;
- uncertainty;
- estimate version.

### SC-48

**Transform provenance is separate from transform value.**

---

# 30. Frame authority can conflict

Two sensors/estimators may provide incompatible estimates of the same nominal frame relation.

### SC-49

**Same frame names do not guarantee same transform truth.**

### SC-50

**Frame identity, transform estimate and transform authority are separate operational variables.**

---

# 31. Stale transform is a distinct failure mode

A frame relation can be correct at `t0` and wrong at `t1` if the body/sensor/frame moves or calibration changes.

### SC-51

**Spatial transform claims can be time-indexed even though MF5 does not yet provide a full ontology of time/dynamics.**

Time dependence is recorded here but deferred structurally to MF6/MF7.

---

# 32. Moving frame ≠ coordinate relabeling

If a camera physically rotates, its frame changes relative to the world.
If we merely switch the coordinate convention used to describe the same fixed camera, the physical camera/world relation does not change.

### SC-52

**Physical frame motion and passive coordinate reparameterization are distinct.**

---

# 33. Active sensing links the two without collapsing them

In MF2 active perception, moving eye/head/camera changes the observation operator and therefore future evidence.

### SC-53

**A frame can physically move as part of sensing while coordinate transformations are simultaneously required to compare observations across frame states.**

The existence of both processes is exactly why active/passive semantics must remain explicit.

---

# 34. Duhamel–Colby–Goldberg provide a biological hard case

Their 1992 experiments show parietal neurons transiently update receptive-field/remembered-stimulus relations around intended eye movements, supporting the idea that useful spatial representation must remain coordinated across changing retinal coordinates rather than treating retinal coordinate identity as world-location identity.

### SC-54

**Retinal coordinate change across eye movement ≠ target-location annihilation/recreation.**

### SC-55

**Spatial updating can preserve task-relevant location across changing sensor-centered coordinates.**

This does not prove one universal allocentric neural frame; it supports transformation/updating among changing spatial descriptions.

---

# 35. Eye position can modulate retinotopic coding

Andersen, Essick & Siegel's 1985 recordings reported systematic modulation of retinotopic receptive-field responses by gaze angle.

### SC-56

**Spatial coding can jointly depend on stimulus location in one frame and state of another reference variable.**

This is evidence against a simplistic `one neuron = one absolute coordinate` ontology.

---

# 36. Egocentric, allocentric and intrinsic frames remain typed alternatives

MF4-F already established viewer-centered, object/intrinsic and world/environment-centered frame distinctions.
MF5-C strengthens them as **different reference relations**, not merely different coordinate units.

### SC-57

```text
Egocentric ≠ Allocentric ≠ Object/Intrinsic-centered
```

### SC-58

**Cross-frame transformation may preserve some spatial content while changing frame-relative predicates such as left/right/front/behind.**

---

# 37. Frame transformation does not imply a universal intermediate frame

A system may transform between several task-relevant frames through distributed or learned computations without constructing one explicit globally canonical coordinate table.

### SC-59

**Multiple-frame competence ≠ evidence for one privileged internal Cartesian frame.**

This preserves MF2 implementation neutrality.

---

# 38. Pose parameterization is not pose ontology

A rotation/pose can be encoded by:

- rotation matrix;
- axis-angle;
- quaternion;
- Euler-angle convention;
- local Lie-algebra/tangent coordinates;
- homogeneous rigid transform.

These representations have different redundancy, singularity and numerical properties.

### SC-60

**Pose ≠ any one pose parameterization.**

### SC-61

**Parameterization failure/singularity can occur while the underlying pose remains regular.**

---

# 39. Local vector coordinates on SO(3)/SE(3) are powerful but local/representation-relative

Solà et al. distinguish the nonlinear group/manifold from tangent vector spaces used for local increments and uncertainty.

### SC-62

**Local tangent coordinates ≠ global group identity.**

### SC-63

**Euclidean operations on local perturbation coordinates do not license treating the global pose manifold as ordinary `R^n`.**

---

# 40. Coordinate dimension and representation size diverge again

An `SO(3)` rotation has 3 degrees of freedom but can be represented by a 3x3 matrix with 9 entries under orthogonality/determinant constraints, or by other parameterizations with different stored component counts.

An `SE(3)` pose has 6 DoF but common homogeneous representation uses 16 matrix entries with structural constraints.

### SC-64

**Stored parameter count ≠ intrinsic degrees of freedom/dimension.**

This strengthens MF5-A dimensionality discipline.

---

# 41. Coordinate periodicity is not spatial periodicity

Angle coordinates can satisfy:

```text
theta ~ theta + 2π
```

without the underlying spatial domain being duplicated.

### SC-65

**Periodic/redundant coordinate labels do not imply multiple spatial states.**

---

# 42. Handedness/axis convention is separate from frame identity

Two coordinate conventions can describe the same physical scene using different axis orientations/handedness/unit conventions.

### SC-66

**Frame semantics must include coordinate convention when sign/orientation interpretation depends on it.**

### SC-67

**Numerically plausible coordinates under the wrong handedness/axis convention can represent the wrong spatial relation.**

---

# 43. Units are not geometry but are part of coordinate interpretation

The same metric relation can be expressed in meters, centimeters or normalized units.

### SC-68

**Unit conversion ≠ spatial transformation.**

### SC-69

**Unit mismatch is a representation/measurement failure, not evidence that the underlying geometry changed.**

---

# 44. Frame-name equality is weak evidence

`world`, `map`, `camera`, `base`, `local`, `screen` are labels.

### SC-70

**Frame names require standing definitions/authorities; string equality alone does not establish coordinate compatibility.**

---

# 45. Gauge/reparameterization freedom must be typed

MF5-C does not freeze a universal physics notion of gauge, but retains a general principle:

> Multiple parameter descriptions may encode the same spatial/representational state because some coordinate degrees of freedom are descriptive redundancy rather than target distinctions.

### SC-71

**Description redundancy ≠ target-state multiplicity.**

### SC-72

**Not every frame choice is pure gauge: a body-attached versus world-attached frame can change operational content even when both validly describe the same underlying scene.**

---

# 46. Coordinate invariants must be distinguished from physical invariants

A formula may be invariant under coordinate reparameterization because it denotes one geometric relation.
A physical system may additionally possess symmetry under actual transformations such as rotation/translation.

### SC-73

**Coordinate invariance ≠ physical symmetry.**

### SC-74

**Passive descriptive equivalence and active symmetry transformation are separate claims.**

---

# 47. Transformation equality can be scope-relative

Two transform estimates may differ numerically yet be equivalent for a coarse task; conversely tiny differences can be decisive near collision/occlusion/topological thresholds.

### SC-75

**Transform error must be evaluated against the claimed spatial/action profile rather than one universal matrix norm.**

---

# 48. Uncertainty over frames/transforms is typed

A system can be uncertain about:

- translation;
- orientation;
- scale;
- time alignment;
- frame correspondence;
- calibration parameters;
- transform authority;
- chart branch/wrapping.

### SC-76

**Frame/transform uncertainty is not one universal covariance scalar.**

### SC-77

**Coordinate covariance matrices are parameterization/frame dependent evidence objects, not intrinsic uncertainty ontology by themselves.**

---

# 49. Rotation/pose uncertainty exposes non-Euclidean state structure

Naively adding large orientation errors as ordinary Euclidean vectors can ignore the manifold/group structure of orientation.
Robotics Lie-group methods instead commonly express small perturbations in local tangent coordinates and map them to/from the group.

### SC-78

**Uncertainty representation must respect the state space's transformation/manifold structure at the claimed scope.**

---

# 50. Cross-frame correspondence is a separate inference problem

To transform coordinates across frames one must know which locus/entity in one description corresponds to which in the other and the frame relation itself.

### SC-79

**Coordinate transformation presupposes or jointly estimates correspondence/transform structure; it does not create correspondence automatically.**

This links back to MF2 tracking/correspondence and MF3 representation grounding.

---

# 51. Coordinate change can preserve spatial structure selectively

Cartesian↔polar can preserve full Euclidean locus identity where mapping is valid.
Projective coordinates preserve projective structure while discarding metric scale under projection.
Map projection may preserve selected local angles/areas/topology but distort others.

### SC-80

**A coordinate/representation transformation must declare which spatial structure is preserved, approximated or lost.**

---

# 52. Reparameterization can alter numerical conditioning without altering geometry

Different coordinate systems can make estimation/optimization easier or harder despite representing the same spatial structure.

### SC-81

**Representational conditioning/computational convenience ≠ target spatial quality.**

This mirrors MF3-C `geometry as code-consumer interface` while keeping target geometry separate.

---

# 53. Coordinates can themselves become systemically meaningful

Although coordinates are generally representational, a designed system can recruit coordinate values operationally:

- grid address determines memory/cell access;
- UI screen coordinate determines hit testing;
- robot map coordinates determine command targets.

### SC-82

**Coordinate representation can acquire operational standing without becoming intrinsic physical geometry.**

Thus `coordinate is merely arbitrary` is also too strong.

---

# 54. Coordinate-standing and spatial-structure-standing must be separated

Define provisionally:

```text
SpatialStructureStanding(S, X | Σ)
CoordinateStanding(C, S | Practice/System)
```

`S` can be target-real while `C` is analyst convenience; `C` can also become conventionally/systemically standing through design/protocol use.

### SC-83

**Target geometry standing ≠ coordinate-system standing.**

---

# 55. Frame-standing and transform-standing must also be separated

A frame can have standing (`camera`, `body`, `object`) even while the current transform between two frames is unknown/uncertain.

### SC-84

**Frame existence/identity ≠ known frame transform.**

A transform estimate can exist numerically for two analyst-created frames whose target standing is weak.

### SC-85

**Transform availability ≠ frame/target ontology validity.**

---

# 56. Provisional FrameProfile

```text
FrameProfile = <
  FrameId,
  Domain/Relata,
  StandingRoute,
  Anchor/Attachment,
  Origin/LocusAnchor,
  Orientation/BasisProfile,
  Handedness/AxisConvention,
  Units/Scale,
  Parent/ReferenceRelations,
  CoordinateConvention,
  Authority/Provenance,
  Time/Validity,
  Uncertainty,
  Scope
>
```

Not every frame requires every field, but ambiguous engineering frames normally need most of the semantic/provenance fields.

---

# 57. Provisional ChartProfile

```text
ChartProfile = <
  Domain U,
  Map φ : U -> V,
  CoordinateCodomain V,
  Inverse/Injectivity Conditions,
  Regularity : topological/smooth/etc.,
  Excluded/Singular Set,
  OverlapTransitionMaps,
  Orientation/BranchConvention,
  Provenance,
  Scope
>
```

### SC-86

**Chart validity is local/structural, not merely `function returns n numbers`.**

---

# 58. Provisional CoordinateClaim

```text
CoordinateClaim = <
  Entity/Locus,
  CoordinateTuple,
  Frame/Chart/CoordinateSystem,
  EntityType : point/vector/pose/etc.,
  Units/Scale,
  Convention/Handedness,
  Time,
  Uncertainty,
  Provenance,
  Scope
>
```

### SC-87

**Bare coordinate tuples should not be treated as self-describing spatial facts.**

---

# 59. Provisional TransformClaim

```text
TransformClaim = <
  SourceFrame,
  TargetFrame,
  TransformType : rigid/affine/projective/chart-transition/etc.,
  Map/Parameters,
  Direction,
  ActiveOrPassiveSemantics,
  MappedEntityType,
  PreservedStructure/Invariants,
  Time/Validity,
  Authority/Provenance,
  Uncertainty,
  Scope
>
```

### SC-88

**A transform matrix/object without this semantic envelope is under-specified.**

---

# 60. Provisional transformation taxonomy

MF5-C distinguishes:

## Reparameterization / chart change

Same locus/state, different numerical description.

## Frame change / passive transform

Same geometric entity, coordinates expressed relative to another frame.

## Active geometric transform

Entity/configuration changes relative to a held-fixed frame.

## Physical frame motion

Reference frame itself changes relation to another standing frame.

## Projection

Higher-dimensional/scene structure mapped to lower-dimensional/other representational space, often many-to-one.

## Calibration transform estimate

Epistemic estimate of a standing relation.

## Symmetry transformation

Active transformation preserving selected system/geometry profile.

### SC-89

**These transformation types can use similar algebra while carrying different semantics.**

---

# 61. Failure taxonomy

## Frame mismatch

Coordinates interpreted in the wrong reference frame.

## Transform inversion error

Correct transform applied in the wrong direction.

## Active/passive confusion

Object motion mistaken for coordinate change or vice versa.

## Basis/point confusion

Vector component change interpreted as point displacement.

## Point/vector homogeneous-role error

Translation incorrectly applied/omitted due wrong homogeneous entity type.

## Handedness/axis mismatch

Right/left-handed or axis-direction conventions silently mixed.

## Unit mismatch

Meters/centimeters/degrees/radians/etc. conflated.

## Stale transform

Transform valid for an earlier frame state/time used as current.

## Authority conflict

Different providers claim inconsistent transforms under same names.

## Calibration error

Estimated extrinsic/frame relation is biased/uncertain.

## Coordinate singularity misread as geometric singularity

Polar origin, chart poles/seams or pose parameter singularity treated as target pathology.

## Parameter wrapping/aliasing

Equivalent angle/projective coordinate representatives treated as different states.

## Transform-order error

Noncommuting transforms composed in wrong order.

## Projection inversion overclaim

2D image coordinate treated as unique 3D locus without depth constraints.

## Intrinsic/extrinsic confusion

Camera intrinsics mistaken for frame transform, or vice versa.

## Pose/parameterization collapse

Stored vector/matrix entries treated as unconstrained Euclidean state.

## Uncertainty laundering

Coordinate covariance/fit score reported as intrinsic spatial certainty independent of frame/parameterization.

## Frame-name reification

String label assumed to define actual spatial relation.

### SC-90

**Frame/coordinate error is a typed family; one matrix residual cannot universally summarize correctness.**

---

# 62. Strongest non-collapse stack after MF5-C

```text
Locus
 ≠ Coordinate Tuple
 ≠ Coordinate System
```

```text
Basis
 ≠ Affine Frame
 ≠ Reference Frame
 ≠ Chart
 ≠ Coordinate System
 ≠ Observer
```

```text
Spatial Structure Standing
 ≠ Frame Standing
 ≠ Coordinate-System Standing
 ≠ Transform Estimate
```

```text
Coordinate Change
 ≠ Frame Change
 ≠ Active Object Transform
 ≠ Physical Frame Motion
 ≠ Projection
```

```text
Coordinate Singularity
 ≠ Geometric Singularity
```

```text
Point
 ≠ Vector
 ≠ Orientation
 ≠ Pose
 ≠ Transform Operator
```

```text
Pose
 ≠ Pose Parameterization
 ≠ Local Tangent Increment
```

```text
Frame Transform / Extrinsics
 ≠ Camera Intrinsics / Projection
```

```text
Transform Value
 ≠ Transform Provenance
 ≠ Transform Uncertainty
 ≠ Transform Authority
```

```text
Coordinate Invariance
 ≠ Physical Symmetry
```

---

# 63. Claims rejected by MF5-C

Reject as universal foundational claims:

- a point/locus is identical to its coordinate tuple;
- same coordinates mean same position without frame provenance;
- different coordinates mean different position;
- frame, basis, chart and coordinate system are interchangeable;
- an observer has one canonical reference frame;
- coordinate systems are intrinsic parts of target geometry whenever they are useful;
- coordinate arbitrariness makes spatial geometry arbitrary;
- coordinate change is physical movement;
- physical frame movement is merely re-labeling;
- one transform matrix carries unambiguous semantics without source/target/direction convention;
- frame transform and pose are interchangeable without declaring viewpoint/convention;
- transform composition order is irrelevant;
- points and vectors transform identically under translation;
- component change implies geometric-vector change;
- coordinate singularity implies geometric singularity;
- a manifold/global space requires one global chart;
- longitude seam/polar singularity is a physical boundary/pathology;
- homogeneous coordinates uniquely label projective points;
- projective image coordinate uniquely identifies a 3D point;
- camera intrinsics and frame extrinsics are the same transform layer;
- calibration procedure is the constitutive frame relation;
- frame name uniquely determines transform truth;
- one pose parameterization is the pose itself;
- 6 pose DoF means the global pose domain is ordinary unconstrained `R^6`;
- stored matrix/vector component count equals intrinsic dimension;
- angle wrapping creates multiple physical orientations;
- local tangent perturbation coordinates are globally identical to the Lie group/manifold;
- coordinate invariance and physical symmetry are the same claim;
- one covariance matrix is coordinate-independent pose uncertainty;
- multiple frames imply one hidden absolute internal frame;
- coordinate representation can never have operational standing.

---

# 64. Primary/original/official anchors

- **Albert Einstein (1916)**, *Relativity: The Special and General Theory*, especially sections on Gaussian coordinates and general relativity. Gaussian coordinates are arbitrary numerical assignments to continuum points subject to neighboring-point continuity, while metric size relations are specified separately; multiple coordinate systems can describe the same continuum.
- **OpenCV official calib3d documentation**, Camera Calibration and 3D Reconstruction. Explicitly distinguishes object/world/camera frames, homogeneous frame transforms `X_c = ^cT_o X_o`, transform chaining/inversion, homogeneous projective scale ambiguity, and camera intrinsic versus extrinsic transformation layers.
- **Joan Solà, Jeremie Deray & Dinesh Atchuthan (2018/2021)**, *A micro Lie theory for state estimation in robotics*, arXiv:1812.01537. Distinguishes Lie group/manifold elements (`SO(3)`, `SE(3)`) from local tangent/vector coordinates, group actions and uncertainty/increment representations.
- **J. R. Duhamel, C. L. Colby & M. E. Goldberg (1992)**, `The updating of the representation of visual space in parietal cortex by intended eye movements`, *Science* 255, 90–92, DOI 10.1126/science.1553535. Shows predictive/remapped spatial response around eye movements and updating of remembered retinal locations.
- **R. A. Andersen, G. K. Essick & R. M. Siegel (1985)**, `Encoding of spatial location by posterior parietal neurons`, *Science* 230, 456–458, DOI 10.1126/science.4048942. Shows gaze-angle modulation of retinotopic visual responses, supporting distributed/frame-state-dependent spatial coding.

---

# 65. Deep reconstruction

Naive model:

```text
Space
  ↓ choose XYZ
Coordinates
  ↓ multiply matrix
Transform
  ↓
New position
```

MF5-C replaces it with:

```text
Spatial domain / loci / geometry
             │
             ├─ may admit many charts / parameterizations
             ├─ may be referenced by many frames
             ├─ frame may have basis/origin/attachment/convention
             ├─ same locus has different coordinate tuples
             ├─ same frame relation can be estimated with uncertainty
             │
             ▼
      Description Layer
   <Frame, Chart, Coordinates,
    Entity Type, Convention,
    Provenance, Uncertainty>
             │
        transformation
             │
    ┌────────┼──────────────┐
    │        │              │
 passive   active        projection
 change    spatial       / observation
 of desc.  change
    │        │              │
    └────────┼──────────────┘
             ▼
  declared preserved/lost structure
```

The decisive move is:

> **Spatial state and spatial description are separate. Transformations must state whether they alter the target relation or only the description, and must carry source/target frame, entity type, direction, invariants, provenance and uncertainty.**

---

# 66. Deepest MF5-C result

The strongest surviving compact formulation is:

```text
Coordinates are typed representations of loci/configurations.
Frames establish reference relations.
Charts provide local coordinate access to structured domains.
Transforms relate descriptions and/or spatial states.
The same algebra does not determine which semantic role is being performed.
```

Therefore:

> **A coordinate/frame description is not the spatial state itself. Spatial correctness requires preservation of the relevant target structure under an explicitly typed transformation semantics.**

A provisional identity rule is:

```text
SameSpatialState
  can coexist with DifferentCoordinates
  when a valid passive/chart transformation preserves the claimed structure.
```

and:

```text
SameCoordinates
  do not imply SameSpatialState
  when frame/chart/convention differs.
```

---

# 67. MF5-C impact on the MF5-A ontology

MF5-A provisional core was:

```text
Space
 ≈ Possibility Domain
 + Loci / Regions / Configurations
 + Spatial Standing
 + Typed Spatial Relation Structure
 + Scope
```

MF5-B strengthened `Typed Spatial Relation Structure` into a multi-axis geometry/equivalence bundle.

MF5-C now adds a strict outer descriptive layer:

```text
Spatial Structure
       ≠
Frame/Chart/Coordinate Description
```

This means coordinates, charts and frames should not be added to the constitutive minimal definition of Space merely because they are indispensable engineering interfaces.

They belong to a **spatial access/description/relational-reference layer** over spatial structure.

---

# 68. No MF4 reopen condition

MF5-C does not falsify MF4 Composition Foundations.

Frame graphs, chart atlases, transform chains and coordinate systems can themselves form compositions under MF4, but the existence of compositional organization does not change the MF5 distinction between target spatial structure and its descriptions.

### SC-91

**MF4 remains frozen.**

---

# 69. MF5-D handoff — Regions, Boundaries, Occupancy, Locality & Spatial Relations

MF5-A/B/C now establish domain, geometry and descriptive access, but several basic spatial predicates remain underdefined.

MF5-D must attack:

- point/locus vs region;
- interior/exterior/boundary;
- open/closed boundary semantics;
- contact vs overlap vs containment;
- occupancy vs region identity;
- empty/negative space;
- obstacle vs forbidden configuration region;
- local neighborhood vs metric-near vs interaction-local;
- adjacency vs connectivity;
- visibility/occlusion versus occupancy;
- field regions and threshold-dependent boundaries;
- fuzzy/probabilistic regions;
- multiscale boundaries;
- boundary ownership;
- spatial granularity and coarse-graining;
- region correspondence across transforms;
- spatial relation calculi without overclaiming one universal ontology;
- place/territory/zone as later semantic extensions rather than raw region primitives.

Central attack:

```text
Region ≠ Occupant
Boundary ≠ Material Edge
Inside ≠ Part-of
Contact ≠ Overlap
Adjacency ≠ Connectivity
Near ≠ Reachable
Empty ≠ Spatially Irrelevant
Visibility ≠ Occupancy
```

MF5-D must also continue the anti-inflation question:

> When is a region/boundary/locality relation target-standing rather than induced only by analyst threshold, segmentation or coordinate discretization?

**Next: MF5-D — Regions, Boundaries, Occupancy, Locality & Spatial Relations.**
