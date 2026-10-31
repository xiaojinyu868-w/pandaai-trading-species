"""把 art/ 里选定的插画转成 H5 用的 WebP，放到 h5/public/art/。

- 名场面图：裁掉顶部给标题留的奶油空带和芥末黄细条
- 物种立绘：裁掉底部给名字留的空带
- 地块插画、图标：把奶油底抠成透明
重跑覆盖。
"""

import glob
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art" / "vmc-output"
OUT = ROOT / "h5" / "public" / "art"
FONTS_SRC = ROOT / "print" / "fonts" / "smiley"
FONTS_DST = ROOT / "h5" / "public" / "fonts" / "smiley"


def first(pattern):
    hits = sorted(glob.glob(str(ART / pattern), recursive=True))
    return Path(hits[0]) if hits else None


def stripe_rows(im, top=True):
    """找芥末黄细条所在的行：整行颜色接近芥末黄、变化很小。"""
    a = np.asarray(im.convert("RGB")).astype(float)
    h = a.shape[0]
    rng = range(0, int(h * 0.3)) if top else range(h - 1, int(h * 0.62), -1)
    for y in rng:
        row = a[y, int(a.shape[1] * 0.1):int(a.shape[1] * 0.9)]
        m = row.mean(0)
        if row.std(0).mean() < 18 and m[0] > 150 and 110 < m[1] < 190 and m[2] < 110 and m[0] - m[2] > 70:
            return y
    return None


def crop_scene(src, extra_top=0.0, bottom=0.92):
    """bottom：底部右下角给印刷留了一块空白标签牌，H5 里不需要，按比例裁掉。"""
    im = Image.open(src).convert("RGB")
    y = stripe_rows(im, top=True)
    if y is not None:
        while y < im.height and stripe_rows(im.crop((0, y, im.width, y + 1)), top=True) == 0:
            y += 1
        im = im.crop((0, y + 6, im.width, im.height))
    w, h = im.size
    return im.crop((int(w * 0.012), int(h * extra_top), int(w * 0.988), int(h * bottom)))


def crop_species(src):
    im = Image.open(src).convert("RGB")
    y = stripe_rows(im, top=False)
    if y is not None:
        while y > 0 and stripe_rows(im.crop((0, y - 1, im.width, y)), top=True) == 0:
            y -= 1
        im = im.crop((0, 0, im.width, y - 6))
    w, h = im.size
    return im.crop((int(w * 0.012), int(h * 0.01), int(w * 0.988), h))


def key_out(im, tol=26, soft=22):
    im = im.convert("RGBA")
    a = np.asarray(im).astype(float)
    corners = np.concatenate([a[:8, :8, :3].reshape(-1, 3), a[:8, -8:, :3].reshape(-1, 3),
                              a[-8:, :8, :3].reshape(-1, 3), a[-8:, -8:, :3].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    d = np.sqrt(((a[..., :3] - bg) ** 2).sum(-1))
    alpha = np.clip((d - tol) / soft, 0, 1) * 255
    a[..., 3] = np.minimum(a[..., 3], alpha)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def save(im, name, width, q=82, alpha=False):
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"{name}.webp", "WEBP", quality=q, method=5, **({"lossless": False} if alpha else {}))
    return OUT / f"{name}.webp"


BLIND = {
    "s924": "style-v6/v6_scene_spring_924/**/*.png",
    "s2015": "style-v2/img_50322/*.png",
    "smt": "style-v6/v6_scene_autumn_moutai/**/*.png",
    "scb": "style-v6/v6_scene_winter_2020/**/*.png",
    "squant": "style-v8/v8_squant_blind/**/*.png",
    "soil": "style-v8/v8_soil_blind/**/*.png",
}
REVEAL = {
    "s924": "style-v7/v7_reveal_spring_924/**/*.png",
    "s2015": "style-v6/v6_scene_summer_2015_reveal/**/*.png",
    "smt": "style-v7/v7_reveal_autumn_moutai/**/*.png",
    "scb": "style-v7/v7_reveal_winter_2020/**/*.png",
    "squant": "style-v8/v8_squant_reveal/**/*.png",
    "soil": "style-v8/v8_soil_reveal/**/*.png",
}
SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
TILES = ["supply", "chance", "research", "dataport", "calm", "station", "start"]
ICONS = ["phone", "ledger", "chart", "letter", "magnifier", "coin", "dice", "egg", "kite", "hourglass", "compass", "waterwheel"]


def main():
    made = []
    for sid, pat in BLIND.items():
        f = first(pat)
        if f:
            made.append(save(crop_scene(f), f"blind_{sid}", 900))
    for sid, pat in REVEAL.items():
        f = first(pat)
        if f:
            made.append(save(crop_scene(f), f"reveal_{sid}", 900))
    for sp in SPECIES:
        f = first(f"style-v7/v7_species_{sp}/**/*.png")
        if f:
            made.append(save(crop_species(f), f"species_{sp}", 820))
        f = first(f"style-v7/v7_figurine_{sp}/**/*.png")
        if f:
            made.append(save(key_out(Image.open(f), tol=14, soft=16), f"fig_{sp}", 640, alpha=True))
    for t in TILES:
        f = first(f"style-v7/v7_tile_{t}/**/*.png")
        if f:
            made.append(save(key_out(Image.open(f)), f"tile_{t}", 360, alpha=True))
    f = first("style-v6/v6_icons/**/*.png")
    if f:
        im = Image.open(f).convert("RGB")
        cw, ch = im.width / 4, im.height / 3
        for i, name in enumerate(ICONS):
            c, r = i % 4, i // 4
            cell = im.crop((int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)))
            made.append(save(key_out(cell), f"icon_{name}", 220, alpha=True))
    for name, pat, w in [("opening", "style-v7/v7_h5_opening/**/*.png", 1000),
                         ("prologue", "style-v7/v7_prologue/**/*.png", 900),
                         ("box_cover", "box-v9/v9_box_lid_x/**/*_2.png", 1600)]:
        f = first(pat)
        if f:
            im = crop_scene(f, extra_top=0.03, bottom=0.99) if name == "prologue" else Image.open(f).convert("RGB")
            made.append(save(im, name, w))
    for i, f in enumerate(sorted(glob.glob(str(ART / "style-v7/v7_board_background/**/*.png"), recursive=True))):
        made.append(save(Image.open(f).convert("RGB"), f"board_bg_{i + 1}", 1400, q=80))
    f = first("style-v7/v7_tile_start/**/*.png")
    if f:
        key_out(Image.open(f)).resize((128, 128), Image.LANCZOS).save(OUT / "icon.png")
    if FONTS_SRC.exists():
        FONTS_DST.mkdir(parents=True, exist_ok=True)
        for p in FONTS_SRC.iterdir():
            (FONTS_DST / p.name).write_bytes(p.read_bytes())
    total = sum(p.stat().st_size for p in made)
    print(f"{len(made)} 张图 -> {OUT}，共 {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
