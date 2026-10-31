"""假数据：在 content/ 真内容出现之前，用它把版式全部做出来。字段严格按 scenes.json 的 schema。

数字和文字只是占位，不能印。真文件出现后 build_all.py 会自动改用 content/ 下的文件。
"""

import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent


def series(n, pts, seed, noise=0.012):
    """pts: [(i, value)...] 分段线性 + 随机波动，返回长度 n 的列表"""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        for (a, va), (b, vb) in zip(pts, pts[1:]):
            if a <= i <= b:
                t = (i - a) / max(1, b - a)
                base = va + (vb - va) * (0.5 - 0.5 * math.cos(math.pi * t))
                break
        else:
            base = pts[-1][1]
        out.append(base)
    walk = 0.0
    res = []
    for i, v in enumerate(out):
        walk = walk * 0.85 + rnd.gauss(0, noise)
        res.append(round(v * (1 + walk), 2))
    res[0] = 100.0 if pts[0][1] == 100 else res[0]
    return res


def trading_days(start, n):
    d = date.fromisoformat(start)
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def ev(kind, title, lines, stat, chart, risk, species, source):
    return {"kind": kind, "label": {"price": "量价", "data": "数据", "news": "消息"}[kind], "title": title,
            "lines": lines, "stat": stat, "chart": chart, "risk": risk, "species": species, "source": source}


def tip(lines):
    return {"kind": "tip", "label": "锦囊", "title": "猫头鹰的信", "lines": lines, "stat": None, "chart": None,
            "risk": False, "species": None, "source": ""}


SRC = "行情：腾讯证券公开接口"


def scene_924():
    blind = series(250, [(0, 100), (120, 96), (236, 86.5), (249, 106.5)], 924)
    rv = series(40, [(0, 88), (18, 86.8), (24, 106.5), (25, 111.5), (26, 104), (39, 101)], 9241)
    return {
        "id": "s924", "season": "spring", "season_cn": "春", "season_name": "入场", "door": "A", "tier": "P0",
        "title": "2024 · 国庆前夜全民开户", "year": "2024", "market": "A股", "door_hint": "A 股 · 一个长假前夜",
        "decision_mode": "sequential", "t_date": "2024-09-30", "t_text": "2024 年 9 月 30 日收盘后",
        "blind": {"headline": "长假前夜，营业厅排起长队",
                  "lines": ["一周前，指数还在一年里的低位。", "这五天连着大涨，成交一天比一天大。", "明天起放七天长假，假期里不能交易。"],
                  "position": "你现在是空仓。", "question": "节后怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "节后开盘追入", "shares": 2}, {"key": "B", "label": "小仓位试水", "shares": 1},
                    {"key": "C", "label": "等回调再说", "shares": 0, "note": "快进时可进 1 份"}, {"key": "D", "label": "不参与", "shares": 0}],
        "evidence": {
            "price": ev("price", "成交额创纪录", ["最后一天的成交额，是过去一年日均的三倍多。", "五个交易日，指数涨了两成多。"],
                        {"value": "3.2 倍", "caption": "成交额 ÷ 过去一年日均"},
                        {"type": "bars", "values": [1.0, 1.1, 0.9, 1.0, 1.6, 2.1, 2.4, 2.9, 3.2], "labels": ["", "", "", "", "第1天", "", "", "", "第5天"], "unit": "倍"},
                        False, "cheetah", SRC),
            "data": ev("data", "估值从低位回到中间", ["大涨之后，市盈率回到过去十年的中间位置。", "一周前，它还在历史最低的一成里。"],
                       {"value": "48%", "caption": "市盈率在过去十年的分位"},
                       {"type": "line", "values": [30, 22, 18, 12, 9, 7, 8, 48], "labels": ["十年前", "", "", "", "", "一年前", "一周前", "今天"], "unit": "%"},
                       False, "elephant", "估值：公开指数估值数据"),
            "news": ev("news", "假期里刷屏的说法", ["“这次不一样，牛市来了。”", "“营业厅排队开户，加班到深夜。”", "“节后至少还有三个涨停。”"],
                       None, None, False, "meerkat", "消息：当年公开报道，已去掉名字和日期"),
            "tip": tip(["急涨之后放长假，节后第一天往往是情绪最满的时候。", "先想清楚：你买的是它，还是别人的兴奋？", "如果要进，想好跌了怎么办。"]),
        },
        "fast_forward": {"title": "七天后开盘", "mechanic": "queue", "mechanic_name": "开户排队",
                         "board_rules": ["选 A 或 B 的人，按选的顺序把棋子放进开户排队条。", "按节后第一天开盘价成交，结算到第二天收盘。", "选 C 的人这时可以进 1 份。"],
                         "cards": [{"title": "快进 · 节后第一天", "lines": ["开盘直接跳高一成，之后一路回落。", "第二天收盘，比开盘价低了不少。"],
                                    "per_share": -1, "pct": -6.2, "dropped": True,
                                    "then": "再决定一次：持有、卖出或加仓。选 C 的人现在可以进 1 份。"}]},
        "reveal": {"headline": "2024 · 国庆前夜全民开户", "date_line": "2024 年 9 月 30 日 → 10 月 9 日",
                   "lines": ["政策组合拳之后，五天涨了两成多，节前最后一天成交创纪录。", "节后第一天开盘涨近一成，收盘只剩一半涨幅；第二天大跌。"],
                   "lesson": "最热闹的那一天，往往不是最好的那一天。", "egg": "长假里，很多营业厅周末加班帮人开户。",
                   "chart": {"dates": trading_days("2024-08-26", 40), "values": rv, "t_index": 24,
                             "marks": [{"i": 24, "label": "决策日"}, {"i": 25, "label": "节后开盘"}]},
                   "payoff_rows": [{"key": "A", "label": "节后开盘追入", "seg1": -1, "seg2": -1, "total": -2},
                                   {"key": "B", "label": "小仓位试水", "seg1": 0, "seg2": -1, "total": -1},
                                   {"key": "C", "label": "等回调再说", "seg1": 0, "seg2": 0, "total": 0},
                                   {"key": "D", "label": "不参与", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：腾讯证券公开接口（Panda Data 接入后替换）；口径：T+1 开盘成交，T+5、T+20 收盘"},
        "exits": [{"name": "情绪温度计（示例）", "url": "https://www.quantskills.ai/", "why": "看成交和涨停家数，判断是不是太热了。"}],
        "qr": {"blind": "s924-blind", "price": "s924-price", "data": "s924-data", "news": "s924-news", "tip": "s924-tip", "reveal": "s924-reveal"},
    }


def scene_2015():
    blind = series(250, [(0, 100), (90, 128), (180, 182), (249, 251)], 2015)
    rv = series(60, [(0, 205), (30, 238), (40, 251), (50, 182), (55, 170), (59, 188)], 20151)
    return {
        "id": "s2015", "season": "summer", "season_cn": "夏", "season_name": "狂热", "door": "A", "tier": "P0",
        "title": "2015 · 杠杆牛与千股跌停", "year": "2015", "market": "A股", "door_hint": "A 股 · 一个人人都在借钱的夏天",
        "decision_mode": "simultaneous", "t_date": "2015-06-12", "t_text": "2015 年 6 月 12 日收盘后",
        "blind": {"headline": "人人都在借钱买的夏天",
                  "lines": ["菜市场里大家都在聊股票。", "身边有人借了钱，赚得比你多。", "指数一年多翻了一倍还多。"],
                  "position": "你已经满仓，还借了一倍。", "question": "现在怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "再加杠杆", "shares": 3}, {"key": "B", "label": "保持不动", "shares": 2},
                    {"key": "C", "label": "降到无杠杆", "shares": 1}, {"key": "D", "label": "全部卖出", "shares": 0}],
        "evidence": {
            "price": ev("price", "成交量创纪录", ["这几个月，每天的成交量都在刷新纪录。", "换手率高到平均两三天就把流通股换一遍。"],
                        {"value": "3.1 倍", "caption": "成交量是一年前的倍数"},
                        {"type": "line", "values": [1.0, 1.2, 1.3, 1.7, 2.0, 2.2, 2.6, 3.1], "labels": ["一年前", "", "", "", "", "", "", "今天"], "unit": "倍"},
                        False, "cheetah", SRC),
            "data": ev("data", "融资余额：借来的钱", ["借钱买股票的余额，一年涨了四倍多。", "前一天的余额已经超过两万亿。", "借来的钱越多，跌的时候越容易被迫卖。"],
                       {"value": "2.2 万亿", "caption": "融资余额（前一交易日）"},
                       {"type": "bars", "values": [0.4, 0.5, 0.7, 1.0, 1.2, 1.5, 1.9, 2.2], "labels": ["一年前", "", "", "", "", "", "", "昨天"], "unit": "万亿"},
                       True, "elephant", "融资余额：交易所公开数据"),
            "news": ev("news", "茶馆里的两种声音", ["“行情才刚刚开始，四千点是起点。”", "“听说要清理场外配资了。”", "“隔壁老王借了五倍，已经翻倍。”"],
                       None, None, False, "meerkat", "消息：当年公开评论，已去掉名字和日期"),
            "tip": tip(["一年翻倍、人人借钱，是热的信号，不是买的理由。", "借来的钱有期限，跌的时候它不等你。", "想一想：如果下周跌两成，你能撑住吗？"]),
        },
        "fast_forward": {"title": "千股跌停", "mechanic": "sell_window", "mechanic_name": "卖出窗口与跌停锁",
                         "board_rules": ["先结算第一段。", "想卖的人同时伸手，把棋子放上卖出窗口；名额是人数的一半（向下取整，至少 1 个）。", "没卖掉的人放一枚跌停锁，下一段照样跟着跌。", "选 A 的人资金低于 5 时被强制平仓。"],
                         "cards": [{"title": "快进 · 接下来的五个交易日", "lines": ["指数掉头向下，五天跌了一成多。", "很多股票一开盘就跌停，想卖也卖不出去。"],
                                    "per_share": -2, "pct": -13.3, "dropped": True,
                                    "then": "想卖的人同时伸手，把棋子放上卖出窗口。先放上的先卖，没卖掉的人放一枚跌停锁。",
                                    "grid": {"rows": 5, "cols": 20, "filled": [12, 40, 68, 88, 95], "label": "每天跌停的股票（每格约 30 只）"}}]},
        "reveal": {"headline": "2015 · 杠杆牛与千股跌停", "date_line": "2015 年 6 月 12 日 → 7 月 9 日",
                   "lines": ["6 月 12 日，指数冲到七年来最高。之后不到一个月跌了三成多。", "最多的一天，一千多只股票跌停；借钱的人被一批批强制平仓。"],
                   "lesson": "借来的钱，会在你最需要时间的时候，逼你离场。", "egg": None,
                   "chart": {"dates": trading_days("2015-04-07", 60), "values": rv, "t_index": 47,
                             "marks": [{"i": 47, "label": "决策日"}, {"i": 56, "label": "千股跌停"}]},
                   "payoff_rows": [{"key": "A", "label": "再加杠杆", "seg1": -4, "seg2": -3, "total": -7},
                                   {"key": "B", "label": "保持不动", "seg1": -3, "seg2": -2, "total": -5},
                                   {"key": "C", "label": "降到无杠杆", "seg1": -1, "seg2": -1, "total": -2},
                                   {"key": "D", "label": "全部卖出", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：腾讯证券公开接口（Panda Data 接入后替换）；口径：T+1 开盘成交，T+5、T+20 收盘"},
        "exits": [{"name": "拥挤度风险监控智能体", "url": "https://www.quantskills.ai/agents/agent-crowding-risk-monitor", "why": "人人都在借钱买的时候，先看拥挤度。"}],
        "qr": {"blind": "s2015-blind", "price": "s2015-price", "data": "s2015-data", "news": "s2015-news", "tip": "s2015-tip", "reveal": "s2015-reveal"},
    }


def scene_mt():
    blind = series(250, [(0, 100), (100, 128), (200, 190), (249, 262)], 2021)
    rv = series(50, [(0, 225), (20, 262), (22, 266), (35, 205), (49, 210)], 20211)
    return {
        "id": "smt", "season": "autumn", "season_cn": "秋", "season_name": "松动", "door": "A", "tier": "P0",
        "title": "2021 · 茅台与顶流基金 · 抱团瓦解", "year": "2021", "market": "A股", "door_hint": "A 股 · 一个抱成一团的春节前",
        "decision_mode": "simultaneous", "t_date": "2021-02-10", "t_text": "2021 年 2 月 10 日收盘后",
        "blind": {"headline": "人人都抱着同一批好股票",
                  "lines": ["最热门的基金一天就卖完了。", "大家都说：好公司，贵一点也值得。", "这一类股票一年多涨了一倍半。"],
                  "position": "你的这类仓位已经浮盈八成。", "question": "春节前怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "加仓", "shares": 3}, {"key": "B", "label": "继续拿", "shares": 2},
                    {"key": "C", "label": "卖一半", "shares": 1}, {"key": "D", "label": "全卖", "shares": 0}],
        "evidence": {
            "price": ev("price", "5/20 双均线信号灯", ["5 日均线仍在 20 日均线上方，信号灯是绿灯“继续持有”。", "但两条线的距离，是一年里最大的。"],
                        {"value": "持有", "caption": "5/20 双均线此刻的信号"},
                        {"type": "line", "values": [100, 108, 115, 126, 140, 151, 170, 190], "labels": ["", "", "", "", "", "", "", "今天"], "unit": ""},
                        False, "cheetah", SRC),
            "data": ev("data", "估值温度计", ["这批股票的平均市盈率，到了过去十年的最高位置。", "同样的利润，现在要付两倍的价钱。"],
                       {"value": "97%", "caption": "市盈率历史分位"},
                       {"type": "grid", "values": [97], "labels": ["温度"], "unit": "%"},
                       True, "elephant", "估值：公开数据"),
            "news": ev("news", "粉丝应援墙", ["“基金经理就是我们的顶流！”", "“好公司永远不嫌贵。”", "“春节后还要再买一点。”"],
                       None, None, False, "meerkat", "消息：当年公开评论，已去掉名字"),
            "tip": tip(["好公司和好价格是两件事。", "所有人都抱着同一批股票时，出口会很挤。", "看看估值，再看看你先看了哪一张。"]),
        },
        "fast_forward": {"title": "节后第一周", "mechanic": "huddle", "mechanic_name": "抱团圈",
                         "board_rules": ["先结算第一段。", "还在场的人把棋子放进抱团圈，在委托单快进栏勾“留下”或“离开”，一起翻。", "同一时刻离开的人越多，每人多亏 1 资金。"],
                         "cards": [{"title": "快进 · 节后第一周", "lines": ["节后第一天又冲了一下新高，随后一路下跌。", "一周跌了一成多，抱团开始松动。"],
                                    "per_share": -2, "pct": -11.5, "dropped": True,
                                    "then": "还在场的人把棋子放进抱团圈：留下还是离开？一起翻。手里有“5/20 双均线”规则牌的人：此刻信号是“卖出”。"}]},
        "reveal": {"headline": "2021 · 茅台与顶流基金 · 抱团瓦解", "date_line": "2021 年 2 月 10 日 → 3 月 9 日",
                   "lines": ["春节后第一个交易日，抱团股冲上最高点。", "之后不到一个月，龙头跌了三成，顶流基金一起回撤。"],
                   "lesson": "好公司也会有坏价格；人越挤，出口越窄。", "egg": "扫码可以直接打开「茅台 5/20 双均线」的回测模板。",
                   "chart": {"dates": trading_days("2021-01-04", 50), "values": rv, "t_index": 27,
                             "marks": [{"i": 27, "label": "决策日"}, {"i": 28, "label": "最高点"}]},
                   "payoff_rows": [{"key": "A", "label": "加仓", "seg1": -3, "seg2": -3, "total": -6},
                                   {"key": "B", "label": "继续拿", "seg1": -2, "seg2": -2, "total": -4},
                                   {"key": "C", "label": "卖一半", "seg1": -1, "seg2": -1, "total": -2},
                                   {"key": "D", "label": "全卖", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：腾讯证券公开接口（Panda Data 接入后替换）；口径：T+1 开盘成交，T+5、T+20 收盘"},
        "exits": [{"name": "Qube 模板「茅台 5/20 双均线」", "url": "https://www.quantskills.ai/", "why": "把你在游戏里用的规则放进更长的历史。"}],
        "qr": {"blind": "smt-blind", "price": "smt-price", "data": "smt-data", "news": "smt-news", "tip": "smt-tip", "reveal": "smt-reveal"},
    }


def scene_cb():
    blind = series(250, [(0, 100), (200, 131), (236, 139), (249, 118)], 2020, noise=0.01)
    rv = series(70, [(0, 132), (25, 139), (34, 118), (42, 96), (52, 108), (69, 128)], 20201, noise=0.016)
    return {
        "id": "scb", "season": "winter", "season_cn": "冬", "season_name": "危机", "door": "A", "tier": "P0",
        "title": "2020 · 美股十天四次熔断", "year": "2020", "market": "美股（A 股上市的跟踪 ETF）", "door_hint": "美股 · 一个全世界都在看新闻的春天",
        "decision_mode": "simultaneous", "t_date": "2020-03-09", "t_text": "2020 年 3 月 9 日收盘后",
        "blind": {"headline": "深夜，屏幕上的数字一起变色",
                  "lines": ["一种新病毒在全世界蔓延。", "油价一夜之间暴跌。", "今晚开盘几分钟，交易就被暂停了。"],
                  "position": "你持有一只跟踪海外科技指数的 ETF。", "question": "明天怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "抄底加仓", "shares": 3}, {"key": "B", "label": "持有", "shares": 2},
                    {"key": "C", "label": "减半", "shares": 1}, {"key": "D", "label": "清仓", "shares": 0}],
        "evidence": {
            "price": ev("price", "三周跌了一成半", ["从高点到今天，指数跌了一成半。", "每天的波动，是过去一年平均的四倍。"],
                        {"value": "−15%", "caption": "距离高点"},
                        {"type": "line", "values": [100, 103, 106, 108, 104, 97, 93, 85], "labels": ["", "", "", "高点", "", "", "", "今天"], "unit": ""},
                        False, "cheetah", SRC),
            "data": ev("data", "大跌之后的 20 天", ["过去三十年，单日跌超 7% 的日子有 10 次。", "其后 20 天，6 次涨回来，4 次继续跌。", "平均下来差不多，但分得很开。"],
                       {"value": "6 : 4", "caption": "其后 20 天 涨 : 跌"},
                       {"type": "bars", "values": [8, -12, 5, 11, -6, 14, -9, 3, 7, -4], "labels": [], "unit": "%"},
                       False, "elephant", "历史统计：公开指数数据"),
            "news": ev("news", "滚动的快讯", ["“多国宣布入境限制。”", "“油价单日暴跌三成。”", "“开盘 5 分钟，触发熔断。”"],
                       None, None, False, "meerkat", "消息：当年公开快讯，已去掉名字和日期"),
            "tip": tip(["没人知道明天，但你能决定自己能承受多大的波动。", "熔断是让大家停下来想一想。", "这只 ETF 有溢价，涨跌不一定和指数一样。"]),
        },
        "fast_forward": {"title": "十天四次熔断", "mechanic": "circuit_breaker", "mechanic_name": "熔断禁声",
                         "board_rules": ["每翻一张熔断牌，翻沙漏：全桌 30 秒不许说话、不许碰牌。", "时间到，每人可以把仓位调一档（记一次“改主意”），再结算这一段。", "第三张之后做第二次决定：补仓、止损或不看了。"],
                         "cards": [
                             {"title": "熔断 · 第一次", "lines": ["开盘几分钟就跌了 7%，交易暂停 15 分钟。"], "per_share": -1, "pct": -7.6, "dropped": True, "then": "翻沙漏，30 秒禁声。时间到，可以调一档。"},
                             {"title": "熔断 · 第二次", "lines": ["三天后再次熔断，全天跌了近一成。"], "per_share": -2, "pct": -9.5, "dropped": True, "then": "翻沙漏，30 秒禁声。时间到，可以调一档。"},
                             {"title": "熔断 · 第三、四次", "lines": ["一周之内又熔断两次，波动大到看不清方向。"], "per_share": -1, "pct": -12.0, "dropped": True, "then": "做第二次决定：补仓、止损，或者不看了（等于不动）。"}]},
        "reveal": {"headline": "2020 · 美股十天四次熔断", "date_line": "2020 年 3 月 9 日 → 4 月 7 日",
                   "lines": ["3 月 9 日、12 日、16 日、18 日，十天里四次熔断。", "3 月 23 日见底之后，指数用不到三个月涨回了熔断前。"],
                   "lesson": "最难的不是看对方向，而是在看不清的时候不乱动。", "egg": "那年 5 月，一位传奇投资人宣布清仓了全部航空股。",
                   "chart": {"dates": trading_days("2020-01-27", 70), "values": rv, "t_index": 30,
                             "marks": [{"i": 30, "label": "决策日"}, {"i": 33, "label": "熔断"}, {"i": 35, "label": "熔断"}, {"i": 37, "label": "熔断"}, {"i": 40, "label": "见底"}]},
                   "payoff_rows": [{"key": "A", "label": "抄底加仓", "seg1": -4, "seg2": 3, "total": -1},
                                   {"key": "B", "label": "持有", "seg1": -3, "seg2": 2, "total": -1},
                                   {"key": "C", "label": "减半", "seg1": -1, "seg2": 1, "total": 0},
                                   {"key": "D", "label": "清仓", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：腾讯证券公开接口（ETF 有溢价，涨跌和指数不完全一样）；口径：T+1 开盘成交，T+5、T+20 收盘"},
        "exits": [{"name": "市场状态判断（示例）", "url": "https://www.quantskills.ai/", "why": "先判断现在是哪种市场，再决定用什么规则。"}],
        "qr": {"blind": "scb-blind", "price": "scb-price", "data": "scb-data", "news": "scb-news", "tip": "scb-tip", "reveal": "scb-reveal"},
    }


def scene_quant():
    blind = series(250, [(0, 100), (150, 118), (220, 126), (249, 104)], 2024)
    rv = series(40, [(0, 120), (15, 104), (20, 82), (24, 78), (39, 96)], 20241)
    return {
        "id": "squant", "season": "autumn", "season_cn": "秋", "season_name": "松动", "door": "B", "tier": "P1",
        "title": "2024 · 量化踩踏 · 微盘股闪崩", "year": "2024", "market": "A股", "door_hint": "A 股 · 一群安静下单的小机器人",
        "decision_mode": "simultaneous", "t_date": "2024-02-02", "t_text": "2024 年 2 月 2 日收盘后",
        "blind": {"headline": "所有人的规则，指向同一个方向",
                  "lines": ["你的规则买了一大堆很小的公司。", "很多人的规则长得差不多。", "这几天，小公司跌得越来越快。"],
                  "position": "你按规则持有一篮子小盘股。", "question": "规则怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "反向加仓", "shares": 3}, {"key": "B", "label": "继续执行", "shares": 2},
                    {"key": "C", "label": "修改规则", "shares": 1}, {"key": "D", "label": "暂停", "shares": 0}],
        "evidence": {
            "price": ev("price", "跌得越来越快", ["小盘股指数一周跌了一成多。", "成交越来越集中在卖出的那一侧。"],
                        {"value": "−13%", "caption": "一周跌幅"},
                        {"type": "line", "values": [100, 99, 98, 96, 95, 92, 90, 87], "labels": ["", "", "", "", "", "", "", "今天"], "unit": ""},
                        False, "cheetah", SRC),
            "data": ev("data", "拥挤度：一样的仓位", ["同类策略持有的股票，重合度到了历史高位。", "大家的止损线也挨得很近。"],
                       {"value": "高", "caption": "同类策略拥挤度"},
                       {"type": "grid", "values": [88], "labels": ["拥挤"], "unit": "%"},
                       True, "elephant", "拥挤度：公开数据估算"),
            "news": ev("news", "群里的消息", ["“有大户在平仓。”", "“雪球产品要敲入了。”", "“明天还会跌吗？”"], None, None, False, "meerkat", "消息：当年公开讨论，已去掉名字"),
            "tip": tip(["规则本身没有错，错在所有人同时用一样的规则。", "出口只有一个时，先到的人才出得去。"]),
        },
        "fast_forward": {"title": "接下来的三天", "mechanic": "exit_board", "mechanic_name": "出口板",
                         "board_rules": ["亮牌后，选了同一种卖出动作的人越多，每人多亏一点。"],
                         "cards": [{"title": "快进 · 接下来的三天", "lines": ["小盘股三天又跌了两成，很多规则同时触发止损。"], "per_share": -3, "pct": -20.1, "dropped": True, "then": "把棋子放上出口板：同一出口的人越多，每人多亏 1。"}]},
        "reveal": {"headline": "2024 · 量化踩踏 · 微盘股闪崩", "date_line": "2024 年 2 月 2 日 → 2 月 8 日",
                   "lines": ["一周之内，小盘股指数跌了三成，很多量化产品同时回撤。", "2 月 8 日之后，市场才慢慢稳下来。"],
                   "lesson": "规则一样，出口就一样窄。", "egg": None,
                   "chart": {"dates": trading_days("2024-01-02", 40), "values": rv, "t_index": 23,
                             "marks": [{"i": 23, "label": "决策日"}, {"i": 26, "label": "闪崩"}]},
                   "payoff_rows": [{"key": "A", "label": "反向加仓", "seg1": -5, "seg2": 2, "total": -3},
                                   {"key": "B", "label": "继续执行", "seg1": -3, "seg2": 1, "total": -2},
                                   {"key": "C", "label": "修改规则", "seg1": -1, "seg2": 0, "total": -1},
                                   {"key": "D", "label": "暂停", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：腾讯证券公开接口；口径：T+1 开盘成交，T+5、T+20 收盘"},
        "exits": [],
        "qr": {"blind": "squant-blind", "price": "squant-price", "data": "squant-data", "news": "squant-news", "tip": "squant-tip", "reveal": "squant-reveal"},
    }


def scene_oil():
    blind = series(250, [(0, 100), (180, 96), (215, 52), (249, 30)], 2026, noise=0.02)
    rv = series(30, [(0, 40), (15, 30), (19, 20), (20, -60), (22, 25), (29, 30)], 20261, noise=0.02)
    return {
        "id": "soil", "season": "winter", "season_cn": "冬", "season_name": "危机", "door": "B", "tier": "P1",
        "title": "2020 · 原油宝 · 油价跌到负数", "year": "2020", "market": "原油期货（银行理财产品）", "door_hint": "原油 · 一个码头边堆满油罐的春天",
        "decision_mode": "simultaneous", "t_date": "2020-04-17", "t_text": "2020 年 4 月 17 日收盘后",
        "blind": {"headline": "油罐都满了，油价还在跌",
                  "lines": ["全世界的车都停了，油没人要。", "码头边的油罐快装不下了。", "银行柜台在推一款跟踪油价的产品。"],
                  "position": "你买了这款产品，跟踪最近一个月到期的合约。", "question": "到期前怎么办？",
                  "chart": {"values": blind, "t_index": 249, "label": "起点 = 100，名字和日期已隐藏"}},
        "options": [{"key": "A", "label": "抄底加仓", "shares": 3}, {"key": "B", "label": "继续持有", "shares": 2},
                    {"key": "C", "label": "换到远月", "shares": 1}, {"key": "D", "label": "全部卖出", "shares": 0}],
        "evidence": {
            "price": ev("price", "近月和远月差得很远", ["最近一个月的合约，比两个月后的便宜了一大截。", "越临近到期，价格跌得越快。"],
                        {"value": "−70%", "caption": "近月合约四个月跌幅"},
                        {"type": "line", "values": [100, 95, 90, 70, 50, 40, 35, 30], "labels": ["", "", "", "", "", "", "", "今天"], "unit": ""},
                        False, "cheetah", SRC),
            "data": ev("data", "产品说明书里的小字", ["“到期前一天按结算价移仓。”", "“极端情况下，亏损可能超过本金。”", "储油罐的使用率已经到了九成。"],
                       {"value": "> 本金", "caption": "最大亏损可能"},
                       {"type": "grid", "values": [90], "labels": ["库容"], "unit": "%"},
                       True, "elephant", "产品说明：公开资料（泛化改写）"),
            "news": ev("news", "柜台和群里", ["“油价已经跌到底了，比水还便宜。”", "“银行的产品，很安全。”", "“下周就到期了，要不要移仓？”"], None, None, False, "meerkat", "消息：当年公开讨论，已去掉名字"),
            "tip": tip(["先弄清楚你买的是什么：是油，还是一张会到期的合约？", "“跌到底”不是价格的下限。"]),
        },
        "fast_forward": {"title": "到期前一天", "mechanic": "debt", "mechanic_name": "穿仓与负债牌",
                         "board_rules": ["买了近月产品的人，资金可以跌破 0，拿负债牌。"],
                         "cards": [{"title": "快进 · 到期前一天", "lines": ["近月合约收在负数，买了近月的人倒欠钱。"], "per_share": -8, "pct": -305.0, "dropped": True, "then": "资金低于 0 的人拿一张负债牌。"}]},
        "reveal": {"headline": "2020 · 原油宝 · 油价跌到负数", "date_line": "2020 年 4 月 17 日 → 4 月 21 日",
                   "lines": ["4 月 20 日，美国原油近月合约收在每桶负 37 美元。", "按这个价格结算，买了近月产品的人不但亏光，还要倒补钱。"],
                   "lesson": "看不懂的产品，最大的风险写在你没读的那一行里。", "egg": None,
                   "chart": {"dates": trading_days("2020-03-20", 30), "values": rv, "t_index": 19,
                             "marks": [{"i": 19, "label": "决策日"}, {"i": 20, "label": "负 37 美元"}]},
                   "payoff_rows": [{"key": "A", "label": "抄底加仓", "seg1": -12, "seg2": 0, "total": -12},
                                   {"key": "B", "label": "继续持有", "seg1": -8, "seg2": 0, "total": -8},
                                   {"key": "C", "label": "换到远月", "seg1": -1, "seg2": 0, "total": -1},
                                   {"key": "D", "label": "全部卖出", "seg1": 0, "seg2": 0, "total": 0}],
                   "source_note": "行情：公开期货数据；口径：结算价"},
        "exits": [],
        "qr": {"blind": "soil-blind", "price": "soil-price", "data": "soil-data", "news": "soil-news", "tip": "soil-tip", "reveal": "soil-reveal"},
    }


def scenes():
    return {"version": 1, "generated_at": "MOCK", "data_source": {"prices": "腾讯证券公开接口", "margin": "交易所公开数据", "note": "假数据，仅用于排版"},
            "scenes": [scene_924(), scene_2015(), scene_mt(), scene_cb(), scene_quant(), scene_oil()]}


def decks():
    sp = [
        ("cheetah", "猎豹", "Cheetah", "先看量价，跑在前面", "反应快，相信价格和成交量说的话。", ["先看走势和成交，再看别的。", "看到动起来就想上车。"], ["抓得住趋势的开头。", "决定快，不拖。"], ["容易追在最热的时候。", "急转弯时来不及刹车。"], "试试给你的“快”加一条离场规则。"),
        ("elephant", "大象", "Elephant", "先翻账本，再做决定", "稳重，相信数据和长期的规律。", ["先看估值、余额这些数字。", "数字不对就按兵不动。"], ["不容易被情绪带走。", "看得到别人忽略的风险。"], ["有时等得太久，错过时机。", "数字也会过时。"], "把你相信的指标放进历史里检验一下。"),
        ("fox", "狐狸", "Fox", "先怀疑，再检验", "喜欢规则和检验，不轻信一句话。", ["用规则代替感觉。", "照计划执行。"], ["说到做到，不乱动。", "能把想法变成可以检验的规则。"], ["规则失效时容易硬撑。", "可能把偶然当成规律。"], "给你的规则换一段历史，看它还灵不灵。"),
        ("owl", "猫头鹰", "Owl", "看清了再出手", "耐心，愿意等待更好的时机。", ["看不清就先观望。", "不急着表态。"], ["少犯冲动的错。", "能看到全局。"], ["观望太久会变成不敢决定。", "机会不会一直等你。"], "练习判断“现在是哪种市场”。"),
        ("meerkat", "狐獴", "Meerkat", "耳朵最灵，消息最快", "对消息敏感，第一个听到风吹草动。", ["先看新闻和大家在说什么。", "很在意身边人的动作。"], ["信息来得快。", "能感到情绪的变化。"], ["容易把热闹当成证据。", "消息常常已经反映在价格里。"], "练习给一条消息找到能核实的数字。"),
        ("chameleon", "变色龙", "Chameleon", "随市场换颜色", "依据随市场切换，但每次都说得通。", ["不同的场景用不同的证据。", "愿意改主意。"], ["适应力强。", "不死守一种方法。"], ["换得太勤会没有主线。", "很难总结自己的方法。"], "写下你每次切换的理由，找出规律。"),
        ("beaver", "海狸", "Beaver", "动手搭一座自己的水坝", "隐藏物种：爱动手，喜欢自己写代码跑数据。", ["读代码、改参数。", "相信自己跑出来的结果。"], ["能把问题拆成可以计算的步骤。", "工具用得好。"], ["容易沉迷工具，忘了问题本身。", "回测好看不等于以后好用。"], "去 panda_data 跑一个你自己的因子。"),
    ]
    species = []
    for i, (sid, name, en, tag, traits, beh, st, bs, rec) in enumerate(sp):
        species.append({"id": sid, "name": name, "en": en, "tagline": tag, "personality": traits, "behaviors": beh,
                        "strengths": st, "blind_spots": bs, "recommend": rec, "hidden": sid == "beaver", "qr": f"sp-{sid}"})
    badges = [
        {"id": "b-evidence", "name": "证据控", "condition": "至少 2 场看了两张及以上不同的证据，并且至少 3 场理由一致"},
        {"id": "b-keepword", "name": "说到做到", "condition": "计划照做至少 2 场"},
        {"id": "b-history", "name": "金融史达人", "condition": "认出并写对事件名至少 2 场"},
        {"id": "b-data", "name": "数据手", "condition": "数据港口答对至少 2 次"},
        {"id": "b-rule", "name": "规则派", "condition": "用规则牌并照做至少 1 场"},
        {"id": "b-risk", "name": "看懂风险", "condition": "看过风险类证据（牌角有标记）至少 2 次"},
    ]
    chance = []
    qs = [
        ("朋友推荐了一只“稳赚”的股票", "你先做什么？", ("先看它最近的走势", "cheetah"), ("先查它的财报和估值", "elephant")),
        ("群里都在说一个新概念", "你会怎么做？", ("跟着看看大家在买什么", "meerkat"), ("等它冷下来再说", "owl")),
        ("你的规则发出了卖出信号", "但你觉得还会涨", ("照规则卖", "fox"), ("先不卖，再看看", "cheetah")),
        ("一只股票三天涨了三成", "你第一反应是？", ("看看成交量是不是也放大了", "cheetah"), ("查查发生了什么新闻", "meerkat")),
        ("你看中的股票比上周便宜了一成", "你会？", ("翻翻估值，看是不是真便宜", "elephant"), ("等它不跌了再买", "owl")),
        ("有人说“这次不一样”", "你会？", ("找历史上相似的时候看看", "elephant"), ("写一条规则：不一样就先少买", "fox")),
        ("你连续亏了三次", "接下来？", ("停一停，复盘", "owl"), ("换一种方法试试", "chameleon")),
        ("一条消息让股票大涨", "你会？", ("先核实消息的来源", "fox"), ("先上车再说", "meerkat")),
        ("市场突然暴跌", "你会？", ("看看过去类似的暴跌之后怎样", "elephant"), ("按事先定的计划做", "fox")),
        ("你同时看到利好和利空", "你会？", ("看价格往哪边走", "cheetah"), ("两边都记下，先不动", "owl")),
        ("有个工具能自动回测", "你会？", ("自己改改参数跑一遍", "fox"), ("看看别人跑出来的结果", "meerkat")),
        ("牛市里人人都在赚钱", "你会？", ("看看大家都在买什么", "meerkat"), ("看看估值到了哪里", "elephant")),
    ]
    for i, (t, p, a, b) in enumerate(qs, 1):
        chance.append({"id": f"chance-{i:02d}", "title": t, "prompt": p,
                       "options": [{"key": "甲", "text": a[0], "species": a[1]}, {"key": "乙", "text": b[0], "species": b[1]}],
                       "qr": f"chance-{i:02d}"})
    retest = []
    rq = [
        ("你最想先看哪一张？", [("走势和成交", "cheetah"), ("估值和余额", "elephant"), ("大家在说什么", "meerkat")]),
        ("做决定前你最需要什么？", [("一条清楚的规则", "fox"), ("更多时间观察", "owl"), ("看看别人怎么做", "meerkat")]),
        ("你上一次改主意，是因为？", [("价格变了", "cheetah"), ("数据变了", "elephant"), ("市场换了样子", "chameleon")]),
        ("如果只能带一件工具", [("放大镜", "fox"), ("望远镜", "owl"), ("账本", "elephant")]),
        ("看到一条大新闻，你先？", [("看价格有没有反应", "cheetah"), ("查它是真是假", "fox"), ("转给朋友讨论", "meerkat")]),
        ("你更怕哪一种？", [("错过机会", "cheetah"), ("买在最高点", "owl"), ("看不懂就亏了", "elephant")]),
    ]
    for i, (p, opts) in enumerate(rq, 1):
        retest.append({"id": f"retest-{i:02d}", "prompt": p, "options": [{"key": k, "text": t, "species": s} for k, (t, s) in zip("甲乙丙", opts)], "qr": f"retest-{i:02d}"})
    rules = []
    rr = [
        ("rule-ma520", "5/20 双均线", "5 日均线上穿 20 日均线买入，下穿卖出。", True, {"s924": "买入", "s2015": "持有", "smt": "持有", "scb": "卖出"}),
        ("rule-ma52060", "5/20/60 三均线", "三条均线多头排列才持有，否则空仓。", True, {"s924": "空仓", "s2015": "持有", "smt": "持有", "scb": "空仓"}),
        ("rule-mom20", "20 日动量", "过去 20 天涨了就持有，跌了就空仓。", True, {"s924": "持有", "s2015": "持有", "smt": "持有", "scb": "空仓"}),
        ("rule-lowpb-roe", "低估值高回报", "只买估值低、回报高的公司；估值太贵就卖。", True, {"s924": "买入", "s2015": "卖出", "smt": "卖出", "scb": "持有"}),
        ("rule-stop10", "跌 10% 止损", "从买入价跌 10% 就卖。", False, {"s924": "—", "s2015": "卖出", "smt": "卖出", "scb": "卖出"}),
        ("rule-dip", "跌多了就抄底", "一个月跌超两成就加仓。", False, {"s924": "—", "s2015": "加仓", "smt": "—", "scb": "加仓"}),
        ("rule-vol", "放量才进", "成交额超过一年平均两倍才买。", False, {"s924": "买入", "s2015": "持有", "smt": "持有", "scb": "—"}),
        ("rule-half", "一半一半", "任何时候只用一半仓位。", False, {"s924": "半仓", "s2015": "降半", "smt": "卖一半", "scb": "减半"}),
        ("rule-calm", "冷静三天", "大涨大跌后等三天再动。", False, {"s924": "等", "s2015": "等", "smt": "等", "scb": "等"}),
        ("rule-pe", "估值红线", "市盈率分位超过 80% 就不买。", False, {"s924": "可买", "s2015": "卖出", "smt": "卖出", "scb": "可买"}),
    ]
    for rid, name, rule, real, by in rr:
        rules.append({"id": rid, "name": name, "rule": rule, "real": real, "by_scene": by, "qr": rid if real else None})
    dataport = []
    dd = [
        ("最近 5 天的收盘价", "df = get_price('000001', days=5)\nprint(df['close'].pct_change().sum())", "这段代码算的是什么？", "5 天涨跌幅的近似和"),
        ("20 日均线", "ma20 = df['close'].rolling(20).mean()", "rolling(20) 是什么意思？", "最近 20 个数取一次平均"),
        ("最大回撤", "dd = df['close'] / df['close'].cummax() - 1\nprint(dd.min())", "dd.min() 越小说明什么？", "从高点跌得越深"),
        ("成交量倍数", "vol_x = df['volume'] / df['volume'].rolling(250).mean()", "vol_x = 3 表示？", "成交量是一年均值的 3 倍"),
        ("涨停家数", "n = (df['pct'] >= 9.9).sum()", "这行在数什么？", "涨幅 ≥ 9.9% 的股票数"),
        ("估值分位", "pct = (pe_hist < pe_now).mean()", "pct = 0.97 表示？", "比历史上 97% 的时候都贵"),
        ("融资余额变化", "chg = margin.iloc[-1] / margin.iloc[-250] - 1", "chg = 4 表示？", "一年涨到原来的 5 倍"),
        ("双均线信号", "sig = ma5 > ma20", "sig 为 True 时规则怎么做？", "持有"),
    ]
    for i, (t, code, q, a) in enumerate(dd, 1):
        dataport.append({"id": f"dp-{i:02d}", "title": t, "code": code, "question": q, "answer": a, "qr": f"dp-{i:02d}"})
    tasks = []
    tt = [
        ("chart", "读图入门", "因为你有两场勾了“看不懂”", "用 10 分钟读懂一张 K 线：开盘、收盘、成交量。", "Qube 新手读图任务"),
        ("explore", "数据自主探索", "因为你拿到了“数据手”", "用 panda_data 取一只指数的成交量，画出它的一年。", "panda_data quickstart"),
        ("regime", "状态判断", "因为你常在看不清时选择观望", "判断三段行情分别是上涨、震荡还是下跌。", "QuantSkills 市场状态判断"),
        ("verify", "证据核查", "因为你两场的理由是“消息”或“跟别人”", "给一条刷屏的消息，找到一个能核实它的数字。", "QuantSkills 证据核查"),
        ("hypo", "假设检验", "因为你在游戏里用过一条规则", "把你用过的规则放进十年的历史里，看它灵不灵。", "Qube 模板回测"),
        ("risk", "风险校准", "因为你两场选了 A，但现实里偏保守", "在模拟盘里用同样的仓位走一周，看看自己的感受。", "期货模拟赛"),
    ]
    for t, name, because, todo, res in tt:
        for lv, lvn in (("basic", "入门"), ("adv", "进阶")):
            tasks.append({"id": f"task-{t}-{lv}", "type": t, "type_name": name, "level": lv, "level_name": lvn,
                          "title": f"{name} · {lvn}", "because": because,
                          "todo": todo if lv == "basic" else todo.replace("10 分钟", "20 分钟") + "再换一个参数试一次。",
                          "minutes": 10 if lv == "basic" else 20, "resource": res, "real": t in ("explore", "hypo", "risk"), "qr": f"task-{t}-{lv}"})
    ai = []
    aa = [("cheetah", "追得快", 2, {"s924": "A", "s2015": "A", "smt": "B", "scb": "A"}), ("meerkat", "听消息", 1, {"s924": "A", "s2015": "B", "smt": "A", "scb": "C"}),
          ("owl", "等一等", 3, {"s924": "C", "s2015": "C", "smt": "C", "scb": "B"}), ("elephant", "看账本", 3, {"s924": "B", "s2015": "C", "smt": "D", "scb": "B"}),
          ("fox", "照规则", 3, {"s924": "B", "s2015": "D", "smt": "C", "scb": "C"}), ("chameleon", "随机应变", 2, {"s924": "B", "s2015": "C", "smt": "B", "scb": "C"})]
    for sid, style, stars, picks in aa:
        ai.append({"id": f"ai-{sid}", "species": sid, "name": f"AI · {dict(cheetah='猎豹', meerkat='狐獴', owl='猫头鹰', elephant='大象', fox='狐狸', chameleon='变色龙')[sid]}",
                   "style": style, "level": "入门" if sid in ("cheetah", "meerkat") else "进阶", "stars_per_scene": stars, "picks": picks,
                   "ff_action": "跌了就走" if sid in ("fox", "elephant") else "不动", "line": "它会解释自己为什么这么选：扫开局码和它对局。"})
    debt = [{"id": f"debt-{i}", "amount": a, "text": "资金低于 0：拿一张负债牌，终局收益名次分记 0。"} for i, a in enumerate([5, 5, 5, 5, 10, 10, 10, 20], 1)]
    return {
        "version": 1, "species": species, "badges": badges, "chance": chance, "retest": retest, "rules": rules, "dataport": dataport,
        "tasks": tasks, "ai_species": ai, "debt": debt,
        "quickref": {
            "front": {"title": "一季怎么走", "steps": ["领预算：每人拿 1 研究点。", "赶路：掷两颗骰子选一个点数，1–5 落小格，6 直接到门口并多拿 1 研究点。", "名场面：全员进门，走完六步。", "驿站：拿一枚本季物种币，走到下一季起点。"],
                      "scene_steps": ["盲入场：读场景牌，认出来了就在委托单写事件名。", "开证据：每轮花 1 研究点看一张。", "做决定：在委托单勾选项、理由和计划，扣在玩家板上。", "亮牌：倒数三二一，一起翻。", "快进：翻快进牌，结算第一段，再决定一次。", "揭幕：翻揭幕牌，结算第二段，记方法星。"]},
            "back": {"title": "物种图标从哪来", "note": "第一场揭幕后再翻看", "rows": [["理由勾量价", "猎豹 ×2"], ["理由勾数据", "大象 ×2"], ["理由勾消息、跟别人", "狐獴 ×2"], ["用规则牌并照做", "狐狸 ×2"], ["选观望且理由不是直觉、看不懂", "猫头鹰 ×2"], ["第一张看的证据", "对应物种 ×1"], ["机会牌的答案", "看牌底"]],
                     "stars": ["看了证据 ★，两张及以上不同 ★★", "理由一致 ★", "计划照做 ★"]},
        },
        "prologue": {"title": "序章 · 1720 南海泡沫", "lines": ["1720 年，伦敦。一家叫南海公司的股票半年涨了八倍。", "人人都在买，连大科学家牛顿也买了。他先赚了一笔，卖掉，又在更高的价钱买回去。", "泡沫破了。相传牛顿亏了大约两万英镑，他说：我能算出天体的运行，却算不出人们的疯狂。", "所以这个游戏不比谁赚得多。我们看你怎么做决定。"],
                     "steps": ["一人朗读这张牌。", "把 6 张物种牌摊开（海狸是隐藏物种，不摊）。", "每人在终局档案卡上偷偷圈一个“我觉得我是”。"]},
        "station": {"title": "驿站", "lines": ["数一数这一季委托单上的物种图标，拿一枚最多的那种物种币。", "平局或不同意：抽一张补测牌。", "认出来的场景：币放空心面，算半枚。"]},
        "self_and_real": {"self": "序章时我觉得我是：", "q1": "现实里你上一次遇到大跌，实际做了什么？", "q2": "你上一次买入的主要原因是什么？"},
        "door_teasers": {"spring": {"B": "春 · 门 B：一个开源的东方模型，让全世界的芯片股一夜变了脸"}, "summer": {"B": "夏 · 门 B：一群散户，把一家快倒闭的游戏店推上了天"}},
        "resources": [],
    }


RULES_MD = """# 交易物种起源 · 规则书 v1.0

## 这是什么游戏

你是一只还没孵化的蛋。你要走过市场的四季：春天入场，夏天狂热，秋天松动，冬天危机。每一季，你会走进一个真实的金融史名场面，在不知道是哪一年的情况下做一个决定，然后揭晓当年到底发生了什么。

走完四季，你会孵化成自己的“交易物种”。物种只表示你做决定的偏好，没有高低；能力用徽章单独记。这个游戏不比谁赚得多，比的是你怎么做决定。

> 1720 年南海泡沫，相传牛顿也亏了约 2 万英镑。连他都算不出人们的疯狂。

## 配件

- 主棋盘 1 张（A2，可以拼成 4 块 A4）
- 场景牌、揭幕牌各 4 张（P1 再加 2 张）
- 证据牌 12 张、锦囊牌 4 张、快进牌 6 张
- 机会牌 12、补测牌 6、规则牌 10、数据港口牌 8、任务牌 12、AI 物种牌 6
- 物种牌 7、序章牌 1、速查卡 5
- 徽章牌 12、负债牌 8
- 玩家板 5、AI 板 1、委托单 4 本、终局档案卡 1 本
- 开户排队条、卖出窗口、抱团圈
- 棋子、物种币、研究点、认出令牌、跌停锁、资金和方法星标记
- 骰子 2 颗、30 秒沙漏 1 个

## 准备

1. 展开主棋盘。四条边是四季，左上角是总起点。
2. 每季的门 A 放这一季的场景牌，门牌面朝上，只显示一句提示。
3. 每个名场面的证据牌、锦囊牌、快进牌、揭幕牌背面朝上，放在棋盘中央的名场面牌位旁边。
4. 机会牌、规则牌、数据港口牌、补测牌分别洗匀，放到中央的牌位上。
5. 每人拿一块玩家板、一枚棋子。资金标记放在 20，方法星放在 0，拿 1 个研究点，棋子放在总起点。
6. 序章：一人朗读序章牌。每人在终局档案卡上偷偷圈一个“我觉得我是”。
7. 最近一次打开行情软件的人当起始玩家。

## 一季怎么走

每一季大约 10 分钟。

1. **领预算**：每人拿 1 研究点。
2. **赶路**：从起始玩家开始，每人掷两颗骰子，选其中一个点数，从本季起点往前走。1–5 落在对应的小格，执行格子效果；6 直接走到门口，再拿 1 研究点。
3. **名场面**：全员一起进门，走完六步。
4. **驿站**：每人拿一枚本季的物种币，棋子走到下一季起点，起始玩家换成左手边的人。

## 名场面六步

1. **盲入场**。翻开场景牌，一人朗读。上面有一张起点为 100 的走势图、三句处境、四个选项和每个选项的仓位。觉得认出来了的人，在委托单上写下事件名，把认出令牌放到玩家板上。
2. **开证据**。从起始玩家开始轮流，每轮每人可以花 1 研究点看一张：量价、数据、消息三张证据牌，或者猫头鹰的锦囊。拿起来自己看，看完扣回原处；也可以扫背面的码在手机上看。在委托单上勾看了哪些、第一张看的是哪张。
3. **做决定**。在委托单上勾选项、理由和计划，扣在玩家板上。手里有规则牌的，可以在理由里写规则牌的名字，这时必须照规则做。场景牌上写着“依次明选”的，按座位顺序公开选项。
4. **亮牌**。倒数三二一，一起翻开委托单。
5. **快进**。翻开快进牌，按牌上的事件结算第一段收益，然后在委托单的快进栏再决定一次：持有、卖出或加仓。勾了计划的人必须照计划做。
6. **揭幕**。翻开揭幕牌，结算第二段收益，记方法星，在委托单上记下本季物种图标。

> 示例：小林先看了量价，又看了数据，勾了 C 降到无杠杆，理由“数据”，计划“跌了就走”。快进牌写着“本段算跌了”，他照计划卖出。他这一场拿到 2 + 1 + 1 = 4 颗方法星。

**认出来了怎么办**：这一场你的收益不按自己的选择算，而是记全桌其他人的平均值（四舍五入）。揭幕时事件名写对，记一次“金融史”。这一季的物种币放空心面朝上，只算半枚。

## 小格子

| 格子 | 怎么玩 |
|---|---|
| ① 补给站 | 拿 1 研究点 |
| ② 机会 | 抽一张机会牌二选一，看牌底你那个答案对应的物种图标 |
| ③ 研究所 | 摸两张规则牌，留一张 |
| ④ 数据港口 | 读代码答题，答案倒印在牌底；答对拿 1 研究点 |
| ⑤ 冷静亭 | 坐下：这一季不能选 A，但可以免费看一张证据。不坐：马上再掷一次 |

## 两本账

**收益账**。资金从 20 开始。每个选项对应 0–3 份仓位；快进牌和揭幕牌上印着这一段每份仓位涨跌多少资金。资金低于 0 叫穿仓，拿一张负债牌。

**方法账**。每场最多 4 颗星，和赚没赚钱无关：看了证据 1 颗，看了两张及以上不同的证据 2 颗；理由一致 1 颗；计划照做 1 颗。

## 驿站与物种币

数一数这一季委托单上的物种图标，拿一枚最多的那种物种币，放到玩家板上这一季的格子里。

- 理由：量价对应猎豹，数据对应大象，消息和跟别人对应狐獴，规则牌对应狐狸。理由图标算 2 个。
- 选了观望类选项、理由又不是直觉或看不懂：理由图标改成猫头鹰。
- 第一张看的证据：量价猎豹，数据大象，消息狐獴。
- 平局：抽一张补测牌回答。不同意：说一句理由，同样抽补测牌。

## 终局

1. **定物种**：数四枚币，空心算半枚。最多那种有 3.5–4 枚：很确定；2.5–3 枚：比较确定；2 枚且没有并列：初步；并列：待确认。
2. **发徽章**：证据控、说到做到、金融史达人、数据手、规则派、看懂风险。
3. **算胜负**：终局分 = 方法星 + 收益名次分（第一 6、第二 4、第三 2、其余 1、穿仓 0）。
4. **两个你**：把自评的物种和你的物种牌并排放，在终局档案卡上答两道现实题。
5. **领任务牌**：按终局档案卡上的决策树拿一张任务牌，扫码开始。

## 单人规则

选两张 AI 物种牌当对手。AI 不走棋、不拿研究点，资金同样从 20 开始。亮牌后看 AI 物种牌上它这一场的选择，按同样的收益表给它记账。终局分高过两只 AI 就赢。

## 扫码玩法

扫码是加料，不是门票。证据牌背面的码可以私下看证据；揭幕牌的码让走势动起来；终局档案卡的码把纸上的记录变成完整画像。

## 常见问题

**认出来了还能玩吗？** 能。收益记全桌平均，物种币算半枚。

**资金跌到 0 以下怎么办？** 拿负债牌，继续玩。终局收益名次分记 0。

**投资者教育游戏，不构成投资建议。**
"""

QUICKSTART_MD = """# 快速入门 · 15 分钟快玩局

## 你要做什么

走进一个金融史名场面，在不知道是哪一年的情况下做一个决定，再看看当年发生了什么。

## 准备（2 分钟）

1. 只用夏季这一条边：把 2015 场景牌放在夏季门 A。
2. 每人拿玩家板、1 张委托单、2 个研究点；资金放在 20。
3. 证据牌、锦囊牌、快进牌、揭幕牌背面朝上，放在中央。

## 玩一场（10 分钟）

1. **盲入场**：一人朗读场景牌。
2. **开证据**：轮流花 1 研究点看一张证据，看完扣回去。
3. **做决定**：在委托单上勾选项、理由、计划，扣好。
4. **亮牌**：倒数三二一，一起翻。
5. **快进**：翻快进牌，结算第一段；想卖的人抢卖出窗口。
6. **揭幕**：翻揭幕牌，结算第二段，记方法星。

## 看看你是谁（3 分钟）

数一数委托单上的物种图标，最多的那个就是你这一场的物种。扫终局档案卡上的码，看完整画像和下一步。

投资者教育游戏，不构成投资建议。
"""


def main():
    (HERE / "scenes.json").write_text(json.dumps(scenes(), ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "decks.json").write_text(json.dumps(decks(), ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "rules-v1.md").write_text(RULES_MD, encoding="utf-8")
    (HERE / "quickstart.md").write_text(QUICKSTART_MD, encoding="utf-8")
    print("mock written")


if __name__ == "__main__":
    main()
