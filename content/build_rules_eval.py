"""把每张规则牌放回每个名场面：T 日收盘看信号，T+1 开盘成交，之后每天收盘再看一次，直到第 20 个交易日。

收益口径和游戏一致：持有 2 份（有信号）或空仓；1 资金 ≈ 一份仓位涨跌 5%，在场景的结算点上四舍五入。
输出 content/rules_eval.json，H5 终局的“假设检验”当场用。
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
SERIES = ROOT / "data" / "series"

SCENES = {
    "s924": ("sse", "2024-09-30", 0, [2, 20], "上证指数"),
    "s2015": ("sse", "2015-06-12", 2, [5, 20], "上证指数"),
    "smt": ("moutai_qfq", "2021-02-10", 2, [5, 20], "贵州茅台（前复权）"),
    "scb": ("ndx", "2020-03-09", 2, [3, 5, 7, 20], "纳斯达克100"),
    "squant": ("cn2000", "2024-02-02", 2, [5, 20], "国证2000"),
}


def per_share(p):
    return int(round(p / 5.0)) if abs(p) >= 2.5 else 0


def pct(a, b):
    return (b / a - 1) * 100


def ma(rows, i, n):
    xs = [r["close"] for r in rows[i - n + 1:i + 1]]
    return sum(xs) / len(xs)


def load(name):
    return json.loads((SERIES / f"{name}.json").read_text(encoding="utf-8"))["rows"]


def source_of(name):
    return json.loads((SERIES / f"{name}.json").read_text(encoding="utf-8"))["source"]


def signal_fn(rule):
    if rule == "rule-ma520":
        return lambda rows, i: ma(rows, i, 5) > ma(rows, i, 20)
    if rule == "rule-ma52060":
        return lambda rows, i: ma(rows, i, 5) > ma(rows, i, 20) > ma(rows, i, 60)
    if rule == "rule-mom20":
        return lambda rows, i: rows[i]["close"] > rows[i - 20]["close"]
    return None


def run_signal(rows, t, bounds, sig, n_on=2):
    """每天收盘看信号，下一天开盘调整；在结算点上按每份 5% 四舍五入。"""
    end = t + bounds[-1]
    marks = sorted(set(t + b for b in bounds))
    pos = n_on if sig(rows, t) else 0
    trades = [{"date": rows[t + 1]["date"], "action": f"开盘{'持有 ' + str(n_on) + ' 份' if pos else '空仓'}"}]
    entry = rows[t + 1]["open"]
    total = 0
    for i in range(t + 1, end + 1):
        if i in marks and pos:
            total += pos * per_share(pct(entry, rows[i]["close"]))
            entry = rows[i]["close"]
        if i < end:
            want = n_on if sig(rows, i) else 0
            if want != pos:
                nxt = rows[i + 1]["open"]
                if pos:
                    total += pos * per_share(pct(entry, nxt))
                trades.append({"date": rows[i + 1]["date"], "action": "开盘卖出" if pos else f"开盘买入 {n_on} 份"})
                pos = want
                entry = nxt
    return total, trades


def run_stop(rows, t, bounds, start, stop=-10.0):
    end = t + bounds[-1]
    marks = sorted(set(t + b for b in bounds))
    pos = start or 2
    entry = base = rows[t + 1]["open"]
    total = 0
    trades = [{"date": rows[t + 1]["date"], "action": f"开盘持有 {pos} 份"}]
    for i in range(t + 1, end + 1):
        if not pos:
            break
        if pct(base, rows[i]["close"]) <= stop:
            total += pos * per_share(pct(entry, rows[i]["close"]))
            trades.append({"date": rows[i]["date"], "action": f"跌破 {abs(stop):.0f}%，收盘止损"})
            pos = 0
            break
        if i in marks:
            total += pos * per_share(pct(entry, rows[i]["close"]))
            entry = rows[i]["close"]
    return total, trades


def run_dip(rows, t, bounds, start, dd=-15.0):
    end = t + bounds[-1]
    marks = sorted(set(t + b for b in bounds))
    lots = [[start or 2, rows[t + 1]["open"]]]
    trades = [{"date": rows[t + 1]["date"], "action": f"开盘持有 {start or 2} 份"}]
    total = 0
    added = False
    for i in range(t + 1, end + 1):
        hi = max(r["close"] for r in rows[max(0, i - 60):i + 1])
        if not added and pct(hi, rows[i]["close"]) <= dd and i < end:
            lots.append([1, rows[i]["close"]])
            added = True
            trades.append({"date": rows[i]["date"], "action": f"离高点 {pct(hi, rows[i]['close']):.0f}%，收盘加 1 份"})
        if i in marks:
            for lot in lots:
                total += lot[0] * per_share(pct(lot[1], rows[i]["close"]))
                lot[1] = rows[i]["close"]
    return total, trades


def run_volume(rows, t, bounds, start, mult=2.0, win=20):
    """成交量超过过去 20 天均量的 2 倍：下一天开盘追进 1 份，只追一次。"""
    end = t + bounds[-1]
    marks = sorted(set(t + b for b in bounds))
    lots = [[start, rows[t + 1]["open"]]] if start else []
    trades = [{"date": rows[t + 1]["date"], "action": f"开盘持有 {start} 份" if start else "开盘空仓"}]
    total = 0
    added = False
    for i in range(t, end + 1):
        if i > t and i in marks:
            for lot in lots:
                total += lot[0] * per_share(pct(lot[1], rows[i]["close"]))
                lot[1] = rows[i]["close"]
        if not added and i < end:
            avg = sum(r["volume"] for r in rows[i - win:i]) / win
            if avg and rows[i]["volume"] > mult * avg:
                lots.append([1, rows[i + 1]["open"]])
                added = True
                trades.append({"date": rows[i + 1]["date"], "action": f"前一天放量 {rows[i]['volume'] / avg:.1f} 倍，开盘追进 1 份"})
    return total, trades


def valuation_pct(series, date, field="pe_ttm"):
    rows = [r for r in load(series) if r["date"] <= date and r.get(field)]
    now = rows[-1][field]
    return 100.0 * sum(r[field] <= now for r in rows) / len(rows), now, rows[0]["date"]


def run_hold(rows, t, bounds, n):
    marks = sorted(set(t + b for b in bounds))
    entry = rows[t + 1]["open"]
    total = 0
    for i in marks:
        total += n * per_share(pct(entry, rows[i]["close"]))
        entry = rows[i]["close"]
    return total, [{"date": rows[t + 1]["date"], "action": f"开盘持有 {n} 份，拿到最后"}]


def soil_eval(rule):
    """冬 B 原油宝：快进只结算不操作，规则只决定决策日选哪个选项，收益直接用本场收益表。"""
    sc = next(s for s in json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))["scenes"] if s["id"] == "soil")
    pay = {r["key"]: r["total"] for r in sc["reveal"]["payoff_rows"]}
    rows = load("wti_cont")
    t = next(i for i, r in enumerate(rows) if r["date"] == sc["t_date"])
    d1 = rows[t + 1]["date"]

    def done(opt, action, note):
        return {"applicable": True, "instrument": "原油宝（挂钩 WTI 近月合约）", "total": pay[opt], "trades": [{"date": d1, "action": action}], "note": note}

    sig = signal_fn(rule)
    if sig:
        on = sig(rows, t)
        return done("A" if on else "D", "开盘持有 2 份" if on else "开盘空仓", "T 日信号：" + ("亮（持有）" if on else "灭（空仓）"))
    if rule == "rule-stop10":
        return done("A", "开盘持有 2 份", "止损规则不决定买不买：这一场按买入 2 份算；结算价一天之内跌成负数，止损来不及")
    if rule == "rule-dip":
        hi = max(r["close"] for r in rows[max(0, t - 60):t + 1])
        return done("A", f"开盘持有 2 份（离高点 {pct(hi, rows[t]['close']):.0f}%，规则说抄底）", "这一场快进只结算不操作，加不了第 3 份")
    if rule == "rule-cap1":
        return done("B", "开盘持有 1 份（远月合约）", "最多 1 份：这一场只有远月合约是 1 份")
    if rule == "rule-wait3":
        return done("D", "等三天：观望", "这一场开局 0 份，先等三天就是观望")
    if rule == "rule-vol2x":
        return {"applicable": False, "note": "这一场的行情没有成交量数据，这条规则不适用"}
    return {"applicable": False, "note": "期货挂钩产品，没有市盈率、PB 和 ROE，这条规则不适用"}


def main():
    out = {"note": "规则放回名场面：T 日收盘看信号、T+1 开盘成交，到第 20 个交易日；持有 2 份或空仓，口径和游戏一致。", "rules": {}}
    rules = ["rule-ma520", "rule-ma52060", "rule-mom20", "rule-stop10", "rule-dip", "rule-cap1", "rule-vol2x", "rule-val80", "rule-lowpb-roe", "rule-wait3"]
    for rule in rules:
        res = {}
        for sid, (series, T, start, bounds, inst) in SCENES.items():
            rows = load(series)
            t = next(i for i, r in enumerate(rows) if r["date"] == T)
            sig = signal_fn(rule)
            # 规则牌背面把“持有”换成本场选项：春 A 开局 0 份，“持有”对应 B 小仓位试水，只有 1 份
            unit = start or 1
            note = ""
            if sig:
                at = sig(rows, t)
                total, trades = run_signal(rows, t, bounds, sig, n_on=unit)
                note = "T 日信号：" + ("亮（持有）" if at else "灭（空仓）")
            elif rule == "rule-stop10":
                total, trades = run_stop(rows, t, bounds, unit)
                note = "止损规则不决定买不买：这一场按小仓位试水 1 份算" if sid == "s924" else ""
            elif rule == "rule-dip":
                total, trades = run_dip(rows, t, bounds, unit)
            elif rule == "rule-cap1":
                total, trades = run_hold(rows, t, bounds, 1)
                note = "最多 1 份：规则不决定买不买，这一场按买入 1 份算" if sid == "s924" else "开局超过 1 份的，马上减到 1 份，拿到最后"
            elif rule == "rule-vol2x":
                total, trades = run_volume(rows, t, bounds, start)
                if len(trades) == 1:
                    note = "这 20 个交易日里没有一天放量到 2 倍，规则没有出手"
            elif rule == "rule-val80":
                if sid != "smt":
                    res[sid] = {"applicable": False, "note": "这一场没有预备逐日估值分位，只在秋季“抱团”那一场算"}
                    continue
                q, pe, since = valuation_pct("moutai_val", T)
                n = 1 if q > 80 else 2
                total, trades = run_hold(rows, t, bounds, n)
                trades = [{"date": rows[t + 1]["date"], "action": f"市盈率 {pe:.0f} 倍，处在 {since[:4]} 年以来 {q:.0f}% 分位：{'减半到 1 份' if n == 1 else '保持 2 份'}，拿到最后"}]
                note = f"估值数据：{source_of('moutai_val')}"
            elif rule == "rule-lowpb-roe":
                if sid == "smt":
                    v = next(r for r in load("moutai_val") if r["date"] == T)
                    total, trades = 0, [{"date": rows[t + 1]["date"], "action": f"市盈率 {v['pe_ttm']:.0f} 倍、市净率 {v['pb']:.0f} 倍：不符合“低 PB”，不持有"}]
                    note = f"估值数据：{source_of('moutai_val')}"
                else:
                    res[sid] = {"applicable": False, "note": "指数或基金，没有单家公司的 PB 和 ROE，这条规则不适用"}
                    continue
            elif rule == "rule-wait3":
                hold_after = rows[t + 3]["close"] > rows[t]["close"]
                n = unit if hold_after else 0
                entry = rows[t + 4]["open"]
                total = 0
                marks = sorted(set(t + b for b in bounds if b > 3))
                if n:
                    for i in marks:
                        total += n * per_share(pct(entry, rows[i]["close"]))
                        entry = rows[i]["close"]
                first = sorted(set(t + b for b in bounds))[0]
                pre = start * per_share(pct(rows[t + 1]["open"], rows[t + 3]["close"])) if start else 0
                total += pre
                trades = [{"date": rows[t + 4]["date"], "action": f"等 3 天后{f'站在决策日上方：持有 {n} 份' if n else '还在决策日下方：空仓'}"}]
                note = "前 3 天保持原来的仓位"
            res[sid] = {"applicable": True, "instrument": inst, "total": total, "trades": trades[:6], "note": note}
        res["soil"] = soil_eval(rule)
        out["rules"][rule] = res
    p = HERE / "rules_eval.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r, v in out["rules"].items():
        print(r, {k: (x.get("total") if x.get("applicable") else "—") for k, x in v.items()})


if __name__ == "__main__":
    main()
