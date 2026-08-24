import bpy


OUTPUT_PATH = bpy.path.abspath("//streetlight_textured.blend")


def set_socket(node, names, value):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def fresh_material(name, viewport_color):
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old, do_unlink=True)
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = viewport_color
    material.node_tree.nodes.clear()
    material["texture_style"] = "procedural_pbr"
    material["asset_role"] = "streetlight"
    return material


def noise_material(
    name,
    viewport_color,
    colors,
    metallic,
    roughness_range,
    texture_scale,
    mapping_scale,
    bump_strength,
    bump_distance,
):
    material = fresh_material(name, viewport_color)
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (650, 40)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (410, 40)
    set_socket(shader, "Metallic", metallic)
    set_socket(shader, "Roughness", sum(roughness_range) / 2)
    set_socket(shader, ("Coat Weight", "Clearcoat"), 0.12)
    set_socket(shader, ("Coat Roughness", "Clearcoat Roughness"), 0.32)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-760, 20)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-590, 20)
    mapping.inputs["Scale"].default_value = (*mapping_scale,)
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-390, 150)
    set_socket(noise, "Scale", texture_scale)
    set_socket(noise, "Detail", 7.0)
    set_socket(noise, "Roughness", 0.78)
    set_socket(noise, "Distortion", 0.22)
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-130, 180)
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    first = ramp.color_ramp.elements[0]
    first.position, first.color = colors[0]
    for position, color in colors[1:]:
        element = ramp.color_ramp.elements.new(position)
        element.color = color
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])

    roughness = nodes.new("ShaderNodeMapRange")
    roughness.location = (120, -70)
    set_socket(roughness, "From Min", 0.18)
    set_socket(roughness, "From Max", 0.82)
    set_socket(roughness, "To Min", roughness_range[0])
    set_socket(roughness, "To Max", roughness_range[1])
    links.new(noise.outputs["Fac"], roughness.inputs["Value"])
    links.new(roughness.outputs["Result"], shader.inputs["Roughness"])

    fine = nodes.new("ShaderNodeTexNoise")
    fine.location = (-360, -170)
    set_socket(fine, "Scale", texture_scale * 18.0)
    set_socket(fine, "Detail", 2.5)
    set_socket(fine, "Roughness", 0.68)
    links.new(mapping.outputs["Vector"], fine.inputs["Vector"])

    bump = nodes.new("ShaderNodeBump")
    bump.location = (150, -220)
    set_socket(bump, "Strength", bump_strength)
    set_socket(bump, "Distance", bump_distance)
    links.new(fine.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


painted_steel = noise_material(
    "SL_Painted_Steel_Weathered",
    (0.018, 0.030, 0.045, 1.0),
    [
        (0.12, (0.003, 0.006, 0.010, 1.0)),
        (0.46, (0.012, 0.026, 0.043, 1.0)),
        (0.70, (0.045, 0.067, 0.088, 1.0)),
        (0.84, (0.17, 0.032, 0.007, 1.0)),
        (0.94, (0.035, 0.011, 0.004, 1.0)),
    ],
    metallic=0.72,
    roughness_range=(0.38, 0.68),
    texture_scale=5.2,
    mapping_scale=(2.8, 7.0, 3.2),
    bump_strength=0.17,
    bump_distance=0.024,
)

cast_iron = noise_material(
    "SL_Cast_Iron_Base",
    (0.055, 0.030, 0.018, 1.0),
    [
        (0.10, (0.006, 0.007, 0.008, 1.0)),
        (0.38, (0.025, 0.018, 0.014, 1.0)),
        (0.58, (0.13, 0.026, 0.006, 1.0)),
        (0.76, (0.035, 0.015, 0.007, 1.0)),
        (0.92, (0.20, 0.050, 0.010, 1.0)),
    ],
    metallic=0.63,
    roughness_range=(0.60, 0.84),
    texture_scale=6.0,
    mapping_scale=(4.0, 4.0, 2.5),
    bump_strength=0.34,
    bump_distance=0.038,
)

galvanized_trim = noise_material(
    "SL_Galvanized_Trim",
    (0.16, 0.19, 0.23, 1.0),
    [
        (0.10, (0.045, 0.055, 0.070, 1.0)),
        (0.42, (0.12, 0.15, 0.18, 1.0)),
        (0.72, (0.28, 0.34, 0.40, 1.0)),
        (0.92, (0.085, 0.105, 0.13, 1.0)),
    ],
    metallic=0.84,
    roughness_range=(0.34, 0.52),
    texture_scale=28.0,
    mapping_scale=(1.0, 1.0, 1.0),
    bump_strength=0.10,
    bump_distance=0.014,
)


def make_warm_lens():
    material = fresh_material("SL_Frosted_Warm_Lens", (1.0, 0.34, 0.055, 1.0))
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (450, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (190, 0)
    set_socket(shader, "Base Color", (0.95, 0.28, 0.035, 1.0))
    set_socket(shader, "Roughness", 0.27)
    set_socket(shader, ("Transmission Weight", "Transmission"), 0.10)
    set_socket(shader, ("Emission Color", "Emission"), (1.0, 0.14, 0.018, 1.0))
    set_socket(shader, "Emission Strength", 7.0)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-440, -130)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-260, -120)
    set_socket(noise, "Scale", 34.0)
    set_socket(noise, "Detail", 2.0)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.location = (-40, -110)
    set_socket(bump, "Strength", 0.08)
    set_socket(bump, "Distance", 0.012)
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


warm_lens = make_warm_lens()

body = bpy.data.objects.get("Cube")
if body is None or body.type != "MESH":
    raise RuntimeError("The expected streetlight body object 'Cube' is missing")

body.data.materials.clear()
for material in (painted_steel, cast_iron, warm_lens):
    body.data.materials.append(material)

normal_matrix = body.matrix_world.to_3x3()
counts = {"painted": 0, "base": 0, "lens": 0}
for polygon in body.data.polygons:
    center = body.matrix_world @ polygon.center
    normal = (normal_matrix @ polygon.normal).normalized()
    if center.z < 0.80:
        polygon.material_index = 1
        counts["base"] += 1
    elif center.x < -1.04 and center.z < 4.18 and normal.z < -0.18:
        polygon.material_index = 2
        counts["lens"] += 1
    else:
        polygon.material_index = 0
        counts["painted"] += 1

for object_name in ("Cube.001", "Cube.002"):
    trim_object = bpy.data.objects.get(object_name)
    if trim_object and trim_object.type == "MESH":
        trim_object.data.materials.clear()
        trim_object.data.materials.append(galvanized_trim)
        for polygon in trim_object.data.polygons:
            polygon.material_index = 0

old_light = bpy.data.objects.get("Streetlight_Warm_Light")
if old_light:
    bpy.data.objects.remove(old_light, do_unlink=True)
light_data = bpy.data.lights.new("Streetlight_Warm_Light", "AREA")
light_data.energy = 420.0
light_data.color = (1.0, 0.31, 0.07)
light_data.shape = "RECTANGLE"
light_data.size = 0.58
light_data.size_y = 0.18
light_data.use_shadow = True
light_object = bpy.data.objects.new("Streetlight_Warm_Light", light_data)
bpy.context.collection.objects.link(light_object)
light_object.location = (-1.33, 0.0, 4.055)

bpy.context.scene["streetlight_texture_notes"] = (
    "Weathered charcoal painted steel, oxidized cast-iron base, galvanized trim, "
    "and a frosted warm emissive lens. All textures are procedural and packed in the file."
)
bpy.context.scene["streetlight_lens_face_count"] = counts["lens"]
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
print("ASSIGNMENT_COUNTS", counts)
print("SAVED", OUTPUT_PATH)
