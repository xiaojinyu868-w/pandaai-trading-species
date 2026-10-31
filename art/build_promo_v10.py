"""第十轮：游园会宣传物料，画风跟盒标定稿（「我不是韭菜！」复古宣传画）一致。

- 主视觉（竖版）：引流卡 A6 正面和展位海报 A2 共用。2400×3392 ≈ A 系列比例；下方留一整条空的深墨绿石台，
  二维码提示、人数时长这些准确文字由 print/src/c_promo.py 排在上面。
- 物种贴纸：7 个物种（含隐藏的海狸）各一张方图，代码裁成 Ø50 圆贴，名字和口号由代码排。
- 口号贴纸：「我不是韭菜！」圆章，字直接画。

输出：promo-v10.jsonl（给 run_parallel.py）
"""

import json
from pathlib import Path

from build_style_batch_v7 import MODEL

HERE = Path(__file__).parent
REFS = HERE / "refs"
ANCHOR, TITLE_REF, CAST_REF = (str(REFS / f"box_anchor_{n}.jpg") for n in ("artist", "title", "cast"))
LID = str(HERE / "vmc-output/box-v9/v9_box_lid_x/img_50672/ai_generate_50672_2.png")

STYLE = (
    "The same retro constructivist propaganda-poster style as the reference images: heroic low angle, bold flat shapes, "
    "aged paper grain, fine halftone and worn ink texture, palette of warm cream, vermilion red, terracotta orange, "
    "mustard, deep teal, slate blue-grey and near-black green ink."
)

NO = "No numbers, no logos, no real brands, no pandas, no real people."

POSTER = " ".join([
    "Flat print-ready portrait poster artwork, full bleed, seen straight-on, only the 2D artwork.",
    STYLE,
    "At the top, the same huge, heavy, chunky, slightly distressed hand-lettered title 我不是韭菜！ in near-black green "
    "ink, set on two lines (我不是 / 韭菜！) and filling the width, letterforms matching the second reference image; "
    "a small dark serif line I'M NOT A LEEK! under the right end of the title. Sunburst rays alternating cream and "
    "vermilion fan out behind.",
    "In the middle, the same neoclassical stock exchange with a pediment carved EXCHANGE, columns, a red vertical "
    "banner BUY on the left and SELL on the right, red flags, angular teal and grey skyscrapers on both sides.",
    "In front, the same six animal characters with exactly the same designs, clothes and poses as the third reference "
    "image, seen from below like monuments: elephant in a dark suit raising its trunk, stern owl in a suit, the tallest "
    "cheetah in the center with a long red scarf flowing, meerkat with crossed arms, fox in a dark suit, green chameleon "
    "in a suit with a curled tail. Their bodies end behind a wide dark teal stone parapet.",
    "The parapet is a plain, flat, very dark teal-green (#0E2A27) stone wall that spans the full width and fills the "
    "bottom 24 percent of the frame, completely empty: no figures, no hands, no text, no ornaments on it, only a subtle "
    "worn stone texture, because text will be printed on it later.",
    "Keep the title and every face at least 6 percent away from the left, right and top edges.",
    "No other text besides 我不是韭菜！, I'M NOT A LEEK!, EXCHANGE, BUY and SELL.", NO,
])

SPECIES = {
    "cheetah": "the cheetah in a dark suit with the long red scarf flowing in the wind, chin raised, looking up to the right",
    "elephant": "the elephant in a dark suit and teal tie, trunk raised proudly",
    "owl": "the stern owl in a dark suit, big amber eyes, arms folded calmly",
    "meerkat": "the meerkat standing upright with crossed arms, ears alert, looking sharply to the side",
    "fox": "the fox in a dark suit, sly confident half smile, one eyebrow raised",
    "chameleon": "the green chameleon in a teal suit with its curled tail, one eye rolled sideways",
    "beaver": ("a new character in exactly the same style as the other six: a sturdy beaver in a dark suit with rolled-up "
               "sleeves and a mustard hard hat, holding a big wrench over its shoulder, buck teeth, determined grin"),
}


def sticker(desc):
    return " ".join([
        "Square artwork for a round sticker, seen straight-on, flat 2D.", STYLE,
        f"A heroic head-and-shoulders portrait of {desc}, matching the character design in the reference images, "
        "seen slightly from below, centered, the whole head and shoulders fitting inside the central circle that is "
        "72 percent of the image width. Behind it, filling the whole square to all four edges, a flat graphic backdrop "
        "of tall cream stone exchange columns and angular deep teal and slate skyscrapers under a warm mustard sky. "
        "Absolutely no sunburst, no radial rays, no rays of any kind. The lower fifth of the square is a plain dark "
        "teal band.",
        "No text, no letters.", NO,
    ])


SLOGAN = " ".join([
    "Square artwork for a round protest-badge sticker, seen straight-on, flat 2D.", STYLE,
    "A round emblem filling the square: a thick near-black green ring, inside it a flat warm mustard field with a "
    "fine halftone dot texture; absolutely no sunburst, no radial rays. In "
    "the center, a single stalk of Chinese chive (a bundle of long flat green leaves with a white base) is crossed out "
    "by a bold vermilion diagonal slash like a prohibition sign. Across the lower half, the heavy chunky distressed "
    "hand-lettered title 我不是韭菜！ in near-black green on a cream banner, letterforms matching the second reference "
    "image. Exactly these five Chinese characters and the exclamation mark, no other text.", NO,
])


def task(id_, label, size, prompt, refs, count=1, **extra):
    return {"id": f"v10_{id_}", "label": label, "size": size, "prompt": prompt, "ref": refs, "count": count,
            **MODEL, **extra}


POSTER_ROWS = [task("poster", "主视觉 · 竖版（引流卡 / 海报）", "2400x3392", POSTER, [LID, TITLE_REF, CAST_REF], count=2)]
ROWS = [task(f"st_{k}", f"贴纸 · {k}", "2048x2048", sticker(v), [CAST_REF, LID]) for k, v in SPECIES.items()]
ROWS += [task("st_slogan", "贴纸 · 我不是韭菜", "2048x2048", SLOGAN, [LID, TITLE_REF], count=2)]


def main():
    out = HERE / "promo-v10.jsonl"
    rows = POSTER_ROWS + ROWS
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(rows), "tasks", sum(r["count"] for r in rows), "images")


if __name__ == "__main__":
    main()
