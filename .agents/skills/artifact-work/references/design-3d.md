# Design / 3D reference

## Bounded proven profile

`design-3d-glb-static-mesh-r1`

- glTF 2.0 / ISO/IEC 12113:2022
- GLB 2.0 / `model/gltf-binary`
- one scene/node/mesh/TRIANGLES primitive
- bounded profile excludes materials, textures, animation, skins, morph targets, extensions, and external assets
- Standing: `SHADOW_PROFILE_LIVE_PROVEN`

## Prior proven providers

- Khronos glTF Validator 2.0.0-dev.3.10 — format/spec validation
- Assimp 6.0.5 — independent source-coordinate scene interpretation
- Blender 5.2.1 LTS — target-grade independent import

## Boundary

Valid glTF may still fail the object-specific topology/bounds contract. Consumer coordinate systems are not universal geometry authority.

## Source evidence

`/root/projects/ordivon-artifact-v2/docs/ARTIFACT_FAMILY_DESIGN_3D_R1.md`
