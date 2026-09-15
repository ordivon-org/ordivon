import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Round-trip verification is disposable execution evidence; do not emit .blend1 backup carriers.
bpy.context.preferences.filepaths.save_version = 0
GLB = ROOT / 'render' / 'convergence-object-001.glb'
OUT = ROOT / 'roundtrip-receipt.json'
ROUNDTRIP_BLEND = ROOT / 'source' / 'convergence-object-001-roundtrip.blend'

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(GLB))

objects = [o for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'}]
mesh_objects = [o for o in objects if o.type == 'MESH']
materials = sorted({slot.material.name for o in objects for slot in o.material_slots if slot.material})

required_prefixes = ['Signal_Path_', 'Signal_Origin_', 'Identity_Marker_']
required_names = ['Resolution_Ring', 'Resolution_Core', 'Convergence_Base']
missing = []
for prefix in required_prefixes:
    if not any(o.name.startswith(prefix) for o in objects):
        missing.append(prefix + '*')
for name in required_names:
    if not any(o.name == name for o in objects):
        missing.append(name)

# Global imported bounds, useful for checking that geometry did not collapse to a point.
mins = [float('inf')]*3
maxs = [float('-inf')]*3
for obj in objects:
    for corner in obj.bound_box:
        world = obj.matrix_world @ __import__('mathutils').Vector(corner)
        for i in range(3):
            mins[i] = min(mins[i], world[i])
            maxs[i] = max(maxs[i], world[i])
extent = [maxs[i]-mins[i] for i in range(3)] if objects else [0,0,0]

receipt = {
    'schemaVersion': 1,
    'kind': 'ordivon.media.blender-glb-roundtrip-receipt',
    'consumer': 'Blender 5.2.1 glTF importer',
    'glb': 'render/convergence-object-001.glb',
    'objectCount': len(objects),
    'meshObjectCount': len(mesh_objects),
    'objectNames': sorted(o.name for o in objects),
    'materials': materials,
    'boundsMin': mins,
    'boundsMax': maxs,
    'extent': extent,
    'missingExpectedIdentities': missing,
    'standing': 'PASS' if (not missing and len(objects) >= 10 and min(extent) > 0.2) else 'FAIL',
    'truthBoundary': 'This proves Blender can re-import the exported GLB with expected named geometry/material structure and non-collapsed spatial extent. It does not prove every third-party GLB viewer renders identically.'
}
OUT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROUNDTRIP_BLEND))
print(json.dumps(receipt, indent=2))
if receipt['standing'] != 'PASS':
    raise SystemExit(2)
