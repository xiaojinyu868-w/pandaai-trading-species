"""第十一轮：物种贴纸重画。v10b 的人物和柱廊背景同色同纹理，轮廓被吃掉，几款也分不出来。

这次只出透明底的半身像；底色、描边、投影由 print/build_promo.py 合成，每个物种一个专属底色。

输出：promo-v11.jsonl（给 run_parallel.py）
"""

import json
from pathlib import Path

from build_promo_v10 import CAST_REF, LID, MODEL, NO, SPECIES

HERE = Path(__file__).parent

STYLE = (
    "Same character design and retro propaganda-poster illustration style as the reference images: bold flat shapes, "
    "strong dark outlines, clear light and shadow, worn print texture inside the figure only."
)


def bust(desc):
    return " ".join([
        "A single sticker character cut-out on a fully transparent background.", STYLE,
        f"Head-and-shoulders bust of {desc}, facing three-quarters toward the viewer, a strong readable silhouette "
        "with crisp clean edges, the whole head (ears, horns, trunk, hat included) inside the frame with a small "
        "margin, the bust cut off flat at the bottom edge of the image. Large expressive face, high contrast between "
        "the character and its clothes.",
        "Nothing behind the character: no background, no scenery, no buildings, no ground, no shadow, no frame, no "
        "circle, no text.", NO,
    ])


ROWS = [{"id": f"v11_{k}", "label": f"贴纸人物 · {k}", "size": "2048x2048", "prompt": bust(v), "ref": [CAST_REF, LID],
         "count": 2, "background": "transparent", **MODEL} for k, v in SPECIES.items()]


def main():
    out = HERE / "promo-v11.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
