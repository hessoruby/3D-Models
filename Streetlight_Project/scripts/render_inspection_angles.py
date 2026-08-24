import bpy
from mathutils import Vector


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.use_nodes = True
world_bg = scene.world.node_tree.nodes.get("Background")
world_bg.inputs["Color"].default_value = (0.02, 0.028, 0.04, 1.0)
world_bg.inputs["Strength"].default_value = 0.25

for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)

def area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    point_camera(obj, (-0.4, 0, 2.0))


area("Key", (4.5, -4.5, 6.5), 1000, 4.0, (1.0, 0.85, 0.72))
area("Fill", (-4.0, 2.0, 4.5), 850, 3.5, (0.55, 0.72, 1.0))

camera = bpy.data.objects.get("Camera")
camera.data.type = "ORTHO"
scene.camera = camera

shots = [
    ("full", (6.2, -8.0, 4.2), (-0.45, 0.0, 2.15), 5.4, 560, 800),
    ("top", (4.0, -6.0, 4.8), (-0.75, 0.0, 3.85), 2.4, 800, 520),
    ("base", (3.2, -5.0, 2.2), (-0.05, 0.0, 0.65), 2.0, 700, 650),
]

for name, location, target, ortho_scale, width, height in shots:
    camera.location = location
    camera.data.ortho_scale = ortho_scale
    point_camera(camera, target)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = f"//renders/streetlight_inspect_{name}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", bpy.path.abspath(scene.render.filepath))
