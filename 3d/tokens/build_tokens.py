#!/usr/bin/env python3.11
"""《交易物种起源》令牌 STL 参数化生成（manifold3d 布尔建模，输出天然是封闭流形）。

用法：
    python3.11 build_tokens.py              # 生成全部 STL + 总览图 preview_all.png
    python3.11 build_tokens.py --no-render  # 只生成 STL 和检查报告
    python3.11 build_tokens.py --crests     # 额外生成物种头饰 + preview_crests.png
                                            # （需要先有 3d/figurines/<sp>/print.stl，颈部高度见 crest_necks.json）

坐标：毫米，Z 向上，底面在 z=0，按打印姿态摆放（平放；除头饰外都无需支撑，立架卡槽只后倾 15°，也不用支撑）。
每个文件生成后都做检查：manifold3d 状态、trimesh 封闭/定向/单体、底面贴床面积、
悬垂面（法线朝下超过 45° 且不在床面上）面积和最大跨度，结果写进 tokens_report.json。
"""
import json
import math
import pathlib
import subprocess
import sys

import numpy as np
import trimesh
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, JoinType, Manifold, OpType

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONT = "/root/.fonts/NotoSansSC-Bold.otf"
SEG = 160

SPECIES = {  # id: (汉字, 建议颜色名, 预览用 sRGB)
    "cheetah": ("豹", "芥末黄", "#C79A2E"),
    "elephant": ("象", "石灰", "#8C8A84"),
    "fox": ("狐", "橙", "#D9772B"),
    "owl": ("鹰", "藏青", "#2D3E5C"),
    "meerkat": ("獴", "沙色", "#D8BE8C"),
    "chameleon": ("变", "青蓝", "#3F8C8C"),
    "beaver": ("狸", "木棕", "#7A5230"),
}

# ---------------------------------------------------------------- 字形


class FlattenPen(BasePen):
    """把字形轮廓里的二次/三次贝塞尔曲线拆成折线。"""

    def __init__(self, glyph_set, steps=24):
        super().__init__(glyph_set)
        self.contours, self.cur, self.steps = [], None, steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            m = 1 - t
            self.cur.append(tuple(m ** 3 * a + 3 * m * m * t * b + 3 * m * t * t * c + t ** 3 * d
                                  for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            m = 1 - t
            self.cur.append(tuple(m * m * a + 2 * m * t * b + t * t * c for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if self.cur and len(self.cur) > 2:
            pts = self.cur[:-1] if self.cur[0] == self.cur[-1] else self.cur
            self.contours.append(np.array(pts, float))
        self.cur = None

    _endPath = _closePath


_font = {}


def glyph(ch, size):
    """汉字 → CrossSection（非零环绕规则），墨迹外框的长边缩放到 size 毫米，并居中。"""
    if "font" not in _font:
        f = TTFont(FONT)
        _font["font"], _font["cmap"], _font["gs"] = f, f.getBestCmap(), f.getGlyphSet()
    pen = FlattenPen(_font["gs"])
    _font["gs"][_font["cmap"][ord(ch)]].draw(pen)
    cs = CrossSection(pen.contours, FillRule.NonZero)
    x0, y0, x1, y1 = cs.bounds()
    s = size / max(x1 - x0, y1 - y0)
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((s, s)).simplify(0.004)


# ---------------------------------------------------------------- 基本形体


def poly(points):
    return CrossSection([np.asarray(points, float)], FillRule.NonZero)


def rounded_rect(w, h, r, center=(0.0, 0.0)):
    cs = CrossSection.square((w - 2 * r, h - 2 * r), center=True).offset(r, JoinType.Round, 2.0, SEG)
    return cs.translate(center)


def chamfered_prism(cs, h, c_bot, c_top):
    """凸轮廓 → 上下边带 45° 倒角的柱体（三层截面求凸包）。"""
    eps = 0.002
    parts = [cs.extrude(h - c_bot - c_top).translate((0, 0, c_bot))]
    if c_bot > 0:
        parts.append(cs.offset(-c_bot, JoinType.Round, 2.0, SEG).extrude(eps))
    if c_top > 0:
        parts.append(cs.offset(-c_top, JoinType.Round, 2.0, SEG).extrude(eps).translate((0, 0, h - eps)))
    return Manifold.batch_hull(parts)


def disc(d, t, chamfer):
    r = d / 2
    return poly([(0, 0), (r - chamfer, 0), (r, chamfer), (r, t - chamfer), (r - chamfer, t), (0, t)]).revolve(SEG)


def medallion(d, t, rim, relief, icon, chamfer=0.5, draft=0.3):
    """圆币：外圈凸边，币面下沉 relief，图案浮雕与凸边齐平（总厚度 = t）。"""
    body = disc(d, t, chamfer)
    fr = d / 2 - rim
    h = relief + 0.5
    pocket = Manifold.cylinder(h, fr, fr + draft * h / relief, SEG).translate((0, 0, t - relief))
    icon = icon ^ CrossSection.circle(fr - 0.2, SEG)
    raised = icon.extrude(relief + 0.02).translate((0, 0, t - relief - 0.02))
    return body - pocket + raised


def engrave(body, cs, depth, top=None):
    """在底面（top=None）或顶面 z=top 处凹刻轮廓。"""
    cut = cs.extrude(depth + 0.02)
    cut = cut.translate((0, 0, -0.02)) if top is None else cut.translate((0, 0, top - depth))
    return body - cut


# ---------------------------------------------------------------- 各令牌


def coin(ch):
    """物种币 Ø22×3：正面实心浮雕字（字高 12，浮雕 0.8）；反面同字空心轮廓：
    沿字形边界刻一圈 0.65 宽、0.6 深的槽（外扩 0.45、内收 0.2），槽里的笔画保留 ≥0.6 mm，0.4 喷嘴打得出。"""
    g = glyph(ch, 12.0)
    body = medallion(22.0, 3.0, rim=1.4, relief=0.8, icon=g)
    return engrave(body, coin_back_outline(g), 0.6)


def coin_back_outline(g):
    back = g.mirror((1, 0))  # 翻过来从背面看是正字
    return back.offset(0.45, JoinType.Round, 2.0, 24) - back.offset(-0.2, JoinType.Round, 2.0, 24)


def research_point():
    """研究点 Ø15×3：放大镜浮雕。"""
    cx, cy = -0.8, 0.8
    ring = (CrossSection.circle(3.1, SEG) - CrossSection.circle(1.9, SEG)).translate((cx, cy))
    u = np.array([1, -1]) / math.sqrt(2)
    a = np.array([cx, cy]) + u * 2.7
    b = np.array([cx, cy]) + u * 5.9
    handle = CrossSection.batch_hull([CrossSection.circle(0.85, 48).translate(tuple(a)),
                                      CrossSection.circle(0.85, 48).translate(tuple(b))])
    return medallion(15.0, 3.0, rim=1.0, relief=0.8, icon=ring + handle, chamfer=0.45)


def vesica(w, h):
    """两段圆弧围成的杏仁形（眼形），宽 w 高 h。"""
    k = (w / 2) ** 2
    r = (k + (h / 2) ** 2) / h
    d = r - h / 2
    return CrossSection.circle(r, SEG).translate((0, -d)) ^ CrossSection.circle(r, SEG).translate((0, d))


def recognize_token():
    """认出令牌 Ø18×3：眼睛浮雕（杏仁形眼眶 + 虹膜，瞳孔下沉）。"""
    eye = vesica(13.0, 7.2)
    lid = eye - eye.offset(-1.05, JoinType.Round, 2.0, 48)
    iris = CrossSection.circle(2.5, SEG) - CrossSection.circle(0.95, SEG)
    return medallion(18.0, 3.0, rim=1.2, relief=0.8, icon=lid + iris, chamfer=0.5)


def plan_token():
    """计划令牌 24×24×3：顶面凹刻“走”，底面凹刻“加”（镜像，翻面看是正字），深 0.7。"""
    body = chamfered_prism(rounded_rect(24, 24, 3.0), 3.0, 0.5, 0.5)
    body = engrave(body, glyph("走", 14.0), 0.7, top=3.0)
    return engrave(body, glyph("加", 14.0).mirror((1, 0)), 0.7)


def shackle_profile(r_in, r_out, t, cb, ct):
    return poly([(r_in + cb, 0), (r_out - cb, 0), (r_out, cb), (r_out, t - ct),
                 (r_out - ct, t), (r_in + ct, t), (r_in, t - ct), (r_in, cb)])


def limit_down_lock():
    """跌停锁 20×24×4：挂锁平放，锁体 4 mm、锁梁 3 mm；锁体顶面凹刻向下箭头（跌）。"""
    body = chamfered_prism(rounded_rect(20, 14, 2.5, center=(0, 7)), 4.0, 0.4, 0.5)
    prof = shackle_profile(4.0, 7.0, 3.0, 0.3, 0.45)  # 倒角与锁体错开，避免共面薄片
    arch = prof.revolve(SEG, 180.0).translate((0, 17, 0))
    leg = prof.extrude(6.0).rotate((90, 0, 0)).translate((0, 17, 0))
    lock = body + arch + leg + leg.mirror((1, 0, 0))
    arrow = rounded_rect(2.6, 4.6, 0.4, center=(0, 9.8)) + poly([(-3.8, 8.0), (3.8, 8.0), (0, 3.0)])
    return engrave(lock, arrow, 1.0, top=4.0)


def marker_cube(s=10.0, c=0.8):
    """资金/方法星标记 10 mm 立方，全部棱边 0.8 mm 倒角。"""
    h, k = s / 2, s / 2 - c
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pts += [(sx * h, sy * k, sz * k), (sx * k, sy * h, sz * k), (sx * k, sy * k, sz * h)]
    return Manifold.hull_points(np.array(pts)).translate((0, 0, h))


def card_stand(width=70.0, depth=40.0, top=15.0, slot_w=1.2, slot_depth=11.0, tilt=75.0):
    """A6 卡牌立架：楔形底座，斜槽与水平面成 75°（向后仰 15°），槽宽 1.2，槽深 11。"""
    c = 0.6
    prof = poly([(c, 0), (depth - c, 0), (depth, c), (depth, 5.0), (23.0, top),
                 (10.0, top), (0, 6.0), (0, c)])
    m = np.array([[0, 0, 1, -width / 2], [1, 0, 0, 0], [0, 1, 0, 0]], float)
    main = prof.extrude(width - 2 * c).translate((0, 0, c)).transform(m)
    inset = prof.offset(-c, JoinType.Round, 2.0, 24)
    ends = [inset.extrude(0.002).transform(m), inset.extrude(0.002).translate((0, 0, width - 0.002)).transform(m)]
    body = Manifold.batch_hull([main] + ends)
    lean = 90.0 - tilt
    y_top = 15.0
    a = np.array([math.sin(math.radians(lean)), math.cos(math.radians(lean))])
    bottom = np.array([y_top, top]) - a * slot_depth
    slot = (Manifold.cube((width + 4, slot_w, 40.0)).translate((-(width + 4) / 2, -slot_w / 2, 0))
            .rotate((-lean, 0, 0)).translate((0, bottom[0], bottom[1])))
    return body - slot


def pawn_egg(height=32.0, **kw):
    """“未定物种”蛋形棋子：成品高 32，最大直径 22；底部在 45° 悬垂处切平（底面约 Ø14），
    顶部 Ø6 插孔深 5（从孔口算起），孔口 0.5 mm 倒角。开孔会削掉蛋尖，所以迭代放高轮廓。"""
    h = height
    for _ in range(4):
        egg, info = _egg(h, **kw)
        bb = egg.bounding_box()
        h += height - (bb[5] - bb[2])
    info["profile_height_mm"] = round(h, 3)
    return egg, info


def _egg(height, width=22.0, b_low=13.0, hole_d=6.0, hole_depth=5.0):
    a = width / 2
    q = b_low / a
    t = q / math.sqrt(1 + q * q)          # 下半椭圆斜率 = 1（45°）处
    z_eq = b_low * t
    b_up = height - z_eq
    phi_cut = math.asin(t)
    pts = [(0.0, 0.0)]
    for phi in np.linspace(phi_cut, 0, 60):
        pts.append((a * math.cos(phi), z_eq - b_low * math.sin(phi)))
    for psi in np.linspace(0, math.pi / 2, 120)[1:-1]:
        pts.append((a * math.cos(psi), z_eq + b_up * math.sin(psi)))
    pts.append((0.0, height))
    egg = poly(pts).revolve(SEG)
    r_h = hole_d / 2
    z_rim = z_eq + b_up * math.sin(math.acos(r_h / a))
    z_bot = z_rim - hole_depth
    hole = Manifold.cylinder(height + 1 - z_bot, r_h, circular_segments=96).translate((0, 0, z_bot))
    h = height + 1 - (z_rim - 0.5)
    mouth = Manifold.cylinder(h, r_h, r_h + h, circular_segments=96).translate((0, 0, z_rim - 0.5))
    info = {"bottom_diameter_mm": round(2 * a * math.cos(phi_cut), 2), "hole_rim_z_mm": round(z_rim, 2),
            "hole_bottom_z_mm": round(z_bot, 2)}
    return egg - hole - mouth, info


# ---------------------------------------------------------------- 物种头饰（可选）

def species_crest(sp, neck_z, head_h=13.0, max_w=20.0, peg_d=5.7, peg_len=4.8, flare_r=5.0):
    """从手办打印件截取头部，缩放到约 13 mm 高（宽不超过 20 mm），
    下接 45° 过渡锥（顶半径 ≤5 mm）和 Ø5.7×4.8 插销（配棋子 Ø6 孔）。"""
    src = trimesh.load(ROOT / "3d" / "figurines" / sp / "print.stl", process=True)
    fig = Manifold(_mesh(src))
    head = fig.trim_by_plane((0, 0, 1), neck_z)
    parts = sorted(head.decompose(), key=lambda m: -m.volume())
    head = parts[0]
    x0, y0, z0, x1, y1, z1 = head.bounding_box()
    s = min(head_h / (z1 - z0), max_w / max(x1 - x0, y1 - y0))
    head = head.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, -z0)).scale((s, s, s))
    neck = max(head.slice(0.05).decompose(), key=lambda c: c.area())  # 颈部主截面（不算耳尖、鼻尖等小块）
    nx0, ny0, nx1, ny1 = neck.bounds()
    cx, cy = (nx0 + nx1) / 2, (ny0 + ny1) / 2
    neck_r = float(np.max(np.linalg.norm(np.vstack(neck.to_polygons()) - (cx, cy), axis=1)))
    neck_r = min(neck_r, flare_r)
    r_p = peg_d / 2
    flare_h = max(neck_r - r_p, 0.4) + 0.4
    peg = Manifold.cylinder(peg_len + 0.01, r_p, circular_segments=96)
    flare = Manifold.cylinder(flare_h, r_p, r_p + flare_h, circular_segments=96).translate((0, 0, peg_len))
    stem = (peg + flare) ^ Manifold.cylinder(peg_len + flare_h, neck_r + 0.6, circular_segments=96)
    head = head.translate((-cx, -cy, peg_len + flare_h - 0.3))
    return stem + head


def _mesh(t):
    from manifold3d import Mesh
    return Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32))


# ---------------------------------------------------------------- 检查与导出


def to_trimesh(man):
    mg = man.to_mesh()
    return trimesh.Trimesh(np.asarray(mg.vert_properties)[:, :3].astype(np.float64),
                           np.asarray(mg.tri_verts), process=True)


def max_span(cs):
    """二维区域的最大内切圆直径（逐步向内偏移直到为空），用来估计桥接跨度。"""
    if cs.is_empty():
        return 0.0
    lo, hi = 0.0, 20.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if cs.offset(-mid, JoinType.Round, 2.0, 32).is_empty():
            hi = mid
        else:
            lo = mid
    return round(2 * lo, 2)


def check(name, man, bridges=None):
    zmin = man.bounding_box()[2]
    man = man.translate((0, 0, -zmin))
    t = to_trimesh(man)
    e = np.sort(t.edges, axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    fn, fa = t.face_normals, t.area_faces
    zc = t.triangles_center[:, 2]
    on_bed = (fn[:, 2] < -0.999) & (zc < 1e-4)
    over = (fn[:, 2] < -math.cos(math.radians(45)) - 1e-3) & ~on_bed
    x0, y0, z0, x1, y1, z1 = man.bounding_box()
    rep = {
        "size_mm": [round(x1 - x0, 2), round(y1 - y0, 2), round(z1 - z0, 2)],
        "manifold3d": str(man.status()),
        "watertight": bool(t.is_watertight),
        "winding_consistent": bool(t.is_winding_consistent),
        "bodies": int(t.body_count),
        "nonmanifold_edges": int((cnt > 2).sum()),
        "volume_mm3": round(float(man.volume()), 1),
        "faces": int(len(t.faces)),
        "bed_contact_mm2": round(float(fa[on_bed].sum()), 1),
        "overhang_gt45_mm2": round(float(fa[over].sum()), 2),
    }
    if bridges is not None:
        rep["bridge_max_span_mm"] = bridges
    ok = (rep["manifold3d"] == "Error.NoError" and rep["watertight"] and rep["winding_consistent"]
          and rep["bodies"] == 1 and rep["nonmanifold_edges"] == 0 and rep["bed_contact_mm2"] > 0)
    rep["ok"] = bool(ok)
    t.export(HERE / f"{name}.stl")
    print(f"{'OK ' if ok else 'BAD'} {name:28s} {rep['size_mm']}  体积 {rep['volume_mm3']} mm³  "
          f"贴床 {rep['bed_contact_mm2']} mm²  悬垂 {rep['overhang_gt45_mm2']} mm²", flush=True)
    return rep


def build(crests=False):
    report = {}
    egg, info = pawn_egg()
    report["pawn_egg"] = check("pawn_egg", egg) | info
    for sp, (ch, _, _) in SPECIES.items():
        span = max_span(coin_back_outline(glyph(ch, 12.0)))
        report[f"coin_{sp}"] = check(f"coin_{sp}", coin(ch), bridges=span) | {"char": ch}
    report["research_point"] = check("research_point", research_point())
    report["recognize_token"] = check("recognize_token", recognize_token())
    report["plan_token"] = check("plan_token", plan_token(), bridges=max_span(glyph("加", 14.0)))
    report["limit_down_lock"] = check("limit_down_lock", limit_down_lock())
    report["marker_cube"] = check("marker_cube", marker_cube())
    report["card_stand_a6"] = check("card_stand_a6", card_stand())
    if crests:
        necks = json.loads((HERE / "crest_necks.json").read_text(encoding="utf-8"))
        for sp, z in necks.items():
            if sp in SPECIES and (ROOT / "3d" / "figurines" / sp / "print.stl").exists():
                report[f"species_crest_{sp}"] = check(f"species_crest_{sp}", species_crest(sp, z))
    (HERE / "tokens_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [k for k, v in report.items() if not v["ok"]]
    print("全部通过" if not bad else f"未通过：{bad}")
    return report


if __name__ == "__main__":
    crests = "--crests" in sys.argv
    build(crests=crests)
    if "--no-render" not in sys.argv:
        cmd = ["blender", "-b", "--factory-startup", "--python", str(HERE / "render_preview.py")]
        subprocess.run(cmd, check=True)
        if crests:
            subprocess.run(cmd + ["--", "crests"], check=True)
