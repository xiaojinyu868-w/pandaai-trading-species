"""主棋盘：A2 594×420 单张 + 四张 A4（297×210）拼接版。

方向：左上角总起点，顺时针。上边春、右边夏、下边秋、左边冬；每条边 本季起点（角）→ ①–⑤ → 名场面门。
轨道本身用中性纸色，季节色只用在小面积的标识上（季节色里的夏红和“涨”同色，不铺大面积）。
"""

from __future__ import annotations

from pathlib import Path

from . import art, content, icons
from .c_a6 import on
from .core import Card, esc, trim
from .model import Model
from .paths import ROOT
from .tokens import C, SEASON, SPECIES_COLOR, SPECIES_ORDER

W, H = 594.0, 420.0
MG = 12.0
D = 54.0
CH = 57.75  # 上下边：④⑤之间正好落在 A4 拼缝 x=297
CV = 36.0   # 左右边：④⑤之间正好落在 A4 拼缝 y=210
DOOR_H = W - 2 * MG - 2 * D - 5 * CH
DOOR_V = H - 2 * MG - 2 * D - 5 * CV
DISC = "投资者教育游戏，不构成投资建议"
SEASON_CN = {"spring": "春", "summer": "夏", "autumn": "秋", "winter": "冬"}
NUM = "①②③④⑤"

CELLS = [
    ("supply", "补给站", "拿 1 研究点"),
    ("chance", "机会", "抽一张机会牌，A、B 选一个，看牌底倒印的图标"),
    ("research", "研究所", "摸两张规则牌，留一张"),
    ("dataport", "数据港口", "读代码答题；答对拿 1 研究点 + 1 枚海狸币"),
    ("calm", "冷静亭", "坐下：不能选 A，免费看 1 张证据；不坐：重掷"),
]


def _tile(x, y, w, h, bg=None, extra=""):
    bg = bg or C["paper_light"]
    return (f'<div class="a" style="left:{x + 0.9:.2f}mm;top:{y + 0.9:.2f}mm;width:{w - 1.8:.2f}mm;height:{h - 1.8:.2f}mm;'
            f'background:{bg};border:0.45mm solid {C["ink"]};border-radius:2.6mm;box-sizing:border-box;{extra}"></div>')


def _circle_art(kind, x, y, d, ring=None):
    a = art.tile_art(kind)
    if not a:
        return ""
    rg = f"box-shadow:0 0 0 0.5mm {ring};" if ring else ""
    return (f'<div class="a" style="left:{x:.2f}mm;top:{y:.2f}mm;width:{d}mm;height:{d}mm;border-radius:50%;overflow:hidden;{rg}">'
            f'<img src="{a["uri"]}" style="width:100%;height:100%;display:block"></div>')


def _num(x, y, i, season, d=6.4):
    col = SEASON[season]["color"]
    return (f'<div class="a row" style="left:{x:.2f}mm;top:{y:.2f}mm;width:{d}mm;height:{d}mm;border-radius:50%;background:{col};'
            f'color:{C["paper_light"]};justify-content:center;box-shadow:0 0 0 0.45mm {C["paper_light"]}">'
            f'<span class="num" style="font-size:{d * 1.75:.1f}pt;line-height:1;padding-top:0.3mm">{i}</span></div>')


def _cell_h(x, y, i, kind, name, eff, season):
    w, h = CH, D
    out = [_tile(x, y, w, h)]
    out.append(_circle_art(kind, x + (w - 27) / 2, y + 3.2, 27))
    out.append(_num(x + 3, y + 3, i + 1, season))
    out.append(f'<div class="a center disp" style="left:{x}mm;width:{w}mm;top:{y + 31.4:.2f}mm;font-size:12pt">{esc(name)}</div>')
    out.append(f'<div class="a center fit" data-min="7" data-what="棋盘格 {name}" style="left:{x + 3.4:.2f}mm;width:{w - 6.8:.2f}mm;top:{y + 37.2:.2f}mm;height:13.2mm;'
               f'font-size:7.4pt;line-height:1.25;color:{C["ink_2"]}">{esc(eff)}</div>')
    return "".join(out)


def _cell_v(x, y, i, kind, name, eff, season):
    w, h = D, CV
    out = [_tile(x, y, w, h)]
    out.append(_circle_art(kind, x + 3, y + (h - 25) / 2, 25))
    out.append(_num(x + 2, y + 1.8, i + 1, season, 6))
    out.append(f'<div class="a disp" style="left:{x + 30.2:.2f}mm;top:{y + 3.4:.2f}mm;font-size:11pt;white-space:nowrap">{esc(name)}</div>')
    out.append(f'<div class="a fit" data-min="7" data-what="棋盘格 {name}" style="left:{x + 30.2:.2f}mm;width:{w - 32.6:.2f}mm;top:{y + 9.4:.2f}mm;height:{h - 11.6:.2f}mm;'
               f'font-size:7.2pt;line-height:1.25;color:{C["ink_2"]}">{esc(eff)}</div>')
    return "".join(out)


def _arch(w, h, color, closed=False):
    r = w / 2
    path = f"M0.4 {h - 0.4} V{r} A{r - 0.4} {r - 0.4} 0 0 1 {w - 0.4} {r} V{h - 0.4} Z"
    if closed:
        return (f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" style="flex:none"><path d="{path}" fill="{C["paper"]}" stroke="{C["ink_3"]}" stroke-width="0.5" stroke-dasharray="1.4 0.9"/>'
                f'<text x="{w / 2}" y="{h * 0.68:.2f}" font-size="{w * 0.5:.2f}" text-anchor="middle" fill="{C["ink_3"]}" font-family="Smiley Sans Oblique">?</text></svg>')
    inner = f"M{w * 0.2:.2f} {h - 0.4} V{r + 0.6:.2f} A{r * 0.6:.2f} {r * 0.6:.2f} 0 0 1 {w * 0.8:.2f} {r + 0.6:.2f} V{h - 0.4}"
    return (f'<svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" style="flex:none"><path d="{path}" fill="{color}" stroke="{C["ink"]}" stroke-width="0.45"/>'
            f'<path d="{inner}" fill="{C["ink"]}" opacity="0.82"/>'
            f'<circle cx="{w * 0.66:.2f}" cy="{h * 0.7:.2f}" r="{w * 0.045:.2f}" fill="{C["sun"]}"/></svg>')


def _door_panel(door, info, season, w, h, size="h"):
    col = SEASON[season]["color"]
    is_open = info.get("open", True)
    tier = info.get("tier") or ""
    teaser = info.get("teaser", "")
    aw, ah = (15, 21) if size == "h" else (13, 18)
    arch = _arch(aw, ah, col, closed=not is_open)
    if is_open:
        chip = (f'<span class="chip" style="background:{C["ink"]};color:{C["paper_light"]};height:4mm;font-size:7pt;padding:0 1.4mm">{esc(tier)}</span>'
                if tier and tier != "P0" else "")
        head = f'<span class="disp" style="font-size:{13 if size == "h" else 11}pt">门 {door}</span>{chip}'
        body = esc(teaser)
    else:
        head = f'<span class="disp" style="font-size:{13 if size == "h" else 11}pt;color:{C["ink_3"]}">门 {door}</span><span style="font-size:7pt;font-weight:700;color:{C["ink_3"]}">未开放 · 敬请期待</span>'
        body = esc(teaser)
    fs = 7.6 if size == "h" else 7.2
    if size == "v":
        return (f'<div class="col" style="width:{w}mm;height:{h}mm;gap:1.6mm">'
                f'<div class="row" style="gap:2mm;align-items:flex-end">{arch}<div class="col" style="gap:0.8mm;padding-bottom:0.4mm">{head}</div></div>'
                f'<div class="fit" data-min="7" data-what="门 {door} 预告" style="font-size:{fs}pt;line-height:1.3;color:{C["ink_2"] if is_open else C["ink_3"]};height:{h - ah - 2:.1f}mm">{body}</div></div>')
    return (f'<div class="row" style="width:{w}mm;height:{h}mm;gap:2mm;align-items:center">{arch}'
            f'<div class="col" style="flex:1;min-width:0;gap:0.8mm"><div class="row" style="gap:1.4mm">{head}</div>'
            f'<div class="fit" data-min="7" data-what="门 {door} 预告" style="font-size:{fs}pt;line-height:1.3;color:{C["ink_2"] if is_open else C["ink_3"]};max-height:{h - 7:.1f}mm;height:{h - 7:.1f}mm">{body}</div></div></div>')


def _door_info(m: Model, season):
    a = next((s for s in m.scenes if s["season"] == season and s.get("door") == "A"), None)
    infoA = {"open": True, "tier": (a or {}).get("tier", "P0"), "teaser": (a or {}).get("door_teaser", "")}
    b = m.door_b(season)
    infoB = {"open": b.get("open"), "tier": b.get("tier"), "teaser": b.get("teaser", "")}
    return infoA, infoB


def _door_h(m, x, y, season):
    w, h = DOOR_H, D
    A, B = _door_info(m, season)
    col = SEASON[season]["color"]
    out = [_tile(x, y, w, h, C["paper"])]
    out.append(f'<div class="a row" style="left:{x + 4:.2f}mm;width:{w - 8:.2f}mm;top:{y + 3.2:.2f}mm;height:6.4mm;gap:2mm">'
               f'{icons.season_disc(season, 6.4)}<span class="disp" style="font-size:12.5pt">{SEASON_CN[season]}季 · 名场面门</span><span class="sp"></span>'
               f'<span style="font-size:7.4pt;color:{C["ink_2"]}">掷 6 直达门口，再拿 1 研究点</span></div>')
    out.append(f'<div class="a" style="left:{x + 4:.2f}mm;width:{w - 8:.2f}mm;top:{y + 11.2:.2f}mm;border-top:0.5pt solid {col}"></div>')
    pw = (w - 8 - 5) / 2
    out.append(f'<div class="a row" style="left:{x + 4:.2f}mm;top:{y + 13.6:.2f}mm;gap:5mm">'
               f'{_door_panel("A", A, season, pw, 36)}{_door_panel("B", B, season, pw, 36)}</div>')
    return "".join(out)


def _door_v(m, x, y, season):
    w, h = D, DOOR_V
    A, B = _door_info(m, season)
    col = SEASON[season]["color"]
    out = [_tile(x, y, w, h, C["paper"])]
    out.append(f'<div class="a row" style="left:{x + 3:.2f}mm;width:{w - 6:.2f}mm;top:{y + 2.8:.2f}mm;height:5.4mm;gap:1.4mm">'
               f'{icons.season_disc(season, 5.4)}<span class="disp" style="font-size:10.5pt;white-space:nowrap">{SEASON_CN[season]}季 · 名场面门</span></div>')
    out.append(f'<div class="a" style="left:{x + 3:.2f}mm;width:{w - 6:.2f}mm;top:{y + 9.2:.2f}mm;font-size:7pt;color:{C["ink_2"]};white-space:nowrap">掷 6 直达门口，再拿 1 研究点</div>')
    out.append(f'<div class="a" style="left:{x + 3:.2f}mm;width:{w - 6:.2f}mm;top:{y + 13.4:.2f}mm;border-top:0.5pt solid {col}"></div>')
    ph = (h - 17 - 4) / 2
    out.append(f'<div class="a col" style="left:{x + 3:.2f}mm;top:{y + 16:.2f}mm;gap:2mm">'
               f'{_door_panel("A", A, season, w - 6, ph, "v")}{_door_panel("B", B, season, w - 6, ph, "v")}</div>')
    return "".join(out)


def _corner(m, x, y, label, text, start_season, kind):
    out = [_tile(x, y, D, D, C["paper"])]
    out.append(_circle_art(kind, x + (D - 27) / 2, y + 2.6, 27))
    out.append(f'<div class="a center disp fit" data-min="9" data-what="角 {label}" style="left:{x + 2:.2f}mm;width:{D - 4:.2f}mm;top:{y + 30.2:.2f}mm;height:5.4mm;font-size:11.5pt;white-space:nowrap">{esc(label)}</div>')
    out.append(f'<div class="a center fit" data-min="7" data-what="角说明" style="left:{x + 3:.2f}mm;width:{D - 6:.2f}mm;top:{y + 36:.2f}mm;height:6.6mm;font-size:7.2pt;line-height:1.25;color:{C["ink_2"]}">{esc(text)}</div>')
    col = SEASON[start_season]["color"]
    out.append(f'<div class="a row" style="left:{x + 3:.2f}mm;width:{D - 6:.2f}mm;top:{y + 44.6:.2f}mm;height:5.4mm;justify-content:center">'
               f'<span class="chip" style="background:{col};color:{C["paper_light"]};height:5mm;font-size:7.6pt">{SEASON_CN[start_season]}季起点 →</span></div>')
    return "".join(out)


def _slot(x, y, w, h, title, sub="", kind=None, icon=None, fill=False):
    bg = "rgba(251,244,228,.8)" if fill else "rgba(251,244,228,.16)"
    out = [f'<div class="a" style="left:{x:.2f}mm;top:{y:.2f}mm;width:{w}mm;height:{h}mm;border-radius:3mm;background:{bg};'
           f'border:0.7mm dashed {C["paper_light"]};box-shadow:0 0 0 0.5mm {C["ink"]}, inset 0 0 0 0.5mm {C["ink"]};box-sizing:border-box"></div>']
    a = art.tile_art(kind) if kind else (art.icon(icon) if icon else None)
    head = ""
    if a:
        head = (f'<span style="display:inline-block;width:9mm;height:9mm;border-radius:50%;overflow:hidden;vertical-align:middle;margin-right:-1.6mm;'
                f'position:relative;box-shadow:0 0 0 0.5mm {C["ink"]}"><img src="{a["uri"]}" style="width:100%;height:100%"></span>')
    out.append(f'<div class="a center" style="left:{x}mm;width:{w}mm;top:{y + 4:.2f}mm">{head}<span class="chip ink" style="font-size:8.4pt;height:6mm;vertical-align:middle;padding-left:3mm">{esc(title)}</span></div>')
    if sub:
        out.append(f'<div class="a center" style="left:{x}mm;width:{w}mm;top:{y + 14.2:.2f}mm"><span style="display:inline-block;font-size:7.2pt;line-height:1.3;'
                   f'background:{C["paper_light"]};border-radius:1mm;padding:0.3mm 1.6mm;color:{C["ink_2"]}">{esc(sub)}</span></div>')
    return "".join(out)


def _center(m: Model) -> str:
    out = []
    sw, sh = 67.0, 92.0
    aw, ah = 109.0, 152.0
    cx = W / 2
    ax = cx - aw / 2
    r1, r2 = 116.0, 214.0           # 两排牌位：拼缝 y=210 落在两排之间
    lx_e = ax - 6 - sw
    rx_e = ax + aw + 6
    lx_d = lx_e - 10 - sw
    rx_d = rx_e + sw + 10
    # 标题（居中，拼缝落在“物”“种”之间）
    out.append(f'<div class="a center" style="left:{cx - 110}mm;width:220mm;top:73mm">'
               f'<div style="display:inline-block;background:{C["ink"]};color:{C["sun"]};border-radius:2.4mm;padding:2.6mm 10mm 2.8mm;box-shadow:0 0 0 1.2mm {C["paper_light"]}">'
               f'<div class="disp" style="font-size:34pt;line-height:1">交易物种起源</div>'
               f'<div class="caps" style="font-size:7.6pt;letter-spacing:.32em;margin-top:1.8mm;color:{C["paper_light"]}">THE ORIGIN OF TRADING SPECIES</div></div></div>')
    out.append(_slot(lx_d, r1, sw, sh, "机会牌", "踩到 ② 抽一张", kind="chance"))
    out.append(_slot(lx_d, r2, sw, sh, "规则牌", "踩到 ③ 摸两张留一张", kind="research"))
    out.append(_slot(rx_d, r1, sw, sh, "数据港口", "踩到 ④ 抽一张", kind="dataport"))
    out.append(_slot(rx_d, r2, sw, sh, "补测牌", "平局时按牌背找", icon="magnifier"))
    out.append(_slot(lx_e, r1, sw, sh, "量价", "证据 · 1 研究点看", icon="chart", fill=True))
    out.append(_slot(lx_e, r2, sw, sh, "数据", "证据 · 1 研究点看", icon="ledger", fill=True))
    out.append(_slot(rx_e, r1, sw, sh, "消息", "证据 · 1 研究点看", icon="phone", fill=True))
    out.append(_slot(rx_e, r2, sw, sh, "锦囊", "猫头鹰的信 · 1 研究点看", icon="letter", fill=True))
    # 名场面区：文字避开两条拼缝
    ay = r1 + (r2 + sh - r1 - ah) / 2
    out.append(f'<div class="a" style="left:{ax:.2f}mm;top:{ay:.2f}mm;width:{aw}mm;height:{ah}mm;border-radius:3.4mm;background:rgba(251,244,228,.92);'
               f'border:0.8mm solid {C["ink"]};box-sizing:border-box"></div>')
    out.append(f'<div class="a" style="left:{ax + 3:.2f}mm;top:{ay + 3:.2f}mm;width:{aw - 6}mm;height:{ah - 6}mm;border-radius:2.4mm;border:0.4mm dashed {C["ink_3"]};box-sizing:border-box"></div>')
    out.append(f'<div class="a center" style="left:{ax}mm;width:{aw}mm;top:{ay + 9:.2f}mm"><span class="chip ink" style="font-size:9.4pt;height:6.6mm;padding:0 3.4mm">名场面区</span></div>')
    hw = aw / 2 - 9
    out.append(f'<div class="a" style="left:{ax + 7:.2f}mm;width:{hw:.2f}mm;top:{ay + 24:.2f}mm;font-size:8pt;line-height:1.5;color:{C["ink_2"]}">'
               f'<b style="color:{C["ink"]}">场景牌</b><br>全员进门后，翻到盲测面朝上</div>')
    out.append(f'<div class="a" style="left:{cx + 2:.2f}mm;width:{hw:.2f}mm;top:{ay + 24:.2f}mm;font-size:8pt;line-height:1.5;color:{C["ink_2"]}">'
               f'<b style="color:{C["ink"]}">快进 · 揭幕</b><br>扣在这里，按顺序翻开</div>')
    steps = ["盲入场", "开证据", "填委托单", "三二一亮单", "快进", "揭幕"]
    col1 = "".join(f'<div class="row" style="gap:1.2mm;white-space:nowrap;margin-bottom:2.2mm"><span class="kb" style="width:4.8mm;height:4.8mm;font-size:9.4pt">{i + 1}</span>'
                   f'<span style="font-size:8pt;font-weight:700">{steps[i]}</span></div>' for i in range(3))
    col2 = "".join(f'<div class="row" style="gap:1.2mm;white-space:nowrap;margin-bottom:2.2mm"><span class="kb" style="width:4.8mm;height:4.8mm;font-size:9.4pt">{i + 1}</span>'
                   f'<span style="font-size:8pt;font-weight:700">{steps[i]}</span></div>' for i in range(3, 6))
    sy = 216.0
    out.append(f'<div class="a" style="left:{ax + 7:.2f}mm;width:{hw:.2f}mm;top:{sy:.2f}mm">{col1}</div>')
    out.append(f'<div class="a" style="left:{cx + 2:.2f}mm;width:{hw:.2f}mm;top:{sy:.2f}mm">{col2}</div>')
    out.append(f'<div class="a" style="left:{ax + 7:.2f}mm;top:{ay + ah - 11:.2f}mm;font-size:7.2pt;color:{C["ink_3"]}">名场面六步</div>')
    out.append(f'<div class="a right" style="left:{cx + 2:.2f}mm;width:{hw:.2f}mm;top:{ay + ah - 11:.2f}mm;font-size:7.2pt;color:{C["ink_3"]}">详见规则书</div>')
    # 物种币库：7 枚，往左挪半格让拼缝落在第 4、5 枚之间
    yb = r2 + sh + 7
    coin, gap = 20.0, 5.5
    cw = 7 * coin + 6 * gap
    x0 = cx - 4 * coin - 3.5 * gap
    coins = []
    for sid in SPECIES_ORDER:
        md = art.medal(sid)
        img = (f'<div style="width:{coin}mm;height:{coin}mm;border-radius:50%;overflow:hidden;border:1mm solid {SPECIES_COLOR[sid]};box-sizing:border-box;background:{C["paper"]}">'
               f'<img src="{md["uri"]}" style="width:100%;height:100%"></div>') if md else ""
        coins.append(f'<div class="col" style="align-items:center;gap:0.6mm;width:{coin}mm">{img}<span class="b7" style="font-size:7.4pt;background:rgba(251,244,228,.92);padding:0 1mm;border-radius:1mm;white-space:nowrap">{esc(m.sp.get(sid, {}).get("name", sid))}</span></div>')
    out.append(f'<div class="a" style="left:{x0 - 5:.2f}mm;top:{yb - 2.5:.2f}mm;width:{cw + 10:.2f}mm;height:30.4mm;border-radius:15mm;background:rgba(251,244,228,.72)"></div>')
    out.append(f'<div class="a row" style="left:{x0:.2f}mm;top:{yb:.2f}mm;gap:{gap}mm;align-items:flex-start">{"".join(coins)}</div>')
    out.append(f'<div class="a" style="left:{x0 + cw + 8:.2f}mm;top:{yb + 4:.2f}mm;width:30mm;font-size:7.4pt;line-height:1.4;color:{C["ink"]};'
               f'background:rgba(251,244,228,.9);border-radius:1.4mm;padding:1mm 1.8mm"><b>物种币库</b><br>每种 8 枚<br>正面实心、背面空心</div>')
    # 研究点、骰子位
    for x, title, sub in ((lx_d, "研究点 · 公共库存", ""), (rx_d, "骰子 · 沙漏", "跌停锁也放这里")):
        d = 40.0
        out.append(f'<div class="a" style="left:{x + (sw - d) / 2:.2f}mm;top:{yb - 6:.2f}mm;width:{d}mm;height:{d}mm;border-radius:50%;background:rgba(251,244,228,.16);'
                   f'border:0.7mm dashed {C["paper_light"]};box-shadow:0 0 0 0.5mm {C["ink"]}, inset 0 0 0 0.5mm {C["ink"]};box-sizing:border-box"></div>')
        out.append(f'<div class="a center" style="left:{x - 6}mm;width:{sw + 12}mm;top:{yb + 8:.2f}mm"><span class="chip ink" style="font-size:8.2pt;height:5.8mm">{title}</span></div>')
        if sub:
            out.append(f'<div class="a center" style="left:{x}mm;width:{sw}mm;top:{yb + 15.4:.2f}mm"><span style="display:inline-block;font-size:7.2pt;background:{C["paper_light"]};border-radius:1mm;padding:0.3mm 1.6mm;color:{C["ink_2"]}">{sub}</span></div>')
    return "".join(out)


def board(m: Model) -> Card:
    src = first_board_src()
    bg = art.plain(src, "board_bg", scale=2.0) if src else None
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{C["paper"]}"></div>']
    if bg:
        side = W + 6
        parts.append(f'<img src="{bg["uri"]}" style="position:absolute;left:-3mm;top:{-3 - (side - H - 6) / 2:.2f}mm;width:{side}mm;height:{side}mm">')
    else:
        content.NOTES.append("主棋盘底图缺失（style-v7/v7_board_background），暂用纸色")
    parts.append(f'<div class="a" style="left:5mm;top:5mm;width:{W - 10}mm;height:{H - 10}mm;border:0.7mm solid {C["ink"]};border-radius:4mm;box-sizing:border-box"></div>')
    # 轨道底
    parts.append(f'<svg class="a" style="left:{MG - 1.4}mm;top:{MG - 1.4}mm" width="{W - 2 * MG + 2.8}mm" height="{H - 2 * MG + 2.8}mm" viewBox="0 0 {W - 2 * MG + 2.8} {H - 2 * MG + 2.8}">'
                 f'<path fill-rule="evenodd" fill="{C["ink"]}" d="M0 4 Q0 0 4 0 H{W - 2 * MG - 1.2} Q{W - 2 * MG + 2.8} 0 {W - 2 * MG + 2.8} 4 V{H - 2 * MG - 1.2} Q{W - 2 * MG + 2.8} {H - 2 * MG + 2.8} {W - 2 * MG - 1.2} {H - 2 * MG + 2.8} H4 Q0 {H - 2 * MG + 2.8} 0 {H - 2 * MG - 1.2} Z '
                 f'M{D + 2.8} {D + 2.8} V{H - 2 * MG - D} H{W - 2 * MG - D} V{D + 2.8} Z"/></svg>')
    corners = {c.get("position"): c for c in m.D.get("station", {}).get("corners", [])}

    def cn(pos, default_label, default_text):
        c = corners.get(pos, {})
        return c.get("label", default_label), c.get("text", default_text)

    lab, txt = cn("左上角", "总起点 · 冬季驿站 · 终点", "从这里出发，回到这里破壳")
    parts.append(_corner(m, MG, MG, "总起点", lab.replace("总起点 · ", "") + " · " + txt, "spring", "start"))
    lab, txt = cn("右上角", "驿站 · 春→夏", "数图标，拿一枚物种币")
    parts.append(_corner(m, W - MG - D, MG, lab, txt, "summer", "station"))
    lab, txt = cn("右下角", "驿站 · 夏→秋", "数图标，拿一枚物种币")
    parts.append(_corner(m, W - MG - D, H - MG - D, lab, txt, "autumn", "station"))
    lab, txt = cn("左下角", "驿站 · 秋→冬", "数图标，拿一枚物种币")
    parts.append(_corner(m, MG, H - MG - D, lab, txt, "winter", "station"))
    # 春：上边，左→右
    for i, (k, nm, ef) in enumerate(CELLS):
        parts.append(_cell_h(MG + D + i * CH, MG, i, k, nm, ef, "spring"))
    parts.append(_door_h(m, MG + D + 5 * CH, MG, "spring"))
    # 夏：右边，上→下
    for i, (k, nm, ef) in enumerate(CELLS):
        parts.append(_cell_v(W - MG - D, MG + D + i * CV, i, k, nm, ef, "summer"))
    parts.append(_door_v(m, W - MG - D, MG + D + 5 * CV, "summer"))
    # 秋：下边，右→左
    for i, (k, nm, ef) in enumerate(CELLS):
        parts.append(_cell_h(W - MG - D - (i + 1) * CH, H - MG - D, i, k, nm, ef, "autumn"))
    parts.append(_door_h(m, MG + D, H - MG - D, "autumn"))
    # 冬：左边，下→上
    for i, (k, nm, ef) in enumerate(CELLS):
        parts.append(_cell_v(MG, H - MG - D - (i + 1) * CV, i, k, nm, ef, "winter"))
    parts.append(_door_v(m, MG, MG + D, "winter"))
    parts.append(_center(m))
    parts.append(f'<div class="a disc" style="left:{MG + D + 4:.2f}mm;top:{H - MG - D - 6.6:.2f}mm;color:{C["ink"]};background:rgba(251,244,228,.9);padding:0.4mm 1.6mm;border-radius:1mm">{DISC}</div>')
    content.NOTES.append("棋盘格子效果是规则书“五种小格子”表的缩写版；机会格写成“看牌底倒印的图标”（规则书写“翻牌背”）")
    return Card(key="board", w=W, h=H, html=trim("".join(parts), W, H), label="主棋盘 A2 594×420")


def first_board_src() -> Path | None:
    base = ROOT / "art" / "vmc-output" / "style-v7" / "v7_board_background"
    c = sorted(base.glob("**/*_1.png")) or sorted(base.glob("**/*.png"))
    return c[0] if c else None


def quadrants(b: Card) -> list[Card]:
    """A2 拆成 2×2 张 A4，内侧出血取相邻内容，拼接时对缝。"""
    inner = b.html
    pre = '<div class="trim" style="width:594.0mm;height:420.0mm">'
    assert inner.startswith(pre), "board html 结构变了"
    body = inner[len(pre):-len("</div>")]
    names = ["左上", "右上", "左下", "右下"]
    out = []
    for q in range(4):
        qx, qy = q % 2, q // 2
        html = (f'<div class="trim" style="left:{3 - qx * 297}mm;top:{3 - qy * 210}mm;width:594mm;height:420mm">{body}</div>')
        out.append(Card(key=f"board-q{q + 1}", w=297, h=210, html=html, label=f"主棋盘 A4 拼接 {q + 1}/4 {names[q]}"))
    return out
