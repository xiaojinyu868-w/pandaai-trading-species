"""桌游 → 手机：照一张纸质记录卡把 /record 填完，生成画像，截图并检查报错。

python3.11 qa/record_check.py --base http://127.0.0.1:5180/ts/
"""

import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

# 示意的纸质记录卡：老周（规则书里的一局示例）
CARD = {
    "self": "大象",
    "seasons": [
        {"ev": ["消息"], "opt": "A", "reason": "消息", "plan": "不定计划"},
        {"ev": ["量价"], "opt": "C", "reason": "量价", "plan": "跌了就走", "recognized": True, "correct": True},
        {"ev": ["量价"], "opt": "C", "reason": "量价", "plan": "不定计划"},
        {"ev": [], "opt": "A", "reason": "直觉", "plan": "不定计划", "coin": "猎豹"},
    ],
    "dp": 0,
    "money": 17,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5180/ts/")
    a = ap.parse_args()
    out = ROOT / "qa" / "record"
    out.mkdir(parents=True, exist_ok=True)
    errs = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1.5, is_mobile=True, has_touch=True, locale="zh-CN")
        p = ctx.new_page()
        p.on("console", lambda m: m.type == "error" and errs.append(m.text[:200]))
        p.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:200]))
        p.goto(a.base + "record", wait_until="networkidle")
        p.locator("button.chip", has_text=CARD["self"]).first.click()
        for i, s in enumerate(CARD["seasons"]):
            p.locator("button.chip").nth(6 + i).click()
            for e in s["ev"]:
                p.locator("button.chip", has_text=e).first.click()
            p.locator("button.chip", has_text=re.compile(rf"^{s['opt']} (?!·)")).first.click()
            p.locator("button.chip", has_text=re.compile(rf"^{s['reason']}$")).last.click()
            p.locator("button.chip", has_text=s["plan"]).first.click()
            if s.get("recognized"):
                p.get_by_label("这一场我认出来了").check()
                if s.get("correct"):
                    p.get_by_label("事件名写对了").check()
            if s.get("coin"):
                p.locator("button.chip", has_text=re.compile(rf"^{s['coin']}$")).last.click()
            p.wait_for_timeout(150)
        p.get_by_role("button", name=str(CARD["dp"]), exact=True).click()
        p.locator("input[type=number]").fill(str(CARD["money"]))
        p.screenshot(path=str(out / "01_form.png"), full_page=True)
        btn = p.locator("button", has_text="生成我的完整画像")
        ok_btn = btn.count() > 0 and btn.first.is_enabled()
        if ok_btn:
            btn.first.click()
            p.wait_for_timeout(2500)
            p.screenshot(path=str(out / "02_ending_top.png"))
            p.screenshot(path=str(out / "03_ending_full.png"), full_page=True)
        state = p.evaluate("() => localStorage.getItem('ts-game-v1')")
        br.close()
    g = json.loads(state)["state"]["g"] if state else None
    summary = {
        "submit_enabled": ok_btn,
        "errors": errs,
        "phase": g and g["phase"],
        "source": g and g["source"],
        "seasons": g and [{k: r.get(k) for k in ("scene", "option", "reason", "plan", "coin", "coinHalf", "stars")} for r in g["seasons"]],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
