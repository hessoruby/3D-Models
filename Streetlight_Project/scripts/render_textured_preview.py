import bpy
from mathutils import Vector


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, target, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.008, 0.014, 0.026, 1.0)
background.inputs["Strength"].default_value = 0.18

for obj in list(bpy.data.objects):
    if obj.type == "LIGHT" and obj.name != "Streetlight_Warm_Light":
        bpy.data.objects.remove(obj, do_unlink=True)

add_area("Preview_Key", (4.8, -5.2, 6.7), (-0.45, 0.0, 2.15), 1100, 4.0, (0.72, 0.84, 1.0))
add_area("Preview_Rim", (-4.2, 2.5, 5.5), (-0.45, 0.0, 2.3), 950, 3.0, (1.0, 0.45, 0.18))
add_area("Preview_Fill", (2.0, 4.5, 3.2), (-0.25, 0.0, 1.8), 500, 3.2, (0.42, 0.60, 1.0))

bpy.ops.mesh.primitive_plane_add(size=18.0, location=(0.0, 0.0, -0.018))
ground = bpy.context.object
ground.name = "Preview_Ground"
ground_mat = bpy.data.materials.new("Preview_Ground_Material")
ground_mat.use_nodes = True
ground_shader = ground_mat.node_tree.nodes.get("Principled BSDF")
ground_shader.inputs["Base Color"].default_value = (0.012, 0.018, 0.026, 1.0)
ground_shader.inputs["Roughness"].default_value = 0.82
ground.data.materials.append(ground_mat)

camera = bpy.data.objects.get("Camera")
camera.data.type = "ORTHO"
scene.camera = camera

shots = [
    ("full", (6.2, -8.0, 4.3), (-0.42, 0.0, 2.15), 5.45, 650, 900),
    ("lamp", (3.8, -6.0, 4.8), (-1.05, 0.0, 4.12), 1.75, 900, 620),
    ("lamp_under", (3.4, -5.5, 3.25), (-1.12, 0.0, 4.10), 1.55, 900, 620),
    ("base", (3.2, -5.0, 2.0), (-0.05, 0.0, 0.58), 1.75, 760, 700),
]

for name, location, target, scale, width, height in shots:
    camera.location = location
    camera.data.ortho_scale = scale
    aim(camera, target)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = f"//renders/streetlight_textured_{name}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", bpy.path.abspath(scene.render.filepath))
