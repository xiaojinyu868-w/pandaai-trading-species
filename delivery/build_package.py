"""把桌游物料打成一个交付包。

python3.11 delivery/build_package.py            # 组装 + 压缩
python3.11 delivery/build_package.py --no-zip   # 只组装，方便检查

规则书、快速入门优先用 print/out 里排好的 PDF；没有就从 content/*.md 排一版。
线上 H5 不进包。不放任何密钥、账号和个人信息。
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import shutil
import zipfile
from pathlib import Path

import markdown
import qrcode
import qrcode.image.svg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "delivery"
NAME = "交易物种起源_桌游物料包_v1.0"
STAGE = DELIVERY / "stage" / NAME
ZIP = DELIVERY / f"{NAME}.zip"
FONTS = Path("/root/.fonts")
SMILEY = ROOT / "print" / "fonts" / "smiley"

SPECIES_CN = {"cheetah": "猎豹", "elephant": "大象", "fox": "狐狸", "owl": "猫头鹰", "meerkat": "狐獴", "chameleon": "变色龙", "beaver": "海狸"}

CSS = """
@font-face { font-family: "Noto"; src: url("file://%(fonts)s/NotoSansSC-Regular.otf"); font-weight: 400; }
@font-face { font-family: "Noto"; src: url("file://%(fonts)s/NotoSansSC-Medium.otf"); font-weight: 500; }
@font-face { font-family: "Noto"; src: url("file://%(fonts)s/NotoSansSC-Bold.otf"); font-weight: 700; }
@page { size: A4; margin: 16mm 16mm 18mm; }
html { font-family: "Noto", sans-serif; color: #2A2A1C; font-size: 10.5pt; line-height: 1.65; }
body { margin: 0; }
h1 { font-size: 24pt; line-height: 1.2; margin: 0 0 4mm; letter-spacing: .02em; }
h2 { font-size: 15pt; margin: 9mm 0 3mm; padding-bottom: 1.5mm; border-bottom: 1.2mm solid #D4432A; break-after: avoid; }
h3 { font-size: 12pt; margin: 6mm 0 2mm; break-after: avoid; }
p, li { orphans: 2; widows: 2; }
blockquote { margin: 3mm 0; padding: 2.5mm 4mm; background: #F7EBD3; border-left: 1.2mm solid #C79A2E; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%%; margin: 3mm 0; font-size: 9.5pt; break-inside: auto; }
th, td { border: 0.3mm solid #CDBF9F; padding: 1.6mm 2.2mm; text-align: left; vertical-align: top; }
th { background: #F2E6CC; }
td:first-child, th:first-child, td:last-child, th:last-child { white-space: nowrap; }
td code { white-space: nowrap; }
tr { break-inside: avoid; }
code { font-family: "Noto", monospace; background: #F2E6CC; padding: 0 1mm; border-radius: 1mm; font-size: 9pt; }
a { color: #2A5D6B; text-decoration: none; }
hr { border: 0; border-top: 0.3mm dashed #CDBF9F; margin: 6mm 0; }
.cover { background: #2A5D6B; color: #FBF4E4; margin: -16mm -16mm 8mm; padding: 18mm 16mm 12mm; }
.cover .k { color: #F3D27F; font-weight: 700; letter-spacing: .2em; font-size: 9pt; }
.cover h1 { color: #FBF4E4; font-size: 30pt; margin-top: 3mm; }
.cover .s { font-size: 11pt; opacity: .92; }
.foot { margin-top: 10mm; font-size: 8.5pt; color: #77745A; }
"""


def md_html(md_text: str, title: str, kicker: str = "") -> str:
    body = markdown.markdown(md_text, extensions=["tables", "sane_lists", "attr_list"])
    if body.startswith("<h1>"):
        end = body.index("</h1>")
        h1 = body[4:end]
        body = body[end + 5:]
    else:
        h1 = title
    cover = f'<div class="cover"><div class="k">{html.escape(kicker)}</div><h1>{h1}</h1></div>'
    return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>{CSS % {'fonts': FONTS}}</style></head><body>{cover}{body}<div class='foot'>投资者教育游戏，不构成投资建议 · 《交易物种起源》</div></body></html>"


def render_pdf(page, html_text: str, out: Path):
    tmp = DELIVERY / "stage" / "_tmp.html"
    tmp.write_text(html_text, encoding="utf-8")
    page.goto(tmp.as_uri(), wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(200)
    out.parent.mkdir(parents=True, exist_ok=True)
    page.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
    tmp.unlink()


def qr_svg(url: str) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8").split("?>", 1)[-1]


def qr_sheet_html(codes: list[dict]) -> str:
    cells = []
    for c in codes:
        cells.append(
            f"<div class='q'><div class='img'>{qr_svg(c['url'])}</div><div class='t'><b>{html.escape(c['id'])}</b><br>"
            f"<span>{html.escape(c['url'].replace('https://', ''))}</span><br><i>{html.escape(c['printed_on'])}</i></div></div>"
        )
    css = CSS % {"fonts": FONTS} + """
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; }
    .q { border: 0.3mm solid #CDBF9F; border-radius: 2mm; padding: 2mm; break-inside: avoid; font-size: 7pt; line-height: 1.35; }
    .q .img svg { width: 26mm; height: 26mm; display: block; margin: 0 auto 1mm; }
    .q i { color: #77745A; font-style: normal; }
    """
    intro = ("<p>每张牌上的码都是无意义的短码，打开前看不出是哪一场。印刷前请用手机逐个扫一遍；"
             "扫码页面不需要登录，也不记录任何信息。</p>")
    return (f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"<div class='cover'><div class='k'>二维码 · 共 {len(codes)} 个</div><h1>二维码总表</h1></div>{intro}<div class='grid'>{''.join(cells)}</div>"
            f"<div class='foot'>投资者教育游戏，不构成投资建议 · 《交易物种起源》</div></body></html>")


def copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args()
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    report: list[str] = []

    print_out = ROOT / "print" / "out"
    out_pdfs = sorted(print_out.rglob("*.pdf")) if print_out.exists() else []
    rulebook = next((p for p in out_pdfs if "规则书" in p.name or "rulebook" in p.name.lower()), None)
    quick = next((p for p in out_pdfs if "快速" in p.name or "quick" in p.name.lower()), None)

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page()

        overview = DELIVERY / "总览.md"
        if overview.exists():
            render_pdf(page, md_html(overview.read_text(encoding="utf-8"), "总览", "先看我"), STAGE / "00_先看我_总览.pdf")
            copy(overview, STAGE / "00_先看我_总览.md")

        if rulebook:
            copy(rulebook, STAGE / "01_规则书" / "规则书.pdf")
        else:
            render_pdf(page, md_html((ROOT / "content" / "rules-v1.md").read_text(encoding="utf-8"), "规则书", "规则书 · v1.0"), STAGE / "01_规则书" / "规则书.pdf")
            report.append("规则书：print/out 里没有排好的版本，用 content/rules-v1.md 排了一版 A4")
        copy(ROOT / "content" / "rules-v1.md", STAGE / "01_规则书" / "规则书.md")

        if quick:
            copy(quick, STAGE / "02_快速入门" / "快速入门.pdf")
        else:
            render_pdf(page, md_html((ROOT / "content" / "quickstart.md").read_text(encoding="utf-8"), "快速入门", "5 分钟开第一局"), STAGE / "02_快速入门" / "快速入门.pdf")
            report.append("快速入门：用 content/quickstart.md 排了一版 A4")
        copy(ROOT / "content" / "quickstart.md", STAGE / "02_快速入门" / "快速入门.md")

        codes = json.loads((ROOT / "content" / "qr.json").read_text(encoding="utf-8"))
        render_pdf(page, qr_sheet_html(codes), STAGE / "05_二维码" / "二维码总表.pdf")

        three_md = ROOT / "3d" / "3D打印说明.md"
        if three_md.exists():
            render_pdf(page, md_html(three_md.read_text(encoding="utf-8"), "3D 打印说明", "3D 打印"), STAGE / "04_3D打印" / "3D打印说明.pdf")
            copy(three_md, STAGE / "04_3D打印" / "3D打印说明.md")
        br.close()

    for p in out_pdfs:
        copy(p, STAGE / "03_印刷文件" / p.relative_to(print_out))
    for p in sorted(print_out.rglob("*.md")) + sorted(print_out.rglob("*.txt")) + sorted(print_out.rglob("*.csv")):
        copy(p, STAGE / "03_印刷文件" / p.relative_to(print_out))
    if not out_pdfs:
        report.append("印刷文件：print/out 里还没有 PDF")

    with open(STAGE / "05_二维码" / "二维码清单.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["编号", "短码", "网址", "打开的页面", "印在哪里", "档位"])
        for c in codes:
            w.writerow([c["id"], c["code"], c["url"], c["route"], c["printed_on"], c.get("tier", "")])

    tokens = ROOT / "3d" / "tokens"
    for p in sorted(tokens.glob("*.stl")):
        copy(p, STAGE / "04_3D打印" / "令牌" / p.name)
    for p in sorted(tokens.glob("preview*.png")) + [tokens / "tokens_report.json"]:
        if p.exists():
            copy(p, STAGE / "04_3D打印" / "令牌" / p.name)
    for sid, cn in SPECIES_CN.items():
        d = ROOT / "3d" / "figurines" / sid
        for fn in ["print.stl", "print.3mf", "preview.png", "print_report.json"]:
            if (d / fn).exists():
                copy(d / fn, STAGE / "04_3D打印" / "手办" / f"{cn}_{sid}" / fn)

    prev = DELIVERY / "previews"
    if prev.exists():
        for p in sorted(prev.glob("*")):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf"):
                copy(p, STAGE / "06_预览图" / p.name)

    files = [p for p in STAGE.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"组装完成：{len(files)} 个文件，{size / 1e6:.1f} MB → {STAGE}")
    for r in report:
        print("  ·", r)
    if a.no_zip:
        return
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(files):
            z.write(p, Path(NAME) / p.relative_to(STAGE))
    print(f"压缩包：{ZIP}（{ZIP.stat().st_size / 1e6:.1f} MB）")


if __name__ == "__main__":
    main()
