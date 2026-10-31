"""A6 牌（105×148）：场景牌（盲测面 / 门牌背）、揭幕牌（正 / 共用背）、物种牌、序章、速查卡、名场面道具板。"""

from __future__ import annotations

from . import art, charts, content, icons, qrsvg
from .core import Card, esc, trim
from .model import SEASON_EN, SEASON_EN2, Model, short_source, strip_teaser_prefix
from .tokens import C, SEASON, SPECIES_COLOR, SPECIES_EN

W, H = 105.0, 148.0
M = 5.5  # 正文左右边距（距裁切线）
DISCLAIMER = "投资者教育游戏，不构成投资建议"


def _img(uri, x, y, w, h, pos="50% 40%", extra=""):
    return (f'<img class="art" src="{uri}" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;'
            f'object-position:{pos};{extra}">')


def _strip(season, left, right, top=-3.0, h=12.5, bg=None, fg=None):
    col = bg or SEASON[season]["color"]
    fg = fg or C["paper_light"]
    return (f'<div class="a" style="left:-3mm;top:{top}mm;width:{W + 6}mm;height:{h}mm;background:{col}"></div>'
            f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{top + 3}mm;height:{h - 3}mm;color:{fg};">'
            f'{left}<div class="sp"></div>{right}</div>')


def _season_left(sc, extra=""):
    s = sc["season"]
    return (f'<div class="row gap1"><span class="disp" style="font-size:14pt;">{esc(sc["season_cn"])} · {esc(sc["season_name"])}</span>'
            f'<span class="caps" style="font-size:7pt;opacity:.9;margin-left:1.5mm;letter-spacing:.14em">{SEASON_EN[s]} · {SEASON_EN2[s]}</span>{extra}</div>')


def _opts(sc, size=8.4):
    cells = []
    for o in sc["opts"]:
        note = f'<small>{esc(o["note"])}</small>' if o.get("note") else ""
        cells.append(f'<div class="opt"><span class="kb">{esc(o["key"])}</span><span class="t" style="font-size:{size}pt">{esc(o["text"])}{note}</span>'
                     f'{icons.dots(o["shares"], 3, 2.5, 0.8)}</div>')
    return f'<div class="opts">{"".join(cells)}</div>'


# ---------------------------------------------------------------- 场景牌 · 盲测面

def scene_blind(m: Model, sc: dict) -> Card:
    imgs = art.scene_images(sc["id"])
    b = sc["blind"]
    s = sc["season"]
    scol = SEASON[s]["color"]
    door = sc.get("door", "A")
    right = (f'<span class="b7" style="font-size:7.5pt;letter-spacing:.08em">名场面 · 门 {esc(door)}</span>'
             f'<span class="chip" style="margin-left:2mm;background:{C["paper_light"]};color:{C["ink"]};height:4.6mm;font-size:7pt">盲测面</span>')
    parts = [_strip(s, _season_left(sc), right)]
    parts.append(f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>')
    art_top, art_h = 10.7, 46.3
    if imgs.get("blind"):
        parts.append(_img(imgs["blind"]["uri"], -3, art_top, W + 6, art_h, "50% 38%"))
    if imgs.get("placeholder"):
        parts.append(f'<div class="a" style="left:-3mm;top:{art_top}mm;width:{W + 6}mm;height:{art_h}mm;background:{scol};mix-blend-mode:multiply;opacity:.55"></div>')
    # 标题与处境
    y = art_top + art_h + 3.0
    parts.append(f'<div class="a disp fit" data-min="12" data-what="标题" style="left:{M}mm;right:{M}mm;top:{y}mm;height:8.2mm;font-size:17pt;white-space:nowrap;">{esc(b["headline"])}</div>')
    y += 8.6
    lines = "".join(f"<li>{esc(t)}</li>" for t in b.get("lines", [])[:3])
    parts.append(f'<ul class="a dots fit lines" data-min="7" data-what="处境" style="left:{M}mm;right:{M}mm;top:{y}mm;height:15.6mm;font-size:7.8pt;line-height:1.36">{lines}</ul>')
    y += 16.6
    # 走势 + 二维码
    qs = 17.0
    qw, qh = qrsvg.block_size(qs, 2.2, "扫码 · 手机看盲测")
    chart_w = W - 2 * M - qw - 3.0
    ch = charts.blind_chart(b["chart"]["values"], b["chart"].get("t_index"), chart_w, qh - 3.2)
    parts.append(f'<div class="a" style="left:{M}mm;top:{y}mm;width:{chart_w}mm;height:{qh}mm;">{ch}'
                 f'<div class="nowrap" style="font-size:7pt;color:{C["ink_2"]};margin-top:0.4mm">{esc(b["chart"].get("label", "起点 = 100"))}</div></div>')
    parts.append(qrsvg.block(sc["qr"]["blind"], W - M - qw + 0.5, y - 0.5, qs, 2.2, "扫码 · 手机看盲测", where=f"场景牌盲测面 {sc['id']}"))
    y += qh + 1.6
    # 处境 + 问题
    parts.append(f'<div class="a row fit" data-min="7.4" data-what="问题" style="left:{M}mm;right:{M}mm;top:{y}mm;height:5.4mm;gap:2mm;white-space:nowrap">'
                 f'<span style="font-size:8pt;color:{C["ink_2"]}">{esc(b.get("position", ""))}</span>'
                 f'<span class="b7" style="font-size:9pt">{esc(b.get("question", ""))}</span></div>')
    y += 6.0
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{y}mm;">{_opts(sc)}</div>')
    # 页脚
    mode = sc["mode_cn"]
    mode_tip = "按座位顺序公开选项" if "依次" in mode else "各自暗中勾选，一起亮单"
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;bottom:{H - 143.2}mm;height:5mm;gap:1.6mm">'
                 f'<span class="chip ink">{esc(mode)}</span><span style="font-size:7pt;color:{C["ink_2"]}">{mode_tip}</span>'
                 f'<div class="sp"></div><span class="disc">{DISCLAIMER}</span></div>')
    return Card(key=f"blind-{sc['id']}", w=W, h=H, html=trim("".join(parts), W, H),
                qr=[sc["qr"]["blind"]], label=f"场景牌 · {sc['season_cn']}{door} · 盲测面")


# ---------------------------------------------------------------- 场景牌 · 门牌背（无剧透）

def scene_door(m: Model, sc: dict) -> Card:
    s = sc["season"]
    scol = SEASON[s]["color"]
    imgs = art.scene_images(sc["id"])
    door = sc.get("door", "A")
    duo = None
    if imgs.get("blind"):
        duo = art.duotone(f"blind_{sc['id']}", C["ink"], SEASON[s]["color"], f"duo_{sc['id']}")
    aw, ah = 66.0, 84.0
    ax, ay = (W - aw) / 2, 22.0
    r = aw / 2
    px = 96 / 25.4
    clip = (f"path('M 0 {r * px:.2f} A {r * px:.2f} {r * px:.2f} 0 0 1 {aw * px:.2f} {r * px:.2f} "
            f"L {aw * px:.2f} {ah * px:.2f} L 0 {ah * px:.2f} Z')")
    arch_path = f"M0,{r} A{r},{r} 0 0 1 {aw},{r} L{aw},{ah} L0,{ah} Z"
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{scol}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;">{icons.sun_rays(W + 6, H + 6, (W + 6) / 2, ay + r + 3, 28, C["paper_light"], 0.10)}</div>']
    # 门框（粗，不怕正反偏移）
    fr = 3.2
    parts.append(f'<svg class="a" style="left:{ax - fr}mm;top:{ay - fr}mm" width="{aw + 2 * fr}mm" height="{ah + fr + 0.01}mm" viewBox="{-fr} {-fr} {aw + 2 * fr} {ah + fr}">'
                 f'<path d="{arch_path}" fill="{C["paper_light"]}" stroke="{C["paper_light"]}" stroke-width="{2 * fr}" stroke-linejoin="round"/></svg>')
    inner = ""
    if duo:
        # 图放大一些、顶对齐，让插画右下角的空白标签框落在门洞外
        inner = f'<img src="{duo["uri"]}" style="position:absolute;left:0;top:0;width:{aw}mm;height:{ah / 0.84:.2f}mm;object-fit:cover;object-position:50% 0%;">'
    parts.append(f'<div class="a" style="left:{ax}mm;top:{ay}mm;width:{aw}mm;height:{ah}mm;clip-path:{clip};background:{C["ink"]}">{inner}'
                 f'<div style="position:absolute;left:0;right:0;bottom:0;height:22mm;background:linear-gradient(to bottom, rgba(42,42,28,0), rgba(42,42,28,.85))"></div></div>')
    # 门牌号
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:{ay + ah - 19}mm;font-size:34pt;color:{C["paper_light"]};line-height:1">门 {esc(door)}</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:{ay + ah - 6.2}mm;font-size:7.5pt;font-weight:700;letter-spacing:.3em;color:{C["sun"]}">DOOR {esc(door)}</div>')
    # 顶部季节
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:7mm;font-size:15pt;color:{C["paper_light"]}">{esc(sc["season_cn"])} · {esc(sc["season_name"])}</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:14mm;font-size:7pt;color:{C["paper_light"]};opacity:.9">{SEASON_EN[s]} · {SEASON_EN2[s]} · 名场面</div>')
    # 预告
    teaser = strip_teaser_prefix(sc["door_teaser"])
    parts.append(f'<div class="a center fit" data-min="8" data-what="门牌预告" style="left:{M + 2}mm;right:{M + 2}mm;top:{ay + ah + 6}mm;height:7.6mm;font-size:11pt;font-weight:700;color:{C["paper_light"]};white-space:nowrap">{esc(teaser)}</div>')
    tier_note = "P1 扩展" if sc.get("tier") == "P1" else ""
    parts.append(f'<div class="a center" style="left:0;right:0;top:{ay + ah + 14.5}mm;font-size:7.5pt;color:{C["paper_light"]};opacity:.92">放在棋盘{esc(sc["season_cn"])}季门 {esc(door)} · 走到门口再翻开{(" · " + tier_note) if tier_note else ""}</div>')
    return Card(key=f"door-{sc['id']}", w=W, h=H, html=trim("".join(parts), W, H),
                label=f"场景牌 · {sc['season_cn']}{door} · 门牌背")


# ---------------------------------------------------------------- 揭幕牌 · 正面

def _payoff_table(sc):
    rv = sc["reveal"]
    rows = rv.get("payoff_rows", [])
    opts = {o["key"]: o for o in sc["opts"]}
    seg2 = rv.get("seg2", {}) or {}
    head = (f'<div class="row b7" style="font-size:7pt;color:{C["ink_2"]};height:3.6mm;border-bottom:0.5pt solid {C["ink"]}">'
            f'<span style="width:13.2mm">选项·份数</span><span style="width:8.8mm;text-align:right">第一段</span>'
            f'<span style="width:8.8mm;text-align:right">第二段</span><span class="sp"></span><span>合计</span></div>')
    body = []
    for r in rows:
        tot = r.get("total", 0)
        col = charts.dir_color(tot)
        arrow = charts.arrow(tot)

        def num(v):
            if v is None:
                return "—"
            return ("+" if v > 0 else ("−" if v < 0 else "")) + str(abs(v))
        sh = r.get("shares", opts.get(r["key"], {}).get("shares", 0))
        body.append(f'<div class="row" style="height:4.25mm;border-bottom:0.5pt dotted {C["ink_3"]}">'
                    f'<span class="kb" style="width:3.6mm;height:3.6mm;font-size:7.5pt;margin-right:1mm">{esc(r["key"])}</span>'
                    f'<span style="width:8.6mm">{icons.dots(sh, 3, 1.9, 0.5, stroke=0.25)}</span>'
                    f'<span class="num" style="width:8.8mm;text-align:right;font-size:8.5pt">{num(r.get("seg1"))}</span>'
                    f'<span class="num" style="width:8.8mm;text-align:right;font-size:8.5pt">{num(r.get("seg2"))}</span><span class="sp"></span>'
                    f'<span class="num b7" style="color:{col};font-size:10pt">{arrow if tot else ""}{num(tot) if tot else "0"}</span></div>')
    return head + "".join(body)


def _method_ledger():
    rows = [("看了证据", 1), ("两张以上不同的", 2), ("理由和证据一致", 1), ("计划照做", 1)]
    out = []
    for t, n in rows:
        stars = "".join(icons.star(2.6, C["mustard"]) for _ in range(n))
        out.append(f'<div class="row" style="height:4.25mm;border-bottom:0.5pt dotted {C["ink_3"]};font-size:7.4pt">'
                   f'<span>{t}</span><span class="sp"></span><span class="row" style="gap:0.3mm">{stars}</span></div>')
    head = (f'<div class="row b7" style="font-size:7pt;color:{C["ink_2"]};height:3.6mm;border-bottom:0.5pt solid {C["ink"]}">'
            f'<span>每场最多 4 颗</span><span class="sp"></span><span>和赚赔无关</span></div>')
    return head + "".join(out)


def reveal_front(m: Model, sc: dict) -> Card:
    imgs = art.scene_images(sc["id"])
    rv = sc["reveal"]
    s = sc["season"]
    door = sc.get("door", "A")
    right = f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">REVEAL · 揭幕</span>'
    left = (f'<div class="row gap1"><span class="disp" style="font-size:14pt">揭幕</span>'
            f'<span class="chip" style="margin-left:1.5mm;background:{SEASON[s]["color"]};color:{C["paper_light"]};height:4.6mm;font-size:7.5pt">{esc(sc["season_cn"])} · 门 {esc(door)}</span></div>')
    parts = [_strip(s, left, right, bg=C["ink"])]
    parts.append(f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>')
    sr = rv.get("second_rows")
    art_top, art_h = 10.7, (32.0 if sr else 40.0)
    if imgs.get("reveal"):
        parts.append(_img(imgs["reveal"]["uri"], -3, art_top, W + 6, art_h, "50% 36%"))
    # 码：盖在插画右下角（同时盖住插画自带的空白标签框）
    qs = 17.0
    qw, qh = qrsvg.block_size(qs, 2.2, "扫码 · 动态揭幕")
    qx, qy = W - M - qw + 0.5, art_top + art_h - qh + 9.0
    y = art_top + art_h + 2.4
    tw = W - 2 * M - qw - 1.5
    parts.append(f'<div class="a disp fit" data-min="11" data-what="事件名" style="left:{M}mm;top:{y}mm;width:{tw}mm;height:7mm;font-size:15pt;white-space:nowrap">{esc(rv.get("headline", sc.get("title", "")))}</div>')
    parts.append(f'<div class="a b7" style="left:{M}mm;top:{y + 7.0}mm;width:{tw}mm;font-size:7.6pt;color:{C["ink_2"]};white-space:nowrap">{esc(rv.get("date_line", ""))}</div>')
    y += 11.4
    facts = rv.get("lines", [])
    budget = 112 if sr else 150
    use = []
    for f in facts[:3]:
        if sum(len(x) for x in use) + len(f) > budget and len(use) >= 2:
            break
        use.append(f)
    if len(use) < len(facts):
        content.NOTES.append(f"{sc['id']} 揭幕牌事实共 {len(facts)} 条，A6 放前 {len(use)} 条（其余在扫码动态揭幕里）")
    lis = "".join(f"<li>{esc(t)}</li>" for t in use)
    fh = 14.6 if sr else 17.2
    parts.append(f'<ul class="a dots fit lines" data-min="7" data-what="揭幕事实" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{fh}mm;font-size:7.4pt;line-height:1.3">{lis}</ul>')
    y += fh + 0.8
    chh = 19.5
    ch = charts.reveal_chart(rv.get("chart", {}), W - 2 * M, chh, rv.get("chart", {}).get("t_index"))
    parts.append(f'<div class="a" style="left:{M}mm;top:{y}mm;width:{W - 2 * M}mm;height:{chh}mm">{ch}</div>')
    y += chh + 1.0
    # 两本账：等宽、同样的标题样式
    lw = (W - 2 * M - 3.0) / 2
    parts.append(f'<div class="a" style="left:{M}mm;top:{y}mm;width:{lw}mm;">'
                 f'<div class="row" style="height:4.8mm"><span class="disp" style="font-size:10.5pt">收益账</span><span class="sp"></span>'
                 f'<span style="font-size:7pt;color:{C["ink_2"]}">资金 · 按份数</span></div>{_payoff_table(sc)}</div>')
    parts.append(f'<div class="a" style="left:{M + lw + 3.0}mm;top:{y}mm;width:{lw}mm;">'
                 f'<div class="row" style="height:4.8mm"><span class="disp" style="font-size:10.5pt">方法账</span><span class="sp"></span>'
                 f'<span style="font-size:7pt;color:{C["ink_2"]}">方法星</span></div>{_method_ledger()}</div>')
    y += 4.8 + 3.6 + 4 * 4.25 + 1.0
    # 熔断的第二次决定
    if sr:
        cells = "".join(f'<span style="margin-right:2.2mm"><b>{esc(r["label"].split("（")[0].replace("熔断后", ""))}</b> {esc(r.get("note", ""))}</span>' for r in sr)
        parts.append(f'<div class="a fit" data-min="7" data-what="第二次决定" style="left:{M}mm;right:{M}mm;top:{y}mm;height:7.2mm;font-size:7pt;line-height:1.3">'
                     f'<span class="chip ink" style="height:3.6mm;font-size:7pt;padding:0 1.4mm;margin-right:1.2mm;vertical-align:0.1mm">第二次决定</span>{cells}</div>')
        y += 7.6
    egg = rv.get("egg")
    lesson = rv.get("lesson")
    tail = egg or lesson or ""
    label = "彩蛋" if egg else "一句话"
    if tail:
        tail = tail.removeprefix("彩蛋：")
        parts.append(f'<div class="a fit" data-min="7" data-what="彩蛋" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{134.6 - y:.2f}mm;font-size:7.3pt;line-height:1.3">'
                     f'<span class="chip" style="background:{C["mustard"]};color:{C["ink"]};height:3.8mm;font-size:7pt;padding:0 1.6mm;margin-right:1mm;vertical-align:0.1mm">{label}</span>{esc(tail)}</div>')
    full = short_source(rv.get("source_note", ""), 999)
    src = short_source(rv.get("source_note", ""), 35)
    if src != full:
        content.NOTES.append(f"揭幕牌 {sc['id']} 的数据来源一行放不下，只印“{src}”；“{full[len(src):].strip('；')}”留在扫码页")
    parts.append(f'<div class="a dashline" style="left:{M}mm;right:{M}mm;top:135.0mm"></div>')
    parts.append(f'<div class="a srcline fit nowrap" data-min="7" data-what="数据来源" style="left:{M}mm;right:{M}mm;top:135.6mm;height:3.4mm">数据：{esc(src)}</div>')
    parts.append(f'<div class="a disc b7" style="left:{M}mm;top:139.3mm;height:3.6mm;color:{C["ink"]}">揭幕后再看 · 投资者教育游戏，不构成投资建议</div>')
    parts.append(qrsvg.block(sc["qr"]["reveal"], qx, qy, qs, 2.2, "扫码 · 动态揭幕", where=f"揭幕牌 {sc['id']}"))
    return Card(key=f"reveal-{sc['id']}", w=W, h=H, html=trim("".join(parts), W, H),
                qr=[sc["qr"]["reveal"]], label=f"揭幕牌 · {sc['season_cn']}{door} · 正面")


# ---------------------------------------------------------------- 物种牌

def lum(hexc):
    h = hexc.lstrip("#")
    r, g_, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g_ + 0.0722 * b


def on(hexc):
    """在这个底色上用什么字色。"""
    return C["ink"] if lum(hexc) > 0.5 else C["paper_light"]


def species_front(m: Model, sp: dict) -> Card:
    sid = sp["id"]
    col = SPECIES_COLOR.get(sid, C["ink"])
    fg = on(col)
    a = art.species_art(sid)
    parts = []
    split = 103.0
    if a:
        parts.append(_img(a["uri"], -3, -3, W + 6, split + 3, "50% 18%"))
    parts.append(f'<div class="a" style="left:-3mm;top:{split}mm;width:{W + 6}mm;height:{H - split + 3}mm;background:{col}"></div>')
    parts.append(f'<div class="a mstripe" style="left:-3mm;top:{split - 1.2}mm;width:{W + 6}mm;height:1.6mm"></div>')
    tag = "隐藏物种" if sp.get("hidden") else "物种"
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{split + 5}mm;color:{fg};align-items:flex-end">'
                 f'<span class="disp" style="font-size:36pt;line-height:.9">{esc(sp["name"])}</span>'
                 f'<span class="caps" style="font-size:8.5pt;letter-spacing:.3em;margin-left:3mm;margin-bottom:1.2mm">{esc(sp.get("en", SPECIES_EN[sid])).upper()}</span>'
                 f'<div class="sp"></div><span class="chip line" style="color:{fg};font-size:7.5pt;margin-bottom:1mm">{tag}</span></div>')
    parts.append(f'<div class="a b7" style="left:{M}mm;right:{M}mm;top:{split + 21}mm;font-size:12pt;color:{fg}">{esc(sp.get("tagline", ""))}</div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{split + 29.5}mm;font-size:7.5pt;color:{fg};opacity:.92">交易物种起源 · THE ORIGIN OF TRADING SPECIES</div>')
    return Card(key=f"species-{sid}", w=W, h=H, html=trim("".join(parts), W, H), label=f"物种牌 · {sp['name']} · 正面")


def species_back(m: Model, sp: dict) -> Card:
    sid = sp["id"]
    col = SPECIES_COLOR.get(sid, C["ink"])
    fg = on(col)
    md = art.medal(sid)
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:24mm;background:{col}"></div>',
             f'<div class="a mstripe" style="left:-3mm;top:21mm;width:{W + 6}mm;height:1.2mm"></div>']
    if md:
        parts.append(f'<div class="a" style="right:{M}mm;top:6mm;width:24mm;height:24mm;border-radius:50%;overflow:hidden;'
                     f'border:1.4mm solid {C["paper_light"]};background:{C["paper"]}"><img src="{md["uri"]}" style="width:100%;height:100%;display:block"></div>')
    parts.append(f'<div class="a row" style="left:{M}mm;top:5.6mm;color:{fg};align-items:flex-end">'
                 f'<span class="disp" style="font-size:22pt;line-height:.95">{esc(sp["name"])}</span>'
                 f'<span class="caps" style="font-size:7.5pt;letter-spacing:.24em;margin-left:2.4mm;margin-bottom:.8mm">{esc(sp.get("en", "")).upper()}</span></div>')
    parts.append(f'<div class="a b7" style="left:{M}mm;top:14.2mm;font-size:8.5pt;color:{fg}">{esc(sp.get("tagline", ""))}</div>')

    def sec(title, body):
        return (f'<div style="margin-bottom:2.1mm"><div class="disp" style="font-size:10pt;color:{C["ink"]};margin-bottom:0.6mm">{title}</div>{body}</div>')
    beh = "".join(f"<li>{esc(t)}</li>" for t in sp.get("looks_like", []))
    body = (sec("你是这样的", f'<div>{esc(sp.get("one_liner", ""))}</div>')
            + sec("游戏里常见的你", f'<ul class="dots">{beh}</ul>')
            + sec("长处", f'<div>{esc(sp.get("strength", ""))}</div>')
            + sec("盲点", f'<div>{esc(sp.get("blind_spot", ""))}</div>'))
    parts.append(f'<div class="a fit" data-min="7" data-what="物种说明" style="left:{M}mm;width:{W - 2 * M - 27}mm;top:25.6mm;height:83mm;font-size:7.7pt;line-height:1.36">{body}</div>')
    # 右栏：图标从哪来
    parts.append(f'<div class="a fit" data-min="7" data-what="图标来源" style="left:{W - M - 24.5}mm;width:24.5mm;top:36mm;height:40mm;font-size:7pt;line-height:1.3;color:{C["ink_2"]}">'
                 f'<div class="b7" style="color:{C["ink"]};margin-bottom:.6mm">图标从哪来</div>{esc(sp.get("icon_from", ""))}</div>')
    # 推荐方向 + 码
    qs = 17.0
    qw, qh = qrsvg.block_size(qs, 2.2, "扫码 · 物种详情")
    yb = 110.0
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{yb - 1.6}mm" ><div class="ruleline"></div></div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="推荐方向" style="left:{M}mm;width:{W - 2 * M - qw - 2.5}mm;top:{yb}mm;height:{142.8 - yb - 5.2:.1f}mm;font-size:7.5pt;line-height:1.34">'
                 f'<div class="disp" style="font-size:10pt;margin-bottom:.6mm">推荐方向</div>{esc(sp.get("recommend_direction", ""))}</div>')
    parts.append(f'<div class="a b7" style="left:{M}mm;top:138.4mm;font-size:7.5pt;color:{C["ink"]}">{esc(sp.get("in_game_only", "游戏里的表现，仅供参考"))} · {DISCLAIMER}</div>')
    parts.append(qrsvg.block(sp["qr"], W - M - qw + 0.5, 142.8 - qh, qs, 2.2, "扫码 · 物种详情", where=f"物种牌背面 {sid}"))
    return Card(key=f"species-{sid}-b", w=W, h=H, html=trim("".join(parts), W, H), qr=[sp["qr"]], label=f"物种牌 · {sp['name']} · 背面")


# ---------------------------------------------------------------- 序章

def prologue_front(m: Model) -> Card:
    p = m.D.get("prologue", {})
    pa = art.scene_art(art.first("style-v7/v7_prologue/**/*.png"), "prologue")
    parts = [_strip("summer", f'<span class="disp" style="font-size:14pt">序章</span>',
                    f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">PROLOGUE · 一人朗读</span>', bg=C["sky_deep"])]
    parts.append(f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>')
    if pa:
        parts.append(_img(pa["uri"], -3, 10.7, W + 6, 56, "50% 40%"))
    title = p.get("title", "序章")
    parts.append(f'<div class="a disp" style="left:{M}mm;right:{M}mm;top:70mm;font-size:20pt">{esc(title)}</div>')
    parts.append(f'<div class="a fit" data-min="7.5" data-what="序章朗读" style="left:{M}mm;right:{M}mm;top:80.5mm;height:55mm;font-size:9pt;line-height:1.55">{esc(p.get("read_aloud", ""))}</div>')
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">{esc(p.get("fact_note", ""))}</div>')
    return Card(key="prologue", w=W, h=H, html=trim("".join(parts), W, H), label="序章牌 · 正面")


def prologue_back(m: Model) -> Card:
    p = m.D.get("prologue", {})
    sr = m.D.get("self_and_real", {}).get("self_assessment", {})
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{C["paper"]}"></div>',
             _strip("summer", f'<span class="disp" style="font-size:14pt">序章 · 偷偷自评</span>', f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">SELF CHECK</span>', bg=C["sky_deep"]),
             f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>']
    parts.append(f'<div class="a fit" data-min="7.5" style="left:{M}mm;right:{M}mm;top:15mm;height:30mm;font-size:8.6pt;line-height:1.5">{esc(p.get("self_assessment", ""))}</div>')
    # 六个物种（海狸隐藏）
    cells = []
    for sid in sr.get("choices", ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon"]):
        md = art.medal(sid)
        img = f'<img src="{md["uri"]}" style="width:100%;height:100%;display:block">' if md else ""
        cells.append(f'<div class="col" style="align-items:center;gap:1mm"><div style="width:25mm;height:25mm;border-radius:50%;overflow:hidden;border:1mm solid {SPECIES_COLOR[sid]}">{img}</div>'
                     f'<div class="disp" style="font-size:11pt">{esc(m.sp.get(sid, {}).get("name", sid))}</div>'
                     f'<div style="font-size:7pt;color:{C["ink_2"]};white-space:nowrap">{esc(m.sp.get(sid, {}).get("tagline", ""))}</div></div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:48mm;display:grid;grid-template-columns:repeat(3,1fr);row-gap:3mm">{"".join(cells)}</div>')
    rc = " / ".join(x["text"] for x in sr.get("risk_choices", []))
    parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:121mm;font-size:8.6pt"><b>{esc(sr.get("risk_prompt", ""))}</b> {esc(rc)}</div>')
    parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:127mm;font-size:7.5pt;color:{C["ink_2"]}">{esc(sr.get("note", ""))}</div>')
    parts.append(f'<div class="a center disc" style="left:0;right:0;top:139.2mm">海狸是隐藏物种，不摊开 · {DISCLAIMER}</div>')
    return Card(key="prologue-b", w=W, h=H, html=trim("".join(parts), W, H), label="序章牌 · 背面")


# ---------------------------------------------------------------- 速查卡

def _numbered(lines, size=8.2, num_bg=None):
    num_bg = num_bg or C["ink"]
    out = []
    for i, t in enumerate(lines, 1):
        head, _, rest = t.partition("：")
        if rest:
            body = f'<b>{esc(head)}</b>　{esc(rest)}'
        else:
            body = esc(t)
        out.append(f'<div class="row" style="align-items:flex-start;gap:2.2mm;margin-bottom:2.6mm">'
                   f'<span class="kb sq" style="background:{num_bg};width:5.4mm;height:5.4mm;font-size:11pt">{i}</span>'
                   f'<div style="font-size:{size}pt;line-height:1.42;flex:1">{body}</div></div>')
    return "".join(out)


def quickref_front(m: Model, n=1) -> Card:
    q = m.D.get("quickref", {}).get("front", {})
    parts = [_strip("summer", f'<span class="disp" style="font-size:14pt">{esc(q.get("title", "速查卡"))}</span>',
                    f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">QUICK REFERENCE</span>', bg=C["ink"]),
             f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>']
    ic = art.tile_art("start")
    if ic:
        parts.append(f'<img class="art" src="{ic["uri"]}" style="right:{M}mm;top:13mm;width:24mm;height:24mm;border-radius:50%">')
    parts.append(f'<div class="a disp" style="left:{M}mm;top:16mm;font-size:19pt">一季怎么走</div>')
    parts.append(f'<div class="a" style="left:{M}mm;top:25mm;font-size:8pt;color:{C["ink_2"]}">四季 × 一个名场面 · 走完回到总起点破壳</div>')
    parts.append(f'<div class="a fit" data-min="7.2" data-what="速查正面" style="left:{M}mm;right:{M}mm;top:40mm;height:94mm">{_numbered(q.get("lines", []), 8.4)}</div>')
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">翻面：物种图标从哪来（第一场揭幕后再看） · {DISCLAIMER}</div>')
    return Card(key=f"quickref-{n}", w=W, h=H, html=trim("".join(parts), W, H), label="速查卡 · 正面")


def quickref_back(m: Model, n=1) -> Card:
    q = m.D.get("quickref", {}).get("back", {})
    parts = [_strip("summer", f'<span class="disp" style="font-size:14pt">{esc(q.get("title", "物种图标从哪来"))}</span>',
                    f'<span class="chip" style="background:{C["mustard"]};color:{C["ink"]};height:4.6mm;font-size:7pt">{esc(q.get("note", ""))}</span>', bg=C["ink"]),
             f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>']
    # 物种头像一排
    cells = []
    for sid in ["cheetah", "elephant", "meerkat", "fox", "owl", "chameleon"]:
        md = art.medal(sid)
        if md:
            cells.append(f'<div class="col" style="align-items:center"><div style="width:13mm;height:13mm;border-radius:50%;overflow:hidden;border:0.8mm solid {SPECIES_COLOR[sid]}"><img src="{md["uri"]}" style="width:100%;height:100%"></div>'
                         f'<span class="b7" style="font-size:7pt;margin-top:.5mm">{esc(m.sp.get(sid, {}).get("name", ""))}</span></div>')
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:14mm;justify-content:space-between">{"".join(cells)}</div>')
    lines = []
    for ln_ in q.get("lines", []):
        if "看牌背" in ln_ and "机会牌" in ln_:
            ln_ = ln_.replace("看牌背", "看牌底倒印的图标")
            if n == 1:
                content.NOTES.append("速查卡背面“机会牌 ×1：看牌背”改成“看牌底倒印的图标”：机会牌答案印在正面底部倒置区，牌背统一（规则书 §格子效果 也写着“翻牌背”，建议同步改）")
        lines.append(ln_)
    parts.append(f'<div class="a fit" data-min="7.2" data-what="速查背面" style="left:{M}mm;right:{M}mm;top:36mm;height:98mm">{_numbered(lines, 8.4, C["mustard"])}</div>')
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">物种只表示做决定的偏好，没有高低 · {DISCLAIMER}</div>')
    return Card(key=f"quickref-{n}-b", w=W, h=H, html=trim("".join(parts), W, H), label="速查卡 · 背面")


# ---------------------------------------------------------------- 名场面道具板（卖出窗口 / 抱团圈 / 出口板）

def _board_rules(rules, top, height, size=8.0):
    lis = "".join(f'<li style="margin-bottom:1.2mm">{esc(t)}</li>' for t in rules)
    return (f'<ul class="a dots fit" data-min="7" data-what="道具板规则" style="left:{M}mm;right:{M}mm;top:{top}mm;height:{height}mm;font-size:{size}pt;line-height:1.4">{lis}</ul>')


def _prop_head(sc, title, en):
    s = sc["season"]
    left = (f'<div class="row gap1"><span class="disp" style="font-size:14pt">{esc(title)}</span>'
            f'<span class="chip" style="margin-left:1.5mm;background:{C["paper_light"]};color:{C["ink"]};height:4.6mm;font-size:7pt">{esc(sc["season_cn"])} · 门 {esc(sc.get("door", "A"))} · 快进时用</span></div>')
    return [_strip(s, left, f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">{en}</span>'),
            f'<div class="a mstripe" style="left:-3mm;top:9.5mm;width:{W + 6}mm;height:1.2mm"></div>']


def prop_sell_window(m: Model) -> Card:
    sc = m.scene("s2015")
    ff = sc["fast_forward"]
    parts = _prop_head(sc, ff.get("mechanic_name", "卖出窗口与跌停锁"), "SELL WINDOW")
    # 售票窗口：拱形窗 + 栏杆，里面是名额格
    wx, wy, ww, wh = M, 15.0, W - 2 * M, 58.0
    parts.append(f'<div class="a" style="left:{wx}mm;top:{wy}mm;width:{ww}mm;height:{wh}mm;background:{C["sky_deep"]};border-radius:{ww / 2}mm {ww / 2}mm 2mm 2mm"></div>')
    parts.append(f'<div class="a center disp" style="left:{wx}mm;width:{ww}mm;top:{wy + 7}mm;font-size:17pt;color:{C["sun"]}">卖出窗口</div>')
    parts.append(f'<div class="a center" style="left:{wx}mm;width:{ww}mm;top:{wy + 15}mm;font-size:7.5pt;color:{C["paper_light"]}">名额 = 人数的一半（向下取整，至少 1 个）</div>')
    slots = []
    for i, cap in enumerate(["第 1 个", "第 2 个"]):
        slots.append(f'<div class="col" style="align-items:center;gap:1mm"><div style="width:22mm;height:22mm;border-radius:50%;background:{C["paper_light"]};border:1.2mm dashed {C["mustard"]}"></div>'
                     f'<span class="b7" style="font-size:8pt;color:{C["paper_light"]}">{cap}</span></div>')
    parts.append(f'<div class="a row" style="left:{wx}mm;width:{ww}mm;top:{wy + 22}mm;justify-content:center;gap:12mm">{"".join(slots)}</div>')
    parts.append(f'<div class="a center" style="left:{wx}mm;width:{ww}mm;top:{wy + wh - 6}mm;font-size:7pt;color:{C["paper_light"]}">2–3 人局只开第 1 个 · 4–5 人局开两个</div>')
    # 跌停锁
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{wy + wh + 3}mm;height:13mm;background:{C["paper_light"]};border-radius:1.5mm;padding:0 3mm;gap:3mm">'
                 f'<div style="width:9mm;height:9mm;border-radius:1.2mm;background:{C["ink"]};display:flex;align-items:center;justify-content:center">'
                 f'<svg width="6mm" height="6mm" viewBox="0 0 6 6"><rect x="0.8" y="2.6" width="4.4" height="3" rx="0.5" fill="{C["mustard"]}"/><path d="M1.8 2.6 V1.8 a1.2 1.2 0 0 1 2.4 0 V2.6" fill="none" stroke="{C["mustard"]}" stroke-width="0.6"/></svg></div>'
                 f'<div style="font-size:8pt;line-height:1.35"><b>跌停锁</b>　没卖掉的人拿一枚，下一段照样跟着跌</div></div>')
    parts.append(_board_rules(ff.get("board_rules", []), wy + wh + 19, 142.6 - (wy + wh + 19) - 5, 7.8))
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">{DISCLAIMER}</div>')
    return Card(key="prop-sellwindow", w=W, h=H, html=trim("".join(parts), W, H), label="卖出窗口（夏 · 2015）")


def prop_crowd_ring(m: Model) -> Card:
    sc = m.scene("smt")
    ff = sc["fast_forward"]
    parts = _prop_head(sc, ff.get("mechanic_name", "抱团圈"), "THE HUDDLE")
    cx, cy, R = W / 2, 48.0, 33.0
    rings = (f'<svg class="a" style="left:0;top:0" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
             f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{SEASON["autumn"]["color"]}"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{R - 4}" fill="none" stroke="{C["paper_light"]}" stroke-width="0.6" stroke-dasharray="1.6 1.2"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{R - 15}" fill="{C["paper_light"]}"/>'
             # 出口缺口
             f'<rect x="{cx - 7}" y="{cy + R - 7}" width="14" height="9" fill="{C["paper"]}"/>'
             f'</svg>')
    parts.append(rings)
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:{cy - 6}mm;font-size:15pt;color:{C["ink"]}">抱团圈</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:{cy + 2}mm;font-size:7.5pt;color:{C["ink_2"]}">还在场的人把棋子放进来</div>')
    parts.append(f'<div class="a center b7" style="left:0;right:0;top:{cy - R + 6}mm;font-size:8pt;color:{C["paper_light"]};letter-spacing:.2em">人人都抱着同一样东西</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:{cy + R - 5.4}mm;font-size:8pt;font-weight:700;color:{C["ink"]}">出口 ↓ 只有一个</div>')
    # 留下 / 离开
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{cy + R + 4}mm;gap:3mm">'
                 f'<div class="sp row" style="height:11mm;border-radius:1.5mm;background:{C["paper_light"]};justify-content:center;gap:2mm;font-size:9pt;font-weight:700">{icons.box(4)} 留下</div>'
                 f'<div class="sp row" style="height:11mm;border-radius:1.5mm;background:{C["ink"]};color:{C["paper_light"]};justify-content:center;gap:2mm;font-size:9pt;font-weight:700">{icons.box(4, C["paper_light"])} 离开</div></div>')
    parts.append(_board_rules(ff.get("board_rules", []), cy + R + 18, 142.6 - (cy + R + 18) - 5, 7.6))
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">挤出口的额外亏损是游戏化处理 · {DISCLAIMER}</div>')
    return Card(key="prop-crowdring", w=W, h=H, html=trim("".join(parts), W, H), label="抱团圈（秋 · 茅台）")


def prop_exit_board(m: Model) -> Card:
    sc = m.scene("squant")
    ff = sc["fast_forward"]
    parts = _prop_head(sc, ff.get("mechanic_name", "出口板"), "EXIT BOARD · P1")
    opts = {o["key"]: o for o in sc["opts"]}
    doors = []
    for k in ("C", "D"):
        o = opts.get(k, {"text": k})
        doors.append(f'<div class="col" style="align-items:center;gap:1.5mm;flex:1">'
                     f'<div style="width:40mm;height:52mm;background:{C["ink"]};border-radius:20mm 20mm 1.5mm 1.5mm;position:relative">'
                     f'<div class="disp center" style="position:absolute;left:0;right:0;top:9mm;font-size:22pt;color:{C["sun"]}">{k}</div>'
                     f'<div class="center b7" style="position:absolute;left:0;right:0;top:20mm;font-size:9pt;color:{C["paper_light"]}">{esc(o["text"])}</div>'
                     f'<div style="position:absolute;left:5mm;right:5mm;bottom:4mm;height:18mm;border:0.8mm dashed {C["mustard"]};border-radius:1.5mm"></div></div>'
                     f'<span style="font-size:7.5pt;color:{C["ink_2"]}">同一出口每多 1 人，每人多亏 1</span></div>')
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:16mm;gap:3mm">{"".join(doors)}</div>')
    parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:77mm;font-size:8pt"><b>选 A、B 的人</b>照常按快进牌结算，不上出口板</div>')
    parts.append(_board_rules(ff.get("board_rules", []), 85, 48, 8.0))
    parts.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">挤出口的额外亏损是游戏化处理 · {DISCLAIMER}</div>')
    return Card(key="prop-exitboard", w=W, h=H, html=trim("".join(parts), W, H), label="出口板（秋 B · 量化踩踏 · P1）")


def prop_back(name: str, en: str, key: str, season="autumn") -> Card:
    col = C["sky_deep"]
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{col}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;">{icons.sun_rays(W + 6, H + 6, (W + 6) / 2, (H + 6) / 2, 24, C["paper_light"], 0.08)}</div>',
             f'<div class="a center disp" style="left:0;right:0;top:60mm;font-size:24pt;color:{C["paper_light"]}">{esc(name)}</div>',
             f'<div class="a center caps" style="left:0;right:0;top:72mm;font-size:8pt;color:{C["sun"]};letter-spacing:.3em">{esc(en)}</div>',
             f'<div class="a center" style="left:0;right:0;top:80mm;font-size:8pt;color:{C["paper_light"]}">名场面道具 · 快进时翻到正面用</div>']
    return Card(key=key, w=W, h=H, html=trim("".join(parts), W, H), label=f"{name} · 背面")


# ---------------------------------------------------------------- 揭幕牌 · 共用背（深色、不透字）

def reveal_back(key="reveal-back") -> Card:
    # 幕布不用红：墨色褶皱 + 芥黄帷幔，不会被读成“涨”；整面深色，对光看不透正面
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{C["ink"]}"></div>']
    folds = []
    for i in range(10):
        x = -3 + i * (W + 6) / 10
        folds.append(f'<div class="a" style="left:{x}mm;top:-3mm;width:{(W + 6) / 10 + 0.05}mm;height:{H + 6}mm;'
                     f'background:linear-gradient(to right, #3B3826 0%, #55513A 45%, #2F2D1F 100%)"></div>')
    parts += folds
    # 顶部帷幔
    parts.append(f'<svg class="a" style="left:-3mm;top:-3mm" width="{W + 6}mm" height="34mm" viewBox="0 0 {W + 6} 34">'
                 + "".join(f'<path d="M{x} 0 H{x + (W + 6) / 6} V14 Q{x + (W + 6) / 12} 24 {x} 14 Z" fill="{C["mustard"]}"/>' for x in [i * (W + 6) / 6 for i in range(6)])
                 + f'<rect x="0" y="0" width="{W + 6}" height="6" fill="{C["ochre"]}"/></svg>')
    parts.append(f'<div class="a" style="left:{(W - 62) / 2}mm;top:52mm;width:62mm;height:62mm;border-radius:50%;background:{C["paper_light"]}"></div>')
    parts.append(f'<div class="a" style="left:{(W - 54) / 2}mm;top:56mm;width:54mm;height:54mm;border-radius:50%;background:{C["sun"]}"></div>')
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:66mm;font-size:46pt;color:{C["ink"]};line-height:1">揭幕</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:86mm;font-size:8pt;color:{C["ink"]};letter-spacing:.32em">THE REVEAL</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:94mm;font-size:7.5pt;font-weight:700;color:{C["ink"]}">快进结算完再翻开</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:126mm;font-size:8pt;color:{C["paper_light"]};letter-spacing:.12em">《交易物种起源》 · 名场面</div>')
    return Card(key=key, w=W, h=H, html=trim("".join(parts), W, H), label="揭幕牌 · 共用背")
