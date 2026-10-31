"""22×22×6.6 cm 现成盒子贴纸 demo 的效果图（由 box_mockup.py 改尺寸和贴图）。

原说明：《我不是韭菜！》（交易物种起源）外包装效果图（Blender 4.x 后台运行）。

    blender -b --factory-startup --python delivery/box22_mockup.py -- [draft] [shot=hero|top]

盒子按印刷说明做成天地盖礼盒：外形 305×220×62 mm；盒盖贴纸 300×215、长边侧标 300×50、短边侧标 215×50。
贴图直接用 print/out 里的印刷 PDF：pdftoppm 转成 PNG、裁掉出血，放在 /tmp/boxmock/tex_*.png。
桌上摆 3 个手办（3d/figurines/<物种>/web.glb，缩到 60 mm）、插了头饰的蛋形棋子、物种币和几张 A6 卡。
"""
import json
import math
import pathlib
import sys

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEX = pathlib.Path("/tmp/box22mock")
TOKENS = ROOT / "3d" / "tokens"
OUT = ROOT / "delivery" / "previews" / "盒子22cm"
MM = 0.001
W, D, H = 220 * MM, 220 * MM, 66 * MM

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DRAFT = "draft" in ARGS
SHOT = next((a.split("=", 1)[1] for a in ARGS if a.startswith("shot=")), "hero")

BOX = "#0E2A27"  # 和侧标底色一致（print/src/c_box.py 的 SPINE）
CREAM = "#EFE4CD"
SPECIES_COLOR = {"cheetah": "#C79A2E", "elephant": "#8C8A84", "fox": "#D9772B", "owl": "#2D3E5C",
                 "meerkat": "#D8BE8C", "chameleon": "#3F8C8C", "beaver": "#7A5230"}


def srgb(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def mat_color(name, hexstr, rough=0.5, bump=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(hexstr)
    bsdf.inputs["Roughness"].default_value = rough
    if bump:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 900.0
        noise.inputs["Detail"].default_value = 6.0
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.0004
        nt.links.new(noise.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def mat_image(name, path, rough=0.42):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return m


def plane(name, w, h, loc, rot_deg, mat, thick=0.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=[math.radians(a) for a in rot_deg])
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(mat)
    if thick:
        sol = ob.modifiers.new("solid", "SOLIDIFY")
        sol.thickness = thick
        sol.offset = -1.0
    return ob


def box():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
    ob = bpy.context.object
    ob.name = "box"
    ob.scale = (W, D, H)
    bpy.ops.object.transform_apply(scale=True)
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width = 0.9 * MM
    bev.segments = 4
    bev.limit_method = "ANGLE"
    ob.data.materials.append(mat_color("box", BOX, rough=0.62, bump=0.06))
    off = 0.12 * MM
    tex = {k: mat_image(k, TEX / f"tex_{k}.png", rough=0.4) for k in ("top", "front", "right", "back", "left")}
    plane("label_top", 214 * MM, 214 * MM, (0, 0, H + off), (0, 0, 0), tex["top"])
    plane("label_front", 220 * MM, 66 * MM, (0, -D / 2 - off, H / 2), (90, 0, 0), tex["front"])
    plane("label_back", 220 * MM, 66 * MM, (0, D / 2 + off, H / 2), (90, 0, 180), tex["back"])
    plane("label_right", 220 * MM, 66 * MM, (W / 2 + off, 0, H / 2), (90, 0, 90), tex["right"])
    plane("label_left", 220 * MM, 66 * MM, (-W / 2 - off, 0, H / 2), (90, 0, -90), tex["left"])


def cyclorama():
    import bmesh
    prof = [(-1.6, 0.0), (0.42, 0.0)]
    r, cy = 0.55, 0.42
    for i in range(1, 17):
        a = -math.pi / 2 + (math.pi / 2) * i / 16
        prof.append((cy + r * math.cos(a), r + r * math.sin(a)))
    prof.append((cy + r, 2.4))
    me = bpy.data.meshes.new("cyc")
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-2.5, 2.5)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("cyc", me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat_color("floor", CREAM, rough=0.92, bump=0.02))


def bounds(objs):
    pts = []
    for o in objs:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def figurine(sp, x, y, rot_z, height=60 * MM):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / "3d" / "figurines" / sp / "web.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(f"fig_{sp}", None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    lo, hi = bounds(new)
    s = height / (hi.z - lo.z)
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    lo, hi = bounds(new)
    root.location = (x - (lo.x + hi.x) / 2, y - (lo.y + hi.y) / 2, -lo.z)
    bpy.context.view_layer.update()
    pivot = bpy.data.objects.new(f"pivot_{sp}", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = (x, y, 0)
    bpy.context.view_layer.update()
    root.parent = pivot
    root.matrix_parent_inverse = pivot.matrix_world.inverted()
    pivot.rotation_euler = (0, 0, math.radians(rot_z))


def stl(name, mat):
    bpy.ops.wm.stl_import(filepath=str(TOKENS / f"{name}.stl"))
    ob = bpy.context.selected_objects[0]
    ob.scale = (MM, MM, MM)
    bpy.ops.object.transform_apply(scale=True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        pass
    ob.data.materials.append(mat)
    return ob


def place_flat(ob, x, y, rot_z=0.0):
    bpy.context.view_layer.update()
    lo, hi = bounds([ob])
    ob.location.x += x - (lo.x + hi.x) / 2
    ob.location.y += y - (lo.y + hi.y) / 2
    ob.location.z += -lo.z
    ob.rotation_euler.z = math.radians(rot_z)


def egg(sp, egg_hex, x, y):
    report = json.loads((TOKENS / "tokens_report.json").read_text(encoding="utf-8"))
    hole = report["pawn_egg"]["hole_bottom_z_mm"] * MM
    e = stl("pawn_egg", mat_color(f"egg_{sp}", egg_hex, rough=0.38))
    c = stl(f"species_crest_{sp}", mat_color(f"crest_{sp}", SPECIES_COLOR[sp], rough=0.42))
    e.location = (x, y, 0)
    c.location = (x, y, hole)


def coin(sp, x, y, rot_z):
    ob = stl(f"coin_{sp}", mat_color(f"coin_{sp}", SPECIES_COLOR[sp], rough=0.36))
    place_flat(ob, x, y, rot_z)


def card(n, x, y, rot_z):
    m = mat_image(f"card{n}", TEX / f"tex_card{n}.png", rough=0.48)
    ob = plane(f"card{n}", 105 * MM, 148 * MM, (x, y, 0.0), (0, 0, rot_z), m, thick=0.35 * MM)
    ob.location.z = 0.36 * MM
    return ob


def props():
    # 卡牌扇形铺在左前方，一角压在盒子下面；后放的压在上面
    for i, (n, x, y, r) in enumerate([(2, -0.205, -0.150, 24), (6, -0.150, -0.172, 11), (23, -0.088, -0.185, -3)]):
        ob = card(n, x, y, r)
        ob.location.z += i * 0.42 * MM
    # 手办站在右前方，转向镜头
    figurine("owl", 0.010, -0.168, 24)
    figurine("fox", 0.088, -0.182, 30)
    figurine("cheetah", 0.168, -0.160, 36)
    # 蛋形棋子 + 头饰、物种币
    egg("elephant", "#F4F0E6", -0.035, -0.232)
    egg("meerkat", "#4E8792", 0.004, -0.250)
    for sp, x, y, r in [("cheetah", 0.052, -0.226, 12), ("fox", 0.080, -0.242, -20), ("owl", 0.140, -0.214, 40), ("chameleon", 0.118, -0.240, 5)]:
        coin(sp, x, y, r)


def area(name, loc, target, size, energy, color):
    lt = bpy.data.lights.new(name, "AREA")
    lt.size, lt.energy, lt.color = size, energy, color
    ob = bpy.data.objects.new(name, lt)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def camera(target, az_deg, el_deg, dist, lens, fstop):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = Vector(target)
    cam.location = t + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = dist
    cam.data.dof.aperture_fstop = fstop
    return cam


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    box()
    cyclorama()
    props()

    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb(CREAM)
    bg.inputs["Strength"].default_value = 0.3

    area("key", (-0.55, -0.50, 0.80), (0.0, -0.04, 0.03), 0.9, 16, (1.0, 0.94, 0.86))
    area("fill", (0.80, -0.55, 0.38), (0.0, -0.04, 0.03), 1.4, 5, (0.93, 0.96, 1.0))
    area("rim", (0.25, 0.75, 0.75), (0.0, 0.0, 0.04), 1.0, 8, (1.0, 0.97, 0.92))

    if SHOT == "top":
        camera((0.0, -0.06, 0.0), 6, 64, 0.95, 50, 8.0)
    else:
        camera((0.0, -0.07, 0.035), 32, 33, 0.66, 50, 7.1)

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16 if DRAFT else 192
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = not DRAFT
    scene.cycles.max_bounces = 8
    scene.render.resolution_x, scene.render.resolution_y = 1800, 1200
    scene.render.resolution_percentage = 35 if DRAFT else 100
    try:
        scene.view_settings.view_transform = "Khronos PBR Neutral"
    except TypeError:
        scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    name = {"hero": "盒子22cm_效果图.jpg", "top": "盒子22cm_俯视.jpg"}[SHOT]
    out = pathlib.Path("/tmp") / f"draft_{name}" if DRAFT else OUT / name
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print("BOX_MOCKUP_OK", out)


main()
