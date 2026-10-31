"""新主线 /go 自动通关：用真实的按住 / 松手手势玩完四关，截图并记录控制台报错。

用法：python3.11 qa/arcade_play.py --base http://127.0.0.1:5197/ts/ --run hold --out /tmp/ts-qa-mine/arc-hold
  hold   一直拿着，借 3 倍（看强平、跌停、熔断）
  swing  频繁进出，不借钱
  calm   大部分时间空仓，只在暴跌后买一次
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# 每关的手势：[(距开局毫秒, "down"|"up")]；开局时都是先按一下开盘
PLANS = {
    "hold": dict(offer="借 3 倍", guess=1, moves={
        "s924": [(0, "down")],
        "s2015": [(0, "down")],
        "smt": [(0, "down"), (16000, "up")],
        "scb": [(0, "down")],
    }),
    "swing": dict(offer="借 1 倍", guess=0, moves={
        "s924": [(0, "down"), (900, "up"), (3500, "down"), (9000, "up"), (12000, "down"), (15000, "up")],
        "s2015": [(0, "down"), (5000, "up"), (7000, "down"), (12000, "up"), (15000, "down"), (19000, "up")],
        "smt": [(0, "down"), (6000, "up"), (8000, "down"), (13000, "up")],
        "scb": [(0, "down"), (3000, "up"), (12000, "down")],
    }),
    "calm": dict(offer="不借", guess=3, moves={
        "s924": [(0, "down"), (500, "up")],
        "s2015": [(0, "down"), (500, "up")],
        "smt": [(0, "down"), (500, "up")],
        "scb": [(0, "down"), (500, "up"), (14000, "down")],
    }),
}

LEVEL_ORDER = ["s924", "s2015", "smt", "scb"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5197/ts/")
    ap.add_argument("--run", default="hold", choices=list(PLANS))
    ap.add_argument("--out", default="/tmp/ts-qa-mine/arc")
    ap.add_argument("--size", default="390x844")
    a = ap.parse_args()
    plan = PLANS[a.run]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = map(int, a.size.split("x"))
    errors, log = [], []
    shots = 0

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, has_touch=False, is_mobile=False)
        p = ctx.new_page()
        p.on("console", lambda m: m.type == "error" and errors.append(m.text))
        p.on("pageerror", lambda e: errors.append(str(e)))

        def shot(name):
            nonlocal shots
            shots += 1
            p.screenshot(path=str(out / f"{shots:02d}_{name}.png"))

        def overflow():
            return p.evaluate("() => document.scrollingElement.scrollHeight - innerHeight")

        def btn_center():
            b = p.query_selector(".arc-btn")
            if not b:
                return None
            bb = b.bounding_box()
            return bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2

        p.goto(a.base + "go")
        p.evaluate("() => localStorage.clear()")
        p.goto(a.base + "go")
        t_all = time.time()

        for li, lid in enumerate(LEVEL_ORDER):
            p.wait_for_selector(".arc-cold", timeout=15000)
            time.sleep(1.2)
            shot(f"{lid}_cold")
            p.click(".arc-cold")
            p.wait_for_selector(".arc-btn", timeout=8000)
            time.sleep(0.6)
            shot(f"{lid}_ready")
            if overflow() > 2:
                log.append(f"{lid} 游戏页溢出 {overflow()}px")
            moves = list(plan["moves"][lid])
            t0 = time.time()
            down = False
            seen = set()
            while not p.query_selector(".arc-reveal"):
                el = (time.time() - t0) * 1000
                if moves and el >= moves[0][0]:
                    _, kind = moves.pop(0)
                    c = btn_center()
                    if c:
                        p.mouse.move(*c)
                        if kind == "down" and not down:
                            p.mouse.down()
                            down = True
                        elif kind == "up" and down:
                            p.mouse.up()
                            down = False
                offer = p.query_selector(".arc-offer")
                if offer and "offer" not in seen:
                    seen.add("offer")
                    time.sleep(0.5)
                    shot(f"{lid}_offer")
                    if down:
                        p.mouse.up()
                        down = False
                    p.get_by_role("button", name=plan["offer"]).click()
                    log.append(f"{lid} 借钱：{plan['offer']}")
                    if plan["moves"][lid] and plan["moves"][lid][-1][1] == "down" and not [m for m in moves if m[1] == "up"]:
                        time.sleep(0.3)
                        c = btn_center()
                        if c:
                            p.mouse.move(*c)
                            p.mouse.down()
                            down = True
                for sel, tag in ((".arc-over.holiday", "holiday"), (".arc-over.halt", "halt"), (".arc-over.dark", "liq"), (".arc-count", "count")):
                    if p.query_selector(sel) and tag not in seen:
                        seen.add(tag)
                        time.sleep(0.4 if tag != "count" else 0.1)
                        shot(f"{lid}_{tag}")
                if p.query_selector(".arc-toast") and "toast" not in seen and el > 3000:
                    seen.add("toast")
                    shot(f"{lid}_toast")
                if el > 6000 and "mid" not in seen:
                    seen.add("mid")
                    shot(f"{lid}_mid")
                if el > 90000:
                    log.append(f"{lid} 超时")
                    break
                time.sleep(0.05)
            if down:
                p.mouse.up()
            log.append(f"{lid} 用时 {time.time() - t0:.1f}s")
            p.wait_for_selector(".arc-reveal", timeout=10000)
            time.sleep(4.8)
            shot(f"{lid}_reveal")
            if overflow() > 2:
                log.append(f"{lid} 揭幕页溢出 {overflow()}px")
            ai = p.inner_text(".arc-ai")
            stamp = p.inner_text(".arc-stamp2")
            money = p.inner_text(".arc-money b")
            log.append(f"{lid} 印章「{stamp}」{money} 旁白：{ai}")
            p.click(".arc-reveal .btn.primary")

        p.wait_for_selector(".arc-guess", timeout=8000)
        time.sleep(0.8)
        shot("guess")
        if overflow() > 2:
            log.append(f"猜物种页溢出 {overflow()}px")
        p.query_selector_all(".arc-sp")[plan["guess"]].click()
        time.sleep(1.0)
        shot("judge")
        tj = time.time()
        p.wait_for_selector(".arc-final", timeout=20000)
        log.append(f"AI 判断等待 {time.time() - tj:.1f}s")
        for i in range(4):
            time.sleep(1.2)
            shot(f"final_{i}")
            if overflow() > 2:
                log.append(f"结果页 {i} 溢出 {overflow()}px")
            if i < 3:
                p.click(".arc-final", position={"x": w / 2, "y": h * 0.3})
        log.append("物种：" + p.evaluate("() => JSON.parse(localStorage.getItem('ts-arcade-v1')).state.verdict.species"))
        log.append("模型：" + p.evaluate("() => JSON.parse(localStorage.getItem('ts-arcade-v1')).state.verdict.model"))
        log.append(f"总用时 {time.time() - t_all:.0f}s")
        br.close()

    rep = {"run": a.run, "log": log, "errors": errors}
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
