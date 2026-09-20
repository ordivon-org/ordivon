# Artifact — CAD admission boundary R1

Current `design-3d` graduation is a glTF/GLB **scene/mesh** result. It is intentionally not CAD, BIM or manufacturing-model graduation.

## Current truth

- GLB static mesh, material scene and skinned animation profiles are live-proven through Khronos validation plus independent Assimp/Blender/Godot consumption.
- Blender is present and useful for scene/mesh work.
- Windows OpenSCAD is present, but executable presence does not establish a durable Artifact CAD profile.
- A bounded FreeCAD 1.1.3 + system Open CASCADE 7.9.3 STEP single-solid path is now locally live-proven and is represented by shadow profile `design-3d-step-solid-r1`.
- This proves metric single-solid BREP STEP exchange/readback only. IFC/BIM, assemblies, PMI/GD&T, feature-history preservation, 3MF/manufacturing and cross-kernel interoperability remain ungraduated.

## First acceptable CAD slice

A future CAD profile must begin with a mature native CAD source authority rather than converting mesh support into a broader claim. The minimum useful slice is:

```text
native parametric/BREP source
  -> exact units + topology/shape contract
  -> STEP (or another deliberately selected CAD interchange)
  -> standard/native validator where available
  -> independent target-grade CAD consumer/readback
  -> destructive invalid/divergent geometry rejection
```

KiCad can itself export PCB geometry to STEP/BREP, which is useful downstream evidence for an EDA product, but that derivative does not by itself graduate general CAD authoring.
