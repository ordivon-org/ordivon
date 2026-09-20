# CONVERGENCE OBJECT 001

A procedural Blender sculpture in the Ordivon `CONVERGENCE` series.

Three independent signal paths enter from different spatial directions and retain distinct color/identity markers before reaching a shared resolution core. The form deliberately avoids depicting convergence as simple erasure: origin nodes, separate trajectories, and near-core identity markers remain visible even after the paths meet.

## Editable / native sources

- `build.py` — procedural scene authoring source.
- `source/convergence-object-001.blend` — native Blender editable scene.
- `verify_import.py` — independent GLB re-import verification script.
- `source/convergence-object-001-roundtrip.blend` — Blender scene created by re-importing the delivered GLB.

## Delivered / inspection artifacts

- `render/convergence-object-001.glb` — glTF 2.0 binary model.
- `render/convergence-object-001.png` — 1400×1400 rendered key image.
- `roundtrip-receipt.json` — Blender 5.2.1 re-import evidence.

## Concept relation

This is a sibling of `media:convergence-sonic-ident`, not a derivative rendering of the audio. Both works explore the same concept through different media.

## Consumption boundary

The GLB has been exported by Blender and independently re-imported into a clean Blender scene. Expected object identities, materials, and non-collapsed spatial extent were verified. This establishes Blender round-trip consumption, not visual equivalence across every third-party GLB viewer.
