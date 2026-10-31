from pathlib import Path

PRINT = Path(__file__).resolve().parent.parent
ROOT = PRINT.parent
CONTENT = ROOT / "content"
ART = ROOT / "art" / "vmc-output"
DESIGN = ROOT / "design"
TEMPLATES = PRINT / "templates"
MOCK = PRINT / "mock"
BUILD = PRINT / "build"
OUT = PRINT / "out"
PREVIEW = PRINT / "preview"
FONTS = PRINT / "fonts"

for _d in (BUILD, OUT, PREVIEW, BUILD / "art", BUILD / "html", BUILD / "fonts"):
    _d.mkdir(parents=True, exist_ok=True)
