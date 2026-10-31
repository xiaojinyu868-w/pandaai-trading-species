"""美术素材预处理：裁掉 AI 图里的奶油空带、芥末条和右下角空白标签框，统一放大、转 JPEG。

输出到 print/build/art/，返回 file:// 路径给模板用。原图不动。
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from .paths import ART, BUILD, ROOT
from .tokens import C

OUT = BUILD / "art"
OUT.mkdir(parents=True, exist_ok=True)
MISSING: list[str] = []
USED: dict[str, str] = {}


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def first(pattern: str) -> Path | None:
    fs = sorted(glob.glob(str(ART / pattern), recursive=True))
    fs = [f for f in fs if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    return Path(fs[0]) if fs else None


def _is_cream(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 205) & (g > 190) & (b > 150) & (r - b < 75) & (r - b > 12)


def _is_mustard(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 150) & (r < 235) & (g > 105) & (g < 185) & (b < 105) & (r - b > 85)


def picture_box(im: Image.Image, kind: str):
    """kind = 'scene'（上空带）或 'species'（下空带）。返回画面区域 (x0,y0,x1,y1)。"""
    a = np.asarray(im.convert("RGB"))
    H, W, _ = a.shape
    c0, c1 = int(W * 0.12), int(W * 0.88)
    must = _is_mustard(a[:, c0:c1]).mean(axis=1) > 0.7
    cream = _is_cream(a[:, c0:c1]).mean(axis=1) > 0.6
    r0, r1 = int(H * 0.15), int(H * 0.85)
    col_cream = _is_cream(a[r0:r1, :]).mean(axis=0) > 0.6
    x0 = 0
    while x0 < W // 4 and col_cream[x0]:
        x0 += 1
    x1 = W - 1
    while x1 > W * 3 // 4 and col_cream[x1]:
        x1 -= 1
    if kind == "scene":
        rows = np.where(must[: H // 3])[0]
        y0 = (rows.max() + 1) if len(rows) else int(H * 0.14)
        while y0 < H // 3 and (cream[y0] or must[y0]):
            y0 += 1
        y1 = H - 1
        while y1 > H * 2 // 3 and cream[y1]:
            y1 -= 1
    else:
        rows = np.where(must[H // 2:])[0]
        y1 = (rows.min() + H // 2 - 1) if len(rows) else int(H * 0.86)
        while y1 > H // 2 and (cream[y1] or must[y1]):
            y1 -= 1
        y0 = 0
        while y0 < H // 4 and cream[y0]:
            y0 += 1
    ins = 6
    return (x0 + ins, y0 + ins, x1 - ins, y1 - ins)


def _save(im: Image.Image, name: str, scale: float = 1.0, q: int = 90, sharpen=True) -> Path:
    if scale != 1.0:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        if sharpen:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=45, threshold=2))
    p = OUT / f"{name}.jpg"
    im.convert("RGB").save(p, "JPEG", quality=q, optimize=True, progressive=False, subsampling=0)
    return p


def _fresh(src: Path, dst: Path) -> bool:
    return dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime


META_FILE = OUT / "meta.json"
META = json.loads(META_FILE.read_text()) if META_FILE.exists() else {}


def _meta_save():
    META_FILE.write_text(json.dumps(META, ensure_ascii=False, indent=1))


def scene_art(src: Path | None, name: str, scale=1.5) -> dict | None:
    """名场面/揭幕/序章这类上方有空带的竖图。返回 {'uri', 'w', 'h', 'label'(右下角空框在裁后图中的相对位置)}"""
    if src is None:
        MISSING.append(name)
        return None
    dst = OUT / f"{name}.jpg"
    if not (_fresh(src, dst) and name in META):
        im = Image.open(src).convert("RGB")
        box = picture_box(im, "scene")
        crop = im.crop(box)
        W, H = crop.size
        # 右下角空白标签框的大概位置（相对裁后图）
        lab = _find_label_box(np.asarray(crop))
        _save(crop, name, scale)
        META[name] = {"w": round(W * scale), "h": round(H * scale), "label": lab, "src": str(src.relative_to(ROOT))}
        _meta_save()
    USED[name] = META[name]["src"]
    return {"uri": dst.as_uri(), **META[name]}


def _find_label_box(a):
    H, W, _ = a.shape
    sub = a[int(H * 0.82):, int(W * 0.70):]
    r, g, b = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
    white = (r > 228) & (g > 220) & (b > 200)
    ys, xs = np.where(white)
    if len(ys) < 200:
        return None
    y0, y1 = np.percentile(ys, 2), np.percentile(ys, 98)
    x0, x1 = np.percentile(xs, 2), np.percentile(xs, 98)
    oy, ox = int(H * 0.82), int(W * 0.70)
    return [round((ox + x0) / W, 4), round((oy + y0) / H, 4), round((ox + x1) / W, 4), round((oy + y1) / H, 4)]


def species_art(sid: str, scale=1.5) -> dict | None:
    src = first(f"style-v7/v7_species_{sid}/**/*.png") or first(f"style-v6/v6_species_{sid}/**/*.png")
    name = f"species_{sid}"
    if src is None:
        MISSING.append(name)
        return None
    dst = OUT / f"{name}.jpg"
    if not (_fresh(src, dst) and name in META):
        im = Image.open(src).convert("RGB")
        crop = im.crop(picture_box(im, "species"))
        _save(crop, name, scale)
        META[name] = {"w": round(crop.width * scale), "h": round(crop.height * scale), "src": str(src.relative_to(ROOT))}
        _meta_save()
    USED[name] = META[name]["src"]
    return {"uri": dst.as_uri(), **META[name]}


# 物种头像中心（相对整张原图）与半径（相对宽度），人工看图标定
HEADS = {
    "cheetah": (0.525, 0.175, 0.16), "elephant": (0.50, 0.17, 0.20), "fox": (0.53, 0.27, 0.23),
    "owl": (0.46, 0.15, 0.20), "meerkat": (0.47, 0.145, 0.15), "chameleon": (0.49, 0.15, 0.20),
    "beaver": (0.46, 0.12, 0.16),
}


def medal(sid: str, size=600) -> dict | None:
    src = first(f"style-v7/v7_species_{sid}/**/*.png")
    name = f"medal_{sid}"
    if src is None:
        MISSING.append(name)
        return None
    dst = OUT / f"{name}.jpg"
    if not _fresh(src, dst):
        im = Image.open(src).convert("RGB")
        cx, cy, r = HEADS.get(sid, (0.5, 0.2, 0.2))
        W, H = im.size
        R = r * W
        box = (int(cx * W - R), int(cy * H - R), int(cx * W + R), int(cy * H + R))
        crop = im.crop(box).resize((size, size), Image.LANCZOS)
        _save(crop, name)
    USED[name] = str(src.relative_to(ROOT))
    return {"uri": dst.as_uri()}


def tile_art(kind: str) -> dict | None:
    """地块插画：底色校正到纸色，便于直接放在奶油格子里。"""
    src = first(f"style-v7/v7_tile_{kind}/**/*.png")
    name = f"tile_{kind}"
    if src is None:
        MISSING.append(name)
        return None
    dst = OUT / f"{name}.jpg"
    if not _fresh(src, dst):
        im = Image.open(src).convert("RGB")
        a = np.asarray(im).astype(np.float32)
        corners = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3), a[-40:, :40].reshape(-1, 3), a[-40:, -40:].reshape(-1, 3)])
        bg = np.median(corners, axis=0)
        paper = np.array(_hex(C["paper"]), dtype=np.float32)
        a = np.clip(a * (paper / bg), 0, 255).astype(np.uint8)
        _save(Image.fromarray(a), name)
    USED[name] = str(src.relative_to(ROOT))
    return {"uri": dst.as_uri()}


ICON_NAMES = ["phone", "ledger", "chart", "letter", "magnifier", "coin", "dice", "egg", "kite", "hourglass", "compass", "waterwheel"]


def icon(name: str) -> dict | None:
    src = ART / "style-v6/v6_icons/img_50570/ai_generate_50570_1.png"
    key = f"icon_{name}"
    if not src.exists():
        MISSING.append(key)
        return None
    dst = OUT / f"{key}.jpg"
    if not _fresh(src, dst):
        im = Image.open(src).convert("RGB")
        idx = ICON_NAMES.index(name)
        r, c = divmod(idx, 4)
        W, H = im.size
        cw, ch = W / 4, H / 3
        cell = im.crop((int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)))
        a = np.asarray(cell)
        mask = ~_is_cream(a)
        # 去掉阴影边缘的细碎点
        ys, xs = np.where(mask)
        if len(ys):
            y0, y1 = np.percentile(ys, 0.5), np.percentile(ys, 99.5)
            x0, x1 = np.percentile(xs, 0.5), np.percentile(xs, 99.5)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            s = max(x1 - x0, y1 - y0) / 2 + 10
            box = (int(cx - s), int(cy - s), int(cx + s), int(cy + s))
            canvas = Image.new("RGB", (int(2 * s), int(2 * s)), _hex(C["paper"]))
            sub = cell.crop((max(0, box[0]), max(0, box[1]), min(cell.width, box[2]), min(cell.height, box[3])))
            canvas.paste(sub, (max(0, -box[0]), max(0, -box[1])))
            cell = canvas
        a = np.asarray(cell).astype(np.float32)
        bg = np.median(np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3)]), axis=0)
        paper = np.array(_hex(C["paper"]), dtype=np.float32)
        a = np.clip(a * (paper / np.maximum(bg, 1)), 0, 255).astype(np.uint8)
        im2 = Image.fromarray(a).resize((520, 520), Image.LANCZOS)
        _save(im2, key)
    USED[key] = str(src.relative_to(ROOT))
    return {"uri": dst.as_uri()}


def plain(src: Path | None, name: str, scale=1.0, crop=None) -> dict | None:
    if src is None or not Path(src).exists():
        MISSING.append(name)
        return None
    dst = OUT / f"{name}.jpg"
    if not (_fresh(src, dst) and name in META):
        im = Image.open(src).convert("RGB")
        if crop:
            W, H = im.size
            im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        _save(im, name, scale)
        META[name] = {"w": round(im.width * scale), "h": round(im.height * scale), "src": str(Path(src).relative_to(ROOT))}
        _meta_save()
    USED[name] = META[name]["src"]
    return {"uri": dst.as_uri(), **META[name]}


def duotone(src_name: str, dark: str, light: str, name: str) -> dict | None:
    """把已处理的图做成双色调（门牌背面“门缝里”看到的风景）。"""
    srcp = OUT / f"{src_name}.jpg"
    if not srcp.exists():
        return None
    dst = OUT / f"{name}.jpg"
    if not _fresh(srcp, dst):
        g = ImageOps.grayscale(Image.open(srcp))
        g = ImageOps.autocontrast(g, cutoff=1)
        im = ImageOps.colorize(g, _hex(dark), _hex(light))
        _save(im, name, 1.0, sharpen=False)
    return {"uri": dst.as_uri()}


# ---------- 场景素材查找（P1 没图时回退到同季图） ----------
SCENE_BLIND = {
    "s924": "style-v6/v6_scene_spring_924/img_50566/ai_generate_50566_1.png",
    "s2015": "style-v2/img_50322/ai_generate_50322_1.png",
    "smt": "style-v6/v6_scene_autumn_moutai/img_50567/ai_generate_50567_1.png",
    "scb": "style-v6/v6_scene_winter_2020/img_50564/ai_generate_50564_1.png",
}
SCENE_REVEAL = {
    "s924": "style-v7/v7_reveal_spring_924/**/*.png",
    "s2015": "style-v6/v6_scene_summer_2015_reveal/img_50573/ai_generate_50573_1.png",
    "smt": "style-v7/v7_reveal_autumn_moutai/**/*.png",
    "scb": "style-v7/v7_reveal_winter_2020/**/*.png",
}
P1_FALLBACK = {"squant": "smt", "soil": "scb"}


def scene_images(sid: str) -> dict:
    """返回 {'blind': art|None, 'reveal': art|None, 'placeholder': bool}"""
    out = {"placeholder": False}
    for face, table in (("blind", SCENE_BLIND), ("reveal", SCENE_REVEAL)):
        src = None
        if sid in table:
            src = first(table[sid])
        else:
            src = first(f"style-v8/v8_{sid}_{face}/**/*.png")
            if src is None:
                fb = P1_FALLBACK.get(sid)
                src = first(table[fb]) if fb else None
                out["placeholder"] = True
                MISSING.append(f"{sid}_{face}（P1 图未出，暂用同季图 + 色块占位）")
        out[face] = scene_art(src, f"{face}_{sid}") if src else None
    return out


# ---------- 盒标：美术定稿「我不是韭菜！」（art/build_box_v9.py） ----------
BOX_LID = "box-v9/v9_box_lid_x/**/*_2.png"
BOX_TITLE = "box-v9/v9_side_title/**/*_1.png"
BOX_ICONS = "box-v9/v9_side_icons/**/*_2.png"
BOX_ICON_NAMES = ["exchange", "chart", "arrows"]


def box_lid(w_mm: float, h_mm: float) -> dict | None:
    """盒盖整图（字是画进去的），居中裁成含出血的成品比例。"""
    src = first(BOX_LID)
    if src is None:
        MISSING.append("box_lid")
        return None
    W, H = Image.open(src).size
    r = w_mm / h_mm
    cw, ch = (W, W / r) if W / H < r else (H * r, H)
    dx, dy = (1 - cw / W) / 2, (1 - ch / H) / 2
    return plain(src, "box_lid", crop=(dx, dy, 1 - dx, 1 - dy))


def box_gold(name: str) -> dict | None:
    """侧标的金色素材，透明底 PNG，裁到内容边界。name = title / exchange / chart / arrows。"""
    src = first(BOX_TITLE if name == "title" else BOX_ICONS)
    key = f"box_{name}"
    if src is None:
        MISSING.append(key)
        return None
    dst = OUT / f"{key}.png"
    if not (_fresh(src, dst) and key in META):
        im = Image.open(src).convert("RGBA")
        a = np.asarray(im)[..., 3]
        if name != "title":
            # 三个图标排成一行，按空白列切开
            cols = np.where((a > 24).any(axis=0))[0]
            gaps = np.where(np.diff(cols) > 40)[0]
            starts = [cols[0]] + [cols[g + 1] for g in gaps]
            ends = [cols[g] for g in gaps] + [cols[-1]]
            assert len(starts) == len(BOX_ICON_NAMES), f"{src.name}: 切出 {len(starts)} 个图标"
            i = BOX_ICON_NAMES.index(name)
            im = im.crop((starts[i], 0, ends[i] + 1, im.height))
            a = np.asarray(im)[..., 3]
        ys, xs = np.where(a > 24)
        pad = 6
        im = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)))
        im.save(dst, optimize=True)
        META[key] = {"w": im.width, "h": im.height, "src": str(src.relative_to(ROOT))}
        _meta_save()
    USED[key] = META[key]["src"]
    return {"uri": dst.as_uri(), **META[key]}


def box_spine(w_mm: float, h_mm: float, color: str, dpi: int = 200) -> dict:
    """侧标底：深色加一层很淡的纸纹和四边压暗，接近美术图侧脊的质感。"""
    key = f"box_spine_{w_mm:g}x{h_mm:g}"
    dst = OUT / f"{key}.jpg"
    if not dst.exists():
        W, H = round(w_mm / 25.4 * dpi), round(h_mm / 25.4 * dpi)
        rng = np.random.default_rng(11)
        fine = rng.normal(0, 1, (H, W))
        blot = np.asarray(Image.fromarray(rng.normal(0, 1, (max(2, H // 40), max(2, W // 40))).astype(np.float32))
                          .resize((W, H), Image.BICUBIC))
        yy, xx = np.mgrid[0:H, 0:W]
        edge = np.minimum(np.minimum(xx, W - 1 - xx) / (0.12 * W), np.minimum(yy, H - 1 - yy) / (0.35 * H)).clip(0, 1)
        k = 1 + 0.035 * fine + 0.045 * blot - 0.07 * (1 - edge)
        a = np.clip(np.array(_hex(color), dtype=np.float32)[None, None, :] * k[..., None], 0, 255).astype(np.uint8)
        _save(Image.fromarray(a), key, sharpen=False)
    return {"uri": dst.as_uri()}
