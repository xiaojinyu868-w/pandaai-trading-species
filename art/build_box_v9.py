"""第九轮：盒标按美术定稿（refs/box_anchor_artist.jpg，标题「我不是韭菜！」）重做。

美术图是一张近似方形的盒子效果照；我们的盒盖贴纸是 300×215（含出血 306×221）的横版，侧标是 300×50 / 215×50 的长条。
- 盒盖：整张让 GPT Image 2.5 照美术图重构成横版平面稿，字也直接画。3328×2400 ≈ 306×221 mm @ 276 dpi。
- 侧标：照美术图的深色侧脊，单独出透明底的金色标题和三个金色图标，由 print/src/c_box.py 排版，
  人数时长、免责声明、盒内配件这些准确文字用代码排。

输出：box-v9.jsonl（给 run_parallel.py）
"""

import json
from pathlib import Path

from build_style_batch_v7 import MODEL

HERE = Path(__file__).parent
REFS = HERE / "refs"
ANCHOR, TITLE_REF, CAST_REF, SPINE_REF = (str(REFS / f"box_anchor_{n}.jpg") for n in ("artist", "title", "cast", "spine"))

FLAT = (
    "Flat print-ready front artwork for a board game box lid, landscape, full bleed to all four edges, seen perfectly "
    "straight-on. Only the 2D artwork itself: no box, no spine, no box edges or corners, no 3D mockup, no table, no room "
    "light, no cast shadows, no perspective distortion."
)

FAITHFUL = (
    "Recreate the box cover design of the first reference image as faithfully as possible, the same artwork re-composed "
    "for a wider landscape frame: the same retro constructivist propaganda-poster style with a heroic low angle, the same "
    "bold flat shapes, aged paper grain, fine halftone and worn ink texture, and the same palette of warm cream, vermilion "
    "red, terracotta orange, mustard, deep teal, slate blue-grey and near-black green ink."
)

TITLE = (
    "At the top, the same huge, heavy, chunky, slightly distressed hand-lettered title 我不是韭菜！ in near-black green "
    "ink on one line across the upper third: exactly these five Chinese characters followed by a bold exclamation mark, "
    "letterforms matching the second reference image. Below the right end of the title, the small dark serif line "
    "I'M NOT A LEEK! on two lines. Behind the title, sunburst rays alternating cream and vermilion fan out from the building."
)

SCENE = (
    "In the middle, the same neoclassical stock exchange with a triangular pediment carved with the word EXCHANGE, tall "
    "columns, a red vertical banner reading BUY on the left and one reading SELL on the right, small red flags on the "
    "roofline; angular teal and grey skyscrapers and red flags fan out on both sides and extend to fill the wider frame."
)

CAST = (
    "In front, the same six animal characters with exactly the same designs, clothes and poses as the third reference "
    "image, seen from below like monuments, standing behind a dark teal stone parapet along the bottom edge: on the left "
    "an elephant in a dark suit and teal tie raising its trunk, a stern owl in a suit in front of it; in the center the "
    "tallest figure, a cheetah with a long red scarf flowing in the wind, looking up to the right; then a meerkat with "
    "crossed arms, a fox in a dark suit, and on the right a green chameleon in a suit with a curled tail; a red rising "
    "arrow block at the lower right. Spread the group a little wider so each character has room to breathe."
)

SAFE = (
    "Keep the title, the English line and every face well inside the frame, at least 7 percent away from each edge, "
    "because the outer edge will be trimmed. No other text, no numbers, no logos, no real brands, no pandas, no real people."
)

GOLD = "flat matte antique-gold ink (#C2A15F) with a subtle worn print texture"

SIDE_TITLE = (
    "A horizontal title lockup for the long side panel of the board game box in the first reference image, on a fully "
    "transparent background. The Chinese title 我不是韭菜！ on one single horizontal line, in the same heavy, chunky, "
    f"slightly distressed hand-lettered style as the title on the box, in {GOLD}; directly to its right, the small gold "
    "serif text I'M NOT A LEEK! stacked on three short lines exactly like on the box spine in the second reference image. "
    "Flat 2D, perfectly straight-on, no box, no shadow, no background color, no frame, nothing else. Exactly these "
    "characters, no other text."
)

SIDE_ICONS = (
    "Three separate emblem icons copied from the gold icons printed on the dark spine of the board game box (first "
    "reference image, enlarged in the second reference image), on a fully transparent background, in one horizontal row "
    "with wide empty gaps between them, each the same height and centered vertically: (1) a classical exchange building "
    "with a triangular pediment, four columns and a stepped base; (2) a rising bar chart with an upward zigzag arrow, "
    "standing on a row of stacked coins; (3) a bundle of upward arrows rising from a small stepped base. "
    f"Simple bold solid shapes in {GOLD}, consistent weight, no text, no letters, no numbers, no shadow, no background "
    "color, nothing else."
)


def task(id_, label, size, prompt, refs, count=1, **extra):
    return {"id": f"v9_{id_}", "label": label, "size": size, "prompt": prompt, "ref": refs, "count": count,
            **MODEL, **extra}


LID = " ".join([FLAT, FAITHFUL, TITLE, SCENE, CAST, SAFE])

ROWS = [
    task("box_lid", "盒盖 · 横版重构（high）", "3328x2400", LID, [ANCHOR, TITLE_REF, CAST_REF], count=2),
    task("box_lid_x", "盒盖 · 横版重构（xhigh）", "3328x2400", LID, [ANCHOR, TITLE_REF, CAST_REF], count=2,
         quality="xhigh"),
    task("side_title", "侧标 · 金色标题", "3072x1024", SIDE_TITLE, [ANCHOR, SPINE_REF, TITLE_REF], count=2,
         background="transparent"),
    task("side_icons", "侧标 · 金色图标", "3072x1024", SIDE_ICONS, [ANCHOR, SPINE_REF], count=2,
         background="transparent"),
]


def main():
    out = HERE / "box-v9.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
