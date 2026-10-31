"""录宣传片的手机素材（线上真站、真实按住 / 松手手势），输出 webm + 时间标记。

  python3.11 video/tools/rec_phone.py --base https://meetmind.online/ts/ --out /tmp/ts-video/raw --only play,demo,qr
"""
import argparse, json, shutil, sys, time
from pathlib import Path

sys.path.insert(0, "/mnt/pandaai-trading-species/qa")
sys.path.insert(0, "/mnt/pandaai-trading-species/qa/video")
import e2e_play as E  # noqa: E402
import rec as R  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

FINGER_JS = """
(() => {
  const css = `.__finger{position:fixed;width:84px;height:84px;margin:-42px 0 0 -42px;border-radius:50%;
    background:radial-gradient(circle, rgba(255,255,255,.55) 0 30%, rgba(31,26,20,.28) 31% 100%);
    border:4px solid rgba(31,26,20,.75);pointer-events:none;z-index:99999;display:none;
    box-shadow:0 0 0 10px rgba(31,26,20,.10)}`;
  let x = 0, y = 0, el = null;
  const ensure = () => { if (el) return el; const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
    el = document.createElement('div'); el.className = '__finger'; document.body.appendChild(el); return el; };
  addEventListener('mousemove', (e) => { x = e.clientX; y = e.clientY; if (el) { el.style.left = x + 'px'; el.style.top = y + 'px'; } }, true);
  addEventListener('mousedown', (e) => { const f = ensure(); f.style.left = e.clientX + 'px'; f.style.top = e.clientY + 'px'; f.style.display = 'block'; }, true);
  addEventListener('mouseup', () => { if (el) el.style.display = 'none'; }, true);
})();
"""


class FilmBot(R.SlowBot):
    def live_game(self, c, si, rec):
        p = self.p
        p.wait_for_selector(".arc-btn", timeout=8000)
        self.mark("game:ready")
        time.sleep(2.2)

        def press(on):
            b = p.query_selector(".arc-btn")
            bb = b.bounding_box() if b else None
            if bb:
                p.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            (p.mouse.down if on else p.mouse.up)()
            self.mark("finger:" + ("down" if on else "up"))

        press(True)
        down, seen, released = True, set(), False
        t0 = time.time()
        while not p.query_selector(".arc-reveal"):
            if p.query_selector(".arc-offer") and "offer" not in seen:
                seen.add("offer")
                self.mark("game:offer")
                time.sleep(1.6)
                if down:
                    press(False)
                    down = False
                btn = p.get_by_role("button", name="借 1 倍")
                bb = btn.bounding_box()
                p.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2, steps=8)
                time.sleep(0.4)
                btn.click()
                self.mark("game:borrow")
                time.sleep(0.6)
                press(True)
                down = True
            lab = p.evaluate("() => (document.querySelector('.arc-toast') || {}).innerText || ''")
            if down and not released and "千股跌停" in lab:
                self.mark("game:limit")
                time.sleep(1.2)
                press(False)
                down, released = False, True
                self.mark("game:release")
            toast = p.query_selector(".arc-toast")
            if toast:
                t = toast.inner_text()
                if t not in seen:
                    seen.add(t)
                    self.mark("toast:" + t[:16])
            if p.query_selector(".arc-over.dark") and "liq" not in seen:
                seen.add("liq")
                self.mark("game:liquidated")
            if time.time() - t0 > 120:
                break
            time.sleep(0.05)
        if down:
            p.mouse.up()
        self.mark("game:reveal")
        self.log.append(f"live {rec.get('scene')} {time.time() - t0:.1f}s")
        return True


def ctx_of(br, vdir):
    return br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                          locale="zh-CN", record_video_dir=str(vdir), record_video_size={"width": 780, "height": 1688})


def rec_play(br, base, out):
    vdir = out / "_play"
    ctx = ctx_of(br, vdir)
    cfg = dict(E.RUNS["Q"], rounds=1, pick=1, self_idx=1, ev=[["price", "data"]], opt=["A"], reason=["量价"],
               plan=["跌了就走"], follow=False, name="film")
    ctx.add_init_script(E.SEED_JS % cfg["seed"])
    ctx.add_init_script(R.TAP_JS)
    ctx.add_init_script(FINGER_JS)
    page = ctx.new_page()
    page.goto(base, wait_until="networkidle")
    page.evaluate("() => localStorage.clear()")
    marks = []
    t0 = time.time()
    page.goto(base, wait_until="networkidle")
    bot = FilmBot(page, cfg, out, marks, t0)
    bot.mark("home")
    time.sleep(2.5)
    ok = bot.run()
    bot.mark("judge")
    page.wait_for_selector(".arc-final", timeout=40000)
    for i in range(6):
        bot.mark(f"final:{i}")
        time.sleep(4.5)
        if not page.query_selector(".arc-tapnext"):
            break
        page.evaluate("() => window.__tap(195, 430)")
        time.sleep(0.15)
        page.click(".arc-final", position={"x": 195, "y": 430})
    bot.mark("end")
    time.sleep(1.0)
    print("\n".join(map(str, bot.log[-30:])))
    video = page.video.path()
    ctx.close()
    shutil.move(video, out / "play.webm")
    shutil.rmtree(vdir, ignore_errors=True)
    return ok, marks


def rec_pages(br, base, out):
    """桌游扫码页：盲测页 → 在手机上玩这一场；揭幕页；熔断沙漏；开局页"""
    res = {}
    for name, path, wait in (("qr_blind", "b/s2015", 7), ("qr_reveal", "r/s2015", 16), ("qr_ff", "ff/scb", 9), ("qr_start", "start", 6), ("qr_record", "record", 6)):
        vdir = out / ("_" + name)
        ctx = ctx_of(br, vdir)
        ctx.add_init_script(R.TAP_JS)
        page = ctx.new_page()
        marks = []
        t0 = time.time()
        page.goto(base + path, wait_until="networkidle")
        marks.append((round(time.time() - t0, 2), "loaded"))
        time.sleep(wait)
        if name == "qr_blind":
            R.tap_text(page, "在手机上玩这一场")
            marks.append((round(time.time() - t0, 2), "tap:play-here"))
            time.sleep(4)
        video = page.video.path()
        ctx.close()
        shutil.move(video, out / f"{name}.webm")
        shutil.rmtree(vdir, ignore_errors=True)
        res[name] = {"marks": marks}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://meetmind.online/ts/")
    ap.add_argument("--out", default="/tmp/ts-video/raw")
    ap.add_argument("--only", default="play,demo,qr")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mf = out / "marks.json"
    res = json.loads(mf.read_text()) if mf.exists() else {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        if "play" in a.only:
            ok, m = rec_play(br, a.base, out)
            res["play"] = {"ok": ok, "marks": m}
        if "demo" in a.only:
            R.new_ctx = ctx_of
            res["demo"] = {"marks": R.rec_demo(br, a.base, out)}
        if "qr" in a.only:
            res.update(rec_pages(br, a.base, out))
        br.close()
    mf.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: len(v["marks"]) for k, v in res.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
