"""把 run_parallel.py 的结果拼成带编号和画风名的网格总表。

  python3.11 grid_sheet.py vmc-output/style-v5/results.json contact-v5 --cols 4 --per-sheet 12
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/root/.fonts/NotoSansSC-Bold.otf"
BG = (30, 30, 34)
INK = (245, 245, 245)
MUTED = (150, 150, 150)
GUTTER = 28
LABEL_H = 76


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results")
    parser.add_argument("out_dir")
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--per-sheet", type=int, default=12)
    parser.add_argument("--cell-h", type=int, default=960)
    args = parser.parse_args()

    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_BOLD, 40)

    cells = []
    for n, r in enumerate(results, start=1):
        image = Image.open(r["files"][0]).convert("RGB") if r.get("files") else None
        cells.append((f"{n:02d} {r['label']}", image))

    cell_w = round(args.cell_h * 2 / 3)
    for start in range(0, len(cells), args.per_sheet):
        chunk = cells[start:start + args.per_sheet]
        rows = -(-len(chunk) // args.cols)
        width = GUTTER + args.cols * (cell_w + GUTTER)
        height = GUTTER + rows * (LABEL_H + args.cell_h + GUTTER)
        sheet = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(sheet)
        for i, (label, image) in enumerate(chunk):
            x = GUTTER + (i % args.cols) * (cell_w + GUTTER)
            y = GUTTER + (i // args.cols) * (LABEL_H + args.cell_h + GUTTER)
            draw.text((x, y + 8), label, font=font, fill=INK)
            top = y + LABEL_H
            if image:
                scale = min(cell_w / image.width, args.cell_h / image.height)
                thumb = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
                sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, top + (args.cell_h - thumb.height) // 2))
            else:
                draw.rectangle((x, top, x + cell_w, top + args.cell_h), outline=MUTED, width=3)
                draw.text((x + 30, top + 30), "没出成功", font=font, fill=MUTED)
        target = out_dir / f"sheet_{start // args.per_sheet + 1}.jpg"
        sheet.save(target, quality=88)
        print(target, sheet.size)


if __name__ == "__main__":
    main()
