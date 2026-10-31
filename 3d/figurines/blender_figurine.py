"""Blender 后台脚本：tripo.glb → preview.png（3/4 角度渲染）+ web.glb（H5 用）。

用法：
    blender -b --factory-startup --python blender_figurine.py -- <species> [--skip-preview] [--skip-web]

- 朝向：Tripo 默认正面朝 glTF +X，这里转成标准 glTF 朝向（Y 上、正面 +Z，
  即 Blender 里正面朝 -Y），底座中心放到原点，高度归一到 1.0。
- web.glb：Collapse 减面 + 贴图缩到 1024 + JPEG，目标 ≤ 2.5 MB；超了就逐步降面数/质量。
- preview.png：Cycles 渲染，透明背景 + 阴影捕捉平面，最后叠到奶油底色 #F2E6CC 上。
"""
import math
import os
import pathlib
import subprocess
import sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SP = argv[0]
SKIP_PREVIEW = "--skip-preview" in argv
SKIP_WEB = "--skip-web" in argv

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = ROOT / "3d" / "figurines" / SP
H5 = ROOT / "h5" / "public" / "models"
CREAM = (0xF2, 0xE6, 0xCC)
WEB_LIMIT = 2.5 * 1024 * 1024
WEB_STEPS = [(60000, 1024, 85), (48000, 1024, 82), (38000, 1024, 80),
             (30000, 1024, 78), (24000, 1024, 75), (24000, 768, 75)]


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def load_normalized():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(D / "tripo.glb"))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    # Tripo 正面 +X（Blender）→ -Y（Blender）＝ glTF +Z
    x, y, z = co[:, 0].copy(), co[:, 1].copy(), co[:, 2].copy()
    co = np.column_stack([y, -x, z])
    h = co[:, 2].max() - co[:, 2].min()
    co /= h
    co[:, 2] -= co[:, 2].min()
    base = co[:, 2] < 0.008
    co[:, 0] -= (co[base, 0].min() + co[base, 0].max()) / 2
    co[:, 1] -= (co[base, 1].min() + co[base, 1].max()) / 2
    me.vertices.foreach_set("co", co.ravel())
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    obj.name = SP + "_src"
    me.name = SP
    for mat in me.materials:
        if mat:
            mat.name = SP
    for img in bpy.data.images:
        for prefix, tag in (("Color", "color"), ("NormalGL", "normal"), ("ORM", "orm")):
            if img.name.startswith(prefix):
                img.name = f"{SP}_{tag}"
    return obj


def frame_camera(cam, obj, az_deg, el_deg, fill=0.84):
    scene = bpy.context.scene
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)[:: max(1, len(me.vertices) // 20000)]
    target = Vector(((co[:, 0].min() + co[:, 0].max()) / 2,
                     (co[:, 1].min() + co[:, 1].max()) / 2,
                     (co[:, 2].min() + co[:, 2].max()) / 2))
    az, el = math.radians(az_deg), math.radians(el_deg)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    dist = 3.0
    for _ in range(6):
        cam.location = target + direction * dist
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        pts = [world_to_camera_view(scene, cam, Vector(p)) for p in co]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        ext = max(max(xs) - min(xs), max(ys) - min(ys))
        cx, cy = (max(xs) + min(xs)) / 2 - 0.5, (max(ys) + min(ys)) / 2 - 0.5
        dist *= ext / fill
        # 把投影中心挪回画面中央
        right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
        fov = cam.data.angle
        span = 2 * dist * math.tan(fov / 2)
        target = target + right * cx * span + up * cy * span
    cam.location = target + direction * dist
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, loc, target, size, energy, color):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "DISK"
    data.size = size
    data.energy = energy
    data.color = color
    o = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def render_preview(obj):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1500
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    world = bpy.data.worlds.new("cream")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*[srgb_to_linear(c) for c in CREAM], 1)
    bg.inputs[1].default_value = 0.55

    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.is_shadow_catcher = True

    add_area("key", (-1.6, -2.2, 2.6), (0, 0, 0.45), 2.4, 260, (1.0, 0.93, 0.84))
    add_area("fill", (2.4, -1.4, 1.2), (0, 0, 0.45), 3.0, 90, (0.92, 0.95, 1.0))
    add_area("rim", (0.8, 2.4, 2.0), (0, 0, 0.6), 1.6, 160, (1.0, 0.96, 0.9))

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 85
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 36
    frame_camera(cam, obj, az_deg=-35, el_deg=14)

    tmp = f"/tmp/preview_{SP}_rgba.png"
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(plane)
    for o in [o for o in scene.objects if o.type in ("LIGHT", "CAMERA")]:
        bpy.data.objects.remove(o)
    subprocess.run(["python3.11", "-c", (
        "from PIL import Image;"
        f"fg=Image.open('{tmp}').convert('RGBA');"
        f"bg=Image.new('RGBA',fg.size,{CREAM + (255,)});"
        f"Image.alpha_composite(bg,fg).convert('RGB').save('{D / 'preview.png'}',optimize=True)")],
        check=True)
    print("PREVIEW_OK", D / "preview.png")


def export_web(obj):
    src_faces = len(obj.data.polygons)
    images = {img.name: tuple(img.size) for img in bpy.data.images if img.size[0] > 0}
    out = D / "web.glb"
    chosen = None
    for faces, tex, quality in WEB_STEPS:
        bpy.ops.object.select_all(action="DESELECT")
        work = obj.copy()
        work.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(work)
        work.select_set(True)
        bpy.context.view_layer.objects.active = work
        mod = work.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = min(1.0, faces / src_faces)
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        for img in bpy.data.images:
            if img.name in images:
                w, h = images[img.name]
                if max(img.size) != tex:
                    img.reload()
                    img.scale(tex, tex)
        work.name = SP
        bpy.ops.export_scene.gltf(
            filepath=str(out), export_format="GLB", use_selection=True,
            export_apply=True, export_yup=True, export_texcoords=True,
            export_normals=True, export_tangents=False, export_materials="EXPORT",
            export_image_format="JPEG", export_image_quality=quality,
            export_draco_mesh_compression_enable=False, export_extras=False,
            export_cameras=False, export_lights=False, export_animations=False)
        size = out.stat().st_size
        tri = sum(len(p.vertices) - 2 for p in work.data.polygons)
        print(f"WEB_TRY faces={tri} tex={tex} q={quality} size={size / 1e6:.2f}MB")
        bpy.data.objects.remove(work)
        chosen = (tri, tex, quality, size)
        if size <= WEB_LIMIT:
            break
    H5.mkdir(parents=True, exist_ok=True)
    (H5 / f"{SP}.glb").write_bytes(out.read_bytes())
    print("WEB_OK", *chosen)


obj = load_normalized()
if not SKIP_PREVIEW:
    render_preview(obj)
if not SKIP_WEB:
    export_web(obj)
