"""生成风格样张 v2 的 vmc 批量文件（参考《西区 NOOKFALL》的视觉方向）。

输出：
  style-samples-v2.jsonl         带 id，留档用
  style-samples-v2.submit.jsonl  去掉 id，直接给 vmc image batch --file
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
REF_KEYS = json.loads((HERE / "refs" / "vmc_ref_keys.json").read_text(encoding="utf-8"))

COVER = REF_KEYS["ref1_cover_landscape.jpg"]
BOOKSTORE = REF_KEYS["ref2_iso_bookstore_magazine.jpg"]
CAFE = REF_KEYS["ref3_iso_cafe_menu.jpg"]
TRAM = REF_KEYS["ref4_tram_poster.jpg"]
MAP = REF_KEYS["ref5_map_station_ui.jpg"]

MODEL = {"model": "gpt", "version": "gpt-image-2.5-flare", "quality": "high"}

STYLE = (
    "Art style: retro-modernist graphic illustration in the spirit of mid-century travel posters and "
    "contemporary indie adventure games: large flat color blocks, simplified geometric architecture, "
    "faceted landscape shapes, subtle digital gouache brush strokes and fine offset or risograph print "
    "grain, crisp clean edges, calm warm light with a hint of mystery. Limited palette: warm cream paper, "
    "brick red, terracotta orange, mustard yellow, olive and sage green, deep forest green, deep teal blue, "
    "dark espresso brown. Use the reference images only as a guide for rendering style, palette, texture "
    "and level of detail. Create an original composition: do not copy any building, character, vehicle, "
    "title, logo or layout from the references."
)

NO_TEXT = (
    "No text, no letters, no numbers, no digits on screens or boards, no logos, no brand marks, "
    "no signage lettering, no watermark, no real people."
)

ROOM = (
    "Isometric cutaway diorama of a single room, like a miniature architectural model: two walls and the "
    "floor visible, the room floating on a flat warm grey-beige background with generous empty margins. "
    "Characters are stylized anthropomorphic animals rendered as low-detail flat-shaded figures, like the "
    "people in the reference rooms. Props that a player could tap are clearly separated and readable."
)


def task(id_, size, prompt, refs, count=1, **extra):
    return {"id": id_, "size": size, "count": count, "prompt": prompt, "ref": refs, **MODEL, **extra}


TASKS = [
    task(
        "v2_01_species_lineup",
        "2048x1024",
        "Character lineup sheet for a board game and a mobile game. Seven anthropomorphic animal characters "
        "standing side by side with even spacing on a flat warm cream background, full body, three-quarter "
        "view, same scale and same rendering style, each with a clear readable silhouette and a calm, "
        "dignified expression: a cheetah in a sporty retro windbreaker holding a stopwatch; an elephant in a "
        "knitted cardigan holding a small potted sapling; a fox in a short trench coat holding a magnifying "
        "glass and a pocket notebook; an owl in a tweed vest and round glasses holding a small lantern; a "
        "meerkat standing tall and alert, wearing a tiny radio headset, a folded newspaper under its arm; a "
        "chameleon wearing a striped scarf whose stripes shift through several colors, holding a brass "
        "compass; a beaver in work overalls holding a wrench and a rolled blueprint. In front of them, in "
        "the center, a small cream-colored egg with a paper tram ticket tucked into a band, sitting on a "
        "tiny suitcase: a traveler whose species is not known yet. Stylized low-detail flat-shaded figures "
        "like painted miniature models, soft cast shadows on the floor. " + STYLE + " " + NO_TEXT,
        [BOOKSTORE, CAFE, COVER],
        count=2,
    ),
    task(
        "v2_02_board_transit_map",
        "2048x2048",
        "Top-down game board illustration, square format, to be printed as a folding board game board. A "
        "small fictional market town seen from directly above, drawn like a retro transit map on cream grid "
        "paper. Four districts arranged clockwise as the four seasons of a market cycle: a spring district in "
        "sage green with blossom trees, a summer district in brick red and terracotta with crowded rooftops, "
        "an autumn district in mustard and ochre with falling leaves, a winter district in deep teal blue "
        "with snowy roofs. One bold looped tram line with a thick dark outline circles the whole town, with "
        "about twenty-four evenly spaced round blank station markers (cream circles with bold dark "
        "outlines). On each season's side, one larger interchange station splits into two short branches, "
        "each ending at a tiny isometric landmark building: two doors to choose from. A river runs "
        "diagonally, small parks, a compass rose in one corner. The center of the board is an open plaza "
        "with generous empty space for cards. Flat even lighting and clean shapes suitable for print. Every "
        "station marker and label area is blank. " + STYLE + " " + NO_TEXT,
        [MAP, COVER],
    ),
    task(
        "v2_03_room_2015_summer",
        "1536x1024",
        ROOM + " The scene: a crowded Chinese securities brokerage trading hall on a hot summer day. A huge "
        "wall of glowing quote boards made only of abstract red bars and blocks, rows of plastic chairs, a "
        "ceiling fan, a water dispenser, a potted plant, a desk with tall stacks of loan papers and a big "
        "rubber stamp. Animal retail investors in summer clothes: an excited cheetah pointing at the board, "
        "two meerkats on tiptoe, an elephant calmly reading a thick report, a fox comparing notes in a "
        "notebook, and an owl in a cardigan sitting at a small side desk with a magnifying glass. Tappable "
        "props: the quote board, a newspaper rack, a ledger on the desk, a telephone. Mood: summer heat, "
        "crowd fever, a faint hint of danger. Dominant brick red, terracotta and mustard with cream. "
        + STYLE + " " + NO_TEXT,
        [BOOKSTORE, CAFE],
    ),
    task(
        "v2_04_room_924_spring",
        "1536x1024",
        ROOM + " The scene: a small modern brokerage branch office in the evening before a long national "
        "holiday. A long queue of animals winds from the service counter to the glass door and out into the "
        "street, most of them lit by glowing smartphones. Red paper lanterns and small red flags for the "
        "coming holiday, a wall calendar with a blank page, fresh green plants. A meerkat on tiptoe at the "
        "back of the line, a chameleon whose colors flicker, a fox standing aside writing in a notebook, a "
        "cheetah dashing in through the door, a beaver clerk behind the counter buried in forms. Tappable "
        "props: the smartphones, a notice board, the calendar, a stack of account forms. Mood: excitement, "
        "hope and a slightly absurd rush. Dominant sage green and cream with festive red accents. "
        + STYLE + " " + NO_TEXT,
        [BOOKSTORE, CAFE],
    ),
    task(
        "v2_05_room_moutai_autumn",
        "1536x1024",
        ROOM + " The scene: a private banquet room in an upscale restaurant in golden autumn. A large round "
        "banquet table with a lazy susan, plain white porcelain liquor bottles without labels and small "
        "glasses. Several animals in business suits hold hands in a tight circle around the table, smiling "
        "with closed eyes, huddled together. One chair is tipping over and a lone fox is quietly slipping out "
        "through a half-open door. A coat rack, a folding screen, a framed mountain painting, a tall window "
        "with autumn trees and falling leaves outside. Tappable props: the bottles, the lazy susan, the door, "
        "a menu folder. Mood: comfortable luxury with a subtle crack of unease. Dominant mustard, ochre and "
        "dark espresso brown with cream. " + STYLE + " " + NO_TEXT,
        [BOOKSTORE, CAFE],
    ),
    task(
        "v2_06_room_2020_winter",
        "1536x1024",
        ROOM + " The scene: a stock exchange trading floor on a cold winter day. Trading booths with screens "
        "showing only abstract falling bars, a giant red emergency circuit-breaker lever mounted on the "
        "wall, a large wall clock, an hourglass on a desk, a shelf with stacked supplies and face masks, "
        "snow falling outside a tall window. Animal traders in winter jackets frozen mid-motion in total "
        "silence: a cheetah mid-stride, an elephant holding a cup, a meerkat clutching a phone, and an owl "
        "sitting calmly beside a lantern. Tappable props: the lever, the clock, the hourglass, the screens. "
        "Mood: tense silence, the whole room holding its breath. Dominant deep teal blue and cream with a "
        "single bright red alarm accent. " + STYLE + " " + NO_TEXT,
        [BOOKSTORE, CAFE],
    ),
    task(
        "v2_07_scene_card_magazine",
        "1024x1536",
        "Vertical cover illustration of a retro weekly magazine, used as a mystery event card in a board "
        "game. The top band is a plain solid cream masthead area above a thin mustard stripe, left completely "
        "blank for typography to be added later. Below it, a bold graphic poster illustration fills the "
        "cover: a hot summer city at noon where a crowd of tiny animals pull on hundreds of taut strings to "
        "lift a giant red paper kite shaped like an upward arrow high into the blazing sky, heat haze over "
        "the rooftops, a few dark clouds far on the horizon. A small blank rectangular price tag in the "
        "bottom corner. Strong poster composition, flat color blocks, rough print grain. "
        + STYLE + " " + NO_TEXT,
        [BOOKSTORE, COVER],
    ),
    task(
        "v2_08_species_poster_fox",
        "1088x1920",
        "Vertical 9:16 poster illustration for a mobile game result screen, composed like a retro travel "
        "poster: a sweeping graphic landscape of faceted olive-green mountains, a peach sunset sky with long "
        "horizontal brush-stroke clouds, a small tram station and modernist buildings in the middle "
        "distance, and in the foreground a fox in a short trench coat standing on a grassy hill with a "
        "magnifying glass and a notebook, looking toward the town. Leave a large empty sky area in the upper "
        "half for a giant condensed title to be added later, and a calm empty band at the bottom for "
        "information blocks. " + STYLE + " " + NO_TEXT,
        [COVER, TRAM],
    ),
    task(
        "v2_09_tabletop_mockup",
        "1536x1024",
        "Photorealistic product photo of a premium tabletop board game on a warm oak table, 45-degree "
        "top-down angle, soft daylight. A square board printed in a retro transit-map style on cream paper "
        "with a looped tram line, colored seasonal districts and round station markers; magazine-style "
        "illustrated event cards and menu-style decision cards fanned out beside it; small matte "
        "3D-printed animal figurines (fox, elephant, cheetah, owl) on round bases used as pawns; mustard and "
        "brick-red tokens, two dice, a small sand timer, a pencil and a scoresheet pad; a smartphone on the "
        "table showing an illustrated game screen. The printed artwork follows the flat retro-modernist "
        "graphic style and palette of the references (cream, brick red, mustard, olive green, deep teal, "
        "espresso brown). Printed materials show only illustrations, color blocks and blank areas. "
        + NO_TEXT,
        [MAP, BOOKSTORE],
    ),
    task(
        "v2_10_fox_figurine",
        "1024x1024",
        "A single painted miniature figurine used as a board game pawn: a stylized anthropomorphic fox in a "
        "short trench coat holding a magnifying glass, standing on a round base. Full body, front "
        "three-quarter view, centered. Chunky, simple, readable shapes suitable for 3D printing at 4 cm "
        "tall, with no thin fragile parts. Matte painted finish: terracotta orange fur, cream chest, mustard "
        "coat, espresso brown details. Plain flat light grey studio background, soft even lighting, no "
        "background shadows. " + NO_TEXT,
        [BOOKSTORE, CAFE],
        background="opaque",
    ),
]


def main():
    with open(HERE / "style-samples-v2.jsonl", "w", encoding="utf-8") as archive, open(
        HERE / "style-samples-v2.submit.jsonl", "w", encoding="utf-8"
    ) as submit:
        for t in TASKS:
            archive.write(json.dumps(t, ensure_ascii=False) + "\n")
            submit.write(json.dumps({k: v for k, v in t.items() if k != "id"}, ensure_ascii=False) + "\n")
    total = sum(t["count"] for t in TASKS)
    print(f"{len(TASKS)} tasks, {total} images")


if __name__ == "__main__":
    main()
