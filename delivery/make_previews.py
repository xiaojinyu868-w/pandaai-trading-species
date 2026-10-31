"""给交付包拼预览图：3D 手办合影、令牌总览、扫码页面合集、印刷物料总览。

python3.11 delivery/make_previews.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "delivery" / "previews"
FONT = "/root/.fonts/NotoSansSC-Bold.otf"
PAPER = (242, 230, 204)
INK = (42, 42, 28)
SPECIES = [("cheetah", "猎豹"), ("elephant", "大象"), ("fox", "狐狸"), ("owl", "猫头鹰"), ("meerkat", "狐獴"), ("chameleon", "变色龙"), ("beaver", "海狸 · 隐藏")]


def font(size):
    return ImageFont.truetype(FONT, size)


def title_bar(img: Image.Image, text: str, sub: str = "") -> Image.Image:
    bar = 120 if sub else 90
    out = Image.new("RGB", (img.width, img.height + bar), PAPER)
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, img.width, bar - 8], fill=(42, 93, 107))
    d.text((40, 22), text, font=font(42), fill=(251, 244, 228))
    if sub:
        d.text((40, 76), sub, font=font(22), fill=(243, 210, 127))
    out.paste(img, (0, bar))
    return out


def figurines():
    cells = []
    for sid, cn in SPECIES:
        p = ROOT / "3d" / "figurines" / sid / "preview.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        w = 520
        im = im.resize((w, int(im.height * w / im.width)))
        c = Image.new("RGB", (w, im.height + 60), PAPER)
        c.paste(im, (0, 0))
        ImageDraw.Draw(c).text((w // 2, im.height + 8), cn, font=font(30), fill=INK, anchor="mt")
        cells.append(c)
    if not cells:
        return
    cols = 4
    w, h = cells[0].width, max(c.height for c in cells)
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 20, rows * h + (rows + 1) * 20), PAPER)
    for i, c in enumerate(cells):
        sheet.paste(c, (20 + (i % cols) * (w + 20), 20 + (i // cols) * (h + 20)))
    title_bar(sheet, "物种手办 · 3D 打印", "高 60 mm，平底；推荐光固化树脂。H5 里可以“转一转”同一份模型").save(OUT / "3D手办预览.jpg", quality=88)


def tokens():
    for name in ("preview_all.png", "preview_crests.png"):
        p = ROOT / "3d" / "tokens" / name
        if p.exists():
            im = Image.open(p).convert("RGB")
            if im.width > 2400:
                im = im.resize((2400, int(im.height * 2400 / im.width)))
            label = "令牌总览" if name == "preview_all.png" else "物种头饰"
            title_bar(im, f"{label} · 3D 打印", "PLA 平放打印，不需要支撑").save(OUT / f"3D{label}.jpg", quality=88)


def qr_pages():
    src = ROOT / "qa" / "pages"
    picks = [("start_start.png", "开局码"), ("b_s924-blind.png", "场景牌 · 盲测"), ("e_s924-price.png", "证据牌背面"), ("r_s924-reveal.png", "揭幕牌"),
             ("ff_scb-ff.png", "熔断沙漏"), ("rule_rule-ma520.png", "规则牌"), ("sp_sp-cheetah.png", "物种牌"), ("dp_dp-01.png", "数据港口牌"),
             ("c_chance-01.png", "机会牌"), ("task_task-chart-basic.png", "任务牌"), ("record_record.png", "档案卡：录入手机"), ("atlas_atlas.png", "物种图鉴")]
    cells = []
    for fn, label in picks:
        p = src / fn
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        w = 390
        im = im.resize((w, int(im.height * w / im.width)))
        im = im.crop((0, 0, w, min(im.height, 760)))
        c = Image.new("RGB", (w, 760 + 56), PAPER)
        c.paste(im, (0, 0))
        ImageDraw.Draw(c).text((w // 2, 770), label, font=font(26), fill=INK, anchor="mt")
        cells.append(c)
    if not cells:
        return
    cols = 6
    w, h = cells[0].width, cells[0].height
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 18, rows * h + (rows + 1) * 18), PAPER)
    for i, c in enumerate(cells):
        sheet.paste(c, (18 + (i % cols) * (w + 18), 18 + (i // cols) * (h + 18)))
    title_bar(sheet, "扫码之后看到什么", "牌上的码都是无意义短码 meetmind.online/ts/q/<短码>；不用登录，不记录任何信息").save(OUT / "扫码页面预览.jpg", quality=86)


def print_sheets():
    src = ROOT / "print" / "preview"
    pngs = sorted(src.glob("*.png")) if src.exists() else []
    for p in pngs:
        im = Image.open(p).convert("RGB")
        if im.width > 3000:
            im = im.resize((3000, int(im.height * 3000 / im.width)))
        im.save(OUT / f"印刷_{p.stem}.jpg", quality=86)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figurines()
    tokens()
    qr_pages()
    print_sheets()
    for p in sorted(OUT.glob("*")):
        print(p.name, f"{p.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
