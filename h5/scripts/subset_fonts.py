"""只保留 H5 里实际出现的字，把 Noto Sans SC 切成很小的 woff2（每个字重几百 KB）。

字表来自 h5/src 下所有代码和内容 JSON，外加 ASCII 和常用中文标点。内容改了要重跑。
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "h5" / "src"
OUT = ROOT / "h5" / "public" / "fonts" / "noto"
FONTS = {400: "NotoSansSC-Regular.otf", 500: "NotoSansSC-Medium.otf", 700: "NotoSansSC-Bold.otf"}
EXTRA = "“”‘’，。、；：？！（）《》〈〉【】—…·→←↑↓↗×÷±−％￥0123456789"


def main():
    chars = set(chr(c) for c in range(0x20, 0x7F)) | set(EXTRA)
    for p in SRC.rglob("*"):
        if p.suffix in {".ts", ".tsx", ".json", ".css"}:
            chars |= set(p.read_text(encoding="utf-8", errors="ignore"))
    chars = {c for c in chars if c.isprintable() and ord(c) < 0x10000}
    OUT.mkdir(parents=True, exist_ok=True)
    text = OUT / "chars.txt"
    text.write_text("".join(sorted(chars)), encoding="utf-8")
    css = []
    for w, name in FONTS.items():
        dst = OUT / f"noto-{w}.woff2"
        subprocess.run(["python3.11", "-m", "fontTools.subset", str(Path("/root/.fonts") / name), f"--text-file={text}",
                        "--flavor=woff2", "--layout-features=*", f"--output-file={dst}"], check=True)
        css.append(f'@font-face{{font-family:"Noto Sans SC";font-weight:{w};font-style:normal;font-display:swap;'
                   f'src:url("./noto-{w}.woff2") format("woff2");}}')
    css.append('@font-face{font-family:"Noto Sans SC";font-weight:800 900;font-style:normal;font-display:swap;'
               'src:url("./noto-700.woff2") format("woff2");}')
    (OUT / "noto.css").write_text("\n".join(css) + "\n", encoding="utf-8")
    sizes = {p.name: f"{p.stat().st_size / 1024:.0f} KB" for p in sorted(OUT.glob("*.woff2"))}
    print(f"{len(chars)} 个字", sizes)


if __name__ == "__main__":
    main()
