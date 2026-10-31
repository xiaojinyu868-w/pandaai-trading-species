"""六个名场面的全部内容：文字手写，数字全部从 data/series 的真实行情算出来。

输出 content/scenes.json（schema 见印刷与 H5 的约定）。重跑：
  python3.11 data/fetch_market.py && python3.11 content/build_scenes.py

收益口径：决策在 T 日收盘后，T+1 开盘成交；第一段到快进牌（多数是 T+5 收盘），第二段到 T+20 收盘。
1 资金 ≈ 一份仓位涨跌 5%，四舍五入。个股用前复权价算收益，牌面显示不复权的真实股价。
“公开报道”的数字不在行情数据里，单独标注。
"""

import datetime as dt
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES = ROOT / "data" / "series"
QR = {r["id"]: r for r in json.loads((ROOT / "content" / "qr.json").read_text(encoding="utf-8"))}


def load(name):
    s = json.loads((SERIES / f"{name}.json").read_text(encoding="utf-8"))
    return s["rows"], s["source"]


def series(name):
    """只有 Panda Data 才取得到的序列（估值、全市场逐只统计、期货各月合约）；公开口径下没有，返回 None。"""
    f = SERIES / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


FQ_CN = {"qfq": "前复权", "post": "后复权", "none": "不复权"}


def at(rows, date):
    """date 当天或之后的第一个交易日的下标。"""
    for i, r in enumerate(rows):
        if r["date"] >= date:
            return i
    raise KeyError(date)


def pct(a, b):
    return (b / a - 1) * 100


def f1(x):
    return f"{x:.1f}"


def signed(x, digits=1):
    return f"{x:+.{digits}f}%"


def per_share(p):
    """一份仓位这一段涨跌多少资金（1 资金 ≈ 5%）。"""
    return int(round(p / 5.0)) if abs(p) >= 2.5 else (0 if abs(p) < 2.5 else 0)


def downsample(values, n):
    if len(values) <= n:
        return values
    step = (len(values) - 1) / (n - 1)
    return [values[round(i * step)] for i in range(n)]


def rebased(rows, end_i, n_days, n_points=72):
    win = rows[max(0, end_i - n_days + 1):end_i + 1]
    base = win[0]["close"]
    vals = [round(r["close"] / base * 100, 1) for r in win]
    return {"values": downsample(vals, n_points), "t_index": n_points - 1 if len(vals) > n_points else len(vals) - 1,
            "label": "起点 = 100，名字和日期已隐藏"}


def dated(rows, a, b, marks, n_points=110, key="close"):
    ia, ib = at(rows, a), at(rows, b)
    win = rows[ia:ib + 1]
    idx = list(range(len(win)))
    keep = downsample(idx, n_points)
    out_m = []
    for d, label in marks:
        j = at(rows, d) - ia
        k = min(range(len(keep)), key=lambda t: abs(keep[t] - j))
        out_m.append({"i": k, "date": rows[ia + j]["date"], "label": label})
    return {"dates": [win[i]["date"] for i in keep], "values": [round(win[i][key], 2) for i in keep], "marks": out_m}


def volume_ratio(rows, i, recent=1, base=250):
    r = statistics.mean(x["volume"] for x in rows[i - recent + 1:i + 1])
    b = statistics.mean(x["volume"] for x in rows[i - base - recent + 1:i - recent + 1])
    return r / b


def payoff_rows(options, seg1, seg2, enter_key=None):
    """每个选项一直拿着不动时的两段收益（每份仓位 × 份数）。enter_key 的选项快进后进 1 份。"""
    rows = []
    for o in options:
        s1 = o["shares"] * seg1
        sh2 = 1 if o["key"] == enter_key else o["shares"]
        s2 = sh2 * seg2
        rows.append({"key": o["key"], "label": o["label"], "shares": o["shares"], "seg1": s1, "seg2": s2, "total": s1 + s2})
    return rows


def qr_ids(sid):
    return {k: f"{sid}-{k}" for k in ("blind", "price", "data", "news", "tip", "reveal")}


def path(rows, t, ends, before=5, after=25, instrument=""):
    """决策日前后的逐日价格，H5 按玩家每一步的操作精确记账。ends 是每张快进牌结束那天的下标（相对 rows）。"""
    a, b = max(0, t - before), min(len(rows) - 1, t + after)
    return {"instrument": instrument, "t": t - a, "ends": [e - a for e in ends],
            "days": [{k: (round(r[k], 3) if k != "date" else r[k]) for k in ("date", "open", "high", "low", "close")}
                     for r in rows[a:b + 1]]}


def dip(rows, start_price, i0, i1, threshold=-5.0):
    """这一段里第一次比买入价跌超 threshold 的那天：计划“跌了就走/跌了就加”在那天收盘执行。"""
    for i in range(i0, i1 + 1):
        p = pct(start_price, rows[i]["close"])
        if p <= threshold:
            return {"date": rows[i]["date"], "pct_at_trigger": round(p, 2), "per_share_at_trigger": per_share(p),
                    "rest_pct": round(pct(rows[i]["close"], rows[i1]["close"]), 2),
                    "rest_per_share": per_share(pct(rows[i]["close"], rows[i1]["close"]))}
    return None


def ev(kind, title, lines, stat=None, chart=None, risk=False, source=""):
    label = {"price": "量价", "data": "数据", "news": "消息", "tip": "锦囊"}[kind]
    species = {"price": "cheetah", "data": "elephant", "news": "meerkat", "tip": None}[kind]
    return {"kind": kind, "label": label, "title": title, "lines": lines, "stat": stat, "chart": chart,
            "risk": risk, "species": species, "source": source}


TIP_SOURCE = "AI 研究员猫头鹰：只给思考方法，不给涨跌判断"
NEWS_SOURCE = "当时的公开报道，去掉了名字和日期"
PUBLIC_REPORT = "公开报道"


def exit_res(name, url, why, kind, login=False, prompt=None):
    d = {"name": name, "url": url, "why": why, "kind": kind, "is_real": True}
    if login:
        d["note"] = "登录 PandaAI 后可用"
    if prompt:
        d["prompt"] = prompt
    return d


QUBE = "https://www.pandaaiquant.com/agent_quant/"
QS_SKILL = "https://www.quantskills.ai/skills/"
QS_AGENT = "https://www.quantskills.ai/agents/"


# ───────────────────────────── 春 · 924 ─────────────────────────────
def scene_924():
    sse, src = load("sse")
    T = "2024-09-30"
    t = at(sse, T)
    t1 = t + 1                      # 2024-10-08 节后首日
    t2 = t + 2                      # 2024-10-09
    t20 = t + 20
    d_t = pct(sse[t - 1]["close"], sse[t]["close"])
    five = pct(sse[t - 5]["close"], sse[t]["close"])
    since = next(r["date"][:4] for r in reversed(sse[:t]) if pct(sse[sse.index(r) - 1]["close"], r["close"]) >= d_t)
    vr = volume_ratio(sse, t)
    ten = [r["close"] for r in sse[at(sse, "2014-09-30"):t + 1]]
    above = sum(c > sse[t]["close"] for c in ten) / len(ten) * 100
    i913 = at(sse, "2024-09-13")
    low913 = sse[i913]["close"]
    lows_since = min(r["close"] for r in sse[at(sse, "2019-01-02"):i913])
    gap = pct(sse[t]["close"], sse[t1]["open"])
    d1 = pct(sse[t]["close"], sse[t1]["close"])
    d2 = pct(sse[t1]["close"], sse[t2]["close"])
    seg1 = pct(sse[t1]["open"], sse[t2]["close"])
    seg2 = pct(sse[t2]["close"], sse[t20]["close"])
    ps1, ps2 = per_share(seg1), per_share(seg2)
    sv, mb = series("sse_val"), series("market_breadth")
    if sv:
        v = {r["date"]: r for r in sv["rows"]}
        val_line = f"市盈率（TTM）从两周前的 {v['2024-09-13']['pe_ttm']:.1f} 倍升到 {v[T]['pe_ttm']:.1f} 倍：涨得快，不等于位置高。"
    else:
        val_line = "涨得快，不等于位置高：先看位置，再看速度。"
    amt = next((r["amount"] for r in mb["rows"] if r["date"] == sse[t1]["date"]), None) if mb else None
    options = [
        {"key": "A", "label": "节后开盘追入", "shares": 2},
        {"key": "B", "label": "小仓位试水", "shares": 1},
        {"key": "C", "label": "等回调再说", "shares": 0, "hint": "快进时可以进 1 份"},
        {"key": "D", "label": "不参与", "shares": 0},
    ]
    vol_bars = [round(r["volume"] / statistics.mean(x["volume"] for x in sse[t - 270:t - 20]), 2) for r in sse[t - 39:t + 1]]
    return {
        "id": "s924", "season": "spring", "season_cn": "春", "season_name": "入场", "door": "A", "tier": "P0",
        "path": path(sse, t, [t2, t20], instrument="上证指数"),
        "title": "924 · 国庆全民开户", "year": "2024", "market": "A股",
        "door_hint": "A 股 · 一个长假前夜",
        "decision_mode": "sequential",
        "t_date": T, "t_text": "2024 年 9 月 30 日收盘后，国庆长假前最后一个交易日",
        "blind": {
            "headline": "长假前夜，人人都在排队",
            "lines": [
                f"五个交易日，指数涨了两成多，成交量放大到平时的 {vr:.0f} 倍多。",
                "一组利好政策接连发布，券商营业部门口排起了队。",
                "明天起放七天长假，假期里交易所不开门。",
            ],
            "position": "你现在空仓。",
            "question": "节后第一天，你怎么做？",
            "chart": rebased(sse, t, 120),
        },
        "options": options,
        "evidence": {
            "price": ev("price", f"单日大涨 {f1(d_t)}%", [
                f"最后一天单日涨 {f1(d_t)}%，是 {since} 年以来最大的单日涨幅。",
                f"五个交易日累计上涨 {f1(five)}%。",
                f"当天成交量是过去一年日均的 {vr:.1f} 倍。",
            ], stat={"value": f"{vr:.1f} 倍", "caption": "成交量 ÷ 过去一年日均"},
                chart={"type": "bars", "values": vol_bars, "labels": [], "unit": "成交量 ÷ 一年日均（最近 40 天）"},
                source=f"行情：{src}"),
            "data": ev("data", "现在站在哪个位置", [
                f"过去十年里，有 {above:.0f}% 的交易日收盘比今天高。",
                f"两周前它还在 {low913:.0f} 点，接近 2019 年以来的最低（{lows_since:.0f} 点）。",
                val_line,
            ], stat={"value": f"{above:.0f}%", "caption": "过去十年收盘高于今天的天数占比"},
                chart={"type": "line", "values": downsample(ten, 80), "labels": ["十年前", "今天"], "unit": "指数点位，十年收盘"},
                source=f"行情：{src}" + (f"；估值：{sv['source']}" if sv else "")),
            "news": ev("news", "假期前的快讯", [
                "周二：三部门联合发布会，降准、降息，并新设两项支持股市的工具。",
                "周四：高层会议提出“努力提振资本市场”。",
                "朋友圈：“十年一遇”“先上车再说”“开户要排队”。",
            ], source=NEWS_SOURCE),
            "tip": ev("tip", "猫头鹰的信", [
                "涨得越快，节后第一天的分歧就越大。",
                "排队之前先写一句：如果节后第一天就跌 5%，我会怎么做？",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "七天后开盘", "mechanic": "queue", "mechanic_name": "开户排队条",
            "board_rules": [
                "依次明选：选 A 或 B 的人把棋子放进开户排队条，后面的人看得见队有多长。",
                "委托单上记下：你选的时候队里已经有几个人。",
                "节后首日按开盘价成交，结算到第二天收盘；然后持有、卖出或加仓，选 C 的人这时可以进 1 份。",
            ],
            "holiday_ticker": [
                "假期第 1 天：香港市场继续大涨。",
                "假期第 3 天：“节后开盘会不会涨停”冲上热搜。",
                "假期第 5 天：券商通宵扩容开户系统。",
                "假期最后一天：所有人都在等明天的开盘铃。",
            ],
            "cards": [{
                "title": "快进 · 节后两天",
                "lines": [
                    f"节后第一天高开 {f1(gap)}%，随后回落，收盘涨 {f1(d1)}%。",
                    f"第二天下跌 {f1(abs(d2))}%。",
                    f"从节后开盘买入到第二天收盘：{signed(seg1)}。",
                ],
                "per_share": ps1, "pct": round(seg1, 2), "dropped": seg1 < 0,
                "dip": dip(sse, sse[t1]["open"], t1, t2),
                "then": "现在：持有、卖出还是加仓？选 C 的人可以进 1 份。",
                "days": [
                    {"date": sse[t1]["date"], "open_pct": round(gap, 2), "close_pct": round(d1, 2)},
                    {"date": sse[t2]["date"], "close_pct": round(d2, 2)},
                ],
            }],
        },
        "reveal": {
            "headline": "924 · 国庆全民开户",
            "date_line": "2024 年 9 月 24 日 → 10 月 9 日",
            "lines": [
                f"9 月 24 日起一组政策利好接连发布，上证指数五天涨了 {f1(five)}%。",
                (f"节后第一天高开 {f1(gap)}%，全天成交 {amt / 1e12:.2f} 万亿元；开盘约 20 分钟就破万亿，创历史纪录（公开报道）。" if amt else
                 f"节后第一天高开 {f1(gap)}%，开盘约 20 分钟两市成交额就破万亿，全天约 3.45 万亿元，创历史纪录（公开报道）。"),
                f"第二天大跌 {f1(abs(d2))}%，之后转入震荡：决策日后第 20 个交易日，上证收在 {sse[t20]['close']:.0f} 点。",
            ],
            "lesson": "排队进场的那一刻，最该想清楚的是：什么时候走。",
            "egg": "很多新股民就是这一周开的户。对他们来说，节后这两天是第一节市场课。",
            "chart": dated(sse, "2024-07-15", "2024-11-29",
                           [("2024-09-24", "利好发布"), (T, "决策日"), (sse[t1]["date"], "节后首日")]),
            "seg2": {"label": "第二天收盘 → 第 20 个交易日", "pct": round(seg2, 2), "per_share": ps2},
            "payoff_rows": payoff_rows(options, ps1, ps2),
            "source_note": (f"行情：{src}；估值：{sv['source'] if sv else '—'}；成交额：{mb['source']}；开盘 20 分钟破万亿、历史纪录为公开报道。" if amt else
                            f"行情：{src}；成交额 3.45 万亿元为公开报道。") + "口径：节后首日开盘成交，第二天收盘、第 20 个交易日收盘结算。",
        },
        "exits": [
            exit_res("Qube · 多均线趋势过滤 MA5/20/60", QUBE, "看 924 之后趋势信号什么时候出现、什么时候失效", "PandaAI 产品", login=True,
                     prompt="用 MA5/20/60 多均线趋势过滤回测上证指数 2024 年 9 月到 12 月，看信号什么时候出现、什么时候失效"),
            exit_res("均线交叉信号分析", QS_SKILL + "skill-ma-crossover-signal", "把“追涨”换成一条可以检验的均线规则", "QuantSkills 技能"),
            exit_res("A股财经新闻情感分析师", QS_SKILL + "skill-news-sentiment-analyst", "消息驱动的人：先核验，再判断情绪", "QuantSkills 技能"),
            exit_res("市场状态监控智能体", QS_AGENT + "agent-market-regime-monitor", "用同一套证据看今天的市场处在什么状态", "QuantSkills 智能体"),
        ],
        "qr": qr_ids("s924"),
    }


# ───────────────────────────── 夏 · 2015 ─────────────────────────────
def scene_2015():
    sse, src = load("sse")
    mg, msrc = load("margin")
    T = "2015-06-12"
    t = at(sse, T)
    t5, t20 = t + 5, t + 20
    year_gain = pct(sse[t - 250]["close"], sse[t]["close"])
    vr = statistics.mean(r["volume"] for r in sse[t - 19:t + 1]) / statistics.mean(r["volume"] for r in sse[t - 269:t - 249])
    big_down = sum(1 for i in range(t - 29, t + 1) if pct(sse[i - 1]["close"], sse[i]["close"]) <= -2)
    m_t1 = next(r for r in reversed(mg) if r["date"] < T)
    m_y0 = next(r for r in reversed(mg) if r["date"] <= "2014-06-11")
    m_peak = max(mg, key=lambda r: r["rzye"])
    seg1 = pct(sse[t + 1]["open"], sse[t5]["close"])
    seg2 = pct(sse[t5]["close"], sse[t20]["close"])
    ps1, ps2 = per_share(seg1), per_share(seg2)
    win = sse[t + 1:at(sse, "2015-07-10") + 1]
    low = min(win, key=lambda r: r["low"])
    dd = pct(sse[t]["high"], low["low"])
    after_max = max(r["high"] for r in sse[t + 1:])
    mb = series("market_breadth")
    breadth = {r["date"]: r for r in mb["rows"]} if mb else {}
    grid = [{"date": sse[i]["date"], "pct": round(pct(sse[i - 1]["close"], sse[i]["close"]), 2)} for i in range(t + 1, t20 + 1)]
    for g in grid:
        b = breadth.get(g["date"])
        if b:  # 线上版：三分之二以上的股票跌停或停牌，这一天卖不出去
            g.update(n=b["n"], limit_down=b["limit_down"], suspended=b["suspended"],
                     lock=(b["limit_down"] + b["suspended"]) * 3 >= b["n"] * 2)
            note = [f"{b['limit_down']} 只跌停" if b["limit_down"] >= 500 else "", f"{b['suspended']} 家停牌" if b["suspended"] >= 1000 else ""]
            if b["limit_down"] >= 900 or b["suspended"] >= 1000:
                g["note"] = "、".join(x for x in note if x)
    if not breadth:
        known = {"2015-06-26": "两千多只股票跌停", "2015-07-08": "一千多只股票跌停、一千多家公司停牌"}
        for g in grid:
            if g["date"] in known:
                g["note"] = known[g["date"]] + "（公开报道）"
    if breadth:
        k1000 = sum(1 for g in grid if g["date"] <= "2015-07-09" and g.get("limit_down", 0) >= 1000)
        top = max((breadth[g["date"]] for g in grid if g["date"] in breadth), key=lambda b: b["suspended"])
        halt_line = (f"{k1000} 个交易日收盘千股跌停；{int(top['date'][5:7])} 月 {int(top['date'][8:])} 日停牌的公司有 {top['suspended']} 家，"
                     f"约占 {top['suspended'] / top['n'] * 100:.0f}%，随后救市。")
    else:
        halt_line = "多次出现千股跌停；7 月初一度有一半左右的股票停牌（公开报道），随后救市。"
    options = [
        {"key": "A", "label": "再加杠杆", "shares": 3},
        {"key": "B", "label": "保持不动", "shares": 2},
        {"key": "C", "label": "还掉借款，降到无杠杆", "shares": 1},
        {"key": "D", "label": "全部卖出", "shares": 0},
    ]
    mchart = [r for r in mg if "2014-06-01" <= r["date"] < T]
    return {
        "id": "s2015", "season": "summer", "season_cn": "夏", "season_name": "狂热", "door": "A", "tier": "P0",
        "path": path(sse, t, [t5, t20], instrument="上证指数"),
        "title": "2015 · 杠杆牛与千股跌停", "year": "2015", "market": "A股",
        "door_hint": "A 股 · 一个人人都在借钱的夏天",
        "decision_mode": "simultaneous",
        "t_date": T, "t_text": "2015 年 6 月 12 日收盘后，当天盘中最高 5178 点",
        "blind": {
            "headline": "人人都在借钱买的夏天",
            "lines": [
                "指数一年多翻了一倍还多，成交量天天放大。",
                "菜市场里大家都在聊股票，身边有人借了钱，赚得比你多。",
                "评论说：这轮行情才刚开始。",
            ],
            "position": "你已经满仓，还借了一倍。",
            "question": "现在怎么办？",
            "chart": rebased(sse, t, 250),
        },
        "options": options,
        "evidence": {
            "price": ev("price", f"一年涨了 {year_gain:.0f}%", [
                f"过去 250 个交易日，指数上涨 {year_gain:.0f}%。",
                f"最近 20 天的日均成交量，是一年前同期的 {vr:.1f} 倍。",
                f"最近 30 个交易日里，有 {big_down} 天单日跌超 2%。",
            ], stat={"value": f"{vr:.1f} 倍", "caption": "成交量 ÷ 一年前同期"},
                chart={"type": "line", "values": downsample([r["close"] for r in sse[t - 249:t + 1]], 72), "labels": ["一年前", "今天"], "unit": "指数点位"},
                source=f"行情：{src}"),
            "data": ev("data", "借来的钱有多少", [
                f"截至前一个交易日，两市融资余额 {m_t1['rzye'] / 1e12:.2f} 万亿元。",
                f"一年前只有 {m_y0['rzye'] / 1e12:.2f} 万亿元，涨到了 {m_t1['rzye'] / m_y0['rzye']:.1f} 倍。",
                "融资余额：投资者借钱买股票、还没还上的钱。这还不算场外配资。",
            ], stat={"value": f"{m_t1['rzye'] / 1e12:.2f} 万亿", "caption": "融资余额（前一交易日口径）"},
                chart={"type": "line", "values": downsample([round(r["rzye"] / 1e12, 3) for r in mchart], 72), "labels": ["一年前", "昨天"], "unit": "万亿元"},
                risk=True, source=f"两融：{msrc}"),
            "news": ev("news", "这三条消息", [
                "一篇官方媒体评论：“4000 点才是 A 股牛市的开端。”",
                "今天收盘后：监管要求券商自查、清理场外配资。",
                "论坛热帖：“借钱的人赚得最多。”",
            ], source=NEWS_SOURCE),
            "tip": ev("tip", "猫头鹰的信", [
                "先算一笔账：借了一倍，指数跌 25%，你的本金还剩多少？",
                "再想一想：如果那时想卖，却卖不掉呢？",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "千股跌停", "mechanic": "sell_window", "mechanic_name": "卖出窗口与跌停锁",
            "board_rules": [
                "先按快进牌结算第一段。",
                "想卖的人同时伸手，把棋子放上卖出窗口：名额只有人数的一半（向下取整，至少 1 个），先放上的先卖。",
                "没卖掉的人放一枚跌停锁，下一段照样跟着跌。",
                "选 A 的人资金低于 5 时被强制平仓。",
            ],
            "online_note": ("线上版：当天三分之二以上的股票跌停或停牌，就记作卖不出去（家数来自 Panda Data 逐只统计，游戏化处理）。" if breadth else
                            "线上版：指数单日跌超 5% 记作“大面积跌停、卖不出去”（游戏化处理）。"),
            "grid": grid,
            "cards": [{
                "title": "快进 · 接下来的五个交易日",
                "lines": [
                    "下跌 2.0%、下跌 3.5%、上涨 1.7%、下跌 3.7%、下跌 6.4%。",
                    f"五个交易日合计 {signed(seg1)}。",
                    "想卖的人，同时伸手抢卖出窗口。",
                ],
                "per_share": ps1, "pct": round(seg1, 2), "dropped": seg1 < 0,
                "dip": dip(sse, sse[t + 1]["open"], t + 1, t5),
                "then": "卖出窗口打开：想卖的人同时伸手。",
            }],
        },
        "reveal": {
            "headline": "2015 · 杠杆牛与千股跌停",
            "date_line": "2015 年 6 月 12 日 → 7 月 9 日",
            "lines": [
                f"6 月 12 日盘中 5178 点见顶。不到一个月，7 月 9 日盘中最低到 {low['low']:.0f} 点，跌去 {abs(dd):.0f}%。",
                halt_line,
                f"融资余额在 6 月 18 日见顶，约 {m_peak['rzye'] / 1e12:.2f} 万亿元，之后快速下降。",
            ],
            "lesson": "借来的钱，会在你最需要时间的时候，逼你离场。",
            "egg": "5178 点之后，上证指数到 2024 年底都没有再回到这个高度。" if after_max < sse[t]["high"] else None,
            "chart": dated(sse, "2014-11-03", "2015-09-30",
                           [(T, "决策日"), ("2015-06-26", "千股跌停"), ("2015-07-09", "盘中最低")]),
            "seg2": {"label": "第 5 个交易日 → 第 20 个交易日", "pct": round(seg2, 2), "per_share": ps2},
            "payoff_rows": payoff_rows(options, ps1, ps2),
            "source_note": f"行情：{src}；两融：{msrc}；跌停、停牌家数" + (f"：{mb['source']}" if breadth else "为公开报道") + "。口径：T+1 开盘成交，T+5、T+20 收盘结算。",
        },
        "exits": [
            exit_res("市场状态监控智能体", QS_AGENT + "agent-market-regime-monitor", "用行情、宽度、波动和资金判断：趋势、震荡、退潮还是风险扩张", "QuantSkills 智能体"),
            exit_res("北向资金与两融期货全景监控", QS_SKILL + "skill-northbound-margin-monitor", "把融资余额这类“借来的钱”变成每天都看得见的信号", "QuantSkills 技能"),
            exit_res("拥挤度风险监控智能体", QS_AGENT + "agent-crowding-risk-monitor", "识别过热、踩踏与去杠杆风险", "QuantSkills 智能体"),
            exit_res("A股可交易性审计", QS_SKILL + "skill-a-share-tradability-auditor", "回测里也要算上“跌停卖不出去”", "QuantSkills 技能"),
        ],
        "qr": qr_ids("s2015"),
    }


# ───────────────────────────── 秋 · 茅台 ─────────────────────────────
def ma(rows, i, n):
    return statistics.mean(r["close"] for r in rows[i - n + 1:i + 1])


def first_cross_down(rows, i0, i1, fast=5, slow=20):
    for i in range(i0, i1 + 1):
        if ma(rows, i, fast) < ma(rows, i, slow) and ma(rows, i - 1, fast) >= ma(rows, i - 1, slow):
            return i
    return None


def scene_moutai():
    mt, src = load("moutai")
    mq, _ = load("moutai_qfq")
    c3, _ = load("csi300")
    val, vsrc = load("moutai_val")
    T = "2021-02-10"
    t = at(mt, T)
    t5, t20 = t + 5, t + 20
    pe = next(r for r in val if r["date"] == T)["pe_ttm"]
    y0 = val[0]["date"][:4]
    pe_hist = [r["pe_ttm"] for r in val if r["date"] <= "2020-12-31"]
    pe_med = statistics.median(pe_hist)
    pe_max_before = max(r["pe_ttm"] for r in val if r["date"] < T)
    ma5, ma20 = ma(mt, t, 5), ma(mt, t, 20)
    two_year = mq[t]["close"] / mq[at(mq, "2019-02-11")]["close"]
    seg1 = pct(mq[t + 1]["open"], mq[t5]["close"])
    seg2 = pct(mq[t5]["close"], mq[t20]["close"])
    ps1, ps2 = per_share(seg1), per_share(seg2)
    high = max(mt[t + 1:t + 21], key=lambda r: r["high"])
    low_m = min(mt[t + 1:t + 21], key=lambda r: r["low"])
    dd = pct(high["high"], low_m["low"])
    i3 = at(c3, T)
    c3_high = max(c3[i3 + 1:i3 + 21], key=lambda r: r["high"])
    c3_low = min(c3[i3 + 1:i3 + 21], key=lambda r: r["low"])
    dd300 = pct(c3_high["high"], c3_low["low"])
    i24 = at(mt, "2024-09-30")
    low24 = min(mt[t:i24 + 1], key=lambda r: r["low"])
    dd24 = pct(high["high"], low24["low"])
    cross = first_cross_down(mt, t + 1, t + 25)
    ma5_t5, ma20_t5 = ma(mt, t5, 5), ma(mt, t5, 20)
    rule_note = None
    if cross:
        after_low = min(r["low"] for r in mt[cross:t + 21])
        rule_note = (f"5/20 双均线在 {int(mt[cross]['date'][5:7])} 月 {int(mt[cross]['date'][8:])} 日才亮红灯：这时已经从最高点跌了 "
                     f"{abs(pct(high['high'], mt[cross]['close'])):.0f}%，但躲过了之后一个月里的再跌 {abs(pct(mt[cross]['close'], after_low)):.0f}%。")
    options = [
        {"key": "A", "label": "加仓", "shares": 3},
        {"key": "B", "label": "继续拿着", "shares": 2},
        {"key": "C", "label": "卖一半", "shares": 1},
        {"key": "D", "label": "全部卖出", "shares": 0},
    ]
    pe_series = [round(r["pe_ttm"], 1) for r in val if r["date"] <= T]
    return {
        "id": "smt", "season": "autumn", "season_cn": "秋", "season_name": "松动", "door": "A", "tier": "P0",
        "path": path(mq, t, [t5, t20], instrument="贵州茅台（前复权）"),
        "title": "茅台与顶流基金 · 抱团瓦解", "year": "2021", "market": "A股",
        "door_hint": "A 股 · 春节前的最后一天",
        "decision_mode": "simultaneous",
        "t_date": T, "t_text": "2021 年 2 月 10 日收盘后，春节前最后一个交易日",
        "blind": {
            "headline": "人人都抱着同一样东西",
            "lines": [
                f"几只龙头股两年涨了好几倍，估值处在历史高位。",
                "新基金一天就卖光，基金经理有了粉丝后援会。",
                "明天起放春节长假。",
            ],
            "position": "你的这类仓位已经浮盈 80%。",
            "question": "节前最后一天，你怎么做？",
            "chart": rebased(mq, t, 250),
        },
        "options": options,
        "evidence": {
            "price": ev("price", "5/20 信号灯：绿灯" if ma5 > ma20 else "5/20 信号灯：红灯", [
                f"5 日均线 {ma5:.0f} 元，{'在' if ma5 > ma20 else '跌破'} 20 日均线 {ma20:.0f} 元{'上方：趋势还在' if ma5 > ma20 else ''}。",
                f"两年里，股价涨到了原来的 {two_year:.1f} 倍。",
                "规则：5 日线跌破 20 日线，才亮红灯。",
            ], stat={"value": "绿灯" if ma5 > ma20 else "红灯", "caption": "5 日线 vs 20 日线"},
                chart={"type": "line", "values": downsample([r["close"] for r in mt[t - 59:t + 1]], 60), "labels": ["三个月前", "今天"], "unit": "股价（元）"},
                source=f"行情：{src}"),
            "data": ev("data", f"估值温度计：{pe:.0f} 倍", [
                f"龙头公司的市盈率 {pe:.1f} 倍，是 {y0} 年以来的最高值（此前最高 {pe_max_before:.1f} 倍）。",
                f"{y0}—2020 年，它的市盈率中位数是 {pe_med:.0f} 倍。",
                "市盈率 = 股价 ÷ 每股盈利：越高，越是在为未来付钱。",
            ], stat={"value": f"{pe:.0f} 倍", "caption": "市盈率（滚动 12 个月）"},
                chart={"type": "line", "values": downsample(pe_series, 72), "labels": [f"{y0} 年初", "今天"], "unit": "市盈率（倍）"},
                risk=True, source=f"估值：{vsrc}（{y0} 年起）"),
            "news": ev("news", "粉丝应援墙", [
                "“喝的是酒，炒的是股。”",
                "一只新基金一天被认购超过 2000 亿元（公开报道）。",
                "“抱紧核心资产，跌了就是上车的机会。”",
            ], source=NEWS_SOURCE),
            "tip": ev("tip", "猫头鹰的信", [
                "人人都拿着的东西，最大的风险不是坏消息，而是所有人同时想走。",
                "你打算在什么信号出现时离开？先写下来。",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "节后第一周", "mechanic": "crowd_ring", "mechanic_name": "抱团圈",
            "board_rules": [
                "先按快进牌结算第一段。",
                "还在场的人把棋子放进抱团圈，在委托单快进栏勾“留下”或“离开”，扣下后一起翻开。",
                "同时离开的人每多 1 个，每个离开的人多亏 1 资金（挤出口，游戏化处理）。",
                "手里有“5/20 双均线”规则牌的人，按快进牌上的信号灯照做。",
            ],
            "cards": [{
                "title": "快进 · 节后五个交易日",
                "lines": [
                    f"节后第一天，股价盘中冲到 {high['high']:.0f} 元的历史新高，随后回落。",
                    f"五个交易日后收在 {mt[t5]['close']:.0f} 元，这一段 {signed(seg1)}。",
                    f"5/20 信号灯：{'红灯，提示卖出' if ma5_t5 < ma20_t5 else '还是绿灯'}。",
                ],
                "per_share": ps1, "pct": round(seg1, 2), "dropped": seg1 < 0,
                "dip": dip(mq, mq[t + 1]["open"], t + 1, t5),
                "signal": {"ma5": round(ma5_t5, 1), "ma20": round(ma20_t5, 1), "red": ma5_t5 < ma20_t5,
                           "first_cross_date": mt[cross]["date"] if cross else None},
                "then": "还在场的人：留下，还是离开？",
            }],
        },
        "reveal": {
            "headline": "茅台与顶流基金 · 抱团瓦解",
            "date_line": f"2021 年 2 月 10 日 → {int(mt[t20]['date'][5:7])} 月 {int(mt[t20]['date'][8:])} 日",
            "lines": [
                f"节后第一天盘中 {high['high']:.2f} 元见顶，之后一个月最多跌了 {abs(dd):.0f}%。",
                f"沪深 300 同期最多跌了 {abs(dd300):.0f}%：一起被抱紧的龙头，一起松动。",
                f"这只是开始：到 2024 年 9 月，股价最低到 {low24['low']:.0f} 元，比高点低了 {abs(dd24):.0f}%。",
            ],
            "lesson": "抱团的时候人人都是长期主义者；松动的时候，出口只有一个。",
            "rule_note": rule_note,
            "egg": "想知道 5/20 双均线当时会不会提示卖出？扫码进 Qube，一句话复现。",
            "chart": dated(mt, "2020-07-01", "2021-06-30", [(T, "决策日"), (high["date"], "盘中见顶"), (low_m["date"], "一个月内低点")]),
            "seg2": {"label": "第 5 个交易日 → 第 20 个交易日", "pct": round(seg2, 2), "per_share": ps2},
            "payoff_rows": payoff_rows(options, ps1, ps2),
            "source_note": f"行情：{src}（收益按前复权价计算）；估值：{vsrc}；新基金认购额为公开报道。口径：T+1 开盘成交，T+5、T+20 收盘结算。",
        },
        "exits": [
            exit_res("Qube · 茅台 5/20 双均线", QUBE, "一句话复现：2021 年春节后它会不会提示你卖出", "PandaAI 产品", login=True,
                     prompt="用 5/20 双均线回测贵州茅台 2020—2021 年，看 2021 年春节后有没有提示卖出"),
            exit_res("均线交叉信号分析", QS_SKILL + "skill-ma-crossover-signal", "把“趋势走坏就卖”写成能检验的规则", "QuantSkills 技能"),
            exit_res("拥挤度风险监控智能体", QS_AGENT + "agent-crowding-risk-monitor", "识别抱团、过热、踩踏与去杠杆风险", "QuantSkills 智能体"),
            exit_res("指数估值轮动", QS_SKILL + "skill-index-valuation-rotation", "看估值分位：现在贵不贵、轮到谁", "QuantSkills 技能"),
            exit_res("A股个股档案", QS_SKILL + "skill-a-share-stock-dossier", "输入一个代码，拿到可溯源的尽调报告", "QuantSkills 技能"),
        ],
        "qr": qr_ids("smt"),
    }


# ───────────────────────────── 冬 · 2020 熔断 ─────────────────────────────
def scene_cb():
    spx, src = load("spx")
    ndx, _ = load("ndx")
    etf, esrc = load("nasdaq_etf")
    T = "2020-03-09"
    t = at(spx, T)
    hi = at(spx, "2020-02-19")
    fall = pct(spx[hi]["close"], spx[t]["close"])
    d_t = pct(spx[t - 1]["close"], spx[t]["close"])
    avgabs = statistics.mean(abs(pct(spx[i - 1]["close"], spx[i]["close"])) for i in range(t - 9, t + 1))
    events = []
    i = 1
    while i < t:
        d = pct(spx[i - 1]["close"], spx[i]["close"])
        if d <= -5 and i + 20 < t:
            events.append((spx[i]["date"], d, pct(spx[i]["close"], spx[i + 20]["close"])))
            i += 5
        else:
            i += 1
    fwd = [e[2] for e in events]
    up = sum(1 for x in fwd if x > 0)
    # 收益按纳斯达克 100 指数算（基金跟踪它）：T 日收盘决定，T+1 开盘成交；每张熔断牌结算到那次熔断当天收盘。
    n = at(ndx, T)
    legs = [("2020-03-12", "熔断 · 3 月 12 日", "美股十天里第二次熔断：标普 500 当天跌 9.5%。"),
            ("2020-03-16", "熔断 · 3 月 16 日", "第三次熔断：标普 500 当天跌 12.0%，1987 年以来最大的单日跌幅。"),
            ("2020-03-18", "熔断 · 3 月 18 日", "十天里第四次熔断：标普 500 当天跌 5.2%。")]
    cards, prev_i, prev_price = [], n, ndx[n + 1]["open"]
    ends = []
    for us_day, title, line in legs:
        j = at(ndx, us_day)
        p = pct(prev_price, ndx[j]["close"])
        between = [f"{int(ndx[k]['date'][5:7])}/{int(ndx[k]['date'][8:])} {signed(pct(ndx[k - 1]['close'], ndx[k]['close']))}"
                   for k in range(prev_i + 1, j + 1)]
        cards.append({"title": title, "lines": [line, "纳指 100 这几天：" + "｜".join(between) + "。", f"你的基金这一段 {signed(p)}。"],
                      "per_share": per_share(p), "pct": round(p, 2), "dropped": p < 0,
                      "us_pct": round(pct(spx[at(spx, us_day) - 1]["close"], spx[at(spx, us_day)]["close"]), 2),
                      "then": "翻沙漏：30 秒不许说话、不许碰牌。时间到，可以把仓位调一档，从下一张牌开始算。"})
        ends.append(j)
        prev_i, prev_price = j, ndx[j]["close"]
    cards[-1]["then"] = "第三次熔断之后：第二次决定——补仓、止损，还是不看了？"
    j_last = ends[-1]
    n20 = n + 20
    seg2 = pct(ndx[j_last]["close"], ndx[n20]["close"])
    ps2 = per_share(seg2)
    seg1_total = pct(ndx[n + 1]["open"], ndx[j_last]["close"])
    bottom = at(spx, "2020-03-23")
    new_high = next(r for r in spx[bottom:] if r["close"] > spx[hi]["close"])
    ndx_t20 = pct(ndx[n + 1]["open"], ndx[n20]["close"])
    e0, e1 = at(etf, "2020-03-10"), at(etf, "2020-03-19")
    etf_ten = pct(etf[e0]["open"], etf[e1]["close"])
    options = [
        {"key": "A", "label": "抄底加仓", "shares": 3},
        {"key": "B", "label": "持有不动", "shares": 2},
        {"key": "C", "label": "减掉一半", "shares": 1},
        {"key": "D", "label": "全部卖出", "shares": 0},
    ]
    seg1_ps = sum(c["per_share"] for c in cards)
    return {
        "id": "scb", "season": "winter", "season_cn": "冬", "season_name": "危机", "door": "A", "tier": "P0",
        "path": path(ndx, n, ends + [n20], instrument="纳斯达克100"),
        "title": "2020 · 美股十天四次熔断", "year": "2020", "market": "美股 / 纳指基金",
        "door_hint": "美股 · 你的 ETF 在海那边",
        "decision_mode": "simultaneous",
        "t_date": T, "t_text": "2020 年 3 月 9 日美股收盘后",
        "blind": {
            "headline": "跌到交易所按下暂停键",
            "lines": [
                "一种新病毒在全球扩散，油价一天暴跌两成多。",
                "美股从高点跌了近两成；今天开盘几分钟，就跌到暂停交易。",
                "你持有一只跟踪美股科技指数的基金。",
            ],
            "position": "你持有 2 份。",
            "question": "明天开盘，你怎么做？",
            "chart": rebased(ndx, at(ndx, T), 120),
        },
        "options": options,
        "evidence": {
            "price": ev("price", f"三周跌了 {abs(fall):.0f}%", [
                f"标普 500 从 2 月 19 日的高点到今天，跌了 {abs(fall):.1f}%。",
                f"最近 10 个交易日，平均每天涨跌 {avgabs:.1f}%。",
                f"今天单日 {signed(d_t)}，开盘几分钟就跌 7%，暂停交易 15 分钟。",
            ], stat={"value": f"{avgabs:.1f}%", "caption": "最近 10 天平均每天的涨跌幅度"},
                chart={"type": "bars", "values": [round(pct(spx[i - 1]["close"], spx[i]["close"]), 2) for i in range(t - 19, t + 1)], "labels": [], "unit": "每日涨跌（%）"},
                source=f"行情：{src}"),
            "data": ev("data", "历史上大跌之后", [
                f"1990 年以来，标普 500 单日跌超 5% 有 {len(events)} 次（相隔 5 天以内的算一次）。",
                f"之后 20 个交易日：{up} 次上涨、{len(events) - up} 次下跌，平均 {signed(statistics.mean(fwd))}。",
                f"最好 {signed(max(fwd))}，最差 {signed(min(fwd))}：平均数挡不住最坏的那次。",
            ], stat={"value": f"{up}/{len(events)}", "caption": "大跌后 20 天上涨的次数"},
                chart={"type": "bars", "values": [round(x, 1) for x in fwd], "labels": [e[0][:7] for e in events], "unit": "大跌后 20 个交易日涨跌（%）"},
                source=f"行情：{src}，自行统计"),
            "news": ev("news", "这几天的快讯", [
                "3 月 3 日：美联储紧急降息 0.5 个百分点。",
                "3 月 9 日：油价一天暴跌约 25%。",
                "3 月 9 日：意大利宣布全国封锁。",
            ], source=NEWS_SOURCE),
            "tip": ev("tip", "猫头鹰的信", [
                "熔断是为了让人停下来，不是逼你马上做决定。",
                "先写下两个数：跌到哪里你认输，涨回哪里你会后悔卖了。",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "十天四次熔断", "mechanic": "circuit_breaker", "mechanic_name": "熔断沙漏",
            "board_rules": [
                "每翻一张熔断牌，先按牌上这一段结算，再翻转沙漏：全桌 30 秒不许说话、不许碰牌。",
                "时间到，每人可以把仓位调一档（记一次“改主意”），调好的仓位从下一张牌开始算。",
                "第三张结算后做第二次决定：补仓、止损或不看了（不看了 = 保持不动）。",
            ],
            "cards": cards,
            "second_decision": {"prompt": "三次熔断之后，第二次决定", "choices": [
                {"key": "add", "label": "补仓", "delta": 1}, {"key": "stop", "label": "止损", "delta": -99},
                {"key": "ignore", "label": "不看了", "delta": 0}]},
            "qr": "scb-ff",
        },
        "reveal": {
            "headline": "2020 · 美股十天四次熔断",
            "date_line": "2020 年 3 月 9 日 → 3 月 18 日",
            "lines": [
                f"3 月 23 日见底：标普 500 收 {spx[bottom]['close']:.0f} 点，比 2 月高点低 {abs(pct(spx[hi]['close'], spx[bottom]['close'])):.0f}%；当天美联储宣布不设上限地购买资产。",
                f"之后一路回升：{int(new_high['date'][5:7])} 月 {int(new_high['date'][8:])} 日，标普 500 收盘 {new_high['close']:.2f} 点，创出新高。",
                f"如果你什么都不做：从决策后开盘到第 20 个交易日收盘，你的基金 {signed(ndx_t20)}，几乎回到原点。胜负全在熔断时那一下。",
                f"同期 A 股上市的纳指 ETF 这十天只跌了 {abs(etf_ten):.0f}%：当时有溢价，买的东西和指数不完全一样。",
            ],
            "lesson": "最恐慌的十天里，卖出和买入的人都觉得自己清醒。区别在于：你有没有提前写好计划。",
            "egg": "彩蛋：5 月初，巴菲特宣布伯克希尔在 4 月清仓了航空股。传奇也会在底部附近卖出。",
            "chart": dated(spx, "2020-01-02", "2020-09-30",
                           [(T, "决策日 · 第一次熔断"), ("2020-03-16", "单日跌 12%"), ("2020-03-23", "见底"), (new_high["date"], "创新高")]),
            "seg1_total": {"pct": round(seg1_total, 2), "per_share": seg1_ps},
            "seg2": {"label": "第二次决定后 → 第 20 个交易日", "pct": round(seg2, 2), "per_share": ps2},
            "payoff_rows": payoff_rows(options, seg1_ps, ps2),
            "second_rows": [
                {"key": "add", "label": "熔断后补仓（多 1 份）", "seg2_extra": ps2, "note": f"第二段多拿 1 份：{ps2:+d}"},
                {"key": "stop", "label": "熔断后止损（清仓）", "seg2_extra": None, "note": f"错过第二段每份 {ps2:+d}"},
                {"key": "ignore", "label": "不看了（不动）", "seg2_extra": 0, "note": "照第一次的仓位拿到底"},
            ],
            "source_note": f"美股指数：{src}；纳指 ETF 513100：{esrc}（{FQ_CN[series('nasdaq_etf')['fq']]}）。口径：T+1 开盘成交，每张熔断牌结算到那次熔断当天收盘，第 20 个交易日收盘揭幕。",
        },
        "exits": [
            exit_res("A2A 办公室", "https://www.pandaaiquant.com/docs/a2a-office", "直接问：“帮我看看这周的美联储议息对我持有的纳指 ETF 有什么影响”", "PandaAI 产品",
                     prompt="帮我看看这周的美联储议息对我持有的纳指 ETF 有什么影响"),
            exit_res("交易行为诊断", QS_SKILL + "skill-trading-behavior-diagnostics", "用你自己的成交记录，看真实大跌时你是恐慌卖、补仓还是冻住", "QuantSkills 技能"),
            exit_res("单标的风险收益画像", QS_SKILL + "skill-risk-return-metrics", "算清楚你拿的东西最坏会跌多少", "QuantSkills 技能"),
            exit_res("全国期货模拟赛「巅峰交易者」", "https://www.pandaaiquant.com/contest/", "在接近真实的压力下，校准你的风险姿态", "PandaAI 赛事"),
        ],
        "qr": qr_ids("scb"),
    }


# ───────────────────────────── 秋门 B · 量化踩踏（P1） ─────────────────────────────
def scene_quant():
    c2, src = load("cn2000")
    c1, _ = load("csi1000")
    c3, _ = load("csi300")
    T = "2024-02-02"
    t = at(c2, T)
    two_w = pct(c2[t - 10]["close"], c2[t]["close"])
    i3 = at(c3, T)
    two_w300 = pct(c3[i3 - 10]["close"], c3[i3]["close"])
    d_t = pct(c2[t - 1]["close"], c2[t]["close"])
    amp = (c2[t]["high"] - c2[t]["low"]) / c2[t - 1]["close"] * 100
    a, b = at(c2, "2021-01-04"), at(c2, "2024-01-02")
    a3, b3 = at(c3, "2021-01-04"), at(c3, "2024-01-02")
    excess = pct(c2[a]["close"], c2[b]["close"]) - pct(c3[a3]["close"], c3[b3]["close"])
    t5, t20 = t + 5, t + 20
    d1 = pct(c2[t]["close"], c2[t + 1]["close"])
    seg1 = pct(c2[t + 1]["open"], c2[t5]["close"])
    seg2 = pct(c2[t5]["close"], c2[t20]["close"])
    ps1, ps2 = per_share(seg1), per_share(seg2)
    lowi = min(range(t, t5 + 1), key=lambda i: c2[i]["low"])
    rebound = pct(c2[lowi]["low"], c2[t5]["close"])
    days = [{"date": c2[i]["date"], "pct": round(pct(c2[i - 1]["close"], c2[i]["close"]), 2)} for i in range(t + 1, t5 + 1)]
    pth = path(c2, t, [t5, t20], instrument="国证2000")
    dp = dip(c2, c2[t + 1]["open"], t + 1, t5)
    options = [
        {"key": "A", "label": "反向加仓", "shares": 3},
        {"key": "B", "label": "继续执行规则", "shares": 2},
        {"key": "C", "label": "修改规则", "shares": 1},
        {"key": "D", "label": "暂停规则", "shares": 0},
    ]
    return {
        "id": "squant", "season": "autumn", "season_cn": "秋", "season_name": "松动", "door": "B", "tier": "P1",
        "path": pth,
        "title": "量化踩踏 · 微盘股闪崩", "year": "2024", "market": "A股 / 量化",
        "door_hint": "A 股 · 一条跑了三年的规则",
        "decision_mode": "simultaneous",
        "t_date": T, "t_text": "2024 年 2 月 2 日收盘后",
        "blind": {
            "headline": "三年都灵的规则，突然不灵了",
            "lines": [
                "“买市值最小的那批股票”，连续三年跑赢大盘。",
                f"最近两周，这类股票突然跌了 {abs(two_w):.0f}%。",
                "新闻里在说雪球敲入、降杠杆，还有“量化收割散户”。",
            ],
            "position": "你按这条规则持有 2 份。",
            "question": "规则还执行吗？",
            "chart": rebased(c2, t, 250),
        },
        "options": options,
        "evidence": {
            "price": ev("price", f"两周跌了 {abs(two_w):.0f}%", [
                f"小市值指数最近 10 个交易日 {signed(two_w)}，同期大盘蓝筹 {signed(two_w300)}。",
                f"今天单日 {signed(d_t)}，盘中振幅 {amp:.1f}%。",
                "跌的时候，成交量反而放大了。",
            ], chart={"type": "line", "values": [r["close"] for r in c2[t - 29:t + 1]], "labels": ["六周前", "今天"], "unit": "指数点位"},
                source=f"行情：{src}（国证 2000）"),
            "data": ev("data", "三年的成绩单", [
                f"2021 年初到今年 1 月，小市值指数跑赢大盘蓝筹约 {excess:.0f} 个百分点。",
                "规则越赚钱，用它的人和钱就越多。",
                "同一时间、同一批股票、同一个方向——这叫拥挤。",
            ], stat={"value": f"+{excess:.0f}", "caption": "三年跑赢大盘的百分点"}, risk=True,
                source=f"行情：{src}；对比：沪深 300"),
            "news": ev("news", "这几天的说法", [
                "“雪球产品大面积敲入。”",
                "“有私募在降杠杆。”",
                "“量化在收割散户。”",
            ], source=NEWS_SOURCE),
            "tip": ev("tip", "猫头鹰的信", [
                "规则的出口，和规则本身一样重要。",
                "如果所有用这条规则的人在同一天卖出，你排在第几个？",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "所有人的规则同时触发", "mechanic": "exit_board", "mechanic_name": "出口板",
            "board_rules": [
                "先按快进牌结算。",
                "亮牌后，选了同一种卖出动作（修改或暂停）的人越多，出口越挤：同一动作每多 1 人，选它的每人多亏 1 资金。",
                "选 A、B 的人照常按快进牌结算。",
            ],
            "cards": [{
                "title": "快进 · 节前四天和节后第一天",
                "lines": [f"2 月 5 日：小市值指数 {signed(d1)}。", f"随后快速反弹，从低点回升 {rebound:.0f}%。",
                          f"到 2 月 19 日收盘，这一段合计 {signed(seg1)}。"],
                "per_share": ps1, "pct": round(seg1, 2), "dropped": dp is not None, "days": days, "dip": dp,
                "then": "按出口板结算挤出口的额外亏损。",
            }],
        },
        "reveal": {
            "headline": "量化踩踏 · 微盘股闪崩",
            "date_line": "2024 年 2 月 2 日 → 2 月 19 日",
            "lines": [
                "2 月初，小市值股票集体暴跌；2 月 7 日起快速反弹。",
                "2 月 19 日，某头部量化私募开盘一分钟卖出约 25 亿元，被交易所限制交易（公开报道）。",
                "“策略失效”还是“只是拥挤”？这正是量化研究要回答的问题。",
            ],
            "lesson": "规则不会恐慌，但用同一条规则的人会一起恐慌。",
            "egg": None,
            "chart": dated(c2, "2023-10-09", "2024-04-30", [(T, "决策日"), (c2[lowi]["date"], "低点"), ("2024-02-19", "节后")]),
            "seg2": {"label": "第 5 个交易日 → 第 20 个交易日", "pct": round(seg2, 2), "per_share": ps2},
            "payoff_rows": payoff_rows(options, ps1, ps2),
            "source_note": f"行情：{src}（国证 2000 作为小市值代理）；私募卖出金额为公开报道。口径：T+1 开盘成交，T+5、T+20 收盘结算。",
        },
        "exits": [
            exit_res("策略与因子失效分诊", QS_AGENT + "agent-quant-failure-triage", "分清是市场变了还是模型坏了，要不要重训", "QuantSkills 智能体"),
            exit_res("B10 因子评估系统", QS_SKILL + "skill-build-b10-factor-evaluation", "看“小市值”的 IC、分层和衰减怎么变拥挤", "QuantSkills 技能"),
            exit_res("因子衰减分析", QS_SKILL + "skill-factor-decay", "估计一个因子的半衰期", "QuantSkills 技能"),
            exit_res("第四届因子大赛", "https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/", "用真实数据把你的规则做成因子去比一比", "PandaAI 赛事"),
        ],
        "qr": qr_ids("squant"),
    }


# ───────────────────────────── 冬门 B · 原油宝（P1） ─────────────────────────────
def scene_oil():
    wti, src = load("wti_cont")
    T = "2020-04-17"
    t = next(i for i, r in enumerate(wti) if r["date"] >= "2020-04-15")
    ytd = pct(wti[at(wti, "2020-01-02")]["close"], 18.27)
    options = [
        {"key": "A", "label": "抄底这款产品", "shares": 2},
        {"key": "B", "label": "改买远月合约", "shares": 1},
        {"key": "C", "label": "看不懂，不碰", "shares": 0},
        {"key": "D", "label": "观望", "shares": 0},
    ]
    near = pct(18.27, -37.63)
    far = pct(25.03, 20.43)
    sc = series("sc_curve")
    if sc:
        m = {r["month"]: r["settlement"] for r in sc["rows"]}
        sc_a, sc_b = m["2020-06"], m[max(m)]
        curve_lines = [
            "WTI 5 月合约 18.27 美元，6 月合约约 25 美元（公开报道）。",
            f"国内原油期货同一天也一样：6 月合约 {sc_a:.0f} 元/桶，一年后的合约 {sc_b:.0f} 元/桶，贵 {pct(sc_a, sc_b):.0f}%。",
            "这叫“远月升水”：现在没人愿意接货，仓库快满了。",
        ]
        curve_chart = {"type": "bars", "values": [round(r["settlement"]) for r in sc["rows"]], "labels": [], "unit": "国内原油期货各月合约结算价（元/桶），从近到远"}
        curve_src = f"WTI：公开报道的结算价；国内原油期货：{sc['source']}"
    else:
        curve_lines = [
            "5 月合约 18.27 美元，6 月合约约 25 美元（公开报道）。",
            "价差这么大，说明现在没人愿意接货：仓库快满了。",
            "这叫“远月升水”：越近越便宜，不是好事。",
        ]
        curve_chart, curve_src = None, "公开报道的结算价"
    return {
        "id": "soil", "season": "winter", "season_cn": "冬", "season_name": "危机", "door": "B", "tier": "P1",
        "title": "原油宝 · 油价跌到负 37 美元", "year": "2020", "market": "期货",
        "door_hint": "期货 · 一款人人都在抄底的理财",
        "decision_mode": "simultaneous",
        "t_date": T, "t_text": "2020 年 4 月 17 日收盘后",
        "blind": {
            "headline": "油价跌掉一大半，该抄底了？",
            "lines": [
                "油价今年跌去一大半，“抄底原油”成了热门理财。",
                "一款挂钩近月合约的银行产品卖得火热。",
                "近月合约下周就到期，远月合约比近月贵不少。",
            ],
            "position": "你手里有一笔闲钱，2 份的额度。",
            "question": "你怎么做？",
            "chart": rebased(wti, t, 150),
        },
        "options": options,
        "evidence": {
            "price": ev("price", f"今年跌了 {abs(ytd):.0f}%", [
                f"年初 WTI 原油每桶 {wti[at(wti, '2020-01-02')]['close']:.0f} 美元左右。",
                "现在近月合约 18.27 美元（4 月 17 日结算价，公开报道）。",
                "跌得越多，“抄底”的声音越大。",
            ], source=f"行情：{src}；结算价为公开报道"),
            "data": ev("data", "远月比近月贵", curve_lines, chart=curve_chart, risk=True, source=curve_src),
            "news": ev("news", "产品说明书（节选，游戏改写）", [
                "本产品挂钩 WTI 原油近月合约。",
                "到期前一个交易日，按当天结算价移仓或轧差。",
                "极端行情下，亏损可能超过本金。",
            ], risk=True, source="根据公开报道改写的产品规则"),
            "tip": ev("tip", "猫头鹰的信", [
                "买之前先回答三个问题：挂钩的是什么？什么时候移仓？最坏会亏多少？",
                "答不上来，就是“看不懂”。看不懂，也是一个好理由。",
            ], source=TIP_SOURCE),
        },
        "fast_forward": {
            "title": "跌破零", "mechanic": "negative_balance", "mechanic_name": "负债牌",
            "board_rules": [
                "买了近月产品的人：本金亏光还倒欠，每份仓位亏 12 资金（游戏化处理），资金可以跌破 0；低于 0 拿负债牌。",
                "改买远月合约的人按快进牌结算。",
            ],
            "cards": [{
                "title": "快进 · 4 月 20 日",
                "lines": ["5 月合约结算价 −37.63 美元。", "历史上第一次跌到负数：手里有油的人，要倒贴钱请别人拿走。",
                          f"6 月合约同日约 20.43 美元，{signed(far)}（公开报道）。"],
                "per_share": -12, "pct": round(near, 1), "dropped": True,
                "far": {"per_share": per_share(far), "pct": round(far, 1)},
                "then": "资金跌破 0 的人拿一张负债牌。",
            }],
        },
        "reveal": {
            "headline": "原油宝 · 油价跌到负 37 美元",
            "date_line": "2020 年 4 月 17 日 → 4 月 22 日",
            "lines": [
                "4 月 20 日，WTI 5 月合约结算价 −37.63 美元，历史上第一次为负。",
                "挂钩近月合约的银行产品按这个价格结算，投资者不仅本金亏光，还被要求补缴穿仓亏损（公开报道）。",
                "同一时间，远月合约跌得少得多：同样是“原油”，买的东西不一样。",
            ],
            "lesson": "看不懂的产品，最贵的不是手续费，是你不知道的那条规则。",
            "egg": None,
            "chart": dated(wti, "2020-01-02", "2020-06-30", [("2020-04-15", "决策前"), ("2020-04-21", "换月")]),
            "seg2": {"label": "揭幕", "pct": 0, "per_share": 0},
            "payoff_rows": [
                {"key": "A", "label": "抄底这款产品", "shares": 2, "seg1": -24, "seg2": 0, "total": -24},
                {"key": "B", "label": "改买远月合约", "shares": 1, "seg1": per_share(far), "seg2": 0, "total": per_share(far)},
                {"key": "C", "label": "看不懂，不碰", "shares": 0, "seg1": 0, "seg2": 0, "total": 0},
                {"key": "D", "label": "观望", "shares": 0, "seg1": 0, "seg2": 0, "total": 0},
            ],
            "source_note": f"走势：{src}（连续合约在到期前已换月，看不到负价那天）；WTI 结算价为公开报道" + (f"；国内原油期货：{sc['source']}" if sc else "") + "。收益为游戏化折算。",
        },
        "exits": [
            exit_res("全国期货模拟赛「巅峰交易者」", "https://www.pandaaiquant.com/contest/", "先在模拟盘里体验一次移仓换月", "PandaAI 赛事"),
            exit_res("期货连续合约换月审计", QS_SKILL + "skill-futures-roll-auditor", "把“移仓”这条规则算清楚", "QuantSkills 技能"),
            exit_res("期货深度分析", QS_SKILL + "skill-futures-deepview-analyst", "期限结构、基差、席位：一次看懂", "QuantSkills 技能"),
            exit_res("原油简报生成", QS_SKILL + "skill-oil-brief", "每天一份中文原油简报", "QuantSkills 技能"),
        ],
        "qr": qr_ids("soil"),
    }


def teasers():
    return [
        {"id": "sds", "season": "spring", "season_cn": "春", "door": "B", "tier": "P2", "title": "DeepSeek 时刻",
         "door_hint": "美股 / 港股 / A 股 · 一个模型改变的长假", "status": "未开放 · 敬请期待"},
        {"id": "sgme", "season": "summer", "season_cn": "夏", "door": "B", "tier": "P2", "title": "GameStop 逼空",
         "door_hint": "美股 · 散户在论坛里集结", "status": "未开放 · 敬请期待"},
    ]


def data_source():
    used = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(SERIES.glob("*.json"))]
    apis = sorted({s["api"] for s in used if s.get("api")})
    public = [s["name"] for s in used if not s["source"].startswith("Panda Data")]
    note = "标“公开报道”的数字不在行情数据里。"
    if not apis:
        return {"prices": "公开行情接口：" + "、".join(sorted({s["source"] for s in used})) + "。", "note": note}
    return {
        "panda": f"Panda Data：A 股指数和个股日线、茅台前复权与估值因子、上证指数估值、全市场个股逐只统计、纳指 ETF 和上海原油期货（{'、'.join(apis)}）。",
        "public": "Panda Data 不覆盖或口径不同的部分用公开接口：" + "、".join(public) + "。",
        "note": note,
    }


def main():
    scenes = [scene_924(), scene_2015(), scene_moutai(), scene_cb(), scene_quant(), scene_oil()]
    for s in scenes:
        for k, v in s["qr"].items():
            if v not in QR:
                raise SystemExit(f"二维码 id 不存在：{v}")
    out = {
        "version": 1,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "data_source": data_source(),
        "payoff_rule": "1 资金 ≈ 一份仓位涨跌 5%，四舍五入；T+1 开盘成交，快进段、T+20 收盘结算。",
        "scenes": scenes,
        "teasers": teasers(),
    }
    path = ROOT / "content" / "scenes.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for s in scenes:
        ff = s["fast_forward"]["cards"]
        print(f"{s['id']:7} seg1 {[c['pct'] for c in ff]} -> {[c['per_share'] for c in ff]}  seg2 {s['reveal']['seg2']}")
    print("->", path)


if __name__ == "__main__":
    main()
