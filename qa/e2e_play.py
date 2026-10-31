"""H5 自动通关：按配置从首页玩到终局，每到一个新画面截一张图，记录控制台报错。

用法：python3.11 qa/e2e_play.py --base http://127.0.0.1:5179/ts/ --run A
"""

import argparse
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent

RUNS = {
    # 春 924 / 夏 2015 / 秋 茅台 / 冬 熔断；入门对手；夏天申报认出
    "A": dict(seed=7, opp="入门", self_idx=0, tiles=[2, 4, 3, 1], doors=["A", "A", "A", "A"], recognize=[1],
              ev=[["price", "news"], ["data", "price"], ["data", "news"], ["tip", "price"]],
              opt=["B", "A", "A", "B"], reason=["量价", "数据", "数据", "消息"], plan=["跌了就走", "跌了就走", "跌了就加", "不定计划"],
              follow=True, ring="离开", dial="不动", second="不看了", decide="拿着不动", calm="坐下"),
    # 秋 量化踩踏 / 冬 原油宝（近月 A，穿仓）；进阶对手；冷静亭不坐
    "B": dict(seed=11, opp="进阶", self_idx=3, tiles=[5, 1, 3, 2], doors=["A", "A", "B", "B"], recognize=[],
              ev=[["tip"], ["price", "data", "news"], ["price"], ["data"]],
              opt=["C", "C", "C", "A"], reason=["数据", "量价", "规则牌", "看不懂"], plan=["不定计划", "跌了就走", "跌了就走", "不定计划"],
              follow=False, ring="留下", dial="减 1 份", second="止损", decide="回调了，进 1 份", calm="不坐"),
    # 镜像对手；研究所拿规则牌后用规则；冬天熔断补仓
    "C": dict(seed=23, opp="镜像", self_idx=2, tiles=[3, 3, 4, 4], doors=["A", "A", "B", "A"], recognize=[0, 1],
              ev=[["data"], ["news", "tip"], ["price", "data"], ["price", "news"]],
              opt=["A", "C", "B", "A"], reason=["规则牌", "跟别人", "规则牌", "直觉"], plan=["跌了就加", "不定计划", "不定计划", "跌了就加"],
              follow=True, ring="留下", dial="加 1 份", second="补仓", decide="再加 1 份", calm="坐下"),
    # 快速版：先玩一场 → 初步画像 → 按推荐再玩一场
    "Q": dict(seed=5, quick=True, rounds=2, pick=0, opp="入门", self_idx=1, tiles=[1, 1, 1, 1], doors=["A"] * 4, recognize=[],
              ev=[["price", "data"], ["news"]], opt=["B", "A"], reason=["量价", "消息"], plan=["跌了就走", "不定计划"],
              follow=True, ring="离开", dial="不动", second="不看了", decide="拿着不动", calm="坐下"),
}

EV_CN = {"price": "量价", "data": "数据", "news": "消息", "tip": "锦囊"}

JS_BUTTONS = """() => {
  const out = [];
  document.querySelectorAll('button, a.btn').forEach((b, i) => {
    const r = b.getBoundingClientRect();
    const st = getComputedStyle(b);
    if (r.width <= 0 || r.height <= 0 || st.visibility === 'hidden' || st.display === 'none') return;
    out.push({ i, t: (b.innerText || '').trim().replace(/\\s+/g, ' '), d: !!b.disabled, c: String(b.className || ''),
      sheet: !!b.closest('.sheet'), slip: !!b.closest('.slip'), ev: b.className.includes && b.className.includes('ev-obj') });
  });
  return out;
}"""

SEED_JS = """(() => { let s = %d >>> 0; Math.random = () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; }; })();"""


class Bot:
    def __init__(self, page, cfg, out: Path):
        self.p = page
        self.cfg = cfg
        self.out = out
        self.n = 0
        self.last_sig = None
        self.log = []
        self.ev_opened = {}
        self.recognized = set()
        self.shot_ff = set()
        self.round = 1

    def state(self):
        raw = self.p.evaluate("() => localStorage.getItem('ts-game-v1')")
        return (json.loads(raw) or {}).get("state", {}).get("g") if raw else None

    def buttons(self):
        return self.p.evaluate(JS_BUTTONS)

    def click(self, b, label=None):
        ok = self.p.evaluate("""([i, t, c]) => {
          const all = Array.from(document.querySelectorAll('button, a.btn'));
          const norm = (x) => (x.innerText || '').trim().replace(/\\s+/g, ' ');
          let el = all[i];
          if (!el || norm(el) !== t) el = all.find((x) => norm(x) === t && String(x.className || '') === c) || all.find((x) => norm(x) === t);
          if (!el) return false;
          el.click();
          return true;
        }""", [b["i"], b["t"], b["c"]])
        self.log.append(("" if ok else "MISS ") + (label or b["t"][:40]))
        time.sleep(0.35)
        return True

    def find(self, bs, text, exact=False, enabled=True, sheet=None):
        for b in bs:
            if enabled and b["d"]:
                continue
            if sheet is not None and b["sheet"] != sheet:
                continue
            if (b["t"] == text) if exact else (text in b["t"]):
                return b
        return None

    def shot(self, label, full=False):
        self.n += 1
        name = f"{self.n:03d}_{re.sub(r'[^0-9A-Za-z_-]+', '_', label)[:40]}.png"
        self.p.screenshot(path=str(self.out / name), full_page=full)
        return name

    def season(self, g):
        return g["seasonIdx"] if g else 0

    def step(self):
        g = self.state()
        bs = self.buttons()
        texts = [b["t"] for b in bs]
        phase = g["phase"] if g else "home"
        step = g.get("step") if g else ""
        si = self.season(g)
        rec = g["seasons"][si] if g else {}
        sig = (phase, step if phase == "scene" else "", si, tuple(sorted(t for t in texts if t))[:8])
        if sig != self.last_sig:
            self.last_sig = sig
            self.shot(f"{phase}_{step if phase == 'scene' else ''}_s{si}")
        c = self.cfg

        if c.get("quick") and phase == "home" and self.find(bs, "先玩一场"):
            return self.click(self.find(bs, "先玩一场"))
        if not c.get("quick") and self.find(bs, "开始一局"):
            return self.click(self.find(bs, "开始一局"))
        if phase == "pick":
            cards = [x for x in bs if "card" in x["c"] and not x["sheet"]]
            if cards:
                time.sleep(0.8)
                self.shot("quick_pick", full=True)
                return self.click(cards[min(c.get("pick", 0), len(cards) - 1)], "pick-scene")
            return None
        if phase == "prologue":
            b = self.find(bs, "开始自评") or self.find(bs, "继续", exact=True)
            return b and self.click(b)
        if phase == "self":
            b = self.find(bs, "出发：春")
            if b:
                card = self.find(bs, c["opp"])
                if card and "dark" not in card["c"]:
                    self.click(card, "opp:" + c["opp"])
                    time.sleep(0.3)
                    self.shot("self_opp")
                return self.click(self.find(self.buttons(), "出发：春"))
            b = self.find(bs, "就是")
            if b:
                return self.click(b)
            cards = [x for x in bs if not x["sheet"] and "sp-card" in x["c"]]
            if cards:
                return self.click(cards[min(c["self_idx"], len(cards) - 1)], "self-pick")
            return None
        if phase == "map":
            want = c["tiles"][si]
            walks = [b for b in bs if b["t"].startswith("走 ") and b["sheet"]]
            if walks:
                vals = [int(re.match(r"走 (\d)", b["t"]).group(1)) for b in walks]
                k = min(range(len(vals)), key=lambda j: (abs(vals[j] - want), vals[j]))
                return self.click(walks[k], f"walk {vals[k]} (want {want})")
            flip = next((x for x in bs if x["sheet"] and "chance-back" in x["c"]), None)
            if flip:
                self.shot("chance_back")
                self.click(flip, "chance-flip")
                time.sleep(0.4)
                return True
            for t in ["收下 +1 研究点", "收好，去门口", "留下这张", "去门口"]:
                b = self.find(bs, t, exact=True, sheet=True)
                if b and not b["d"]:
                    if t == "去门口":
                        time.sleep(0.6)
                        self.shot("dataport_answered")
                    if t == "收好，去门口":
                        time.sleep(0.6)
                        self.shot("chance_answered")
                    return self.click(b)
            opts = [b for b in bs if b["sheet"] and "opt" in b["c"] and not b["d"]]
            if opts and ("收好，去门口" in texts or "去门口" in texts):
                return self.click(opts[(si + c["seed"]) % len(opts)], "answer")
            rules = [b for b in bs if b["sheet"] and "card" in b["c"] and not b["d"]]
            if "留下这张" in texts and rules:
                return self.click(rules[0], "keep-rule")
            calm_sit = self.find(bs, "坐下", sheet=True)
            if calm_sit and ("不坐" in " ".join(texts) or "又落到" in self.p.inner_text("body")):
                if c["calm"] == "不坐" and self.find(bs, "不坐", sheet=True):
                    return self.click(self.find(bs, "不坐", sheet=True), "calm-skip")
                return self.click(calm_sit, "calm-sit")
            doors = [b for b in bs if b["sheet"] and "card" in b["c"] and re.match(r"^[AB] ", b["t"])]
            if doors:
                want_d = c["doors"][si]
                pick = next((b for b in doors if b["t"].startswith(want_d)), doors[0])
                self.shot("doors")
                return self.click(pick, "door " + pick["t"][:1])
            for t in ["前往名场面之门 →", "推开门", "🎲 掷骰子"]:
                b = self.find(bs, t)
                if b:
                    return self.click(b)
            return None
        if phase == "scene":
            if step in ("blind", "evidence", "slip"):
                if not getattr(self, "cold_seen", False) and self.p.query_selector(".cold"):
                    self.cold_seen = True
                    time.sleep(1.8)
                    self.shot("cold_open")
                    try:
                        self.p.click(".cold", timeout=1500)
                    except Exception:
                        pass
                    return True
                b = self.find(bs, "看完了", exact=True, sheet=True)
                if b:
                    time.sleep(1.0)
                    self.shot("evidence_open")
                    return self.click(b)
                if si in c["recognize"] and si not in self.recognized:
                    b = self.find(bs, "就是它", sheet=True)
                    if b and not b["d"]:
                        self.recognized.add(si)
                        self.shot("recognize_sheet")
                        return self.click(b)
                    opts = [x for x in bs if x["sheet"] and "opt" in x["c"]]
                    if opts:
                        title = rec.get("scene")
                        names = {"s924": "924", "s2015": "2015", "smt": "茅台", "scb": "熔断", "squant": "量化", "soil": "原油"}
                        hit = next((x for x in opts if names.get(title, "@@") in x["t"]), opts[0])
                        return self.click(hit, "recognize " + hit["t"][:12])
                    b = self.find(bs, "认出来了")
                    if b:
                        time.sleep(1.8)
                        return self.click(b)
                sheet_cards = [x for x in bs if x["sheet"] and "card" in x["c"]]
                if sheet_cards:
                    return self.click(sheet_cards[0], "rule-card")
                want = c["ev"][si]
                done = self.ev_opened.setdefault(si, [])
                for k in want:
                    if k in done:
                        continue
                    obj = next((x for x in bs if "intel" in x["c"] and x["t"].startswith(EV_CN[k])), None)
                    if not done:
                        time.sleep(1.6)
                        self.shot("desk_full", full=True)
                    done.append(k)
                    if obj and "locked" not in obj["c"]:
                        self.click(obj, "ev " + k)
                        time.sleep(0.6)
                        return True
                opt = c["opt"][si]
                opts = [x for x in bs if x["slip"] and "opt" in x["c"]]
                chosen = [x for x in opts if " on" in x["c"] or x["c"].endswith("on")]
                if not chosen and opts:
                    target = next((x for x in opts if x["t"].startswith(opt) and not x["d"]), None) or next(x for x in opts if not x["d"])
                    return self.click(target, "opt " + target["t"][:1])
                chips = [x for x in bs if x["slip"] and "chip" in x["c"]]
                reason = c["reason"][si]
                if reason == "规则牌" and not any("规则牌" in x["t"] for x in chips):
                    reason = "量价"
                rchip = next((x for x in chips if x["t"].startswith(reason)), None)
                if rchip and " on" not in rchip["c"]:
                    return self.click(rchip, "reason " + reason)
                pchip = next((x for x in chips if x["t"] == c["plan"][si]), None)
                if pchip and " on" not in pchip["c"]:
                    return self.click(pchip, "plan " + c["plan"][si])
                b = self.find(bs, "下单 ·") or next((x for x in bs if "order-go" in x["c"] and not x["d"]), None)
                if b:
                    self.shot("slip_filled", full=True)
                    return self.click(b)
                return None
            if step == "flip":
                b = self.find(bs, "快进：")
                if b:
                    time.sleep(1.2)
                    self.shot("flip_cards", full=True)
                    return self.click(b)
                return None
            if step == "ff":
                body = self.p.inner_text("body")
                key = (si, body[:0])
                for t in (["照计划"] if c["follow"] else ["先不了"]):
                    b = self.find(bs, t)
                    if b:
                        self.shot("ff_plan_prompt")
                        return self.click(b)
                b = self.find(bs, "揭幕：这到底是哪一次")
                if b:
                    time.sleep(0.8)
                    self.shot("ff_done", full=True)
                    return self.click(b)
                order = ["结算这一段", c["decide"], "拿着不动", "继续不参与", "继续等", "▶ 开盘", "▶ 继续", c["ring"], "再过三周",
                         "翻沙漏", c["second"], c["dial"], "=不动", "第三次熔断之后", "接下来四个交易日", "=结算", "签收负债牌", "记下这一笔"]
                for t in order:
                    exact = t.startswith("=")
                    t = t.lstrip("=")
                    b = self.find(bs, t, exact=exact)
                    if b:
                        if t in ("结算这一段", "再过三周", "第三次熔断之后", "接下来四个交易日", "签收负债牌", "记下这一笔", "结算") or t == c["ring"]:
                            self.shot("ff_" + t[:6])
                        return self.click(b)
                if "冷静期" in body and (si, "freeze") not in self.shot_ff:
                    self.shot_ff.add((si, "freeze"))
                    self.shot("ff_freeze")
                if "开盘" in body and (si, "bell") not in self.shot_ff and "节后第一天" in body:
                    self.shot_ff.add((si, "bell"))
                    self.shot("ff_bell")
                if "国庆长假" in body and (si, "hol") not in self.shot_ff:
                    self.shot_ff.add((si, "hol"))
                    time.sleep(2.5)
                    self.shot("ff_holiday")
                return None
            if step == "reveal":
                b = self.find(bs, "入账")
                if b:
                    time.sleep(2.8)
                    self.shot("reveal_top")
                    self.click(b)
                    time.sleep(1.2)
                    self.shot("reveal_booked")
                    return True
                b = self.find(bs, "去驿站")
                if b:
                    time.sleep(1.5)
                    self.shot("reveal_full", full=True)
                    return self.click(b)
                return None
        if phase == "station":
            opts = [x for x in bs if x["sheet"] and "opt" in x["c"]]
            if opts:
                self.shot("retest")
                return self.click(opts[c["seed"] % len(opts)], "retest-answer")
            chips = [x for x in bs if x["sheet"] and "chip" in x["c"]]
            if chips:
                self.shot("retest_pick")
                return self.click(chips[0], "retest-pick " + chips[0]["t"][:6])
            b = self.find(bs, "抽补测牌")
            if b:
                return self.click(b)
            b = self.find(bs, "收下，去")
            if b:
                time.sleep(1.4)
                self.shot("station_coin", full=True)
                return self.click(b)
            return None
        if phase == "ending":
            if c.get("rounds", 1) > self.round:
                b = self.find(bs, "再玩一场")
                if b:
                    time.sleep(1.0)
                    self.shot(f"quick_ending_r{self.round}", full=True)
                    self.round += 1
                    return self.click(b)
                return None
            return "ending"
        return None

    def run(self, max_steps=600):
        idle = 0
        t0 = time.time()
        for _ in range(max_steps):
            r = self.step()
            if r == "ending":
                return True
            if r is None:
                idle += 1
                time.sleep(0.5)
                if idle > 80:
                    self.shot("stuck", full=True)
                    return False
            else:
                idle = 0
            if time.time() - t0 > 900:
                return False
        return False


def ending(bot: Bot):
    p = bot.p
    time.sleep(4.5)
    bot.shot("ending_top")
    p.evaluate("() => window.scrollTo(0, 0)")
    time.sleep(1.5)
    bot.shot("ending_full", full=True)
    t = bot.find(bot.buttons(), "画像依据", exact=True)
    if t:
        bot.click(t)
        time.sleep(1.0)
        bot.shot("ending_profile", full=True)
    bs = bot.buttons()
    b = bot.find(bs, "看依据")
    if b:
        bot.click(b)
        time.sleep(0.6)
    t = bot.find(bot.buttons(), "输赢", exact=True)
    if t:
        bot.click(t)
        time.sleep(1.0)
        bot.shot("ending_score", full=True)
    b = bot.find(bot.buttons(), "生成分享图")
    if b:
        bot.click(b)
        time.sleep(3.5)
        bot.shot("share_sheet")
        c = bot.find(bot.buttons(), "关闭", exact=True)
        c and bot.click(c)
    b = bot.find(bot.buttons(), "画像 JSON")
    if b:
        bot.click(b)
        time.sleep(1.0)
        bot.shot("profile_json")
    return bot.state()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5179/ts/")
    ap.add_argument("--run", default="A")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=float, default=1.5)
    a = ap.parse_args()
    cfg = RUNS[a.run]
    out = Path(a.out or ROOT / "e2e" / a.run)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    errors = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=a.scale, is_mobile=True, has_touch=True, locale="zh-CN")
        ctx.add_init_script(SEED_JS % cfg["seed"])
        page = ctx.new_page()
        page.on("console", lambda m: m.type in ("error", "warning") and errors.append(f"{m.type}: {m.text[:300]}"))
        page.on("pageerror", lambda e: errors.append(f"pageerror: {str(e)[:300]}"))
        page.goto(a.base, wait_until="networkidle")
        page.evaluate("() => localStorage.clear()")
        page.goto(a.base, wait_until="networkidle")
        bot = Bot(page, cfg, out)
        ok = bot.run()
        g = ending(bot) if ok else bot.state()
        br.close()
    summary = {"run": a.run, "ok": ok, "screens": bot.n, "errors": errors[:40], "log": bot.log}
    if g:
        summary["result"] = {"money": g.get("money"), "rp": g.get("rp"), "aiMoney": g.get("aiMoney"),
                             "seasons": [{k: r.get(k) for k in ("scene", "tile", "option", "reason", "plan", "evidence", "money", "stars", "coin", "coinHalf", "recognized", "calm", "ruleKept")} for r in g.get("seasons", [])]}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("run", "ok", "screens")}, ensure_ascii=False), "errors:", len(errors))
    for e in errors[:15]:
        print("  ", e)


if __name__ == "__main__":
    main()
