"""A3 印刷测试页（正反两面）：二维码三档、涨跌色块、最小字号、线宽、色板、灰阶、插画实际倍率、透印与正反套位。"""
from __future__ import annotations

from . import art, icons, qrsvg
from .core import Card, esc, trim
from .model import Model
from .tokens import C, PLAYERS, SEASON, SEASON_ORDER, SPECIES_CN, SPECIES_COLOR, SPECIES_ORDER

TW, TH = 414.0, 291.0  # 成品框 + 3 mm 出血 = 420×297，正好 A3，不用裁
SAMPLE = "投资者教育游戏，不构成投资建议 0123456789 ABC"
SHOW = (316.0, 214.0, 88.0, 58.0)  # 透印块（成品框坐标）
REG = [(TW / 2, 4.5), (TW / 2, TH - 4.5), (4.5, TH / 2), (TW - 4.5, TH / 2)]


def _gray(hexc: str) -> str:
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    y = round(0.299 * r + 0.587 * g + 0.114 * b)
    return f"#{y:02X}{y:02X}{y:02X}"


def _panel(no, x, y, w, h, title, note=""):
    return (f'<div class="a" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;border:0.5pt solid {C["ink_3"]};border-radius:1.6mm;background:{C["paper_light"]}"></div>'
            f'<div class="a row" style="left:{x + 3}mm;top:{y + 2.4}mm;width:{w - 6}mm;gap:1.6mm;align-items:baseline">'
            f'<span class="num" style="display:inline-flex;width:5mm;height:5mm;border-radius:50%;background:{C["ink"]};color:{C["sun"]};align-items:center;justify-content:center;font-size:8.6pt">{no}</span>'
            f'<b class="disp" style="font-size:11pt">{esc(title)}</b><span style="font-size:7pt;color:{C["ink_2"]}">{esc(note)}</span></div>')


def _reg(x, y, r=2.2):
    return (f'<svg class="a" style="left:{x - 4}mm;top:{y - 4}mm" width="8mm" height="8mm" viewBox="0 0 8 8"><g stroke="#000" stroke-width="0.18" fill="none">'
            f'<circle cx="4" cy="4" r="{r}"/><line x1="0" y1="4" x2="8" y2="4"/><line x1="4" y1="0" x2="4" y2="8"/></g></svg>')


def front(m: Model) -> Card:
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{TW + 6}mm;height:{TH + 6}mm;background:{C["paper"]}"></div>']
    p.append(f'<div class="a" style="left:9mm;top:7mm"><div class="disp" style="font-size:20pt;line-height:1">印刷测试页 · 正面</div>'
             f'<div style="font-size:8pt;margin-top:1.6mm;color:{C["ink_2"]}">《交易物种起源》v1.0 · 用正式纸张、正式色彩设置，双面（长边翻转）打印本页；逐项确认后再开印。'
             f'颜色以本页实物为准，屏幕只作参考。</div></div>')
    p.append(f'<div class="a" style="right:9mm;top:8mm;text-align:right;font-size:7.4pt;line-height:1.5;color:{C["ink_2"]}">纸：A3 · 成品 = 纸张，不用裁<br>四边中点有套位十字，正反面对着光应重合</div>')

    # 1 二维码三档
    x, y, w, h = 9, 27, 128, 98
    p.append(_panel(1, x, y, w, h, "二维码三档", "同一个开局码，黑码白底，四周留白 2.4 mm"))
    qx = x + 6
    for size, cap, cap2 in ((15.0, "15 mm", "仅对比"), (18.0, "18 mm", "最小可用"), (22.0, "22 mm", "推荐")):
        bw, bh = qrsvg.block_size(size, 2.4, cap, cap2)
        p.append(qrsvg.block("start", qx, y + 14 + (26.8 - size), size, 2.4, cap, cap2, where="A3 测试页"))
        qx += bw + 6
    p.append(f'<div class="a" style="left:{x + 4}mm;top:{y + 62}mm;width:{w - 8}mm;font-size:7.4pt;line-height:1.5">'
             f'15 mm 低于下限，只用来对比；正式件上的码是 20–22 mm（A6 卡背 17 mm 例外，见印刷说明）。<br><b>怎么验：</b>用三部不同手机（含一部旧机）在 30 cm 和 50 cm 各扫一次；18 mm 也要一次扫中，打开的是开局页。'
             f'扫不出来就整体放大到 22 mm，并检查印刷有没有糊点、发灰。<br><b>码的规则：</b>纠错 M，≥ 18 mm，离裁切 ≥ 5 mm，不放在深色底上，不覆亮膜反光。</div>')

    # 2 涨跌红绿
    x, y, w, h = 143, 27, 128, 98
    p.append(_panel(2, x, y, w, h, "涨跌红绿", "红 = 涨、绿 = 跌，永远配 ▲▼；不当装饰色"))
    for k, (key, up, lab) in enumerate((("up", True, "涨"), ("down", False, "跌"))):
        col = C[key]
        bx = x + 5 + k * 61
        p.append(f'<div class="a row" style="left:{bx}mm;top:{y + 12}mm;width:57mm;height:22mm;background:{col};border-radius:1.2mm;color:#fff;justify-content:center;gap:2mm">'
                 f'{icons.tri(up, 6.5, "#fff")}<span class="disp" style="font-size:20pt">{lab}</span><span style="font-size:8pt">{col}</span></div>')
        g = _gray(col)
        p.append(f'<div class="a row" style="left:{bx}mm;top:{y + 36}mm;width:57mm;height:10mm;background:{g};border-radius:1.2mm;color:#fff;justify-content:center;gap:1.6mm;font-size:7.4pt">'
                 f'{icons.tri(up, 3.4, "#fff")}黑白复印后约 {g}</div>')
        p.append(f'<div class="a row" style="left:{bx}mm;top:{y + 49}mm;gap:1mm;color:{col};font-size:7pt">{icons.tri(up, 2.4, col)}<b>{"+" if up else "−"}12.5%</b>'
                 f'<span style="margin-left:2mm;font-size:9pt" class="row">{icons.tri(up, 3, col)}<b>{"+" if up else "−"}3 份</b></span></div>')
    p.append(f'<div class="a" style="left:{x + 4}mm;top:{y + 58}mm;width:{w - 8}mm;font-size:7.4pt;line-height:1.5">'
             f'<b>怎么验：</b>红绿两块印出来要一眼分得开，不能发橙、发灰；再拿黑白复印件看：两块灰度几乎一样深，所以只靠 ▲▼ 区分，'
             f'这是故意的（照顾色弱）。7 pt 的红、绿小字要清楚、不虚边。<br><b>注意：</b>夏季色和“涨”的红是同一个色号，棋盘上大面积只用中性色。</div>')

    # 3 最小字号
    x, y, w, h = 277, 27, 128, 98
    p.append(_panel(3, x, y, w, h, "最小字号", "正文 ≥ 7 pt；图表标签 ≥ 6 pt"))
    rows = []
    for fam, label, extra in (("Noto Sans SC", "黑体", ""), ("Noto Sans SC", "黑体粗", "font-weight:700;"), ("Smiley Sans Oblique", "得意黑", "")):
        for pt in (6, 7, 8, 9):
            rows.append(f'<div class="row" style="gap:2mm;height:4.7mm;align-items:center"><span style="width:17mm;flex:none;white-space:nowrap;font-size:7pt;color:{C["ink_2"]}">{label} {pt} pt</span>'
                        f'<span style="font-family:\'{fam}\';{extra}font-size:{pt}pt;white-space:nowrap">{SAMPLE}</span></div>')
    p.append(f'<div class="a nocheck" style="left:{x + 4}mm;top:{y + 11}mm;width:{w - 8}mm;overflow:hidden">{"".join(rows)}</div>')
    rv = "".join(f'<div class="row" style="gap:2mm;height:5mm;align-items:center;padding:0 2mm;background:{bg};color:{fg}"><span style="width:15mm;flex:none;white-space:nowrap;font-size:7pt">反白 {pt} pt</span>'
                 f'<span style="font-size:{pt}pt;white-space:nowrap">{SAMPLE}</span></div>'
                 for bg, fg, pt in ((C["sky_deep"], C["paper_light"], 7), (C["ink"], C["sun"], 7), (C["sky_deep"], C["paper_light"], 6)))
    p.append(f'<div class="a nocheck" style="left:{x + 4}mm;top:{y + 70}mm;width:{w - 8}mm;overflow:hidden;border-radius:1mm">{rv}</div>')
    p.append(f'<div class="a" style="left:{x + 4}mm;top:{y + 87}mm;width:{w - 8}mm;font-size:7pt;line-height:1.4;color:{C["ink_2"]}">6 pt 只给图表刻度用；如果 7 pt 反白字糊了，改成更粗的字重或放大，不要缩。</div>')

    # 4 线宽
    x, y, w, h = 9, 131, 96, 77
    p.append(_panel(4, x, y, w, h, "线宽", "≥ 0.5 pt"))
    ls = []
    for i, pt in enumerate((0.25, 0.35, 0.5, 0.75, 1.0, 1.5)):
        mm = pt * 0.3528
        yy = 3 + i * 7.6
        ok = "不用" if pt < 0.5 else ("最细" if pt == 0.5 else "")
        ls.append(f'<line x1="22" y1="{yy}" x2="52" y2="{yy}" stroke="{C["ink"]}" stroke-width="{mm:.4f}"/>'
                  f'<line x1="55" y1="{yy}" x2="85" y2="{yy}" stroke="{C["ink"]}" stroke-width="{mm:.4f}" stroke-dasharray="1.2 0.9"/>'
                  f'<text x="0" y="{yy + 1}" font-size="2.47" fill="{C["ink_2"]}" font-family="Noto Sans SC">{pt:g} pt {ok}</text>')
    p.append(f'<svg class="a nocheck" style="left:{x + 4}mm;top:{y + 11}mm" width="88mm" height="44mm" viewBox="0 0 88 44">{"".join(ls)}</svg>')
    rev = "".join(f'<line x1="3" y1="{3 + i * 4}" x2="84" y2="{3 + i * 4}" stroke="{C["paper_light"]}" stroke-width="{pt * 0.3528:.4f}"/>' for i, pt in enumerate((0.35, 0.5, 0.75)))
    p.append(f'<svg class="a" style="left:{x + 4}mm;top:{y + 55}mm;border-radius:1mm;background:{C["sky_deep"]}" width="88mm" height="14mm" viewBox="0 0 88 14">{rev}'
             f'<text x="3" y="13" font-size="2.47" fill="{C["paper_light"]}" font-family="Noto Sans SC">反白线 0.35 / 0.5 / 0.75 pt：0.5 pt 也要连续不断</text></svg>')

    # 5 色板
    x, y, w, h = 111, 131, 160, 77
    p.append(_panel(5, x, y, w, h, "色板", "tokens.json；季节色只用在小标识上"))
    sw = []
    keys = [k for k in C]
    for i, k in enumerate(keys):
        r, c = divmod(i, 10)
        sx, sy = x + 4 + c * 15.2, y + 11 + r * 13.5
        fg = "#fff" if _gray(C[k]) < "#9A9A9A" else C["ink"]
        sw.append(f'<div class="a" style="left:{sx}mm;top:{sy}mm;width:14.2mm;height:12.4mm;background:{C[k]};border-radius:0.8mm;border:0.5pt solid rgba(0,0,0,.18);'
                  f'color:{fg};font-size:6pt;line-height:1.2;padding:0.8mm" >{esc(k)}<br>{C[k]}</div>')
    row3 = [(SEASON[s]["color"], SEASON[s]["cn"] + "季") for s in SEASON_ORDER] + [(pl["color"], pl["name"] + " " + pl["mark"]) for pl in PLAYERS]
    for i, (col, lab) in enumerate(row3):
        sx, sy = x + 4 + i * 15.2, y + 41
        fg = "#fff" if _gray(col) < "#9A9A9A" else C["ink"]
        sw.append(f'<div class="a" style="left:{sx}mm;top:{sy}mm;width:14.2mm;height:12.4mm;background:{col};border-radius:0.8mm;color:{fg};font-size:6pt;line-height:1.2;padding:0.8mm">{esc(lab)}<br>{col}</div>')
    for i, sid in enumerate(SPECIES_ORDER):
        col = SPECIES_COLOR[sid]
        sx, sy = x + 4 + i * 15.2, y + 56
        fg = "#fff" if _gray(col) < "#9A9A9A" else C["ink"]
        sw.append(f'<div class="a" style="left:{sx}mm;top:{sy}mm;width:14.2mm;height:12.4mm;background:{col};border-radius:50%;color:{fg};font-size:6pt;line-height:1.1;'
                  f'display:flex;align-items:center;justify-content:center;text-align:center">{SPECIES_CN[sid]}</div>')
    p.append(f'<div class="nocheck">{"".join(sw)}</div>')
    p.append(f'<div class="a" style="left:{x + 112}mm;top:{y + 57}mm;width:44mm;font-size:7pt;line-height:1.4;color:{C["ink_2"]}">第一排：tokens；第二排：季节 + 玩家（雾紫不在 tokens 里）；第三排：物种币色。</div>')

    # 6 灰阶
    x, y, w, h = 277, 131, 128, 36
    p.append(_panel(6, x, y, w, h, "灰阶", "10%–100%，检查暗部有没有并级"))
    gs = []
    for i in range(10):
        v = round(255 * (1 - (i + 1) / 10))
        gs.append(f'<div class="a" style="left:{x + 4 + i * 12}mm;top:{y + 11}mm;width:12mm;height:14mm;background:#{v:02X}{v:02X}{v:02X}"></div>'
                  f'<div class="a center nocheck" style="left:{x + 4 + i * 12}mm;top:{y + 26}mm;width:12mm;font-size:6pt;color:{C["ink_2"]}">{(i + 1) * 10}%</div>')
    p.append("".join(gs))

    # 7 插画实际倍率
    x, y, w, h = 277, 171, 128, 37
    p.append(_panel(7, x, y, w, h, "插画实际倍率", "看会不会发糊"))
    from . import c_board
    bsrc = c_board.first_board_src()
    bg = art.plain(bsrc, "board_bg", scale=2.0) if bsrc else None
    from .c_book import hero
    hk = hero()
    if bg:
        p.append(f'<div class="a" style="left:{x + 4}mm;top:{y + 10}mm;width:58mm;height:22mm;overflow:hidden;border-radius:1mm">'
                 f'<img src="{bg["uri"]}" style="position:absolute;left:-250mm;top:-14mm;width:600mm;height:600mm"></div>'
                 f'<div class="a" style="left:{x + 5}mm;top:{y + 28}mm;font-size:7pt;color:#fff;text-shadow:0 0 1mm #000" >主棋盘底图 · A2 实际倍率 ≈ 87 dpi</div>')
    if hk:
        ih = 183 * hk["h"] / hk["w"]
        p.append(f'<div class="a" style="left:{x + 66}mm;top:{y + 10}mm;width:58mm;height:22mm;overflow:hidden;border-radius:1mm">'
                 f'<img src="{hk["uri"]}" style="position:absolute;left:-70mm;top:{-0.78 * ih:.1f}mm;width:183mm;height:{ih:.1f}mm"></div>'
                 f'<div class="a" style="left:{x + 67}mm;top:{y + 28}mm;font-size:7pt;color:#fff;text-shadow:0 0 1mm #000">盒盖主视觉 · 实际倍率 ≈ 143 dpi</div>')

    # 8 圆角与安全线
    x, y, w, h = 9, 214, 150, 68
    p.append(_panel(8, x, y, w, h, "圆角 · 出血 · 安全线", "实际大小"))
    sv = []
    for k, (rad, lab) in enumerate(((3, "R3 标准卡 63×88、迷你卡 44×68"), (4, "R4 A6 卡 105×148"))):
        ox = 6 + k * 70
        sv.append(f'<rect x="{ox - 3}" y="11" width="42" height="40" fill="{C["sky_light"]}" opacity=".55"/>'
                  f'<path d="M{ox} 54 V{14 + rad} A{rad} {rad} 0 0 1 {ox + rad} 14 H{ox + 39}" fill="none" stroke="{C["ink"]}" stroke-width="0.25"/>'
                  f'<path d="M{ox + 5} 54 V{19} H{ox + 39}" fill="none" stroke="{C["kite_deep"]}" stroke-width="0.2" stroke-dasharray="1 0.7"/>'
                  f'<text x="{ox}" y="9" font-size="2.47" fill="{C["ink"]}" font-family="Noto Sans SC">{lab}</text>')
    sv.append(f'<text x="3" y="60" font-size="2.47" fill="{C["ink_2"]}" font-family="Noto Sans SC">浅蓝 = 3 mm 出血；黑线 = 裁切 + 圆角；虚线 = 5 mm 安全线（字和码不出线）。</text>')
    p.append(f'<svg class="a" style="left:{x + 4}mm;top:{y + 6}mm" width="142mm" height="62mm" viewBox="0 0 142 62">{"".join(sv)}</svg>')

    # 9 透印
    sx, sy, sw_, sh = SHOW
    p.append(_panel(9, 165, 214, 145, 68, "透印 · 正反套位", "翻到背面看"))
    p.append(f'<div class="a" style="left:{169}mm;top:{226}mm;width:{sx - 175}mm;font-size:7.4pt;line-height:1.5">'
             f'右边是一整块深色（墨色满版，和卡背、棋盘深色区一样）。打印双面后翻到背面：同一位置是浅底 7 pt 小字。'
             f'<br><b>合格：</b>背面小字清楚，看不到明显暗影。<br><b>不合格：</b>换更厚或更不透的纸（卡牌建议 300 g 以上的黑芯 / 蓝芯卡纸）。'
             f'<br><b>套位：</b>纸四边中点的十字，对着光看正反应重合，偏差 ≤ 0.5 mm。</div>')
    p.append(f'<div class="a" style="left:{sx}mm;top:{sy}mm;width:{sw_}mm;height:{sh}mm;background:{C["ink"]};border-radius:1mm"></div>'
             f'<div class="a center" style="left:{sx}mm;top:{sy + sh / 2 - 3}mm;width:{sw_}mm;font-size:8pt;color:{C["paper_light"]}">透印测试块 · 墨色满版</div>')
    p.extend(_reg(x, y) for x, y in REG)
    return Card(key="test-front", w=TW, h=TH, html=trim("".join(p), TW, TH), label="A3 测试页 正面")


def back(m: Model) -> Card:
    p = [f'<div class="a" style="left:-3mm;top:-3mm;width:{TW + 6}mm;height:{TH + 6}mm;background:{C["paper"]}"></div>']
    p.append(f'<div class="a" style="right:9mm;top:7mm;text-align:right"><div class="disp" style="font-size:20pt;line-height:1">印刷测试页 · 背面</div>'
             f'<div style="font-size:8pt;margin-top:1.6mm;color:{C["ink_2"]}">长边翻转双面打印；左边浅色块的背后就是正面的深色透印块</div></div>')
    sx, sy, sw, sh = SHOW
    bx = TW - sx - sw
    txt = ("名场面牌的背面、证据牌的文字、委托单的小字都印在浅底上。如果这段 7 pt 的字后面能看到一块灰影，说明纸太薄或者墨量太大，"
           "卡牌正反面会互相干扰，正式印刷前要换纸。") * 2
    p.append(f'<div class="a" style="left:{bx}mm;top:{sy}mm;width:{sw}mm;height:{sh}mm;background:{C["paper_light"]};border:0.5pt dashed {C["ink_3"]};border-radius:1mm"></div>'
             f'<div class="a" style="left:{bx + 4}mm;top:{sy + 4}mm;width:{sw - 8}mm;font-size:7pt;line-height:1.55;color:{C["ink"]}">'
             f'<b>透印检查（背后是正面的深色块）</b><br>{esc(txt)}</div>')
    p.append(f'<div class="a" style="left:{bx + sw + 8}mm;top:{sy + 4}mm;width:110mm;font-size:8pt;line-height:1.6">'
             f'<b>背面还要看：</b><br>1. 四边中点的十字和正面重合（对着光）。<br>2. 卡牌背面是左右镜像拼版，裁完正反不错位、不露白边。<br>'
             f'3. 背面不放细边框，因为裁切偏 1 mm 就会看出来。</div>')
    p.extend(_reg(TW - x, y) for x, y in REG)
    return Card(key="test-back", w=TW, h=TH, html=trim("".join(p), TW, TH), label="A3 测试页 背面")


def cards(m: Model) -> list[Card]:
    return [front(m), back(m)]
