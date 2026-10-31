"""SVG 图表（用户单位 = mm）。红涨绿跌只用于方向，同时配 ▲▼；线宽 ≥ 0.5pt，标注 ≥ 6pt。"""

from __future__ import annotations

import math

from .core import esc
from .tokens import C

PT = 0.3528  # 1pt = 0.3528 mm
F6 = 6 * PT
F65 = 6.5 * PT
F7 = 7 * PT
LW = 0.9 * PT  # 主线
LW_THIN = 0.55 * PT  # 辅助线（≥0.5pt）
# 标签衬底：用浅色小底块，不用描边光晕（描边文字在 Chromium PDF 里会变成 Type 3 字体）
HALO = "__halo__"


def _fmt(v, unit=""):
    if v is None:
        return ""
    a = abs(v)
    if a >= 1000:
        s = f"{v:,.0f}"
    elif a >= 100:
        s = f"{v:.0f}"
    elif a >= 10:
        s = f"{v:.1f}".rstrip("0").rstrip(".")
    else:
        s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _poly(pts):
    return " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)


def _scale(vals, lo, hi, y0, y1):
    rng = (hi - lo) or 1
    return [y1 - (v - lo) / rng * (y1 - y0) for v in vals]


def _text_w(s, size, mono=False):
    w = 0.0
    for ch in str(s):
        o = ord(ch)
        if o >= 0x2E80:
            w += size
        elif ch == " ":
            w += size * 0.28
        elif 0x2000 <= o < 0x2E80:
            w += size * 0.9
        else:
            w += size * (0.6 if mono else 0.56)
    return w


def _text(x, y, s, size=F6, anchor="start", fill=None, weight=400, family="Noto Sans SC", extra=""):
    fill = fill or C["ink"]
    pre = ""
    if extra == HALO:
        extra = ""
        tw = _text_w(s, size, "Mono" in family) * (1.05 if int(weight) >= 600 else 1.0)
        bx = x if anchor == "start" else (x - tw if anchor == "end" else x - tw / 2)
        pre = (f'<rect x="{bx - 0.35:.3f}" y="{y - size * 0.86:.3f}" width="{tw + 0.7:.3f}" height="{size * 1.1:.3f}" rx="0.45" '
               f'fill="{C["paper_light"]}" fill-opacity="0.9"/>')
    return pre + (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size:.3f}" text-anchor="{anchor}" fill="{fill}" '
            f'font-weight="{weight}" font-family="{family}" {extra}>{esc(s)}</text>')


def _hatch(x0, y0, x1, y1, step=1.1, color=None, width=LW_THIN, clip_id="h"):
    color = color or C["ink_3"]
    lines = []
    w, h = x1 - x0, y1 - y0
    k = -h
    while k < w:
        lines.append(f'<line x1="{x0 + k:.3f}" y1="{y1:.3f}" x2="{x0 + k + h:.3f}" y2="{y0:.3f}"/>')
        k += step
    return (f'<clipPath id="{clip_id}"><rect x="{x0:.3f}" y="{y0:.3f}" width="{w:.3f}" height="{h:.3f}"/></clipPath>'
            f'<g clip-path="url(#{clip_id})" stroke="{color}" stroke-width="{width:.3f}">{"".join(lines)}</g>')


def dir_color(v):
    if v is None or abs(v) < 1e-9:
        return C["ink_2"]
    return C["up"] if v > 0 else C["down"]


def arrow(v):
    if v is None or abs(v) < 1e-9:
        return "—"
    return "▲" if v > 0 else "▼"


_uid = [0]


def _id(p):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


def blind_chart(values, t_index=None, w=50.0, h=26.0, label="", curtain=0.2) -> str:
    """盲测走势：只画到决策日，右侧盖一块“幕布”。"""
    if t_index is None:
        t_index = len(values) - 1
    vals = values[: t_index + 1]
    pad_l, pad_r, pad_t, pad_b = 1.0, 1.0, 3.6, 3.4
    cw = (w - pad_l - pad_r) * (1 - curtain)
    x0, x1 = pad_l, pad_l + cw
    y0, y1 = pad_t, h - pad_b
    lo, hi = min(min(vals), 100), max(max(vals), 100)
    span = hi - lo or 1
    lo -= span * 0.08
    hi += span * 0.10
    n = len(vals)
    xs = [x0 + i / max(1, n - 1) * (x1 - x0) for i in range(n)]
    ys = _scale(vals, lo, hi, y0, y1)
    yb = _scale([100], lo, hi, y0, y1)[0]
    last = vals[-1]
    col = dir_color(last - 100)
    area = [(xs[0], y1)] + list(zip(xs, ys)) + [(xs[-1], y1)]
    cid = _id("bc")
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" overflow="visible">']
    out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0:.3f}" height="{y1 - y0:.3f}" fill="{C["paper_light"]}"/>')
    out.append(f'<polygon points="{_poly(area)}" fill="{C["paper_deep"]}" opacity="0.9"/>')
    out.append(f'<line x1="{x0}" y1="{yb:.3f}" x2="{x1:.3f}" y2="{yb:.3f}" stroke="{C["ink_3"]}" stroke-width="{LW_THIN:.3f}" stroke-dasharray="0.8 0.6"/>')
    k = max(3, n // 6)
    head_above = sum(ys[:k]) / k < yb  # 开头一段在基准线上方 → 标签放到线下
    out.append(_text(x0 + 0.4, yb + 2.5 if head_above else yb - 0.7, "起点 100", F6, fill=C["ink_2"], extra=HALO))
    out.append(f'<polyline points="{_poly(zip(xs, ys))}" fill="none" stroke="{C["ink"]}" stroke-width="{LW * 1.15:.3f}" stroke-linejoin="round" stroke-linecap="round"/>')
    # 幕布
    cx0, cx1 = x1, w - pad_r
    out.append(f'<rect x="{cx0:.3f}" y="{y0 - 1.6:.3f}" width="{cx1 - cx0:.3f}" height="{y1 - y0 + 1.6:.3f}" fill="{C["ink"]}"/>')
    out.append(_hatch(cx0, y0 - 1.6, cx1, y1, step=1.0, color=C["ink_2"], clip_id=cid))
    out.append(_text((cx0 + cx1) / 2, (y0 + y1) / 2 + 2.2, "?", 6.2, "middle", C["sun"], 400, "Smiley Sans Oblique"))
    out.append(f'<line x1="{x1:.3f}" y1="{y0 - 1.6:.3f}" x2="{x1:.3f}" y2="{y1:.3f}" stroke="{C["mustard"]}" stroke-width="{LW:.3f}"/>')
    out.append(f'<circle cx="{xs[-1]:.3f}" cy="{ys[-1]:.3f}" r="0.85" fill="{col}" stroke="{C["paper_light"]}" stroke-width="0.25"/>')
    tx = xs[-1] - 1.4
    ty = max(y0 + 2.2, min(ys[-1] - 1.2, y1 - 0.5))
    out.append(_text(tx, ty, f"{arrow(last - 100)} {_fmt(last)}", F65, "end", col, 700, extra=HALO))
    out.append(_text(x1, y0 - 2.0, "今天", F6, "middle", C["ink"], 700))
    out.append(f'<line x1="{x0}" y1="{y1:.3f}" x2="{w - pad_r:.3f}" y2="{y1:.3f}" stroke="{C["ink"]}" stroke-width="{LW_THIN:.3f}"/>')
    if label:
        out.append(_text(x0, h - 0.5, label, F6, "start", C["ink_2"]))
    out.append("</svg>")
    return "".join(out)


def evidence_chart(chart: dict, w: float, h: float, kind: str = "price", tone="ink") -> str:
    """证据牌小图。kind: price（纸带）/ data（账本）。"""
    if not chart or not chart.get("values"):
        return ""
    t = chart.get("type", "line")
    vals = [v for v in chart["values"] if v is not None]
    labels = chart.get("labels") or []
    unit = chart.get("unit", "")
    ink = C["ink"]
    pad_l, pad_r, pad_t, pad_b = 0.4, 0.4, 2.2, 3.0
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" overflow="visible">']
    x0, x1, y0, y1 = pad_l, w - pad_r, pad_t, h - pad_b
    mono = "TS Mono" if kind == "price" else "Noto Sans SC"
    if kind == "data":
        # 账本横线
        for i in range(5):
            yy = y0 + i * (y1 - y0) / 4
            out.append(f'<line x1="{x0}" y1="{yy:.3f}" x2="{x1}" y2="{yy:.3f}" stroke="{C["sky_light"]}" stroke-width="{LW_THIN:.3f}"/>')
    if t == "bars":
        lo, hi = min(min(vals), 0), max(max(vals), 0)
        if hi == lo:
            hi = lo + 1
        rng = hi - lo
        hi += rng * 0.06
        n = len(vals)
        bw = (x1 - x0) / n
        gap = min(0.5, bw * 0.28)
        yz = _scale([0], lo, hi, y0, y1)[0]
        signed = lo < 0
        for i, v in enumerate(vals):
            yv = _scale([v], lo, hi, y0, y1)[0]
            if signed:
                col = dir_color(v)
            else:
                col = C["mustard"] if i == n - 1 else (C["sky_deep"] if kind == "price" else C["ochre"])
            yt, hh = (yv, yz - yv) if v >= 0 else (yz, yv - yz)
            out.append(f'<rect x="{x0 + i * bw + gap / 2:.3f}" y="{yt:.3f}" width="{max(0.2, bw - gap):.3f}" height="{max(0.15, hh):.3f}" fill="{col}"/>')
        out.append(f'<line x1="{x0}" y1="{yz:.3f}" x2="{x1}" y2="{yz:.3f}" stroke="{ink}" stroke-width="{LW_THIN:.3f}"/>')
        # 最高/最低标注
        imax = max(range(n), key=lambda i: vals[i])
        imin = min(range(n), key=lambda i: vals[i])
        sx = lambda i: x0 + (i + 0.5) * bw
        ymax = _scale([vals[imax]], lo, hi, y0, y1)[0]
        out.append(_text(min(max(sx(imax), x0 + 3), x1 - 3), ymax - 0.6, _fmt(vals[imax]), F6, "middle", ink, 700, mono))
        if signed and vals[imin] < 0:
            ymin = _scale([vals[imin]], lo, hi, y0, y1)[0]
            out.append(_text(min(max(sx(imin), x0 + 3), x1 - 3), ymin + 2.3, _fmt(vals[imin]), F6, "middle", ink, 700, mono))
    elif t == "grid":
        v = vals[0]
        n = 20
        cw = (x1 - x0) / n
        for i in range(n):
            filled = (i + 1) / n * 100 <= v + 1e-6
            out.append(f'<rect x="{x0 + i * cw + 0.15:.3f}" y="{y0 + 1:.3f}" width="{cw - 0.3:.3f}" height="{y1 - y0 - 2:.3f}" '
                       f'fill="{C["mustard"] if filled else C["paper_light"]}" stroke="{ink}" stroke-width="{LW_THIN:.3f}"/>')
        out.append(_text(x1, y0 - 0.4, f"{_fmt(v)}%", F7, "end", ink, 700, mono))
    else:
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or abs(hi) or 1
        lo -= span * 0.06
        hi += span * 0.12
        n = len(vals)
        xs = [x0 + i / max(1, n - 1) * (x1 - x0) for i in range(n)]
        ys = _scale(vals, lo, hi, y0, y1)
        if kind == "price":
            area = [(xs[0], y1)] + list(zip(xs, ys)) + [(xs[-1], y1)]
            out.append(f'<polygon points="{_poly(area)}" fill="{C["sky_light"]}" opacity="0.55"/>')
        out.append(f'<polyline points="{_poly(zip(xs, ys))}" fill="none" stroke="{ink}" stroke-width="{LW * 1.1:.3f}" stroke-linejoin="round"/>')
        col = dir_color(vals[-1] - vals[0])
        out.append(f'<circle cx="{xs[-1]:.3f}" cy="{ys[-1]:.3f}" r="0.75" fill="{col}"/>')
        out.append(_text(xs[-1] - 1.2, max(y0 + 0.4, ys[-1] - 0.9), _fmt(vals[-1]), F6, "end", ink, 700, mono, extra=HALO))
        out.append(_text(xs[0] + 0.2, min(y1 - 0.6, ys[0] - 0.9) if ys[0] > y0 + 3 else ys[0] + 2.6, _fmt(vals[0]), F6, "start", C["ink_2"], 400, mono, extra=HALO))
        out.append(f'<line x1="{x0}" y1="{y1:.3f}" x2="{x1}" y2="{y1:.3f}" stroke="{ink}" stroke-width="{LW_THIN:.3f}"/>')
    # 横轴标签：首尾
    if labels:
        first, last = labels[0], labels[-1]
        if first:
            out.append(_text(x0, h - 0.4, first, F6, "start", C["ink_2"]))
        if last and len(labels) > 1:
            out.append(_text(x1, h - 0.4, last, F6, "end", C["ink_2"]))
    out.append("</svg>")
    return "".join(out)


def reveal_chart(chart: dict, w: float, h: float, t_index=None) -> str:
    vals = chart.get("values") or []
    dates = chart.get("dates") or []
    marks = chart.get("marks") or []
    if not vals:
        return ""
    if t_index is None:
        t_index = chart.get("t_index")
    if t_index is None:
        t_index = len(vals) // 2
    n = len(vals)
    pad_l, pad_r, pad_t, pad_b = 0.6, 0.6, 8.0, 3.2
    x0, x1, y0, y1 = pad_l, w - pad_r, pad_t, h - pad_b
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    lo -= span * 0.06
    hi += span * 0.08
    xs = [x0 + i / max(1, n - 1) * (x1 - x0) for i in range(n)]
    ys = _scale(vals, lo, hi, y0, y1)
    tx = xs[t_index]
    vt = vals[t_index]
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" overflow="visible">']
    out.append(f'<rect x="{x0}" y="{y0 - 1.0:.3f}" width="{tx - x0:.3f}" height="{y1 - y0 + 1.0:.3f}" fill="{C["paper_light"]}"/>')
    out.append(f'<rect x="{tx:.3f}" y="{y0 - 1.0:.3f}" width="{x1 - tx:.3f}" height="{y1 - y0 + 1.0:.3f}" fill="{C["paper_deep"]}"/>')
    # 决策日之前 / 之后
    pre = list(zip(xs[: t_index + 1], ys[: t_index + 1]))
    post = list(zip(xs[t_index:], ys[t_index:]))
    out.append(f'<polyline points="{_poly(pre)}" fill="none" stroke="{C["ink_3"]}" stroke-width="{LW:.3f}" stroke-linejoin="round"/>')
    out.append(f'<polyline points="{_poly(post)}" fill="none" stroke="{C["ink"]}" stroke-width="{LW * 1.25:.3f}" stroke-linejoin="round"/>')
    out.append(f'<line x1="{tx:.3f}" y1="{y0 - 1.0:.3f}" x2="{tx:.3f}" y2="{y1:.3f}" stroke="{C["ink"]}" stroke-width="{LW_THIN:.3f}" stroke-dasharray="0.7 0.5"/>')
    out.append(f'<line x1="{x0}" y1="{y1:.3f}" x2="{x1}" y2="{y1:.3f}" stroke="{C["ink"]}" stroke-width="{LW_THIN:.3f}"/>')
    # 标注统一放在图上方的标签带里（两行错开），用细引线连到点上，保证不压线、不互相遮挡
    def tw_of(s):
        return sum(F6 * (0.56 if ord(ch) < 128 else 1.0) for ch in s) + 2.0
    ms = []
    for m in marks:
        i = m.get("i")
        if i is None or i >= n:
            continue
        ms.append((xs[i], ys[i], i, str(m.get("label", ""))))
    ms.sort()
    rows_end = [-1e9, -1e9]
    row_y = [0.3, 3.9]
    for x, y, i, lab in ms:
        is_t = "决策" in lab
        if not is_t and i > t_index and abs(vals[i] - vt) > 1e-9:
            lab = arrow(vals[i] - vt) + " " + lab
        tw = tw_of(lab)
        bx = min(max(x - tw / 2, x0), x1 - tw)
        r = 0 if bx > rows_end[0] + 0.8 else (1 if bx > rows_end[1] + 0.8 else (0 if rows_end[0] <= rows_end[1] else 1))
        if r == 0 and bx <= rows_end[0] + 0.8:
            bx = rows_end[0] + 0.8
        if r == 1 and bx <= rows_end[1] + 0.8:
            bx = rows_end[1] + 0.8
        bx = min(bx, x1 - tw)
        rows_end[r] = bx + tw
        by = row_y[r]
        col = C["ink"] if is_t else (dir_color(vals[i] - vt) if i > t_index else C["ink_2"])
        # 引线
        out.append(f'<line x1="{x:.3f}" y1="{by + 3.2:.3f}" x2="{x:.3f}" y2="{y - 0.9:.3f}" stroke="{C["ink_3"]}" stroke-width="{LW_THIN:.3f}" stroke-dasharray="0.5 0.4"/>')
        if is_t:
            out.append(f'<rect x="{bx:.3f}" y="{by:.3f}" width="{tw:.3f}" height="3.2" rx="0.6" fill="{C["ink"]}"/>')
            out.append(_text(bx + tw / 2, by + 2.3, lab, F6, "middle", C["paper"], 700))
            out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="0.9" fill="{C["mustard"]}" stroke="{C["ink"]}" stroke-width="0.25"/>')
        else:
            out.append(f'<rect x="{bx:.3f}" y="{by:.3f}" width="{tw:.3f}" height="3.2" rx="0.6" fill="{C["paper_light"]}" stroke="{col}" stroke-width="{LW_THIN:.3f}"/>')
            out.append(_text(bx + tw / 2, by + 2.3, lab, F6, "middle", col, 700))
            out.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="0.75" fill="{col}" stroke="{C["paper_light"]}" stroke-width="0.2"/>')
    # 日期轴
    if dates:
        d0, d1 = dates[0], dates[-1]
        out.append(_text(x0, h - 0.3, d0[:7].replace("-", "."), F6, "start", C["ink_2"]))
        out.append(_text(x1, h - 0.3, d1[:7].replace("-", "."), F6, "end", C["ink_2"]))
        if t_index < len(dates):
            dt = dates[t_index]
            # 决策日日期，避开首尾
            if x0 + 9 < tx < x1 - 9:
                out.append(_text(tx, h - 0.3, dt[5:].replace("-", "."), F6, "middle", C["ink"], 700))
    out.append(_text(x0 + 0.6, y0 + 1.6, _fmt(max(vals)), F6, "start", C["ink_2"], 400, "TS Mono") if ys.index(min(ys)) > n * 0.25 else "")
    out.append("</svg>")
    return "".join(out)


def day_strip(days: list[dict], w: float, h: float, key="pct") -> str:
    """快进牌上的逐日小格：每格一天，红涨绿跌 + ▲▼ + 数字。"""
    n = len(days)
    if not n:
        return ""
    gap = 0.8
    cw = (w - gap * (n - 1)) / n
    out = [f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">']
    for i, d in enumerate(days):
        v = d.get(key)
        if v is None:
            v = d.get("close_pct", d.get("pct", 0))
        x = i * (cw + gap)
        col = dir_color(v)
        out.append(f'<rect x="{x:.3f}" y="0" width="{cw:.3f}" height="{h - 3.0:.3f}" rx="0.6" fill="{col}"/>')
        out.append(_text(x + cw / 2, (h - 3.0) / 2 + 1.0, f"{arrow(v)}{_fmt(abs(v))}%", F65 if cw > 8 else F6, "middle", C["paper_light"], 700))
        lab = d.get("label") or (d.get("date", "")[5:].replace("-", "/") if d.get("date") else f"第{i + 1}天")
        out.append(_text(x + cw / 2, h - 0.3, lab, F6, "middle", C["ink_2"]))
    out.append("</svg>")
    return "".join(out)
