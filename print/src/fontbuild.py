"""把 CFF 轮廓的 OTF（Noto Sans SC、Source Code Pro）子集化并转成 TrueType 轮廓。

Chromium 打 PDF 时，CFF 字体会被嵌成 Type 3，部分印前 RIP 处理不好；
转成 glyf 轮廓后嵌入为 CID TrueType（子集、可检索），和得意黑一致。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

from .paths import BUILD

FONT_DIR = BUILD / "fonts"

SOURCES = {
    "NotoSansSC-400": "/root/.fonts/NotoSansSC-Regular.otf",
    "NotoSansSC-500": "/root/.fonts/NotoSansSC-Medium.otf",
    "NotoSansSC-700": "/root/.fonts/NotoSansSC-Bold.otf",
    "SourceCodePro-400": "/usr/share/fonts/adobe-source-code-pro/SourceCodePro-Regular.otf",
    "SourceCodePro-600": "/usr/share/fonts/adobe-source-code-pro/SourceCodePro-Semibold.otf",
}


def gb2312_chars() -> str:
    out = []
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    for hi in range(0xA1, 0xAA):  # 全角符号、序号、制表符
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    return "".join(out)


BASE_EXTRA = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "·—–…‘’“”《》「」『』【】（）〔〕：；、，。！？·￥×÷±≈≠≤≥→←↑↓↗↘⇢⟶"
    + "●○◐◑◎◇◆□■△▲▽▼☆★✓✔✗✘①②③④⑤⑥⑦⑧⑨⑩❶❷❸❹❺№℃％‰°"
)


def _otf_to_ttf(font: TTFont, max_err: float = 0.8) -> None:
    order = font.getGlyphOrder()
    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    gs = font.getGlyphSet()
    for name in order:
        pen = TTGlyphPen(gs)
        gs[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        glyf[name] = pen.glyph()
    del font["CFF "]
    for t in ("VORG", "DSIG"):
        if t in font:
            del font[t]
    glyf.compile(font)
    hmtx = font["hmtx"]
    for name, g in glyf.glyphs.items():
        if hasattr(g, "xMin"):
            hmtx[name] = (hmtx[name][0], g.xMin)
    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    for k in ("maxZones",):
        setattr(maxp, k, 1)
    for k in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
              "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"):
        setattr(maxp, k, 0)
    font["maxp"] = maxp
    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = order
    font.sfntVersion = "\000\001\000\000"


def build(extra_text: str = "", force: bool = False) -> dict[str, Path]:
    """返回 {key: ttf 路径}。字符集 = GB2312 + 常用符号 + 内容里实际出现的字。"""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    chars = set(gb2312_chars()) | set(BASE_EXTRA) | set(extra_text)
    chars = {c for c in chars if c.isprintable() or c in " \u3000\u00a0\u2009\u202f"}
    text = "".join(sorted(chars))
    sig = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    stamp = FONT_DIR / "stamp.json"
    old = json.loads(stamp.read_text()) if stamp.exists() else {}
    out: dict[str, Path] = {}
    for key, src in SOURCES.items():
        dst = FONT_DIR / f"{key}.ttf"
        out[key] = dst
        if not Path(src).exists():
            continue
        if dst.exists() and not force and old.get(key) == sig:
            continue
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.glyph_names = False
        opts.hinting = False
        opts.drop_tables += ["VORG", "BASE", "vhea", "vmtx", "DSIG"]
        f = TTFont(src)
        sub = subset.Subsetter(opts)
        sub.populate(text=text if key.startswith("Noto") else "".join(chr(c) for c in range(0x20, 0x250)) + "·—…“”‘’→←↑↓●○▲▼■◆★✓×÷±≈≤≥")
        sub.subset(f)
        _otf_to_ttf(f)
        f.save(dst)
        old[key] = sig
    stamp.write_text(json.dumps(old))
    return out


if __name__ == "__main__":
    import time

    t = time.time()
    print(build(force=True), round(time.time() - t, 1), "s")
