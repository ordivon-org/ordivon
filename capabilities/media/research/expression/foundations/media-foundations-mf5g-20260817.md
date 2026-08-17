# Ordivon Media Foundations — MF5-G Representational, Map, Diagram & Virtual Space

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 29 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3 Representation Foundations v1 frozen; MF4 Composition Foundations v1 frozen; MF5-A→F complete and provisional.  
**Status:** MF5-G complete and PROVISIONAL. Space Foundations remain UNFROZEN.  
**Next:** MF5-H — Computational, Latent, Semantic & Abstract Spatial Standing.

---

# 0. Purpose

MF5-A→F distinguish physical, geometric, descriptive, regional, perceptual and action spatial structures.

MF5-G asks the representational/design hard case:

> **When does a map, diagram, screen layout, game world, virtual environment or AR layer possess spatial standing, and how should its own vehicle/display geometry be separated from the geometry, topology or action structure it represents or computationally enacts?**

The dangerous collapses are:

```text
Map Space = Target Space
Vehicle Geometry = Represented Geometry
Screen Space = World Space
Document Structure = Layout Geometry
Rendered Geometry = Collision/Action Geometry
Virtual Space = Physical Space
AR Coordinates = Physical Location Identity
Projection Distortion = Total Spatial Failure
Responsive Reflow = Content/Target Change
Spatial Metaphor = Target Spatial Standing
Minimap Geometry = World Geometry
Portal Adjacency = Physical Nearness
```

MF5-G extends MF3 Representation: a spatial representation has at least two potentially independent spatial profiles — the geometry of the vehicle itself and the geometry/relations attributed to the represented target.

---

# 1. Representation can have its own vehicle space

A map, diagram, display or layout has a material/digital vehicle with its own loci, regions, order, distances and adjacency.

Examples:

- ink positions on paper;
- pixels/window coordinates;
- SVG coordinates;
- DOM/CSS layout boxes;
- minimap screen positions;
- mesh vertices in a rendered view.

### SG-01

**Representational vehicle space can possess spatial standing independently of the represented target.**

### SG-02

**Vehicle locus ≠ represented target locus.**

---

# 2. MF3 grounding binds vehicle distinctions to target distinctions

Under MF3, spatial representation requires a grounded standing-in relation between vehicle structure and target spatial distinctions/possibilities.

### SG-03

**Vehicle spatial structure ≠ represented spatial content.**

### SG-04

A vehicle can be spatial without representing space, and can represent space while preserving only selected vehicle/target relations.

---

# 3. One map supports two geometries at minimum

For a map `M` representing target `T`:

```text
G_vehicle(M)
G_target(T)
K : selected vehicle relations -> selected target relations
```

### SG-05

**Map geometry ≠ target geometry.**

### SG-06

**Spatial representation quality must be evaluated through the declared representational key `K`, not raw vehicle-target coordinate equality.**

---

# 4. Beck Tube Map is a decisive selective-fidelity hard case

Transport for London's own history notes that earlier public transport maps emphasized geographic distance/accuracy and were difficult to read; Harry Beck's redesign used straight horizontal/vertical lines, 45-degree angles and clear interchange points to improve network usability.

### SG-07

**Metric/geographic distortion can coexist with high route/topological representation value.**

### SG-08

**Spatial fidelity is typed: station identity, adjacency, interchange and route order can be preserved while physical distance, direction and scale are distorted.**

---

# 5. A schematic map is not a failed geographic map by default

If its declared function is navigation through network topology, exact geographic angle/length can be irrelevant or harmful.

### SG-09

**Schematic distortion ≠ representational error unless it violates the declared key/task.**

### SG-10

**More metric realism can reduce task utility while preserving more physical geometry.**

This parallels MF5-E/F sufficiency-vs-veridicality distinctions.

---

# 6. Cartographic projection proves that preservation profiles trade off

USGS projection references distinguish conformal, equal-area, equidistant and other projections because planar projections preserve different spatial properties.

### SG-11

**Projection cannot be assessed by one scalar `accuracy` independent of preserved property.**

### SG-12

`AngleFidelity ≠ AreaFidelity ≠ DistanceFidelity ≠ DirectionFidelity ≠ TopologicalFidelity`.

---

# 7. Projection is a transformation between spatial descriptions with selective loss/distortion

A map projection maps a curved target surface/model to a planar vehicle.

### SG-13

**Projection ≠ coordinate relabeling when geometric invariants are changed.**

### SG-14

**Projection can preserve one structure class while distorting another.**

This is MF5-B invariance discipline applied to representation.

---

# 8. Topology can survive large metric distortion

A transit/network map may preserve connectivity and route order through severe changes in metric length/angle.

### SG-15

**Represented topology ≠ represented metric geometry.**

### SG-16

A map can be topologically adequate and metrically misleading simultaneously.

---

# 9. Diagram space is not automatically physical space

A circuit diagram, family tree, flowchart or causal graph uses spatial layout to express relations that need not be physical spatial relations.

### SG-17

**Diagram vehicle space ≠ target physical space.**

### SG-18

**Spatially encoded relation ≠ spatial target relation.**

For example, left-to-right ordering can stand for temporal/causal/logical order rather than physical left-right.

---

# 10. Diagrammatic spatial convention can have representational standing

The fact that target relation is nonspatial does not make diagram space arbitrary: conventions such as containment boxes, arrows, alignment, lanes and proximity can be systemically meaningful.

### SG-19

**Vehicle spatial standing can encode nonspatial semantic/structural content.**

### SG-20

**Representational use of space ≠ claim that the target itself is spatial.**

This is central for later MF5-H semantic/latent spaces.

---

# 11. Spatial metaphor must be separated from target spatial standing

Terms like `idea space`, `political landscape`, `topic region` may use spatial language or visual embeddings.

### SG-21

**Spatial vocabulary/metaphor ≠ target spatial ontology.**

### SG-22

A metaphor can guide representation or reasoning without establishing topology/metric/action relations in the target domain.

---

# 12. A scatterplot has unquestionable vehicle geometry but only conditionally target geometry

Points have screen/data-coordinate positions and Euclidean distances in the plot.

### SG-23

**Plot geometry has formal/vehicle standing even if the represented entities lack target spatial standing.**

### SG-24

Inferring target nearness from plotted nearness requires the axes/embedding key and target semantics to support that interpretation.

---

# 13. Screen space is a real representational space

A screen/window supplies loci, extents, overlap, clipping, z-order/hit-test relations and pixel/window coordinates.

### SG-25

**Screen/display space has designed/operational spatial standing.**

### SG-26

**Screen spatial standing does not make it identical to world/scene space.**

---

# 14. Rendering pipelines explicitly separate coordinate spaces

Khronos OpenGL material distinguishes object coordinates, eye coordinates, clip coordinates, normalized device coordinates and window coordinates; the viewport maps NDC to window space.

### SG-27

```text
Object/Model Space
 ≠ Eye/View Space
 ≠ Clip Space
 ≠ NDC
 ≠ Window/Screen Space
```

### SG-28

**A world/scene point's screen coordinate is a projection/rendering result, not its world-space identity.**

---

# 15. `World space` can itself be application-defined

Khronos notes that a `world coordinate system` is often an application construct rather than an intrinsic OpenGL API stage.

### SG-29

**Engine/application world space ≠ universal graphics primitive.**

### SG-30

Designed reference frames can nevertheless possess strong operational standing inside a system.

This reinforces MF5-C frame standing.

---

# 16. Projection is generally many-to-one

Perspective rendering can map distinct world points along related view rays/depth configurations to overlapping image positions.

### SG-31

**Screen position underdetermines world position without depth/correspondence information.**

### SG-32

**Screen overlap ≠ world overlap.**

This preserves MF5-D/E occlusion distinctions.

---

# 17. Z/depth buffer geometry is not physical depth ontology

Depth buffers encode a rendering depth coordinate under projection/clip conventions.

### SG-33

**Rendered depth value ≠ physical metric depth by default.**

### SG-34

A depth-buffer ordering may be operationally sufficient for occlusion while using nonlinear/projective depth encoding.

---

# 18. Scene graph hierarchy is not spatial containment by default

Parent-child transforms in a scene graph can organize transform inheritance.

### SG-35

**Scene-graph parenthood ≠ physical containment ≠ compositional parthood universally.**

A camera may be parented to a character for transform convenience without being materially inside or part of the character under all ontologies.

---

# 19. Transform hierarchy can nonetheless enact standing spatial dependence

If child pose is defined relative to parent frame, moving parent changes child world pose.

### SG-36

**Transform-parent relation can have operational spatial standing even when its semantic parthood is weak.**

This is another MF4/MF5 distinction.

---

# 20. Layout space is not document/semantic structure

CSS visual formatting transforms document/tree/style information into generated boxes whose layout depends on dimensions, positioning schemes, containing blocks and external factors including viewport size.

### SG-37

**Document/semantic structure ≠ rendered layout geometry.**

### SG-38

**One document can admit multiple valid layout geometries.**

---

# 21. Responsive reflow is a hard case against fixed representational geometry

W3C explicitly allows viewport resizing to change layout; container queries allow descendants' styles/layout to depend on container dimensions.

### SG-39

**Same represented content/semantic organization can be realized by different spatial layouts under different viewports/containers.**

### SG-40

**Layout reflow ≠ target/content identity change.**

---

# 22. But reflow can alter interaction and perceptual spatial relations

Moving a control from sidebar to bottom bar changes:

- screen distance;
- adjacency;
- scan path;
- pointer travel;
- occlusion/visibility;
- grouping.

### SG-41

**Representation-equivalent content can be interaction-spatially non-equivalent.**

### SG-42

Therefore semantic/content preservation does not imply perceptual/action-layout preservation.

---

# 23. Responsive layout can be relational rather than globally coordinate-stable

Container queries make component layout depend on the size of its containing region.

### SG-43

**Layout standing can be rule/constraint based rather than fixed-coordinate based.**

### SG-44

**A responsive component can retain identity/function across discontinuous layout transitions.**

---

# 24. Layout rule is not rendered layout instance

CSS/grid/flex/constraint specification defines relationships; an actual viewport/container state realizes one layout.

### SG-45

**Layout specification ≠ layout realization.**

### SG-46

This parallels action model ≠ trajectory and representation type ≠ active token.

---

# 25. UI hit space can differ from visible geometry

Interactive systems may use invisible or expanded hit regions, pointer capture, clipping or overlays.

### SG-47

**Visible shape ≠ interactive hit region.**

### SG-48

**Screen action geometry can have operational standing distinct from rendered appearance geometry.**

This is the UI counterpart of rendered vs collision geometry.

---

# 26. Rendered geometry and collision geometry can diverge

A game/virtual system can render a detailed mesh while using coarse colliders/navmeshes/hitboxes, or render no visible object while maintaining an invisible collision barrier.

### SG-49

**Rendered surface ≠ collision surface.**

### SG-50

**Visual world geometry ≠ action/enacted geometry.**

---

# 27. Collision geometry can be more operationally constitutive than render geometry

If movement, contact, projectiles and physics obey a collision shape rather than the visible mesh, the collision structure defines important virtual action relations.

### SG-51

**For action consequences, enacted collision geometry can have stronger operational standing than visual mesh geometry.**

### SG-52

This does not erase the perceptual/representational standing of the rendered mesh; both profiles coexist.

---

# 28. Virtual space can possess genuine designed spatial standing

A virtual system can define:

- re-identifiable loci/regions;
- adjacency/connectivity;
- position/orientation/pose;
- containment;
- collision;
- visibility/occlusion;
- navigation/reachability;
- spatial transforms;
- persistent reference frames.

### SG-53

**Physical realization is not required for formal/designed/operational spatial standing.**

### SG-54

**Virtual spatial standing can arise from rules that systematically constrain state transitions and interactions.**

---

# 29. Virtual space is not merely a visual depiction

A text-only MUD can define rooms, exits, containment and navigation without continuous 3D rendering.

### SG-55

**Virtual spatial standing does not require visual 2D/3D display geometry.**

### SG-56

A continuous rendered 3D scene can conversely be largely decorative if interactions ignore spatial relations.

---

# 30. Designed spatial standing criterion

MF5-G proposes a provisional criterion:

```text
VirtualSpatialStanding(V | System, Scope)
```

is stronger when spatial distinctions are not merely visual labels but are recruited by system rules for one or more of:

- transition possibility;
- collision/contact;
- containment;
- visibility/occlusion;
- navigation/reachability;
- interaction range;
- persistence/reference;
- spatial query/evaluation.

### SG-57

**Operational recruitment distinguishes enacted virtual space from decorative spatial metaphor.**

### SG-58

No single listed relation is universally necessary; designed standing is profile-based.

---

# 31. Portal/teleport topology is a decisive virtual hard case

A portal can connect distant rendered/world regions by a one-step transition.

### SG-59

**Virtual action adjacency ≠ rendered Euclidean nearness.**

### SG-60

**Designed topology can include nonlocal edges and discontinuous transitions.**

This strengthens MF5-F.

---

# 32. Portal-connected worlds can have coherent topology without Euclidean embedding fidelity

The game's adjacency/reachability structure can remain internally well-defined even when no single ordinary Euclidean embedding preserves all portal relations as metric-local.

### SG-61

**Virtual spatial coherence does not require globally Euclidean display embedding.**

### SG-62

`RenderedGeometry ≠ EnactedTopology`.

---

# 33. Minimap creates a spatial representation of a spatially enacted world

A game may simultaneously possess:

- enacted world/action space;
- camera/render space;
- screen space;
- minimap vehicle space.

### SG-63

**One system can contain several spatial representations of one virtual spatial domain.**

### SG-64

Minimap icon distance/orientation need not exactly equal world distance/orientation if the key intentionally compresses/rotates/recenters.

---

# 34. HUD space can be head/view locked while world content is world locked

OpenXR distinguishes VIEW, LOCAL, LOCAL_FLOOR and STAGE reference spaces with different semantics; VIEW is useful for head-locked content, while LOCAL/STAGE are world-locked frames.

### SG-65

**Head/view-locked display space ≠ world-locked virtual/physical space.**

### SG-66

**XR content attachment/reference-space choice changes operational spatial relation without changing content identity.**

---

# 35. AR is a correspondence problem between virtual and physical spatial structures

AR places virtual content relative to estimates of physical/world space.

ARCore explicitly uses anchors so content appears fixed to physical locations while the numeric anchor coordinates may update as spatial understanding improves.

### SG-67

**Virtual-physical registration ≠ coordinate-value permanence.**

### SG-68

**A standing physical attachment relation can persist while its numerical world-space description changes.**

This is a direct real engineering validation of MF5-C.

---

# 36. Anchor identity and pose estimate must remain separate

ARCore describes an anchor as a fixed physical location/orientation whose pose values can change as world understanding updates.

### SG-69

**Anchor identity/standing ≠ current numeric pose estimate.**

### SG-70

AR registration can improve without the target physical place moving.

---

# 37. AR world coordinate space can be epistemically revised

ARCore warns that numerical coordinates of camera/anchors can change significantly as its environmental model adjusts and that frame coordinates should not be treated as persistent physical identifiers.

### SG-71

**Estimated world coordinate system ≠ immutable physical world frame.**

### SG-72

Persistent spatial identity may need anchors/relative relations rather than bare coordinates.

---

# 38. OpenXR independently reinforces multiple reference-space semantics

OpenXR defines VIEW, LOCAL, LOCAL_FLOOR and STAGE with different origins/orientations/locking semantics and permits runtime adjustments as tracking understanding evolves.

### SG-73

**XR `space` is typed by reference semantics, not merely a 4×4 pose matrix.**

### SG-74

**Same virtual object can have different operational behavior when expressed in different reference spaces.**

---

# 39. AR registration error is typed

Possible errors include:

- translation offset;
- orientation drift;
- scale error;
- floor/height misalignment;
- temporal lag;
- anchor relocalization jump;
- target correspondence error.

### SG-75

**AR alignment fidelity ≠ one pixel residual.**

### SG-76

Physical, perceptual and interaction consequences of registration error can differ.

---

# 40. Representation can preserve action relations instead of geometry

A navigation schematic may preserve `take this exit after that station` while distorting distance/angle.

### SG-77

**Representational target can be action topology/cost rather than physical geometry.**

### SG-78

A map's represented target is not automatically `physical space`; it may represent navigation/action space from MF5-F.

---

# 41. Therefore `map` is a representational role, not one ontology

Maps can target:

- geographic/physical geometry;
- transit topology;
- hazard regions;
- social/administrative territories;
- navigation costs;
- virtual/game worlds;
- conceptual structures.

### SG-79

**Map artifact type does not determine represented spatial ontology.**

---

# 42. Diagrammatic proximity can encode semantic grouping without metric semantics

Items placed near each other in a layout may communicate grouping/association without asserting that target semantic distance obeys triangle inequality or a metric.

### SG-80

**Vehicle proximity as code ≠ target metric distance.**

### SG-81

Proximity can be categorical, ordinal or conventional rather than quantitative.

---

# 43. Container/box diagrams can encode hierarchy, membership or scope

A box enclosing another mark may stand for set membership, module ownership, conceptual scope or physical containment.

### SG-82

**Vehicle containment ≠ target physical containment by default.**

### SG-83

Representation key determines the standing relation.

---

# 44. Arrow geometry and arrow semantics are separable

A curved/straight arrow vehicle has direction/orientation in the diagram, while represented relation may be causal, temporal, data-flow or physical motion.

### SG-84

**Arrow direction in vehicle space ≠ target physical direction by default.**

### SG-85

The target relation can still possess ordered/directional semantics through MF3 grounding.

---

# 45. Representation can intentionally break spatial continuity

Insets, exploded views, cutaways, foldouts, discontinuous axes and teleport maps place logically related target regions discontinuously in vehicle space.

### SG-86

**Vehicle continuity ≠ target continuity.**

### SG-87

Spatial discontinuity in representation can improve legibility while preserving intended correspondence.

---

# 46. Scale can be nonuniform within one representation

Maps, fisheye views and focus+context displays can vary local scale.

### SG-88

**One vehicle need not possess one globally uniform target scale factor.**

### SG-89

Local scale variation is not automatically error if declared/grounded by the representation design.

---

# 47. Level of detail changes representation, not necessarily represented identity

Rendering can replace distant geometry with lower-resolution meshes/impostors while maintaining object/world identity.

### SG-90

**LOD representation change ≠ target object disappearance/change by default.**

### SG-91

But LOD can change collision/perceptual/action fidelity if corresponding system structures also change.

---

# 48. Representation identity can survive spatial rearrangement

A diagram can be relaid out while preserving node identities/edges; a subway map can be redesigned while preserving station/network relations.

### SG-92

**Representational identity ≠ fixed vehicle coordinates.**

### SG-93

Equivalence must specify which semantic/spatial relations survive rearrangement.

---

# 49. Vehicle geometry can affect cognition/action even when target content is invariant

Different layouts can alter search, grouping, comparison, motor reach and attention.

### SG-94

**Vehicle geometry is not semantically constitutive in every representation, but it can materially affect consumer performance.**

### SG-95

Target-equivalent representations can be perceptually/actionally nonequivalent.

---

# 50. Responsive representation creates a family, not one canonical layout

A single web document/component may have several valid realization geometries conditioned on viewport/container state.

### SG-96

**Representational standing can belong to a transformation/reflow family rather than one fixed arrangement.**

### SG-97

Fidelity testing should distinguish invariants intended across responsive variants from relations allowed to change.

---

# 51. Render-time camera transformation is not world mutation

Changing camera/view transform changes projected screen coordinates and visibility while world object poses may remain fixed.

### SG-98

**Camera motion/view change ≠ world object motion.**

### SG-99

This is MF5-C active/passive semantics applied to rendered media.

---

# 52. Screen clipping is not target deletion

Geometry outside viewport/clip region may not be rendered while remaining in world/scene state.

### SG-100

**Not rendered ≠ not present in represented/enacted space.**

### SG-101

Visibility/rendering state and world existence remain distinct.

---

# 53. Culling/occlusion optimizations should not silently alter ontology

A renderer may omit geometry for performance while collision/logic persists.

### SG-102

**Rendering omission ≠ spatial-state removal unless system semantics explicitly tie them.**

---

# 54. Virtual world can be persistent without being continuously rendered

Server-side world state can retain objects/regions while no client currently renders them.

### SG-103

**Virtual spatial persistence ≠ active display persistence.**

This distinguishes world-state standing from presentation standing.

---

# 55. Instancing/duplication complicates vehicle-target identity

The same mesh/asset can be instantiated at multiple virtual poses.

### SG-104

**Asset identity ≠ world-instance identity.**

### SG-105

Representation type/token and spatial instance must be separated.

This connects MF3 type/token distinctions.

---

# 56. Mirror/reflection/portal views create multiple images of one virtual target

One virtual object can appear at several screen loci through mirrors/portals/cameras.

### SG-106

**Rendered image instance ≠ virtual object instance.**

### SG-107

Screen multiplicity does not imply target multiplicity.

---

# 57. Conversely one screen object can stand for many target entities

Aggregation markers, heatmaps, clusters and density maps can collapse many target regions/entities into one display mark.

### SG-108

**Vehicle token count ≠ represented entity count.**

This is spatial aggregation under MF3/MF4.

---

# 58. Map uncertainty and target uncertainty are distinct

A map can contain:

- target-location uncertainty;
- registration uncertainty;
- cartographic generalization;
- stale data;
- projection distortion;
- deliberate schematic displacement.

### SG-109

**Representational spatial uncertainty/error must be typed by source and relation family.**

---

# 59. Deliberate distortion is not epistemic uncertainty

Beck-style schematic displacement can be intentional and known exactly.

### SG-110

**Designed distortion ≠ uncertainty.**

### SG-111

A map can be certain about a deliberately nonmetric vehicle position while representing target topology correctly.

---

# 60. Generalization/simplification is not necessarily falsehood

Removing small bends/details or aggregating regions can preserve task-relevant topology/order.

### SG-112

**Spatial simplification ≠ representational failure when omitted distinctions are outside declared scope.**

### SG-113

But simplification can create false topology/adjacency if not controlled.

---

# 61. RepresentationalSpatialStanding

MF5-G proposes:

```text
RepresentationalSpatialStanding(R | Vehicle, Target, Key, Scope)
```

when vehicle distinctions/relations are grounded as standing for selected spatial distinctions/possibilities in the target domain under MF3.

### SG-114

**Spatial-looking layout alone is insufficient for represented spatial standing.**

### SG-115

Representational standing must declare which target relation family is encoded/preserved.

---

# 62. VirtualSpatialStanding is different from RepresentationalSpatialStanding

A virtual world may be represented on a screen, but its computational rules may independently enact location/adjacency/collision/navigation.

### SG-116

**Virtual/enacted spatial standing ≠ screen representation standing.**

### SG-117

A system can have strong virtual spatial standing even when not currently rendered.

---

# 63. One artifact/system can have both kinds simultaneously

A game screen represents a virtual world whose rules themselves instantiate virtual spatial relations.

### SG-118

**Representation of a spatial domain and enactment of that domain are separate roles that can coexist.**

### SG-119

Do not infer one role from the other automatically.

---

# 64. Spatial metaphor criterion

MF5-G uses a provisional anti-inflation test:

A candidate target domain should not be treated as genuinely spatial merely because:

- it is visualized on a plane;
- words like `near`, `far`, `space`, `region` are used metaphorically;
- a dimensionality-reduction embedding provides coordinates;
- a graph layout places related nodes nearby;
- a UI arranges categories into panels.

### SG-120

**Vehicle spatialization ≠ target spatial standing.**

---

# 65. Stronger evidence for target spatial standing

Depending on domain, stronger evidence includes:

- spatial relations survive legitimate re-representations;
- interventions predicted by target spatial relations have systematic consequences;
- topology/metric/orientation is part of target specification/dynamics;
- agents/systems recruit relations for navigation/contact/containment;
- multiple independent representations converge on the same relation structure;
- formal construction explicitly defines spatial primitives/equivalences.

### SG-121

**Cross-representation invariance can support target spatial standing but is not universally necessary.**

---

# 66. Screen/layout geometry standing does not require represented target space

A dashboard's panels have real designed layout relations even if they represent nonspatial statistics.

### SG-122

**Vehicle spatial ontology is legitimate in its own domain and should not be dismissed as `merely visual`.**

The anti-inflation restriction applies to transfer from vehicle to target, not to vehicle spatiality itself.

---

# 67. UI spatial semantics can be partly constitutive of interaction

Drag/drop zones, menus, hit regions, stacking order and viewport clipping determine allowed interaction.

### SG-123

**Designed interface space can be both representational and action-spatial.**

### SG-124

One locus can simultaneously have display, semantic and interaction roles.

---

# 68. Spatial relation can be multimodal in representation

A map may encode region identity through color, topology through lines, distance through labels, and accessibility through symbols.

### SG-125

**Represented spatial structure need not be carried solely by vehicle geometry.**

### SG-126

Nonspatial channels can encode spatial facts, and spatial channels can encode nonspatial facts.

This prevents `representation space = content space` collapse.

---

# 69. Coordinate labels can override/qualify vehicle geometry

A distorted map may print exact distances/coordinates.

### SG-127

**Vehicle metric distortion can coexist with explicitly represented metric truth through symbolic channels.**

Thus overall representation profile is compositional and multimodal.

---

# 70. Representation can be spatially inconsistent across channels

A diagram may show A near B but label a large numeric distance; minimap may disagree with world route structure due staleness/bug.

### SG-128

**Cross-channel spatial consistency is a separate quality criterion.**

### SG-129

Conflicting spatial cues require provenance/authority resolution rather than silent averaging.

---

# 71. Representation can intentionally show impossible viewpoints/geometries

Exploded diagrams, cutaways, impossible perspective, multiple simultaneous scales and nonphotorealistic layouts can communicate target structure.

### SG-130

**Representational utility does not require physically realizable camera geometry.**

### SG-131

The representation key determines which target relations remain valid.

---

# 72. Virtual physics can be nonphysical yet spatially coherent

A designed world may use altered gravity, discrete tiles, wraparound topology or teleport edges.

### SG-132

**Virtual spatial law ≠ physical law.**

### SG-133

A virtual domain can be spatially coherent under its own specified transformation/transition rules.

---

# 73. Wraparound/toroidal worlds are a topology hard case

A screen may depict left and right boundaries as far apart while the virtual world identifies them as adjacent through wraparound.

### SG-134

**Display boundary ≠ virtual topological boundary.**

### SG-135

**Virtual adjacency can contradict naive screen metric adjacency while remaining rule-consistent.**

---

# 74. Infinite/repeating virtual worlds can have local standing without one finite global map

Procedural generation or periodic tiling can define local neighborhood/transition rules without materializing every locus simultaneously.

### SG-136

**Virtual spatial standing does not require complete extensional enumeration of all loci.**

### SG-137

Generative rule standing can support spatial structure.

---

# 75. Procedural generation separates rule space from realized world space

A seed/generator can produce one spatial realization.

### SG-138

**Generator/parameter space ≠ generated virtual world space.**

### SG-139

Different seeds can generate different spatial domains under the same generative rules.

This anticipates MF5-H computational spaces.

---

# 76. Virtual coordinate units are conventional but operational

`1 unit = 1 meter` may be a design convention, and engines may use arbitrary unit scales.

### SG-140

**Virtual unit convention ≠ physical unit identity.**

### SG-141

Once used by collision, movement and camera systems, the convention gains operational coordinate standing.

---

# 77. Physical display size and virtual size are distinct

A virtual mountain can occupy 5 cm on a screen yet represent/enact kilometers in world scale.

### SG-142

**Display extent ≠ represented/enacted extent.**

### SG-143

Scale correspondence requires an explicit key/calibration.

---

# 78. AR superposition adds a third domain rather than merging two into one

At minimum AR involves:

- physical target space;
- estimated/tracked reference space;
- virtual content space;
- rendered screen/view space.

### SG-144

**AR `mixed space` should not be treated as ontological identity of physical and virtual domains.**

### SG-145

It is a maintained correspondence/registration among distinct spatial profiles.

---

# 79. Registration can be locally strong and globally weak

Nearby anchors can appear stable while larger-scale world alignment drifts or is uncertain.

### SG-146

**Registration fidelity can be local/scale dependent.**

### SG-147

Global coordinate agreement is not necessary for useful local AR attachment.

---

# 80. Spatial provenance matters for AR/XR

A pose can come from:

- local tracking;
- cloud/geospatial anchor;
- user placement;
- map localization;
- controller action space.

### SG-148

**Same numeric pose with different reference/authority provenance is not the same spatial claim.**

This directly extends MF5-C TransformClaim.

---

# 81. RepresentationalSpaceProfile

MF5-G proposes:

```text
RepresentationalSpaceProfile = <
  Vehicle,
  VehicleSpace/Geometry,
  TargetDomain,
  TargetSpatialProfile?,
  RepresentationKey,
  PreservedRelations/Invariants,
  Distorted/OmittedRelations,
  Projection/Transform,
  Scale/Generalization,
  Layout/ResponsiveFamily?,
  Interaction/HitSpace?,
  Uncertainty/DistortionType,
  Provenance/Authority,
  Consumer/Task,
  Scope
>
```

### SG-149

**Representational space requires both vehicle-side and target-side descriptions where target spatial claims are made.**

---

# 82. VirtualSpaceProfile

```text
VirtualSpaceProfile = <
  System/WorldIdentity,
  Loci/Regions/Entities,
  Topology/Adjacency,
  Geometry/Frames/Coordinates,
  Collision/Containment,
  Visibility/RenderingRelation,
  Action/Navigation/Reachability,
  Portals/NonlocalTransitions,
  Persistence/GenerationRules,
  RenderedViews?,
  Physical/ARRegistration?,
  StandingRoute : designed/formal/operational,
  Provenance/Version,
  Uncertainty/State,
  Scope
>
```

### SG-150

**Rendered view is optional in VirtualSpaceProfile.**

---

# 83. SpatialRepresentationClaim

```text
SpatialRepresentationClaim = <
  VehicleRegion/Relation,
  TargetRegion/Relation,
  Key/Mapping,
  TargetRelationType,
  VehicleRelationType,
  Transformation/Projection,
  IntendedInvariants,
  AllowedDistortions,
  Scale/Granularity,
  Evidence/Provenance,
  Uncertainty,
  Task/Scope
>
```

### SG-151

**Bare `map is accurate` is under-specified.**

---

# 84. VirtualRegistrationClaim

```text
VirtualRegistrationClaim = <
  VirtualEntity/Frame,
  Physical/ReferenceTarget,
  ReferenceSpace/Anchor,
  Transform/PoseEstimate,
  ValidityTime/Scale,
  Authority/Tracker,
  Uncertainty/Drift,
  IntendedAttachment : world/head/object/etc.,
  Evidence,
  Scope
>
```

### SG-152

**Registration claim separates attachment identity from current coordinate estimate.**

---

# 85. Failure taxonomy

## Vehicle/target collapse

Map/display coordinates treated as target coordinates.

## Metric-fidelity absolutism

Schematic/topological map rejected because physical distances are distorted despite preserving intended route relations.

## Projection-profile collapse

Conformal/equal-area/equidistant properties conflated under one `accuracy` score.

## Diagram-literalism

Target assumed physically spatial because representation uses proximity/containment/arrows.

## Spatial-metaphor inflation

Conceptual/semantic domain promoted to target spatial ontology from spatial language/layout alone.

## World/screen collapse

Window coordinates treated as world-space identity.

## Screen/world overlap collapse

Projected overlap treated as physical/world overlap.

## Scene-graph semantic inflation

Transform parent interpreted automatically as parthood/containment.

## Document/layout collapse

Semantic/document identity tied to one responsive layout realization.

## Reflow identity error

Viewport/container-driven rearrangement interpreted as represented-content change.

## Hit/render collapse

Visible bounds treated as interaction/collision bounds.

## Render/collision collapse

Visual mesh treated as enacted physical/action geometry.

## Virtual/physical collapse

Designed world law interpreted as physical-world law.

## Portal/metric collapse

Portal adjacency forced into ordinary Euclidean nearness.

## Map/world target confusion

Map assumed to target physical space when it actually represents action/topological/institutional structure.

## AR coordinate reification

Current world-space numeric coordinates treated as persistent physical-location identity.

## Anchor/pose collapse

Anchor identity confused with current pose estimate.

## Rendering omission ontology error

Culled/offscreen entity treated as absent from virtual world.

## Instance/image collapse

Multiple renders/reflections treated as multiple world entities, or instanced assets treated as one world entity.

## Distortion/uncertainty collapse

Deliberate schematic displacement treated as epistemic uncertainty.

## Simplification/topology error

Generalization accidentally changes connectivity/containment while assumed semantically safe.

## Cross-channel inconsistency

Geometry/symbol/label channels assert incompatible spatial relations without provenance handling.

### SG-153

**Representational/virtual spatial error is a typed family, not one geometric residual.**

---

# 86. Strongest non-collapse stack after MF5-G

```text
Vehicle Space
 ≠ Represented Target Space
 ≠ Virtual Enacted Space
 ≠ Physical Space
```

```text
Map Geometry
 ≠ Target Geometry
```

```text
Vehicle Geometry
 ≠ Represented Geometry
 ≠ Represented Action Topology
```

```text
Object/World Space
 ≠ View/Eye Space
 ≠ Clip/NDC Space
 ≠ Screen/Window Space
```

```text
Document/Semantic Structure
 ≠ Layout Geometry
 ≠ One Layout Realization
```

```text
Rendered Geometry
 ≠ Collision Geometry
 ≠ Navigation Geometry
 ≠ Hit-Test Geometry
```

```text
Virtual Space
 ≠ Rendered View
 ≠ Physical Space
```

```text
Portal/Teleport Adjacency
 ≠ Physical/Rendered Nearness
```

```text
AR Anchor Identity
 ≠ Current Pose Coordinates
 ≠ Physical Coordinate Permanence
```

```text
Projection Distortion
 ≠ Total Spatial Failure
```

```text
Designed Distortion
 ≠ Uncertainty
```

```text
Spatial Metaphor/Visualization
 ≠ Target Spatial Standing
```

```text
RepresentationalSpatialStanding
 ≠ VirtualSpatialStanding
```

---

# 87. Claims rejected by MF5-G

Reject as universal foundational claims:

- map space is identical to target space;
- vehicle geometry is represented geometry;
- spatial representation quality is one coordinate/geometric error scalar;
- metric/geographic distortion makes a transit/schematic map spatially invalid;
- every useful map must preserve physical distance/angle/scale;
- projection is merely coordinate relabeling;
- a diagram's physical arrangement proves its target relation is spatial;
- spatial metaphor or a spatial visualization establishes target spatial ontology;
- plot/embedding nearness automatically means target nearness;
- screen/window coordinates are world coordinates;
- projected overlap means world overlap;
- depth-buffer value is physical metric depth;
- scene-graph parenthood implies physical containment/parthood;
- document/semantic structure determines one fixed layout geometry;
- responsive reflow changes represented content identity;
- visible UI bounds equal hit/interactable bounds;
- rendered mesh equals collision/action geometry;
- virtual space requires visual 3D rendering;
- rendered 3D appearance by itself establishes virtual spatial standing;
- virtual spatial laws must obey physical Euclidean geometry;
- portal/teleport adjacency is physical nearness;
- minimap geometry equals enacted world geometry;
- AR virtual and physical spaces become one identical coordinate domain;
- persistent physical attachment requires persistent numeric world coordinates;
- AR anchor identity is current pose estimate;
- one XR reference space is universally canonical;
- offscreen/culled/not-rendered means absent from virtual world;
- asset identity equals world instance identity;
- multiple rendered images imply multiple target objects;
- deliberate schematic distortion is uncertainty/error;
- simplification/generalization is always falsehood;
- `map is accurate` is meaningful without specifying preserved relation family;
- representation of a virtual spatial world and computational enactment of that world are the same role.

---

# 88. Primary/authoritative literature and specification anchors

- **Transport for London, Made by TfL (2024)**, `Our brand assets`: official account of early geographically detailed transit maps and Harry Beck's redesign using straight/horizontal/vertical/45° lines and clear interchange points to improve usability. Hard case for selective topological/route fidelity over geographic metric fidelity.
- **John P. Snyder, USGS (1987)**, *Map Projections: A Working Manual*, USGS Professional Paper 1395, DOI 10.3133/pp1395. Authoritative treatment of projections preserving different geometric properties and their forward/inverse mappings.
- **Khronos OpenGL Registry / OpenGL Wiki**, coordinate transformation pipeline: object → eye → clip → normalized device → window coordinates; viewport transformation maps NDC to window coordinates. Used as an engineering hard case for `world/object ≠ screen`.
- **W3C CSS Visual Formatting Model / CSS Containment Level 3**, official specifications showing generated box geometry depends on document/style relationships and external viewport/container dimensions; viewport resizing/container queries can change layout realization without changing document identity.
- **Khronos OpenXR 1.1 Specification**, reference spaces VIEW, LOCAL, LOCAL_FLOOR and STAGE with distinct origin/locking semantics and runtime tracking updates. Hard case for typed XR reference-space standing.
- **Google ARCore official Anchor/Pose documentation**, anchors represent fixed physical locations/orientations while current numeric world coordinates can update as environmental understanding improves; world coordinate frames should not be treated as persistent physical identifiers across frames. Hard case for anchor identity ≠ coordinate permanence.

---

# 89. Deep reconstruction

Naive model:

```text
Target world
    ↓ copy coordinates
Map / screen / 3D scene
    ↓ render
User sees same space
```

MF5-G replaces it with:

```text
Target / represented domain
        │
        │  MF3 representation key
        ▼
Representational vehicle
  ├─ vehicle geometry/layout
  ├─ symbols/labels/color
  ├─ projection/generalization
  └─ responsive realization family
        │
        ├───────────────┐
        │               │
   screen/view       interaction/hit space
        │               │
        ▼               ▼
 perception          interface action

Separately, in virtual systems:

Designed computational world
  ├─ loci/regions
  ├─ topology/portals
  ├─ collision
  ├─ navigation/reachability
  └─ persistence/rules
        │
        ▼
VirtualSpatialStanding
        │
        ├─ rendered through camera/screen representations
        └─ optionally registered to physical space via AR/XR anchors/reference spaces
```

The decisive move is:

> **A spatial representation has vehicle-side space and target-side spatial content linked by a key; a virtual world may additionally enact its own spatial relations computationally. Neither should be collapsed into screen coordinates or physical space.**

---

# 90. Deepest MF5-G result

The strongest surviving formulation is:

> **Representational space is the spatial organization of a representation vehicle together with a grounded mapping to selected target relations, where fidelity is typed by the structures intended to be preserved. Virtual space is a distinct designed/formal/operational spatial domain whose loci, topology, geometry and action relations are enacted by system rules; its rendered representations are views of that domain rather than the domain itself.**

Compact:

```text
RepresentationalSpace
 = VehicleSpatialStructure
 + RepresentationKey
 + TargetSpatialProfile
 + Preserved/Distorted Relations
 + Consumer/Scope
```

and:

```text
VirtualSpace
 = Designed Spatial Domain
 + Operational Spatial Relations
 + Persistence/Rules
 + Action/Interaction Consequences
 + Standing
 + Scope
```

---

# 91. MF5-A→G reconstructed picture

```text
MF5-A  Space ontology
 = standing spatial possibility domain

MF5-B  Geometry
 = typed relation/invariance/equivalence structures

MF5-C  Spatial description
 = frames/charts/coordinates/transforms

MF5-D  Regionalization
 = regions/boundaries + occupancy/locality/visibility/access

MF5-E  Perceptual/embodied space
 = body/world-relative sensorimotor spatial organization

MF5-F  Action space
 = system-relative configurations/states + transition/reachability/cost relations

MF5-G  Representational/virtual space
 = vehicle↔target spatial mapping + independently enacted designed spatial domains
```

MF5-G demonstrates that `representation of space`, `space of the representation`, and `computationally enacted virtual space` are three different notions.

---

# 92. No FoundationReopenCondition

MF5-G strongly consumes MF3 Representation and MF4 Composition but does not falsify either.

- MF3 already requires grounded standing-in relations and typed evaluation; MF5-G specializes them for spatial keys/fidelity.
- MF4 already permits responsive/reflow compositions, multimodal encoding and overlapping organization; MF5-G shows those arrangements can be vehicle geometry without being target geometry.
- MF2 Perception remains compatible with screen/view geometry versus experienced/perceived space separation.

### SG-154

**MF2, MF3 and MF4 remain frozen.**

---

# 93. MF5-H handoff — Computational, Latent, Semantic & Abstract Spatial Standing

MF5-G now exposes the final major anti-inflation frontier before MF5 falsification:

> **When mathematics/ML/computation gives a domain coordinates, neighborhoods or distances, under what conditions should we call that domain genuinely spatial rather than merely a mathematically structured or representational `space`?**

MF5-H must attack:

- vector spaces versus spatial domains;
- feature/embedding/latent spaces;
- semantic spaces and distributional geometry;
- similarity distance versus spatial distance;
- PCA/manifold/UMAP/t-SNE display geometry versus latent/target geometry;
- topology/manifold hypotheses in learned representation;
- arbitrary invertible reparameterization and coordinate non-identifiability;
- representation geometry recruited by downstream systems;
- learned metric versus analyst-chosen metric;
- causal/interventional evidence for latent geometry;
- disentanglement/non-identifiability;
- quotient/equivalence spaces;
- probability/state/function spaces named `space` but not necessarily spatial;
- computational grids/tensors versus target spatial standing;
- neural feature maps and topographic organization;
- semantic maps/metaphorical landscapes;
- spatialization for visualization;
- whether systematic transition/interpolation/intervention structure can create computational spatial standing;
- relation among formal spatial standing, representational spatial standing and target spatial standing;
- anti-inflation criteria strong enough to survive arbitrary embeddings.

Central attack:

```text
Mathematical Space ≠ Spatial Domain
Vector Coordinates ≠ Spatial Standing
Embedding Distance ≠ Target Distance
Visualization Geometry ≠ Latent Geometry
Latent Geometry ≠ Semantic/World Geometry
Decodability ≠ Spatiality
Smooth Interpolation ≠ Meaningful Path
Analyst Metric ≠ System-Recruited Geometry
```

**Next: MF5-H — Computational, Latent, Semantic & Abstract Spatial Standing.**
