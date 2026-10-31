"""易拉宝 80×200 cm（四边各 3 mm 出血，成品文件 806×2006 mm）。

  python3.11 promo/banner/build_banner.py                                   # 出 PDF、100 dpi JPG 和预览图
  python3.11 promo/banner/build_banner.py --art <png> --preview <out.png>   # 只出预览，用来比较候选画面

画面是 GPT Image 2.5 出的整张信息图（art/build_banner_v12.py），这里只做三件事：
放大铺满 80 cm 宽，下面接一条和画面底部色带同色的底边（底座会挡住最下面约 10 cm）；
在画面留的白方块里贴二维码；在顶部色带贴赛道名，在底边贴网址和合规声明。版面按 1px = 1mm 写，出 PDF 时换成 mm。
"""
import argparse
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
ASSETS = HERE / "assets"
OUT = HERE / "out"
URL = "https://meetmind.online/ts/"
ART = ROOT / "art/vmc-output/banner-v12/v12_banner_flat/img_50711/ai_generate_50711_2.png"
PW, PH, BLEED = 806, 2006, 3
PX_MM = 4
DPI = 100
BASE = 100

sys.path.insert(0, str(ROOT / "print"))
from fontTools import subset  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from src.fontbuild import SOURCES, _otf_to_ttf  # noqa: E402


def build_fonts(page: str):
    """Noto Sans SC 是 CFF 轮廓，Chromium 会嵌成 Type 3；按版面用到的字子集化并转成 TrueType。"""
    body = re.sub(r"<style>.*?</style>|<[^>]+>", "", page, flags=re.S)
    text = "".join(sorted(set(body) | set(map(chr, range(0x20, 0x7F)))))
    d = ASSETS / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    for w in (500, 700):
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.notdef_outline = True
        opts.hinting = False
        opts.drop_tables += ["VORG", "BASE", "vhea", "vmtx", "DSIG"]
        f = TTFont(SOURCES[f"NotoSansSC-{w}"])
        s = subset.Subsetter(opts)
        s.populate(text=text)
        s.subset(f)
        _otf_to_ttf(f)
        f.save(d / f"noto-{w}.ttf")


def measure(art: np.ndarray) -> dict:
    """量出画面自带的上下色带和留给二维码的白方块（原图像素）。"""
    h, w, _ = art.shape
    inner = slice(w * 6 // 100, w * 94 // 100)

    def color(rows):
        return np.median(art[rows, inner].reshape(-1, 3), axis=0)

    def share(c):
        return (np.abs(art[:, inner] - c).sum(axis=2) < 45).mean(axis=1)

    top_c, bottom_c = color(slice(3, 20)), color(slice(h - 20, h - 3))
    st, sb = share(top_c), share(bottom_c)
    top = next(y for y in range(h) if st[y] < 0.9)
    bottom = next(y for y in range(h - 1, 0, -1) if sb[y] < 0.9) + 1
    white = (art.min(axis=2) > 240).astype(np.uint8)
    white[: h // 2] = 0
    _, _, stats, _ = cv2.connectedComponentsWithStats(white, 8)
    x, y, bw, bh, _ = max((s for s in stats[1:] if 0.75 < s[2] / s[3] < 1.33), key=lambda s: s[4])
    return {"top": top, "bottom": bottom, "color": bottom_c, "blank": (x, y, bw, bh)}


def background(art: Image.Image, m: dict) -> float:
    """放大画面、接底边，存成 4 px/mm 的底图；返回原图 1 像素对应多少 mm。"""
    w, h = PW * PX_MM, PH * PX_MM
    k = w / art.width
    big = art.resize((w, round(art.height * k)), Image.LANCZOS)
    big = big.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
    fill = Image.new("RGB", (w, h), tuple(int(c) for c in m["color"]))
    canvas = fill.copy()
    canvas.paste(big, (0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((0, round((m["bottom"] + 6) * k), w, h), fill=255)
    canvas = Image.composite(fill, canvas, mask.filter(ImageFilter.GaussianBlur(4)))
    canvas.save(ASSETS / "bg.jpg", quality=92, dpi=(PX_MM * 25.4,) * 2)
    return PW / art.width


def html(unit: str, m: dict, k: float) -> str:
    a = ASSETS.as_uri()
    x, y, bw, bh = m["blank"]
    qs = min(bw, bh) * k - 4
    qx, qy = (x + bw / 2) * k - qs / 2, (y + bh / 2) * k - qs / 2
    foot = m["bottom"] * k
    band = m["top"] * k - BLEED
    top_size = min(24, round(band * 0.45))
    css = f"""
  @page {{ size: {PW}px {PH}px; margin: 0; }}
  html, body {{ margin: 0; padding: 0; }}
  @font-face {{ font-family: 'TS Sans'; font-weight: 500; src: url({a}/fonts/noto-500.ttf); }}
  @font-face {{ font-family: 'TS Sans'; font-weight: 700; src: url({a}/fonts/noto-700.ttf); }}
  #page {{ position: relative; width: {PW}px; height: {PH}px; overflow: hidden;
          background: url({a}/bg.jpg) 0 0 / 100% 100% no-repeat;
          font-family: 'TS Sans', sans-serif; font-weight: 700; color: #F6EEDC; }}
  .t {{ position: absolute; left: 0; width: {PW}px; text-align: center; line-height: 1; white-space: nowrap; }}
  .top {{ top: {BLEED + (band - top_size) / 2:.1f}px; font-size: {top_size}px; letter-spacing: 3px; color: #F3D27F; }}
  .url {{ top: {foot + 20:.1f}px; font-size: 22px; letter-spacing: 1px; color: #F3D27F; }}
  .foot {{ top: {foot + 54:.1f}px; font-size: 17px; font-weight: 500; letter-spacing: 1px; }}
  .qr {{ position: absolute; left: {qx:.1f}px; top: {qy:.1f}px; width: {qs:.1f}px; height: {qs:.1f}px; }}
  .qr img {{ width: 100%; height: 100%; display: block; }}
"""
    if unit == "mm":
        css = re.sub(r"(\d+(?:\.\d+)?)px", r"\1mm", css)
    return f"""<html><head><meta charset="utf-8"><style>{css}</style></head>
<body><div id="page">
  <div class="t top">PandaAI 黑客松 · 寻找你的交易人格</div>
  <div class="qr"><img src="{a}/qr.svg"></div>
  <div class="t url">meetmind.online/ts</div>
  <div class="t foot">投资者教育游戏，不构成投资建议 · 行情数据主要来自 Panda Data</div>
</div></body></html>"""


def check_layout(pg) -> list[str]:
    """文字不能贴着裁切边，也不能压进底座会挡住的最下面 10 cm。"""
    boxes = pg.evaluate("""() => [...document.querySelectorAll('.t, .qr')].map(e => {
        let r = e.getBoundingClientRect();
        if (e.classList.contains('t')) { const g = document.createRange(); g.selectNodeContents(e); r = g.getBoundingClientRect(); }
        return [e.textContent.trim().slice(0, 12) || 'QR', r.left, r.top, r.right, r.bottom]; })""")
    return [f"越界：{n} ({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})" for n, x0, y0, x1, y1 in boxes
            if x0 < BLEED + 25 or x1 > PW - BLEED - 25 or y0 < BLEED + 5 or y1 > PH - BLEED - BASE]


def decode(im: Image.Image) -> str:
    got, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR))
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", type=Path, default=ART)
    ap.add_argument("--preview", type=Path, help="只出 1 px/mm 的预览图到这个路径")
    opt = ap.parse_args()
    opt.art = opt.art.resolve()
    t0 = time.time()
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    art = Image.open(opt.art).convert("RGB")
    m = measure(np.asarray(art).astype(int))
    k = background(art, m)
    qrcode.make(URL, image_factory=qrcode.image.svg.SvgPathImage, border=2,
                error_correction=qrcode.constants.ERROR_CORRECT_M).save(str(ASSETS / "qr.svg"))
    build_fonts(html("px", m, k))
    (HERE / "banner.html").write_text(html("px", m, k), encoding="utf-8")
    (HERE / "banner_mm.html").write_text(html("mm", m, k), encoding="utf-8")
    preview = opt.preview or OUT / "易拉宝_预览.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    pdf = OUT / f"易拉宝_80x200cm_含3mm出血_{PW}x{PH}mm.pdf"
    jpg = OUT / f"易拉宝_80x200cm_含3mm出血_{DPI}dpi.jpg"
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": PW, "height": PH}, device_scale_factor=1)
        pg.goto((HERE / "banner.html").as_uri(), wait_until="networkidle")
        pg.wait_for_timeout(800)
        bad = check_layout(pg)
        pg.screenshot(path=str(preview))
        if not opt.preview:
            pg = br.new_page(viewport={"width": PW, "height": PH}, device_scale_factor=DPI / 25.4)
            pg.goto((HERE / "banner.html").as_uri(), wait_until="networkidle")
            pg.wait_for_timeout(1500)
            pg.screenshot(path=str(OUT / "_print.png"))
            pg = br.new_page()
            pg.goto((HERE / "banner_mm.html").as_uri(), wait_until="networkidle")
            pg.wait_for_timeout(1500)
            pg.pdf(path=str(pdf), width=f"{PW}mm", height=f"{PH}mm", print_background=True, prefer_css_page_size=True)
        br.close()
    x, y, bw, bh = m["blank"]
    print("画面：", opt.art.relative_to(ROOT), f"顶部色带 0–{m['top']} px，底部色带 {m['bottom']}– px，白方块 {bw}×{bh} px")
    print(f"二维码边长 {min(bw, bh) * k - 4:.0f} mm，离成品底边 {PH - BLEED - (y + bh) * k:.0f} mm")
    print("排版：", "通过" if not bad else bad)
    if opt.preview:
        print("预览二维码：", "解码一致" if decode(Image.open(preview)) == URL else "解不出")
        return
    big = Image.open(OUT / "_print.png").convert("RGB")
    big.save(jpg, quality=90, dpi=(DPI, DPI))
    (OUT / "_print.png").unlink()
    small = big.resize((big.width // 4, big.height // 4), Image.LANCZOS)
    print("二维码：", "解码一致" if decode(big) == URL and decode(small) == URL else "不一致", "（原尺寸和缩到 1/4 都试过）")
    print(f"尺寸：{big.size[0]}×{big.size[1]} px（{DPI} dpi）；用时 {time.time() - t0:.0f}s")
    for f in sorted(OUT.iterdir()):
        if f.is_file():
            print(f"  {f.name}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
