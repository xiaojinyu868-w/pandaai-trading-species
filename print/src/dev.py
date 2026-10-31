"""开发用：快速把一组牌渲染成预览 PNG。python3.11 -m src.dev <name> ..."""

from __future__ import annotations

import sys
import time

from .core import doc, preview_body
from .paths import BUILD
from .render import Renderer


def show(cards, out_name, cols=4, dpi=110, trimmed=True, title=""):
    body, w, h = preview_body(cards, cols=cols, trimmed=trimmed, title=title)
    html = doc(body, w, h, title=out_name)
    r = Renderer()
    try:
        p = BUILD / f"dev_{out_name}.png"
        r.png(html, f"dev_{out_name}", p, dpi=dpi, viewport={"width": int(w / 25.4 * 96) + 2, "height": int(h / 25.4 * 96) + 2})
        for i in r.issues:
            print("ISSUE", i)
        return p
    finally:
        r.close()


def main():
    from . import c_a6
    from .model import Model
    t = time.time()
    m = Model()
    which = sys.argv[1] if len(sys.argv) > 1 else "scene"
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 110
    cards = []
    if which == "scene":
        for sc in m.scenes:
            if only and sc["id"] not in only:
                continue
            cards += [c_a6.scene_blind(m, sc), c_a6.scene_door(m, sc), c_a6.reveal_front(m, sc)]
        if not only:
            cards.append(c_a6.reveal_back())
        p = show(cards, which + ("_" + "_".join(only) if only else ""), cols=6, dpi=dpi)
    elif which == "a6misc":
        for sp in m.species:
            if only and sp["id"] not in only:
                continue
            cards += [c_a6.species_front(m, sp), c_a6.species_back(m, sp)]
        if not only:
            cards += [c_a6.prologue_front(m), c_a6.prologue_back(m), c_a6.quickref_front(m), c_a6.quickref_back(m),
                      c_a6.prop_sell_window(m), c_a6.prop_crowd_ring(m), c_a6.prop_exit_board(m),
                      c_a6.prop_back("卖出窗口", "SELL WINDOW", "x")]
        p = show(cards, which + ("_" + "_".join(only) if only else ""), cols=6, dpi=dpi)
    elif which == "std":
        from . import c_std
        cards = c_std.dev_cards(m, only)
        p = show(cards, which + ("_" + "_".join(only) if only else ""), cols=8, dpi=dpi)
    print(p, time.time() - t)


if __name__ == "__main__":
    main()
