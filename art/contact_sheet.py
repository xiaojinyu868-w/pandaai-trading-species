"""把一轮样张按“行 = 物料、列 = 画风”拼成并排对比图，方便逐行挑选。

用法：
  python3.11 contact_sheet.py style-samples-v4.jsonl vmc-output/style-v4 contact-v4

id 约定：<轮次>_<行>__<列>，例如 v4_r01_map__a。行名、列名从对应的 build 脚本里读。
"""

import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT_BOLD = "/root/.fonts/NotoSansSC-Bold.otf"
FONT_REGULAR = "/root/.fonts/NotoSansSC-Regular.otf"

BG = (38, 35, 31)
INK = (240, 230, 210)
MUTED = (170, 160, 140)
CELL_LONG_SIDE = 1100
GUTTER = 40
HEADER = 120
LABEL = 70


def load_build_module(archive: Path):
    version = archive.stem.split("-")[-1]
    path = HERE / f"build_style_batch_{version}.py"
    spec = importlib.util.spec_from_file_location("build_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def latest_manifest(out_dir: Path):
    manifests = sorted(out_dir.glob("b_*.manifest.json"))
    if not manifests:
        sys.exit(f"{out_dir} 里还没有 manifest，批次可能没跑完")
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def fit(image: Image.Image, long_side: int) -> Image.Image:
    scale = long_side / max(image.size)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)


def main():
    archive, out_dir, sheet_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    build = load_build_module(archive)
    row_labels = {row["row"]: row["label"] for row in build.ROWS}
    style_names = build.STYLE_NAMES

    ids = [json.loads(line)["id"] for line in archive.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = latest_manifest(out_dir)
    files_by_id = {}
    for item in manifest["items"]:
        files = item.get("files") or []
        if item.get("status") == "completed" and files:
            files_by_id[ids[item["index"] - 1]] = files[0]

    rows = {}
    for id_ in ids:
        _, rest = id_.split("_", 1)
        row, col = rest.rsplit("__", 1)
        rows.setdefault(row, {})[col] = files_by_id.get(id_)

    sheet_dir.mkdir(parents=True, exist_ok=True)
    title_font = ImageFont.truetype(FONT_BOLD, 56)
    label_font = ImageFont.truetype(FONT_BOLD, 44)
    note_font = ImageFont.truetype(FONT_REGULAR, 32)

    for n, (row, cols) in enumerate(rows.items(), start=1):
        cells = []
        for col in sorted(cols):
            path = cols[col]
            image = fit(Image.open(path).convert("RGB"), CELL_LONG_SIDE) if path else None
            cells.append((col, image))
        cell_w = max((img.width for _, img in cells if img), default=CELL_LONG_SIDE)
        cell_h = max((img.height for _, img in cells if img), default=CELL_LONG_SIDE)
        width = GUTTER + len(cells) * (cell_w + GUTTER)
        height = HEADER + LABEL + cell_h + GUTTER
        sheet = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(sheet)
        draw.text((GUTTER, 30), f"第 {n} 行 · {row_labels.get(row, row)}", font=title_font, fill=INK)
        for i, (col, image) in enumerate(cells):
            x = GUTTER + i * (cell_w + GUTTER)
            draw.text((x, HEADER), style_names.get(col, col), font=label_font, fill=INK)
            top = HEADER + LABEL
            if image:
                sheet.paste(image, (x + (cell_w - image.width) // 2, top + (cell_h - image.height) // 2))
            else:
                draw.rectangle((x, top, x + cell_w, top + cell_h), outline=MUTED, width=3)
                draw.text((x + 40, top + 40), "这张没出成功", font=note_font, fill=MUTED)
        target = sheet_dir / f"{n:02d}_{row}.jpg"
        sheet.save(target, quality=88)
        print(target)


if __name__ == "__main__":
    main()
