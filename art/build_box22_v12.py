"""第十二轮：22×22×6.6 cm 现成盒子贴纸 demo 的盒盖顶面（方图）。

以用户 16:38 发的竖版定稿为锚点（标题、交易所、六个物种、复古宣传画），
去掉标题后面的红白放射线（避免像旭日旗），换成上涨的阶梯柱状天际线，外加一圈细金色装饰艺术边框。
字直接画；侧面和盒底的字由 print/build_box22.py 排。

输出：box22-v12.jsonl（给 run_parallel.py）
"""

import json
from pathlib import Path

from build_promo_v10 import CAST_REF, LID, MODEL, TITLE_REF

HERE = Path(__file__).parent
USER_REF = "/root/.cursor/projects/mnt/assets/_______01-a80d2b95-5465-4dc0-9e52-cc6e7dd029ea.jpg"

TOP = " ".join([
    "Flat print-ready square artwork for the top of a board game box lid, full bleed, seen perfectly straight-on, only "
    "the 2D artwork itself: no box, no 3D mockup, no table.",
    "The same retro propaganda-poster illustration as the first reference image, but more refined and premium: bold flat "
    "shapes, aged paper grain, fine halftone and worn ink texture, palette of warm cream, vermilion, terracotta, mustard, "
    "deep teal, slate blue-grey and near-black green ink, with a few antique-gold accents.",
    "Top third: the same huge, heavy, chunky, slightly distressed hand-lettered title 我不是韭菜！ in near-black green on "
    "one line, letterforms matching the third reference image, and directly below it the small serif line "
    "I'M NOT A LEEK! centered.",
    "IMPORTANT: absolutely no sunburst, no radiating rays, no light beams, no rising-sun motif anywhere. The sky behind "
    "the title is a calm flat warm cream with a soft halftone gradient, and behind the exchange rises a stepped skyline "
    "of tall bar-chart columns and candlestick shapes in mustard, terracotta and slate, climbing from left to right like a "
    "rising stock chart.",
    "Middle: the same neoclassical stock exchange with a pediment carved EXCHANGE, columns, a red vertical banner BUY on "
    "the left and SELL on the right.",
    "Front: the same six animal characters with exactly the same designs, clothes and poses as the fourth reference "
    "image, seen from below like monuments: elephant in a dark suit raising its trunk, stern owl, the tallest cheetah in "
    "the center with a long red scarf, meerkat with crossed arms, fox in a dark suit, green chameleon in a suit with a "
    "curled tail; they stand behind a dark teal stone parapet along the bottom edge.",
    "A thin antique-gold art-deco double-line frame runs around the whole image about 4 percent inside the edges, with "
    "small stepped corner ornaments.",
    "Keep the title, the English line and every face at least 9 percent away from each edge, because the edges wrap "
    "around the box. No other text, no numbers, no logos, no real brands, no pandas, no real people, no QR code.",
])

ROWS = [{"id": "v12_box22_top", "label": "22 cm 盒盖顶面", "size": "2880x2880", "prompt": TOP,
         "ref": [USER_REF, LID, TITLE_REF, CAST_REF], "count": 3, **MODEL}]


def main():
    out = HERE / "box22-v12.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
