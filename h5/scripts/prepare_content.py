"""把 content/ 下的内容复制进 H5（src/data/），H5 构建时直接打包；码表另放 public/q-map.json（不缓存，可改）。"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "content"
DST = ROOT / "h5" / "src" / "data"


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for name in ("scenes.json", "decks.json", "qr.json", "rules_eval.json"):
        p = SRC / name
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            (DST / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            print("复制", name)
        elif not (DST / name).exists():
            (DST / name).write_text("{}", encoding="utf-8")
            print("占位", name)


if __name__ == "__main__":
    main()
