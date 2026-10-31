"""标准卡（63×88）：证据（量价/数据/消息）、锦囊、快进、机会、补测、规则、数据港口、任务、AI 物种，以及各副牌的牌背。"""

from __future__ import annotations

import math
import re

from . import art, charts, content, icons, qrsvg, rulesig
from .c_a6 import on
from .core import Card, esc, trim
from .model import Model
from .tokens import C, EVIDENCE_KIND, SEASON, SPECIES_CN, SPECIES_COLOR

W, H = 63.0, 88.0
M = 4.6
PT = 0.3528
DISC = "投资者教育游戏，不构成投资建议"
QS = 18.0  # 二维码码区边长（≥18mm）
FOOT_Y = 80.4

DECK = {
    "chance": {"cn": "机会", "en": "CHANCE", "color": C["sun"], "icon": "dice", "tile": "chance", "line": "落在 ② 机会格时抽一张"},
    "retest": {"cn": "补测", "en": "RETEST", "color": C["sage"], "icon": "magnifier", "tile": None, "line": "驿站平局或“我不同意”时抽"},
    "rules": {"cn": "规则牌", "en": "RULE CARD", "color": C["sky"], "icon": "compass", "tile": "research", "line": "落在 ③ 研究所：摸两张留一张"},
    "dataport": {"cn": "数据港口", "en": "DATA PORT", "color": C["sky_light"], "icon": "ledger", "tile": "dataport", "line": "落在 ④ 数据港口时抽一张"},
    "tasks": {"cn": "任务", "en": "TASK", "color": C["paper_deep"], "icon": "kite", "tile": None, "line": "终局按档案卡的决策树领一张"},
    "ai": {"cn": "AI 物种", "en": "AI SPECIES", "color": C["ink_3"], "icon": "waterwheel", "tile": None, "line": "单人规则：挑两张当对手"},
    "ff": {"cn": "快进", "en": "FAST FORWARD", "color": C["ink_2"], "icon": "hourglass", "tile": None, "line": "亮单之后再翻开"},
}


def _band(color, left, right, h=11.0):
    fg = on(color)
    return (f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{h + 3}mm;background:{color}"></div>'
            f'<div class="a row" style="left:{M}mm;right:{M}mm;top:0;height:{h}mm;color:{fg};gap:1.4mm">{left}<div class="sp"></div>{right}</div>'
            f'<div class="a mstripe" style="left:-3mm;top:{h}mm;width:{W + 6}mm;height:0.9mm"></div>')


def _icon_disc(name, size=7.6, ring=None, tile=False):
    a = art.tile_art(name) if tile else art.icon(name)
    if not a:
        return ""
    rb = f"border:0.5mm solid {ring};" if ring else ""
    return (f'<span style="display:inline-block;flex:none;width:{size}mm;height:{size}mm;border-radius:50%;overflow:hidden;background:{C["paper"]};{rb}">'
            f'<img src="{a["uri"]}" style="width:100%;height:100%;display:block"></span>')


def _scene_tag(sc, fg):
    return (f'<span class="chip line" style="color:{fg};height:4.4mm;font-size:7pt;padding:0 1.6mm">{esc(sc["season_cn"])} · 门 {esc(sc.get("door", "A"))}</span>')


def _foot(text=DISC, top=FOOT_Y):
    return f'<div class="a disc" style="left:{M}mm;right:{M}mm;top:{top}mm;white-space:nowrap">{esc(text)}</div>'


def _vw(s: str) -> float:
    """按字宽估算：汉字 1，ASCII 约 0.55。"""
    return sum(0.55 if ord(c) < 128 else 1 for c in s)


def ev_source(e: dict, kind: str, limit: float = 19) -> str:
    """证据来源缩成一行：数据：……（Panda Data 的几项合并成一段放最前）。"""
    s = e.get("source") or ""
    if not s or kind == "tip":
        return ""
    s = re.sub(r"（[^）]*）|\([^)]*\)", "", s)
    panda, parts = [], []
    for p in re.split(r"[；;]", s):
        p = p.strip()
        if not p or p.startswith("估值分位待"):
            continue
        p = re.sub(r"^(行情|两融|估值)：", "", p)
        p = re.sub(r"^对比：", "对比", p)
        p = re.sub(r"，?待 ?Panda.*$", "，待复核", p)
        p = p.replace("公开日线接口", "公开日线")
        m = re.search(r"Panda Data (.+)$", p)
        if m and "待复核" not in p:
            if m.group(1) not in panda:
                panda.append(m.group(1))
        else:
            parts.append(p)
    if panda:
        parts.insert(0, "Panda Data " + "、".join(panda))
    out = ""
    for p in parts:
        cand = p if not out else out + "；" + p
        if _vw(cand) > limit and out:
            break
        out = cand
    return ("来源：" if kind == "news" else "数据：") + out


# ======================================================================= 证据牌

def _tape(w, h, inner):
    """行情纸带：锯齿撕边 + 两排打孔。"""
    z, n = 0.9, 6
    left = [(0 if i % 2 == 0 else z, i * h / (2 * n)) for i in range(2 * n + 1)]
    right = [(w if i % 2 == 0 else w - z, h - i * h / (2 * n)) for i in range(2 * n + 1)]
    poly = " ".join(f"{x:.2f},{y:.2f}" for x, y in left + right)
    holes = "".join(f'<circle cx="{x:.2f}" cy="1.15" r="0.42"/><circle cx="{x:.2f}" cy="{h - 1.15:.2f}" r="0.42"/>'
                    for x in [2.6 + i * 2.2 for i in range(int((w - 5) / 2.2) + 1)])
    return (f'<svg class="a" style="left:0;top:0" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            f'<polygon points="{poly}" fill="{C["paper_deep"]}"/><g fill="{C["paper"]}">{holes}</g>'
            f'<line x1="1.4" y1="2.1" x2="{w - 1.4}" y2="2.1" stroke="{C["ochre"]}" stroke-width="0.18" stroke-dasharray="0.6 0.5"/>'
            f'<line x1="1.4" y1="{h - 2.1}" x2="{w - 1.4}" y2="{h - 2.1}" stroke="{C["ochre"]}" stroke-width="0.18" stroke-dasharray="0.6 0.5"/></svg>'
            f'<div class="row" style="position:absolute;left:2.6mm;right:2.2mm;top:2.4mm;bottom:2.4mm;gap:1.8mm">{inner}</div>')


def evidence_front(m: Model, sc: dict, kind: str) -> Card:
    e = sc["evidence"][kind]
    k = EVIDENCE_KIND[kind]
    col = k["color"]
    fg = on(col)
    left = f'{_icon_disc(k["icon"], 7.6)}<span class="disp" style="font-size:15pt">{k["cn"]}</span>'
    parts = [_band(col, left, _scene_tag(sc, fg))]
    y = 13.2
    risk = bool(e.get("risk"))
    tw = W - 2 * M - (9.5 if risk else 0)
    parts.append(f'<div class="a disp fit" data-min="10" data-what="证据标题" style="left:{M}mm;top:{y}mm;width:{tw}mm;height:6.4mm;font-size:13pt;white-space:nowrap">{esc(e.get("title", ""))}</div>')
    if risk:
        parts.append(f'<div class="a" style="right:{M - 0.6}mm;top:{y - 0.9}mm">{icons.warn_corner(8.0)}</div>')
    y += 7.8
    stat, chart, lines = e.get("stat"), e.get("chart"), e.get("lines", [])
    cw = W - 2 * M
    src = ev_source(e, kind)
    bottom = 76.4 if src else 79.6
    if kind == "price":
        th = 11.0
        inner = (f'<span class="num" style="font-size:17pt;line-height:1;white-space:nowrap">{esc(stat.get("value", ""))}</span>'
                 f'<span style="font-size:7pt;line-height:1.2;color:{C["ink_2"]}">{esc(stat.get("caption", ""))}</span>') if stat else (
                 f'<span class="mono" style="font-size:8pt;letter-spacing:.08em;color:{C["ink_2"]}">TICKER · 当时的行情</span>')
        parts.append(f'<div class="a" style="left:{M}mm;top:{y}mm;width:{cw}mm;height:{th}mm">{_tape(cw, th, inner)}</div>')
        y += th + 1.4
    elif kind == "data" and stat:
        parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{y}mm;height:9.6mm;padding:0 1.2mm 0 0;gap:1.6mm;border-bottom:1.6pt double {C["ochre"]}">'
                     f'<span class="b7" style="font-size:7pt;color:{C["ochre"]};flex:none">合计</span>'
                     f'<span style="font-size:7pt;line-height:1.2;color:{C["ink_2"]};flex:1">{esc(stat.get("caption", ""))}</span>'
                     f'<span class="num" style="font-size:17pt;line-height:1;white-space:nowrap">{esc(stat.get("value", ""))}</span></div>')
        y += 10.8
    if chart and chart.get("values"):
        chh = 15.5 if kind == "price" else 13.6
        parts.append(f'<div class="a" style="left:{M}mm;top:{y}mm;width:{cw}mm;height:{chh}mm">{charts.evidence_chart(chart, cw, chh, kind if kind in ("price", "data") else "data")}</div>')
        parts.append(f'<div class="a nowrap" style="left:{M}mm;right:{M}mm;top:{y + chh + 0.2}mm;font-size:7pt;line-height:1.15;color:{C["ink_3"]}">{esc(chart.get("unit", ""))}</div>')
        y += chh + 3.8
    if kind == "news":
        items = "".join(
            f'<div style="padding:1.3mm 1.6mm 1.4mm;border-bottom:0.6pt dashed {C["ink_3"]};display:flex;gap:1.6mm">'
            f'<span class="mono" style="font-size:0.88em;color:{C["ink_3"]};flex:none;padding-top:.25mm">{i + 1:02d}</span>'
            f'<span style="line-height:1.4">{esc(t)}</span></div>' for i, t in enumerate(lines))
        parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{y}mm;background:{C["paper_light"]};border-radius:0.6mm">'
                     f'<div class="row" style="height:5.4mm;padding:0 1.6mm;background:{C["ink"]};color:{C["paper_light"]};border-radius:0.6mm 0.6mm 0 0">'
                     f'<span class="b7" style="font-size:7.5pt;letter-spacing:.2em">快讯 · 电报</span><div class="sp"></div>'
                     f'<span class="chip" style="background:{C["mustard"]};color:{C["ink"]};height:3.6mm;font-size:7pt;padding:0 1.4mm">已隐去名字和日期</span></div>'
                     f'<div class="fit" data-min="7" data-what="快讯" style="max-height:{bottom - y - 6.4:.1f}mm;font-size:8pt">{items}</div>'
                     f'<svg width="{cw}mm" height="1.6mm" viewBox="0 0 {cw} 1.6" style="display:block"><path d="{_zig(cw)}" fill="{C["paper"]}"/></svg></div>')
    elif kind == "data":
        rows = "".join(
            f'<div style="display:flex;border-bottom:0.5pt solid {C["sky_light"]};padding:0.6mm 0 0.7mm">'
            f'<span class="mono" style="width:4.6mm;flex:none;font-size:7pt;color:{C["ochre"]};padding-top:0.2mm">{i + 1:02d}</span>'
            f'<span style="flex:1;padding-left:2mm;line-height:1.36">{esc(t)}</span></div>' for i, t in enumerate(lines))
        parts.append(f'<div class="a fit" data-min="7" data-what="证据正文" style="left:{M}mm;right:{M}mm;top:{y}mm;max-height:{bottom - y:.1f}mm;font-size:7.6pt;'
                     f'background-image:linear-gradient(to right, transparent 4.9mm, {C["ochre"]} 4.9mm, {C["ochre"]} 5.08mm, transparent 5.08mm, transparent 5.5mm, {C["ochre"]} 5.5mm, {C["ochre"]} 5.68mm, transparent 5.68mm)">{rows}</div>')
    else:
        lis = "".join(f"<li>{esc(t)}</li>" for t in lines)
        parts.append(f'<ul class="a dots fit lines" data-min="7" data-what="证据正文" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{bottom - y:.1f}mm;font-size:7.6pt;line-height:1.36">{lis}</ul>')
    if src:
        parts.append(f'<div class="a srcline fit" data-min="7" data-what="来源" style="left:{M}mm;right:{M}mm;top:76.7mm;height:3.4mm;white-space:nowrap">{esc(src)}</div>')
    parts.append(_foot())
    return Card(key=f"ev-{sc['id']}-{kind}", w=W, h=H, html=trim("".join(parts), W, H),
                label=f"{k['cn']}证据 · {sc['season_cn']}{sc.get('door', 'A')}{' · 风险' if risk else ''}")


def _zig(w, h=1.6, step=1.6):
    pts = [f"M0 0"]
    x = 0.0
    while x < w:
        pts.append(f"L{x + step / 2:.2f} {h:.2f} L{min(x + step, w):.2f} 0")
        x += step
    pts.append(f"L{w} 0 Z")
    return " ".join(pts)


def tip_front(m: Model, sc: dict) -> Card:
    e = sc["evidence"]["tip"]
    col = C["mustard"]
    left = f'{_icon_disc("letter", 7.6)}<span class="disp" style="font-size:15pt">锦囊</span>'
    parts = [_band(col, left, _scene_tag(sc, on(col)))]
    lw = W - 2 * M
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:14mm;height:59mm;background:{C["paper_light"]};border-radius:0.8mm"></div>')
    parts.append(f'<svg class="a" style="left:{M}mm;top:14mm" width="{lw}mm" height="9mm" viewBox="0 0 {lw} 9">'
                 f'<path d="M0 0 L{lw / 2} 7.5 L{lw} 0" fill="none" stroke="{C["mustard"]}" stroke-width="0.5"/></svg>')
    parts.append(f'<div class="a disp" style="left:{M + 2.4}mm;top:22.6mm;font-size:12.5pt">{esc(e.get("title", "猫头鹰的信"))}</div>')
    lis = "".join(f'<p style="margin:0 0 1.6em 0">{esc(t)}</p>' for t in e.get("lines", []))
    parts.append(f'<div class="a fit" data-min="7.5" data-what="锦囊正文" style="left:{M + 2.4}mm;right:{M + 2.4}mm;top:30.2mm;height:28.8mm;font-size:9pt;line-height:1.6;'
                 f'background-image:repeating-linear-gradient(to bottom, transparent 0, transparent calc(1.6em - 0.5pt), {C["paper_deep"]} calc(1.6em - 0.5pt), {C["paper_deep"]} 1.6em)">{lis}</div>')
    md = art.medal("owl")
    if md:
        parts.append(f'<div class="a" style="right:{M + 2}mm;top:61mm;width:10.5mm;height:10.5mm;border-radius:50%;overflow:hidden;border:0.6mm solid {C["sky_deep"]}"><img src="{md["uri"]}" style="width:100%;height:100%"></div>')
    parts.append(f'<div class="a b7" style="right:{M + 14}mm;top:64.6mm;font-size:7.5pt">—— AI 研究员 · 猫头鹰</div>')
    parts.append(f'<div class="a srcline" style="left:{M}mm;right:{M}mm;top:74.6mm">只给思考方法，不给涨跌判断</div>')
    parts.append(_foot())
    return Card(key=f"tip-{sc['id']}", w=W, h=H, html=trim("".join(parts), W, H), label=f"锦囊 · {sc['season_cn']}{sc.get('door', 'A')}")


def evidence_back(m: Model, sc: dict, kind: str) -> Card:
    k = EVIDENCE_KIND[kind]
    col, icon, cn, en = k["color"], k["icon"], k["cn"], k["en"]
    cap = "扫码 · 在手机上读信" if kind == "tip" else "扫码 · 私下看证据"
    fg = on(col)
    qid = sc["qr"][kind]
    ray = C["paper_light"] if fg != C["ink"] else C["ink"]
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{col}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm">{icons.sun_rays(W + 6, H + 6, (W + 6) / 2, 22, 22, ray, 0.09)}</div>']
    a = art.icon(icon)
    if a:
        parts.append(f'<div class="a" style="left:{(W - 25) / 2}mm;top:6.5mm;width:25mm;height:25mm;border-radius:50%;overflow:hidden;background:{C["paper"]};'
                     f'box-shadow:0 0 0 1.2mm {C["paper_light"]}"><img src="{a["uri"]}" style="width:100%;height:100%"></div>')
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:35mm;font-size:21pt;color:{fg}">{cn}</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:44.2mm;font-size:7pt;letter-spacing:.24em;color:{fg};opacity:.92">{en}</div>')
    parts.append(f'<div class="a center b7" style="left:0;right:0;top:48.6mm;font-size:7.5pt;color:{fg}">{esc(sc["season_cn"])} · 门 {esc(sc.get("door", "A"))} · 花 1 研究点看</div>')
    qw, qh = qrsvg.block_size(QS, 2.0, cap)
    parts.append(qrsvg.block(qid, (W - qw) / 2, 83.0 - qh, QS, 2.0, cap, where=f"{cn}牌背面 {sc['id']}"))
    return Card(key=f"ev-{sc['id']}-{kind}-b", w=W, h=H, html=trim("".join(parts), W, H), qr=[qid], label=f"{cn} · {sc['season_cn']}{sc.get('door', 'A')} · 背面")


# ======================================================================= 快进牌

def _num(v):
    return f'{"+" if v > 0 else ("−" if v < 0 else "±")}{abs(v)}'


def _result_box(card, left, top, width, narrow=False):
    ps = card.get("per_share", 0)
    pct = card.get("pct")
    col = charts.dir_color(ps) if ps else C["ink"]
    arrow = charts.arrow(ps) if ps else ""
    pct_s = f"这一段 {'+' if pct and pct > 0 else ''}{charts._fmt(pct)}%" if pct is not None else ""
    drop = (f'<span class="chip" style="background:{C["mustard"]};color:{C["ink"]};height:4.2mm;font-size:7pt;padding:0 1.4mm">本段算“跌了”</span>' if card.get("dropped")
            else f'<span class="chip line" style="color:{C["ink_2"]};height:4.2mm;font-size:7pt;padding:0 1.4mm">本段不算“跌了”</span>')
    big = (f'<div class="col" style="line-height:1.1"><span style="font-size:7pt;color:{C["ink_2"]}">每份仓位</span>'
           f'<span class="num" style="font-size:15pt;color:{col};white-space:nowrap">{arrow}{_num(ps)}<span style="font-size:7.5pt;font-family:\'Noto Sans SC\';font-weight:700"> 资金</span></span></div>')
    h = 14.2 if narrow else 10.4
    if narrow:
        inner = f'<div class="col" style="gap:0.8mm;width:100%">{big}<div class="row" style="gap:1.2mm">{drop}<span style="font-size:7pt;color:{C["ink_2"]}">{esc(pct_s)}</span></div></div>'
    else:
        inner = f'{big}<div class="sp"></div><div class="col" style="align-items:flex-end;gap:0.8mm">{drop}<span style="font-size:7pt;color:{C["ink_2"]}">{esc(pct_s)}</span></div>'
    return (f'<div class="a row" style="left:{left}mm;width:{width}mm;top:{top}mm;height:{h}mm;background:{C["paper_light"]};border-radius:1mm;padding:0 2mm;gap:1.6mm">{inner}</div>'), h


def _rule_bar(m, sc, idx, top):
    acts, missing = rulesig.ff_actions(m, sc, idx)
    n_rules = len(content.deck_list(m.D, "rules"))
    if missing:
        content.NOTES.append(f"快进牌“规则信号”栏：{sc['id']} 缺 {len(missing)} 张规则牌的评估（{', '.join(missing)}），rules_eval.json 补算后需重出")
    if len(missing) >= n_rules:
        content.NOTES.append(f"快进牌 {sc['id']}-{idx + 1}：rules_eval.json 里这一场一张规则牌都没评估，“规则信号”栏先不印")
        return "", 0.0
    else:
        texts = [(n, a.replace("止损卖光", "卖光")) for n, a in acts] + [("", "其余规则 → 不动" if acts else "所有规则牌 → 不动")]
    items = "".join(f'<span style="white-space:nowrap">{f"<b>{esc(n)}</b> → " if n else ""}{esc(a)}</span>' for n, a in texts)
    chars = 4 + sum(len(n) + len(a) + 3 for n, a in texts)
    lines = max(1, math.ceil(chars * 7 * PT * 1.0 / (W - 2 * M - 3.2)))
    hb = 1.8 + lines * 7 * PT * 1.36
    html = (f'<div class="a fit" data-min="7" data-what="规则信号" style="left:{M}mm;right:{M}mm;top:{top - hb:.2f}mm;height:{hb:.2f}mm;border:0.5pt dashed {C["ink"]};border-radius:0.8mm;'
            f'padding:0.5mm 1.4mm;font-size:7pt;line-height:1.36;display:flex;flex-wrap:wrap;column-gap:2mm;align-content:center">'
            f'<span class="b7" style="white-space:nowrap">规则信号</span>{items}</div>')
    return html, hb


def _vlen(s):
    """估算显示宽度（以汉字为 1，数字、拉丁字母和空格算半个）。"""
    return sum(0.55 if (c.isascii() and c not in "“”") else 1.0 for c in s)


def _pcts(s):
    return [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", s)]


def _ff_lines(card, known, sig):
    """去掉和逐日小格、结算框重复的句子（只含这些百分比、没有别的数字）。"""
    out, dropped = [], []
    for l in card.get("lines", []):
        if sig and "信号灯" in l:
            dropped.append(l)
            continue
        ps = _pcts(l)
        rest = re.sub(r"\d+(?:\.\d+)?\s*%|\d+\s*月\s*\d+\s*日|\d+/\d+", "", l)
        if ps and not re.search(r"\d", rest) and all(any(abs(p - k) <= 0.06 for k in known) for p in ps):
            dropped.append(l)
            continue
        out.append(l)
    return out, dropped


def ff_front(m: Model, sc: dict, idx: int, card: dict, n_cards: int) -> Card:
    ff = sc["fast_forward"]
    col = DECK["ff"]["color"]
    fg = on(col)
    word = "熔断" if ff.get("mechanic") == "circuit_breaker" else "快进"
    left = f'{_icon_disc("hourglass", 7.6)}<span class="disp" style="font-size:15pt">{word}</span>'
    if n_cards > 1:
        left += f'<span class="chip" style="background:{C["sun"]};color:{C["ink"]};height:4.2mm;font-size:7pt;padding:0 1.4mm">第 {idx + 1}/{n_cards} 张</span>'
    parts = [_band(col, left, _scene_tag(sc, fg))]
    title = re.sub(r"^(快进|熔断)\s*·\s*", "", card.get("title", ff.get("title", "")))
    parts.append(f'<div class="a disp fit" data-min="10" data-what="快进标题" style="left:{M}mm;right:{M}mm;top:13.0mm;height:6.2mm;font-size:13pt;white-space:nowrap">{esc(title)}</div>')

    # 逐日小格
    days = card.get("days")
    if not days and ff.get("grid") and idx == 0:
        days = ff["grid"][:5]
    dd = []
    for d in days or []:
        md = d["date"][5:].replace("-", "/")
        if "open_pct" in d:
            dd.append({"pct": d["open_pct"], "label": f"{md} 开盘"})
        dd.append({"pct": d.get("close_pct", d.get("pct")), "label": md + (" 收盘" if ("open_pct" in d or "close_pct" in d) else "")})
    dd = dd[:5]
    sig = card.get("signal")
    us = card.get("us_pct")
    far = card.get("far")
    known = [abs(x["pct"]) for x in dd if x.get("pct") is not None]
    if card.get("pct") is not None:
        known.append(abs(card["pct"]))
    if far and far.get("pct") is not None:
        known.append(abs(far["pct"]))
    lines, dropped = _ff_lines(card, known, sig)
    if dropped:
        content.NOTES.append(f"快进牌 {sc['id']}-{idx + 1}：和逐日小格/结算框重复的 {len(dropped)} 句没有印（{'；'.join(x[:14] + '…' for x in dropped)}）")
    show_us = us is not None and not any(f"{abs(us):.1f}" in l for l in lines)

    # ---- 自下而上：规则信号栏、（二维码）、之后做什么、结算框、附加行
    bar, hb = _rule_bar(m, sc, idx, FOOT_Y - 0.6)
    parts.append(bar)
    bottom = FOOT_Y - 0.6 - hb - 0.9
    then = card.get("then", "")
    qr_id = ff.get("qr") if (ff.get("qr") and idx == 0) else None
    fs = 7.8
    if qr_id:
        qcap = "扫码 · 15 秒熔断"
        qw, qh = qrsvg.block_size(QS, 2.0, qcap)
        lw = W - 2 * M - qw - 1.0
        cpl = max(1, int(lw / (7.4 * PT)))
        th = math.ceil(len(then) / cpl) * 7.4 * PT * 1.34 + 0.3
        blk = max(qh, 14.2 + 0.8 + th)
        parts.append(qrsvg.block(qr_id, W - M - qw + 0.4, bottom - qh, QS, 2.0, qcap, where=f"熔断快进牌 {sc['id']}"))
        box, bh = _result_box(card, M, bottom - blk, lw, narrow=True)
        parts.append(box)
        parts.append(f'<div class="a fit" data-min="7" data-what="快进之后" style="left:{M}mm;width:{lw}mm;top:{bottom - blk + bh + 0.8:.2f}mm;height:{blk - bh - 0.8:.2f}mm;font-size:7.4pt;line-height:1.34;font-weight:700">{esc(then)}</div>')
        box_top = bottom - blk
    else:
        cpl = max(1, int((W - 2 * M) / (fs * PT)))
        th = math.ceil(len(then) / cpl) * fs * PT * 1.36 + 0.3
        parts.append(f'<div class="a fit" data-min="7" data-what="快进之后" style="left:{M}mm;right:{M}mm;top:{bottom - th:.2f}mm;height:{th:.2f}mm;font-size:{fs}pt;line-height:1.36;font-weight:700">{esc(then)}</div>')
        box_top = bottom - th - 0.9 - 10.4
        box, bh = _result_box(card, M, box_top, W - 2 * M)
        parts.append(box)
    top_limit = box_top - 0.9
    extra = []
    if show_us:
        extra.append((5.2, f'<div class="row" style="gap:1.4mm;font-size:7.6pt;height:5.2mm"><span>标普 500 当天</span>'
                           f'<span class="num" style="font-size:12pt;color:{charts.dir_color(us)}">{charts.arrow(us)}{charts._fmt(abs(us))}%</span></div>'))
    if sig:
        off = bool(sig.get("red"))
        rays = "" if off else "".join(
            f'<line x1="{2.6 + 2.0 * math.cos(a):.2f}" y1="{2.6 + 2.0 * math.sin(a):.2f}" x2="{2.6 + 2.55 * math.cos(a):.2f}" y2="{2.6 + 2.55 * math.sin(a):.2f}" stroke="{C["ink"]}" stroke-width="0.3"/>'
            for a in [i * math.pi / 4 for i in range(8)])
        lamp = (f'<svg width="5.2mm" height="5.2mm" viewBox="0 0 5.2 5.2" style="flex:none">{rays}'
                f'<circle cx="2.6" cy="2.6" r="1.55" fill="{C["ink"] if off else C["paper_light"]}" stroke="{C["ink"]}" stroke-width="0.35"/></svg>')
        state = "灭了 · 规则说离开" if off else "还亮着 · 规则说留下"
        extra.append((8.4, f'<div class="row" style="gap:1.4mm;height:8.4mm;padding:0 1.6mm;border:0.5pt solid {C["ink"]};border-radius:0.8mm;font-size:7pt;line-height:1.3">'
                           f'{lamp}<div class="col"><b>5/20 信号灯{esc(state)}</b><span style="color:{C["ink_2"]}">5 日均价 {charts._fmt(sig.get("ma5"))} {"＜" if off else "＞"} 20 日均价 {charts._fmt(sig.get("ma20"))}</span></div></div>'))
    if far:
        fps = far.get("per_share", 0)
        extra.append((5.4, f'<div class="row" style="gap:1.2mm;height:5.4mm;font-size:7.6pt;white-space:nowrap"><span>改买远月的人：每份</span>'
                           f'<span class="num" style="font-size:12pt;color:{charts.dir_color(fps)}">{charts.arrow(fps)}{_num(fps)}</span>'
                           f'<span style="color:{C["ink_2"]}">这一段 {charts._fmt(far.get("pct"))}%</span></div>'))
    for hh, html in reversed(extra):
        top_limit -= hh
        parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{top_limit:.2f}mm">{html}</div>')
        top_limit -= 0.8

    # ---- 自上而下：假期快讯、逐日小格、正文
    y = 20.4
    ticker = ff.get("holiday_ticker") if idx == 0 else None
    if ticker:
        tk = "".join(f'<div>{esc(t)}</div>' for t in ticker)
        cpl = (W - 2 * M - 3.2) / (7 * PT)
        thh = 2.0 + sum(math.ceil(_vlen(t) / cpl) for t in ticker) * 7 * PT * 1.32
        parts.append(f'<div class="a fit" data-min="7" data-what="假期快讯" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{thh:.1f}mm;background:{C["ink"]};color:{C["sun"]};'
                     f'border-radius:0.8mm;padding:1mm 1.6mm;font-size:7pt;line-height:1.32">{tk}</div>')
        y += thh + 1.0
    if dd:
        sh = 12.0 if len(lines) <= 1 else 9.0
        parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{sh}mm">{charts.day_strip(dd, W - 2 * M, sh)}</div>')
        y += sh + 1.0
    if lines:
        lis = "".join(f"<li>{esc(t)}</li>" for t in lines)
        parts.append(f'<ul class="a dots fit lines" data-min="7" data-what="快进正文" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{top_limit - y:.1f}mm;font-size:8pt;line-height:1.38">{lis}</ul>')
    parts.append(_foot())
    return Card(key=f"ff-{sc['id']}-{idx + 1}", w=W, h=H, html=trim("".join(parts), W, H), qr=[qr_id] if qr_id else [],
                label=f"{word} · {sc['season_cn']}{sc.get('door', 'A')}" + (f" · {idx + 1}/{n_cards}" if n_cards > 1 else ""))


# ======================================================================= 牌背（每副一个设计）

def _back_base(deck, art_size=34.0, art_top=12.0):
    d = DECK[deck]
    col = d["color"]
    fg = on(col)
    ray = C["paper_light"] if fg != C["ink"] else C["ink"]
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm;background:{col}"></div>',
             f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:{H + 6}mm">{icons.sun_rays(W + 6, H + 6, (W + 6) / 2, art_top + 3 + art_size / 2, 22, ray, 0.08)}</div>']
    a = art.tile_art(d["tile"]) if d.get("tile") else art.icon(d["icon"])
    if a:
        parts.append(f'<div class="a" style="left:{(W - art_size) / 2}mm;top:{art_top}mm;width:{art_size}mm;height:{art_size}mm;border-radius:50%;overflow:hidden;background:{C["paper"]};'
                     f'box-shadow:0 0 0 1.4mm {C["paper_light"]}"><img src="{a["uri"]}" style="width:100%;height:100%"></div>')
    return parts, fg


def deck_back(deck: str, extra_html: str = "", key=None, sub=None) -> Card:
    d = DECK[deck]
    parts, fg = _back_base(deck)
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:51mm;font-size:22pt;color:{fg}">{esc(d["cn"])}</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:60.6mm;font-size:7pt;letter-spacing:.28em;color:{fg};opacity:.92">{d["en"]}</div>')
    parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:65mm;font-size:7.5pt;font-weight:700;color:{fg}">{esc(sub or d["line"])}</div>')
    parts.append(extra_html)
    parts.append(f'<div class="a center" style="left:0;right:0;top:79.6mm;font-size:7pt;color:{fg};opacity:.9">《交易物种起源》</div>')
    return Card(key=key or f"back-{deck}", w=W, h=H, html=trim("".join(parts), W, H), label=f"{d['cn']} · 牌背")


def qr_back(deck, qid, cap, extra_html="", key=None, sub=None, where="") -> Card:
    """副牌牌背 + 每张自己的二维码（码是无意义短码，不泄露牌面）。"""
    d = DECK[deck]
    parts, fg = _back_base(deck, art_size=24.0, art_top=5.0)
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:31.6mm;font-size:19pt;color:{fg}">{esc(d["cn"])}</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:39.6mm;font-size:7pt;letter-spacing:.28em;color:{fg};opacity:.92">{d["en"]}</div>')
    if not extra_html:
        parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:44.6mm;font-size:7.5pt;font-weight:700;color:{fg}">{esc(sub or d["line"])}</div>')
    else:
        parts.append(f'<div class="a center" style="left:{M}mm;right:{M}mm;top:52.9mm;font-size:7.5pt;font-weight:700;color:{fg}">{esc(sub or d["line"])}</div>')
        parts.append(extra_html)
    qr = []
    if qid and qrsvg.exists(qid):
        qw, qh = qrsvg.block_size(QS, 2.0, cap)
        parts.append(qrsvg.block(qid, (W - qw) / 2, 83.0 - qh, QS, 2.0, cap, where=where))
        qr = [qid]
    return Card(key=key or f"back-{deck}", w=W, h=H, html=trim("".join(parts), W, H), qr=qr, label=f"{d['cn']} · 牌背")


def ff_back(sc) -> Card:
    tag = (f'<div class="a center" style="left:0;right:0;top:70.2mm"><span class="chip" style="background:{C["paper_light"]};color:{C["ink"]};height:4.8mm;font-size:7.5pt">'
           f'{icons.season_disc(sc["season"], 3.6)}&nbsp;{esc(sc["season_cn"])} · 门 {esc(sc.get("door", "A"))}</span></div>')
    return deck_back("ff", tag, key=f"ff-{sc['id']}-b")


# ======================================================================= 机会 / 补测

def _ab_options(opts, top, size=8.0, h=10.4):
    out, y = [], top
    for o in opts:
        out.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{h}mm;background:{C["paper_light"]};border-radius:1mm;padding:0 1.8mm;gap:1.8mm">'
                   f'<span class="kb">{esc(o["key"])}</span><span class="b7 fit" data-min="7" data-what="选项" style="font-size:{size}pt;line-height:1.28;max-height:{h - 0.4}mm;flex:1">{esc(o["text"])}</span></div>')
        y += h + 1.3
    return "".join(out), y


def _species_name(s):
    return SPECIES_CN.get(s, "你主张的那种" if s == "other" else (s or ""))


def _seal(s, size):
    if s in SPECIES_COLOR:
        return icons.seal(s, size)
    return icons.seal("x", size, char="任", color=C["ink_3"])


def _fit_sentences(text, cap):
    """按句子截到 cap 个字以内（至少保留第一句）。"""
    parts = re.split(r"(?<=[。；！？])", text or "")
    out = ""
    for p in parts:
        if out and len(out + p) > cap:
            break
        out += p
    if out.endswith("；") and out != text:
        out = out[:-1] + "。"
    return out


def _flip_answer(rows_html, note, top, rows_h, title="选完再倒过来看", bot=79.4, where=""):
    """整条倒印的答案区：倒过来看时标题在上。"""
    height = bot - top
    width = W - 2 * M
    nh = height - 2.6 - 3.4 - rows_h - 1.2
    cpl = (width - 3.6) / (7.2 * PT)
    nl = max(1, int((nh - 0.6) // (7.2 * PT * 1.3)))
    cap = int(nl * cpl * 0.96)
    short = _fit_sentences(note, cap) if nh >= 3.5 else ""
    if short != (note or ""):
        content.NOTES.append(f"倒印答案说明太长，只印了前半（{where}）：省略“{(note or '')[len(short):][:20]}…”")
    return (f'<div class="a flip" style="left:{M}mm;top:{top:.2f}mm;width:{width}mm;height:{height:.2f}mm;background:{C["paper_deep"]};border-radius:1mm;padding:1.3mm 1.8mm;overflow:hidden">'
            f'<div class="row" style="height:3.4mm"><span class="b7" style="font-size:7pt;color:{C["ink_2"]}">{esc(title)}</span></div>'
            f'<div class="row" style="gap:3mm;flex-wrap:wrap">{rows_html}</div>'
            f'<div class="fit" data-min="7" data-what="倒印说明" style="font-size:7.2pt;line-height:1.3;color:{C["ink_2"]};height:{nl * 7.2 * PT * 1.3 + 0.8:.2f}mm;margin-top:0.6mm">{esc(short)}</div></div>')


def _map_rows(opts):
    """答案 → 物种图标；放得下就并排，否则上下排。返回 (html, 高度)。"""
    html = "".join(
        f'<div class="row" style="gap:1.2mm;height:5.2mm;font-size:7.8pt"><span class="kb" style="width:4.2mm;height:4.2mm;font-size:8.5pt">{esc(o["key"])}</span>'
        f'{icons.arrow_right(3.4, 2.4)}{_seal(o.get("species"), 4.8)}<b class="nowrap">{esc(_species_name(o.get("species")))}</b></div>' for o in opts)
    wid = sum(12.4 + 7.8 * PT * len(_species_name(o.get("species"))) for o in opts) + 3.0 * (len(opts) - 1)
    return html, (5.2 if wid <= W - 2 * M - 3.6 else 5.2 * len(opts))


def chance_front(m: Model, c: dict) -> Card:
    col = DECK["chance"]["color"]
    fg = on(col)
    left = f'{_icon_disc("dice", 7.6)}<span class="disp" style="font-size:15pt">机会</span>'
    right = f'<span class="chip line" style="color:{fg};height:4.4mm;font-size:7pt;padding:0 1.6mm">{esc(c.get("dimension", ""))}</span>'
    parts = [_band(col, left, right)]
    parts.append(f'<div class="a disp fit" data-min="10" data-what="机会标题" style="left:{M}mm;right:{M}mm;top:13.4mm;height:6.4mm;font-size:13pt;white-space:nowrap">{esc(c.get("title", ""))}</div>')
    parts.append(f'<div class="a fit" data-min="7.5" data-what="机会问题" style="left:{M}mm;right:{M}mm;top:20.6mm;height:8.6mm;font-size:8.6pt;line-height:1.35">{esc(c.get("prompt", ""))}</div>')
    opts_html, y = _ab_options(c.get("options", []), 30.0)
    parts.append(opts_html)
    mh, mrh = _map_rows(c.get("options", []))
    parts.append(_flip_answer(mh, c.get("back_note", ""), y + 1.2, mrh, where=c["id"]))
    parts.append(_foot("先选 A 或 B，再倒过来看图标"))
    return Card(key=c["id"], w=W, h=H, html=trim("".join(parts), W, H), label=f"机会 · {c['id'][-2:]}")


def retest_front(m: Model, c: dict) -> Card:
    col = DECK["retest"]["color"]
    pair = c.get("pair", [])
    seals = "".join(_seal(s, 5.6) for s in pair)
    left = f'{_icon_disc("magnifier", 7.6)}<span class="disp" style="font-size:15pt">补测</span>'
    parts = [_band(col, left, f'<span class="row" style="gap:0.8mm">{seals}</span>')]
    pn = " / ".join(_species_name(s) if s != "other" else "任意" for s in pair)
    parts.append(f'<div class="a b7" style="left:{M}mm;right:{M}mm;top:13.2mm;font-size:7.5pt;color:{C["ink_2"]}">分辨：{esc(pn)}</div>')
    parts.append(f'<div class="a fit disp" data-min="9" data-what="补测问题" style="left:{M}mm;right:{M}mm;top:17.6mm;height:11.6mm;font-size:11.5pt;line-height:1.25">{esc(c.get("prompt", ""))}</div>')
    opts_html, y = _ab_options(c.get("options", []), 30.0, 7.8)
    parts.append(opts_html)
    note = c.get("other_means") or c.get("why", "")
    mh, mrh = _map_rows(c.get("options", []))
    parts.append(_flip_answer(mh, note, y + 1.2, mrh, "答完再倒过来看", where=c["id"]))
    parts.append(_foot("按答案拿币，不能自己挑"))
    return Card(key=c["id"], w=W, h=H, html=trim("".join(parts), W, H), label=f"补测 · {c['id'][-2:]}")


def retest_back(c: dict) -> Card:
    pair = c.get("pair", [])
    seals = "".join(_seal(s, 8.4) for s in pair)
    names = " / ".join(_species_name(s) if s != "other" else "任意一种" for s in pair)
    extra = f'<div class="a row" style="left:0;right:0;top:43.6mm;justify-content:center;gap:2.4mm">{seals}</div>'
    return qr_back("retest", c.get("qr"), "扫码 · 看完整解释", extra, key=f"{c['id']}-b", sub=f"平局：{names}", where=f"补测牌背面 {c['id']}")


# ======================================================================= 规则牌

def rule_front(m: Model, r: dict) -> Card:
    col = DECK["rules"]["color"]
    left = f'{_icon_disc("research", 7.6, tile=True)}<span class="disp" style="font-size:15pt">规则牌</span>'
    parts = [_band(col, left, icons.seal(r.get("species", "fox"), 6.4))]
    real = bool(r.get("is_real_template"))
    name = r.get("name", "")
    if r.get("spoils"):
        name = re.sub(r"^(贵州)?茅台\s*", "", name)
    parts.append(f'<div class="a disp fit" data-min="9.5" data-what="规则名" style="left:{M}mm;right:{M}mm;top:13.4mm;height:12.4mm;font-size:13.5pt;line-height:1.2">{esc(name)}</div>')
    parts.append(f'<div class="a fit" data-min="7.5" data-what="规则正文" style="left:{M}mm;right:{M}mm;top:26.6mm;height:19.4mm;font-size:9pt;line-height:1.42;'
                 f'background:{C["paper_light"]};border-left:1.2mm solid {col};padding:1.6mm 2mm;border-radius:0 1mm 1mm 0">{esc(r.get("text", ""))}</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="规则用法" style="left:{M}mm;right:{M}mm;top:47.0mm;height:7.0mm;font-size:7.4pt;line-height:1.34;color:{C["ink_2"]}">'
                 f'理由写“规则牌：{esc(rulesig.short(r))}”，决策和快进都必须照规则做。</div>')
    qid = r.get("qr")
    if real and qid and qrsvg.exists(qid):
        cap = "扫码 · Qube 模板"
        qw, qh = qrsvg.block_size(QS, 2.0, cap)
        parts.append(qrsvg.block(qid, W - M - qw + 0.4, 79.6 - qh, QS, 2.0, cap, where=f"规则牌 {r['id']}"))
        parts.append(f'<div class="a" style="left:{M}mm;top:{79.6 - qh + 1}mm;width:{W - 2 * M - qw - 1.5}mm">'
                     f'<span class="chip ink" style="font-size:7pt;height:4.4mm">真实 Qube 模板</span>'
                     f'<div style="font-size:7pt;line-height:1.32;margin-top:1.2mm;color:{C["ink_2"]}">扫码看这条规则在更长历史里的回测</div></div>')
    else:
        parts.append(f'<div class="a" style="left:{M}mm;top:64.6mm;right:{M}mm"><span class="chip line" style="font-size:7pt;height:4.4mm;color:{C["ink_2"]}">散户常说的土规则</span>'
                     f'<div style="font-size:7pt;line-height:1.32;margin-top:1.2mm;color:{C["ink_2"]}">它灵不灵？终局后可以在 Qube 里自己写出来回测。</div></div>')
    parts.append(_foot())
    return Card(key=r["id"], w=W, h=H, html=trim("".join(parts), W, H), qr=[qid] if (real and qid) else [], label=f"规则 · {r.get('name', '')}")


def rule_back(m: Model, r: dict) -> Card:
    col = DECK["rules"]["color"]
    fg = on(col)
    parts, _ = _back_base("rules", art_size=19.0, art_top=4.0)
    parts.append(f'<div class="a center disp" style="left:0;right:0;top:25.4mm;font-size:16pt;color:{fg}">规则牌</div>')
    parts.append(f'<div class="a center caps" style="left:0;right:0;top:32.4mm;font-size:7pt;letter-spacing:.28em;color:{fg};opacity:.92">RULE CARD</div>')
    rows = []
    for sc in m.scenes:
        d = rulesig.decision(m, r, sc["id"])
        p1 = '<span style="font-size:7pt;color:#77745A;margin-left:0.6mm">P1</span>' if sc.get("tier") == "P1" else ""
        if d is None and sc.get("tier") == "P1":
            content.NOTES.append(f"规则牌背面：P1 场景 {sc['id']} 在 rules_eval.json 里还没有评估，这一行先不印（补算后重出规则牌背面）")
            continue
        if d is None:
            cell = f'<span style="color:{C["ink_3"]}">待补</span>'
            content.NOTES.append(f"规则牌背面：{r['id']} 在 {sc['id']} 没有评估（rules_eval.json），印了“待补”")
        elif d["na"]:
            cell = f'<span class="b7" style="color:{C["ink_3"]}">不适用</span>'
        else:
            opt = f'<span style="margin-left:auto" class="row">选&nbsp;<span class="kb" style="width:4.4mm;height:4.4mm;font-size:9pt">{esc(d["opt"])}</span></span>' if d["opt"] else ""
            cell = f'<span class="b7 nowrap">{esc(d["signal"])}</span>{opt}'
        rows.append(f'<div class="row" style="height:5.3mm;gap:1.4mm;border-bottom:0.5pt dotted {C["ink_3"]};font-size:7.5pt">'
                    f'<span class="row nowrap" style="width:15mm;flex:none">{icons.season_disc(sc["season"], 4.2)}<b style="margin-left:0.8mm">{esc(sc["season_cn"])} {esc(sc.get("door", "A"))}</b>{p1}</span>'
                    f'<span class="row" style="flex:1">{cell}</span></div>')
    parts.append(f'<div class="a" style="left:{M - 0.8}mm;right:{M - 0.8}mm;top:38.2mm;height:{H - 38.2 - 3.6}mm;background:{C["paper_light"]};border-radius:1.2mm;padding:1.6mm 2.2mm">'
                 f'<div class="row" style="font-size:7.5pt;height:4.6mm"><b>决策日信号</b><div class="sp"></div><span class="nowrap fit" data-min="7" style="color:{C["ink_2"]};max-width:30mm">{esc(rulesig.short(r))}</span></div>'
                 f'<div style="border-top:0.6pt solid {C["ink"]};margin-top:0.4mm">{"".join(rows)}</div>'
                 f'<div style="font-size:7pt;color:{C["ink_2"]};margin-top:1mm;line-height:1.3">决策日看这里，快进看快进牌的“规则信号”栏；“不适用”的那一场不能用。</div></div>')
    return Card(key=f"{r['id']}-b", w=W, h=H, html=trim("".join(parts), W, H), label=f"规则 · {r.get('name', '')} · 背面")


# ======================================================================= 数据港口

def dataport_front(m: Model, dp: dict) -> Card:
    col = DECK["dataport"]["color"]
    left = f'{_icon_disc("dataport", 7.6, tile=True)}<span class="disp" style="font-size:14pt">数据港口</span>'
    parts = [_band(col, left, f'<span class="disp nowrap" style="font-size:11pt">{esc(dp.get("title", ""))}</span>')]
    code = dp.get("code", [])
    if isinstance(code, str):
        code = code.split("\n")
    code_html = "".join(f'<div style="white-space:pre-wrap;word-break:break-all;padding-left:2ch;text-indent:-2ch">{esc(l) or "&nbsp;"}</div>' for l in code)
    cpl = (W - 2 * M - 2.8) / (7 * PT * 0.6 * 0.97)
    rows = sum(max(1, math.ceil((len(l) + (2 if len(l) > cpl else 0)) / cpl)) for l in code)
    ch = 1.8 + rows * 7 * PT * 1.2
    parts.append(f'<div class="a fit" data-min="6.2" data-what="代码" style="left:{M}mm;right:{M}mm;top:13.4mm;height:{ch:.1f}mm;background:{C["ink"]};color:{C["paper_light"]};'
                 f'border-radius:0.8mm;padding:0.9mm 1.4mm;font-family:\'TS Mono\',\'Noto Sans SC\';font-size:7pt;line-height:1.2;letter-spacing:-0.03em">{code_html}</div>')
    y = 13.4 + ch + 1.0
    qh_ = math.ceil(_vlen(dp.get("question", "")) / ((W - 2 * M) / (7.8 * PT))) * 7.8 * PT * 1.3 + 0.2
    parts.append(f'<div class="a b7 fit" data-min="7" data-what="港口问题" style="left:{M}mm;right:{M}mm;top:{y}mm;height:{qh_:.2f}mm;font-size:7.8pt;line-height:1.3">{esc(dp.get("question", ""))}</div>')
    y += qh_ + 0.5
    for o in dp.get("options", []):
        parts.append(f'<div class="a row" style="left:{M}mm;right:{M}mm;top:{y}mm;height:4.4mm;gap:1.4mm;font-size:7.4pt">'
                     f'<span class="kb o" style="width:3.8mm;height:3.8mm;font-size:7.5pt">{esc(o["key"])}</span>'
                     f'<span class="fit nowrap" data-min="7" data-what="港口选项" style="flex:1">{esc(o["text"])}</span></div>')
        y += 4.6
    rows = (f'<div class="row" style="gap:1.2mm;font-size:7.8pt;height:5.2mm"><b>答案</b><span class="kb" style="width:4.4mm;height:4.4mm;font-size:9pt">{esc(dp.get("answer", ""))}</span>'
            f'<span style="font-size:7.2pt">答对：1 研究点 + 1 枚海狸币</span></div>')
    parts.append(_flip_answer(rows, dp.get("explain", ""), y + 0.4, 5.2, "答完再倒过来看", where=dp["id"]))
    parts.append(_foot("代码是 panda_data 里真实的函数，回家可以亲手跑"))
    return Card(key=dp["id"], w=W, h=H, html=trim("".join(parts), W, H), label=f"数据港口 · {dp['id'][-2:]}")


# ======================================================================= 任务牌

TASK_ICON = {"chart": "chart", "explore": "ledger", "regime": "compass", "verify": "magnifier", "hypo": "egg", "risk": "hourglass"}


def task_front(m: Model, t: dict) -> Card:
    col = DECK["tasks"]["color"]
    lv = "进阶" if t.get("level") == "adv" else "入门"
    left = f'{_icon_disc(TASK_ICON.get(t.get("type"), "kite"), 7.6)}<span class="disp" style="font-size:15pt">任务</span>'
    right = f'<span class="chip {"ink" if lv == "进阶" else "line"}" style="height:4.4mm;font-size:7pt;padding:0 1.6mm">{lv}</span>'
    parts = [_band(col, left, right)]
    name = t.get("name", "").split(" · ")[0]
    parts.append(f'<div class="a disp fit" data-min="10" data-what="任务名" style="left:{M}mm;right:{M}mm;top:13.2mm;height:6.4mm;font-size:13.5pt;white-space:nowrap">{esc(name)}</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="给谁" style="left:{M}mm;right:{M}mm;top:20.4mm;height:10mm;font-size:7.3pt;line-height:1.36;color:{C["ink_2"]}">{esc(t.get("for_whom", ""))}</div>')
    parts.append(f'<div class="a fit" data-min="7.2" data-what="任务正文" style="left:{M}mm;right:{M}mm;top:31.2mm;height:21.4mm;font-size:8.4pt;line-height:1.42;font-weight:700;'
                 f'background:{C["paper_light"]};border-left:1.2mm solid {C["ochre"]};padding:1.4mm 1.8mm;border-radius:0 1mm 1mm 0">{esc(t.get("card_text", ""))}</div>')
    qid = t.get("qr")
    cap = "扫码 · 开始任务"
    qw, qh = qrsvg.block_size(QS, 2.0, cap)
    cpl = (W - 2 * M - qw - 1.2 - 2.0) / (7 * PT)
    budget = (79.6 - 54.2 - 3.6) / (7 * PT * 1.3)
    res, used = [], 0
    for r in [r for r in t.get("resources", []) if r.get("name")]:
        n = math.ceil(_vlen(r["name"]) / cpl)
        if used + n > budget:
            content.NOTES.append(f"任务牌 {t['id']}：资源“{r['name'][:16]}…”放不下，只在扫码页里")
            continue
        res.append(r)
        used += n
    rl = "".join(f'<div style="display:flex;gap:0.8mm;margin-bottom:0.3mm"><span style="flex:none">·</span><span>{esc(r["name"])}</span></div>' for r in res)
    parts.append(f'<div class="a fit" data-min="7" data-what="任务资源" style="left:{M}mm;width:{W - 2 * M - qw - 1.2}mm;top:{54.2}mm;height:{79.6 - 54.2:.1f}mm;font-size:7pt;line-height:1.3">'
                 f'<div class="b7" style="margin-bottom:0.6mm">用得上的</div>{rl}</div>')
    if qid and qrsvg.exists(qid):
        parts.append(qrsvg.block(qid, W - M - qw + 0.4, 79.6 - qh, QS, 2.0, cap, where=f"任务牌 {t['id']}"))
    parts.append(_foot())
    return Card(key=t["id"], w=W, h=H, html=trim("".join(parts), W, H), qr=[qid] if qid else [], label=f"任务 · {t.get('name', '')}")


# ======================================================================= AI 物种

REASON_CN = {"price": "量价", "data": "数据", "news": "消息", "follow": "跟别人", "gut": "直觉", "lost": "看不懂", "rule": "规则牌"}
FF_CN = {"hold": "持有", "sell": "卖出", "add": "加仓", "enter": "进场", "stay": "留下", "leave": "离开"}
SECOND_CN = {"add": "补仓", "stop": "止损", "ignore": "不看了"}


def ai_front(m: Model, a: dict) -> Card:
    sid = a.get("species")
    col = SPECIES_COLOR.get(sid, C["ink_3"])
    parts = [_band(DECK["ai"]["color"], f'{_icon_disc("waterwheel", 7.6)}<span class="disp" style="font-size:15pt">AI 物种</span>',
                   f'<span class="chip" style="background:{C["paper_light"]};color:{C["ink"]};height:4.4mm;font-size:7pt;padding:0 1.6mm">{esc(a.get("difficulty", ""))}</span>')]
    md = art.medal(sid)
    if md:
        parts.append(f'<div class="a" style="left:{M}mm;top:14mm;width:22mm;height:22mm;border-radius:50%;overflow:hidden;border:1mm solid {col}"><img src="{md["uri"]}" style="width:100%;height:100%"></div>')
    parts.append(f'<div class="a disp" style="left:{M + 25}mm;top:15.4mm;font-size:17pt">AI · {esc(a.get("name", ""))}</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="AI 口吻" style="left:{M + 25}mm;right:{M}mm;top:24.2mm;height:12mm;font-size:7pt;line-height:1.32;color:{C["ink_2"]}">{esc(a.get("voice", ""))}</div>')
    parts.append(f'<div class="a fit disp" data-min="9" data-what="口头禅" style="left:{M}mm;right:{M}mm;top:39mm;height:13mm;font-size:12pt;line-height:1.25;'
                 f'background:{C["paper_light"]};border-radius:1mm;padding:1.6mm 2mm;display:flex;align-items:center">“{esc(a.get("catchphrase", ""))}”</div>')
    parts.append(f'<div class="a fit" data-min="7" data-what="AI 说明" style="left:{M}mm;right:{M}mm;top:54.4mm;height:17mm;font-size:7.6pt;line-height:1.4">{esc(a.get("card_text", ""))}</div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:73.4mm;font-size:7pt;color:{C["ink_2"]}">资金从 20 开始；不走棋、不拿研究点</div>')
    parts.append(_foot())
    return Card(key=a["id"], w=W, h=H, html=trim("".join(parts), W, H), label=f"AI · {a.get('name', '')} · 正面")


def ai_back(m: Model, a: dict) -> Card:
    sid = a.get("species")
    col = SPECIES_COLOR.get(sid, C["ink_3"])
    fg = on(col)
    parts = [f'<div class="a" style="left:-3mm;top:-3mm;width:{W + 6}mm;height:14mm;background:{col}"></div>',
             f'<div class="a row" style="left:{M}mm;right:{M}mm;top:0;height:11mm;color:{fg}"><span class="disp" style="font-size:13pt">AI · {esc(a.get("name", ""))}</span>'
             f'<div class="sp"></div><span class="b7" style="font-size:7pt">亮单时只看这一场那一行</span></div>',
             f'<div class="a mstripe" style="left:-3mm;top:11mm;width:{W + 6}mm;height:0.9mm"></div>']
    head = (f'<div class="row b7" style="font-size:7pt;color:{C["ink_2"]};height:4.4mm;border-bottom:0.6pt solid {C["ink"]}">'
            f'<span style="width:13.4mm">名场面</span><span style="width:7mm">选</span><span style="width:10.6mm">理由</span><span style="width:12.4mm">快进</span><span class="sp"></span><span>方法星</span></div>')
    rows = []
    for sc in m.scenes:
        x = a.get("scenes", {}).get(sc["id"])
        if not x:
            continue
        stars = a.get("method_stars", {}).get(sc["id"], 0)
        ffa = FF_CN.get(x.get("ff_action"), x.get("ff_action", ""))
        if x.get("second"):
            ffa += "·" + SECOND_CN.get(x["second"], "")
        p1 = '<span style="font-size:7pt;color:#77745A;margin-left:0.5mm">P1</span>' if sc.get("tier") == "P1" else ""
        rows.append(f'<div class="row" style="height:7.4mm;border-bottom:0.5pt dotted {C["ink_3"]};font-size:7.4pt">'
                    f'<span style="width:13.4mm" class="row nowrap">{icons.season_disc(sc["season"], 4.4)}<b style="margin-left:0.8mm">{esc(sc["season_cn"])}{esc(sc.get("door", "A"))}</b>{p1}</span>'
                    f'<span style="width:7mm"><span class="kb" style="width:4.6mm;height:4.6mm;font-size:9pt">{esc(x.get("option", ""))}</span></span>'
                    f'<span style="width:10.6mm">{esc(REASON_CN.get(x.get("reason"), ""))}</span><span style="width:12.4mm" class="nowrap">{esc(ffa)}</span><span class="sp"></span>'
                    f'<span class="row" style="gap:0.2mm">{"".join(icons.star(2.4) for _ in range(stars))}</span></div>')
    parts.append(f'<div class="a" style="left:{M}mm;right:{M}mm;top:13.6mm">{head}{"".join(rows)}</div>')
    parts.append(f'<div class="a fit" data-min="7" style="left:{M}mm;right:{M}mm;top:63.6mm;height:15.6mm;font-size:7pt;line-height:1.34;color:{C["ink_2"]}">'
                 f'按同样的收益表给它记账，方法星照这张表记。春 A 时 AI 先选；夏 A 卖出窗口只有 1 个名额；冬 A 的 AI 只在第一张熔断牌后调仓。</div>')
    parts.append(_foot())
    return Card(key=f"{a['id']}-b", w=W, h=H, html=trim("".join(parts), W, H), label=f"AI · {a.get('name', '')} · 背面")


# ======================================================================= 汇总

def scene_std_cards(m: Model, sc: dict):
    """一个名场面的标准卡（正、背成对）：量价、数据、消息、锦囊、快进×n。"""
    pairs = []
    for k in ("price", "data", "news"):
        if k in sc["evidence"]:
            pairs.append((evidence_front(m, sc, k), evidence_back(m, sc, k)))
    if "tip" in sc["evidence"]:
        pairs.append((tip_front(m, sc), evidence_back(m, sc, "tip")))
    cards = sc["fast_forward"].get("cards", [])
    for i, c in enumerate(cards):
        pairs.append((ff_front(m, sc, i, c, len(cards)), ff_back(sc)))
    return pairs


def deck_pairs(m: Model):
    D = m.D
    return {
        "chance": [(chance_front(m, c), qr_back("chance", c.get("qr"), "扫码 · 看完整解释", key=f"{c['id']}-b", where=f"机会牌背面 {c['id']}")) for c in content.deck_list(D, "chance")],
        "retest": [(retest_front(m, c), retest_back(c)) for c in content.deck_list(D, "retest")],
        "rules": [(rule_front(m, r), rule_back(m, r)) for r in content.deck_list(D, "rules")],
        "dataport": [(dataport_front(m, d), qr_back("dataport", d.get("qr"), "扫码 · 改参数再跑", key=f"{d['id']}-b", where=f"数据港口牌背面 {d['id']}")) for d in content.deck_list(D, "dataport")],
        "tasks": [(task_front(m, t), deck_back("tasks")) for t in content.deck_list(D, "tasks")],
        "ai": [(ai_front(m, a), ai_back(m, a)) for a in content.deck_list(D, "ai_species")],
    }


def dev_cards(m: Model, only=None):
    only = only or ["s924", "s2015"]
    cards = []
    for sc in m.scenes:
        if sc["id"] in only:
            for f, b in scene_std_cards(m, sc):
                cards += [f, b]
    if any(k in only for k in ("chance", "retest", "rules", "dataport", "tasks", "ai", "decks")):
        for k, v in deck_pairs(m).items():
            if k in only or "decks" in only:
                for f, b in (v if k in only else v[:2]):
                    cards += [f, b]
    return cards
