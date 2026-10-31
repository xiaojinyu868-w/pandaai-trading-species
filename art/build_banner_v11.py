"""第十一轮：易拉宝（80×200 cm）整张信息图，画风跟盒标定稿（「我不是韭菜！」复古宣传画）一致。

字少、图大、3 米外看得懂。二维码位置留一块空白方块，顶部和底部各留一条空的深墨绿色带，
二维码、赛道名、合规小字由 promo/banner 的代码贴上去。
1536×3840 是 1:2.5 下的最大尺寸（总像素上限 8,294,400）。

输出：banner-v11.jsonl（给 run_parallel.py）
"""
import json
from pathlib import Path

from build_style_batch_v7 import MODEL

HERE = Path(__file__).parent
REFS = HERE / "refs"
ANCHOR, TITLE_REF, CAST_REF = (str(REFS / f"box_anchor_{n}.jpg") for n in ("artist", "title", "cast"))
LID = str(HERE / "vmc-output/box-v9/v9_box_lid_x/img_50672/ai_generate_50672_2.png")
REF = [ANCHOR, TITLE_REF, CAST_REF, LID]

STYLE = (
    "The same retro constructivist propaganda-poster style as the reference images: heroic low angle, bold flat shapes, "
    "aged paper grain, fine halftone and worn ink texture, palette of warm cream, vermilion red, terracotta orange, "
    "mustard, deep teal, slate blue-grey and near-black green ink."
)

HEAD = " ".join([
    "Flat print-ready vertical roll-up banner designed as a clear infographic, full bleed, seen straight-on, only the 2D "
    "artwork. Very little text, every word big and readable from three meters, bold simple icons, generous spacing, "
    "large clear zones from top to bottom.",
    STYLE,
    "Zone 1, the top 4.5 percent: a plain flat very dark teal-green (#0E2A27) band, completely empty, no text.",
    "Zone 2, the next 15 percent: the huge, heavy, chunky, slightly distressed hand-lettered title 我不是韭菜！ on one "
    "line in near-black green ink, filling the width, letterforms matching the second reference image; a small dark "
    "serif line I'M NOT A LEEK! under the right end of the title; cream and vermilion sunburst rays behind.",
    "Zone 3, right below: a vermilion ribbon banner across the width with big cream lettering 那你是哪种交易物种？",
])

CAST = ("the same six animal characters with exactly the same designs and clothes as the third reference image: the "
        "cheetah with a long red scarf, the elephant in a dark suit, the stern owl in a suit, the meerkat with crossed "
        "arms, the fox in a dark suit, the green chameleon in a suit with a curled tail")

QR = " ".join([
    "Next zone, about 12.5 percent: a big cream paper card. On its left, an empty, perfectly blank, pure white rounded "
    "square about 32 percent of the banner width, with a thin dark border; a QR code will be printed there later, so "
    "draw nothing at all inside it. On its right, the big hand-lettered words 扫码开玩 in near-black green with a thick "
    "vermilion arrow pointing left to the white square, and a vermilion starburst badge with cream text 3 分钟.",
    "Last zone, the bottom 12.5 percent: a plain flat very dark teal-green (#0E2A27) band, completely empty, no text.",
    "Keep every word and every face at least 5 percent away from the left and right edges.",
    "No logos, no real brands, no pandas, no real people, no QR code pattern anywhere.",
])

A = " ".join([
    HEAD,
    "Zone 4, about 27 percent: the same neoclassical stock exchange as the first reference image (pediment carved "
    "EXCHANGE, columns, red vertical banners BUY and SELL, red flags, angular teal and grey skyscrapers), and in front "
    f"of it, seen from below like monuments, {CAST}; the cheetah is the tallest, in the center. At the right edge, one "
    "dark mysterious animal silhouette with a big glowing mustard question mark on it, a hidden seventh species. "
    "Below each of the six animals, a small cream name plate with its name in dark ink: 猎豹, 大象, 猫头鹰, 狐獴, 狐狸, 变色龙.",
    "Zone 5, about 23 percent: one thick winding board-game track of stone tiles snakes down the banner and connects "
    "four large round medallions in order, each with a big number and one bold flat icon, and a short big label "
    "beside it: medallion 1, icon of an old newspaper whose headline and date are hidden under black redaction bars "
    "with a small candlestick chart, label 闯金融史名场面; medallion 2, icon of a magnifying glass over evidence cards "
    "and a red rubber stamp, label 看证据，做决定; medallion 3, icon of a portrait card of a fox with three check marks, "
    "label 测出你的物种; medallion 4, icon of a signpost arrow and a ticket, label 领你的下一步.",
    QR,
    "No other text besides 我不是韭菜！, I'M NOT A LEEK!, 那你是哪种交易物种？, EXCHANGE, BUY, SELL, 猎豹, 大象, 猫头鹰, "
    "狐獴, 狐狸, 变色龙, 闯金融史名场面, 看证据，做决定, 测出你的物种, 领你的下一步, 扫码开玩, 3 分钟 and the numbers 1 to 4.",
])

B = " ".join([
    HEAD,
    "Zone 4, about 30 percent: a big round species wheel like a personality-test dial. In its center, a large playing "
    "card lying face down with a big mustard question mark. Around it in a ring, six round sunburst portrait "
    f"medallions of {CAST}, each medallion with a small cream name plate below it: 猎豹, 大象, 猫头鹰, 狐獴, 狐狸, 变色龙. "
    "Behind the wheel, the same neoclassical stock exchange with the pediment carved EXCHANGE, and angular teal and "
    "grey skyscrapers.",
    "Zone 5, about 20 percent: three big round icons in a vertical zig-zag, connected by thick dashed vermilion "
    "arrows, each with a big number and a short big label beside it: 1, icon of an old newspaper whose headline and "
    "date are hidden under black redaction bars with a small candlestick chart, label 闯金融史名场面; 2, icon of a "
    "magnifying glass over evidence cards and a red rubber stamp, label 看证据，做决定; 3, icon of a fox portrait card "
    "with a signpost arrow, label 测出物种，领下一步.",
    QR,
    "No other text besides 我不是韭菜！, I'M NOT A LEEK!, 那你是哪种交易物种？, EXCHANGE, 猎豹, 大象, 猫头鹰, 狐獴, 狐狸, "
    "变色龙, 闯金融史名场面, 看证据，做决定, 测出物种，领下一步, 扫码开玩, 3 分钟 and the numbers 1 to 3.",
])


def task(id_, label, prompt, count=2):
    return {"id": f"v11_{id_}", "label": label, "size": "1536x3840", "prompt": prompt, "ref": REF, "count": count,
            **{**MODEL, "quality": "xhigh"}}


ROWS = [task("banner_a", "易拉宝 · A 物种群像 + 四步棋盘路", A), task("banner_b", "易拉宝 · B 物种转盘 + 三步", B)]


def main():
    out = HERE / "banner-v11.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
