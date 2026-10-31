"""矢量小部件：仓位圆点、勾选框、玩家形状、物种印章、季节徽、警示角标、箭头。都是内联 SVG，单位 mm。"""

from __future__ import annotations

import math

from .core import esc
from .tokens import C, SEASON, SPECIES_CN, SPECIES_COLOR, SPECIES_SEAL


def dots(k: int, total: int = 3, d: float = 2.6, gap: float = 0.9, color=None, hollow=None, stroke=0.32) -> str:
    """仓位圆点 ●●○：k 个实心，其余空心。"""
    color = color or C["ink"]
    hollow = hollow or color
    w = total * d + (total - 1) * gap
    out = [f'<svg class="dots-svg" width="{w:.2f}mm" height="{d:.2f}mm" viewBox="0 0 {w:.3f} {d:.3f}" style="vertical-align:-0.12em">']
    r = d / 2
    for i in range(total):
        cx = r + i * (d + gap)
        if i < k:
            out.append(f'<circle cx="{cx:.3f}" cy="{r:.3f}" r="{r:.3f}" fill="{color}"/>')
        else:
            out.append(f'<circle cx="{cx:.3f}" cy="{r:.3f}" r="{r - stroke / 2:.3f}" fill="none" stroke="{hollow}" stroke-width="{stroke}"/>')
    out.append("</svg>")
    return "".join(out)


def box(size: float = 3.2, color=None, stroke=0.3, radius=0.5, fill="none") -> str:
    color = color or C["ink"]
    s = size
    return (f'<svg class="cb" width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.15em;flex:none">'
            f'<rect x="{stroke / 2:.3f}" y="{stroke / 2:.3f}" width="{s - stroke:.3f}" height="{s - stroke:.3f}" rx="{radius}" '
            f'fill="{fill}" stroke="{color}" stroke-width="{stroke}"/></svg>')


def circle_box(size=3.2, color=None, stroke=0.3) -> str:
    color = color or C["ink"]
    s = size
    return (f'<svg class="cb" width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.15em;flex:none">'
            f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2 - stroke / 2:.3f}" fill="none" stroke="{color}" stroke-width="{stroke}"/></svg>')


def shape_path(shape: str, cx: float, cy: float, r: float) -> str:
    if shape == "circle":
        return f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}"/>'
    if shape == "square":
        a = r * 0.88
        return f'<rect x="{cx - a:.3f}" y="{cy - a:.3f}" width="{2 * a:.3f}" height="{2 * a:.3f}" rx="{r * 0.08:.3f}"/>'
    if shape == "triangle":
        pts = [(cx, cy - r), (cx + r * 0.95, cy + r * 0.72), (cx - r * 0.95, cy + r * 0.72)]
    elif shape == "diamond":
        pts = [(cx, cy - r), (cx + r * 0.85, cy), (cx, cy + r), (cx - r * 0.85, cy)]
    elif shape == "star":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang) + r * 0.08))
    else:
        return f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}"/>'
    return '<polygon points="' + " ".join(f"{x:.3f},{y:.3f}" for x, y in pts) + '"/>'


def shape(shape: str, size: float = 4, color=None, stroke=None) -> str:
    color = color or C["ink"]
    s = size
    st = f' stroke="{stroke}" stroke-width="0.35"' if stroke else ""
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.15em;flex:none">'
            f'<g fill="{color}"{st}>{shape_path(shape, s / 2, s / 2, s / 2 - 0.25)}</g></svg>')


def tri(up: bool, size=2.4, color=None) -> str:
    color = color or (C["up"] if up else C["down"])
    s = size
    pts = f"{s / 2},0.2 {s - 0.1},{s - 0.3} 0.1,{s - 0.3}" if up else f"0.1,0.3 {s - 0.1},0.3 {s / 2},{s - 0.2}"
    return f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.05em"><polygon points="{pts}" fill="{color}"/></svg>'


def warn_corner(size=9.0, tone="mustard") -> str:
    """风险类证据牌角标：芥黄三角 + 叹号（不用红绿）。"""
    s = size
    col = C[tone]
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}">'
            f'<polygon points="{s / 2},0.6 {s - 0.4},{s - 0.8} 0.4,{s - 0.8}" fill="{col}" stroke="{C["ink"]}" stroke-width="0.45" stroke-linejoin="round"/>'
            f'<rect x="{s / 2 - 0.45:.2f}" y="{s * 0.32:.2f}" width="0.9" height="{s * 0.30:.2f}" rx="0.3" fill="{C["ink"]}"/>'
            f'<circle cx="{s / 2}" cy="{s * 0.72:.2f}" r="0.55" fill="{C["ink"]}"/></svg>')


def hazard(w: float, h: float, a=None, b=None, step=2.2) -> str:
    a = a or C["mustard"]
    b = b or C["ink"]
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="display:block">',
           f'<rect width="{w}" height="{h}" fill="{a}"/>',
           f'<clipPath id="hz{int(w * 10)}{int(h * 10)}"><rect width="{w}" height="{h}"/></clipPath><g clip-path="url(#hz{int(w * 10)}{int(h * 10)})" fill="{b}">']
    x = -h
    while x < w + h:
        out.append(f'<polygon points="{x:.2f},{h} {x + step / 2:.2f},{h} {x + step / 2 + h:.2f},0 {x + h:.2f},0"/>')
        x += step
    out.append("</g></svg>")
    return "".join(out)


def seal(sid: str, size: float = 9, ring=True, char=None, color=None, text_color=None) -> str:
    """物种印章：彩色圆 + 单字（瘦金体不用，统一 Smiley）。"""
    col = color or SPECIES_COLOR.get(sid, C["ink"])
    ch = char or SPECIES_SEAL.get(sid, "?")
    tc = text_color or C["paper_light"]
    s = size
    rg = (f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2 - 0.9:.2f}" fill="none" stroke="{tc}" stroke-width="0.3" opacity="0.9"/>' if ring else "")
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="flex:none">'
            f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2}" fill="{col}"/>{rg}'
            f'<text x="{s / 2}" y="{s / 2 + s * 0.2:.2f}" font-size="{s * 0.56:.2f}" text-anchor="middle" fill="{tc}" '
            f'font-family="Smiley Sans Oblique">{esc(ch)}</text></svg>')


def season_disc(season: str, size=10.0, label=None) -> str:
    col = SEASON[season]["color"]
    ch = label or SEASON[season]["cn"]
    s = size
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="flex:none">'
            f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2}" fill="{col}"/>'
            f'<text x="{s / 2}" y="{s / 2 + s * 0.21:.2f}" font-size="{s * 0.6:.2f}" text-anchor="middle" fill="{C["paper_light"]}" '
            f'font-family="Smiley Sans Oblique">{esc(ch)}</text></svg>')


def arrow_right(w=6, h=3, color=None, sw=0.45) -> str:
    color = color or C["ink"]
    return (f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" style="vertical-align:-0.1em;flex:none">'
            f'<path d="M0.3 {h / 2} H{w - 0.6} M{w - h / 2 - 0.3} 0.4 L{w - 0.4} {h / 2} L{w - h / 2 - 0.3} {h - 0.4}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def sun_rays(w: float, h: float, cx: float, cy: float, n=24, color=None, opacity=0.18) -> str:
    """海报式放射光线背景。"""
    color = color or C["sun"]
    R = math.hypot(max(cx, w - cx), max(cy, h - cy)) + 2
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" style="position:absolute;left:0;top:0">',
           f'<g fill="{color}" opacity="{opacity}">']
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        out.append(f'<polygon points="{cx:.2f},{cy:.2f} {cx + R * math.cos(a0):.2f},{cy + R * math.sin(a0):.2f} {cx + R * math.cos(a1):.2f},{cy + R * math.sin(a1):.2f}"/>')
    out.append("</g></svg>")
    return "".join(out)


def star(size=3.0, color=None, hollow=False) -> str:
    color = color or C["mustard"]
    s = size
    body = shape_path("star", s / 2, s / 2, s / 2 - 0.2)
    if hollow:
        return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.12em;flex:none">'
                f'<g fill="none" stroke="{color}" stroke-width="0.3">{body}</g></svg>')
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="vertical-align:-0.12em;flex:none">'
            f'<g fill="{color}">{body}</g></svg>')
