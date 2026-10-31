"""规则书（A5，16 页骑马钉）与快速入门卡（A4）。文字全部来自 content/rules-v1.md、quickstart.md。"""

from __future__ import annotations

import re
from pathlib import Path

from . import art, content, icons, qrsvg
from .c_board import CELLS
from .core import Card, esc, trim
from .model import Model
from .paths import ROOT
from .tokens import C, SEASON, SPECIES_COLOR, SPECIES_ORDER

PW, PH = 148.0, 210.0
DISC = "投资者教育游戏，不构成投资建议"

# 规则书和实际印出来的配件对齐的几处措辞（内容文件不改，排版时替换并记进说明）
WORDING = [
    ("再翻牌背看你那个答案对应的物种图标", "再看牌底倒印的、你那个答案对应的物种图标"),
    ("写在委托单背面", "写在委托单下半张的复盘面"),
    ("在委托单背面记方法星", "在委托单复盘面记方法星"),
    ("委托单背面有图标栏", "委托单复盘面有图标栏"),
    ("在委托单背面勾“留下”或“离开”", "在委托单复盘面勾“留下”或“离开”"),
]


# ---------------------------------------------------------------- markdown（够用的子集）

def _warn_inline():
    svg = (f'<svg width="100%" height="100%" viewBox="0 0 4 4">'
           f'<polygon points="2,0.35 3.75,3.55 0.25,3.55" fill="{C["mustard"]}" stroke="{C["ink"]}" stroke-width="0.26" stroke-linejoin="round"/>'
           f'<rect x="1.76" y="1.3" width="0.48" height="1.25" rx="0.2" fill="{C["ink"]}"/>'
           f'<circle cx="2" cy="2.98" r="0.27" fill="{C["ink"]}"/></svg>')
    return f'<span style="display:inline-block;vertical-align:-0.2em;width:1.25em;height:1.25em;margin:0 0.08em">{svg}</span>'


def inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = t.replace("⚠", _warn_inline())
    return t


def md(text: str, cls_quote=None) -> str:
    out = []
    lines = text.strip("\n").split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</table>")
            continue
        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            q = " ".join(buf)
            if q.startswith("**例**"):
                q = q[len("**例**"):].lstrip("：: ")
                out.append(f'<div class="ex">{inline(q)}</div>')
            else:
                out.append(f'<div class="{cls_quote or "note"}">{inline(q)}</div>')
            continue
        if re.match(r"^\d+\.\s", ln):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if ln.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        buf = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s|- |>|\||#)", lines[i]):
            buf.append(lines[i].rstrip())
            i += 1
        out.append(f"<p>{inline(''.join(buf))}</p>")
    return "".join(out)


def rules_sections() -> dict:
    txt = content.load_text("rules-v1.md")
    for a, b in WORDING:
        if a in txt:
            txt = txt.replace(a, b)
    secs = {}
    for part in re.split(r"\n(?=## )", txt):
        if part.startswith("## "):
            head, _, body = part.partition("\n")
            secs[head[3:].strip()] = body.strip()
    return secs


def _wording_note():
    txt = content.load_text("rules-v1.md")
    if not any(a in txt for a, _ in WORDING):
        return
    content.NOTES.append("规则书排版时把“翻牌背看图标”改成“看牌底倒印的图标”、“委托单背面”改成“委托单复盘面”，和印出来的机会牌、单面委托单对齐（rules-v1.md 原文没动，建议同步）")


# ---------------------------------------------------------------- 示意图

def board_diagram(w=118.0) -> str:
    from . import c_board as B
    s = w / B.W
    h = B.H * s
    el = [f'<svg width="{w}mm" height="{h:.2f}mm" viewBox="0 0 {B.W} {B.H}" style="display:block">',
          f'<rect x="4" y="4" width="{B.W - 8}" height="{B.H - 8}" rx="14" fill="{C["paper_deep"]}" stroke="{C["ink"]}" stroke-width="2"/>']

    def rect(x, y, ww, hh, fill, stroke=C["ink"], sw=1.6, rx=6):
        el.append(f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{ww - 4:.1f}" height="{hh - 4:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def txt(x, y, t, size=20, fill=C["ink"], font="Smiley Sans Oblique", anchor="middle", weight=400):
        el.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-family="{font}" font-weight="{weight}">{esc(t)}</text>')

    corners = [(B.MG, B.MG, "总起点"), (B.W - B.MG - B.D, B.MG, "驿站"), (B.W - B.MG - B.D, B.H - B.MG - B.D, "驿站"), (B.MG, B.H - B.MG - B.D, "驿站")]
    for x, y, t in corners:
        rect(x, y, B.D, B.D, C["ochre"])
        txt(x + B.D / 2, y + B.D / 2 + 9, t, 26, C["paper_light"])
    nums = "①②③④⑤"
    seq = []
    for i in range(5):
        seq.append(("spring", B.MG + B.D + i * B.CH, B.MG, B.CH, B.D, i))
        seq.append(("summer", B.W - B.MG - B.D, B.MG + B.D + i * B.CV, B.D, B.CV, i))
        seq.append(("autumn", B.W - B.MG - B.D - (i + 1) * B.CH, B.H - B.MG - B.D, B.CH, B.D, i))
        seq.append(("winter", B.MG, B.H - B.MG - B.D - (i + 1) * B.CV, B.D, B.CV, i))
    for season, x, y, ww, hh, i in seq:
        rect(x, y, ww, hh, C["paper_light"])
        el.append(f'<circle cx="{x + ww / 2:.1f}" cy="{y + hh / 2:.1f}" r="{min(ww, hh) * 0.3:.1f}" fill="{SEASON[season]["color"]}"/>')
        txt(x + ww / 2, y + hh / 2 + 8, str(i + 1), 24, C["paper_light"])
    doors = [("spring", B.MG + B.D + 5 * B.CH, B.MG, B.DOOR_H, B.D), ("summer", B.W - B.MG - B.D, B.MG + B.D + 5 * B.CV, B.D, B.DOOR_V),
             ("autumn", B.MG + B.D, B.H - B.MG - B.D, B.DOOR_H, B.D), ("winter", B.MG, B.MG + B.D, B.D, B.DOOR_V)]
    for season, x, y, ww, hh in doors:
        rect(x, y, ww, hh, C["paper"], sw=1.6)
        cn = SEASON[season]["cn"]
        if ww > hh:
            for k, dx in enumerate((0.3, 0.7)):
                ax = x + ww * dx
                el.append(f'<path d="M{ax - 10:.1f} {y + hh - 7:.1f} V{y + 31:.1f} A10 10 0 0 1 {ax + 10:.1f} {y + 31:.1f} V{y + hh - 7:.1f} Z" fill="{SEASON[season]["color"] if k == 0 else C["paper_deep"]}" stroke="{C["ink"]}" stroke-width="1.4"/>')
                txt(ax + 18, y + hh - 9, "AB"[k], 20, C["ink"], anchor="start")
            txt(x + ww / 2, y + 17, f"{cn}季名场面门", 16)
        else:
            for k, dy in enumerate((0.36, 0.76)):
                ay = y + hh * dy
                el.append(f'<path d="M{x + 12:.1f} {ay + 12:.1f} V{ay - 6:.1f} A10 10 0 0 1 {x + 32:.1f} {ay - 6:.1f} V{ay + 12:.1f} Z" fill="{SEASON[season]["color"] if k == 0 else C["paper_deep"]}" stroke="{C["ink"]}" stroke-width="1.4"/>')
                txt(x + 40, ay + 8, "AB"[k], 18, C["ink"], anchor="start")
            txt(x + ww / 2, y + 16, f"{cn}季门", 15)
    # 方向箭头 + 季节字
    cx, cy = B.W / 2, B.H / 2
    labels = [("spring", cx, B.MG + B.D + 30), ("summer", B.W - B.MG - B.D - 30, cy), ("autumn", cx, B.H - B.MG - B.D - 22), ("winter", B.MG + B.D + 30, cy)]
    for season, x, y in labels:
        el.append(f'<circle cx="{x:.1f}" cy="{y - 8:.1f}" r="17" fill="{SEASON[season]["color"]}"/>')
        txt(x, y + 1, SEASON[season]["cn"], 24, C["paper_light"])
    el.append(f'<path d="M{cx - 70} {cy - 40} A90 60 0 0 1 {cx + 80} {cy - 30}" fill="none" stroke="{C["ink"]}" stroke-width="3" stroke-dasharray="8 6"/>'
              f'<path d="M{cx + 72} {cy - 44} L{cx + 86} {cy - 28} L{cx + 66} {cy - 24} Z" fill="{C["ink"]}"/>')
    txt(cx, cy + 10, "顺时针走", 26)
    txt(cx, cy + 42, "中间放牌堆和名场面区", 18, C["ink_2"], font="Noto Sans SC")
    el.append("</svg>")
    return "".join(el)


def _icon_disc(name, d, ring=None, kind="icon"):
    a = art.icon(name) if kind == "icon" else art.tile_art(name)
    if not a:
        return f'<span style="display:inline-block;width:{d}mm;height:{d}mm;border-radius:50%;background:{C["paper_deep"]}"></span>'
    rg = f"box-shadow:0 0 0 0.5mm {ring};" if ring else ""
    return (f'<span style="display:inline-block;flex:none;width:{d}mm;height:{d}mm;border-radius:50%;overflow:hidden;{rg}">'
            f'<img src="{a["uri"]}" style="width:100%;height:100%;display:block"></span>')


def season_steps() -> str:
    steps = [("coin", "icon", "领预算", "1 研究点 + 本季委托单"), ("dice", "icon", "赶路", "两骰挑一个点数"),
             ("door", None, "名场面", "全员到齐一起进门"), ("station", "tile", "驿站", "拿一枚物种币")]
    cells = []
    for i, (nm, kind, t, sub) in enumerate(steps):
        if kind is None:
            img = (f'<span style="display:inline-flex;width:13mm;height:13mm;border-radius:50%;background:{C["paper_deep"]};align-items:center;justify-content:center">'
                   f'<svg width="7mm" height="9mm" viewBox="0 0 7 9"><path d="M0.3 8.7 V3.5 A3.2 3.2 0 0 1 6.7 3.5 V8.7 Z" fill="{SEASON["autumn"]["color"]}" stroke="{C["ink"]}" stroke-width="0.3"/></svg></span>')
        else:
            img = _icon_disc(nm, 13, C["ink"], kind)
        cells.append(f'<div class="col" style="align-items:center;gap:0.25em;flex:1;min-width:0">{img}'
                     f'<div class="row" style="gap:0.3em"><span class="kb" style="width:1.35em;height:1.35em;font-size:1em">{i + 1}</span><b style="font-size:1.08em">{t}</b></div>'
                     f'<div style="font-size:0.92em;color:{C["ink_2"]};text-align:center;line-height:1.3">{sub}</div></div>')
        if i < 3:
            cells.append(f'<div style="padding-top:5mm">{icons.arrow_right(5, 3)}</div>')
    return f'<div class="diag row" style="align-items:flex-start;gap:1mm">{"".join(cells)}</div>'


def scene_ribbon() -> str:
    steps = [("chart", "盲入场"), ("magnifier", "开证据"), ("ledger", "填委托单"), (None, "三二一亮单"), ("hourglass", "快进"), ("kite", "揭幕")]
    cells = []
    for i, (nm, t) in enumerate(steps):
        if nm:
            img = _icon_disc(nm, 14, C["ink"])
        else:
            img = (f'<span style="display:inline-flex;width:14mm;height:14mm;border-radius:50%;background:{C["ink"]};align-items:center;justify-content:center;'
                   f'color:{C["sun"]}" class="disp"><span style="font-size:13pt">3·2·1</span></span>')
        cells.append(f'<div class="col" style="align-items:center;gap:0.3em;width:17.4mm">{img}'
                     f'<div class="row" style="gap:0.25em;white-space:nowrap"><span class="kb" style="width:1.3em;height:1.3em;font-size:0.95em">{i + 1}</span>'
                     f'<b style="font-size:0.98em">{t}</b></div></div>')
    return f'<div class="diag row" style="justify-content:space-between;align-items:flex-start">{"".join(cells)}</div>'


def cells_table(secs) -> str:
    body = secs.get("五种小格子", "")
    rows = {}
    for ln in body.splitlines():
        mm = re.match(r"^\|\s*([①②③④⑤])\s*(\S+)\s*\|\s*(.+?)\s*\|$", ln)
        if mm:
            rows[mm.group(1)] = (mm.group(2), mm.group(3))
    out = []
    for i, (kind, name, _) in enumerate(CELLS):
        n = "①②③④⑤"[i]
        nm, how = rows.get(n, (name, ""))
        out.append(f'<div class="row" style="gap:0.8em;align-items:flex-start;padding:0.45em 0;border-bottom:0.5pt solid {C["ink_3"]}">'
                   f'{_icon_disc(kind, 11.5, None, "tile")}<div style="flex:1"><b style="font-size:1.08em">{n} {esc(nm)}</b><br>{inline(how)}</div></div>')
    rest = "\n".join(l for l in body.splitlines() if not l.startswith("|")).strip()
    return "".join(out) + (md(rest) if rest else "")


def coin_faces_inline() -> str:
    col = SPECIES_COLOR["fox"]
    solid = (f'<svg width="11mm" height="11mm" viewBox="0 0 15 15" style="flex:none"><circle cx="7.5" cy="7.5" r="7.3" fill="{col}"/>'
             f'<text x="7.5" y="10.4" font-size="8.4" text-anchor="middle" fill="{C["paper_light"]}" font-family="Smiley Sans Oblique">狐</text></svg>')
    hollow = (f'<svg width="11mm" height="11mm" viewBox="0 0 15 15" style="flex:none"><circle cx="7.5" cy="7.5" r="7.3" fill="{C["paper_light"]}"/>'
              f'<circle cx="7.5" cy="7.5" r="6.6" fill="none" stroke="{col}" stroke-width="1.2"/>'
              f'<text x="7.5" y="10.4" font-size="8.4" text-anchor="middle" fill="{col}" font-family="Smiley Sans Oblique">狐</text></svg>')
    return (f'<div class="diag row" style="gap:1.2em;background:{C["paper_light"]};border-radius:2mm;padding:0.6em 0.9em">'
            f'<div class="row" style="gap:0.6em">{solid}<div><b>实心面 = 1 枚</b><br>平常放这一面</div></div>'
            f'<div class="row" style="gap:0.6em">{hollow}<div><b>空心面 = 半枚</b><br>这季申报了“认出来了”</div></div></div>')


def mini(card: Card, scale: float, shadow=True) -> str:
    """把一张做好的牌缩小嵌进页面（只露成品框）。"""
    w, h = card.w * scale, card.h * scale
    sh = "box-shadow:0 0.6mm 1.8mm rgba(0,0,0,.28);" if shadow else ""
    return (f'<div class="nocheck" style="position:relative;width:{w:.2f}mm;height:{h:.2f}mm;flex:none;overflow:hidden;border-radius:1mm;{sh}">'
            f'<div style="position:absolute;left:{-3 * scale:.3f}mm;top:{-3 * scale:.3f}mm;width:{card.bw}mm;height:{card.bh}mm;transform:scale({scale});transform-origin:0 0">'
            f'{card.root()}</div></div>')


def components_grid(m: Model) -> str:
    items = [("tile", "start", "主棋盘", "A2 或 4 张 A4"), ("icon", "chart", "名场面牌", "每场一组"), ("tile", "chance", "通用牌", "6 种牌堆"),
             ("medal", "owl", "物种牌", "7 张"), ("icon", "letter", "速查 · 序章", "A6 卡"),
             ("icon", "coin", "物种币", "56 枚"), ("icon", "egg", "研究点", "40 个"), ("icon", "dice", "骰子 · 沙漏", "2 颗 · 30 秒"),
             ("icon", "ledger", "委托单", "四季四本"), ("icon", "compass", "玩家板", "每人一块")]
    cells = []
    for kind, nm, t, sub in items:
        a = art.icon(nm) if kind == "icon" else (art.tile_art(nm) if kind == "tile" else art.medal(nm))
        img = (f'<span style="display:block;width:13mm;height:13mm;border-radius:50%;overflow:hidden;box-shadow:0 0 0 0.45mm {C["ink"]}">'
               f'<img src="{a["uri"]}" style="width:100%;height:100%"></span>') if a else ""
        cells.append(f'<div class="col" style="align-items:center;gap:0.2em;text-align:center">{img}<b style="font-size:0.98em;margin-top:0.3em">{t}</b>'
                     f'<span style="font-size:0.92em;color:{C["ink_2"]};line-height:1.2">{sub}</span></div>')
    return (f'<div class="diag" style="display:grid;grid-template-columns:repeat(5,1fr);row-gap:0.9em;column-gap:0.4em;background:{C["paper_light"]};'
            f'border-radius:2mm;padding:0.9em 0.6em">{"".join(cells)}</div>')


def scene_area_diagram() -> str:
    W, H = 120.0, 56.0
    el = [f'<svg width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" style="display:block;margin:0 auto">']

    def card(x, y, w, h, label, sub, fill, fg=C["ink"]):
        el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.2" fill="{fill}" stroke="{C["ink"]}" stroke-width="0.35"/>')
        el.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 0.4}" font-size="3.1" text-anchor="middle" fill="{fg}" font-family="Smiley Sans Oblique">{label}</text>')
        if sub:
            el.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 3.6}" font-size="2.47" text-anchor="middle" fill="{fg}" font-family="Noto Sans SC">{sub}</text>')

    sw, sh = 15.8, 22.0
    ax, aw, ah = 47.0, 26.0, 36.0
    card(ax, 4, aw, ah, "场景牌", "盲测面朝上", C["paper_light"])
    for i, (t, col) in enumerate((("量价", C["sky"]), ("数据", C["sky"]))):
        card(ax - 4 - sw - (sw + 3) * (1 - i), 4 + 7, sw, sh, t, "扣着放", col, C["paper_light"])
    for i, (t, col) in enumerate((("消息", C["sky"]), ("锦囊", C["ink_3"]))):
        card(ax + aw + 4 + (sw + 3) * i, 4 + 7, sw, sh, t, "扣着放", col, C["paper_light"])
    card(ax, 43, 12, 10, "快进", "", C["ink_2"], C["paper_light"])
    card(ax + 14, 43, 12, 10, "揭幕", "", C["ink_2"], C["paper_light"])
    el.append(f'<path d="M{ax + 12.3} 48 h1.4" stroke="{C["ink"]}" stroke-width="0.4"/>')
    el.append(f'<text x="{ax - 3}" y="49.6" font-size="2.47" text-anchor="end" fill="{C["ink_2"]}" font-family="Noto Sans SC">按顺序翻</text>')
    rx = ax + aw + 6
    el.append(f'<circle cx="{rx + 4}" cy="48" r="4" fill="{C["mustard"]}" stroke="{C["ink"]}" stroke-width="0.35"/>'
              f'<text x="{rx + 4}" y="49.2" font-size="3.2" text-anchor="middle" fill="{C["ink"]}" font-family="Smiley Sans Oblique">1</text>'
              f'<text x="{rx + 10}" y="46.8" font-size="2.47" fill="{C["ink"]}" font-family="Noto Sans SC">研究点 = 看 1 张证据</text>'
              f'<text x="{rx + 10}" y="50.6" font-size="2.47" fill="{C["ink_2"]}" font-family="Noto Sans SC">自己看，看完扣回</text>')
    el.append("</svg>")
    return f'<div class="diag" style="background:{C["paper_light"]};border-radius:2mm;padding:0.5em 0">{"".join(el)}</div>'


def slip_figure(m: Model) -> str:
    from . import c_misc
    slip = c_misc.order_slip(m, "spring", c_misc.SLIP_TINT["spring"])
    sc = 0.5
    fig = mini(slip, sc)
    h = slip.h * sc
    notes = [(3, "上半张 · 亮单前填", "落在哪格、认出来了、看了哪几张、选项、理由、计划"),
             (h / 2 - 2.6, "对折线", "字朝里对折，扣在玩家板上，三二一一起翻"),
             (h / 2 + 10, "下半张 · 复盘面", "快进动作、两段结算、方法星、图标和本季物种币")]
    ns = "".join(f'<div style="position:absolute;left:0;top:{y:.1f}mm;right:0"><div class="row" style="gap:0.4em"><span style="display:inline-block;width:5mm;border-top:0.6pt solid {C["ink"]}"></span>'
                 f'<b>{t}</b></div><div style="padding-left:calc(5mm + 0.4em);color:{C["ink_2"]};font-size:0.94em;line-height:1.35">{d}</div></div>' for y, t, d in notes)
    return (f'<div class="diag row" style="gap:3mm;align-items:flex-start">{fig}<div style="position:relative;flex:1;height:{h:.1f}mm">{ns}'
            f'<div style="position:absolute;left:0;bottom:0;font-size:0.92em;color:{C["ink_3"]}">图：春季委托单（季节色纸），缩小 50%</div></div></div>')


def ai_board_figure(m: Model) -> str:
    from . import c_misc
    b = c_misc.ai_board(m)
    sc = 0.4
    return (f'<div class="diag center">{mini(b, sc).replace("position:relative;", "position:relative;display:inline-block;")}'
            f'<div style="font-size:0.92em;color:{C["ink_3"]};margin-top:0.4em">图：AI 板，两张 AI 物种牌背面朝下放在左边，缩小 40%</div></div>')


def split_at(body: str, marker: str) -> tuple[str, str]:
    k = body.find(marker)
    if k < 0:
        return body, ""
    return body[:k].rstrip(), body[k:]


# ---------------------------------------------------------------- 页

def _page(n, inner, head="", bg=None, full=False) -> Card:
    left = n % 2 == 0
    ml, mr = (12.0, 15.0) if left else (15.0, 12.0)
    parts = []
    if bg:
        parts.append(f'<div class="a" style="left:-3mm;top:-3mm;width:{PW + 6}mm;height:{PH + 6}mm;background:{bg}"></div>')
    if full:
        parts.append(inner)
    else:
        if head:
            al = "left" if left else "right"
            parts.append(f'<div class="a caps" style="left:{ml}mm;right:{mr}mm;top:7.4mm;text-align:{al};font-size:7pt;letter-spacing:.2em;color:{C["ink_3"]}">'
                         f'交易物种起源 · 规则书 · {esc(head)}</div>')
            parts.append(f'<div class="a" style="left:{ml}mm;right:{mr}mm;top:11.2mm;border-top:0.5pt solid {C["ink_3"]}"></div>')
        parts.append(f'<div class="a fit bk" data-min="7.6" data-what="规则书第 {n} 页" style="left:{ml}mm;right:{mr}mm;top:14.6mm;height:178.4mm">{inner}</div>')
        nx = f"left:{ml}mm" if left else f"right:{mr}mm"
        parts.append(f'<div class="a row" style="{nx};top:198.2mm;gap:2mm;{"" if left else "flex-direction:row-reverse;"}">'
                     f'<span class="row num" style="width:6.4mm;height:6.4mm;border-radius:50%;background:{C["ink"]};color:{C["sun"]};justify-content:center;font-size:10pt">{n}</span>'
                     f'<span style="font-size:7pt;color:{C["ink_3"]}">{DISC}</span></div>')
    return Card(key=f"book-p{n:02d}", w=PW, h=PH, html=trim("".join(parts), PW, PH), label=f"规则书 第 {n} 页")


def h2(t, no=None):
    nb = f'<span class="no">{no}</span>' if no else ""
    return f'<h2>{nb}<span>{esc(t)}</span></h2>'


def _kite_src():
    base = ROOT / "art" / "vmc-output" / "style-v7" / "v7_h5_opening"
    c = sorted(base.glob("**/*.png"))
    return c[0] if c else None


def hero():
    src = _kite_src()
    if not src:
        content.NOTES.append("盒面 / 封面主视觉（style-v7/v7_h5_opening 红风筝海报）缺失")
        return None
    return art.plain(src, "hero_kite_c", scale=2.0, crop=(0.025, 0.014, 0.975, 0.986))


def kite_emblem(left: float, top: float, d: float, ring: float = 1.2) -> str:
    """红风筝圆徽：主视觉右上角的大红风筝特写（裁掉了海报的米色边）。"""
    h = hero()
    if not h:
        return f'<div class="a" style="left:{left}mm;top:{top}mm;width:{d}mm;height:{d}mm;border-radius:50%;background:{C["sky"]}"></div>'
    k = d / 44.0
    iw = 200.0 * k
    return (f'<div class="a" style="left:{left}mm;top:{top}mm;width:{d}mm;height:{d}mm;border-radius:50%;overflow:hidden;box-shadow:0 0 0 {ring}mm {C["sun"]}">'
            f'<img src="{h["uri"]}" style="position:absolute;left:{-155.6 * k:.2f}mm;top:{-4.4 * k:.2f}mm;width:{iw:.2f}mm;height:{iw * h["h"] / h["w"]:.2f}mm"></div>')


def cover(m: Model, secs) -> Card:
    h = hero()
    cv = secs.get("封面语", "")
    tag = re.search(r"\*\*(.+?)\*\*", cv)
    tag = tag.group(1) if tag else ""
    meta = next((l.strip() for l in cv.splitlines() if "人" in l and "｜" in l), "")
    sub = next((l.strip() for l in cv.splitlines() if l.startswith("一款")), "")
    disc = next((l.lstrip("> ").strip() for l in cv.splitlines() if l.startswith(">")), DISC)
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{PW + 6}mm;height:{PH + 6}mm;background:{C["paper"]}"></div>']
    if h:
        p.append(f'<div class="a" style="left:-3mm;top:-3mm;width:{PW + 6}mm;height:146mm;overflow:hidden">'
                 f'<img src="{h["uri"]}" style="position:absolute;left:0;top:-6mm;width:{PW + 6}mm;height:{(PW + 6) * h["h"] / h["w"]:.2f}mm"></div>')
    p.append(f'<div class="a mstripe" style="left:-3mm;top:143mm;width:{PW + 6}mm;height:1.6mm"></div>')
    p.append(f'<div class="a" style="left:-3mm;top:144.6mm;width:{PW + 6}mm;height:{PH - 141.6:.1f}mm;overflow:hidden">{icons.sun_rays(PW + 6, PH - 141.6, (PW + 6) / 2, PH - 141.6 + 30, 30, C["sun"], 0.22)}</div>')
    p.append(f'<div class="a center" style="left:0;right:0;top:150mm"><span class="chip ink" style="font-size:8pt;height:5.4mm;letter-spacing:.2em">规则书 v1.0</span></div>')
    p.append(f'<div class="a center disp" style="left:0;right:0;top:157.4mm;font-size:38pt;line-height:1">交易物种起源</div>')
    p.append(f'<div class="a center caps" style="left:0;right:0;top:172.4mm;font-size:8pt;letter-spacing:.34em">THE ORIGIN OF TRADING SPECIES</div>')
    p.append(f'<div class="a center b7" style="left:10mm;right:10mm;top:178.6mm;font-size:9pt;line-height:1.4">{esc(tag)}</div>')
    p.append(f'<div class="a center" style="left:8mm;right:8mm;top:185.4mm;font-size:7.8pt;color:{C["ink_2"]}">{esc(meta)}</div>')
    p.append(f'<div class="a center" style="left:8mm;right:8mm;top:190.4mm;font-size:7.6pt;color:{C["ink_2"]}">{esc(sub)}</div>')
    p.append(f'<div class="a center" style="left:8mm;right:8mm;top:197.4mm;font-size:7pt;color:{C["ink_2"]}">{esc(disc)}</div>')
    return Card(key="book-p01", w=PW, h=PH, html=trim("".join(p), PW, PH), label="规则书 第 1 页 · 封面")


def back_cover(m: Model) -> Card:
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{PW + 6}mm;height:{PH + 6}mm;background:{C["sky_deep"]}"></div>',
         f'<div class="a" style="left:-3mm;top:-3mm;width:{PW + 6}mm;height:{PH + 6}mm;overflow:hidden">{icons.sun_rays(PW + 6, PH + 6, (PW + 6) / 2, 82, 36, C["paper_light"], 0.07)}</div>']
    p.append(f'<div class="a center disp" style="left:0;right:0;top:20mm;font-size:24pt;color:{C["sun"]}">交易物种起源</div>')
    p.append(f'<div class="a center caps" style="left:0;right:0;top:30.6mm;font-size:7.4pt;letter-spacing:.3em;color:{C["paper_light"]}">THE ORIGIN OF TRADING SPECIES</div>')
    qs = 30.0
    bw, bh = qrsvg.block_size(qs, 3, "扫码开局")
    p.append(qrsvg.block("start", (PW - bw) / 2, 48, qs, 3, "扫码开局", "选人数 · 单人对 AI · 手机对局", where="规则书封底"))
    meds = []
    for sid in [s for s in SPECIES_ORDER if s != "beaver"]:
        md_ = art.medal(sid)
        if md_:
            meds.append(f'<div class="col" style="align-items:center;gap:1mm"><span style="display:block;width:14mm;height:14mm;border-radius:50%;overflow:hidden;box-shadow:0 0 0 0.7mm {SPECIES_COLOR[sid]}">'
                        f'<img src="{md_["uri"]}" style="width:100%;height:100%"></span><span class="b7" style="font-size:7.4pt;color:{C["paper_light"]}">{esc(m.sp.get(sid, {}).get("name", ""))}</span></div>')
    p.append(f'<div class="a row" style="left:12mm;right:12mm;top:{48 + bh + 14:.1f}mm;justify-content:space-between">{"".join(meds)}</div>')
    p.append(f'<div class="a center" style="left:14mm;right:14mm;top:{48 + bh + 36:.1f}mm;font-size:8.4pt;line-height:1.6;color:{C["paper_light"]}">'
             f'猎豹、大象、狐狸、猫头鹰、狐獴、变色龙，还有隐藏的海狸。<br>没有高低，只是习惯不同。</div>')
    p.append(f'<div class="a center" style="left:10mm;right:10mm;top:190mm;font-size:7.4pt;line-height:1.5;color:{C["paper_light"]}">'
             f'{DISC}。游戏里的资金和收益都是模拟的。<br>规则书 v1.0 · 1–5 人</div>')
    return Card(key="book-p16", w=PW, h=PH, html=trim("".join(p), PW, PH), label="规则书 第 16 页 · 封底")


PLAN = [
    # (页号, 页眉, [段落名…])
    (2, "目录", ["这是个什么游戏"]),
    (3, "配件清单", ["配件清单"]),
    (4, "准备", ["准备"]),
    (5, "序章 · 一季怎么走", ["序章", "一季怎么走"]),
    (6, "名场面六步", ["名场面六步#1"]),
    (7, "名场面六步", ["名场面六步#2"]),
    (8, "五种小格子 · 两本账", ["五种小格子", "两本账"]),
    (9, "驿站与物种币 · 终局", ["驿站与物种币", "终局#1"]),
    (10, "终局", ["终局#2"]),
    (11, "招牌机制", ["招牌机制"]),
    (12, "单人 · 多人变体", ["单人：你和两只 AI", "多人变体"]),
    (13, "一局示例", ["一局示例：老周和小林"]),
    (14, "和手机互通 · 常见问题", ["和手机互通", "常见问题"]),
    (15, "设计说明 · 制作与数据说明", ["设计说明", "制作与数据说明"]),
]


def _toc(secs):
    first = {}
    for n, _, names in PLAN:
        for nm in names:
            base = nm.split("#")[0]
            first.setdefault(base, n)
    rows = []
    for nm, n in first.items():
        rows.append(f'<div class="row" style="gap:0.6em;padding:0.28em 0;border-bottom:0.5pt dotted {C["ink_3"]}">'
                    f'<span>{esc(nm)}</span><span class="sp"></span><span class="num" style="font-size:1.15em">{n}</span></div>')
    return (f'<div class="toc" style="columns:2;column-gap:6mm;margin-bottom:1.2em">{"".join(rows)}</div>')


def book_pages(m: Model) -> list[Card]:
    secs = rules_sections()
    _wording_note()
    six1, six2 = split_at(secs.get("名场面六步", ""), "**4. ")
    end1, end2 = split_at(secs.get("终局", ""), "**2. ")
    part = {"名场面六步#1": six1, "名场面六步#2": six2, "终局#1": end1, "终局#2": end2}
    pages = [cover(m, secs)]
    no = 0
    for n, head, names in PLAN:
        html = []
        if n == 2:
            html.append(h2("目录"))
            html.append(_toc(secs))
        for nm in names:
            base = nm.split("#")[0]
            body = part.get(nm, secs.get(base, ""))
            if not nm.endswith("#2"):
                no += 1
                html.append(h2(base, no))
            else:
                html.append(f'<div class="cont">{esc(base)}（续）</div>')
            if base == "配件清单":
                html.append(md(body))
                html.append(components_grid(m))
                continue
            if base == "准备":
                html.append(f'<div class="diag center">{board_diagram(112)}</div>')
            if base == "一季怎么走":
                html.append(season_steps())
            if nm == "名场面六步#1":
                html.append(scene_ribbon())
                html.append(md(body))
                html.append(scene_area_diagram())
                continue
            if nm == "名场面六步#2":
                html.append(md(body))
                html.append(slip_figure(m))
                continue
            if base == "单人：你和两只 AI":
                html.append(md(body))
                html.append(ai_board_figure(m))
                continue
            if base == "五种小格子":
                html.append(cells_table(secs))
                continue
            if base == "驿站与物种币":
                html.append(md(body))
                html.append(coin_faces_inline())
                continue
            if base == "序章":
                html.append(md(body, cls_quote="quote"))
                continue
            html.append(md(body))
        pages.append(_page(n, "".join(html), head))
    pages.append(back_cover(m))
    return pages


def spreads(pages: list[Card]) -> list[tuple[Card, Card]]:
    n = len(pages)
    assert n % 4 == 0, f"规则书页数 {n} 不是 4 的倍数"
    out = []
    for i in range(n // 4):
        out.append((pages[n - 1 - 2 * i], pages[2 * i]))
        out.append((pages[1 + 2 * i], pages[n - 2 - 2 * i]))
    return out


def spread_sheet(l: Card, r: Card, slug=10.0) -> str:
    """对页拼版：外侧留出血，书脊处不留，四角裁切线 + 书脊折线。"""
    W2, H2 = 2 * PW + 6, PH + 6
    x0, y0 = slug, slug
    parts = [f'<div class="a" style="left:{x0}mm;top:{y0}mm;width:{PW + 3}mm;height:{H2}mm;overflow:hidden">{l.root(0, 0)}</div>',
             f'<div class="a" style="left:{x0 + PW + 3}mm;top:{y0}mm;width:{PW + 3}mm;height:{H2}mm;overflow:hidden">{r.root(-3, 0)}</div>']
    k = "#000"
    tx0, tx1, ty0, ty1 = x0 + 3, x0 + 3 + 2 * PW, y0 + 3, y0 + 3 + PH
    L = 5.0
    marks = []
    for x in (tx0, tx1):
        marks.append(f'<line x1="{x}" y1="{ty0 - 3 - L}" x2="{x}" y2="{ty0 - 3}" stroke="{k}" stroke-width="0.25"/>')
        marks.append(f'<line x1="{x}" y1="{ty1 + 3}" x2="{x}" y2="{ty1 + 3 + L}" stroke="{k}" stroke-width="0.25"/>')
    for y in (ty0, ty1):
        marks.append(f'<line x1="{tx0 - 3 - L}" y1="{y}" x2="{tx0 - 3}" y2="{y}" stroke="{k}" stroke-width="0.25"/>')
        marks.append(f'<line x1="{tx1 + 3}" y1="{y}" x2="{tx1 + 3 + L}" y2="{y}" stroke="{k}" stroke-width="0.25"/>')
    sx = x0 + 3 + PW
    marks.append(f'<line x1="{sx}" y1="{ty0 - 3 - L}" x2="{sx}" y2="{ty0 - 3}" stroke="{k}" stroke-width="0.25" stroke-dasharray="1 0.6"/>')
    marks.append(f'<line x1="{sx}" y1="{ty1 + 3}" x2="{sx}" y2="{ty1 + 3 + L}" stroke="{k}" stroke-width="0.25" stroke-dasharray="1 0.6"/>')
    pw, ph = W2 + 2 * slug, H2 + 2 * slug
    parts.append(f'<svg class="a" style="left:0;top:0" width="{pw}mm" height="{ph}mm" viewBox="0 0 {pw} {ph}">{"".join(marks)}</svg>')
    lab = f'{l.label.replace("规则书 ", "")} ｜ {r.label.replace("规则书 ", "")} · 骑马钉对页'
    parts.append(f'<div class="a slug" style="left:{x0 + 3}mm;top:{ph - slug + 4.6:.1f}mm;font-size:7pt;color:#000">{esc(lab)}</div>')
    return "".join(parts), pw, ph


# ---------------------------------------------------------------- 快速入门卡 A4

QW, QH = 210.0, 297.0


def quickstart(m: Model) -> Card:
    txt = content.load_text("quickstart.md")
    title = txt.splitlines()[0].lstrip("# ").strip()
    secs = {}
    for part in re.split(r"\n(?=## )", txt):
        if part.startswith("## "):
            head, _, body = part.partition("\n")
            secs[head[3:].strip()] = body.strip()
    callout = re.search(r"^>\s*(.+)$", txt, re.M)
    callout = callout.group(1) if callout else ""
    tail = secs.get("终局 3 步", "")
    tail_list, _, tail_rest = tail.partition("\n\n")
    closing = [l for l in tail_rest.splitlines() if l.strip()]
    M = 12.0
    h = hero()
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{QW + 6}mm;height:{QH + 6}mm;background:{C["paper"]}"></div>',
         f'<div class="a" style="left:-3mm;top:-3mm;width:{QW + 6}mm;height:53mm;background:{C["sky_deep"]}"></div>',
         f'<div class="a" style="left:-3mm;top:-3mm;width:{QW + 6}mm;height:53mm;overflow:hidden">{icons.sun_rays(QW + 6, 53, 178, 26, 36, C["paper_light"], 0.08)}</div>']
    if h:
        p.append(kite_emblem(150, 5, 44, 1.2))
    p.append(f'<div class="a mstripe" style="left:-3mm;top:50mm;width:{QW + 6}mm;height:1.4mm"></div>')
    name, _, sub = title.partition("·")
    p.append(f'<div class="a" style="left:{M}mm;top:9mm;color:{C["paper_light"]}"><div class="caps" style="font-size:8pt;letter-spacing:.3em">{esc(name.strip())} · 快速入门</div>'
             f'<div class="disp" style="font-size:34pt;line-height:1.05;margin-top:2.4mm;color:{C["sun"]}">{esc(sub.strip())}</div>'
             f'<div class="caps" style="font-size:7.4pt;letter-spacing:.28em;margin-top:2.6mm">THE ORIGIN OF TRADING SPECIES · QUICK START</div></div>')
    p.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:56mm;min-height:11mm;background:{C["sun"]};border-radius:2mm;padding:2mm 3.4mm;font-size:9pt;line-height:1.4;gap:2.4mm">'
             f'{icons.warn_corner(6)}<div>{inline(callout)}</div></div>')

    def panel(x, y, w, hh, no, head, body_html, color):
        return (f'<div class="a" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{hh}mm;background:{C["paper_light"]};border-radius:2.6mm;border:0.45mm solid {C["ink"]}"></div>'
                f'<div class="a row" style="left:{x}mm;top:{y}mm;width:{w}mm;height:11mm;background:{color};border-radius:2.6mm 2.6mm 0 0;border:0.45mm solid {C["ink"]};padding:0 3.4mm;gap:2mm;color:{C["paper_light"]}">'
                f'<span class="num" style="font-size:16pt">{no}</span><span class="disp" style="font-size:14pt">{esc(head)}</span></div>'
                f'<div class="a fit bk qs" data-min="7.6" data-what="快速入门 {head}" style="left:{x + 3.6}mm;top:{y + 14}mm;width:{w - 7.2}mm;height:{hh - 17}mm">{body_html}</div>')

    cw = (QW - 2 * M - 6) / 2
    xL, xR = M, M + cw + 6
    p.append(panel(xL, 72, cw, 74, "1", "准备 3 步", md(secs.get("准备 3 步", "")), C["ochre"]))
    p.append(panel(xL, 150, cw, 56, "2", "一季 4 步", md(secs.get("一季 4 步", "")), C["sage"]))
    p.append(f'<div class="a" style="left:{xL}mm;top:210mm;width:{cw}mm">{board_diagram(cw)}</div>')
    p.append(panel(xR, 72, cw, 100, "3", "名场面 6 步", md(secs.get("名场面 6 步", "")), C["sky_deep"]))
    p.append(panel(xR, 176, cw, 58, "4", "终局 3 步", md(tail_list), C["mustard"]))
    p.append(f'<div class="a" style="left:{xR}mm;top:238mm;width:{cw - 30}mm;font-size:8pt;line-height:1.55">{"".join(f"<p style=margin-bottom:1.2mm>{inline(c)}</p>" for c in closing if DISC not in c)}</div>')
    qs = 22.0
    bw, bh = qrsvg.block_size(qs, 2.4, "扫码开局")
    p.append(qrsvg.block("start", QW - M - bw + 0.6, 238, qs, 2.4, "扫码开局", "", where="快速入门卡"))
    p.append(f'<div class="a disc" style="left:{M}mm;top:{QH - 9}mm">{DISC} · 细节查规则书</div>')
    return Card(key="quickstart", w=QW, h=QH, html=trim("".join(p), QW, QH), qr=["start"], label="快速入门卡 A4")
