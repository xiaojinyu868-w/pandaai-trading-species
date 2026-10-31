"""第十二轮：易拉宝重做，游园会展板的明亮画风，角色用展位上那 7 个 3D 手办（3d/figurines/*/preview.png）。

不要放射线、旭日、大红圆这类会让人联想到旭日旗的东西，也不要宣传画风格。
1536×3536（1:2.3）：画面铺满 80 cm 宽，下面再由 promo/banner 的代码接一条约 15 cm 的深青色底边给底座；
二维码位置留空白方块，顶部深青色带留给代码贴赛道名。

输出：banner-v12.jsonl（给 run_parallel.py）
"""
import json
from pathlib import Path

from build_style_batch_v7 import MODEL

HERE = Path(__file__).parent
FIGS = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
REF = [str(HERE.parent / f"3d/figurines/{k}/preview.png") for k in FIGS]

INTRO = (
    "Vertical roll-up banner for a friendly booth at a fair, designed as a clear, modern, premium infographic poster: "
    "bright, warm, inviting and airy, lots of whitespace, strong visual hierarchy, very few words, every word big "
    "enough to read from three meters. Flat front view of the 2D artwork only."
)

CHARS = (
    "the seven 3D figurine characters from reference images 1 to 7, with exactly their designs, clothes, props, "
    "colors and round brown bases: 1 the cheetah in a coral-red track jacket and green track pants holding a "
    "stopwatch; 2 the elephant in a green knit sweater holding a potted sapling; 3 the fox in a mustard trench coat "
    "holding a magnifying glass and a book; 4 the owl in a green waistcoat holding a lantern; 5 the meerkat in a khaki "
    "safari vest with a headset; 6 the green chameleon with a striped scarf, a backpack and a compass, tail curled; "
    "7 the beaver in blue overalls holding a wrench"
)

NAMES = (
    "On the front of each figurine's round base, a small cream label with its Chinese name in dark ink: the "
    "cheetah's says 猎豹, the elephant's 大象, the fox's 狐狸, the owl's 猫头鹰, the meerkat's 狐獴, the chameleon's "
    "变色龙, the beaver's 海狸."
)

STEPS = (
    "step 1, icon of an old newspaper whose headline is hidden under black bars with a small candlestick chart, "
    "label 闯金融史名场面, with a small mustard pill tag 真实历史行情 under the label; step 2, icon of a magnifying "
    "glass over evidence cards and a red rubber stamp, label 看证据，做决定; step 3, icon of a figurine card with a "
    "check mark and an arrow, label 测出物种，领下一步"
)

QR = (
    "QR zone, from 80 to 96 percent of the height: a big white rounded card. On its left, an empty, perfectly blank, "
    "pure white square about 30 percent of the image width with a thin dark outline; a QR code will be printed there "
    "later, so draw nothing at all inside it. On its right, the big bold words 扫码开玩 in dark ink with a thick coral "
    "arrow pointing left to the square, and a round coral sticker badge with cream text 3 分钟."
)

BANDS = (
    "The top 4 percent of the image is a plain solid deep teal (#2D5F6B) band, completely empty. The bottom 4 percent "
    "is a plain solid deep teal (#2D5F6B) band, completely empty. Keep every word and every figure at least 5 percent "
    "away from the left and right edges."
)

NO = (
    "Absolutely no sunburst, no radial rays or stripes, no light beams or spotlights, no rising sun, no big red circle "
    "or red disc behind anything, no starburst shapes, no national flags, no military, political or propaganda "
    "imagery. No logos, no brands, no pandas, no real people, no QR code pattern anywhere. No other text besides "
    "我不是韭菜！, 那你是哪种交易物种？, 猎豹, 大象, 狐狸, 猫头鹰, 狐獴, 变色龙, 海狸, 闯金融史名场面, 真实历史行情, "
    "看证据，做决定, 测出物种，领下一步, 扫码开玩, 3 分钟 and the numbers 1 to 3."
)

TOY = " ".join([
    INTRO,
    "Style: a soft, polished 3D toy-render poster, like a premium collectible-figure showcase: matte vinyl and clay "
    "materials, soft even studio light with gentle shadows, warm cream (#F6EEDC) background with a few floating "
    "rounded shapes and tiny candlestick-chart confetti in coral red (#E0533D), deep teal (#2D5F6B), sunny yellow "
    "(#F3C94F) and soft mint.",
    BANDS,
    "Title zone, from 4 to 20 percent: the big chunky rounded 3D lettering 我不是韭菜！ in coral red with a cream "
    "outline and a soft drop shadow, slightly bouncy and playful; below it a deep teal rounded pill with big cream "
    "lettering 那你是哪种交易物种？",
    f"Figure zone, from 20 to 56 percent: a round two-tier cream and teal display stage like a toy showcase, with {CHARS} "
    "standing on it in two rows, four in the back and three in the front, all facing the viewer and fully visible. In "
    "the center front, a closed mystery gift box in coral and cream with a big yellow question mark, as if one more "
    "figure is hidden inside. " + NAMES,
    f"Steps zone, from 56 to 80 percent: three rounded white cards stacked vertically and joined by a dotted coral "
    f"path, each card with a big coral number, a small 3D icon and a short big label: {STEPS}.",
    QR, NO,
])

FLAT = " ".join([
    INTRO,
    "Style: a clean, modern flat vector infographic with bold rounded shapes and thick friendly outlines, like a "
    "well-designed science-museum exhibition board; the figurines appear as crisp cut-out 3D renders exactly as in "
    "the references, with soft shadows; warm cream (#F6EEDC) background with large solid color blocks in deep teal "
    "(#2D5F6B), coral red (#E0533D), sunny yellow (#F3C94F) and soft mint.",
    BANDS,
    "Title zone, from 4 to 20 percent: the huge heavy rounded lettering 我不是韭菜！ in dark ink (#2A2A1C) with a thick "
    "coral underline swoosh; below it a sunny yellow rounded tag with big dark lettering 那你是哪种交易物种？",
    f"Figure zone, from 20 to 56 percent: a large deep teal rounded panel; on a simple cream floor line inside it, "
    f"{CHARS}, standing side by side in a gentle arc like a character lineup chart, all facing the viewer and fully "
    "visible; in the middle of the lineup, a big sunny yellow rounded tile with a dark question mark. " + NAMES,
    f"Steps zone, from 56 to 80 percent: three big coral numbered circles stacked vertically and joined by a thick "
    f"dashed teal line, each with a simple flat icon and a short big label beside it: {STEPS}.",
    QR, NO,
])

MAP = " ".join([
    INTRO,
    "Style: a cheerful illustrated fairground map in soft 3D clay style seen from a high three-quarter angle, like a "
    "cute board-game map; warm cream (#F6EEDC) ground, soft mint lawns, small trees, colorful triangular bunting "
    "flags in coral red, deep teal, sunny yellow and cream strung across the top; soft even daylight.",
    BANDS,
    "Title zone, from 4 to 20 percent: 我不是韭菜！ as big chunky rounded coral lettering on a wide wooden fair sign "
    "on two posts; under the sign, a deep teal ribbon with big cream lettering 那你是哪种交易物种？",
    "Map zone, from 20 to 80 percent: one winding path of square board-game tiles snakes down the banner through "
    "three small fair booths with striped tents, each booth a numbered stop with a big sign: stop 1, a newspaper kiosk "
    "whose headline is hidden under black bars with a small candlestick chart, sign 闯金融史名场面, with a small "
    "mustard pill tag 真实历史行情; stop 2, a detective desk with a big magnifying glass, evidence cards and a red "
    "rubber stamp, sign 看证据，做决定; stop 3, a little stage at the bottom of the path where "
    f"{CHARS} stand in a row facing the viewer, big and fully visible, next to a closed mystery gift box with a big "
    "yellow question mark, sign 测出物种，领下一步. " + NAMES,
    QR, NO,
])


def task(id_, label, prompt, count=2):
    return {"id": f"v12_{id_}", "label": label, "size": "1536x3536", "prompt": prompt, "ref": REF, "count": count,
            **{**MODEL, "quality": "xhigh"}}


ROWS = [
    task("banner_toy", "易拉宝 · 3D 潮玩展台", TOY),
    task("banner_flat", "易拉宝 · 清爽扁平信息图", FLAT),
    task("banner_map", "易拉宝 · 游园会地图", MAP),
]


def main():
    out = HERE / "banner-v12.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
