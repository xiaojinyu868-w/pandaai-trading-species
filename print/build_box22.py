"""现成盒子 22×22×6.6 cm 的贴纸 demo：盒盖、盒底各一张展开图，外加 A3 分片印刷文件。

  python3.11 print/build_box22.py

现成盒子边缘有厚度和圆角，实测 22 cm 不一定准，所以尺寸按“宁大勿小”留余量，适合 216–224 mm 见方、62–72 mm 高的盒子。
每个盒子拆成 1 块面板 + 4 条侧条（铜版不干胶）：
- 面板 214×214：比盒面小，四周露出侧条包过来的深绿边（约 3 mm），盒子大一点小一点都不露底。
- 侧条 232×88：可见 66 mm；一边多 8 mm 包到盒面（被面板压住），另一边多 14 mm 折进盒口；
  长度按 224 mm 的盒子再加 8 mm 转角搭边，多出来的贴到相邻那面下面。文字都在中间 220×66 里，再留安全边。
A3 竖版：第 1 张 = 面板 + 1 条侧条，第 2 张 = 3 条侧条。盒盖、盒底各 2 张，共 4 张。

输出 print/out_box22/，预览在 delivery/previews/盒子22cm/。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from src import art, qrsvg  # noqa: E402
from src.c_book import DISC  # noqa: E402
from src.c_box import SERIES, _meta, box_contents  # noqa: E402
from src.core import doc, esc  # noqa: E402
from src.paths import ART, BUILD, ROOT  # noqa: E402
from src.render import Renderer, pdf_pages, pdf_size_mm  # noqa: E402
from src.tokens import PLAYERS  # noqa: E402

import build_promo as promo  # noqa: E402

OUT = Path(__file__).parent / "out_box22"
TMP = BUILD / "box22"
PREV = ROOT / "delivery" / "previews" / "盒子22cm"
for d in (OUT, TMP, PREV, BUILD / "html"):
    d.mkdir(parents=True, exist_ok=True)

SPINE, GOLD, CREAM, INK = "#0E2A27", "#C9A25E", "#F4E4BF", "#1B2A22"
B = 3.0                       # 出血
S, DEP = 220.0, 66.0          # 名义盒面边长、盒高（排版用）
FIT = 224.0                   # 侧条按这么大的盒子算长度
FACE = 214.0
WRAP, TURN, TAB = 8.0, 14.0, 8.0
STRIP_W, STRIP_H = FIT + TAB, WRAP + DEP + TURN   # 232 × 88
TOP_ART = sorted((ART / "box22-v12").glob("v12_box22_top/*/*.png"))
QR_ID = "start"

CSS = f"""
.page {{ break-after: page; position:relative; overflow:hidden; }}
.t {{ position:absolute; white-space:nowrap; }}
.k {{ font-family:"Noto Sans SC"; font-weight:900; }}
.cream {{ color:{CREAM}; }} .gold {{ color:{GOLD}; }}
.panel {{ position:absolute; overflow:hidden; }}
"""


def top_art(pick: int) -> str:
    src = TOP_ART[pick]
    im = Image.open(src).convert("RGB")
    p = TMP / f"top_{pick}.jpg"
    px = round((FACE + 2 * B) / 25.4 * 330)
    im.resize((px, px), Image.LANCZOS).save(p, quality=92, subsampling=0)
    return p.as_uri()


def spine_bg(w, h, key):
    a = art.box_spine(w, h, SPINE)
    return (f'<div class="a" style="left:0;top:0;width:{w}mm;height:{h}mm;background:{SPINE}"></div>'
            f'<img class="a" src="{a["uri"]}" style="left:0;top:0;width:{w}mm;height:{h}mm">')


def gold(name, left, top, h):
    a = art.box_gold(name)
    if not a:
        return ""
    return (f'<img class="a" src="{a["uri"]}" style="left:{left:.2f}mm;top:{top:.2f}mm;'
            f'width:{h * a["w"] / a["h"]:.2f}mm;height:{h:.2f}mm">')


def ratio(name):
    a = art.box_gold(name)
    return a["w"] / a["h"] if a else 1


def rule(x, y, w):
    return f'<div class="a" style="left:{x}mm;top:{y}mm;width:{w}mm;height:0.35mm;background:{GOLD};opacity:.8"></div>'


# ---------- 侧面内容：只管可见的 220×66（坐标原点 = 可见区左上角） ----------

def side_title():
    th = 24.0
    tw = th * ratio("title")
    ih = 17.0
    gap = 9.0
    total = ih * ratio("exchange") + gap + tw + gap + ih * ratio("arrows")
    x = (S - total) / 2
    p = [gold("exchange", x, (DEP - ih) / 2 - 3, ih)]
    x += ih * ratio("exchange") + gap
    p.append(gold("title", x, 9.0, th))
    p.append(f'<div class="t cream" style="left:{x}mm;width:{tw}mm;text-align:center;top:{9 + th + 3.4}mm;'
             f'font-size:8.6pt;font-weight:700;letter-spacing:.05em">{esc(SERIES)} · {esc(_meta())}</div>')
    p.append(f'<div class="t gold" style="left:{x}mm;width:{tw}mm;text-align:center;top:{9 + th + 8.6}mm;'
             f'font-size:7.2pt;letter-spacing:.06em">{DISC}</div>')
    x += tw + gap
    p.append(gold("arrows", x, (DEP - ih) / 2 - 3, ih))
    return "".join(p)


def side_steps():
    steps = [("01", "查看行情", "回到真实的金融史名场面，", "名字和日期涂黑，线索都在图里。"),
             ("02", "做出决定", "买入、卖出还是观望？", "每个选择都要写下理由。"),
             ("03", "揭晓物种", "看你怎么做，不看你赚多少：", "你是猎豹、大象，还是猫头鹰？")]
    cw = (S - 24) / 3
    p = [f'<div class="t k gold" style="left:0;width:{S}mm;text-align:center;top:5.2mm;font-size:12pt;'
         f'letter-spacing:.2em">一局三步</div>', rule(S / 2 - 12, 12.6, 24)]
    for i, (n, h, a, b) in enumerate(steps):
        x = 12 + i * cw
        if i:
            p.append(f'<div class="a" style="left:{x - 0.2}mm;top:19mm;width:0.3mm;height:38mm;background:{GOLD};opacity:.5"></div>')
        p.append(f'<div class="t k gold" style="left:{x + 5}mm;top:17.5mm;font-size:24pt;line-height:1">{n}</div>')
        p.append(f'<div class="t k cream" style="left:{x + 5}mm;top:30.5mm;font-size:12pt">{esc(h)}</div>')
        p.append(f'<div class="t cream" style="left:{x + 5}mm;top:39.5mm;font-size:7.6pt;line-height:1.6;opacity:.92">'
                 f'{esc(a)}<br>{esc(b)}</div>')
    return "".join(p)


def side_cast(sp):
    D = 27.0
    ids = promo.ORDER[:6]
    gap = (S - 16 - 6 * D) / 5
    p = [f'<div class="t k gold" style="left:0;width:{S}mm;text-align:center;top:4.2mm;font-size:11pt;'
         f'letter-spacing:.2em">六种交易物种 · 还有一种藏着</div>']
    for i, sid in enumerate(ids):
        x = 8 + i * (D + gap)
        img = promo.jpg(promo.sticker_src(sid), f"b22_{sid}", 40, 40, dpi=300)
        p.append(f'<img class="a" src="{img}" style="left:{x:.2f}mm;top:12.5mm;width:{D}mm;height:{D}mm;'
                 f'border-radius:50%;box-shadow:0 0 0 0.6mm {GOLD}">')
        p.append(f'<div class="t k cream" style="left:{x - 3:.2f}mm;width:{D + 6}mm;text-align:center;top:42.4mm;'
                 f'font-size:9.5pt">{esc(sp[sid]["name"])}</div>')
        p.append(f'<div class="t gold" style="left:{x - 4:.2f}mm;width:{D + 8}mm;text-align:center;top:48.6mm;'
                 f'font-size:7pt">{esc(sp[sid]["tagline"])}</div>')
    return "".join(p)


def side_qr():
    qs, qp = 34.0, 2.5
    x0 = 26.0
    y0 = (DEP - qs - 2 * qp) / 2
    p = [f'<div class="a" style="left:{x0}mm;top:{y0}mm;width:{qs + 2 * qp}mm;height:{qs + 2 * qp}mm;background:#fff;'
         f'border-radius:1.6mm;padding:{qp}mm;box-shadow:0 0 0 0.6mm {GOLD}">{qrsvg.svg(QR_ID, qs, "22cm 盒子侧面")}</div>']
    tx = x0 + qs + 2 * qp + 12
    p += [f'<div class="t k cream" style="left:{tx}mm;top:{y0 + 1}mm;font-size:17pt">扫码体验</div>',
          f'<div class="t k gold" style="left:{tx}mm;top:{y0 + 10.5}mm;font-size:13pt">发现你的交易物种</div>',
          rule(tx, y0 + 19.6, 60),
          f'<div class="t cream" style="left:{tx}mm;top:{y0 + 22.4}mm;font-size:8pt;line-height:1.65">'
          f'手机打开就能玩，先玩一场约 3 分钟<br>完整四季 15 分钟，桌游 {esc(_meta())}</div>',
          f'<div class="t gold mono" style="left:{tx}mm;top:{y0 + 34}mm;font-size:8pt">meetmind.online/ts</div>']
    return "".join(p)


def side_base(i):
    """盒底侧面：开盒才看得到，做得安静一点——一圈淡金色的走马灯字 + 中间一枚小图标。"""
    words = "我不是韭菜！ · I'M NOT A LEEK! · BUY · HOLD · SELL · "
    p = []
    for r, y in enumerate((6.0, 54.0)):
        p.append(f'<div class="t gold" style="left:{-20 - r * 30}mm;top:{y}mm;font-size:7.5pt;letter-spacing:.18em;'
                 f'opacity:.45">{esc(words * 5)}</div>')
    name = ["exchange", "chart", "arrows", "exchange"][i]
    ih = 22.0
    p.append(gold(name, S / 2 - ih * ratio(name) / 2, 14.5, ih))
    p.append(f'<div class="t k cream" style="left:0;width:{S}mm;text-align:center;top:40mm;font-size:9pt;'
             f'letter-spacing:.3em">交易物种起源</div>')
    return "".join(p)


# ---------- 面板 ----------

def face_lid(pick):
    W = FACE + 2 * B
    return f'<img class="a" src="{top_art(pick)}" style="left:0;top:0;width:{W}mm;height:{W}mm">'


def face_base():
    W = FACE + 2 * B
    o = B + 14
    pub, per = box_contents()
    lis = "".join(f"<li>{esc(t)}</li>" for t in pub)
    lis2 = "".join(f"<li>{esc(t)}</li>" for t in per)
    qs = 26.0
    p = [spine_bg(W, W, "base"),
         f'<div class="a" style="left:{B + 7}mm;top:{B + 7}mm;width:{FACE - 14}mm;height:{FACE - 14}mm;'
         f'border:0.5mm solid {GOLD};outline:0.3mm solid {GOLD};outline-offset:1.4mm;opacity:.85"></div>',
         gold("title", W / 2 - 34 * ratio("title") / 2, o + 2, 34),
         f'<div class="t cream" style="left:0;width:{W}mm;text-align:center;top:{o + 41}mm;font-size:10pt;'
         f'font-weight:700;letter-spacing:.08em">{esc(SERIES)}</div>',
         rule(W / 2 - 30, o + 50, 60),
         f'<div class="a" style="left:{o + 4}mm;top:{o + 58}mm;width:{FACE - 36}mm;font-size:8.4pt;line-height:1.55;color:{CREAM}">'
         f'<div style="font-weight:900;color:{GOLD};font-size:11pt;margin-bottom:1.5mm">盒内配件</div>'
         f'<ul style="columns:2;column-gap:8mm;padding-left:4mm">{lis}</ul>'
         f'<div style="margin:2mm 0 0.6mm;color:{GOLD}">每人一套 × {len(PLAYERS)}</div>'
         f'<ul style="columns:2;column-gap:8mm;padding-left:4mm">{lis2}</ul></div>',
         f'<div class="a" style="left:{o + 4}mm;top:{W - o - qs - 6}mm;width:{qs + 5}mm;height:{qs + 5}mm;background:#fff;'
         f'border-radius:1.4mm;padding:2.5mm">{qrsvg.svg(QR_ID, qs, "22cm 盒底")}</div>',
         f'<div class="t cream" style="left:{o + qs + 16}mm;top:{W - o - qs - 4}mm;font-size:8.4pt;line-height:1.75">'
         f'<b style="color:{GOLD};font-size:10pt">扫码开玩 · 线上同步</b><br>{esc(_meta())}<br>'
         f'数据：Panda Data 真实行情<br>PandaAI 黑客松 · 寻找你的交易人格</div>',
         f'<div class="t gold" style="left:0;width:{W}mm;text-align:center;top:{W - B - 12.5}mm;font-size:7.5pt;'
         f'letter-spacing:.08em">{DISC}</div>']
    return "".join(p)


# ---------- 侧条（含包边、折进、搭边） ----------

def strip(kind, content):
    """kind = lid：上沿 5 mm 包到盒顶，下沿 12 mm 折进盒口；base 反过来。返回 (html, w, h)，含出血。"""
    w, h = STRIP_W + 2 * B, STRIP_H + 2 * B
    vy = B + (WRAP if kind == "lid" else TURN)
    p = [spine_bg(w, h, "strip"),
         f'<div class="a" style="left:{B + (FIT - S) / 2}mm;top:{vy}mm;width:{S}mm;height:{DEP}mm">{content}</div>']
    return "".join(p), w, h


# ---------- 拼装 ----------

def lid_sides(sp):
    return [("正面 · 标题", side_title()), ("右侧 · 一局三步", side_steps()),
            ("背面 · 扫码", side_qr()), ("左侧 · 物种", side_cast(sp))]


def base_sides():
    return [(f"盒底侧面 {i + 1}", side_base(i)) for i in range(4)]


def piece(html, w, h, x, y, rot=0):
    return (f'<div class="panel" style="left:{x:.3f}mm;top:{y:.3f}mm;width:{w:.3f}mm;height:{h:.3f}mm;'
            f'transform:rotate({rot}deg);transform-origin:center">{html}</div>')


def corner_marks(x, y, w, h, off=2.0, ln=5.0):
    L = []
    for xx in (x, x + w):
        L += [(xx, y - B - off - ln, xx, y - B - off), (xx, y + h + B + off, xx, y + h + B + off + ln)]
    for yy in (y, y + h):
        L += [(x - B - off - ln, yy, x - B - off, yy), (x + w + B + off, yy, x + w + B + off + ln, yy)]
    return "".join(f'<line x1="{a:.3f}" y1="{b:.3f}" x2="{c:.3f}" y2="{d:.3f}"/>' for a, b, c, d in L)


def fold_ticks(x, y, kind):
    """侧条的折线只在出血外画短虚线，成品里不印线。"""
    ys = [WRAP, WRAP + DEP] if kind == "lid" else [TURN, TURN + DEP]
    L = []
    for f in ys:
        for x0, x1 in ((x - B - 9, x - B - 2), (x + STRIP_W + B + 2, x + STRIP_W + B + 9)):
            L.append(f'<line x1="{x0}" y1="{y + f:.3f}" x2="{x1}" y2="{y + f:.3f}" stroke-dasharray="1 0.8"/>')
    return "".join(L)


def a3_sheets(kind, face_html, sides):
    SW, SH = 297.0, 420.0
    fw = FACE + 2 * B
    sw, sh = STRIP_W + 2 * B, STRIP_H + 2 * B
    cn = "盒盖" if kind == "lid" else "盒底"
    pages = []
    lay1 = [("face", face_html, None)] + [("strip", sides[0][1], sides[0][0])]
    lay2 = [("strip", c, n) for n, c in sides[1:]]
    for k, lay in enumerate((lay1, lay2)):
        hs = [fw if t == "face" else sh for t, _, _ in lay]
        gap = 16.0
        y = (SH - sum(hs) - gap * (len(hs) - 1)) / 2
        parts, marks, ticks, labels = [], [], [], []
        for (t, c, n), hh in zip(lay, hs):
            if t == "face":
                x = (SW - fw) / 2
                parts.append(piece(c, fw, fw, x, y))
                marks.append(corner_marks(x + B, y + B, FACE, FACE))
                labels.append(f"{cn}面板 {FACE:.0f}×{FACE:.0f}")
            else:
                x = (SW - sw) / 2
                html, _, _ = strip(kind, c)
                parts.append(piece(html, sw, sh, x, y))
                marks.append(corner_marks(x + B, y + B, STRIP_W, STRIP_H))
                ticks.append(fold_ticks(x + B, y + B, kind))
                labels.append(f"侧条「{n}」{STRIP_W:.0f}×{STRIP_H:.0f}")
            y += hh + gap
        slug = (f"22cm 盒子 · {cn} 第 {k + 1}/2 张 · " + "、".join(labels) +
                " · 出血 3 mm · 实线=裁切，虚线=折线 · 铜版不干胶 覆哑膜")
        pages.append(f'<div class="page" style="width:{SW}mm;height:{SH}mm;background:#fff">{"".join(parts)}'
                     f'<svg class="a" style="left:0;top:0" width="{SW}mm" height="{SH}mm" viewBox="0 0 {SW} {SH}">'
                     f'<g stroke="#000" stroke-width="0.1764" fill="none">{"".join(marks)}{"".join(ticks)}</g></svg>'
                     f'<div class="t" style="left:8mm;top:4mm;font-size:7pt;color:#000">{esc(slug)}</div></div>')
    return "".join(pages)


def net(kind, face_html, sides, guides=True):
    """十字展开图：中间面板，四边侧面（可见 66 mm + 折进 12 mm）。只用来看效果和交大幅面整张印。"""
    arm = DEP + 12.0
    N = S + 2 * arm
    pad = 14.0
    W = N + 2 * pad
    c0 = pad + arm  # 面板左上角
    p = [f'<div class="a" style="left:0;top:0;width:{W}mm;height:{W}mm;background:#ECE7DC"></div>']
    fw = FACE + 2 * B
    inset = (S - FACE) / 2
    p.append(f'<div class="panel" style="left:{c0}mm;top:{c0}mm;width:{S}mm;height:{S}mm;background:{SPINE}">'
             + f'<div class="panel" style="left:{inset}mm;top:{inset}mm;width:{FACE}mm;height:{FACE}mm">'
             + piece(face_html, fw, fw, -B, -B) + '</div></div>')
    # 侧面：盒盖的侧面上沿挨着顶面；盒底的侧面下沿挨着底面
    rots = {"lid": [0, 180, 90, -90], "base": [180, 0, -90, 90]}[kind]
    order = [0, 2, 3, 1]  # 下=正面，上=背面，左=左侧，右=右侧
    sw, sh = S, arm
    for slot, rot in zip(range(4), rots):
        _, content = sides[order[slot]]
        vy = 0 if kind == "lid" else 12.0
        inner = (f'<div class="a" style="left:0;top:0;width:{sw}mm;height:{sh}mm">{spine_bg(sw, sh, "n")}</div>'
                 f'<div class="a" style="left:0;top:{vy}mm;width:{S}mm;height:{DEP}mm">{content}</div>')
        if slot == 0:
            x, y = c0, c0 + S
        elif slot == 1:
            x, y = c0, c0 - sh
        elif slot == 2:
            x, y = c0 - sh / 2 - sw / 2, c0 + S / 2 - sh / 2
        else:
            x, y = c0 + S - sw / 2 + sh / 2, c0 + S / 2 - sh / 2
        p.append(piece(inner, sw, sh, x, y, rot))
    if guides:
        g = []
        ln = lambda a, b, c, d, dash="": g.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" {dash}/>')
        dash = 'stroke-dasharray="2 1.4"'
        for a, b, c, d in ((c0, c0, c0 + S, c0), (c0, c0 + S, c0 + S, c0 + S), (c0, c0, c0, c0 + S), (c0 + S, c0, c0 + S, c0 + S)):
            ln(a, b, c, d, dash)
        k = DEP  # 两种盒子都是：挨着盒面的 66 mm 可见，外侧 12 mm 折进盒口
        ln(c0, c0 + S + k, c0 + S, c0 + S + k, dash)
        ln(c0, c0 - k, c0 + S, c0 - k, dash)
        ln(c0 - k, c0, c0 - k, c0 + S, dash)
        ln(c0 + S + k, c0, c0 + S + k, c0 + S, dash)
        outline = (f"M{c0},{c0 - arm} H{c0 + S} V{c0} H{c0 + S + arm} V{c0 + S} H{c0 + S} V{c0 + S + arm} H{c0} "
                   f"V{c0 + S} H{c0 - arm} V{c0} H{c0} Z")
        g.append(f'<path d="{outline}" stroke="#E4007F"/>')
        lab = []
        cn = "盒盖" if kind == "lid" else "盒底"
        lab.append(f'<div class="t" style="left:{pad}mm;top:4mm;font-size:9pt;color:#333;font-weight:700">'
                   f'{cn}展开图 · 按 220×220×66 mm 示意 · 洋红实线 = 外轮廓，虚线 = 折线 · 实际印刷用 A3 分片（留了余量）</div>')
        p.append(f'<svg class="a" style="left:0;top:0" width="{W}mm" height="{W}mm" viewBox="0 0 {W} {W}">'
                 f'<g stroke="#333" stroke-width="0.35" fill="none">{"".join(g)}</g></svg>' + "".join(lab))
    return f'<div class="page" style="width:{W}mm;height:{W}mm">{"".join(p)}</div>', W


def main(pick=0):
    sp = promo.species()
    R = Renderer()
    outs = []

    def emit(name, body, w, h):
        p = OUT / name
        R.pdf(doc(body, w, h, extra_css=CSS, title=name), f"box22_{p.stem}", p, w, h)
        outs.append(p)

    lid_face, base_face = face_lid(pick), face_base()
    ls, bs = lid_sides(sp), base_sides()
    emit("B1_盒盖_A3_2张_面板加4条侧条.pdf", a3_sheets("lid", lid_face, ls), 297, 420)
    emit("B2_盒底_A3_2张_面板加4条侧条.pdf", a3_sheets("base", base_face, bs), 297, 420)
    for kind, face, sides, cn in (("lid", lid_face, ls, "盒盖"), ("base", base_face, bs, "盒底")):
        body, W = net(kind, face, sides)
        emit(f"B0_{cn}展开图_整张_{W:.0f}x{W:.0f}.pdf", body, W, W)
        R.png(doc(body, W, W, extra_css=CSS), f"box22_prev_{kind}", PREV / f"{cn}展开图.png", dpi=60)
        clean, _ = net(kind, face, sides, guides=False)
        R.png(doc(clean, W, W, extra_css=CSS), f"box22_tex_{kind}", TMP / f"net_{kind}.png", dpi=150)
    # 效果图贴图（delivery/box22_mockup.py 用）：顶面 218 方、四个侧面的可见 220×66
    mock = Path("/tmp/box22mock")
    mock.mkdir(exist_ok=True)
    fw = FACE + 2 * B
    R.png(doc(f'<div class="page" style="width:{FACE}mm;height:{FACE}mm">{piece(lid_face, fw, fw, -B, -B)}</div>',
              FACE, FACE, extra_css=CSS), "box22_mock_top", mock / "tex_top.png", dpi=200, selector=".page")
    for (n, c), key in zip(ls, ("front", "right", "back", "left")):
        R.png(doc(f'<div class="page" style="width:{S}mm;height:{DEP}mm">{spine_bg(S, DEP, "m")}'
                  f'<div class="a" style="left:0;top:0;width:{S}mm;height:{DEP}mm">{c}</div></div>', S, DEP, extra_css=CSS),
              f"box22_mock_{key}", mock / f"tex_{key}.png", dpi=200, selector=".page")
    R.close()
    for p in outs:
        print(f"{p.name}\t{pdf_pages(p)} 页\t{pdf_size_mm(p)}")
    print("小于 7pt：", [i for i in R.issues if i["type"] == "small"][:5])
    print("溢出：", [i for i in R.issues if i["type"] == "overflow"][:5])


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
