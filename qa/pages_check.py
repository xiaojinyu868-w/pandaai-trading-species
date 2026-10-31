"""逐个打开二维码落地页和独立页面：记录报错、空白页，并给每类页面截一张图。

用法：python3.11 qa/pages_check.py --base http://127.0.0.1:5179/ts/
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5179/ts/")
    a = ap.parse_args()
    out = ROOT / "qa" / "pages"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    codes = json.loads((ROOT / "content" / "qr.json").read_text(encoding="utf-8"))
    extra = ["record", "atlas", "about"]
    report = []
    shot_kinds = set()
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True, locale="zh-CN")
        errs = []

        def fresh():
            pg = ctx.new_page()
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:240]))
            pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:240]))
            return pg

        page = fresh()
        targets = [(c["id"], f"q/{c['code']}", c["route"]) for c in codes] + [(x, x, "/" + x) for x in extra]
        for cid, path, route in targets:
            for attempt in range(2):
                errs.clear()
                try:
                    page.goto(a.base + path, wait_until="networkidle")
                    page.wait_for_timeout(900)
                    url = page.url
                    text = page.inner_text("body").strip()
                    break
                except Exception as e:
                    try:
                        page.close()
                    except Exception:
                        pass
                    page = fresh()
                    url, text = "", ""
                    if attempt:
                        errs.append(f"crash: {str(e)[:120]}")
            kind = route.split("/")[1]
            ok = len(text) > 40 and not errs
            report.append({"id": cid, "route": route, "landed": url.split("/ts")[-1], "chars": len(text), "errors": list(errs), "ok": ok})
            if kind not in shot_kinds or not ok:
                shot_kinds.add(kind)
                page.screenshot(path=str(out / f"{kind}_{cid}.png"), full_page=True)
        br.close()
    bad = [r for r in report if not r["ok"]]
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(report)} 页，问题 {len(bad)} 页")
    for r in bad[:20]:
        print(" ", r["id"], r["route"], "->", r["landed"], r["chars"], r["errors"][:2])


if __name__ == "__main__":
    main()
