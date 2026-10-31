"""风格样张 v4：以“像素报社经营”参考图为主，重做整套桌游呈现，每行 3 种画风并排供挑选。

行（物料）：主地图、盒子封面、名场面盲测面、名场面揭幕面、证据牌、委托单、物种档案、任务电报。
列（画风）：甲 像素风 / 乙 像素画 + 实物纸张 / 丙 报纸版画风。
不再使用《西区》参考图；角色和场景内容用我们自己的 v2 出图做参考。

输出：
  style-samples-v4.jsonl         带 id，留档用（id 形如 v4_r01_map__a）
  style-samples-v4.submit.jsonl  去掉 id，直接给 vmc image batch --file
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
K = json.loads((HERE / "refs" / "vmc_ref_keys.json").read_text(encoding="utf-8"))

DESK = K["ref6a_pixel_newsroom_desk.png"]
FACTORY = K["ref6b_pixel_newsroom_factory.png"]
OWN_LINEUP = K["own_lineup"]
OWN_ROOM2015 = K["own_room2015"]

MODEL = {"model": "gpt", "version": "gpt-image-2.5-flare", "quality": "high"}

STYLES = {
    "a": (
        "Style: detailed 2D pixel art in the manner of modern narrative management games, following the "
        "first reference image: a crisp, consistent pixel grid, careful dithering, no blur, chunky pixel "
        "typography for the Chinese text. Every interface element is a physical paper object (newspaper, "
        "letter, telegram, ledger page, ticket, rubber stamp, paper clip) with torn edges and small drop "
        "shadows. Warm limited palette: sepia brown, cream paper, muted brick red, deep teal, mustard, ink "
        "black."
    ),
    "b": (
        "Style: crisp pixel art pictures printed on realistic paper, following the first reference image "
        "for the pixel pictures: the illustrations inside the documents are pixel art, while the paper "
        "itself is real (aged newsprint fibres, letterpress ink spread, folds, a faint coffee ring) and all "
        "typography is sharp, clean Chinese print type: a bold Song serif for headlines and a typewriter "
        "style for small text. Warm limited palette: sepia brown, cream paper, muted brick red, deep teal, "
        "mustard, ink black."
    ),
    "c": (
        "Style: vintage newspaper illustration, not pixel art: fine ink engraving lines and halftone dot "
        "shading like early twentieth-century newspapers, printed in a few inks (black, brick red, deep "
        "teal, mustard) on cream newsprint, bold Song serif Chinese headlines and a classic editorial layout "
        "with column rules. Use the first reference image only for the idea of layered paper documents."
    ),
}

STYLE_NAMES = {"a": "甲 像素风", "b": "乙 像素画 + 实物纸张", "c": "丙 报纸版画风"}

LIGHT = (
    "Composition and light: one clear focal point, layered overlapping elements arranged on a diagonal, "
    "generous darker negative space; warm desk-lamp light from the upper left forms a golden pool on the "
    "focal area and falls off into deep brown shadow at the edges. Characters and the key paper are "
    "brighter and higher in contrast than their background, so they stand clearly apart from it."
)

CARD = (
    "The image is the flat face of one printed board game card filling the whole frame edge to edge: no "
    "table around it, no hands, no perspective. Dramatic lighting and contrast apply inside the card's "
    "picture panel."
)

TEXT = (
    "Render every quoted string exactly as written, in simplified Chinese with correct strokes. Apart from "
    "the quoted strings, do not write any words, letters or digits; show any other body text as plain "
    "horizontal line marks. No logos, no brand names, no watermark, no pandas, no real people. Where a QR "
    "code space is requested, leave a completely empty white square with a thin dark border; never draw a "
    "QR pattern."
)

ROWS = [
    {
        "row": "r01_map",
        "label": "主地图",
        "size": "2048x2048",
        "card": False,
        "refs": [DESK, FACTORY],
        "body": (
            "A square board game board seen from directly above, structured like a classic property-trading "
            "board game but set in a small market town. Four streets form a square loop track around the edge "
            "of the board, one street per season, each lined with small spaces drawn as tiny shopfronts facing "
            "the track. Top street '春 · 入场': fresh green, blossom trees, morning light. Right street "
            "'夏 · 狂热': brick red, summer heat, crowds. Bottom street '秋 · 松动': mustard and ochre, "
            "falling leaves. Left street '冬 · 危机': snow, deep teal, glowing night lamps. On every street, "
            "going clockwise: five small numbered spaces labeled '① 补给站', '② 机会', '③ 研究所', "
            "'④ 数据港口', '⑤ 冷静亭', then one large double-width building with two doors labeled '门 A' and "
            "'门 B' and a small stop sign. The four big corner spaces are each labeled '驿站'; the top-left "
            "corner also says '起点'. Small arrows along the track show the clockwise direction. The center of "
            "the board is a lamp-lit editor's desk seen from above, with four marked card slots labeled "
            "'机会牌', '规则牌', '数据港口牌', '补测牌', one larger slot labeled '今日报纸', and a newspaper "
            "masthead in the middle reading '交易物种起源'. Every label must be legible from arm's length."
        ),
    },
    {
        "row": "r02_box",
        "label": "盒子封面",
        "size": "1536x1024",
        "card": False,
        "refs": [DESK, OWN_LINEUP],
        "body": (
            "Board game box lid art, landscape. An editor's desk at night seen from a high angle. In the "
            "foreground, the fox from the second reference image (short trench coat, magnifying glass) leans "
            "over the desk reading a newspaper under a desk lamp, warm rim light on its fur. On the desk: a "
            "stack of old newspapers, a ticker-tape machine spilling paper tape, an inkwell, a rubber stamp, a "
            "cup of coffee. In the darker background, a corkboard where the other six species from the second "
            "reference image (cheetah, elephant, owl, meerkat, chameleon, beaver) appear as small pinned "
            "photos joined by red string. The title is the masthead of the top newspaper: '交易物种起源' with "
            "small English 'THE ORIGIN OF TRADING SPECIES'. A red rubber stamp: '金融史名场面桌游'. A small "
            "paper tag: '1–5 人 · 15–60 分钟'."
        ),
    },
    {
        "row": "r03_scene_blind",
        "label": "名场面牌·盲测面",
        "size": "1024x1536",
        "card": True,
        "refs": [DESK, OWN_ROOM2015],
        "body": (
            "Mystery event card, blind side: the front page of an old newspaper. Masthead '丛林日报' with "
            "small English 'JUNGLE DAILY'. The date line and a few names are covered by thick black redaction "
            "bars. Large headline: '人人都在借钱买的夏天'. A big picture based on the second reference image: a "
            "crowded brokerage trading hall on a hot day, animal investors staring up at a glowing red quote "
            "board, the board's light falling on their faces, deep shadows behind them. A text box with three "
            "short lines: '菜市场里，大家都在聊股票。' '身边有人借了钱，赚得比你多。' '你已经满仓，还借了一倍。'. "
            "A rubber stamp mark: '盲测'. Bottom right: an empty white square with a thin dark border labeled "
            "'扫码开档案'."
        ),
    },
    {
        "row": "r04_scene_reveal",
        "label": "名场面牌·揭幕面",
        "size": "1024x1536",
        "card": True,
        "refs": [DESK, OWN_ROOM2015],
        "body": (
            "Mystery event card, reveal side: an extra-edition newspaper page. Top banner '丛林日报 · 号外'. "
            "Huge headline: '2015 · 杠杆牛与千股跌停'. Dateline: '2015 年 6 月 12 日，上证指数盘中见顶 5178 点'. "
            "A picture based on the second reference image: the same trading hall, now the quote board glows "
            "green (in this game green means down), animals crowd a sell counter whose window is shut, papers "
            "flying. Body text: '此后不到一个月，指数最多跌去三成以上。' and '多个交易日上千只股票跌停，想卖也卖不出去。'. "
            "A boxed note: '借来的钱，会在你最需要时间的时候，逼你离场。'. Small footer: '揭幕后再翻看 · 不构成投资建议'."
        ),
    },
    {
        "row": "r05_evidence",
        "label": "证据牌",
        "size": "1024x1536",
        "card": True,
        "refs": [DESK],
        "body": (
            "Evidence card: a ledger page clipped to a manila folder. Folder tab '档案 · 数据'. A red rubber "
            "stamp '风险类'. Title: '借钱买股票的人，有多少？'. A bar chart drawn on ledger grid paper, bars "
            "rising steadily; the right end of the chart is hidden under a folded paper flap. Chart label: "
            "'融资余额（示意）'. A note: '只含决策日之前看得到的数据'. A small token icon with the text "
            "'花 1 研究点'. Bottom right: an empty white square with a thin dark border labeled '扫码看完整数据'."
        ),
    },
    {
        "row": "r06_order_slip",
        "label": "委托单（选择 + 理由 + 计划）",
        "size": "1024x1536",
        "card": True,
        "refs": [DESK],
        "body": (
            "Decision card: an old brokerage order slip, a printed paper form with a perforated tear-off edge "
            "at the top and a faint blue carbon-copy tint. Header: '委托单' with small English 'ORDER SLIP' and "
            "a small tag '夏 · 名场面'. A line: '你现在：满仓 + 借了一倍'. Section '选一项' with four checkbox "
            "rows: '□ A 再加杠杆 ●●●', '□ B 保持不动 ●●○', '□ C 还掉借款 ●○○', '□ D 全部卖出 ○○○'. Section "
            "'理由（勾一个）' with six small checkboxes: '量价' '数据' '消息' '跟别人' '直觉' '看不懂'. Section "
            "'跌了怎么办' with two checkboxes: '跌了就走' '跌了就加'. A dotted line at the bottom with "
            "'倒数 3 · 2 · 1，一起翻开'."
        ),
    },
    {
        "row": "r07_species_file",
        "label": "物种档案",
        "size": "1024x1536",
        "card": True,
        "refs": [DESK, OWN_LINEUP],
        "body": (
            "Species card: a personnel dossier sheet with a portrait photo paper-clipped at the top right. "
            "The portrait is the fox from the second reference image (short trench coat, magnifying glass), "
            "dramatically lit by a desk lamp. Header: '物种档案' with small English 'SPECIES FILE'. Big name "
            "'狐狸' with small 'FOX'. Tagline: '先怀疑，再检验'. Two rows: '常做的事：先翻历史统计，愿意把想法写成规则' "
            "and '要留意：规则写多了，会错过简单的机会'. A slanted rubber stamp: '初判 · 还需要更多场景'. Bottom: "
            "'下一站：因子评估 · 入门' and an empty white square with a thin dark border labeled '扫码看完整画像'."
        ),
    },
    {
        "row": "r08_task_telegram",
        "label": "任务电报（下一站）",
        "size": "1536x1024",
        "card": True,
        "refs": [DESK],
        "body": (
            "Task card, landscape: a telegram form lying across an envelope with a red wax seal. Telegram "
            "header '任务电报' with small English 'TELEGRAM'. Big text: '下一站：因子评估 · 入门'. Rows: "
            "'约 10 分钟', '因为你：先看历史统计，还用了一条自己的规则', '去做：用沪深 300 的历史数据，检验一个你相信的规律'. "
            "A small grey tag: '示例资源'. On the envelope: an empty white square with a thin dark border "
            "labeled '扫码前往'."
        ),
    },
]


def build():
    tasks = []
    for row in ROWS:
        for key, style in STYLES.items():
            parts = [row["body"], style, LIGHT]
            if row["card"]:
                parts.insert(0, CARD)
            parts.append(TEXT)
            tasks.append(
                {
                    "id": f"v4_{row['row']}__{key}",
                    "size": row["size"],
                    "count": 1,
                    "prompt": " ".join(parts),
                    "ref": row["refs"],
                    **MODEL,
                }
            )
    return tasks


def main():
    tasks = build()
    with open(HERE / "style-samples-v4.jsonl", "w", encoding="utf-8") as archive, open(
        HERE / "style-samples-v4.submit.jsonl", "w", encoding="utf-8"
    ) as submit:
        for t in tasks:
            archive.write(json.dumps(t, ensure_ascii=False) + "\n")
            submit.write(json.dumps({k: v for k, v in t.items() if k != "id"}, ensure_ascii=False) + "\n")
    print(f"{len(tasks)} tasks, {sum(t['count'] for t in tasks)} images")


if __name__ == "__main__":
    main()
