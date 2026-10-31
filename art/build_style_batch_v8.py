"""第八轮：P1 两个名场面（秋门 B 量化踩踏、冬门 B 原油宝）的盲测图和揭幕图，共 4 张。

沿用第七轮的风格块；参考图用定稿的红风筝海报、物种群像，以及同季的 v6 盲测图（保证同一季的光线和色调）。
输出：style-samples-v8.jsonl（给 run_parallel.py）
"""

import json
from pathlib import Path

from build_style_batch_v7 import CHARACTERS, KITE, LINEUP, MEANING, MODEL, NO_TEXT, SCENE_CARD, STYLE, v6

HERE = Path(__file__).parent


def task(id_, label, prompt, refs):
    return {"id": f"v8_{id_}", "label": label, "size": "1024x1536", "prompt": prompt, "ref": refs, "count": 1, **MODEL}


AUTUMN = v6("scene_autumn_moutai")
WINTER = v6("scene_winter_2020")

ROWS = [
    task("squant_blind", "量化踩踏 · 盲测", " ".join([
        SCENE_CARD,
        "Scene: autumn. Hundreds of identical small wind-up tin robots march in perfect lockstep in one long line across a "
        "golden autumn valley, all carrying the same small red flag, on a single narrow wooden plank bridge over a deep gorge. "
        "In the foreground a fox in a trench coat holds the key of her own wind-up robot, looking back uneasily at the endless "
        "identical line behind; the plank bends under the weight. Exaggerated sense of crowding and sameness; the bridge is the "
        "narrow exit.", MEANING, CHARACTERS, STYLE, NO_TEXT]), [KITE, LINEUP, AUTUMN]),
    task("squant_reveal", "量化踩踏 · 揭幕", " ".join([
        SCENE_CARD,
        "Scene: autumn, a moment later. The narrow plank bridge has jammed: the identical wind-up robots pile up and tumble "
        "into a chaotic heap at the single narrow exit, flags flying; at the same time, on the far side, a few animals calmly "
        "climb back up a rope ladder into warm light, hinting at a sharp rebound. Dramatic diagonal composition, falling "
        "autumn leaves.", MEANING, CHARACTERS, STYLE, NO_TEXT]), [KITE, LINEUP, AUTUMN]),
    task("soil_blind", "原油宝 · 盲测", " ".join([
        SCENE_CARD,
        "Scene: winter harbor at dusk. A long excited queue of animals in winter coats lines up on an icy pier to buy shiny "
        "black oil barrels at a tiny bargain stall, many already carrying barrels like treasure; behind them the harbor "
        "tanks and storage yard are completely full, barrels stacked sky-high, a cargo ship waiting with nowhere to unload. "
        "A small calm owl stands aside reading a long scroll of fine print.", MEANING, CHARACTERS, STYLE, NO_TEXT]),
        [KITE, LINEUP, WINTER]),
    task("soil_reveal", "原油宝 · 揭幕", " ".join([
        SCENE_CARD,
        "Scene: winter harbor, the next morning. The ice under the pier has cracked open and the shiny black barrels sink "
        "below the waterline into dark freezing water, dragging the frozen price-board pole down past the water surface; "
        "the animals who bought them are stranded on drifting ice floes, shocked; the owl stands on solid ground holding the "
        "fine-print scroll. Exaggerated sense of falling below zero.", MEANING, CHARACTERS, STYLE, NO_TEXT]),
        [KITE, LINEUP, WINTER]),
]


def main():
    out = HERE / "style-samples-v8.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in ROWS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(out, len(ROWS), "tasks", sum(r["count"] for r in ROWS), "images")


if __name__ == "__main__":
    main()
