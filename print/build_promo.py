"""游园会宣传物料：引流卡、物种贴纸、口号贴纸、展位海报。画风跟盒标一致（art/build_promo_v10.py 出图）。

  python3.11 print/build_promo.py

输出到 print/out_promo/（不放 print/out/，全量构建会清空那里）。二维码用 qr.json 的 start（开局页）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from src import qrsvg  # noqa: E402
from src.c_book import DISC  # noqa: E402
from src.core import BLEED, crop_marks, doc, esc, Grid  # noqa: E402
from src.paths import ART, BUILD, CONTENT, ROOT  # noqa: E402
from src.render import Renderer, pdf_pages, pdf_size_mm  # noqa: E402

OUT = Path(__file__).parent / "out_promo"
TMP = BUILD / "promo"
PREV = ROOT / "delivery" / "previews" / "游园会"
for d in (OUT, TMP, PREV, BUILD / "html"):
    d.mkdir(parents=True, exist_ok=True)

SPINE, GOLD, CREAM, PAPER = "#0E2A27", "#C9A25E", "#F4E4BF", "#F4E4BF"
QR_ID = "start"
POSTER_ART = ART / "promo-v10-poster/v10_poster/img_50698/ai_generate_50698_1.png"
STICKER_DIR = ART / "promo-v10b"
SLOGAN_ART = STICKER_DIR / "v10_st_slogan/img_50706/ai_generate_50706_1.png"
ORDER = ["cheetah", "elephant", "owl", "meerkat", "fox", "chameleon", "beaver"]

CARD_W, CARD_H = 90.0, 128.0      # 引流卡：A3 拼 3×3 = 9 张
POST_W, POST_H = 420.0, 594.0     # A2
ST_D, ST_BLEED, ST_PITCH = 50.0, 2.0, 56.0  # 圆贴 Ø50，出血 2 mm，A3 上 5×7 = 35 枚
LEDGE = 0.868                     # 主视觉里深墨绿石台的上沿（占图高）


def species():
    d = json.loads((CONTENT / "decks.json").read_text(encoding="utf-8"))
    return {s["id"]: s for s in d["species"]}


BUSTS = ART / "promo-v11"
BUST = {"cheetah": ("v11_cheetah", 1), "elephant": ("v11_elephant", 2), "owl": ("v11_owl", 1),
        "meerkat": ("v11_meerkat2", 2), "fox": ("v11_fox", 2), "chameleon": ("v11_chameleon", 2),
        "beaver": ("v11_beaver", 1)}
# 每个物种一个底色，和角色本身的主色拉开；海狸是隐藏物种，用浅底
ST_BG = {"cheetah": "#41627E", "elephant": "#E2A93B", "owl": "#1F5A57", "meerkat": "#D4432A",
         "fox": "#EFDDB0", "chameleon": "#C8663A", "beaver": "#86A9A8"}
BAND = 0.66  # 名字带上沿，占贴纸含出血直径的比例


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def sticker_src(sid: str) -> Path:
    """合成物种贴纸的画（不含名字带）：纯色底 + 纸纹暗角 + 透明底半身像，奶油色描边加投影。方图，Ø54 的外接正方形。"""
    import numpy as np
    from PIL import ImageFilter
    out = TMP / f"st_{sid}_comp.png"
    folder, n = BUST[sid]
    src = next(BUSTS.glob(f"{folder}/*/*_{n}.png"))
    if out.exists() and out.stat().st_mtime > src.stat().st_mtime and out.stat().st_mtime > Path(__file__).stat().st_mtime:
        return out
    S = 1200  # 54 mm ≈ 565 dpi
    px = S / (ST_D + 2 * ST_BLEED)
    base = np.zeros((S, S, 3), float) + _rgb(ST_BG[sid])
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - S / 2, yy - S / 2) / (S / 2)
    light = sum(_rgb(ST_BG[sid])) > 500
    base *= (1 - 0.16 * np.clip(r - 0.35, 0, 1)[..., None]) if not light else (1 - 0.08 * np.clip(r - 0.35, 0, 1)[..., None])
    rng = np.random.default_rng(7)
    base += rng.normal(0, 5, (S, S, 1))
    canvas = Image.fromarray(np.clip(base, 0, 255).astype("uint8")).convert("RGBA")

    fig = Image.open(src).convert("RGBA")
    fig = fig.crop(fig.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox())
    top, bottom = 0.075 * S, BAND * S + 0.10 * S  # 身体下端藏在名字带后面
    k = min((bottom - top) / fig.height, 0.86 * S / fig.width)
    fig = fig.resize((round(fig.width * k), round(fig.height * k)), Image.LANCZOS)
    x, y = (S - fig.width) // 2, round(bottom - fig.height)
    a = fig.getchannel("A")
    pad = round(1.1 * px)
    big = Image.new("L", (fig.width + 2 * pad, fig.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    ring = big.filter(ImageFilter.MaxFilter(9))
    for _ in range(max(1, pad // 4) - 1):
        ring = ring.filter(ImageFilter.MaxFilter(9))
    ring = ring.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(0.8))
    shadow = Image.new("RGBA", big.size, (10, 20, 18, 0))
    shadow.putalpha(ring.point(lambda v: v * 0.45).filter(ImageFilter.GaussianBlur(px * 0.5)))
    canvas.alpha_composite(shadow, (x - pad + round(0.5 * px), y - pad + round(0.9 * px)))
    outline = Image.new("RGBA", big.size, _rgb(CREAM) + (0,))
    outline.putalpha(ring)
    canvas.alpha_composite(outline, (x - pad, y - pad))
    canvas.alpha_composite(fig, (x, y))
    canvas.convert("RGB").save(out)
    return out


def jpg(src: Path, name: str, w_mm: float, h_mm: float, dpi: int = 320, crop=None) -> str:
    """按成品（含出血）尺寸裁成同比例、缩到 dpi，存 JPEG，返回 file:// 路径。"""
    im = Image.open(src).convert("RGB")
    if crop:
        im = im.crop(crop)
    W, H = im.size
    r = w_mm / h_mm
    if W / H > r:
        nw = int(H * r)
        im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = int(W / r)
        im = im.crop((0, 0, W, nh))  # 竖向多出来的从底部（石台）裁，标题留着
    px = (round(w_mm / 25.4 * dpi), round(h_mm / 25.4 * dpi))
    if px[0] < im.size[0]:
        im = im.resize(px, Image.LANCZOS)
    p = TMP / f"{name}.jpg"
    im.save(p, quality=92, subsampling=0, dpi=(dpi, dpi))
    return p.as_uri()


def qr_tile(left, top, size, pad, radius=1.5):
    return (f'<div class="a" style="left:{left}mm;top:{top}mm;width:{size + 2 * pad}mm;height:{size + 2 * pad}mm;'
            f'background:#fff;border-radius:{radius}mm;padding:{pad}mm">{qrsvg.svg(QR_ID, size, "游园会")}</div>')


def page(inner, w, h, bg=SPINE):
    """单张成品页：页面 = 成品 + 出血。"""
    return (f'<div class="page" style="position:relative;width:{w + 2 * BLEED}mm;height:{h + 2 * BLEED}mm;'
            f'overflow:hidden;background:{bg}"><div class="trim">{inner}</div></div>')


CSS = f"""
.page {{ break-after: page; }}
.t {{ position:absolute; white-space:nowrap; }}
.k {{ font-family:"Noto Sans SC"; font-weight:900; }}
.cream {{ color:{CREAM}; }} .gold {{ color:{GOLD}; }} .ink {{ color:{SPINE}; }}
"""


# ---------- 引流卡 ----------

def card_front():
    W, H = CARD_W, CARD_H
    bw, bh = W + 2 * BLEED, H + 2 * BLEED
    src = jpg(POSTER_ART, "card_front", bw, bh)
    ledge = bh * LEDGE - BLEED + 0.8  # 石台在成品坐标里的上沿
    mid = (ledge + H) / 2
    return page(
        f'<img class="a" src="{src}" style="left:-3mm;top:-3mm;width:{bw}mm;height:{bh}mm">'
        f'<div class="t k cream" style="left:0;width:{W}mm;text-align:center;top:{mid - 5.0:.2f}mm;font-size:10.5pt;'
        f'letter-spacing:0.04em">翻到背面 · 扫码测你的交易物种</div>'
        f'<div class="t gold" style="left:0;width:{W}mm;text-align:center;top:{mid + 0.9:.2f}mm;font-size:7pt;'
        f'font-weight:500;letter-spacing:0.06em">交易物种起源 · 金融史名场面桌游</div>', W, H)


def card_back(sp):
    W, H = CARD_W, CARD_H
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{PAPER}"></div>',
         f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:23mm;background:{SPINE}"></div>',
         f'<div class="t k cream" style="left:0;width:{W}mm;text-align:center;top:4.2mm;font-size:16pt">你是哪种交易物种？</div>',
         f'<div class="t gold" style="left:0;width:{W}mm;text-align:center;top:13.6mm;font-size:7pt;font-weight:500;'
         f'letter-spacing:0.05em">在真实的金融史名场面里做决定，看看你的打法</div>']
    D, top0, rowh = 19.5, 25.5, 31.5
    colw = (W - 8) / 3
    for i, sid in enumerate(ORDER[:6]):
        s = sp[sid]
        r, c = divmod(i, 3)
        cx = 4 + colw * c + colw / 2
        y = top0 + r * rowh
        img = jpg(sticker_src(sid), f"mini_{sid}", 30, 30, dpi=300)
        p.append(f'<img class="a" src="{img}" style="left:{cx - D / 2:.2f}mm;top:{y:.2f}mm;width:{D}mm;height:{D}mm;'
                 f'border-radius:50%;box-shadow:0 0 0 0.5mm {SPINE}">')
        p.append(f'<div class="t k ink" style="left:{cx - colw / 2:.2f}mm;width:{colw:.2f}mm;text-align:center;'
                 f'top:{y + D + 1.4:.2f}mm;font-size:9pt">{esc(s["name"])}</div>')
        p.append(f'<div class="t ink" style="left:{cx - colw / 2:.2f}mm;width:{colw:.2f}mm;text-align:center;'
                 f'top:{y + D + 5.6:.2f}mm;font-size:7pt">{esc(s["tagline"])}</div>')
    y = top0 + 2 * rowh + 0.6
    p.append(f'<div class="t ink" style="left:0;width:{W}mm;text-align:center;top:{y:.2f}mm;font-size:7pt;'
             f'font-weight:700">还有一种隐藏物种，等你解锁</div>')
    qs, qp = 22.0, 2.0
    qtop = H - 6.5 - qs - 2 * qp
    p.append(f'<div class="a" style="left:4mm;top:{qtop - 1.2:.2f}mm;width:{W - 8}mm;height:{qs + 2 * qp + 2.4:.2f}mm;'
             f'background:{SPINE};border-radius:2mm"></div>')
    p.append(qr_tile(5.2, qtop, qs, qp))
    tx = 5.2 + qs + 2 * qp + 3.2
    lines = [("扫码开玩", "k cream", "11pt", 1.2), ("先玩一场，约 3 分钟", "cream", "8pt", 7.4),
             ("测完凭结果页", "gold", "8pt", 12.4), ("到展位领物种贴纸", "gold", "8pt", 16.6),
             ("meetmind.online/ts", "cream mono", "7pt", 21.4)]
    for t, cls, fs, dy in lines:
        p.append(f'<div class="t {cls}" style="left:{tx:.2f}mm;top:{qtop + dy:.2f}mm;font-size:{fs};'
                 f'font-weight:{700 if "k" in cls.split() else 500}">{esc(t)}</div>')
    p.append(f'<div class="t" style="left:0;width:{W}mm;text-align:center;top:{H - 3.9:.2f}mm;font-size:7pt;'
             f'color:#4A4A33">{DISC}</div>')
    return page("".join(p), W, H, bg=PAPER)


# ---------- 贴纸 ----------

def sticker_art(sid: str | None) -> str:
    """圆贴的画：方图裁内切圆，出血 2 mm（画 Ø54）。口号章的圆圈在画面里约占 94%，裁 Ø92%。"""
    if sid is None:
        im = Image.open(SLOGAN_ART).convert("RGB")
        W = im.size[0]
        bg = Image.new("RGB", (int(W * 1.06), int(W * 1.06)), im.getpixel((W // 2, 6)))
        bg.paste(im, ((bg.size[0] - W) // 2, (bg.size[1] - W) // 2))
        bg.save(TMP / "st_slogan_pad.png")
        return jpg(TMP / "st_slogan_pad.png", "st_slogan", 54, 54, dpi=500)
    return jpg(sticker_src(sid), f"st_{sid}", 54, 54, dpi=560)


def sticker_html(sid, sp, cx, cy):
    """圆心 (cx, cy)，画到 Ø54（含出血），切 Ø50。物种贴纸在底部深墨绿带上排名字和口号。"""
    R = ST_D / 2 + ST_BLEED
    D = 2 * R
    h = [f'<img class="a" src="{sticker_art(sid)}" style="left:0;top:0;width:{D}mm;height:{D}mm">']
    if sid:
        s = sp[sid]
        name = s["name"] + ("（隐藏）" if s.get("hidden") else "")
        band = D * BAND  # 再往下圆弧太窄，7pt 口号排不下
        h.append(f'<div class="a" style="left:0;top:{band:.3f}mm;width:{D}mm;height:{D - band:.3f}mm;background:{SPINE};'
                 f'border-top:0.5mm solid {GOLD}"></div>')
        h.append(f'<div class="t k gold" style="left:0;width:{D}mm;text-align:center;top:{band + 1.0:.3f}mm;'
                 f'font-size:10pt;letter-spacing:0.08em">{esc(name)}</div>')
        h.append(f'<div class="t cream" style="left:0;width:{D}mm;text-align:center;top:{band + 5.7:.3f}mm;'
                 f'font-size:7pt;font-weight:500">{esc(s["tagline"])}</div>')
    ins = ST_BLEED + 1.4
    h.append(f'<div class="a" style="left:{ins}mm;top:{ins}mm;width:{D - 2 * ins:.3f}mm;height:{D - 2 * ins:.3f}mm;'
             f'border-radius:50%;border:0.45mm solid {CREAM};opacity:0.85"></div>')
    return (f'<div class="a" style="left:{cx - R:.3f}mm;top:{cy - R:.3f}mm;width:{D}mm;height:{D}mm;'
            f'border-radius:50%;overflow:hidden">{"".join(h)}</div>')


def sticker_sheet(sid, sp):
    """A3 竖，5×7 = 35 枚同一款；第 2 页是半切线（Ø50 圆）。"""
    SW, SH, cols, rows = 297.0, 420.0, 5, 7
    gx = (SW - cols * ST_PITCH) / 2 + ST_PITCH / 2
    gy = (SH - rows * ST_PITCH) / 2 + ST_PITCH / 2
    centers = [(gx + c * ST_PITCH, gy + r * ST_PITCH) for r in range(rows) for c in range(cols)]
    art_ = "".join(sticker_html(sid, sp, x, y) for x, y in centers)
    label = (sp[sid]["name"] if sid else "我不是韭菜")
    slug = (f'<div class="t" style="left:10mm;top:4mm;font-size:7pt;color:#000">游园会贴纸 · {esc(label)} · Ø50 圆形 · '
            f'A3 每张 35 枚 · 第 1 页印刷，第 2 页半切线</div>')
    cut = "".join(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{ST_D / 2}"/>' for x, y in centers)
    p1 = f'<div class="page" style="position:relative;width:{SW}mm;height:{SH}mm;background:#fff">{art_}{slug}</div>'
    p2 = (f'<div class="page" style="position:relative;width:{SW}mm;height:{SH}mm;background:#fff">{slug}'
          f'<svg class="a" style="left:0;top:0" width="{SW}mm" height="{SH}mm" viewBox="0 0 {SW} {SH}">'
          f'<g fill="none" stroke="#E4007F" stroke-width="0.25">{cut}</g></svg></div>')
    return p1 + p2, SW, SH


def sticker_single(sid, sp):
    s = ST_D + 2 * ST_BLEED
    c = s / 2
    return (f'<div class="page" style="position:relative;width:{s}mm;height:{s}mm;background:#fff">'
            f'{sticker_html(sid, sp, c, c)}</div>'), s, s


# ---------- 海报 ----------

def poster():
    W, H = POST_W, POST_H
    bw, bh = W + 2 * BLEED, H + 2 * BLEED
    src = jpg(POSTER_ART, "poster", bw, bh, dpi=200)
    ledge = bh * LEDGE - BLEED + 2
    qs, qp = 56.0, 4.0
    qtop = ledge + (H - ledge - qs - 2 * qp) / 2
    qleft = W - 18 - qs - 2 * qp
    x = 18
    band = H - ledge
    return page(
        f'<img class="a" src="{src}" style="left:-3mm;top:-3mm;width:{bw}mm;height:{bh}mm">'
        f'<div class="t k cream" style="left:{x}mm;top:{ledge + band * 0.08:.1f}mm;font-size:54pt;letter-spacing:0.03em">'
        f'扫码，测测你是哪种交易物种</div>'
        f'<div class="t gold" style="left:{x}mm;top:{ledge + band * 0.44:.1f}mm;font-size:22pt;font-weight:700">'
        f'在真实的金融史名场面里做决定 · 先玩一场，约 3 分钟</div>'
        f'<div class="t cream" style="left:{x}mm;top:{ledge + band * 0.64:.1f}mm;font-size:22pt;font-weight:500">'
        f'测完凭结果页，到展位领你的物种贴纸</div>'
        f'<div class="t gold" style="left:{x}mm;top:{ledge + band * 0.85:.1f}mm;font-size:13pt;font-weight:500">'
        f'交易物种起源 · 金融史名场面桌游　|　{DISC}</div>'
        + qr_tile(qleft, qtop, qs, qp, radius=3), W, H)


# ---------- 拼版 / 输出 ----------

def impose_cards(html_one: str, cols=3, rows=3, slug=""):
    SW, SH = 297.0, 420.0
    g = Grid(SW, SH, cols, rows, CARD_W, CARD_H)
    gx, gy, bw, bh = g.origin()
    cells = []
    for i in range(cols * rows):
        x, y = g.slot(i)
        cells.append(f'<div class="a" style="left:{x:.3f}mm;top:{y:.3f}mm;width:{bw}mm;height:{bh}mm;overflow:hidden">'
                     f'{html_one}</div>')
    s = f'<div class="t" style="left:10mm;top:4mm;font-size:7pt;color:#000">{esc(slug)}</div>'
    return (f'<div class="page" style="position:relative;width:{SW}mm;height:{SH}mm;background:#fff">'
            f'{"".join(cells)}{crop_marks(g)}{s}</div>'), SW, SH


def strip_page(h: str) -> str:
    """把 page() 的外层 .page 去掉，留里面的内容给拼版格子用。"""
    a = h.index(">") + 1
    return f'<div style="position:relative;width:100%;height:100%;background:inherit">' + h[a:-len("</div>")] + "</div>"


def main():
    sp = species()
    R = Renderer()
    outs = []

    def emit(name, body, w, h):
        p = OUT / name
        R.pdf(doc(body, w, h, extra_css=CSS, title=name), f"promo_{p.stem}", p, w, h)
        outs.append(p)

    f, b = card_front(), card_back(sp)
    emit("P1_引流卡_90x128_正反2页.pdf", f + b, CARD_W + 6, CARD_H + 6)
    fb, _, _ = impose_cards(strip_page(f), slug="引流卡 正面 · 90×128 · A3 每张 9 张")
    bb, _, _ = impose_cards(strip_page(b), slug="引流卡 反面 · 90×128 · A3 每张 9 张（9 张相同，不用镜像）")
    emit("P1b_引流卡_拼版_A3_正反2页.pdf", fb + bb, 297, 420)

    for sid in ORDER + [None]:
        tag = sp[sid]["name"] if sid else "我不是韭菜"
        body, w, h = sticker_sheet(sid, sp)
        emit(f"P2_贴纸_{tag}_A3_35枚_印刷加半切线2页.pdf", body, w, h)
    singles = [sticker_single(sid, sp)[0] for sid in ORDER + [None]]
    emit("P2b_贴纸_单枚_Ø50_8款8页.pdf", "".join(singles), ST_D + 2 * ST_BLEED, ST_D + 2 * ST_BLEED)

    emit("P3_展位海报_A2_420x594_1张.pdf", poster(), POST_W + 6, POST_H + 6)

    # 预览图
    R.png(doc(f + b, CARD_W + 6, CARD_H + 6, extra_css=CSS + ".page{display:inline-block;margin:6mm}"),
          "promo_prev_card", PREV / "引流卡_正反.png", dpi=200)
    R.png(doc("".join(singles), 54, 54, extra_css=CSS + ".page{display:inline-block;margin:3mm;background:transparent!important}"
              "body{width:260mm}"), "promo_prev_st", PREV / "贴纸_8款.png", dpi=200)
    R.png(doc(poster(), POST_W + 6, POST_H + 6, extra_css=CSS), "promo_prev_poster", PREV / "展位海报.png", dpi=40)

    import markdown
    note = OUT / "00_游园会物料印刷说明.md"
    if note.exists():
        body = markdown.markdown(note.read_text(encoding="utf-8"), extensions=["tables"])
        css = ("body{font-size:9.5pt;line-height:1.6;padding:14mm 15mm;color:#222}h1{font-size:16pt}h2{font-size:12pt;"
               "margin:5mm 0 2mm}table{border-collapse:collapse;width:100%;margin:2mm 0}td,th{border:0.3pt solid #999;"
               "padding:1.2mm 1.6mm;font-size:8.5pt;vertical-align:top}th{background:#eee}blockquote{border-left:1mm "
               "solid #C9A25E;padding-left:3mm;margin:2mm 0;color:#333}code{font-size:8pt}li{margin:0.6mm 0}")
        pdf = OUT / "00_游园会物料印刷说明.pdf"
        hp = BUILD / "html" / "promo_note.html"
        hp.write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><link rel="stylesheet" '
                      f'href="{(Path(__file__).parent / "templates/base.css").as_uri()}"><style>{css}</style></head>'
                      f'<body>{body}</body></html>', encoding="utf-8")
        ctx, pg = R._open(hp)
        pg.pdf(path=str(pdf), format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        ctx.close()
        outs.insert(0, pdf)
    R.close()

    for p in outs:
        print(f"{p.name}\t{pdf_pages(p)} 页\t{pdf_size_mm(p)}")
    small = [i for i in R.issues if i["type"] == "small"]
    over = [i for i in R.issues if i["type"] == "overflow"]
    print("小于 7pt：", small[:5])
    print("溢出：", over[:5])
    print("二维码：", qrsvg.url(QR_ID))


if __name__ == "__main__":
    main()
