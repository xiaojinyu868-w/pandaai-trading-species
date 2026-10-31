"""令牌总览渲染（Blender 4.x 后台运行）：
    blender -b --factory-startup --python render_preview.py            # → preview_all.png
    blender -b --factory-startup --python render_preview.py -- crests  # → preview_crests.png
总览：读 tokens_report.json 里的文件顺序，把令牌 STL 按打印姿态排成一行（头饰除外）。
头饰：7 个蛋形棋子各插一个物种头饰，演示终局“破壳”。
暖米色底 #F2E6CC，颜色用 3D打印说明.md 里的建议耗材色。
"""
import json
import math
import pathlib
import subprocess
import sys

import bpy
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
CREAM = "#F2E6CC"
GAP = 7.0          # 件与件之间的间距（mm）
SCALE = 0.01       # 场景里 1 单位 = 100 mm，灯光参数和手办预览一致

COLORS = {
    "pawn_egg": "#4E8792",        # 玩家色示例：蓝 ■
    "coin_cheetah": "#C79A2E", "coin_elephant": "#8C8A84", "coin_fox": "#D9772B",
    "coin_owl": "#2D3E5C", "coin_meerkat": "#D8BE8C", "coin_chameleon": "#3F8C8C",
    "coin_beaver": "#7A5230",
    "research_point": "#F4F0E6",  # 白
    "recognize_token": "#2A2A1C",  # 黑
    "plan_token": "#6E4F8A",      # 玩家色示例：紫 ★
    "limit_down_lock": "#3C7A4E",  # 跌停 = 绿
    "marker_cube": "#F3D27F",     # 玩家色示例：黄 ◆
    "card_stand_a6": "#B07D3F",   # 任意色
}
SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
EGG_COLORS = ["#F4F0E6", "#2A2A1C", "#4E8792", "#F3D27F", "#6E4F8A", "#8C8A84", "#8C8A84"]  # 5 玩家色 + 2 AI 灰


def srgb(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def material(name, hexstr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(hexstr)
    bsdf.inputs["Roughness"].default_value = 0.42
    return mat


def load(name):
    bpy.ops.wm.stl_import(filepath=str(HERE / f"{name}.stl"))
    obj = bpy.context.selected_objects[0]
    obj.name = name
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        pass
    return obj


def frame_ortho(cam, objs, el_deg, fill_w=0.95, fill_h=0.80):
    """正前方俯视的正交相机，整排令牌保持水平、同一比例；按投影包围盒定 ortho_scale 并居中。"""
    scene = bpy.context.scene
    pts = [o.matrix_world @ v.co for o in objs for i, v in enumerate(o.data.vertices) if i % 5 == 0]
    target = sum(pts, Vector()) / len(pts)
    el = math.radians(el_deg)
    cam.data.type = "ORTHO"
    cam.location = target + Vector((0, -math.cos(el), math.sin(el))) * 20
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    rot = cam.matrix_world.to_3x3()
    right, up = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
    us, vs = [p.dot(right) for p in pts], [p.dot(up) for p in pts]
    aspect = scene.render.resolution_y / scene.render.resolution_x
    cam.data.ortho_scale = max((max(us) - min(us)) / fill_w, (max(vs) - min(vs)) / fill_h / aspect)
    cam.location += right * ((max(us) + min(us)) / 2 - target.dot(right)) \
        + up * ((max(vs) + min(vs)) / 2 - target.dot(up))


def bounds(obj):
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (Vector([min(p[i] for p in bb) for i in range(3)]),
            Vector([max(p[i] for p in bb) for i in range(3)]))


def token_row(report):
    names = [n for n in report if not n.startswith("species_crest_") and (HERE / f"{n}.stl").exists()]
    objs, x = [], 0.0
    for name in names:
        obj = load(name)
        obj.data.materials.append(material(name, COLORS[name]))
        lo, hi = bounds(obj)
        obj.location = (x - lo.x, -(lo.y + hi.y) / 2, -lo.z)
        x += hi.x - lo.x + GAP
        objs.append(obj)
    return objs, x - GAP


def crest_row(report):
    """每个蛋插一个头饰：头饰 z=0 是插销底，对齐蛋的孔底。"""
    hole_z = report["pawn_egg"]["hole_bottom_z_mm"]
    objs, x = [], 0.0
    for i, sp in enumerate(SPECIES):
        name = f"species_crest_{sp}"
        if not (HERE / f"{name}.stl").exists():
            continue
        egg = load("pawn_egg")
        egg.name = f"egg_{sp}"
        egg.data.materials.append(material(egg.name, EGG_COLORS[i]))
        crest = load(name)
        crest.data.materials.append(material(name, COLORS[f"coin_{sp}"]))
        lo, hi = bounds(crest)
        half = max(11.0, (hi.x - lo.x) / 2)
        egg.location = (x + half, 0, 0)
        crest.location = (x + half, 0, hole_z)
        x += 2 * half + GAP
        objs += [egg, crest]
    return objs, x - GAP


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    report = json.loads((HERE / "tokens_report.json").read_text(encoding="utf-8"))
    crests = "crests" in sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else False
    objs, width = crest_row(report) if crests else token_row(report)
    root = bpy.data.objects.new("row", None)
    bpy.context.scene.collection.objects.link(root)
    for obj in objs:
        obj.parent = root
    root.location = (-width / 2 * SCALE, 0, 0)
    root.scale = (SCALE,) * 3
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    # 约 290 万像素：再大的话降噪阶段峰值内存会超过 3.5 GB
    scene.render.resolution_x, scene.render.resolution_y = (2800, 1050) if crests else (3600, 800)
    scene.render.film_transparent = True
    try:
        scene.view_settings.view_transform = "Khronos PBR Neutral"
    except TypeError:
        scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -0.5  # 平放的令牌顶面正对灯光，比手办亮，压一点免得颜色发白
    if "draft" in sys.argv:
        scene.cycles.samples = 12
        scene.cycles.use_denoising = False
        scene.render.resolution_percentage = 50

    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = srgb(CREAM)
    bg.inputs["Strength"].default_value = 0.4

    bpy.ops.mesh.primitive_plane_add(size=40)
    bpy.context.object.is_shadow_catcher = True

    def sun(name, toward_light, strength, angle_deg, color):
        """平行光：整排令牌受光一致。主光从左侧低角度斜照，浮雕字的边缘才有影子。"""
        light = bpy.data.lights.new(name, "SUN")
        light.energy, light.angle, light.color = strength, math.radians(angle_deg), color
        ob = bpy.data.objects.new(name, light)
        scene.collection.objects.link(ob)
        ob.rotation_euler = Vector(toward_light).normalized().to_track_quat("Z", "Y").to_euler()

    sun("key", (-0.85, -0.3, 0.5), 2.8, 10, (1.0, 0.93, 0.84))
    sun("fill", (0.4, -0.9, 0.6), 0.9, 30, (0.92, 0.95, 1.0))
    sun("rim", (0.3, 0.9, 0.7), 0.8, 20, (1.0, 0.96, 0.9))

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.sensor_fit = "HORIZONTAL"
    frame_ortho(cam, objs, el_deg=25 if crests else 45)

    rgba = "/tmp/tokens_preview_rgba.png"
    scene.render.filepath = rgba
    bpy.ops.render.render(write_still=True)
    out = HERE / ("preview_crests.png" if crests else "preview_all.png")
    if "draft" in sys.argv:
        out = pathlib.Path("/tmp") / ("draft_" + out.name)
    code = ("from PIL import Image;import sys;"
            "fg=Image.open(sys.argv[1]).convert('RGBA');"
            "bg=Image.new('RGBA',fg.size,sys.argv[3]);"
            "Image.alpha_composite(bg,fg).convert('RGB').save(sys.argv[2])")
    subprocess.run(["python3.11", "-c", code, rgba, str(out), CREAM], check=True)
    print("TOKENS_PREVIEW_OK", out)


main()
