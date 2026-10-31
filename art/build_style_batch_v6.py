"""第六轮：按用户选定的第二轮画风（红风筝海报 img_50322）统一出一套物料。

选定画风的长处：一个画面只讲一个比喻，大面积天空，小人物对大场景，强对角线，
主体用饱和的强调色压在平静的背景上，阳光方向清楚。
参考图只用我们自己第二轮的图：own_magazine（红风筝海报）定画风，own_lineup（物种群像）定角色。
画面里不写字，标题和数字之后由代码排版。

输出：style-samples-v6.jsonl（含 id、label，给 run_parallel.py 用）
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
K = json.loads((HERE / "refs" / "vmc_ref_keys.json").read_text(encoding="utf-8"))
KITE, LINEUP, BOARD = K["own_magazine"], K["own_lineup"], K["own_board"]

MODEL = {"model": "gpt", "version": "gpt-image-2.5-flare", "quality": "high", "count": 1}

STYLE = (
    "Art style: retro-modernist graphic illustration in the spirit of mid-century travel posters: large flat color "
    "blocks, simplified geometric architecture, faceted landscape shapes, subtle digital gouache brush strokes and fine "
    "print grain, crisp clean edges, clear warm sunlight. Limited palette: warm cream, brick red, terracotta orange, "
    "mustard yellow, olive and sage green, deep forest green, deep teal blue, sky blue, dark espresso brown. "
    "Follow the first reference image closely for rendering style, palette, texture and level of detail."
)

COMPOSITION = (
    "Compose it like a great poster: one single bold visual idea, small figures against a vast landscape and a large "
    "calm sky, a strong diagonal or leading line, the key object in a saturated accent color against calmer "
    "surroundings, a clear light direction with soft long shadows."
)

CHARACTERS = (
    "The animal characters match the second reference image: same species designs, clothes and proportions."
)

NO_COPY = (
    "Do not draw any kite, and do not reuse the hilltop, the town, the sun or the layout of the first reference image."
)

NO_TEXT = (
    "No text, no letters, no numbers, no logos, no brand marks, no signage lettering, no watermark, no pandas, "
    "no real people."
)

SCENE_CARD = (
    "Vertical cover illustration for a board game event card, with the same layout as the first reference image: a "
    "plain solid cream band at the top above a thin mustard stripe, left completely blank for a title added later; "
    "below it a full-width poster illustration; a small blank rectangular tag in the bottom-right corner."
)

SPECIES_CARD = (
    "Vertical character card illustration for a board game: a full-width poster illustration, and at the bottom a "
    "plain solid cream band below a thin mustard stripe, left completely blank for the name added later. "
    "The character is the clear hero of the image, but still small enough to show its world around it."
)


def task(id_, label, size, prompt, refs, count=1):
    return {"id": f"v6_{id_}", "label": label, "size": size, "prompt": prompt, "ref": refs, **MODEL, "count": count}


def scene(id_, label, body, copy_ok=False):
    parts = [SCENE_CARD, body, CHARACTERS, STYLE, COMPOSITION, NO_TEXT]
    if not copy_ok:
        parts.insert(5, NO_COPY)
    return task(id_, label, "1024x1536", " ".join(parts), [KITE, LINEUP])


def species(id_, label, body):
    return task(id_, label, "1024x1536", " ".join([SPECIES_CARD, body, CHARACTERS, STYLE, COMPOSITION, NO_COPY, NO_TEXT]),
                [KITE, LINEUP])


TASKS = [
    scene("scene_spring_924", "春 · 924 盲测面",
          "The scene (spring, everyone enters the market): a bright spring morning over a modern hillside town full of "
          "blossoming trees. One single long queue of tiny animals winds like a ribbon across the whole landscape, over a "
          "bridge, along terraces and down the streets, all the way to one small glowing doorway in a modern white "
          "building at the bottom. Many of them hold glowing smartphones; more animals run from distant hills to join the "
          "end of the queue. A few festive red flags along the route. The queue draws a big S-shaped leading line. Mood: "
          "excitement, hope and a slightly absurd rush. Dominant sage green, soft blossom pink and cream with festive red "
          "accents."),
    scene("scene_summer_2015_reveal", "夏 · 2015 揭幕面",
          "The same place and moment as the first reference image, a few seconds later: this is the reveal side of that "
          "card. The giant arrow-shaped kite has flipped nose-down and turned dull green (in China green means falling), "
          "torn, plunging toward the town; most strings have snapped and whip through the air; the animals on the hilltop "
          "tumble backward and fall over each other; the dark storm clouds from the horizon now cover half the sky and "
          "slanting rain begins over the town; the sun is hidden. Keep the same layout as the reference.",
          copy_ok=True),
    scene("scene_autumn_moutai", "秋 · 茅台 盲测面",
          "The scene (autumn, the crowd starts to loosen): a golden autumn valley. In the middle rises one tall, narrow "
          "rock pillar, and on its small flat top a tight crowd of animals in dark business suits huddle shoulder to "
          "shoulder, eyes closed and smiling, all hugging one large plain white porcelain liquor bottle with no label. A "
          "strong autumn wind sweeps orange leaves across the sky; thin cracks run down the pillar; a lone fox on a nearby "
          "hill watches with a notebook. Mood: comfortable luxury with a growing crack of unease. Dominant mustard, ochre "
          "and espresso with a deep teal sky."),
    scene("scene_winter_2020", "冬 · 2020 熔断 盲测面",
          "The scene (winter, crisis): a snowy mountain valley at dusk in a blizzard. A long cable-car line crosses the "
          "valley high above a frozen river, and every cabin has stopped dead in mid-air, swaying in the wind; tiny "
          "animals inside press against the windows. Below, the lights of a small modern town switch off district by "
          "district. At the top station one amber warning lamp glows. Mood: tense silence, everyone holding their breath. "
          "Dominant deep teal blue, slate and cream with one amber accent."),
    species("species_cheetah", "猎豹 · 看量价",
            "The cheetah in the retro windbreaker surfs a huge curling ocean wave at full speed along a sunny coast, "
            "crouched low on a surfboard, timing the wave with its stopwatch; the wave forms a big rising diagonal; a "
            "lighthouse and a small coastal town far behind. Mood: thrill and speed, riding the momentum. Dominant teal, "
            "sky blue and terracotta."),
    species("species_elephant", "大象 · 看数据",
            "The elephant in the knitted cardigan kneels on a quiet green hill, carefully planting a small sapling; behind "
            "it stands one enormous old tree with a wide canopy that it planted long ago, its shadow covering the hill; "
            "far fields fade through the seasons. Mood: patience and calm. Dominant olive, sage, forest green and cream."),
    species("species_fox", "狐狸 · 先怀疑再检验",
            "The fox in the short trench coat stands on a rocky lookout beside a small surveying tripod, comparing a "
            "hand-drawn map in its notebook with the real valley below, magnifying glass in hand; a few small marker "
            "flags it has placed run along the valley. Morning light. Mood: curiosity and careful checking. Dominant "
            "terracotta, mustard and teal."),
    species("species_owl", "猫头鹰 · 先看清再出手",
            "The owl in the tweed vest and round glasses sits in a small round hilltop observatory at dusk, the dome open, "
            "a brass telescope pointed at the far horizon where a storm is forming far away; it waits calmly with its "
            "lantern; the first stars appear. Mood: patience and judgment. Dominant deep teal, dusk blue and warm mustard "
            "lantern light."),
    species("species_meerkat", "狐獴 · 听消息",
            "The meerkat with the radio headset stands tall on top of a tall radio mast above a busy market town; many "
            "small paper notes and signal lines fly toward it from every direction like flocks of birds; below, a crowd of "
            "small animals looks up at it, waiting for its signal. Mood: alertness and noise. Dominant brick red, sky blue "
            "and cream."),
    species("species_chameleon", "变色龙 · 随市场切换",
            "The chameleon in the striped scarf, brass compass in hand, walks along one long branch that stretches across "
            "the whole image through the four seasons: blossoms on the left, green summer leaves, golden autumn leaves, and "
            "snowy twigs on the right; its skin changes color to match each part of the branch it touches. Mood: "
            "adaptability. The palette moves through all four season colors."),
    species("species_beaver", "海狸 · 隐藏物种",
            "The beaver in work overalls has built a precise wooden water mill and a small dam on a forest river; neat "
            "channels and gears turn the wild river into an even flow that drives the wheel; a blueprint lies unrolled on "
            "a rock beside its wrench. Mood: craft and systems. Dominant forest green, teal and warm wood tones."),
    task("box_kites", "盒子封面 · 七只风筝", "1536x1024",
         " ".join([
             "Board game box lid illustration, landscape. A wide grassy hilltop above a sunny modern town and a sea bay, "
             "under a huge summer sky with big clouds. The seven animal characters stand spread along the hilltop, each "
             "flying its own very different kite in the same strong wind: the cheetah's sleek red racing kite already far "
             "ahead and highest; the elephant's large steady box kite held with both hands; the fox launching a small test "
             "kite while writing in its notebook; the owl sitting calmly with its kite still folded, watching the sky; the "
             "meerkat watching the others' kites through binoculars; the chameleon's kite changing colors; the beaver's "
             "precise engineered kite on a little hand winch. The kites form a rising diagonal across the sky. Leave a "
             "large calm empty area of sky in the upper left for the game title added later. Mood: open and curious, "
             "everyone in the same wind but each in its own way.",
             CHARACTERS, STYLE, COMPOSITION, NO_TEXT]),
         [KITE, LINEUP]),
    task("box_road", "盒子封面 · 四季之路", "1536x1024",
         " ".join([
             "Board game box lid illustration, landscape. A road winds from a hilltop in the foreground through four "
             "seasonal regions toward the far horizon: a spring valley of blossom trees, a hot red-roofed summer town, a "
             "golden autumn forest, and snowy winter mountains at the end. At the start of the road in the foreground, a "
             "small cream-colored egg with a paper ticket tucked into a band sits on a tiny suitcase, looking down the "
             "road: a traveler whose species is not known yet. High in the sky, seven soft clouds faintly take the shapes "
             "of a cheetah, an elephant, a fox, an owl, a meerkat, a chameleon and a beaver. Leave a large calm sky area "
             "for the game title added later.",
             CHARACTERS, STYLE, COMPOSITION, NO_COPY, NO_TEXT]),
         [KITE, LINEUP]),
    task("map_board", "主地图（两张）", "2048x2048",
         " ".join([
             "A square board game board seen from directly above, buildings drawn with a slight axonometric tilt, to be "
             "printed about 50 cm wide. A ring road runs around the edge of the board, and each side of the ring is one "
             "season district: top side spring in sage green with blossom trees, right side summer in brick red and "
             "terracotta rooftops, bottom side autumn in mustard and ochre with falling leaves, left side winter in deep "
             "teal with snowy roofs. Going clockwise from the top-left corner, each side has five evenly spaced square "
             "spaces on the road (cream squares with a bold dark outline, completely blank inside), followed by one large "
             "landmark building that takes two spaces, with two doors side by side (two blank cream door plaques). Each "
             "of the four corners is a small round plaza with a blank round plaque. Small arrows on the road show the "
             "clockwise direction. The center of the board is a calm town square park with five blank rectangular card "
             "slots (four in a row and one larger below) and generous empty space. Flat even lighting, clean shapes, every "
             "plaque and space blank, suitable for print.",
             "Follow the first reference image for how districts, roofs, trees and the road are drawn, and the second "
             "for palette, texture and print grain.",
             NO_TEXT]),
         [BOARD, KITE], count=2),
    task("icons", "图标 · 证据与道具", "1536x1024",
         " ".join([
             "A sheet of twelve small spot illustrations for board game cards and a mobile game interface, arranged in "
             "a neat grid of four columns and three rows on a plain warm cream background with generous spacing, all in "
             "the same style and scale: a smartphone with a speech bubble (news); an open ledger with a small bar chart "
             "(data); a small screen with a candlestick chart (price and volume); a sealed envelope with an owl feather "
             "(a hint); a magnifying glass over a flask (research point); a coin; a pair of dice; a cream egg with a "
             "ticket in a band; a red arrow-shaped kite; an hourglass; a compass; a small wooden water mill. Simple bold "
             "shapes readable at 1 cm.",
             STYLE, NO_TEXT]),
         [KITE]),
]


def main():
    target = HERE / "style-samples-v6.jsonl"
    target.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in TASKS) + "\n", encoding="utf-8")
    print(target, len(TASKS), "tasks", sum(t["count"] for t in TASKS), "images")


if __name__ == "__main__":
    main()
