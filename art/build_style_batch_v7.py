"""第七轮：按定稿画风（红风筝海报）补齐全套插画。

用户要求：卡片首先要表达意思。一张图一个夸张的比喻，主体大、轮廓清楚，
和背景在明暗与颜色上明显分开，一臂远也能看懂。
画面里不写字，标题、数字、二维码之后由代码排版。

输出：style-samples-v7.jsonl（给 run_parallel.py）
"""

import glob
import json
from pathlib import Path

HERE = Path(__file__).parent
K = json.loads((HERE / "refs" / "vmc_ref_keys.json").read_text(encoding="utf-8"))
KITE, LINEUP = K["own_magazine"], K["own_lineup"]
V6 = HERE / "vmc-output" / "style-v6"
FIGURINE_V2 = str(next((HERE / "vmc-output" / "style-v2").glob("img_50326/*.png")))


def v6(name):
    return str(sorted(glob.glob(str(V6 / f"v6_{name}" / "img_*" / "*.png")))[0])


MODEL = {"model": "gpt", "version": "gpt-image-2.5-flare", "quality": "high"}

STYLE = (
    "Art style: retro-modernist graphic illustration in the spirit of mid-century travel posters: large flat color "
    "blocks, simplified geometric shapes, faceted landscape shapes, subtle digital gouache brush strokes and fine print "
    "grain, crisp clean edges, clear warm sunlight. Limited palette: warm cream, brick red, terracotta orange, mustard "
    "yellow, olive and sage green, deep forest green, deep teal blue, sky blue, dark espresso brown. Follow the first "
    "reference image closely for rendering style, palette, texture and level of detail."
)

MEANING = (
    "Above all, the image must say its meaning at a glance from arm's length: one bold, exaggerated visual metaphor; "
    "the main subject is large, with a strong clear silhouette and a dramatic gesture, clearly separated from a simplified, "
    "calmer, lower-contrast background by value and color; exaggerate scale like a great poster."
)

CHARACTERS = "The animal characters match the second reference image: same species designs, clothes and proportions."

NO_TEXT = (
    "No text, no letters, no numbers, no logos, no brand marks, no signage lettering, no watermark, no pandas, "
    "no real people."
)

SCENE_CARD = (
    "Vertical illustration for a board game event card, with the same layout as the first reference image: a plain "
    "solid cream band at the top above a thin mustard stripe, left blank for a title added later; below it a full-width "
    "poster illustration; a small blank rectangular tag in the bottom-right corner."
)

SPECIES_CARD = (
    "Vertical character card illustration for a board game: a full-width poster illustration, and at the bottom a plain "
    "solid cream band below a thin mustard stripe, left blank for the name added later. The character is the hero: it "
    "fills about two thirds of the image height, seen close and slightly from below, monumental, with a strong rim light; "
    "the landscape behind is simplified into a few large calm shapes."
)

FIGURINE = (
    "A single painted collectible figurine of one stylized anthropomorphic animal character, used as a board game pawn "
    "and to be turned into a 3D-printable model: full body, standing on a simple round base, front three-quarter view, "
    "centered with generous margin. Chunky, simple, rounded, readable shapes; thick limbs, props held close to the body, "
    "no thin, fragile or floating parts, no separate small accessories. Matte hand-painted finish in the flat colors of "
    "the character design. Plain flat light grey studio background, soft even lighting, no cast shadow on the background. "
    "Match the character design of the first reference image and the figurine finish of the second reference image."
)

TILE = (
    "A square spot illustration for one board game space and its card deck back, readable when printed 4 cm wide: one "
    "single bold, exaggerated object or tiny scene centered on a plain warm cream background with generous margin, simple "
    "large shapes, strong silhouette, a few flat colors, soft long shadow. Match the style of the first reference image "
    "and the scale and simplicity of the icons in the second reference image."
)


def task(id_, label, size, prompt, refs, count=1, **extra):
    return {"id": f"v7_{id_}", "label": label, "size": size, "prompt": prompt, "ref": refs, "count": count,
            **MODEL, **extra}


def species(id_, label, body):
    return task(f"species_{id_}", label, "1024x1536",
                " ".join([SPECIES_CARD, body, CHARACTERS, MEANING, STYLE, NO_TEXT]), [KITE, LINEUP])


def figurine(id_, label, body):
    return task(f"figurine_{id_}", label, "1024x1024", " ".join([FIGURINE, body, NO_TEXT]), [LINEUP, FIGURINE_V2],
                background="opaque")


def reveal(id_, label, blind, body):
    return task(f"reveal_{id_}", label, "1024x1536",
                " ".join([SCENE_CARD, body, CHARACTERS, MEANING, STYLE, NO_TEXT]), [KITE, LINEUP, v6(blind)])


def tile(id_, label, body):
    return task(f"tile_{id_}", label, "1024x1024", " ".join([TILE, body, NO_TEXT]), [KITE, v6("icons")])


TASKS = [
    species("cheetah", "猎豹 · 看量价",
            "The cheetah in the retro windbreaker crouches low on a surfboard, riding the crest of a gigantic wave that "
            "rears up into the sky in one steep rising curve like a price line going up, stopwatch held out in one paw, eyes "
            "locked forward, spray and speed streaks behind it. Mood: thrill, speed, riding the momentum."),
    species("elephant", "大象 · 看数据",
            "The elephant in the knitted cardigan sits monumental and calm like a mountain, reading a giant open ledger as big "
            "as a door, its pages showing simple bar charts drawn as shapes; a strong wind blows leaves and tiny scurrying "
            "animals past it, but the elephant does not move at all. Mood: patience, weight, fundamentals."),
    species("fox", "狐狸 · 先怀疑再检验",
            "The fox in the short trench coat holds up a gigantic magnifying glass as big as its own body; through the lens "
            "its one eye looks enormous and skeptical, and the valley behind the lens appears sharp and magnified with a few "
            "small flags marking a tested route; in its other paw a notebook with a ticked checklist drawn as simple marks. "
            "Mood: curiosity and careful checking."),
    species("owl", "猫头鹰 · 先看清再出手",
            "The owl in the tweed vest sits perfectly still on top of a round observatory dome at dusk, seen close and large; "
            "its enormous round glasses reflect a storm far away on the horizon; one wing holds a glowing lantern; birds and "
            "leaves rush past in the wind while it waits. Mood: patience and judgment."),
    species("meerkat", "狐獴 · 听消息",
            "The meerkat with oversized radio headphones stands bolt upright on top of a tall radio mast, ears and whiskers "
            "alert, while hundreds of small paper notes and speech-bubble shapes swirl around it in a huge spiral like a "
            "tornado of news. Mood: alertness, noise, everyone talking."),
    species("chameleon", "变色龙 · 随市场切换",
            "The chameleon in the striped scarf grips a branch with its curled tail, its body clearly divided into four "
            "color zones from head to tail: blossom pink, summer green, autumn gold and winter blue; one huge eye swivels "
            "toward the viewer; it holds a brass compass whose needle is spinning. Mood: adaptability."),
    species("beaver", "海狸 · 隐藏物种",
            "The beaver in work overalls stands proudly on top of a giant, precise machine it has built across a river: a "
            "big wooden and brass water wheel with gears and neat channels that turn a wild, tangled river into straight, "
            "orderly streams; a rolled blueprint under its arm, wrench in paw. Mood: craft, systems, building tools."),
    figurine("cheetah", "猎豹手办", "The cheetah in a sporty retro windbreaker and track pants, holding a stopwatch close to its chest."),
    figurine("elephant", "大象手办", "The elephant in a knitted cardigan, holding a small potted sapling with both hands in front of its belly."),
    figurine("fox", "狐狸手办", "The fox in a short trench coat, holding a chunky magnifying glass against its chest and a thick notebook under its arm; bushy tail resting on the base."),
    figurine("owl", "猫头鹰手办", "The owl in a tweed vest and round glasses, holding a small chunky lantern with both wings in front of it."),
    figurine("meerkat", "狐獴手办", "The meerkat standing tall and alert with a small radio headset, a folded newspaper held flat against its chest; tail resting on the base."),
    figurine("chameleon", "变色龙手办", "The chameleon in a striped scarf, standing upright, its curled tail resting on the base, holding a chunky compass with both hands."),
    figurine("beaver", "海狸手办", "The beaver in work overalls, holding a chunky wrench against its chest, its flat tail resting on the base."),
    reveal("spring_924", "春 · 924 揭幕面", "scene_spring_924",
           "The reveal side of the spring card in the third reference image, a week later: the long queue has finally gone "
           "through the glowing door, and it leads straight onto a gigantic roller coaster towering over the festive town. "
           "The front car, packed with the animals who queued longest, has just tipped over the very top of a steep peak and "
           "is plunging down a near-vertical drop; screaming faces, paws in the air; fireworks burst in the evening sky for "
           "the holiday; far below, a few calm animals who never joined the queue watch from a bench. Mood: euphoria turning "
           "into a sudden drop."),
    reveal("autumn_moutai", "秋 · 茅台 揭幕面", "scene_autumn_moutai",
           "The reveal side of the autumn card in the third reference image, a few weeks later: the tall rock pillar has "
           "cracked through and its top is breaking apart; the huge plain white porcelain bottle tips and falls; the animals "
           "in business suits tumble off in every direction, some still hugging each other; a storm of autumn leaves; the lone "
           "fox on the nearby hill calmly closes its notebook. Mood: the crowd breaking up all at once."),
    reveal("winter_2020", "冬 · 熔断 揭幕面", "scene_winter_2020",
           "The reveal side of the winter card in the third reference image, a few weeks later: the blizzard has cleared, a "
           "huge warm sun rises over the valley, the frozen river cracks open into flowing water, and the cable cars are moving "
           "again, climbing steeply upward toward the sun; the animals who stayed inside cheer at the windows; down in the "
           "snow below, a few animals who jumped out earlier look up. Mood: the panic is over, a sharp rebound."),
    tile("supply", "补给站", "A small supply kiosk with a striped awning and a huge open wooden crate bursting with glowing round tokens that spill out."),
    tile("chance", "机会", "A tall signpost at a fork in the road with two big arrows pointing in opposite directions, and a large coin flipping high in the air above it."),
    tile("research", "研究所", "A small modernist research building with a giant brass microscope rising through its roof like a tower."),
    tile("dataport", "数据港口", "A harbor crane lifting a large shipping container made of a glowing grid of small squares, above a little quay with water."),
    tile("calm", "冷静亭", "A small modern glass shelter with a bench under a tree, a steaming teacup on the bench; strong wind and swirling leaves outside, perfectly calm and still inside."),
    tile("station", "驿站", "A small railway station building with a big round clock on its gable, a mailbox and a bench with a suitcase in front."),
    tile("start", "起点", "A small cream-colored egg with a paper ticket tucked into a band, sitting on a tiny suitcase at the start line of a road, a small flag beside it."),
    task("h5_opening", "H5 开场", "1088x1920",
         " ".join([
             "Vertical 9:16 opening illustration for a mobile game. A huge sky fills the upper two thirds, calm and empty at "
             "the top for a title added later. Seven very different kites rise in the same strong wind in a sweeping diagonal: a "
             "sleek red racing kite far ahead and highest, a large steady box kite, a small test kite, a folded kite still on "
             "the ground, a kite changing colors, a precise engineered kite on a winch, a kite watched through binoculars. At "
             "the bottom, on a grassy hilltop above a four-season valley, a tiny cream egg with a paper ticket in a band sits on "
             "a small suitcase and looks up at the kites; the seven animal characters stand along the ridge, each holding a "
             "kite string. The kites are large and bold against the sky; the egg is tiny.",
             CHARACTERS, MEANING, STYLE, NO_TEXT]),
         [KITE, LINEUP, v6("box_kites")]),
    task("prologue", "序章 · 1720 南海泡沫", "1024x1536",
         " ".join([
             SCENE_CARD,
             "The scene: a harbor town in 1720. Floating above the crowd is a gigantic shimmering soap bubble with a whole "
             "sailing ship inside it, rising into the sky. Elegant animals in 18th-century coats and tricorn hats reach up "
             "with nets, ladders and money bags, climbing over each other to catch it; one edge of the bubble is already "
             "starting to burst into droplets. In the corner, a thoughtful owl in an 18th-century coat holds an apple and a "
             "small telescope, also reaching for the bubble. Mood: a beautiful mania about to pop.",
             CHARACTERS, MEANING, STYLE, NO_TEXT]),
         [KITE, LINEUP]),
    task("board_background", "主地图底图（两张）", "2048x2048",
         " ".join([
             "A square board game board background seen from directly above, buildings with a slight axonometric tilt. A "
             "small fictional town where the four seasons sit side by side around a large calm central plaza: the top edge is "
             "spring with sage-green fields and blossom trees, the right edge is summer with brick-red rooftops, the bottom edge "
             "is autumn with mustard and ochre trees, the left edge is winter with deep teal water and snowy roofs; the "
             "seasons blend smoothly at the four corners. The central plaza is a big, simple, light cream paved square with a "
             "few trees around its rim. Unlike the second reference image, there is no ring road, no tiles, no plaques, no "
             "card slots and no stations: only the landscape and the plaza, because game spaces will be printed on top.",
             STYLE, NO_TEXT]),
         [KITE, v6("map_board")], count=2),
]


def main():
    target = HERE / "style-samples-v7.jsonl"
    target.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in TASKS) + "\n", encoding="utf-8")
    print(target, len(TASKS), "tasks", sum(t["count"] for t in TASKS), "images")


if __name__ == "__main__":
    main()
