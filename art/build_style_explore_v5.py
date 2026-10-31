"""第五轮：画风探索。同一个画面，12 种现代画风各出一张，供用户直接挑。

上一轮的教训：做旧纸、棕褐色、宋体大标题、印章、罗马柱和旧报纸让画面像古代；
我们的名场面发生在 2015–2024 年的现代城市，画风要新、要有设计感。
不带参考图，避免把旧画风带进来。

输出：style-explore-v5.jsonl（每行含 id、label、prompt 等）
"""

import json
from pathlib import Path

HERE = Path(__file__).parent

SUBJECT = (
    "Key art for a mobile game and board game named 交易物种起源 (The Origin of Trading Species), portrait format. "
    "A summer evening in a modern Chinese city in 2015, at the peak of a stock-market frenzy. "
    "Behind everything, a huge LED screen on a glass office tower shows only a steep rising red line chart and red up arrows "
    "(in China red means prices going up), with no readable words or numbers on it. "
    "In the foreground, the hero: a fox in a short beige trench coat holding a smartphone, one eyebrow raised, skeptical and calm. "
    "Around the fox, smaller and further back, six other animal investors each react in their own way: "
    "a cheetah in a sporty windbreaker sprinting with its phone held high; "
    "an elephant in a knitted cardigan sitting calmly on a bench holding a small potted sapling; "
    "an owl with round glasses reading a thick printed report; "
    "a meerkat standing tall on top of a newsstand kiosk, wearing a small headset, scanning the crowd; "
    "a chameleon in a striped scarf whose skin is turning red to match the screen; "
    "a beaver in work overalls at a folding table with a laptop and a small toolbox. "
    "Contemporary city details: smartphones, shared bikes, a convenience store, plaza lights. "
    "The world is populated only by animals, no humans."
)

DIRECTION = (
    "Composition and light: the fox is the clear focal point, large in the lower third; "
    "strong figure-ground separation, the characters are brighter and more saturated than a simplified background; "
    "clear foreground, middle ground and background; the red glow of the screen rims the characters from behind. "
    "Adapt the amount of detail and the lighting to the style, but keep the focal point and the separation."
)

TITLE = (
    'Render the title "交易物种起源" exactly, large, at the top, in a bold modern Chinese display typeface that suits the style '
    "(clean geometric sans-serif or rounded display type); not calligraphy, not brush strokes, not an old-fashioned Song serif. "
    "Apart from the title, no words, no letters, no numbers anywhere."
)

AVOID = (
    "Contemporary, fresh and high-end. Not vintage, not sepia, no brown cast, no aged or yellowed paper, no old newspapers, "
    "no ancient Chinese motifs, no seals or stamps, no classical columns or old buildings. "
    "No logos, no brand names, no watermark, no pandas, no real people."
)

STYLES = [
    ("s01_toy", "潮玩手办 3D",
     "Style: designer vinyl toy and collectible blind-box figure aesthetic. The characters are chunky chibi figures with big heads "
     "and small bodies, smooth matte and glossy vinyl surfaces, soft rounded forms and tiny painted details; the city is a miniature "
     "toy diorama. Soft studio lighting with a gentle rim light, pastel candy colors with a few saturated accents, shallow depth of "
     "field like a premium product photo."),
    ("s02_film3d", "动画电影 3D",
     "Style: a still from a high-end stylized 3D animated feature film. Appealing, expressive character designs with clear "
     "silhouettes, detailed fur and fabric, cinematic lighting with warm practical lights against a cool dusk sky, volumetric glow "
     "from the screen, rich saturated color grading, shallow depth of field."),
    ("s03_clay", "黏土定格",
     "Style: stop-motion claymation. Everything is handmade from plasticine and craft materials: visible fingerprints and tool marks "
     "on the characters, felt and cardboard props, a miniature set with tilt-shift depth of field, practical miniature lights, "
     "playful saturated colors."),
    ("s04_papercraft", "纸艺分层",
     "Style: layered paper-craft diorama in a shadow box. Every element is cut from bright colored cardstock in many layers with "
     "real depth and soft shadows between the layers, crisp cut edges, characters as paper puppets, bright contemporary colors "
     "(white and vivid card, never aged paper), the red screen glowing through translucent paper."),
    ("s05_flat", "扁平几何海报",
     "Style: modern flat vector poster illustration. Characters built from simple geometric shapes with no outlines, flat color "
     "fields with a subtle grain, a bold limited palette of vermilion red, cobalt blue, sunny yellow, black and white; a strong "
     "grid-based layout with a large title and generous negative space; crisp and graphic like a contemporary design-studio poster."),
    ("s06_editorial", "极简杂志插画",
     "Style: minimalist editorial illustration for the cover of a modern business magazine. Very few elements, bold silhouettes and "
     "clever negative space, flat shapes in only three colors (deep navy, hot red, off-white), elegant and witty; the fox and its "
     "phone dominate, the other six animals are reduced to small, sharp, recognizable silhouettes."),
    ("s07_riso", "孔版印刷",
     "Style: risograph print. Only three fluorescent spot inks (fluorescent pink, bright blue and yellow) overprinting to make the "
     "other colors, visible grain and halftone texture, slight color misregistration, bold hand-drawn shapes, fresh indie zine energy "
     "on clean white paper."),
    ("s08_comic", "美漫分镜",
     "Style: contemporary comic-book key art. Bold ink lines, a dramatic low camera angle, speed lines, halftone dots and offset color "
     "printing, slight chromatic aberration, punchy saturated colors and dynamic poses, like a modern animated comic-book film."),
    ("s09_anime", "日系动画",
     "Style: modern anime key visual. Crisp clean line art with cel shading, a vivid sunset-to-night sky gradient, dramatic lighting "
     "with bloom and sparkles from the city lights, expressive characters, highly polished like a theatrical anime poster."),
    ("s10_pixel", "霓虹像素",
     "Style: modern high-quality pixel art on a strict pixel grid: every pixel the same size, no anti-aliasing, no blur, no mixed "
     "resolutions. A limited vivid palette of about 32 colors, a deep blue-purple night with neon red and cyan glows, crisp sprite-like "
     "characters with clean outlines, arcade energy."),
    ("s11_y2k", "酸性 Y2K",
     "Style: Y2K acid graphic design. Chrome and holographic metallic surfaces, a liquid-metal title, neon lime and hot pink gradients, "
     "glossy 3D characters with iridescent highlights, sticker shapes, wireframe grids and lens flares; loud, young and energetic."),
    ("s12_gouache", "现代绘本",
     "Style: contemporary picture-book gouache illustration. Bright, clean opaque paint with visible brush texture, simplified "
     "charming characters, a fresh palette of teal, coral, warm yellow and leaf green, soft warm evening light; cozy and modern like an "
     "award-winning children's book, not antique."),
]

MODEL = {"model": "gpt", "version": "gpt-image-2.5-flare", "quality": "high", "size": "1024x1536", "count": 1}


def build():
    rows = []
    for key, label, style in STYLES:
        prompt = " ".join([SUBJECT, style, DIRECTION, TITLE, AVOID])
        rows.append({"id": f"v5_{key}", "label": label, "prompt": prompt, **MODEL})
    target = HERE / "style-explore-v5.jsonl"
    target.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(target, len(rows))


if __name__ == "__main__":
    build()
