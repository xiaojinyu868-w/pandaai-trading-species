"""录视频素材：快速版一局（自评大象，做法像猎豹）+ 评委演示台改一个选择。

  python3.11 qa/video/rec.py --base https://meetmind.online/ts/ --out /tmp/ts-video/raw
"""
import argparse, json, shutil, sys, time
from pathlib import Path

sys.path.insert(0, "/mnt/pandaai-trading-species/qa")
import e2e_play as E  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

TAP_JS = """
(() => {
  const css = `.__tap{position:fixed;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;
    background:rgba(212,67,42,.35);border:3px solid rgba(212,67,42,.9);pointer-events:none;z-index:99999;
    animation:__tapk .55s ease-out forwards}
    @keyframes __tapk{0%{transform:scale(.4);opacity:1}100%{transform:scale(1.25);opacity:0}}`;
  const add = () => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); };
  if (document.head) add(); else document.addEventListener('DOMContentLoaded', add);
  window.__tap = (x, y) => { const d = document.createElement('div'); d.className = '__tap';
    d.style.left = x + 'px'; d.style.top = y + 'px'; document.body.appendChild(d); setTimeout(() => d.remove(), 700); };
})();
"""

FIND_JS = """([i, t, c]) => {
  const all = Array.from(document.querySelectorAll('button, a.btn'));
  const norm = (x) => (x.innerText || '').trim().replace(/\\s+/g, ' ');
  let el = all[i];
  if (!el || norm(el) !== t) el = all.find((x) => norm(x) === t && String(x.className || '') === c) || all.find((x) => norm(x) === t);
  if (!el) return null;
  window.__el = el;
  el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  return true;
}"""

PRESS_JS = """() => { const el = window.__el; if (!el) return false;
  const r = el.getBoundingClientRect(); window.__tap(r.left + r.width / 2, r.top + r.height / 2);
  setTimeout(() => el.click(), 160); return true; }"""


class SlowBot(E.Bot):
    def __init__(self, page, cfg, out, marks, t0):
        super().__init__(page, cfg, out)
        self.marks, self.t0 = marks, t0

    def mark(self, label):
        self.marks.append((round(time.time() - self.t0, 2), label))

    def click(self, b, label=None):
        ok = self.p.evaluate(FIND_JS, [b["i"], b["t"], b["c"]])
        if ok:
            time.sleep(0.45)
            self.p.evaluate(PRESS_JS)
        self.log.append(("" if ok else "MISS ") + (label or b["t"][:40]))
        self.mark("tap:" + (label or b["t"][:24]))
        time.sleep(1.05)
        return True

    def shot(self, label, full=False):
        self.n += 1
        self.mark("screen:" + label)
        time.sleep(1.2)
        return label


def smooth_scroll(p, dy, steps=24, pause=0.03):
    for _ in range(steps):
        p.mouse.wheel(0, dy / steps)
        time.sleep(pause)


def scroll_to_text(p, text, block="start"):
    p.evaluate("""([t, b]) => { const els = Array.from(document.querySelectorAll('div, h2, h3, span, button'));
      const el = els.find((x) => x.childElementCount < 6 && (x.innerText || '').trim().startsWith(t));
      if (el) el.scrollIntoView({ block: b, behavior: 'smooth' }); return !!el; }""", [text, block])


def tap_text(p, text, sel="button"):
    ok = p.evaluate("""([t, s]) => { const el = Array.from(document.querySelectorAll(s)).find((x) => (x.innerText || '').trim().replace(/\\s+/g, ' ').startsWith(t));
      if (!el) return false; window.__el = el; el.scrollIntoView({ block: 'center', behavior: 'smooth' }); return true; }""", [text, sel])
    if not ok:
        print("MISS", text)
        return False
    time.sleep(0.6)
    p.evaluate(PRESS_JS)
    time.sleep(1.0)
    return True


def new_ctx(br, vdir):
    return br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                          locale="zh-CN", record_video_dir=str(vdir), record_video_size={"width": 390, "height": 844})


def rec_quick(br, base, out):
    vdir = out / "_quick"
    ctx = new_ctx(br, vdir)
    cfg = dict(E.RUNS["Q"], rounds=1)
    ctx.add_init_script(E.SEED_JS % cfg["seed"])
    ctx.add_init_script(TAP_JS)
    page = ctx.new_page()
    page.goto(base, wait_until="networkidle")
    page.evaluate("() => localStorage.clear()")
    marks = []
    t0 = time.time()
    page.goto(base, wait_until="networkidle")
    bot = SlowBot(page, cfg, out, marks, t0)
    bot.mark("home")
    time.sleep(3.0)
    ok = bot.run()
    bot.mark("ending")
    time.sleep(5.0)
    for label in ["一枚物种币", "画像还很初步", "PandaAI · Qube", "学习路线", "当场就能做", "两个你", "画像 · 每条判断", "徽章"]:
        if label == "两个你":
            tap_text(page, "画像依据")
        scroll_to_text(page, label)
        bot.mark("ending:" + label)
        time.sleep(3.2)
    page.evaluate("() => window.scrollTo({ top: 0, behavior: 'smooth' })")
    time.sleep(1.5)
    video = page.video.path()
    ctx.close()
    shutil.move(video, out / "quick.webm")
    shutil.rmtree(vdir, ignore_errors=True)
    return ok, marks


def rec_demo(br, base, out):
    vdir = out / "_demo"
    ctx = new_ctx(br, vdir)
    ctx.add_init_script(TAP_JS)
    page = ctx.new_page()
    marks = []
    t0 = time.time()
    mark = lambda l: marks.append((round(time.time() - t0, 2), l))
    page.goto(base + "demo", wait_until="networkidle")
    mark("demo:top")
    time.sleep(4.0)
    tap_text(page, "等证据", "tr")
    mark("demo:careful")
    time.sleep(2.0)
    tap_text(page, "A 节后开盘追入")
    mark("demo:changed")
    time.sleep(1.5)
    scroll_to_text(page, "实时结果")
    mark("demo:result")
    time.sleep(6.0)
    smooth_scroll(page, 520)
    mark("demo:rec")
    time.sleep(4.0)
    scroll_to_text(page, "PandaAI · Qube")
    mark("demo:qube")
    time.sleep(4.0)
    page.evaluate("() => window.scrollTo({ top: 0, behavior: 'smooth' })")
    mark("demo:back")
    time.sleep(3.0)
    video = page.video.path()
    ctx.close()
    shutil.move(video, out / "demo.webm")
    shutil.rmtree(vdir, ignore_errors=True)
    return marks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://meetmind.online/ts/")
    ap.add_argument("--out", default="/tmp/ts-video/raw")
    ap.add_argument("--only", default="quick,demo")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        if "quick" in a.only:
            ok, m = rec_quick(br, a.base, out)
            res["quick"] = {"ok": ok, "marks": m}
        if "demo" in a.only:
            res["demo"] = {"marks": rec_demo(br, a.base, out)}
        br.close()
    old = json.loads((out / "marks.json").read_text()) if (out / "marks.json").exists() else {}
    old.update(res)
    (out / "marks.json").write_text(json.dumps(old, ensure_ascii=False, indent=1))
    print(json.dumps({k: (v.get("ok"), len(v["marks"])) for k, v in res.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
