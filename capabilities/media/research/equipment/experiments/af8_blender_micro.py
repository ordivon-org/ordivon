from pathlib import Path
import bpy
import math

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "out" / "af8"
OUT.mkdir(parents=True, exist_ok=True)
BLEND = OUT / "blender-micro.blend"
PNG = OUT / "blender-micro.png"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0), scale=(1.35, 1.35, 1.35))
cube = bpy.context.object
cube.name = "AF8 Semantic Cube"
cube.rotation_euler = (math.radians(24), math.radians(8), math.radians(34))

material = bpy.data.materials.new("AF8 Material")
material.diffuse_color = (0.08, 0.48, 0.86, 1.0)
cube.data.materials.append(material)

bpy.ops.object.camera_add(location=(5.4, -5.4, 4.1))
camera = bpy.context.object
camera.name = "AF8 Camera"
bpy.context.scene.camera = camera

def look_at(obj, point=(0.0, 0.0, 0.0)):
    direction = mathutils.Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

import mathutils
look_at(camera)

bpy.ops.object.light_add(type="AREA", location=(3.5, -2.0, 5.0))
key = bpy.context.object
key.name = "AF8 Key"
key.data.energy = 900
key.data.shape = "DISK"
key.data.size = 4.0

bpy.ops.object.light_add(type="AREA", location=(-3.0, 1.0, 2.5))
fill = bpy.context.object
fill.name = "AF8 Fill"
fill.data.energy = 450
fill.data.size = 3.0

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PNG)
scene.world.color = (0.015, 0.02, 0.04)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.render.render(write_still=True)

if not BLEND.is_file() or not PNG.is_file():
    raise RuntimeError("AF8 declared Blender artifacts were not materialized")
print(f"AF8_BLEND={BLEND}")
print(f"AF8_RENDER={PNG}")
