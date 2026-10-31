"""Playwright 渲染：HTML → 矢量 PDF / PNG 预览，并在导出前做自动缩字与溢出检查。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

from .paths import BUILD

FIT_JS = r"""
() => {
  const pt = 96 / 72;
  const out = [];
  const els = Array.from(document.querySelectorAll('.fit'));
  // 内层先缩，外层后缩
  els.sort((a, b) => b.querySelectorAll('*').length < a.querySelectorAll('*').length ? -1 : 1);
  for (const el of els.reverse()) {
    const min = parseFloat(el.dataset.min || '7');
    let fs = parseFloat(getComputedStyle(el).fontSize) / pt;
    const over = () => el.scrollHeight > el.clientHeight + 0.6 || el.scrollWidth > el.clientWidth + 0.6;
    let guard = 0;
    while (over() && fs > min + 0.001 && guard < 80) {
      fs = Math.max(min, fs - 0.25);
      el.style.fontSize = fs + 'pt';
      guard++;
    }
    if (over()) {
      const card = el.closest('[data-key]');
      out.push({key: card ? card.dataset.key : '?', what: el.dataset.what || el.className, text: el.innerText.slice(0, 80),
                h: el.scrollHeight - el.clientHeight, w: el.scrollWidth - el.clientWidth});
      el.dataset.overflow = '1';
    }
  }
  // 最小字号检查：所有可见文字 >= 7pt（图表 svg 内 >= 6pt）
  const small = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const t = n.textContent.trim();
    if (!t) continue;
    const p = n.parentElement;
    if (!p) continue;
    const cs = getComputedStyle(p);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    if (p.closest('.slug') || p.closest('.nocheck')) continue;
    let fs = parseFloat(cs.fontSize) / pt;
    const inSvg = !!p.closest('svg');
    if (inSvg) {
      // svg 里用 mm 作用户单位：按实际渲染高度估算
      const svg = p.closest('svg');
      const r = svg.getBoundingClientRect();
      const vb = svg.viewBox && svg.viewBox.baseVal;
      if (vb && vb.width) fs = fs * (r.width / vb.width);
    }
    const lim = inSvg ? 5.95 : 6.95;
    if (fs < lim) {
      const card = p.closest('[data-key]');
      small.push({key: card ? card.dataset.key : '?', size: Math.round(fs * 100) / 100, text: t.slice(0, 30)});
    }
  }
  return {overflow: out, small: small.slice(0, 60)};
}
"""


class Renderer:
    def __init__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(args=["--font-render-hinting=none", "--disable-lcd-text"])
        self.issues: list[dict] = []

    def close(self):
        try:
            self.browser.close()
        finally:
            self.pw.stop()

    def _open(self, html_path: Path, scale: float = 1.0, viewport=None):
        ctx = self.browser.new_context(device_scale_factor=scale, viewport=viewport or {"width": 1200, "height": 900})
        page = ctx.new_page()
        page.goto(html_path.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(150)
        return ctx, page

    def fit(self, page, name):
        res = page.evaluate(FIT_JS)
        for o in res["overflow"]:
            self.issues.append({"file": name, "type": "overflow", **o})
        for s in res["small"]:
            self.issues.append({"file": name, "type": "small", **s})
        return res

    def pdf(self, html: str, name: str, out_pdf: Path, w: float, h: float):
        hp = BUILD / "html" / f"{name}.html"
        hp.write_text(html, encoding="utf-8")
        ctx, page = self._open(hp)
        page.emulate_media(media="print")
        self.fit(page, name)
        page.pdf(path=str(out_pdf), width=f"{w}mm", height=f"{h}mm", print_background=True,
                 prefer_css_page_size=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        ctx.close()
        return out_pdf

    def png(self, html: str, name: str, out_png: Path, dpi: float = 150, selector: str | None = None,
            full_page=True, viewport=None):
        hp = BUILD / "html" / f"{name}.html"
        hp.write_text(html, encoding="utf-8")
        ctx, page = self._open(hp, scale=dpi / 96.0, viewport=viewport)
        self.fit(page, name)
        if selector:
            page.locator(selector).first.screenshot(path=str(out_png))
        else:
            page.screenshot(path=str(out_png), full_page=full_page)
        ctx.close()
        return out_png

    def pngs_per_element(self, html: str, name: str, selector: str, out_paths: list[Path], dpi: float = 150, viewport=None):
        hp = BUILD / "html" / f"{name}.html"
        hp.write_text(html, encoding="utf-8")
        ctx, page = self._open(hp, scale=dpi / 96.0, viewport=viewport)
        self.fit(page, name)
        loc = page.locator(selector)
        cnt = loc.count()
        for i in range(min(cnt, len(out_paths))):
            loc.nth(i).screenshot(path=str(out_paths[i]))
        ctx.close()


def pdf_pages(p: Path) -> int:
    out = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0


def pdf_size_mm(p: Path):
    out = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Page size:"):
            parts = line.split()
            w, h = float(parts[2]), float(parts[4])
            return round(w / 72 * 25.4, 1), round(h / 72 * 25.4, 1)
    return None


def pdf_fonts(p: Path) -> list[str]:
    out = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True).stdout
    return out.splitlines()[2:]
