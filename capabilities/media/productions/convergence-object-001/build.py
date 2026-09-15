import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDER = ROOT / "render"
SOURCE = ROOT / "source"
# Repeated automated builds should not emit Blender's .blend1 backup carriers into the production tree.
bpy.context.preferences.filepaths.save_version = 0
RENDER.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)

# Clean scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.curves, bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.filepath = str(RENDER / 'convergence-object-001.png')
scene.render.image_settings.color_mode = 'RGBA'
scene.world.color = (0.007, 0.009, 0.015)

# Color management.
scene.view_settings.look = 'AgX - Medium High Contrast'

# Materials.
def material(name, color, metallic=0.0, roughness=0.35, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    return m

mats = [
    material('Signal_A', (0.11, 0.42, 0.95), metallic=0.35, roughness=0.24, emission=(0.03, 0.12, 0.38), emission_strength=0.9),
    material('Signal_B', (0.94, 0.32, 0.16), metallic=0.25, roughness=0.26, emission=(0.35, 0.06, 0.02), emission_strength=0.7),
    material('Signal_C', (0.12, 0.82, 0.56), metallic=0.30, roughness=0.22, emission=(0.02, 0.30, 0.13), emission_strength=0.7),
]
core_mat = material('Resolution_Core', (0.72, 0.75, 0.84), metallic=0.85, roughness=0.16, emission=(0.08, 0.09, 0.14), emission_strength=0.5)
base_mat = material('Base', (0.035, 0.043, 0.065), metallic=0.35, roughness=0.32)

# Curves: three independent trajectories with distinct origins, converging toward one core.
def make_curve(name, points, mat, radius=0.16):
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 24
    curve.bevel_depth = radius
    curve.bevel_resolution = 6
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

paths = [
    [(-4.8, -2.8, -0.2), (-3.1, -1.9, 1.1), (-1.6, -0.8, 1.65), (-0.45, -0.20, 0.55), (0.0, 0.0, 0.15)],
    [(4.6, -2.5, 0.6), (3.0, -1.7, -0.6), (1.7, -0.65, -1.35), (0.55, -0.15, -0.45), (0.0, 0.0, 0.15)],
    [(0.5, 4.9, -1.2), (0.25, 3.1, 0.25), (-0.25, 1.7, 1.45), (-0.15, 0.55, 0.55), (0.0, 0.0, 0.15)],
]
for i, (pts, mat) in enumerate(zip(paths, mats), start=1):
    make_curve(f'Signal_Path_{i}', pts, mat, radius=0.18 - 0.015 * (i - 1))

# Arrival nodes at the three origins.
for i, (p, mat) in enumerate(zip([paths[0][0], paths[1][0], paths[2][0]], mats), start=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.34, location=p)
    o = bpy.context.object
    o.name = f'Signal_Origin_{i}'
    o.data.materials.append(mat)

# Central resolution core: nested torus + sphere.
bpy.ops.mesh.primitive_torus_add(major_radius=0.72, minor_radius=0.12, major_segments=96, minor_segments=24, location=(0,0,0.15), rotation=(math.radians(72), math.radians(18), math.radians(12)))
ring = bpy.context.object
ring.name = 'Resolution_Ring'
ring.data.materials.append(core_mat)

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.44, location=(0,0,0.15))
core = bpy.context.object
core.name = 'Resolution_Core'
core.data.materials.append(core_mat)

# Pedestal / ground disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=4.2, depth=0.16, location=(0,0,-1.72))
base = bpy.context.object
base.name = 'Convergence_Base'
base.data.materials.append(base_mat)
bevel = base.modifiers.new('Base_Bevel', 'BEVEL')
bevel.width = 0.14
bevel.segments = 5

# Three subtle markers near the core preserve the idea that inputs do not become anonymous before resolution.
for i, angle in enumerate((215, -35, 92), start=1):
    r = 1.13
    a = math.radians(angle)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.12, location=(r*math.cos(a), r*math.sin(a), 0.22))
    marker = bpy.context.object
    marker.name = f'Identity_Marker_{i}'
    marker.data.materials.append(mats[i-1])

# Camera.
bpy.ops.object.camera_add(location=(10.4, -13.0, 9.0))
cam = bpy.context.object
cam.name = 'Camera'
scene.camera = cam

def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
point_at(cam, (0, 0, 0.1))
cam.data.lens = 54

# Lighting: large soft key, rim, and low fill.
def area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    point_at(obj, (0,0,0))
    return obj

area('Key', (4.5,-4.0,8.5), 1150, 5.5, (0.82,0.88,1.0))
area('Rim', (-6.0,2.8,4.6), 920, 4.0, (0.55,0.68,1.0))
area('Fill', (1.0,5.8,2.1), 650, 5.0, (1.0,0.58,0.38))

# Save native editable source before export.
blend_path = SOURCE / 'convergence-object-001.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# Render still.
bpy.ops.render.render(write_still=True)

# Export the actual artwork only; omit camera/lights from GLB delivery.
for obj in bpy.context.scene.objects:
    obj.select_set(obj.type in {'MESH','CURVE'})
bpy.context.view_layer.objects.active = core
bpy.ops.export_scene.gltf(
    filepath=str(RENDER / 'convergence-object-001.glb'),
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True,
)

print(f'BLEND={blend_path}')
print(f'PNG={scene.render.filepath}')
print(f'GLB={RENDER / "convergence-object-001.glb"}')
print('OBJECTS=' + ','.join(sorted(o.name for o in bpy.context.scene.objects if o.type in {'MESH','CURVE'})))
