# Artifact E2E — Design / 3D Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Design/3D R1 proves a deliberately narrow GLB 2.0 static-mesh interchange profile. It does not claim generic CAD, BIM, manufacturing-model, animation or textured-scene support.

## External authority

The selected interchange authority is Khronos glTF 2.0, standardized as ISO/IEC 12113:2022. R1 uses binary glTF / GLB 2.0 with media type `model/gltf-binary`.

The evidence stack separates three roles:

1. **Khronos glTF Validator** — format/specification validation and profile-relevant glTF facts;
2. **Assimp** — independent scene importer exposing source-coordinate topology and bounds;
3. **Blender** — independent target-grade importer proving the asset can be consumed as the expected mesh topology.

No consumer is promoted to universal geometry authority.

## First bounded profile

`design-3d-glb-static-mesh-r1`

R1 selects:

```text
container        GLB 2.0
scene            one default scene
nodes            one
meshes           one
primitives       one TRIANGLES primitive
POSITION         float
indices          unsigned short
materials        none
textures         none
animations       none
skins            none
morph targets    none
cameras/lights   none
extensions       none
external assets  none
```

The smoke object is one indexed triangle with three vertices and source-coordinate bounds:

```text
min = [0, 0, 0]
max = [1, 1, 0]
```

## Object contract

Schema:

`artifact-delivery/shadow-contracts/design-3d-glb-contract-v1.schema.json`

The object contract binds scene/topology facts that are specific to the actual asset:

- node count;
- mesh count;
- primitive count;
- vertex count;
- triangle count;
- source-coordinate minimum/maximum bounds.

A GLB may be perfectly valid glTF while failing this object contract.

## Khronos validator

The official Khronos `gltf-validator` npm package was frozen as:

`/opt/ordivon/external/gltf-validator/2.0.0-dev.3.10`

Pinned package facts:

- npm SHA-1 `9b09225db864fe3f0a584259f65d087e2213a93a`;
- npm integrity `sha512-odJ4k0tRkGXiDGn78yDBg+fBbAIvBnXxh3RwAta0emSxGtyagFE8B4xELB1oYe3S5RD8Ci3uZAsZaascH2LAEQ==`;
- package archive SHA-256 `4e03dbdc3bc0d1342afd5d2d7ae341a7e3474502ccb872b02dbbaddaee0fdec6`;
- module wrapper SHA-256 `f817fde51399f0a7a3f9eb3fd5ae6ff77108d492a7397978022c94700e244b56`.

An initial wrapper attempt failed because the package's ES module exports named functions rather than a default object. That integration failure was corrected before the validator was promoted.

The smoke validator report establishes:

```text
validator version     2.0.0-dev.3.10
errors                0
warnings              0
glTF version           2.0
material count         0
animation count        0
textures               false
skins                  false
morph targets          false
default scene          true
draw calls             1
vertices               3
triangles              1
```

## Independent consumers

### Assimp 6.0.5

Assimp independently observes:

```text
nodes       1
meshes      1
vertices    3
faces       1
primitive   triangle
animations  0
textures    0
bones       0
cameras     0
lights      0
bounds      [0,0,0] → [1,1,0]
```

Its source-coordinate bounds are used as the independent object-contract view.

### Blender 5.2.1 LTS

Blender headless independently imports the same GLB and observes one mesh object with three vertices, one polygon and zero material slots.

Blender performs the expected glTF Y-up → Blender Z-up coordinate-system conversion. Therefore Blender coordinates are **not** compared directly to glTF source coordinates. This is a deliberate authority boundary:

```text
ConsumerTransformedCoordinates != SourceGeometryCoordinates
```

Blender proves target consumption/topology, not source-coordinate identity.

## Live proof

Runtime job:

`job-01a0961a-f63a-7c40-963e-374bb7e3d27f`

Exact GLB:

- size 636 bytes;
- SHA-256 `c9293c553471438317be72ef6a95a5dd9f71729cfee78536ab9ec42fbdafeb34`;
- contract canonical digest `ba89fa6799fa4b0273d859c7803340fdceb277601863acd9db9919b365e32de6`.

Evidence digests:

- Khronos report `e6436227e4e688c642232e114eec5b8681f56618e2507aeb2e682a2204f81ae2`;
- Assimp report `b594d8de4a776146c66f067105a1bfb44a0203cf692227028be7dc917d56d50c`;
- Blender stdout `f8c2472fc282f60f544260cda82ddde934ba4767874cf5fc00fe64b8b7ff2578`.

## Falsifiers proven

Seven focused tests pass:

1. bounded one-triangle GLB + matching contract → PASS;
2. valid GLB but contract requests wrong source bounds → Khronos PASS, Artifact FAIL;
3. valid GLB adds a material → Khronos PASS, bounded profile FAIL;
4. accessor declares bounds inconsistent with actual data → Khronos validator FAIL;
5. valid GLB adds another node → Khronos PASS, scene contract FAIL through Assimp;
6. corrupt GLB header → fail closed;
7. frozen consumer/tool identities match the proven substrate.

Hence:

```text
GLBValid != SceneContractSatisfied
ConsumerImportSuccess != SourceGeometryAuthority
```

## Claim boundary

R1 does not establish materials/PBR, textures, color management, animation, skinning, morphs, CAD/BIM/manufacturing semantics, artistic quality or cross-renderer pixel equivalence. Those require separate profiles and native domain standards rather than widening this GLB profile implicitly.

## R2 — bounded material-scene and skinned-animation profiles

Game pressure did not widen `design-3d-glb-static-mesh-r1`. Two separate GLB 2.0 profiles were added instead:

| Profile | Admitted feature set | Target readback |
| --- | --- | --- |
| `design-3d-glb-material-scene-r1` | triangle meshes + core glTF materials; no textures, skins, animations or morphs | Khronos Validator + Assimp + Blender + Godot `GLTFDocument` |
| `design-3d-glb-skinned-animation-r1` | triangle meshes + materials + skinning + animations; no textures or morphs | Khronos Validator + Assimp + Blender + Godot `GLTFDocument` |

The profiles share one verifier implementation but have separate profile identities, schemas, object contracts and capability bindings. Family classification never chooses the validator; the exact `profileId` does.

The Veilwild F05 material scene passed with 0 Khronos errors / 0 warnings, 153 draw calls, 7 materials, 11,923 vertices and 7,832 triangles. Assimp, Blender and Godot independently imported the contracted scene structure.

The repaired Veilwild F10 successor (`9a50900f2a7fcb17af6be1be8b7788fbc743fd7a8e1bd075515a62cf6fd24daa`) passed with 0 Khronos errors / 0 warnings, 7 animations, 3 materials, skinning enabled, maximum 4 influences, 5,131 validator vertices and 7,408 validator triangles. Godot independently observed 11 imported mesh instances, one 23-bone skeleton and 7 animations.

Blender's F10 imported scene intentionally does not have to reproduce Khronos aggregate vertex/polygon totals: Blender materializes an additional consumer-side mesh object in this scene. The object contract therefore binds Blender's own exact import facts separately instead of laundering consumer-transformed topology into source-format authority.

`Artifact` may bind clip names and material-slot counts as technical identities requested by an object contract, but it does not interpret their Game meaning. Animation behavior, gameplay meaning, artistic deformation quality, visual equivalence, player value and rights remain outside these profiles.
