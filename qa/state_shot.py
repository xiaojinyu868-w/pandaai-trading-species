"""把一份 e2e 结果注入 localStorage，直接截结局页（不用重玩一局）。

  python3.11 qa/state_shot.py --from qa/e2e/B/summary.json --self chameleon --out qa/tie
"""
import argparse, json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

SEASONS = ["spring", "summer", "autumn", "winter"]


def state_from(summary: dict, self_sp: str) -> dict:
    r = summary["result"]
    seasons = []
    for i, s in enumerate(r["seasons"]):
        rec = {"season": SEASONS[i], "rpGained": 1, "evidenceMs": {}, **s}
        rec = {k: v for k, v in rec.items() if v is not None}
        seasons.append(rec)
    now = int(time.time() * 1000)
    return {
        "state": {
            "g": {
                "id": "qa-state", "phase": "ending", "step": "reveal", "seasonIdx": 4, "pos": 0,
                "money": r["money"], "rp": r["rp"], "self": self_sp,
                "opponents": list(r["aiMoney"].keys()), "aiMoney": r["aiMoney"],
                "rules": [s["ruleKept"] for s in r["seasons"] if s.get("ruleKept")],
                "dataportRight": 0, "dataportSeen": 0, "seasons": seasons,
                "startedAt": now - 900000, "finishedAt": now, "source": "h5",
            },
            "muted": True,
        },
        "version": 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--self", dest="self_sp", default="chameleon")
    ap.add_argument("--base", default="http://127.0.0.1:5179/ts/")
    ap.add_argument("--out", default="qa/state")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    st = state_from(json.loads(Path(a.src).read_text()), a.self_sp)
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True, locale="zh-CN")
        ctx.add_init_script(f"localStorage.setItem('ts-game-v1', {json.dumps(json.dumps(st, ensure_ascii=False))})")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(a.base + "play", wait_until="networkidle")
        pg.wait_for_timeout(3000)
        pg.screenshot(path=str(out / "hatch.png"))
        pg.wait_for_timeout(2500)
        pg.screenshot(path=str(out / "ending_top.png"))
        pg.screenshot(path=str(out / "ending_full.png"), full_page=True)
        share = pg.locator("button", has_text="分享图")
        if share.count():
            share.first.click(); pg.wait_for_timeout(1500)
            pg.screenshot(path=str(out / "share.png"))
        print(json.dumps({"errors": errs, "text": pg.inner_text("body")[:600]}, ensure_ascii=False))
        br.close()


if __name__ == "__main__":
    main()
