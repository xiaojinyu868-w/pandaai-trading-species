"""迷你卡（徽章、负债）、驿站卡、玩家板 / AI 板、开户排队条、委托单、终局档案卡。"""

from __future__ import annotations

from . import art, content, icons, qrsvg
from .c_a6 import on
from .core import Card, esc, trim
from .model import Model, SEASON_EN, SEASON_EN2
from .tokens import AI_COLOR, C, PLAYERS, SEASON, SEASON_ORDER, SPECIES_COLOR, SPECIES_ORDER, SPECIES_SEAL

DISC = "投资者教育游戏，不构成投资建议"
SEASON_CN = {"spring": "春", "summer": "夏", "autumn": "秋", "winter": "冬"}
SEASON_NAME = {"spring": "入场", "summer": "狂热", "autumn": "松动", "winter": "危机"}


def cb(o=False):
    return f'<span class="cb{" o" if o else ""}"></span>'


def ln(w):
    return f'<span class="ln" style="width:{w}mm"></span>'


def it(text, o=False):
    return f'<span class="it">{cb(o)}{esc(text)}</span>'


def _band(w, color, left, right="", h=11.0, stripe=True):
    fg = on(color)
    out = (f'<div class="a" style="left:-3mm;top:-3mm;width:{w + 6}mm;height:{h + 3}mm;background:{color}"></div>'
           f'<div class="a row" style="left:4mm;right:4mm;top:0;height:{h}mm;color:{fg};gap:1.4mm">{left}<div class="sp"></div>{right}</div>')
    if stripe:
        out += f'<div class="a mstripe" style="left:-3mm;top:{h}mm;width:{w + 6}mm;height:0.9mm"></div>'
    return out


def _disc_img(uri, size, ring=None, bg=None):
    rb = f"border:{ring};" if ring else ""
    return (f'<span style="display:inline-block;flex:none;width:{size}mm;height:{size}mm;border-radius:50%;overflow:hidden;background:{bg or C["paper"]};{rb}">'
            f'<img src="{uri}" style="width:100%;height:100%;display:block"></span>')


# ======================================================================= 迷你卡：徽章

MW, MH = 44.0, 68.0
MM = 4.0
BADGE_ICON = {"badge-evidence": "magnifier", "badge-promise": "letter", "badge-history": "coin",
              "badge-data": "ledger", "badge-rule": "compass", "badge-risk": "kite"}


def _rosette(size, color, inner_uri):
    n, r0, r1 = 24, size / 2, size / 2 - 1.4
    import math
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n
        r = r0 if i % 2 == 0 else r1
        pts.append(f"{size / 2 + r * math.cos(a):.2f},{size / 2 + r * math.sin(a):.2f}")
    inner = size - 6.4
    return (f'<div style="position:relative;width:{size}mm;height:{size}mm">'
            f'<svg width="{size}mm" height="{size}mm" viewBox="0 0 {size} {size}" style="position:absolute;left:0;top:0">'
            f'<polygon points="{" ".join(pts)}" fill="{color}"/><circle cx="{size / 2}" cy="{size / 2}" r="{size / 2 - 2.4}" fill="none" stroke="{C["paper_light"]}" stroke-width="0.4"/></svg>'
            f'<div style="position:absolute;left:3.2mm;top:3.2mm;width:{inner}mm;height:{inner}mm;border-radius:50%;overflow:hidden;background:{C["paper"]}">'
            f'<img src="{inner_uri}" style="width:100%;height:100%"></div></div>')


def badge_front(m: Model, b: dict, n=1) -> Card:
    a = art.icon(BADGE_ICON.get(b["id"], "coin"))
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{MW + 6}mm;height:36mm;background:{C["sky_deep"]}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{MW + 6}mm;height:36mm">{icons.sun_rays(MW + 6, 36, (MW + 6) / 2, 19, 18, C["paper_light"], 0.1)}</div>',
             f'<div class="a mstripe" style="left:-3mm;top:33mm;width:{MW + 6}mm;height:0.9mm"></div>']
    if a:
        parts.append(f'<div class="a" style="left:{(MW - 25) / 2}mm;top:4mm">{_rosette(25, C["mustard"], a["uri"])}</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:29.2mm;font-size:7pt;letter-spacing:.3em;color:{C["paper_light"]}">BADGE · 徽章</div>')
    parts.append(f'<div class="a center disp fit" data-min="11" data-what="徽章名" style="left:{MM}mm;right:{MM}mm;top:36.4mm;height:7mm;font-size:16pt;white-space:nowrap">{esc(b["name"])}</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="徽章条件" style="left:{MM}mm;right:{MM}mm;top:44.6mm;height:15.4mm;font-size:7.4pt;line-height:1.36">'
                 f'<b>怎么拿：</b>{esc(b.get("condition", ""))}</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:61.2mm;font-size:7pt;color:{C["ink_3"]}">习惯，不是输赢</div>')
    return Card(key=f"{b['id']}-{n}", w=MW, h=MH, html=trim("".join(parts), MW, MH), label=f"徽章 · {b['name']}")


def badge_back(m: Model, b: dict, n=1) -> Card:
    parts = [_band(MW, C["mustard"], f'<span class="disp" style="font-size:12pt">{esc(b["name"])}</span>', "", h=9.5)]
    parts.append(f'<div class="a fit" data-min="7" data-what="徽章含义" style="left:{MM}mm;right:{MM}mm;top:12.8mm;height:25mm;font-size:8.2pt;line-height:1.42">{esc(b.get("meaning", ""))}</div>')
    parts.append(f'<div class="a" style="left:{MM}mm;right:{MM}mm;top:38.6mm;border-top:0.6pt dashed {C["ink_3"]}"></div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="徽章建议" style="left:{MM}mm;right:{MM}mm;top:40.4mm;height:20mm;font-size:7.8pt;line-height:1.4">'
                 f'<b>带进实盘：</b>{esc(b.get("tip", ""))}</div>')
    parts.append(f'<div class="a center" style="left:0;right:0;top:61.2mm;font-size:7pt;color:{C["ink_3"]}">《交易物种起源》</div>')
    return Card(key=f"{b['id']}-{n}-b", w=MW, h=MH, html=trim("".join(parts), MW, MH), label=f"徽章 · {b['name']} · 背面")


def debt_front(m: Model, n=1) -> Card:
    d = m.D.get("debt", {})
    parts = [_band(MW, C["ink"], f'<span class="disp" style="font-size:13pt">{esc(d.get("name", "负债牌"))}</span>',
                   f'<span class="chip" style="background:{C["mustard"]};color:{C["ink"]};height:4mm;font-size:7pt;padding:0 1.2mm">P1</span>', h=9.5)]
    parts.append(f'<div class="a fit" data-min="7" data-what="负债正文" style="left:{MM}mm;right:{MM}mm;top:12.4mm;height:22mm;font-size:7.4pt;line-height:1.38">{esc(d.get("card_text", ""))}</div>')
    parts.append(f'<div class="a row" style="left:{MM}mm;right:{MM}mm;top:35.4mm;height:9mm;border:0.6pt solid {C["ink"]};border-radius:1mm;padding:0 2mm;font-size:8pt">'
                 f'<b>欠款</b><span class="ln" style="flex:1;margin-left:1.6mm"></span><span style="margin-left:1mm">资金</span></div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="负债规则" style="left:{MM}mm;right:{MM}mm;top:46mm;height:7mm;font-size:7.2pt;line-height:1.3;font-weight:700">{esc(d.get("end_rule", ""))}</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="负债注" style="left:{MM}mm;right:{MM}mm;top:53.6mm;height:10mm;font-size:7pt;line-height:1.3;color:{C["ink_2"]}">{esc(d.get("flavor", ""))}</div>')
    return Card(key=f"debt-{n}", w=MW, h=MH, html=trim("".join(parts), MW, MH), label="负债牌 · P1")


def debt_back(n=1) -> Card:
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{MW + 6}mm;height:{MH + 6}mm;background:{C["ink"]}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{MW + 6}mm;height:{MH + 6}mm;opacity:.9">{icons.hazard(MW + 6, MH + 6, C["ink"], C["ink_2"], 4.0)}</div>',
             f'<div class="a" style="left:{MM}mm;right:{MM}mm;top:20mm;height:28mm;background:{C["ink"]};border:0.8mm solid {C["mustard"]};border-radius:1.4mm"></div>',
             f'<div class="a center disp" style="left:0;right:0;top:25.6mm;font-size:17pt;color:{C["sun"]}">负债牌</div>',
             f'<div class="a center caps" style="left:0;right:0;top:34.4mm;font-size:7pt;letter-spacing:.24em;color:{C["paper_light"]}">DEBT</div>',
             f'<div class="a center" style="left:0;right:0;top:39.6mm;font-size:7pt;color:{C["paper_light"]}">资金跌破 0 才拿</div>']
    return Card(key=f"debt-{n}-b", w=MW, h=MH, html=trim("".join(parts), MW, MH), label="负债牌 · 背面")


# ======================================================================= 驿站卡（A6）

A6W, A6H = 105.0, 148.0


def _seal_or_none(sid, size=5.2):
    if not sid:
        return f'<span style="font-size:7pt;color:{C["ink_3"]}">不给</span>'
    return icons.seal(sid, size, ring=False)


def _inline_seal(sid, size=4.6):
    return f'<span style="display:inline-block;vertical-align:-1.3mm">{icons.seal(sid, size, ring=False)}</span>'


def _icon_table(m: Model, top: float) -> str:
    ir = m.D.get("meta", {}).get("icon_rules", {}) or {}
    RC = {"price": "量价", "data": "数据", "news": "消息", "follow": "跟别人", "rule": "规则牌", "gut": "直觉", "lost": "看不懂", "tip": "锦囊"}
    M = 5.5

    def cells(mp, order):
        groups = {}
        for k in order:
            if k in mp:
                groups.setdefault(mp[k], []).append(RC.get(k, k))
        out = []
        for sid, names in groups.items():
            out.append(f'<span class="row" style="gap:0.8mm;white-space:nowrap">{"、".join(names)}{_seal_or_none(sid)}</span>')
        return "".join(out)

    rows = []
    rows.append(("理由 ×{}".format(ir.get("reason_weight", 2)), cells(ir.get("reason_icons", {}), ["price", "data", "news", "follow", "rule", "gut", "lost"])))
    wo = ir.get("wait_override", {})
    if wo:
        rows.append(("观望改判", f'<span style="line-height:1.5">选了 0 份、理由又不是直觉或看不懂：理由的 2 个图标改成 {_inline_seal(wo.get("to"))}　用规则牌仍是 {_inline_seal("fox")}</span>'))
    rows.append(("第一张证据 ×{}".format(ir.get("first_evidence_weight", 1)), cells(ir.get("first_evidence_icons", {}), ["price", "data", "news", "tip"])))
    rows.append(("机会牌 ×{}".format(ir.get("chance_weight", 1)), '看牌底倒印的那个图标'))
    trs = "".join(f'<div class="row" style="gap:2mm;min-height:6.6mm;border-top:0.5pt solid {C["ink_3"]};padding:0.6mm 0">'
                  f'<b style="width:19mm;flex:none">{esc(h)}</b><div class="row" style="flex:1;flex-wrap:wrap;column-gap:2.6mm;row-gap:0.6mm">{c}</div></div>'
                  for h, c in rows)
    return (f'<div class="a" style="left:{M}mm;right:{M}mm;top:{top}mm;height:{140 - top - 2}mm;background:{C["paper_light"]};border-radius:1.6mm;padding:1.6mm 2.4mm;font-size:7.6pt;line-height:1.3">'
            f'<div class="row" style="margin-bottom:1mm"><span class="disp" style="font-size:11pt">图标怎么数</span><span class="sp"></span>'
            f'<span style="font-size:7pt;color:{C["ink_2"]}">最多的那种拿一枚</span></div>{trs}</div>')


def _retest_hint(m: Model, top: float) -> str:
    M = 5.5
    col = C["sage"]
    mini = (f'<div style="position:relative;width:17mm;height:23.6mm;flex:none;border-radius:1.2mm;background:{col};overflow:hidden">'
            f'<div style="position:absolute;left:0;top:0;width:17mm;height:23.6mm">{icons.sun_rays(17, 23.6, 8.5, 11, 14, C["paper_light"], 0.14)}</div>'
            f'<div class="center disp" style="position:absolute;left:0;right:0;top:3mm;font-size:8pt;color:{C["paper_light"]}">补测</div>'
            f'<div class="row" style="position:absolute;left:0;right:0;top:9.6mm;justify-content:center;gap:0.8mm">{icons.seal("cheetah", 6.4)}{icons.seal("elephant", 6.4)}</div>'
            f'<div class="center" style="position:absolute;left:0;right:0;top:17mm;font-size:7pt;color:{C["paper_light"]}">豹 / 象</div></div>')
    return (f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{top}mm;gap:3.4mm;background:{C["paper_light"]};border-radius:1.6mm;padding:2.4mm 3mm;font-size:8pt;line-height:1.45">'
            f'{mini}<div><div class="disp" style="font-size:11pt;margin-bottom:1mm">平局时找哪张补测牌</div>'
            f'比如猎豹和大象各 3 个图标：翻找牌背印着“豹 / 象”的那张，读题作答，按答案拿币。</div></div>')


def _coin_faces(m: Model, top: float) -> str:
    M = 5.5
    ir = m.D.get("meta", {}).get("icon_rules", {}) or {}
    col = SPECIES_COLOR["fox"]
    solid = (f'<svg width="15mm" height="15mm" viewBox="0 0 15 15"><circle cx="7.5" cy="7.5" r="7.3" fill="{col}"/>'
             f'<circle cx="7.5" cy="7.5" r="6.2" fill="none" stroke="{C["paper_light"]}" stroke-width="0.3"/>'
             f'<text x="7.5" y="10.4" font-size="8.4" text-anchor="middle" fill="{C["paper_light"]}" font-family="Smiley Sans Oblique">狐</text></svg>')
    hollow = (f'<svg width="15mm" height="15mm" viewBox="0 0 15 15"><circle cx="7.5" cy="7.5" r="7.3" fill="{C["paper_light"]}"/>'
              f'<circle cx="7.5" cy="7.5" r="6.6" fill="none" stroke="{col}" stroke-width="1.2"/>'
              f'<text x="7.5" y="10.4" font-size="8.4" text-anchor="middle" fill="{col}" font-family="Smiley Sans Oblique">狐</text></svg>')
    beaver = ir.get("beaver", "")
    return (f'<div class="a" style="left:{M}mm;right:{M}mm;top:{top}mm;background:{C["paper_light"]};border-radius:1.6mm;padding:2.4mm 3mm;font-size:8pt;line-height:1.45">'
            f'<div class="disp" style="font-size:11pt;margin-bottom:1.6mm">物种币的两面</div>'
            f'<div class="row" style="gap:3mm;margin-bottom:2mm">'
            f'<div class="row" style="gap:2mm;flex:1">{solid}<div><b>实心面 = 1 枚</b><br>平常就放这一面</div></div>'
            f'<div class="row" style="gap:2mm;flex:1">{hollow}<div><b>空心面 = 半枚</b><br>这季申报了“认出来了”</div></div></div>'
            f'<div style="border-top:0.5pt solid {C["ink_3"]};padding-top:1.4mm"><b>海狸币</b>：{esc(beaver)}</div></div>')


def station_card(m: Model) -> tuple[Card, Card]:
    st = m.D.get("station", {}).get("card", {})
    M = 5.5
    a = art.tile_art("station")

    def head(title, en):
        out = _band(A6W, C["ochre"], f'<span class="disp" style="font-size:15pt">{esc(title)}</span>',
                    f'<span class="caps" style="font-size:7pt;letter-spacing:.2em">{en}</span>', h=11.5)
        return out

    def numbered(lines, top, h, size=8.6):
        rows = []
        for i, t in enumerate(lines, 1):
            t = t.lstrip("0123456789 ")
            head_, _, rest = t.partition("：")
            body = f"<b>{esc(head_)}：</b>{esc(rest)}" if rest else esc(t)
            rows.append(f'<div class="row" style="align-items:flex-start;gap:2.2mm;margin-bottom:2.4mm"><span class="kb sq" style="background:{C["ochre"]};width:5.4mm;height:5.4mm;font-size:11pt">{i}</span>'
                        f'<div style="flex:1;line-height:1.45">{body}</div></div>')
        return f'<div class="a fit" data-min="7.4" data-what="驿站卡" style="left:{M}mm;right:{M}mm;top:{top}mm;height:{h}mm;font-size:{size}pt">{"".join(rows)}</div>'

    f = [head(st.get("front_title", "驿站 · 季度小结"), "STATION")]
    if a:
        f.append(f'<div class="a" style="left:{M}mm;top:15.6mm;width:27mm;height:27mm;border-radius:50%;overflow:hidden;box-shadow:0 0 0 1mm {C["paper_light"]}"><img src="{a["uri"]}" style="width:100%;height:100%"></div>')
    f.append(f'<div class="a" style="left:{M + 31}mm;right:{M}mm;top:18.4mm;font-size:8.2pt;line-height:1.45;color:{C["ink_2"]}">'
             f'<div class="disp" style="font-size:12pt;color:{C["ink"]};margin-bottom:1mm">每季走到下一个角</div>拿出这一季的委托单，看复盘面的图标栏，四步做完再进下一季。</div>')
    f.append(numbered(st.get("front", []), 46, 44, 8.4))
    f.append(_icon_table(m, 91.6))
    f.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">翻面：平局与“我不同意” · {DISC}</div>')
    front = Card(key="station", w=A6W, h=A6H, html=trim("".join(f), A6W, A6H), label="驿站卡 · 正面")

    b = [head(st.get("back_title", "平局与“我不同意”"), "TIE · DISAGREE")]
    seals = "".join(icons.seal(s, 10) for s in ["cheetah", "elephant", "meerkat", "fox", "owl", "chameleon"])
    b.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:17mm;justify-content:space-between">{seals}</div>')
    b.append(numbered(st.get("back", []), 31, 44, 9.4))
    b.append(_retest_hint(m, 66.5))
    b.append(_coin_faces(m, 98))
    b.append(f'<div class="a disc" style="left:{M}mm;top:139.2mm">补测牌按牌背上的物种对找 · {DISC}</div>')
    back = Card(key="station-b", w=A6W, h=A6H, html=trim("".join(b), A6W, A6H), label="驿站卡 · 背面")
    return front, back


# ======================================================================= 玩家板 / AI 板（A5 横放 210×148）

BW, BH = 210.0, 148.0


def _track(x, y, n0, n1, cw, ch, start=None, star=False, mark5=True, label_left=None):
    cells = []
    for i, v in enumerate(range(n0, n1 + 1)):
        cx = x + i * cw
        bg = C["paper_light"]
        fg = C["ink"]
        if mark5 and v % 5 == 0 and v:
            bg = C["sun"]
        if start is not None and v == start:
            bg = C["mustard"]
        if v == 0 and not star:
            bg, fg = C["ink"], C["paper_light"]
        inner = f'<span class="num" style="font-size:{9.5 if not star else 8.5}pt;line-height:1">{v}</span>'
        if star:
            inner = f'<div class="col" style="align-items:center;gap:0.2mm">{icons.star(2.6, C["ink"] if v else C["ink_3"], hollow=not v)}{inner}</div>'
        cells.append(f'<div class="a row" style="left:{cx:.2f}mm;top:{y}mm;width:{cw - 0.5:.2f}mm;height:{ch}mm;background:{bg};color:{fg};border-radius:0.8mm;justify-content:center">{inner}</div>')
    return "".join(cells)


def _coin_slot(cx, cy, d, color, label, sub=""):
    return (f'<div class="a" style="left:{cx - d / 2:.2f}mm;top:{cy - d / 2:.2f}mm;width:{d}mm;height:{d}mm;border-radius:50%;'
            f'background:{C["paper_light"]};box-shadow:inset 0 0 0 1.1mm {color}"></div>'
            f'<div class="a center disp" style="left:{cx - d / 2:.2f}mm;width:{d}mm;top:{cy - 3.2:.2f}mm;font-size:16pt;color:{color};opacity:.35">{esc(label)}</div>'
            + (f'<div class="a center b7" style="left:{cx - 12:.2f}mm;width:24mm;top:{cy + d / 2 + 0.8:.2f}mm;font-size:7.4pt">{esc(sub)}</div>' if sub else ""))


def player_board(m: Model, p: dict, idx: int) -> Card:
    col = p["color"]
    fg = on(col)
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{BW + 6}mm;height:{BH + 6}mm;background:{C["paper"]}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{BW + 6}mm;height:19mm;background:{col}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{BW + 6}mm;height:19mm;overflow:hidden">{icons.sun_rays(BW + 6, 19, 15.5, 10.5, 40, C["paper_light"], 0.13)}</div>',
             f'<div class="a mstripe" style="left:-3mm;top:16mm;width:{BW + 6}mm;height:1.2mm"></div>',
             f'<div class="a row" style="left:5.6mm;top:1.2mm;width:13.4mm;height:13.4mm;border-radius:50%;background:{C["paper_light"]};box-shadow:inset 0 0 0 0.5mm {C["ink"]};justify-content:center">'
             f'{icons.shape(p["shape"], 8.4, col, C["ink"])}</div>',
             f'<div class="a" style="left:21.5mm;top:2.4mm;color:{fg}"><span class="disp" style="font-size:21pt">玩家板</span>'
             f'<span class="caps" style="font-size:7pt;letter-spacing:.24em;margin-left:2.4mm">PLAYER BOARD</span></div>',
             f'<div class="a b7" style="left:22mm;top:10.6mm;font-size:7.5pt;color:{fg}">{esc(p["name"])} · 开局：资金放 20、方法星放 0、拿 1 研究点</div>',
             f'<div class="a row" style="right:6mm;top:3.4mm;height:9mm;gap:2mm;color:{fg}">'
             f'<span class="disp" style="font-size:12pt">交易物种起源</span>{icons.shape(p["shape"], 6, C["paper_light"], C["ink"])}</div>']
    # 委托单区
    parts.append(f'<div class="a" style="left:6mm;top:21mm;width:106mm;height:75mm;border:0.7mm dashed {C["ink_3"]};border-radius:3mm;background:{C["paper_light"]}"></div>')
    parts.append(f'<div class="a center disp" style="left:6mm;width:106mm;top:43mm;font-size:30pt;color:{C["paper_deep"]}">委托单</div>')
    parts.append(f'<div class="a center b7" style="left:6mm;width:106mm;top:57mm;font-size:8.4pt;color:{C["ink_2"]}">填完对折，扣在这里 · 全桌“三、二、一”一起翻开</div>')
    parts.append(f'<div class="a center" style="left:6mm;width:106mm;top:62.6mm;font-size:7.4pt;color:{C["ink_3"]}">规则牌也放这里：每场最多用一张</div>')
    # 四季物种币
    parts.append(f'<div class="a b7" style="left:117mm;top:20.4mm;font-size:8pt">四季物种币</div>')
    parts.append(f'<div class="a" style="left:139mm;top:20.8mm;font-size:7pt;color:{C["ink_2"]}">认出来的那季：空心面，算半枚</div>')
    for i, s in enumerate(SEASON_ORDER):
        cx = 130 + (i % 2) * 29
        cy = 38 + (i // 2) * 30
        parts.append(_coin_slot(cx, cy, 24, SEASON[s]["color"], SEASON_CN[s], f"{SEASON_CN[s]} · {SEASON_NAME[s]}"))
    # 工具箱
    parts.append(f'<div class="a" style="left:177mm;top:25mm;width:27mm;height:71mm;border:0.5pt solid {C["ink"]};border-radius:2mm"></div>')
    parts.append(f'<div class="a center b7" style="left:177mm;width:27mm;top:26.6mm;font-size:8pt">工具箱</div>')
    for k in range(2):
        parts.append(f'<div class="a" style="left:{179.5}mm;top:{32.5 + k * 25}mm;width:22mm;height:22mm;border-radius:50%;border:0.5mm dashed {SPECIES_COLOR["beaver"]}"></div>')
    md = art.medal("beaver")
    if md:
        parts.append(f'<div class="a" style="left:184.5mm;top:37.5mm;width:12mm;height:12mm;border-radius:50%;overflow:hidden;opacity:.5"><img src="{md["uri"]}" style="width:100%;height:100%"></div>')
    parts.append(f'<div class="a center" style="left:177mm;width:27mm;top:82mm;font-size:7pt;line-height:1.25;color:{C["ink_2"]}">海狸币不占季节格<br>2 枚：翻开海狸牌</div>')
    # 资金轨
    parts.append(f'<div class="a row" style="left:6mm;top:99.4mm;gap:2mm;font-size:8pt"><b>资金</b><span style="color:{C["ink_2"]};font-size:7pt">每份仓位涨跌按快进牌、揭幕牌结算 · 跌破 0 拿负债牌（P1），标记停在 0</span></div>')
    cw = 198 / 21
    parts.append(_track(6, 104.4, 0, 20, cw, 8.6, start=20))
    parts.append(_track(6, 113.6, 21, 40, cw, 8.6))
    parts.append(f'<div class="a row" style="left:{6 + 20 * cw:.2f}mm;top:113.6mm;width:{cw - 0.5:.2f}mm;height:8.6mm;justify-content:center;font-size:7pt;color:{C["ink_2"]}">40+</div>')
    parts.append(f'<div class="a center b7" style="left:{6 + 20 * cw:.2f}mm;width:{cw}mm;top:101.2mm;font-size:7pt">起点</div>')
    # 方法星轨
    parts.append(f'<div class="a row" style="left:6mm;top:124.8mm;gap:2mm;font-size:8pt"><b>方法星</b><span style="color:{C["ink_2"]};font-size:7pt">每场最多 4 颗，和赚没赚钱无关</span></div>')
    parts.append(_track(6, 129.6, 0, 16, 8.8, 9.4, star=True))
    # 研究点 + 认出令牌
    parts.append(f'<div class="a" style="left:158mm;top:124mm;width:46mm;height:19.4mm;border:0.5pt solid {C["ink"]};border-radius:2mm"></div>')
    parts.append(f'<div class="a b7" style="left:160.4mm;top:125.4mm;font-size:7.4pt">研究点</div>')
    parts.append(f'<div class="a" style="left:160.4mm;top:129.6mm;width:20mm;font-size:7pt;line-height:1.3;color:{C["ink_2"]}">放这里<br>1 点看 1 张证据</div>')
    parts.append(f'<div class="a" style="left:183mm;top:125.2mm;width:17mm;height:17mm;border-radius:50%;border:0.5mm dashed {C["ink"]};background:{C["paper_light"]}"></div>')
    parts.append(f'<div class="a center" style="left:183mm;width:17mm;top:129.2mm;font-size:7pt;line-height:1.2;font-weight:700">认出<br>令牌</div>')
    return Card(key=f"player-{idx + 1}", w=BW, h=BH, html=trim("".join(parts), BW, BH), label=f"玩家板 · {p['name']}")


def solo_rules() -> list[str]:
    """规则书“单人”一节的编号条目（保留加粗）。"""
    import re
    txt = content.load_text("rules-v1.md")
    sec = txt.split("## 单人", 1)[1].split("\n## ", 1)[0] if "## 单人" in txt else ""
    out = []
    for line in sec.splitlines():
        mm = re.match(r"^\d+\.\s+(.*)", line.strip())
        if mm:
            t = esc(mm.group(1))
            t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
            out.append(t)
    if not out:
        content.NOTES.append("规则书里没找到“单人”一节，AI 板的单人规则留空")
    return out


def ai_board(m: Model) -> Card:
    col = AI_COLOR
    fg = on(col)
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{BW + 6}mm;height:{BH + 6}mm;background:{C["paper"]}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{BW + 6}mm;height:19mm;background:{col}"></div>',
             f'<div class="a mstripe" style="left:-3mm;top:16mm;width:{BW + 6}mm;height:1.2mm"></div>']
    a = art.icon("waterwheel")
    if a:
        parts.append(f'<div class="a" style="left:6mm;top:2mm">{_disc_img(a["uri"], 12, "0.6mm solid " + C["paper_light"])}</div>')
    parts.append(f'<div class="a" style="left:21.5mm;top:2.4mm;color:{fg}"><span class="disp" style="font-size:21pt">AI 板</span>'
                 f'<span class="caps" style="font-size:7pt;letter-spacing:.24em;margin-left:2.4mm">SOLO · 你和两只 AI</span></div>')
    parts.append(f'<div class="a b7" style="left:22mm;top:10.6mm;font-size:7.5pt;color:{fg}">两张 AI 物种牌背面朝下放在这里，亮单时只看这一场那一行</div>')
    for k, nm in enumerate(["AI ①", "AI ②"]):
        x = 6 + k * 67
        parts.append(f'<div class="a" style="left:{x}mm;top:21mm;width:64mm;height:89mm;border:0.7mm dashed {C["ink_3"]};border-radius:3mm;background:{C["paper_light"]}"></div>')
        parts.append(f'<div class="a center disp" style="left:{x}mm;width:64mm;top:56mm;font-size:22pt;color:{C["paper_deep"]}">{nm}</div>')
        parts.append(f'<div class="a center" style="left:{x}mm;width:64mm;top:66mm;font-size:7.4pt;color:{C["ink_3"]}">AI 物种牌 · 背面朝上</div>')
    solo = solo_rules()
    lis = "".join(f"<li style='margin-bottom:1.4mm'>{t}</li>" for t in solo)
    parts.append(f'<div class="a b7" style="left:142mm;top:21mm;font-size:8.4pt">单人规则</div>')
    parts.append(f'<ul class="a dots fit" data-min="7" data-what="单人规则" style="left:142mm;right:6mm;top:26.4mm;height:83mm;font-size:7.6pt;line-height:1.38">{lis}</ul>')
    cw = 198 / 21
    parts.append(f'<div class="a row" style="left:6mm;top:111.6mm;gap:2mm;font-size:7.6pt"><b>资金</b><span style="color:{C["ink_2"]};font-size:7pt">两只 AI 共用一条轨，用两种标记</span></div>')
    parts.append(_track(6, 116.2, 0, 20, cw, 7.8, start=20))
    parts.append(_track(6, 124.6, 21, 40, cw, 7.8))
    parts.append(f'<div class="a col" style="left:6mm;top:133.6mm;width:26mm;font-size:7.6pt;line-height:1.2"><b>方法星</b><span style="color:{C["ink_2"]};font-size:7pt">照 AI 牌背面那一行</span></div>')
    parts.append(_track(33, 133.4, 0, 16, 10.0, 8.0, star=True))
    return Card(key="ai-board", w=BW, h=BH, html=trim("".join(parts), BW, BH), label="AI 板")


# ======================================================================= 开户排队条 210×60

QW, QH = 210.0, 60.0


def queue_strip(m: Model) -> Card:
    col = C["sky_deep"]
    img = art.scene_images("s924").get("blind")
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{QW + 6}mm;height:{QH + 6}mm;background:{C["paper"]}"></div>']
    if img:
        parts.append(f'<div class="a" style="left:-3mm;top:-3mm;width:47mm;height:{QH + 6}mm;overflow:hidden">'
                     f'<img src="{img["uri"]}" style="position:absolute;left:-7mm;top:-5mm;width:60mm;height:80.3mm"></div>')
    parts.append(f'<div class="a mstripe" style="left:44mm;top:-3mm;width:1.2mm;height:{QH + 6}mm"></div>')
    parts.append(f'<div class="a" style="left:45.2mm;top:-3mm;width:56mm;height:{QH + 6}mm;background:{col}"></div>')
    parts.append(f'<div class="a" style="left:45.2mm;top:-3mm;width:56mm;height:{QH + 6}mm;overflow:hidden">{icons.sun_rays(56, QH + 6, 0, QH + 6, 18, C["paper_light"], 0.08)}</div>')
    parts.append(f'<div class="a" style="left:49.5mm;top:5mm;color:{C["paper_light"]}"><div class="disp" style="font-size:19pt">开户排队条</div>'
                 f'<div class="caps" style="font-size:7pt;letter-spacing:.2em;margin-top:1.4mm">QUEUE · 春 A 招牌机制</div></div>')
    parts.append(f'<div class="a" style="left:49.5mm;top:21.5mm;width:48mm;font-size:7.4pt;line-height:1.42;color:{C["paper_light"]}">'
                 f'依次明选：从起始玩家开始，轮到你时大声说出选项。<b>选 A、B 的人</b>把棋子放进队里，后面的人看得见队有多长。</div>')
    parts.append(f'<div class="a" style="left:49.5mm;top:44.6mm;width:48mm;font-size:7.2pt;line-height:1.35;color:{C["sun"]}">'
                 f'理由和计划照样扣着写。委托单上记下：你选的时候队里已经有几个人。</div>')
    # 排队位：第 1 位挨着柜台
    n, d, step = 5, 15.6, 17.4
    right = 189.6
    for i in range(n):
        cx = right - d / 2 - i * step
        parts.append(f'<div class="a" style="left:{cx - d / 2:.2f}mm;top:12mm;width:{d}mm;height:{d}mm;border-radius:50%;background:{C["paper_light"]};border:0.6mm dashed {C["ink_3"]}"></div>')
        parts.append(f'<div class="a center num" style="left:{cx - d / 2:.2f}mm;width:{d}mm;top:16.4mm;font-size:15pt;color:{C["paper_deep"]}">{i + 1}</div>')
        parts.append(f'<div class="a center" style="left:{cx - 9:.2f}mm;width:18mm;top:29.4mm;font-size:7pt;color:{C["ink_2"]}">第 {i + 1} 个</div>')
    x0 = right - d - (n - 1) * step
    parts.append(f'<svg class="a" style="left:{x0:.2f}mm;top:36.6mm" width="{right - x0 + 2:.2f}mm" height="5mm" viewBox="0 0 {right - x0 + 2:.2f} 5">'
                 f'<line x1="0" y1="2.5" x2="{right - x0 - 5:.2f}" y2="2.5" stroke="{C["ink"]}" stroke-width="0.5" stroke-dasharray="2 1.2"/>'
                 f'<path d="M{right - x0 - 5:.2f} 0.4 L{right - x0 + 1:.2f} 2.5 L{right - x0 - 5:.2f} 4.6 Z" fill="{C["ink"]}"/></svg>')
    parts.append(f'<div class="a row" style="left:{x0:.2f}mm;width:{right - x0:.2f}mm;top:43mm;font-size:7.4pt"><span>后到的排在左边</span><span class="sp"></span><b>先到的离柜台最近</b></div>')
    parts.append(f'<div class="a disc" style="left:{x0:.2f}mm;top:50.6mm">{DISC}</div>')
    parts.append(f'<div class="a" style="left:193mm;top:5mm;width:12mm;height:50mm;background:{C["ink"]};border-radius:1.6mm"></div>')
    parts.append(f'<div class="a" style="left:195mm;top:8mm;width:8mm;height:5mm;border-radius:4mm 4mm 0 0;background:{C["sun"]}"></div>')
    parts.append(f'<div class="a vt disp" style="left:195.4mm;top:17mm;font-size:13pt;color:{C["sun"]}">开户柜台</div>')
    return Card(key="queue", w=QW, h=QH, html=trim("".join(parts), QW, QH), label="开户排队条 210×60")


# ======================================================================= 委托单（A6，单色）

SW, SH = 105.0, 148.0
K = "#000"
SLIP_CSS = """
.srow { display: flex; align-items: center; gap: 1.8mm; min-height: 5mm; }
.srow.top { align-items: flex-start; }
.stag { flex: none; width: 11.6mm; height: 4.3mm; background: #000; color: var(--slipbg, #fff); border-radius: 0.8mm; font-weight: 700;
        font-size: 7.2pt; line-height: 1; display: flex; align-items: center; justify-content: center; letter-spacing: .04em; }
.sbody { flex: 1 1 auto; min-width: 0; display: flex; flex-wrap: wrap; align-items: center; column-gap: 2.1mm; row-gap: 0.5mm;
         font-size: 7.4pt; line-height: 1.25; }
.sbody .it { white-space: nowrap; display: inline-flex; align-items: center; }
.snote { font-size: 7pt; }
.sbar { width: 0; height: 3.2mm; border-left: 0.5pt solid #000; }
"""


def _warn_k(size=2.9):
    s = size
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="flex:none;vertical-align:-0.4mm">'
            f'<polygon points="{s / 2},0.25 {s - 0.2},{s - 0.3} 0.2,{s - 0.3}" fill="none" stroke="#000" stroke-width="0.35" stroke-linejoin="round"/>'
            f'<rect x="{s / 2 - 0.22:.2f}" y="{s * 0.36:.2f}" width="0.44" height="{s * 0.28:.2f}" fill="#000"/>'
            f'<circle cx="{s / 2}" cy="{s * 0.76:.2f}" r="0.26" fill="#000"/></svg>')


def _seal_k(sid, size=5.0):
    ch = SPECIES_SEAL.get(sid, "?")
    s = size
    return (f'<svg width="{s}mm" height="{s}mm" viewBox="0 0 {s} {s}" style="flex:none">'
            f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2 - 0.2}" fill="none" stroke="#000" stroke-width="0.35"/>'
            f'<text x="{s / 2}" y="{s / 2 + s * 0.2:.2f}" font-size="{s * 0.56:.2f}" text-anchor="middle" fill="#000" font-family="Smiley Sans Oblique">{esc(ch)}</text></svg>')


def _srow(tag, body, top=False):
    return f'<div class="srow{" top" if top else ""}"><span class="stag">{tag}</span><div class="sbody">{body}</div></div>'


def _opt_rows(sc):
    rows = []
    for o in sc["opts"]:
        dots = icons.dots(o["shares"], 3, d=2.1, gap=0.55, color=K)
        rows.append(f'<div class="row" style="gap:1mm;height:4mm;font-size:7.4pt;white-space:nowrap">{cb()}<b>{esc(o["key"])}</b>'
                    f'<span style="overflow:hidden;flex:0 1 auto;min-width:0">{esc(o["text"])}</span><span class="sp"></span>{dots}</div>')
    return "".join(rows)


def _risk_kinds(sc):
    return [k for k, e in sc.get("evidence", {}).items() if isinstance(e, dict) and e.get("risk")]


def order_slip(m: Model, season: str, tint=None) -> Card:
    scA = next((s for s in m.scenes if s["season"] == season and s.get("door") == "A"), None)
    bB = m.door_b(season) or {}
    scB = bB.get("scene") if bB.get("open") else None
    cn = SEASON_CN[season]
    M = 5.0
    bg = tint or "#fff"
    bar = '<span class="sbar"></span>'
    parts = [f'<style>{SLIP_CSS}</style>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{SW + 6}mm;height:{SH + 6}mm;background:{bg}"></div>']
    shapes = "".join(icons.shape(x, 3.3, K) for x in ["circle", "triangle", "square", "diamond", "star"])
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:4mm;height:9.4mm;gap:2.2mm;color:{K}">'
                 f'<span class="disp" style="display:inline-flex;align-items:center;justify-content:center;width:9.4mm;height:9.4mm;border-radius:50%;background:{K};color:{bg}"><span style="font-size:16pt">{cn}</span></span>'
                 f'<div class="col"><span class="row" style="gap:2mm;align-items:baseline"><span class="disp" style="font-size:17pt;line-height:1">委托单</span><b style="font-size:8pt">亮单前填</b></span>'
                 f'<span class="caps" style="font-size:7pt;letter-spacing:.18em;margin-top:0.8mm">ORDER SLIP · {SEASON_EN.get(season, "")}</span></div>'
                 f'<div class="sp"></div><div class="col" style="align-items:flex-end;gap:0.9mm">'
                 f'<span class="row" style="gap:1.2mm;font-size:7pt">玩家{shapes}</span><span style="font-size:7pt">圈出你的记号</span></div></div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:14.4mm;border-top:1.4pt solid {K}"></div>')
    risk_a = _risk_kinds(scA) if scA else []
    risk_b = _risk_kinds(scB) if scB else []

    def ev_item(k, label):
        marks = []
        if k in risk_a:
            marks.append(_warn_k() + ("A" if scB else ""))
        if k in risk_b:
            marks.append(_warn_k() + "B")
        mk = f'<span class="row" style="gap:0.3mm;font-size:7pt;font-weight:700;margin-left:0.6mm">{"".join(marks)}</span>' if marks else ""
        return f'<span class="it">{cb()}{label}{mk}</span>'

    rows = []
    rows.append(_srow("门", f'{it("A")}{it("B")}{bar}<span class="it">落在&nbsp;<span style="letter-spacing:.12em">①②③④⑤⑥</span></span>{bar}{it("④答对")}{it("⑤坐下")}'))
    rows.append(_srow("认出来了", f'<span class="it">事件名{ln(46)}</span><span class="snote">亮单前写</span>'))
    rows.append(_srow("看了", f'{ev_item("price", "量价")}{ev_item("data", "数据")}{ev_item("news", "消息")}{ev_item("tip", "锦囊")}<span class="snote">第一张画圈</span>'))
    blocks = []
    for door, sc in (("A", scA), ("B", scB)):
        if not sc:
            continue
        tag = f"门 {door}" + (" · P1" if sc.get("tier") == "P1" else "")
        blocks.append(f'<div style="flex:1 1 0;min-width:0"><div style="font-size:7pt;font-weight:700;border-bottom:0.5pt solid {K};margin-bottom:0.5mm;height:3.4mm">{tag}</div>{_opt_rows(sc)}</div>')
    if not scB:
        t = bB.get("teaser", "")
        blocks.append(f'<div style="flex:1 1 0;min-width:0"><div style="font-size:7pt;font-weight:700;border-bottom:0.5pt dashed {K};margin-bottom:0.8mm;height:3.4mm">门 B · 未开放</div>'
                      f'<div style="font-size:7pt;line-height:1.35"><b>敬请期待</b><br>{esc(t)}</div></div>')
    rows.append(_srow("选项", f'<div class="row" style="flex:1;gap:3mm;align-items:flex-start">{"".join(blocks)}</div>', top=True))
    rows.append(_srow("理由", f'<span class="snote">勾一个</span>{it("量价")}{it("数据")}{it("消息")}{it("跟别人")}{it("直觉")}{it("看不懂")}'
                      f'<span class="it">{cb()}规则牌：{ln(22)}</span><span class="snote">决策日看规则牌背面</span>'))
    rows.append(_srow("计划", f'{it("跌了就走")}{it("跌了就加")}{it("不定")}<span class="snote">0 份不勾“走”；用规则牌不勾</span>'))
    last = []
    if season == "spring":
        last.append(f'<span class="it"><b>春 A</b>&nbsp;我选时排队条上有{ln(7)}人</span>{bar}')
    last.append(f'<span class="it"><b>想开的门</b></span>{it("A")}{it("B")}')
    rows.append(_srow("备注", "".join(last)))
    parts.append(f'<div class="a fit" data-min="7" data-what="委托单正面" style="left:{M}mm;right:{M}mm;top:15.6mm;height:55.6mm;color:{K};display:flex;flex-direction:column;justify-content:space-between">{"".join(rows)}</div>')
    # 对折线
    parts.append(f'<div class="a" style="left:-3mm;right:-3mm;top:74mm;border-top:0.6pt dashed {K}"></div>')
    parts.append(f'<div class="a row" style="left:0;right:0;top:72.3mm;justify-content:center"><span style="background:{bg};padding:0 2mm;font-size:7pt;color:{K}">'
                 f'对折线 · 字朝里对折，扣在玩家板上 · 三二一一起翻开</span></div>')
    # 复盘面
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:77.2mm;height:6mm;gap:2mm;color:{K};border-bottom:1.4pt solid {K}">'
                 f'<span class="disp" style="font-size:13pt">复盘面</span><span style="font-size:7.2pt">快进和揭幕时填</span><span class="sp"></span>'
                 f'<span style="font-size:7pt">{cn}季 · {SEASON_NAME[season]}</span></div>')
    b = []
    door_b_note = f'{bar}<span class="it"><b>门 B</b>&nbsp;只结算不操作</span>' if scB else ""
    chg = f'{bar}<span class="it"><b>改主意了吗</b></span>{it("是")}{it("否")}'
    if season == "spring":
        b.append(_srow("快进", f'{it("持有")}{it("卖出")}{it("加仓")}{it("进场")}<span class="snote">0 份的选 C 才能进场</span>'))
        b.append(_srow("改主意", f'{it("是")}{it("否")}'))
    elif season == "summer":
        b.append(_srow("快进", f'{it("持有")}{it("卖出（去抢卖出窗口）")}{bar}{it("强制平仓")}<span class="snote">选 A、资金低于 5</span>'))
        b.append(_srow("窗口", f'{it("抢到了")}{it("没抢到 · 放跌停锁")}{chg}'))
    elif season == "autumn":
        b.append(_srow("快进", f'<span class="it"><b>门 A</b>&nbsp;抱团圈</span>{it("留下")}{it("离开")}{door_b_note}'))
        b.append(_srow("改主意", f'{it("是")}{it("否")}'))
    else:
        b.append(_srow("熔断", f'<span class="it"><b>门 A</b>&nbsp;第 1 张后调{ln(7)}第 2 张后调{ln(7)}</span><span class="snote">加 1 / 减 1 / 不动</span>'))
        b.append(_srow("第二次", f'{it("补仓")}{it("止损")}{it("不看了")}{door_b_note}'))
        b.append(_srow("改主意", f'{it("是")}{it("否")}'))
    if season == "winter":
        b.append(_srow("结算", f'<span class="it">①±{ln(6)}</span><span class="it">②±{ln(6)}</span><span class="it">③±{ln(6)}</span><span class="it">揭幕 ±{ln(6)}</span><span class="it">＝ 资金{ln(8)}</span>'))
    else:
        b.append(_srow("结算", f'<span class="it">第一段&nbsp;±{ln(10)}</span><span class="it">第二段&nbsp;±{ln(10)}</span><span class="it">＝ 资金{ln(12)}</span>'))
    st = lambda n: "".join(icons.star(3.1, K, hollow=True) for _ in range(n))
    b.append(_srow("方法星", f'<span class="it">证据&nbsp;{st(2)}</span><span class="it">理由一致&nbsp;{st(1)}</span><span class="it">计划照做&nbsp;{st(1)}</span><span class="it">＝{ln(7)}颗</span>'))
    cell = lambda t, w: (f'<div class="col" style="align-items:center;gap:0.3mm"><span style="font-size:7pt;line-height:1">{t}</span>'
                         f'<span style="display:block;width:{w}mm;height:6mm;border:0.5pt solid {K};border-radius:0.8mm"></span></div>')
    b.append(_srow("图标", f'<div class="row" style="gap:1.6mm;align-items:flex-end">{cell("理由 ×2", 17)}{cell("第一张证据 ×1", 17)}{cell("机会牌 ×1", 14)}'
                           f'<span style="padding-bottom:1.2mm;font-size:7pt">写物种的字</span></div>', top=True))
    seals = "".join(_seal_k(x, 4.8) for x in ["cheetah", "elephant", "meerkat", "fox", "owl", "chameleon"])
    b.append(_srow("物种币", f'<span class="row" style="gap:1mm">{seals}</span><span class="snote">圈一个</span>{bar}{it("空心（认出来了）")}'))
    b.append(_srow("标记", f'{it("平局补测")}{it("改（我不同意）")}{bar}<span class="it"><b>揭幕后</b></span>{it("事件名写对了")}'))
    parts.append(f'<div class="a fit" data-min="7" data-what="委托单复盘面" style="left:{M}mm;right:{M}mm;top:85.6mm;height:50.4mm;color:{K};display:flex;flex-direction:column;justify-content:space-between">{"".join(b)}</div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:137.6mm;border-top:0.5pt solid {K}"></div>')
    parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:138.6mm;font-size:7pt;color:{K}"><span>四张委托单合起来，就是你的对局记录</span><div class="sp"></div><span>{DISC}</span></div>')
    key = f"slip-{season}" + ("-tint" if tint else "")
    return Card(key=key, w=SW, h=SH, html=trim("".join(parts), SW, SH), style=f"background:{bg};--slipbg:{bg};", label=f"委托单 · {cn}季" + (" · 季节色纸预览" if tint else " · 单色"))


SLIP_TINT = {"spring": "#DDEBD3", "summer": "#F6D5CC", "autumn": "#F4E0BF", "winter": "#D4E4E7"}


# ======================================================================= 终局档案卡（A5 竖 148×210，双面）

RW, RH = 148.0, 210.0


def _privacy() -> str:
    import re
    txt = content.load_text("rules-v1.md")
    mm = re.search(r"\*\*隐私\*\*[：:]\s*(.+)", txt)
    if not mm:
        content.NOTES.append("规则书里没找到“隐私”一句，档案卡隐私栏留空")
        return ""
    return mm.group(1).strip()


def _two_you(sr: dict) -> list[tuple[str, str]]:
    ty = sr.get("two_you", {}) or {}
    out = []
    try:
        out.append(("对得上", ty["same"].split("：", 1)[1]))
    except (KeyError, IndexError):
        pass
    try:
        parts = [x for x in ty["differ"].split("。") if x]
        out.append(("对不上", parts[1].split("：")[0] + "。" + parts[2] + "。"))
    except (KeyError, IndexError):
        pass
    try:
        parts = [x for x in ty["risk_gap"].split("。") if x]
        out.append(("游戏里更敢", parts[1] + "。"))
    except (KeyError, IndexError):
        pass
    if ty.get("no_real"):
        out.append(("没遇到过大跌", ty["no_real"]))
    return out


def record_card(m: Model) -> tuple[Card, Card]:
    D = m.D
    sr = D.get("self_and_real", {})
    M = 7.0
    sp6 = [s for s in SPECIES_ORDER if s != "beaver"]
    parts = [_band(RW, C["ink"], f'<span class="disp" style="font-size:19pt">终局档案卡</span>'
                   f'<span class="caps" style="font-size:7pt;letter-spacing:.22em;margin-left:2mm">RECORD</span>',
                   f'<span style="font-size:7.4pt">玩家 {" ".join(icons.shape(s, 3.4, None, C["paper_light"]) for s in ["circle", "triangle", "square", "diamond", "star"])} 圈一个</span>', h=13)]

    def sec(n, title, body, note=""):
        return (f'<div style="margin-bottom:3.6mm"><div class="fhead"><span class="kb sq" style="width:5mm;height:5mm;font-size:10pt">{n}</span>'
                f'<span class="disp" style="font-size:12pt">{esc(title)}</span><span style="font-size:7pt;color:{C["ink_2"]}">{esc(note)}</span></div>{body}</div>')

    # 1 自评
    meds = []
    for s in sp6:
        md = art.medal(s)
        img = _disc_img(md["uri"], 11, f"0.6mm solid {SPECIES_COLOR[s]}") if md else ""
        meds.append(f'<div class="col" style="align-items:center;gap:0.6mm">{img}<span class="b7" style="font-size:7.4pt">{esc(m.sp.get(s, {}).get("name", s))}</span></div>')
    risk = "".join(it(r["text"]) for r in sr.get("self_assessment", {}).get("risk_choices", []))
    s1 = (f'<div class="row" style="justify-content:space-between;margin-bottom:1.4mm">{"".join(meds)}</div>'
          f'<div class="fm"><b>我觉得我是</b>圈一个 ↑<span style="color:{C["ink_3"]}">｜</span><b>我平时更像</b>{risk}</div>')
    # 2 物种
    coins = "".join(f'<span class="it">{icons.season_disc(s, 4.2)}&nbsp;{SEASON_CN[s]}{ln(13)}</span>' for s in SEASON_ORDER)
    conf = "".join(it(x) for x in ["很确定", "比较确定", "初步", "待确认"])
    s2 = (f'<div class="fm" style="margin-bottom:1.2mm"><b>四季物种币</b>{coins}</div>'
          f'<div class="fm" style="margin-bottom:1.2mm"><b>工具箱</b>海狸币{ln(8)}枚<span style="color:{C["ink_3"]}">｜</span><b>隐藏特质</b>{it("海狸")}</div>'
          f'<div class="fm"><b>我的物种</b>{ln(20)}<b>置信度</b>{conf}</div>')
    # 3 徽章 + 分数
    bds = "".join(it(b["name"]) for b in D.get("badges", []))
    s3 = (f'<div class="fm" style="margin-bottom:1.4mm"><b>徽章</b>{bds}</div>'
          f'<div class="fm"><b>终局分</b>方法星{ln(10)}＋ 名次分{ln(10)}＝<span class="ln" style="width:14mm;height:5mm"></span>'
          f'<span style="font-size:7pt;color:{C["ink_2"]}">资金第一 6、第二 4、第三 2、其余 1；还拿着负债牌记 0</span></div>')
    # 4 现实题
    rq = []
    for q in sr.get("real_questions", []):
        opts = "".join(f'<span class="it" style="margin-right:2mm">{cb()}<b>{esc(o["key"])}</b>&nbsp;{esc(o["text"])}</span>' for o in q.get("options", []))
        rq.append(f'<div style="margin-bottom:1.8mm"><div class="b7" style="font-size:8.4pt;margin-bottom:0.8mm">{esc(q["prompt"])}</div>'
                  f'<div class="fm" style="column-gap:0">{opts}</div></div>')
    s4 = "".join(rq)
    # 5 两个你 + 任务
    tasks = "".join(it(x) for x in ["读图", "探索", "状态", "核查", "假设"])
    s5 = (f'<div class="fm" style="margin-bottom:1.4mm"><b>两个你</b>自评{ln(14)}／ 游戏{ln(14)}／ 现实{ln(14)}</div>'
          f'<div class="fm" style="margin-bottom:1.4mm"><b>一句话</b>{ln(100)}</div>'
          f'<div class="fm"><b>我的任务</b>{tasks}<span>＋</span>{it("风险校准")}<span style="color:{C["ink_3"]}">×</span>{it("入门")}{it("进阶")}</div>')
    body = (sec(1, "自评", s1, "序章时偷偷填，扣在玩家板下，终局再翻开") + sec(2, "我的物种", s2, "数币：空心算半枚") +
            sec(3, "徽章与终局分", s3) + sec(4, "两道现实题", s4, "现实里的你") + sec(5, "两个你 · 下一步", s5, "决策树在背面"))
    parts.append(f'<style>.rec .fm {{ font-size: 8.2pt; row-gap: 1mm; }} .rec .fm .ln {{ height: 4.4mm; }} .rec .cb {{ width: 3mm; height: 3mm; }}</style>')
    parts.append(f'<div class="a fit rec" data-min="7" data-what="档案卡正面" style="left:{M}mm;right:{M}mm;top:17.4mm;height:160mm;font-size:8.2pt">{body}</div>')
    cap, cap2 = "扫码录入档案", "生成完整画像"
    qw, qh = qrsvg.block_size(20, 2.4, cap)
    parts.append(qrsvg.block("record", RW - M - qw + 0.6, RH - 6 - qh, 20, 2.4, cap, cap2, where="终局档案卡"))
    parts.append(f'<div class="a" style="left:{M}mm;width:{RW - 2 * M - qw - 4}mm;top:{RH - 6 - qh + 1}mm;font-size:7.4pt;line-height:1.45;color:{C["ink_2"]}">'
                 f'<b style="color:{C["ink"]}">隐私</b>：{esc(_privacy())}'
                 f'<br><span style="font-size:7pt">{DISC}</span></div>')
    front = Card(key="record", w=RW, h=RH, html=trim("".join(parts), RW, RH), qr=["record"], label="终局档案卡 · 正面")

    # 背面：置信度 + 任务决策树
    bp = [_band(RW, C["mustard"], '<span class="disp" style="font-size:17pt">怎么定物种、领任务</span>', '<span class="caps" style="font-size:7pt;letter-spacing:.2em">HOW TO READ</span>', h=13)]
    conf_rows = "".join(f'<div class="row" style="border-bottom:0.5pt dotted {C["ink_3"]};height:6mm;font-size:7.6pt"><span style="width:62mm">{esc(c["rule"])}</span><b>{esc(c["label"])}</b></div>'
                        for c in D.get("meta", {}).get("confidence", [])[:4])
    cham = next((c for c in D.get("meta", {}).get("confidence", []) if "变色龙" in c.get("label", "")), None)
    conf_html = conf_rows + (f'<div style="font-size:7.4pt;line-height:1.4;margin-top:1.2mm"><b>变色龙</b>：{esc(cham["rule"])}；{esc(cham["label"].replace("变色龙：", ""))}</div>' if cham else "")
    tree = D.get("meta", {}).get("task_tree", [])
    TASK_CN = {"chart": "读图入门", "explore": "数据自主探索", "regime": "状态判断", "verify": "证据核查", "hypo": "假设检验", "risk": "风险校准"}
    steps = [t for t in tree if "step" in t]
    nodes = []
    for i, t in enumerate(steps):
        last = i == len(steps) - 1
        cond = esc(t["if"])
        res = TASK_CN.get(t["then"], t["then"])
        nodes.append(f'<div class="row" style="gap:2mm;margin-bottom:1.2mm">'
                     f'<span class="kb sq" style="width:5.2mm;height:5.2mm;font-size:10pt;background:{C["sky_deep"]}">{t["step"]}</span>'
                     f'<div style="flex:1;border:0.5pt solid {C["ink"]};border-radius:1.2mm;padding:1.2mm 2mm;font-size:7.8pt;line-height:1.35;background:{C["paper_light"]}">{"" if last else "如果 "}{cond}</div>'
                     f'{icons.arrow_right(6, 3)}<div class="disp" style="width:30mm;font-size:11.5pt">{esc(res)}</div></div>')
        if not last:
            nodes.append(f'<div style="margin:-0.6mm 0 0.6mm 2.2mm;font-size:7pt;color:{C["ink_2"]}">↓ 不符合就往下看</div>')
    level = next((t["level"] for t in tree if "level" in t), "").replace("拿 adv", "拿进阶").replace("否则 basic", "否则拿入门")
    extra = next((t["extra"] for t in tree if "extra" in t), "")
    tree_html = ("".join(nodes) +
                 f'<div style="margin-top:2mm;font-size:7.8pt;line-height:1.45"><b>入门还是进阶</b>：{esc(level)}</div>'
                 f'<div style="margin-top:1mm;font-size:7.8pt;line-height:1.45"><b>加拿一张</b>：{esc(extra.replace("risk", "风险校准"))}</div>')
    bbody = (sec("A", "置信度", conf_html, "看最多那种有几枚") + sec("B", "任务决策树", tree_html, "从上往下，第一个符合的就是你的任务"))
    bp.append(f'<div class="a fit" data-min="7" data-what="档案卡背面" style="left:{M}mm;right:{M}mm;top:17mm;height:130mm;font-size:7.6pt">{bbody}</div>')
    ty = "".join(f'<div class="row" style="align-items:flex-start;gap:2mm;margin-bottom:1.2mm"><b style="flex:none;width:19mm">{esc(h)}</b><span>{esc(t)}</span></div>'
                 for h, t in _two_you(m.D.get("self_and_real", {})))
    bp.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:150mm;border-radius:2mm;background:{C["paper_light"]};padding:2.6mm 3.4mm;font-size:7.8pt;line-height:1.45">'
              f'<div class="disp" style="font-size:12pt;margin-bottom:1.6mm">两个你：自评和游戏不一样怎么办</div>{ty}'
              f'<div style="margin-top:1.4mm;font-size:7pt;color:{C["ink_2"]}">物种只描述习惯，游戏里的表现，仅供参考 · {DISC}</div></div>')
    back = Card(key="record-b", w=RW, h=RH, html=trim("".join(bp), RW, RH), label="终局档案卡 · 背面")
    return front, back


# ======================================================================= 汇总

def mini_pairs(m: Model):
    pairs = []
    for b in m.D.get("badges", []):
        for n in range(1, int(b.get("copies", 2)) + 1):
            pairs.append((badge_front(m, b, n), badge_back(m, b, n)))
    debt = [(debt_front(m, n), debt_back(n)) for n in range(1, int(m.D.get("debt", {}).get("copies", 8)) + 1)]
    return pairs, debt
