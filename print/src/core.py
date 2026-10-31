"""HTML 拼装：文档外壳、卡牌外框、A3 拼版与裁切线。所有尺寸单位 mm。"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass, field

from .paths import BUILD, DESIGN, TEMPLATES
from .tokens import C

BLEED = 3.0


def esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=True)


def tokens_css() -> str:
    css = (DESIGN / "tokens.css").read_text(encoding="utf-8")
    return css


def doc(body: str, page_w: float, page_h: float, extra_css: str = "", title: str = "print", body_class: str = "") -> str:
    css_files = ["base.css", "cards.css"]
    links = "\n".join(f'<link rel="stylesheet" href="{(TEMPLATES / f).as_uri()}">' for f in css_files if (TEMPLATES / f).exists())
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>{tokens_css()}</style>
{links}
<style>@page {{ size: {page_w}mm {page_h}mm; margin: 0; }}
{extra_css}</style>
</head><body class="{body_class}">
{body}
</body></html>"""


@dataclass
class Card:
    """一张牌（或一块板）的一面。html 是带出血尺寸的根元素内容（不含根元素本身）。"""
    key: str
    w: float  # 成品宽
    h: float  # 成品高
    html: str
    cls: str = ""
    style: str = ""
    qr: list = field(default_factory=list)  # 这一面印的二维码 url 列表
    label: str = ""  # 人能读的说明，用于清单和预览

    @property
    def bw(self):
        return self.w + 2 * BLEED

    @property
    def bh(self):
        return self.h + 2 * BLEED

    def root(self, left: float = 0, top: float = 0, extra_style: str = "") -> str:
        return (f'<div class="card {self.cls}" data-key="{esc(self.key)}" '
                f'style="left:{left:.3f}mm;top:{top:.3f}mm;width:{self.bw:.3f}mm;height:{self.bh:.3f}mm;{self.style}{extra_style}">'
                f'{self.html}</div>')


def trim(inner: str, w: float, h: float) -> str:
    """成品框：左上角 = 裁切线，子元素用 mm 绝对定位，出血元素用负值伸出 3mm。"""
    return f'<div class="trim" style="width:{w}mm;height:{h}mm">{inner}</div>'


def blank_card(w, h, key="blank") -> Card:
    return Card(key=key, w=w, h=h, html="", style="background:#fff;")


def single_pages(cards: list[Card]) -> tuple[str, float, float]:
    """每张一页（带出血）。返回 body html 与页面尺寸。"""
    assert cards
    w, h = cards[0].bw, cards[0].bh
    parts = []
    for c in cards:
        parts.append(f'<div class="page" style="width:{w}mm;height:{h}mm;">{c.root()}</div>')
    return "\n".join(parts), w, h


@dataclass
class Grid:
    sheet_w: float
    sheet_h: float
    cols: int
    rows: int
    w: float  # 成品宽
    h: float
    rotate: bool = False  # 预留

    @property
    def per(self):
        return self.cols * self.rows

    def origin(self):
        bw, bh = self.w + 2 * BLEED, self.h + 2 * BLEED
        gx = (self.sheet_w - self.cols * bw) / 2
        gy = (self.sheet_h - self.rows * bh) / 2
        return gx, gy, bw, bh

    def slot(self, i: int, mirror: bool = False):
        gx, gy, bw, bh = self.origin()
        r, c = divmod(i, self.cols)
        if mirror:
            c = self.cols - 1 - c
        return gx + c * bw, gy + r * bh


def crop_marks(grid: Grid, used: set[int] | None = None, mirror=False) -> str:
    """只在拼版外缘画裁切线：每条成品边线延长到纸边方向，离出血 1.5 mm 起画 5 mm。线宽 0.5pt，套版黑。"""
    gx, gy, bw, bh = grid.origin()
    W, H = grid.sheet_w, grid.sheet_h
    xs, ys = set(), set()
    for c in range(grid.cols):
        x0 = gx + c * bw + BLEED
        xs.update([round(x0, 4), round(x0 + grid.w, 4)])
    for r in range(grid.rows):
        y0 = gy + r * bh + BLEED
        ys.update([round(y0, 4), round(y0 + grid.h, 4)])
    top, bot = gy, gy + grid.rows * bh
    left, right = gx, gx + grid.cols * bw
    off, ln = 1.5, 5.0
    lines = []
    for x in sorted(xs):
        lines.append((x, top - off - ln, x, top - off))
        lines.append((x, bot + off, x, bot + off + ln))
    for y in sorted(ys):
        lines.append((left - off - ln, y, left - off, y))
        lines.append((right + off, y, right + off + ln, y))
    segs = "".join(f'<line x1="{a:.3f}" y1="{b:.3f}" x2="{c:.3f}" y2="{d:.3f}"/>' for a, b, c, d in lines)
    return (f'<svg class="marks" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
            f'<g stroke="#000" stroke-width="0.1764" fill="none">{segs}</g></svg>')


def impose(cards: list[Card], grid: Grid, slug: str, mirror: bool = False, total_sheets: int | None = None,
           side: str = "正面") -> tuple[str, int]:
    """把卡牌按网格拼到大张上。返回 (body html, 张数)。mirror=True 时左右镜像（反面）。"""
    pages = []
    n = max(1, -(-len(cards) // grid.per))
    for s in range(n):
        chunk = cards[s * grid.per:(s + 1) * grid.per]
        parts = []
        for i, c in enumerate(chunk):
            if c is None:
                continue
            x, y = grid.slot(i, mirror)
            parts.append(c.root(x, y))
        marks = crop_marks(grid, mirror=mirror)
        gx, gy, bw, bh = grid.origin()
        slug_txt = f"{slug} · {side} · 第 {s + 1}/{n} 张 · 成品 {grid.w:g}×{grid.h:g} mm · 出血 3 mm · 《交易物种起源》v1.0"
        slug_html = (f'<div class="slug" style="left:12mm;bottom:5mm;">{esc(slug_txt)}</div>')
        reg = registration_marks(grid)
        pages.append(f'<div class="page sheet" style="width:{grid.sheet_w}mm;height:{grid.sheet_h}mm;">'
                     f'{"".join(parts)}{marks}{reg}{slug_html}</div>')
    return "\n".join(pages), n


def registration_marks(grid: Grid) -> str:
    """纸边中线处的十字套准标记（正反面对位检查用），对称放置，镜像后位置不变。"""
    W, H = grid.sheet_w, grid.sheet_h
    gx, gy, bw, bh = grid.origin()
    pts = []
    if gy > 12:
        pts += [(W / 2, gy / 2)]
    if H - (gy + grid.rows * bh) > 14:
        pts += [(W / 2, H - (H - (gy + grid.rows * bh)) / 2 - 2)]
    if gx > 12:
        pts += [(gx / 2, H / 2), (W - gx / 2, H / 2)]
    out = []
    for x, y in pts:
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.6"/><line x1="{x - 2.6:.2f}" y1="{y:.2f}" x2="{x + 2.6:.2f}" y2="{y:.2f}"/>'
                   f'<line x1="{x:.2f}" y1="{y - 2.6:.2f}" x2="{x:.2f}" y2="{y + 2.6:.2f}"/>')
    return (f'<svg class="marks" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
            f'<g stroke="#000" stroke-width="0.1764" fill="none">{"".join(out)}</g></svg>')


def preview_body(cards: list[Card], cols: int = 4, gap: float = 7.0, trimmed: bool = True, captions: bool = True,
                 title: str = "") -> tuple[str, float, float]:
    """预览拼图：按成品尺寸裁掉出血（trimmed=True），灰底排成网格。返回 (body, 宽, 高) mm。"""
    items = []
    cw = max(c.w if trimmed else c.bw for c in cards)
    ch = max(c.h if trimmed else c.bh for c in cards)
    cap_h = 6.0 if captions else 0
    rows = -(-len(cards) // cols)
    W = cols * cw + (cols + 1) * gap
    head = 12.0 if title else 0
    H = head + rows * (ch + cap_h) + (rows + 1) * gap
    for i, c in enumerate(cards):
        r, k = divmod(i, cols)
        x = gap + k * (cw + gap)
        y = head + gap + r * (ch + cap_h + gap)
        w, h = (c.w, c.h) if trimmed else (c.bw, c.bh)
        inner = c.root(0 if not trimmed else 0, 0)
        cap = f'<div class="pvcap" style="position:absolute;left:{x}mm;top:{y + h + 0.6}mm;width:{w}mm">{esc(c.label or c.key)}</div>' if captions else ""
        cls = "pvwrap" if trimmed else "pvwrap untrim"
        items.append(f'<div class="{cls}" style="position:absolute;left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm">{inner}</div>{cap}')
    t = (f'<div style="position:absolute;left:{gap}mm;top:4mm;font-size:13pt;color:#fff;font-family:\'Smiley Sans Oblique\'">{esc(title)}</div>'
         if title else "")
    body = f'<div class="page" style="width:{W}mm;height:{H}mm;background:#7d7a6c;position:relative">{t}{"".join(items)}</div>'
    return body, W, H


A3 = (297.0, 420.0)
GRID_STD = Grid(A3[0], A3[1], 4, 4, 63, 88)
GRID_A6 = Grid(A3[0], A3[1], 2, 2, 105, 148)
GRID_MINI = Grid(A3[0], A3[1], 5, 5, 44, 68)
