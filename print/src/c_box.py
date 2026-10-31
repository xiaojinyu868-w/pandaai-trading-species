"""盒标：盒盖贴纸 + 长边、短边侧标（铜版不干胶，覆哑膜）。尺寸按 内径 ≥ 300×215×60 的天地盖礼盒，实际以盒子为准。

画面按美术定稿 art/refs/box_anchor_artist.jpg（标题「我不是韭菜！」）：盒盖是一整张图，字画在图里；
侧标照美术图的深色侧脊，金色标题和图标是透明底素材，人数时长、免责声明、盒内配件由代码排。
"""
from __future__ import annotations

import re

from . import art
from .c_book import DISC, rules_sections
from .core import BLEED, Card, esc, trim
from .model import Model
from .tokens import PLAYERS

LID_W, LID_H = 300.0, 215.0
LONG_W, LONG_H = 300.0, 50.0
SHORT_W, SHORT_H = 215.0, 50.0
SERIES = "交易物种起源 · 金融史名场面桌游"
SPINE = "#0E2A27"  # 盒盖标题的墨色
GOLD = "#C9A25E"   # 小字用，比金色素材亮一点，深底上好认
CREAM = "#F4E4BF"


def _age() -> str:
    cv = rules_sections().get("封面语", "")
    a = re.search(r"(\d+\s*岁以上)", cv)
    return a.group(1) if a else ""


def _meta() -> str:
    age = _age()
    return "1–5 人 · 15–60 分钟" + (f" · {age}" if age else "")


def _spine(W: float, H: float) -> str:
    bg = art.box_spine(W + 2 * BLEED, H + 2 * BLEED, SPINE)
    return (f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{SPINE}"></div>'
            f'<img class="a" src="{bg["uri"]}" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm">')


def _ratio(name: str) -> float:
    a = art.box_gold(name)
    return a["w"] / a["h"] if a else 1.0


def _gold(name: str, left: float, top: float, h: float) -> str:
    """金色素材按高度等比放。"""
    a = art.box_gold(name)
    if not a:
        return ""
    return f'<img class="a" src="{a["uri"]}" style="left:{left:.2f}mm;top:{top:.2f}mm;width:{h * a["w"] / a["h"]:.2f}mm;height:{h:.2f}mm">'


def lid(m: Model) -> Card:
    W, H = LID_W, LID_H
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{SPINE}"></div>']
    a = art.box_lid(W + 2 * BLEED, H + 2 * BLEED)
    if a:
        p.append(f'<img class="a" src="{a["uri"]}" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm">')
    return Card(key="box-lid", w=W, h=H, html=trim("".join(p), W, H), label="盒盖贴纸 300×215")


def long_side(m: Model) -> Card:
    """照美术图侧脊的顺序横排：交易所 · 标题 · 柱状图 · 上升箭头，间距相等；标题下面两行小字。"""
    W, H = LONG_W, LONG_H
    ih, th, margin = 23.0, 23.0, 13.0
    ws = [ih * _ratio("exchange"), th * _ratio("title"), ih * _ratio("chart"), ih * _ratio("arrows")]
    gap = (W - 2 * margin - sum(ws)) / 3
    xs = [margin]
    for w in ws[:-1]:
        xs.append(xs[-1] + w + gap)
    ty = 6.6
    iy = (H - ih) / 2
    p = [_spine(W, H),
         _gold("exchange", xs[0], iy, ih),
         _gold("title", xs[1], ty, th),
         _gold("chart", xs[2], iy, ih),
         _gold("arrows", xs[3], iy, ih)]
    p.append(f'<div class="a b7" style="left:{xs[1] + 0.6:.2f}mm;top:{ty + th + 2.6:.2f}mm;font-size:8.6pt;letter-spacing:.04em;color:{CREAM};white-space:nowrap">'
             f'{esc(SERIES)} · {esc(_meta())}</div>')
    p.append(f'<div class="a" style="left:{xs[1] + 0.6:.2f}mm;top:{ty + th + 7.6:.2f}mm;font-size:7.4pt;letter-spacing:.06em;color:{GOLD};white-space:nowrap">{DISC}</div>')
    return Card(key="box-long", w=W, h=H, html=trim("".join(p), W, H), label="长边侧标 300×50")


def box_contents() -> tuple[list[str], list[str]]:
    body = rules_sections().get("配件清单", "")
    pub, per = ["规则书 1 本、快速入门卡 1 张"], []
    cur = pub
    for raw in body.splitlines():
        l = raw.strip()
        if l.startswith("**每人**"):
            cur = per
            continue
        if l.startswith("**P1"):
            break
        if not l.startswith("- "):
            continue
        t = re.sub(r"（[^）]*）", "", l[2:]).strip()
        if cur is per:
            t = t.split("，")[0]
        cur.append(t)
    return pub, per


def short_side(m: Model) -> Card:
    W, H = SHORT_W, SHORT_H
    LX, RX = 8.0, 80.0
    p = [_spine(W, H), _gold("title", LX, 6.4, 12.4)]
    p.append(f'<div class="a" style="left:{LX + 0.4}mm;top:22.4mm;width:{RX - LX - 8}mm;font-size:7.6pt;line-height:1.5;color:{CREAM}">'
             f'{esc(SERIES)}<br>{esc(_meta())}</div>')
    p.append(f'<div class="a" style="left:{LX + 0.4}mm;top:37.6mm;width:{RX - LX - 6}mm;font-size:7.2pt;color:{GOLD};white-space:nowrap">{DISC}</div>')
    p.append(f'<div class="a" style="left:{RX - 5}mm;top:6mm;width:0.35mm;height:{H - 12}mm;background:{GOLD};opacity:.7"></div>')
    pub, per = box_contents()
    lis = "".join(f'<li>{esc(t)}</li>' for t in pub)
    lis2 = "".join(f'<li>{esc(t)}</li>' for t in per)
    p.append(f'<div class="a fit" data-min="7" data-what="盒标短边 盒内配件" style="left:{RX}mm;top:5.4mm;width:{W - RX - 6}mm;height:{H - 10.8}mm;font-size:7.6pt;line-height:1.36;color:{CREAM}">'
             f'<div class="row" style="gap:2mm;align-items:baseline;margin-bottom:0.8mm"><b style="font-size:1.25em;color:{GOLD}">盒内配件</b><span style="opacity:.75">公共</span></div>'
             f'<ul class="boxlist" style="columns:2;column-gap:5mm">{lis}</ul>'
             f'<div style="margin-top:0.8mm;opacity:.75">每人一套 × {len(PLAYERS)}</div><ul class="boxlist" style="columns:2;column-gap:5mm">{lis2}</ul></div>')
    return Card(key="box-short", w=W, h=H, html=trim("".join(p), W, H), label="短边侧标 215×50")


def cards(m: Model) -> list[Card]:
    return [lid(m), long_side(m), short_side(m)]


def _corner_marks(x0, y0, w, h, off=1.5, ln=5.0) -> str:
    """单件裁切角线：从出血外 off 起，沿成品边线向外 ln。"""
    x1, y1 = x0 + w, y0 + h
    b = BLEED
    L = []
    for x in (x0, x1):
        L += [(x, y0 - b - off - ln, x, y0 - b - off), (x, y1 + b + off, x, y1 + b + off + ln)]
    for y in (y0, y1):
        L += [(x0 - b - off - ln, y, x0 - b - off, y), (x1 + b + off, y, x1 + b + off + ln, y)]
    return "".join(f'<line x1="{a:.3f}" y1="{c:.3f}" x2="{e:.3f}" y2="{f:.3f}"/>' for a, c, e, f in L)


def sheets(cs: list[Card]) -> str:
    """A3 横版两张：第 1 张盒盖，第 2 张两条侧标。"""
    SW, SH = 420.0, 297.0
    lid_c, long_c, short_c = cs
    pages = []
    layouts = [[(lid_c, (SW - lid_c.w) / 2, (SH - lid_c.h) / 2 - 4)],
               [(long_c, (SW - long_c.w) / 2, 60.0), (short_c, (SW - long_c.w) / 2, 60.0 + long_c.h + 22)]]
    for k, lay in enumerate(layouts):
        parts, marks = [], []
        for c, x, y in lay:
            parts.append(c.root(x - BLEED, y - BLEED))
            marks.append(_corner_marks(x, y, c.w, c.h))
        names = "、".join(f"{c.label}" for c, _, _ in lay)
        slug = f"09_盒标 · 第 {k + 1}/2 张 · {names} · 出血 3 mm · 铜版不干胶 覆哑膜 · 《交易物种起源》v1.0"
        pages.append(f'<div class="page sheet" style="width:{SW}mm;height:{SH}mm;">{"".join(parts)}'
                     f'<svg class="marks" width="{SW}mm" height="{SH}mm" viewBox="0 0 {SW} {SH}"><g stroke="#000" stroke-width="0.1764" fill="none">{"".join(marks)}</g></svg>'
                     f'<div class="slug" style="left:12mm;bottom:5mm;">{esc(slug)}</div></div>')
    return "\n".join(pages)
