import bpy


obj = bpy.data.objects["Cube"]
mesh = obj.data
normal_matrix = obj.matrix_world.to_3x3()

rows = []
for poly in mesh.polygons:
    center = obj.matrix_world @ poly.center
    if center.x < -0.75 and center.z > 3.75:
        normal = (normal_matrix @ poly.normal).normalized()
        verts = [obj.matrix_world @ mesh.vertices[index].co for index in poly.vertices]
        zmin = min(vertex.z for vertex in verts)
        zmax = max(vertex.z for vertex in verts)
        xmin = min(vertex.x for vertex in verts)
        xmax = max(vertex.x for vertex in verts)
        rows.append((center.x, poly.index, center, normal, poly.area, xmin, xmax, zmin, zmax))

for _, index, center, normal, area, xmin, xmax, zmin, zmax in sorted(rows):
    print(
        f"FACE {index:03d} center=({center.x:.4f},{center.y:.4f},{center.z:.4f}) "
        f"normal=({normal.x:.3f},{normal.y:.3f},{normal.z:.3f}) area={area:.5f} "
        f"x=({xmin:.4f},{xmax:.4f}) z=({zmin:.4f},{zmax:.4f})"
    )
