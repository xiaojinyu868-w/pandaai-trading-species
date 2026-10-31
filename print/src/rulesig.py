"""规则牌在各名场面的信号（content/rules_eval.json）：决策日信号印在规则牌背面，快进时的动作印在快进牌底部。"""

from __future__ import annotations

import datetime as dt
import re

from . import content

SHORT = {
    "rule-ma520": "5/20 双均线",
    "rule-ma52060": "多均线 5/20/60",
    "rule-mom20": "20 日动量",
    "rule-lowpb-roe": "低 PB + 高 ROE",
    "rule-stop10": "跌 10% 止损",
    "rule-dip": "跌多了就抄底",
    "rule-wait3": "先等三天",
    "rule-cap1": "不超过一半",
    "rule-vol2x": "放量就追",
    "rule-val80": "估值太高减半",
}

_EVAL = None


def evals() -> dict:
    global _EVAL
    if _EVAL is None:
        try:
            _EVAL = content.load_json("rules_eval.json").get("rules", {})
        except Exception:
            _EVAL = {}
    return _EVAL


def short(rule: dict) -> str:
    return SHORT.get(rule["id"], rule.get("name", ""))


def _d(s):
    return dt.date.fromisoformat(s)


def _add_weekdays(s: str, n: int) -> str:
    d = _d(s)
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d.isoformat()


def ff_windows(sc: dict) -> list[tuple[str, str]]:
    """每张快进牌覆盖的交易日区间（含首尾）。"""
    ff = sc.get("fast_forward", {})
    cards = ff.get("cards", [])
    t = sc.get("t_date", "")
    dates = sc.get("reveal", {}).get("chart", {}).get("dates", [])
    after = [d for d in dates if d > t]
    start = after[0] if after else t
    year = start[:4]
    out = []
    for i, c in enumerate(cards):
        days = c.get("days")
        if days:
            s, e = days[0]["date"], days[-1]["date"]
        elif ff.get("grid") and i == 0:
            g = ff["grid"][:5]
            s, e = g[0]["date"], g[-1]["date"]
        else:
            m = re.search(r"(\d+)\s*月\s*(\d+)\s*日", c.get("title", ""))
            s = start
            e = f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else _add_weekdays(start, 4)
        out.append((s, e))
        start = _add_weekdays(e, 1)
    return out


def _is_initial(tr: dict, t1: str) -> bool:
    a = tr.get("action", "")
    return tr.get("date") <= t1 and (a.startswith("开盘持有") or a.startswith("开盘空仓") or "不持有" in a)


def _act(a: str) -> str:
    if "止损" in a:
        return "止损卖光"
    if "加 1 份" in a:
        return "加 1 份"
    m = re.search(r"买入\s*(\d)\s*份", a)
    if m:
        return f"买入 {m.group(1)} 份"
    if "减" in a:
        return "减半"
    if "卖出" in a or "空仓" in a:
        return "卖光"
    return a


def ff_actions(m, sc: dict, idx: int):
    """某张快进牌上，各规则牌这一段要做的动作。返回 (动作列表, 未评估的规则)。"""
    wins = ff_windows(sc)
    if idx >= len(wins):
        return [], []
    s, e = wins[idx]
    t1 = wins[0][0]
    acts, missing = [], []
    for r in content.deck_list(m.D, "rules"):
        ev = evals().get(r["id"], {}).get(sc["id"])
        if ev is None:
            missing.append(r["id"])
            continue
        if not ev.get("applicable", True):
            continue
        hits = [tr for tr in ev.get("trades", []) if not _is_initial(tr, t1) and s <= tr["date"] <= e]
        if hits:
            acts.append((short(r), "，".join(dict.fromkeys(_act(h["action"]) for h in hits))))
    return acts, missing


DIR_TEXT = {"in": "持有 2 份", "out": "空仓", "wait": "先等着", "add": "加仓", "reduce": "减一半", "cap1": "不超过一半"}


def decision(m, rule: dict, sid: str):
    """规则牌背面某一格：决策日信号和对应的选项。None 表示还没有评估数据。"""
    ev = evals().get(rule["id"], {}).get(sid)
    if ev is None:
        return None
    if not ev.get("applicable", True):
        return {"signal": "不适用", "opt": None, "na": True}
    om = m.D.get("meta", {}).get("rule_option_map", {}).get(sid, {})
    note = ev.get("note", "")
    t0 = (ev.get("trades") or [{}])[0].get("action", "")
    if "T 日信号：亮" in note:
        d, sig = "in", "亮 · 持有"
    elif "T 日信号：灭" in note:
        d, sig = "out", "灭 · 空仓"
    elif rule.get("logic", {}).get("type") == "wait" or t0.startswith("等"):
        d, sig = "wait", "先等三天"
    elif "减半" in t0:
        d, sig = "reduce", "估值高 · 减半"
    elif "保持 2 份" in t0:
        d, sig = "in", "估值不高 · 持有"
    elif "不持有" in t0 or t0.startswith("开盘空仓"):
        d, sig = "out", "不持有"
    elif rule.get("logic", {}).get("type") == "position_cap":
        d, sig = "cap1", "最多一半"
    elif "持有" in t0:
        n = re.search(r"持有\s*(\d)\s*份", t0)
        d, sig = "in", f"持有 {n.group(1) if n else 2} 份"
    else:
        d, sig = None, note[:10]
    opt = om.get(d) if d else None
    if d == "wait" and not opt:
        sig = "先等三天 · 保持开局仓位"
    return {"signal": sig, "opt": opt, "na": False}
