import bpy
from collections import defaultdict, deque
from mathutils import Vector


for obj in sorted((item for item in bpy.data.objects if item.type == "MESH"), key=lambda item: item.name):
    mesh = obj.data
    adjacency = defaultdict(set)
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)

    unseen = set(range(len(mesh.vertices)))
    components = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        component = set()
        while queue:
            vertex = queue.popleft()
            component.add(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)

    data = []
    for component in components:
        world_points = [obj.matrix_world @ mesh.vertices[index].co for index in component]
        mins = tuple(min(point[axis] for point in world_points) for axis in range(3))
        maxs = tuple(max(point[axis] for point in world_points) for axis in range(3))
        center = tuple((mins[axis] + maxs[axis]) / 2 for axis in range(3))
        faces = [
            poly.index
            for poly in mesh.polygons
            if all(vertex in component for vertex in poly.vertices)
        ]
        data.append((mins[2], mins, maxs, center, len(component), len(faces), min(component), max(component)))

    print(f"MESH {obj.name!r} components={len(data)}")
    for index, (_, mins, maxs, center, verts, faces, first_vert, last_vert) in enumerate(sorted(data, reverse=True)):
        fmt = lambda values: tuple(round(value, 4) for value in values)
        print(
            f"  C{index:02d} verts={verts} faces={faces} vi={first_vert}:{last_vert} "
            f"min={fmt(mins)} max={fmt(maxs)} center={fmt(center)}"
        )
