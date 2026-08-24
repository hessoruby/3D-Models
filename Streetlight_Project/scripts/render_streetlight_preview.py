import bpy

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 700
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = "//renders/streetlight_before.png"
scene.render.film_transparent = False

scene.world.use_nodes = True
background = scene.world.node_tree.nodes.get("Background")
if background:
    background.inputs["Color"].default_value = (0.035, 0.045, 0.06, 1.0)
    background.inputs["Strength"].default_value = 0.35

bpy.ops.render.render(write_still=True)
print("RENDERED", bpy.path.abspath(scene.render.filepath))
