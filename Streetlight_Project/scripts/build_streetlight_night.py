import bpy
import math
import os
import random
from mathutils import Matrix, Vector


random.seed(23)
OUTPUT_PATH = bpy.path.abspath("//streetlight_night_environment.blend")
PREFIX = "ENV_"


def checkpoint(stage):
    print("STAGE", stage, flush=True)
    if os.environ.get("ENV_BUILD_STOP") == stage:
        raise RuntimeError("DEBUG_STOP_" + stage)


def set_socket(node, names, value):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return socket
    return None


def try_set(target, name, value):
    if hasattr(target, name):
        try:
            setattr(target, name, value)
            return True
        except (TypeError, ValueError):
            pass
    return False


def get_collection(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for current in list(obj.users_collection):
        if current != collection:
            current.objects.unlink(obj)


def apply_mesh_scale(obj):
    sx, sy, sz = obj.scale
    obj.data.transform(Matrix.Diagonal((sx, sy, sz, 1.0)))
    obj.scale = (1.0, 1.0, 1.0)
    obj.data.update()


def clear_previous_environment():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name.startswith(PREFIX):
            bpy.data.collections.remove(collection)
    for material in list(bpy.data.materials):
        if material.name.startswith(PREFIX):
            bpy.data.materials.remove(material, do_unlink=True)
    for texture in list(bpy.data.textures):
        if texture.name.startswith(PREFIX):
            bpy.data.textures.remove(texture)


clear_previous_environment()
geometry_collection = get_collection("ENV_Geometry")
lighting_collection = get_collection("ENV_Lighting")
atmosphere_collection = get_collection("ENV_Atmosphere")
particle_collection = get_collection("ENV_Particles")
camera_collection = get_collection("ENV_Cameras")


def fresh_material(name, viewport_color):
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old, do_unlink=True)
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = viewport_color
    material.node_tree.nodes.clear()
    return material


def make_asphalt_material():
    material = fresh_material("ENV_MAT_Asphalt_PBR", (0.018, 0.021, 0.025, 1.0))
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (820, 30)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (580, 30)
    set_socket(shader, "Metallic", 0.0)
    set_socket(shader, "Roughness", 0.48)
    set_socket(shader, "IOR", 1.48)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-980, 20)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-810, 20)
    mapping.inputs["Scale"].default_value = (5.0, 11.0, 2.0)
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])

    aggregate = nodes.new("ShaderNodeTexNoise")
    aggregate.location = (-610, 180)
    set_socket(aggregate, "Scale", 7.0)
    set_socket(aggregate, "Detail", 9.0)
    set_socket(aggregate, "Roughness", 0.82)
    set_socket(aggregate, "Distortion", 0.18)
    links.new(mapping.outputs["Vector"], aggregate.inputs["Vector"])

    asphalt_colors = nodes.new("ShaderNodeValToRGB")
    asphalt_colors.location = (-370, 210)
    asphalt_colors.color_ramp.elements[0].position = 0.18
    asphalt_colors.color_ramp.elements[0].color = (0.006, 0.007, 0.009, 1.0)
    mid = asphalt_colors.color_ramp.elements.new(0.48)
    mid.color = (0.018, 0.021, 0.026, 1.0)
    pale = asphalt_colors.color_ramp.elements.new(0.72)
    pale.color = (0.042, 0.047, 0.054, 1.0)
    asphalt_colors.color_ramp.elements[-1].position = 0.90
    asphalt_colors.color_ramp.elements[-1].color = (0.013, 0.016, 0.020, 1.0)
    links.new(aggregate.outputs["Fac"], asphalt_colors.inputs["Fac"])

    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (-610, -80)
    voronoi.feature = "DISTANCE_TO_EDGE"
    set_socket(voronoi, "Scale", 3.2)
    set_socket(voronoi, "Randomness", 0.88)
    links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])

    crack_ramp = nodes.new("ShaderNodeValToRGB")
    crack_ramp.location = (-350, -70)
    crack_ramp.color_ramp.interpolation = "CONSTANT"
    crack_ramp.color_ramp.elements[0].position = 0.0025
    crack_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    crack_ramp.color_ramp.elements[1].position = 0.0065
    crack_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    links.new(voronoi.outputs["Distance"], crack_ramp.inputs["Fac"])

    crack_breakup = nodes.new("ShaderNodeTexNoise")
    crack_breakup.location = (-610, -230)
    set_socket(crack_breakup, "Scale", 1.6)
    set_socket(crack_breakup, "Detail", 5.0)
    set_socket(crack_breakup, "Roughness", 0.78)
    links.new(mapping.outputs["Vector"], crack_breakup.inputs["Vector"])
    crack_presence = nodes.new("ShaderNodeValToRGB")
    crack_presence.location = (-390, -220)
    crack_presence.color_ramp.elements[0].position = 0.54
    crack_presence.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    crack_presence.color_ramp.elements[1].position = 0.68
    crack_presence.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(crack_breakup.outputs["Fac"], crack_presence.inputs["Fac"])
    final_crack_mask = nodes.new("ShaderNodeMixRGB")
    final_crack_mask.blend_type = "MULTIPLY"
    final_crack_mask.inputs[0].default_value = 1.0
    final_crack_mask.location = (-150, -160)
    links.new(crack_ramp.outputs["Color"], final_crack_mask.inputs[1])
    links.new(crack_presence.outputs["Color"], final_crack_mask.inputs[2])

    crack_mix = nodes.new("ShaderNodeMixRGB")
    crack_mix.location = (-50, 150)
    crack_mix.inputs[2].default_value = (0.0015, 0.0015, 0.0018, 1.0)
    links.new(final_crack_mask.outputs["Color"], crack_mix.inputs[0])
    links.new(asphalt_colors.outputs["Color"], crack_mix.inputs[1])
    links.new(crack_mix.outputs["Color"], shader.inputs["Base Color"])

    roughness = nodes.new("ShaderNodeMapRange")
    roughness.location = (30, -30)
    set_socket(roughness, "From Min", 0.18)
    set_socket(roughness, "From Max", 0.82)
    set_socket(roughness, "To Min", 0.32)
    set_socket(roughness, "To Max", 0.66)
    links.new(aggregate.outputs["Fac"], roughness.inputs["Value"])
    links.new(roughness.outputs["Result"], shader.inputs["Roughness"])

    micro = nodes.new("ShaderNodeTexNoise")
    micro.location = (-290, -300)
    set_socket(micro, "Scale", 135.0)
    set_socket(micro, "Detail", 3.0)
    set_socket(micro, "Roughness", 0.72)
    links.new(mapping.outputs["Vector"], micro.inputs["Vector"])
    height_mix = nodes.new("ShaderNodeMixRGB")
    height_mix.location = (10, -230)
    height_mix.blend_type = "MULTIPLY"
    height_mix.inputs[0].default_value = 0.76
    links.new(micro.outputs["Fac"], height_mix.inputs[1])
    links.new(final_crack_mask.outputs["Color"], height_mix.inputs[2])
    bump = nodes.new("ShaderNodeBump")
    bump.location = (320, -180)
    set_socket(bump, "Strength", 0.18)
    set_socket(bump, "Distance", 0.018)
    links.new(height_mix.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_concrete_material(name, base_dark, base_light, roughness=0.72):
    material = fresh_material(name, (*base_light, 1.0))
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (280, 0)
    set_socket(shader, "Roughness", roughness)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-650, 0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-460, 80)
    set_socket(noise, "Scale", 18.0)
    set_socket(noise, "Detail", 8.0)
    set_socket(noise, "Roughness", 0.76)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-220, 100)
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = (*base_dark, 1.0)
    stain = ramp.color_ramp.elements.new(0.54)
    stain.color = tuple(v * 0.78 for v in base_light) + (1.0,)
    ramp.color_ramp.elements[-1].position = 0.86
    ramp.color_ramp.elements[-1].color = (*base_light, 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.location = (30, -120)
    set_socket(bump, "Strength", 0.22)
    set_socket(bump, "Distance", 0.022)
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_simple_material(name, color, roughness, metallic=0.0):
    material = fresh_material(name, (*color, 1.0))
    shader = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
    set_socket(shader, "Base Color", (*color, 1.0))
    set_socket(shader, "Roughness", roughness)
    set_socket(shader, "Metallic", metallic)
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


asphalt_mat = make_asphalt_material()
sidewalk_mat = make_concrete_material(
    "ENV_MAT_Sidewalk_Concrete", (0.055, 0.060, 0.066), (0.18, 0.19, 0.20), 0.78
)
curb_mat = make_concrete_material(
    "ENV_MAT_Curb_Concrete", (0.070, 0.073, 0.075), (0.24, 0.25, 0.25), 0.74
)
marking_mat = make_concrete_material(
    "ENV_MAT_Road_Marking_Dirty", (0.22, 0.21, 0.17), (0.63, 0.59, 0.46), 0.62
)
patch_mat = make_simple_material("ENV_MAT_Asphalt_Patch", (0.010, 0.012, 0.014), 0.38)
groove_mat = make_simple_material("ENV_MAT_Groove_Dirt", (0.008, 0.007, 0.006), 0.90)
base_ground_mat = make_simple_material("ENV_MAT_Background_Ground", (0.004, 0.006, 0.009), 0.96)
checkpoint("materials")


def add_box(name, location, dimensions, material, collection, bevel=0.0):
    hx, hy, hz = (value * 0.5 for value in dimensions)
    verts = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    if bevel > 0:
        modifier = obj.modifiers.new("Edge_Soften", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


road_nx, road_ny = 38, 72
road_verts = []
for iy in range(road_ny):
    y = -7.0 + 14.0 * iy / (road_ny - 1)
    for ix in range(road_nx):
        x = -8.10 + 7.50 * ix / (road_nx - 1)
        road_verts.append((x, y, -0.125))
road_faces = []
for iy in range(road_ny - 1):
    for ix in range(road_nx - 1):
        a = iy * road_nx + ix
        road_faces.append((a, a + 1, a + 1 + road_nx, a + road_nx))
road_mesh = bpy.data.meshes.new("ENV_Road_Asphalt_Mesh")
road_mesh.from_pydata(road_verts, [], road_faces)
road_mesh.update()
road = bpy.data.objects.new("ENV_Road_Asphalt", road_mesh)
geometry_collection.objects.link(road)
road.data.materials.append(asphalt_mat)
road_noise = bpy.data.textures.new("ENV_TEX_Road_Unevenness", type="CLOUDS")
road_noise.noise_scale = 0.72
road_noise.noise_depth = 2
displace = road.modifiers.new("Subtle_Uneven_Surface", "DISPLACE")
displace.texture = road_noise
displace.strength = 0.012
displace.mid_level = 0.52
checkpoint("road")

sidewalk = add_box(
    "ENV_Sidewalk", (1.45, 0.0, -0.075), (3.80, 14.0, 0.15), sidewalk_mat, geometry_collection, 0.025
)
curb = add_box(
    "ENV_Curb", (-0.56, 0.0, -0.02), (0.22, 14.0, 0.20), curb_mat, geometry_collection, 0.025
)
background_ground = add_box(
    "ENV_Background_Ground", (0.0, 0.0, -0.34), (32.0, 32.0, 0.35), base_ground_mat, geometry_collection
)
checkpoint("slabs")

for index, y in enumerate((-5.0, -2.5, 0.0, 2.5, 5.0)):
    add_box(
        f"ENV_Sidewalk_Joint_{index:02d}",
        (1.45, y, 0.004),
        (3.72, 0.022, 0.009),
        groove_mat,
        geometry_collection,
    )
checkpoint("joints")

marking_verts = []
marking_faces = []
for y in (-6.0, -3.0, 0.0, 3.0, 6.0):
    angle = math.radians(random.uniform(-0.35, 0.35))
    cosine, sine = math.cos(angle), math.sin(angle)
    base = len(marking_verts)
    for local_x, local_y in ((-0.065, -0.675), (0.065, -0.675), (0.065, 0.675), (-0.065, 0.675)):
        marking_verts.append(
            (-4.55 + local_x * cosine - local_y * sine, y + local_x * sine + local_y * cosine, -0.112)
        )
    marking_faces.append((base, base + 1, base + 2, base + 3))
marking_mesh = bpy.data.meshes.new("ENV_Road_Markings_Mesh")
marking_mesh.from_pydata(marking_verts, [], marking_faces)
marking_mesh.update()
markings = bpy.data.objects.new("ENV_Road_Markings", marking_mesh)
geometry_collection.objects.link(markings)
markings.data.materials.append(marking_mat)
checkpoint("markings")


def add_patch(name, center, points, material):
    verts = [(center[0] + x, center[1] + y, -0.109) for x, y in points]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    geometry_collection.objects.link(obj)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Patch_Edge_Soften", "BEVEL")
    bevel.width = 0.018
    bevel.segments = 2
    return obj


add_patch(
    "ENV_Road_Patch_A",
    (-2.55, 2.05),
    [(-0.72, -0.58), (0.62, -0.46), (0.84, 0.18), (0.30, 0.62), (-0.55, 0.50), (-0.90, 0.05)],
    patch_mat,
)
checkpoint("geometry")
add_patch(
    "ENV_Road_Patch_B",
    (-6.15, -2.35),
    [(-0.52, -0.30), (0.48, -0.42), (0.70, 0.12), (0.22, 0.48), (-0.62, 0.38)],
    patch_mat,
)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


for name in ("Streetlight_Warm_Light", "ENV_Lamp_Spot", "ENV_Lamp_Soft_Fill"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
default_light = bpy.data.objects.get("Light")
if default_light:
    default_light.hide_render = True
    default_light.hide_viewport = True


def add_light(name, light_type, location, color, energy):
    data = bpy.data.lights.new(name, light_type)
    data.color = color
    data.energy = energy
    obj = bpy.data.objects.new(name, data)
    lighting_collection.objects.link(obj)
    obj.location = location
    return obj


lamp_spot = add_light("ENV_Lamp_Spot", "SPOT", (-1.33, 0.0, 4.02), (1.0, 0.56, 0.30), 3600.0)
lamp_spot.data.spot_size = math.radians(63.0)
lamp_spot.data.spot_blend = 0.76
lamp_spot.data.shadow_soft_size = 0.22
lamp_spot.data.use_shadow = True
try_set(lamp_spot.data, "volume_factor", 1.35)
aim(lamp_spot, (-1.45, 0.0, -0.10))

lamp_fill = add_light("ENV_Lamp_Soft_Fill", "AREA", (-1.33, 0.0, 4.00), (1.0, 0.56, 0.30), 520.0)
lamp_fill.data.shape = "DISK"
lamp_fill.data.size = 0.46
lamp_fill.data.use_shadow = True
aim(lamp_fill, (-1.40, 0.0, -0.10))

moon = add_light("ENV_Moon_Fill", "AREA", (-4.0, 1.5, 8.5), (0.20, 0.32, 1.0), 720.0)
moon.data.shape = "DISK"
moon.data.size = 7.5
aim(moon, (0.0, 0.0, 1.5))

rim = add_light("ENV_Cool_Rim", "AREA", (5.5, -4.0, 6.5), (0.16, 0.30, 1.0), 580.0)
rim.data.shape = "DISK"
rim.data.size = 4.0
aim(rim, (0.0, 0.0, 2.1))


def make_lens_insert_material():
    material = fresh_material("ENV_MAT_Lamp_Lens_Emission", (1.0, 0.34, 0.055, 1.0))
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    set_socket(shader, "Base Color", (1.0, 0.38, 0.08, 1.0))
    set_socket(shader, "Roughness", 0.22)
    set_socket(shader, ("Emission Color", "Emission"), (1.0, 0.18, 0.025, 1.0))
    set_socket(shader, "Emission Strength", 14.0)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


lens_insert = add_box(
    "ENV_Lamp_Lens_Insert",
    (-1.33, 0.0, 4.061),
    (0.43, 0.105, 0.018),
    make_lens_insert_material(),
    lighting_collection,
    0.035,
)

existing_lens = bpy.data.materials.get("SL_Frosted_Warm_Lens")
if existing_lens and existing_lens.use_nodes:
    for node in existing_lens.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            set_socket(node, ("Emission Color", "Emission"), (1.0, 0.16, 0.02, 1.0))
            set_socket(node, "Emission Strength", 10.0)

for material_name, multiplier, lift, cap in (
    ("SL_Painted_Steel_Weathered", 3.5, 0.018, 0.30),
    ("SL_Cast_Iron_Base", 2.4, 0.012, 0.24),
):
    material = bpy.data.materials.get(material_name)
    if material and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "VALTORGB":
                for element in node.color_ramp.elements:
                    red, green, blue, alpha = element.color
                    element.color = (
                        min(cap, red * multiplier + lift),
                        min(cap, green * multiplier + lift),
                        min(cap, blue * multiplier + lift),
                        alpha,
                    )
checkpoint("lighting")


def make_beam_material():
    material = fresh_material("ENV_MAT_Volumetric_Beam", (1.0, 0.25, 0.05, 1.0))
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (750, 0)
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.location = (500, 0)
    set_socket(volume, "Color", (0.62, 0.36, 0.18, 1.0))
    set_socket(volume, "Anisotropy", 0.40)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-980, 0)
    separate = nodes.new("ShaderNodeSeparateXYZ")
    separate.location = (-800, 100)
    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])

    xsub = nodes.new("ShaderNodeMath")
    xsub.operation = "SUBTRACT"
    xsub.inputs[1].default_value = 0.5
    ysub = nodes.new("ShaderNodeMath")
    ysub.operation = "SUBTRACT"
    ysub.inputs[1].default_value = 0.5
    xsub.location, ysub.location = (-620, 220), (-620, 110)
    links.new(separate.outputs["X"], xsub.inputs[0])
    links.new(separate.outputs["Y"], ysub.inputs[0])
    xsq = nodes.new("ShaderNodeMath")
    xsq.operation = "MULTIPLY"
    ysq = nodes.new("ShaderNodeMath")
    ysq.operation = "MULTIPLY"
    xsq.location, ysq.location = (-460, 220), (-460, 110)
    links.new(xsub.outputs[0], xsq.inputs[0])
    links.new(xsub.outputs[0], xsq.inputs[1])
    links.new(ysub.outputs[0], ysq.inputs[0])
    links.new(ysub.outputs[0], ysq.inputs[1])
    add = nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    add.location = (-300, 180)
    links.new(xsq.outputs[0], add.inputs[0])
    links.new(ysq.outputs[0], add.inputs[1])
    sqrt = nodes.new("ShaderNodeMath")
    sqrt.operation = "SQRT"
    sqrt.location = (-150, 180)
    links.new(add.outputs[0], sqrt.inputs[0])
    radial = nodes.new("ShaderNodeMapRange")
    radial.location = (10, 180)
    radial.clamp = True
    set_socket(radial, "From Min", 0.15)
    set_socket(radial, "From Max", 0.50)
    set_socket(radial, "To Min", 1.0)
    set_socket(radial, "To Max", 0.0)
    links.new(sqrt.outputs[0], radial.inputs["Value"])

    vertical = nodes.new("ShaderNodeMapRange")
    vertical.location = (-230, 20)
    vertical.clamp = True
    set_socket(vertical, "From Min", 0.0)
    set_socket(vertical, "From Max", 1.0)
    set_socket(vertical, "To Min", 0.20)
    set_socket(vertical, "To Max", 1.0)
    links.new(separate.outputs["Z"], vertical.inputs["Value"])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-420, -170)
    set_socket(noise, "Scale", 3.6)
    set_socket(noise, "Detail", 4.0)
    set_socket(noise, "Roughness", 0.72)
    set_socket(noise, "Distortion", 0.18)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    noise_range = nodes.new("ShaderNodeMapRange")
    noise_range.location = (-160, -170)
    noise_range.clamp = True
    set_socket(noise_range, "From Min", 0.18)
    set_socket(noise_range, "From Max", 0.82)
    set_socket(noise_range, "To Min", 0.48)
    set_socket(noise_range, "To Max", 1.0)
    links.new(noise.outputs["Fac"], noise_range.inputs["Value"])

    mul1 = nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.location = (190, 120)
    links.new(radial.outputs["Result"], mul1.inputs[0])
    links.new(vertical.outputs["Result"], mul1.inputs[1])
    mul2 = nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.location = (330, 80)
    links.new(mul1.outputs[0], mul2.inputs[0])
    links.new(noise_range.outputs["Result"], mul2.inputs[1])
    density = nodes.new("ShaderNodeMath")
    density.operation = "MULTIPLY"
    density.location = (380, -30)
    density.inputs[1].default_value = 0.016
    links.new(mul2.outputs[0], density.inputs[0])
    links.new(density.outputs[0], volume.inputs["Density"])
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


beam_segments = 48
beam_verts = []
for z, radius in ((-0.10, 2.15), (4.02, 0.16)):
    for index in range(beam_segments):
        angle = math.tau * index / beam_segments
        beam_verts.append((-1.39 + math.cos(angle) * radius, math.sin(angle) * radius, z))
beam_faces = []
for index in range(beam_segments):
    next_index = (index + 1) % beam_segments
    beam_faces.append((index, next_index, beam_segments + next_index, beam_segments + index))
beam_faces.append(tuple(reversed(range(beam_segments))))
beam_faces.append(tuple(range(beam_segments, beam_segments * 2)))
beam_mesh = bpy.data.meshes.new("ENV_Volumetric_Light_Beam_Mesh")
beam_mesh.from_pydata(beam_verts, [], beam_faces)
beam_mesh.update()
beam = bpy.data.objects.new("ENV_Volumetric_Light_Beam", beam_mesh)
atmosphere_collection.objects.link(beam)
beam.data.materials.append(make_beam_material())
beam.display_type = "WIRE"


def make_glow_volume_material():
    material = fresh_material("ENV_MAT_Lamp_Glow_Volume", (1.0, 0.22, 0.03, 1.0))
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    set_socket(volume, "Density", 0.018)
    set_socket(volume, "Color", (1.0, 0.25, 0.045, 1.0))
    set_socket(volume, "Emission Color", (1.0, 0.20, 0.045, 1.0))
    set_socket(volume, "Emission Strength", 0.10)
    set_socket(volume, "Anisotropy", 0.20)
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


glow_segments, glow_rings = 24, 10
glow_verts = [(0.0, 0.0, 0.14)]
for ring in range(1, glow_rings):
    phi = math.pi * ring / glow_rings
    for index in range(glow_segments):
        angle = math.tau * index / glow_segments
        glow_verts.append((0.38 * math.sin(phi) * math.cos(angle), 0.22 * math.sin(phi) * math.sin(angle), 0.14 * math.cos(phi)))
bottom_index = len(glow_verts)
glow_verts.append((0.0, 0.0, -0.14))
glow_faces = []
first_ring = 1
for index in range(glow_segments):
    glow_faces.append((0, first_ring + index, first_ring + (index + 1) % glow_segments))
for ring in range(glow_rings - 2):
    first = 1 + ring * glow_segments
    second = first + glow_segments
    for index in range(glow_segments):
        next_index = (index + 1) % glow_segments
        glow_faces.append((first + index, second + index, second + next_index, first + next_index))
last_ring = 1 + (glow_rings - 2) * glow_segments
for index in range(glow_segments):
    glow_faces.append((bottom_index, last_ring + (index + 1) % glow_segments, last_ring + index))
glow_mesh = bpy.data.meshes.new("ENV_Lamp_Glow_Volume_Mesh")
glow_mesh.from_pydata(glow_verts, [], glow_faces)
glow_mesh.update()
glow = bpy.data.objects.new("ENV_Lamp_Glow_Volume", glow_mesh)
glow.location = (-1.33, 0.0, 4.10)
atmosphere_collection.objects.link(glow)
glow.data.materials.append(make_glow_volume_material())
glow.display_type = "WIRE"


world = bpy.context.scene.world
world.use_nodes = True
world_nodes, world_links = world.node_tree.nodes, world.node_tree.links
world_nodes.clear()
world_output = world_nodes.new("ShaderNodeOutputWorld")
world_output.location = (420, 0)
world_bg = world_nodes.new("ShaderNodeBackground")
world_bg.location = (100, 80)
world_bg.inputs["Color"].default_value = (0.0025, 0.0055, 0.015, 1.0)
world_bg.inputs["Strength"].default_value = 0.032
world_fog = world_nodes.new("ShaderNodeVolumePrincipled")
world_fog.location = (100, -130)
set_socket(world_fog, "Density", 0.0028)
set_socket(world_fog, "Color", (0.025, 0.045, 0.090, 1.0))
set_socket(world_fog, "Anisotropy", 0.28)
world_links.new(world_bg.outputs["Background"], world_output.inputs["Surface"])
world_links.new(world_fog.outputs["Volume"], world_output.inputs["Volume"])
checkpoint("volumes_world")


def make_particle_material(name, color, emission_strength, opacity, fade_speed):
    material = fresh_material(name, (*color, 1.0))
    try_set(material, "surface_render_method", "DITHERED")
    try_set(material, "use_transparency_overlap", False)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (650, 0)
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (330, -80)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (330, 90)
    set_socket(shader, "Base Color", (*color, 1.0))
    set_socket(shader, "Roughness", 0.92)
    set_socket(shader, ("Emission Color", "Emission"), (*color, 1.0))
    set_socket(shader, "Emission Strength", emission_strength)

    info = nodes.new("ShaderNodeObjectInfo")
    info.location = (-720, 120)
    phase = nodes.new("ShaderNodeMath")
    phase.operation = "MULTIPLY"
    phase.inputs[1].default_value = math.tau
    phase.location = (-540, 150)
    links.new(info.outputs["Random"], phase.inputs[0])
    time = nodes.new("ShaderNodeValue")
    time.name = "Animated_Time"
    time.location = (-720, -40)
    time.outputs[0].default_value = 0.0
    driver = time.outputs[0].driver_add("default_value").driver
    driver.expression = "frame / 24.0"
    speed = nodes.new("ShaderNodeMath")
    speed.operation = "MULTIPLY"
    speed.inputs[1].default_value = fade_speed
    speed.location = (-540, -20)
    links.new(time.outputs[0], speed.inputs[0])
    add_phase = nodes.new("ShaderNodeMath")
    add_phase.operation = "ADD"
    add_phase.location = (-370, 80)
    links.new(phase.outputs[0], add_phase.inputs[0])
    links.new(speed.outputs[0], add_phase.inputs[1])
    sine = nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    sine.location = (-210, 80)
    links.new(add_phase.outputs[0], sine.inputs[0])
    remap = nodes.new("ShaderNodeMapRange")
    remap.location = (-40, 90)
    remap.clamp = True
    set_socket(remap, "From Min", -1.0)
    set_socket(remap, "From Max", 1.0)
    set_socket(remap, "To Min", 0.06)
    set_socket(remap, "To Max", opacity)
    links.new(sine.outputs[0], remap.inputs["Value"])
    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (480, 0)
    links.new(remap.outputs["Result"], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(shader.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    return material


dust_material = make_particle_material("ENV_MAT_Dust_Particle", (0.50, 0.35, 0.20), 0.0, 0.065, 0.75)
insect_material = make_particle_material("ENV_MAT_Insect_Particle", (1.0, 0.42, 0.10), 0.08, 0.18, 1.35)


def make_particle_mesh(name, material):
    mesh = bpy.data.meshes.new(name)
    verts = [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
    faces = [(0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2), (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(material)
    return mesh


dust_mesh = make_particle_mesh("ENV_Dust_Shared_Mesh", dust_material)
insect_mesh = make_particle_mesh("ENV_Insect_Shared_Mesh", insect_material)
dust_rig = bpy.data.collections.new("ENV_Dust_Particle_Rig")
insect_rig = bpy.data.collections.new("ENV_Insect_Particle_Rig")
particle_collection.children.link(dust_rig)
particle_collection.children.link(insect_rig)


def animate_particle(obj, start, middle, end):
    obj.location = start
    obj.keyframe_insert(data_path="location", frame=1)
    obj.location = middle
    obj.keyframe_insert(data_path="location", frame=120)
    obj.location = end
    obj.keyframe_insert(data_path="location", frame=240)


for index in range(52):
    z = random.uniform(0.18, 3.95)
    max_radius = 0.18 + (4.0 - z) / 4.0 * 1.82
    radius = math.sqrt(random.random()) * max_radius * 0.88
    angle = random.uniform(0.0, math.tau)
    start = Vector((-1.39 + math.cos(angle) * radius, math.sin(angle) * radius, z))
    middle = start + Vector((random.uniform(-0.16, 0.16), random.uniform(-0.16, 0.16), random.uniform(0.06, 0.26)))
    end = middle + Vector((random.uniform(-0.12, 0.12), random.uniform(-0.12, 0.12), random.uniform(0.05, 0.22)))
    obj = bpy.data.objects.new(f"ENV_Dust_{index:03d}", dust_mesh)
    dust_rig.objects.link(obj)
    size = random.uniform(0.0025, 0.0065)
    obj.scale = (size, size, size)
    obj.rotation_euler = tuple(random.uniform(0.0, math.tau) for _ in range(3))
    animate_particle(obj, start, middle, end)

for index in range(10):
    start = Vector((-1.33 + random.uniform(-0.42, 0.42), random.uniform(-0.38, 0.38), 4.08 + random.uniform(-0.24, 0.24)))
    middle = Vector((-1.33 + random.uniform(-0.44, 0.44), random.uniform(-0.40, 0.40), 4.08 + random.uniform(-0.25, 0.25)))
    end = Vector((-1.33 + random.uniform(-0.42, 0.42), random.uniform(-0.38, 0.38), 4.08 + random.uniform(-0.24, 0.24)))
    obj = bpy.data.objects.new(f"ENV_Insect_{index:03d}", insect_mesh)
    insect_rig.objects.link(obj)
    size = random.uniform(0.004, 0.009)
    obj.scale = (size, size * random.uniform(0.45, 0.80), size * random.uniform(0.45, 0.80))
    obj.rotation_euler = tuple(random.uniform(0.0, math.tau) for _ in range(3))
    animate_particle(obj, start, middle, end)

checkpoint("instanced_particle_rigs")


old_camera = bpy.data.objects.get("Camera")
if old_camera:
    old_camera.hide_viewport = True
    old_camera.hide_render = True
camera_data = bpy.data.cameras.new("ENV_Camera_Cinematic")
camera = bpy.data.objects.new("ENV_Camera_Cinematic", camera_data)
camera_collection.objects.link(camera)
camera.location = (6.2, -9.2, 3.25)
camera_data.lens = 51.0
camera_data.sensor_width = 36.0
aim(camera, (-0.30, 0.0, 2.02))
focus = bpy.data.objects.new("ENV_Camera_Focus", None)
camera_collection.objects.link(focus)
focus.location = (-0.35, 0.0, 2.05)
camera_data.dof.use_dof = True
camera_data.dof.focus_object = focus
camera_data.dof.aperture_fstop = 4.0
bpy.context.scene.camera = camera
checkpoint("camera")


scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.filepath = "//../renders/streetlight_night_final.png"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 240
scene.eevee.taa_render_samples = 64
scene.eevee.volumetric_tile_size = "4"
scene.eevee.volumetric_samples = 64
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_shadow_samples = 16
scene.eevee.volumetric_start = 0.1
scene.eevee.volumetric_end = 40.0
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
scene.view_settings.exposure = 1.45

scene["environment_description"] = (
    "Optimized cinematic night road with procedural asphalt, curb, sidewalk, warm volumetric streetlight, "
    "subtle world haze, and native dust/insect particle systems. Existing streetlight geometry preserved."
)
scene["environment_render_engine"] = "Eevee"
scene["existing_streetlight_geometry_preserved"] = True
checkpoint("render_settings")

bpy.data.libraries.write(
    OUTPUT_PATH,
    set(bpy.data.scenes),
    path_remap="RELATIVE_ALL",
    fake_user=True,
    compress=True,
)
print("SAVED", OUTPUT_PATH)
print("OBJECTS", len(bpy.data.objects), "MATERIALS", len(bpy.data.materials))
