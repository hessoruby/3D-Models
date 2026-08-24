import bpy

print("SCENE", bpy.context.scene.name)
print("ENGINE", bpy.context.scene.render.engine)
print("OBJECTS", len(bpy.data.objects))

for obj in sorted(bpy.data.objects, key=lambda item: item.name.lower()):
    dims = tuple(round(value, 4) for value in obj.dimensions)
    loc = tuple(round(value, 4) for value in obj.location)
    mats = [slot.material.name if slot.material else "<empty>" for slot in obj.material_slots]
    mesh_info = ""
    if obj.type == "MESH":
        mesh_info = f" verts={len(obj.data.vertices)} faces={len(obj.data.polygons)}"
    print(
        f"OBJ name={obj.name!r} type={obj.type} loc={loc} dims={dims}{mesh_info} mats={mats}"
    )

print("MATERIALS", len(bpy.data.materials))
for mat in sorted(bpy.data.materials, key=lambda item: item.name.lower()):
    print(
        f"MAT name={mat.name!r} users={mat.users} nodes={mat.use_nodes} "
        f"blend={getattr(mat, 'surface_render_method', 'n/a')}"
    )
