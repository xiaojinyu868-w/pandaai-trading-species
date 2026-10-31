#!/usr/bin/env python3.11
"""校验 content/decks.json。

检查：顶层键和牌堆数量、必填字段、id 唯一、物种 id 合法、牌面字数、二维码 id、
资源白名单、规则牌逻辑、AI 物种的选项与快进动作、数据港口代码与本机 panda_data SDK
的函数名和参数；和 scenes.json 的选项文字、门牌文字对一遍；
顺带检查 rules-v1.md、quickstart.md 的字数和禁用词。

只读本地文件：不导入 panda_data，不调用任何接口，不读任何凭据。
用法：python3.11 content/check_decks.py
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DECKS = HERE / "decks.json"
QR_FILE = HERE / "qr.json"
SCENES_FILE = HERE / "scenes.json"
RULES_EVAL_FILE = HERE / "rules_eval.json"
DOCS = {"rules-v1.md": (6000, 8000), "quickstart.md": (0, 900)}
SDK_DIR = Path("/usr/local/lib/python3.11/site-packages/panda_data")

SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
PUBLIC = SPECIES[:-1]
SCENES = ["s924", "s2015", "smt", "squant", "scb", "soil"]
REASONS = ["price", "data", "news", "follow", "gut", "lost", "rule"]
FF_ACTIONS = ["hold", "sell", "add", "enter"]
SECOND = ["add", "stop", "ignore"]
DIMENSIONS = ["时间尺度", "证据使用", "人群与消息", "规则化", "风险姿态", "等待理由"]
TASK_TYPES = ["chart", "explore", "regime", "verify", "hypo", "risk"]
KINDS = ["QuantSkills 技能", "QuantSkills 智能体", "PandaAI 产品", "PandaAI 赛事", "开源工具"]
IN_GAME_ONLY = "游戏里的表现，仅供参考"
DIFFICULTY = {"cheetah": "入门", "meerkat": "入门", "owl": "进阶", "elephant": "进阶", "fox": "中等", "chameleon": "中等"}
REAL_RULES = {
    "rule-ma520": "茅台 5/20 双均线",
    "rule-ma52060": "多均线趋势过滤 MA5/20/60",
    "rule-mom20": "20 日动量",
    "rule-lowpb-roe": "低 PB + 高 ROE 复合",
}
RETEST_PAIRS = [{"cheetah", "fox"}, {"elephant", "owl"}, {"meerkat", "cheetah"},
                {"fox", "elephant"}, {"owl", "meerkat"}, {"chameleon", "other"}]
LOGIC = {
    "ma_cross": {"fast", "slow"},
    "ma_trend": {"windows"},
    "momentum": {"window"},
    "stop_loss": {"pct"},
    "take_profit": {"pct"},
    "buy_dip": {"pct"},
    "valuation": {"sell_above_pct", "buy_below_pct"},
    "position_cap": {"max_shares"},
    "wait": {"days"},
    "volume_breakout": {"mult"},
    "fundamental_screen": {"desc"},
}
TOP_KEYS = ["meta", "scene_options", "species", "badges", "chance", "retest", "rules", "dataport",
            "tasks", "ai_species", "quickref", "prologue", "debt", "station", "self_and_real",
            "door_teasers", "resources"]
COUNTS = {"species": 7, "badges": 6, "chance": 12, "retest": 6, "rules": 10, "dataport": 8,
          "tasks": 12, "ai_species": 6, "door_teasers": 8}
LIMIT = {"standard": 70, "a6": 160, "mini": 50, "ai_line": 40, "prologue": 150, "tagline": 8}

PANDA = "https://www.pandaaiquant.com"
QS = "https://www.quantskills.ai"
SKILLS = [
    "skill-trading-behavior-diagnostics", "skill-qbti", "skill-ma-crossover-signal",
    "skill-build-b10-factor-evaluation", "skill-a-share-stock-dossier", "skill-index-valuation-rotation",
    "skill-news-sentiment-analyst", "skill-a-share-market-risk-radar", "skill-northbound-margin-monitor",
    "skill-a-share-tradability-auditor", "skill-pandadata-api", "skill-backtesting-bias-avoidance",
    "skill-backtest-overfit", "skill-futures-roll-auditor", "skill-futures-deepview-analyst",
    "skill-oil-brief", "skill-factor-decay", "skill-capital-flow-crowding-monitor", "skill-trade-review",
    "skill-keynes-contrarian-investment", "skill-serenity-research-model",
    "skill-quant-factor-skill-factory", "skill-market-regime-analysis", "skill-kline-pattern-vision",
    "skill-risk-return-metrics", "skill-b11-auto-stop-loss-take-profit",
]
AGENTS = ["agent-market-regime-monitor", "agent-crowding-risk-monitor", "agent-quant-failure-triage",
          "agent-correlation-break-research", "agent-cross-market-event-radar"]
URL_WHITELIST = {
    f"{PANDA}/agent_quant/", f"{PANDA}/evo", f"{PANDA}/docs/evo", f"{PANDA}/docs/a2a-office",
    f"{PANDA}/quantfactor-center", f"{PANDA}/quantflow/", f"{PANDA}/learninghub/newcourse",
    f"{PANDA}/docs/api", f"{PANDA}/contest/", f"{PANDA}/factorhub/fourthFactorCompetition/",
    f"{PANDA}/data-service",
    "https://github.com/quantskills/QuantStudio", "https://gitee.com/quantskills/QuantStudio",
    *(f"{QS}/skills/{s}" for s in SKILLS), *(f"{QS}/agents/{a}" for a in AGENTS),
}

FORBIDDEN = ["大富翁", "monopoly", "熊猫"]
NO_ADVICE = ["稳赚", "必涨", "保本保收益", "保证收益", "一定会涨", "肯定涨", "闭眼买", "抄底必赚"]
EVENT_WORDS = ["924", "2015", "2020", "2021", "2024", "2025", "股灾", "茅台", "熔断", "原油宝", "踩踏",
               "DeepSeek", "GameStop", "新冠", "疫情", "白酒", "负油价", "微盘", "逼空"]
SECRET = re.compile(r"(?i)password|passwd|secret_key|api_key|/root/\.config|PANDA_?DATA_?(USER|PASS|TOKEN|ACCOUNT)")

errors: list[str] = []
warns: list[str] = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warns.append(f"{where}: {msg}")


def n(*parts) -> int:
    """牌面字数：非空白字符，中英文、数字、标点各算 1。"""
    text = "".join("".join(p) if isinstance(p, list) else (p or "") for p in parts)
    return len(re.sub(r"\s", "", text))


def limit(where, count, cap):
    if count > cap:
        err(where, f"{count} 字，超过 {cap}")


def need(obj, fields, where, nullable=()):
    ok = True
    for f in fields:
        if f not in obj:
            err(where, f"缺字段 {f}")
            ok = False
        elif obj[f] in (None, "", [], {}) and f not in nullable:
            err(where, f"字段 {f} 为空")
            ok = False
    return ok


def strings(obj):
    """递归取出所有字符串（含键路径），用来做全文扫描。"""
    if isinstance(obj, str):
        yield "", obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            for path, s in strings(v):
                yield f"{k}.{path}" if path else k, s
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for path, s in strings(v):
                yield f"[{i}].{path}" if path else f"[{i}]", s


# ---------------------------------------------------------------- SDK（只做 AST 解析）

def load_sdk():
    init = SDK_DIR / "__init__.py"
    if not init.exists():
        return None
    exports = {}
    for node in ast.parse(init.read_text(encoding="utf-8")).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name)):
            exports[node.targets[0].id] = (node.value.value.id, node.value.attr)
    funcs, trees = {}, {}
    for name, (mod, attr) in exports.items():
        path = SDK_DIR / "readers" / f"{mod}.py"
        if not path.exists():
            continue
        if mod not in trees:
            trees[mod] = ast.parse(path.read_text(encoding="utf-8"))
        for fn in trees[mod].body:
            if isinstance(fn, ast.FunctionDef) and fn.name == attr:
                a = fn.args
                funcs[name] = {
                    "params": [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs],
                    "deprecated": "WARNING" in (ast.get_docstring(fn) or ""),
                    "where": f"readers/{mod}.py:{attr}",
                }
    return funcs


SYMBOL_RE = {
    "stock": re.compile(r"^\d{6}\.(SH|SZ)$"),
    "index": re.compile(r"^(H\d{5}|\d{6}|399\d{3})\.(SH|SZ)$"),
    "fund": re.compile(r"^[F\d]+\.(OF|SZ|SH)$"),
    "future": re.compile(r"^([A-Z]+_DOMINANT|[A-Z]+\d{4})\.[A-Z]+$"),
}
SYMBOL_KIND = {
    "get_stock_daily": "stock", "get_stock_daily_post": "stock", "get_stock_daily_pre": "stock",
    "get_margin": "stock", "get_index_daily": "index", "get_index_indicator": "index",
    "get_fund_daily": "fund", "get_future_daily": "future",
}
MAX_DAYS = {"get_stock_daily": 1827, "get_stock_daily_post": 1827, "get_index_daily": 1827,
            "get_factor": 1827, "get_fund_daily": 366}


def literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def check_code(card, sdk):
    where = card.get("id", "dataport?")
    code = card.get("code")
    if not isinstance(code, list) or not all(isinstance(x, str) for x in code):
        err(where, "code 要写成字符串数组（一行一个）")
        return
    if len(code) > 8:
        err(where, f"代码 {len(code)} 行，超过 8 行")
    src = "\n".join(code)
    if '"' in src:
        warn(where, "代码里有双引号，牌面统一用单引号")
    if SECRET.search(src) or re.search(r"init_token\([^)]", src):
        err(where, "代码里不能出现账号、密码或带参数的 init_token")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        err(where, f"代码不能解析：{e}")
        return
    if not any(isinstance(x, ast.Import) and any(a.name == "panda_data" for a in x.names) for x in tree.body):
        err(where, "缺 import panda_data")
    called = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "panda_data"):
            continue
        fname = node.func.attr
        called.append(fname)
        if sdk is None:
            continue
        if fname not in sdk:
            err(where, f"panda_data.{fname} 不在本机 SDK 里")
            continue
        info = sdk[fname]
        if info["deprecated"]:
            warn(where, f"panda_data.{fname} 在 SDK 里标着“已废弃或未上线”（{info['where']}），印刷前请确认服务端支持")
        if node.args:
            warn(where, f"{fname} 用了位置参数，牌面建议全写成关键字参数")
        kws = {}
        for kw in node.keywords:
            if kw.arg is None:
                err(where, f"{fname} 不要用 **kwargs")
            elif kw.arg not in info["params"]:
                err(where, f"{fname} 没有参数 {kw.arg}（可用：{', '.join(info['params'])}）")
            else:
                kws[kw.arg] = literal(kw.value)
        dates = {}
        for k in ("start_date", "end_date", "date"):
            if k in kws:
                v = kws[k]
                try:
                    dates[k] = dt.datetime.strptime(v, "%Y%m%d").date()
                except (TypeError, ValueError):
                    err(where, f"{fname} 的 {k}={v!r} 不是 YYYYMMDD")
        if "start_date" in dates and "end_date" in dates:
            span = (dates["end_date"] - dates["start_date"]).days
            if span < 0:
                err(where, f"{fname} 的 end_date 早于 start_date")
            elif fname in MAX_DAYS and span > MAX_DAYS[fname]:
                err(where, f"{fname} 时间跨度 {span} 天，超过接口上限")
        kind = SYMBOL_KIND.get(fname)
        if kind and "symbol" in kws:
            syms = kws["symbol"] if isinstance(kws["symbol"], (list, tuple)) else [kws["symbol"]]
            for s in syms:
                if not isinstance(s, str) or not SYMBOL_RE[kind].match(s):
                    err(where, f"{fname} 的 symbol {s!r} 格式不对")
        if fname == "get_margin" and kws.get("margin_type") not in (None, "stock", "cash"):
            err(where, "margin_type 只能是 'stock' 或 'cash'")
        if "exchange" in kws and fname in ("get_prev_trade_date", "get_trade_cal") and kws["exchange"] not in ("SH", "HK", "US"):
            err(where, "exchange 只能是 SH / HK / US")
    if not called:
        err(where, "代码里没有调用 panda_data")
    if sorted(set(called)) != sorted(set(card.get("functions", []))):
        err(where, f"functions 字段 {card.get('functions')} 和代码实际调用 {sorted(set(called))} 不一致")


# ---------------------------------------------------------------- 各牌堆

def check_species(d, qr_ids, res_ids):
    ids = [s.get("id") for s in d["species"]]
    if ids != SPECIES:
        err("species", f"id 应依次为 {SPECIES}，现在是 {ids}")
    for s in d["species"]:
        w = f"species/{s.get('id')}"
        need(s, ["id", "name", "en", "tagline", "one_liner", "looks_like", "strength", "blind_spot",
                 "in_game_only", "recommend_direction", "qr", "hidden"], w, nullable=("hidden",))
        if n(s.get("tagline")) > LIMIT["tagline"]:
            err(w, f"tagline {n(s.get('tagline'))} 字，超过 8")
        if not isinstance(s.get("looks_like"), list) or len(s["looks_like"]) != 3:
            err(w, "looks_like 要 3 条")
        if s.get("in_game_only") != IN_GAME_ONLY:
            err(w, f"in_game_only 必须是“{IN_GAME_ONLY}”")
        if s.get("qr") != f"sp-{s.get('id')}" or s.get("qr") not in qr_ids:
            err(w, f"qr 应为 sp-{s.get('id')} 且在 qr.json 里")
        if s.get("hidden") is not (s.get("id") == "beaver"):
            err(w, "只有海狸 hidden 为 true")
        for r in s.get("recommend_resource_ids", []):
            if r not in res_ids:
                err(w, f"推荐资源 {r} 不在 resources 里")
        limit(f"{w} 正面", n(s.get("name"), s.get("tagline"), s.get("one_liner"), s.get("looks_like", [])), LIMIT["a6"])
        limit(f"{w} 背面", n(s.get("strength"), s.get("blind_spot"), s.get("in_game_only"), s.get("recommend_direction")), LIMIT["a6"])


def check_badges(d, res_ids):
    ids = [b.get("id") for b in d["badges"]]
    names = [b.get("name") for b in d["badges"]]
    want = ["证据控", "说到做到", "金融史达人", "数据手", "规则派", "看懂风险"]
    if sorted(names) != sorted(want):
        err("badges", f"徽章应为 {want}，现在是 {names}")
    for b in d["badges"]:
        w = f"badges/{b.get('id')}"
        need(b, ["id", "name", "condition", "meaning", "tip"], w)
        if not re.search(r"\d", b.get("condition", "")):
            err(w, "condition 要写成能数的条件（带次数）")
        limit(f"{w} 正面", n(b.get("name"), b.get("condition")), LIMIT["mini"])
        limit(f"{w} 背面", n(b.get("meaning")), LIMIT["mini"])
        for r in b.get("resource_ids", []):
            if r not in res_ids:
                err(w, f"资源 {r} 不在 resources 里")
    return ids


def check_chance(d, qr_ids):
    per_species, per_key = Counter(), Counter()
    dims = Counter()
    for i, c in enumerate(d["chance"], 1):
        w = f"chance/{c.get('id')}"
        if c.get("id") != f"chance-{i:02d}":
            err(w, f"id 应为 chance-{i:02d}")
        need(c, ["id", "dimension", "title", "prompt", "options", "back_note", "qr"], w)
        if c.get("dimension") not in DIMENSIONS:
            err(w, f"dimension 必须是 {DIMENSIONS} 之一")
        dims[c.get("dimension")] += 1
        if c.get("qr") != c.get("id") or c.get("qr") not in qr_ids:
            err(w, "qr 应等于 id 且在 qr.json 里")
        opts = c.get("options", [])
        if [o.get("key") for o in opts] != ["A", "B"]:
            err(w, "options 必须是 A、B 两项")
        for o in opts:
            if o.get("species") not in PUBLIC:
                err(w, f"选项 {o.get('key')} 的物种 {o.get('species')} 不合法（机会牌不给海狸）")
            per_species[o.get("species")] += 1
            per_key[(o.get("species"), o.get("key"))] += 1
            if not o.get("text"):
                err(w, f"选项 {o.get('key')} 没有文字")
        if len({o.get("species") for o in opts}) != len(opts):
            err(w, "两个选项不能给同一种物种")
        limit(f"{w} 正面", n(c.get("title"), c.get("prompt"), [o.get("text", "") for o in opts]), LIMIT["standard"])
        limit(f"{w} 背面", n(c.get("back_note")), LIMIT["standard"])
    for sp in PUBLIC:
        if per_species[sp] == 0:
            err("chance", f"没有一张机会牌会给 {sp}")
    if len(set(per_species[sp] for sp in PUBLIC)) > 1:
        warn("chance", f"物种分布不均：{dict(per_species)}")
    for dim in DIMENSIONS:
        if dims[dim] != 2:
            warn("chance", f"维度“{dim}”有 {dims[dim]} 张（建议每个维度 2 张）")
    return per_species, per_key


def check_retest(d, qr_ids):
    pairs = []
    for i, r in enumerate(d["retest"], 1):
        w = f"retest/{r.get('id')}"
        if r.get("id") != f"retest-{i:02d}":
            err(w, f"id 应为 retest-{i:02d}")
        need(r, ["id", "pair", "prompt", "options", "why", "qr"], w)
        pair = r.get("pair", [])
        pairs.append(set(pair))
        allowed = set(SPECIES) | ({"other"} if r.get("id") == "retest-06" else set())
        for sp in pair:
            if sp not in allowed:
                err(w, f"pair 里的 {sp} 不合法")
        opts = r.get("options", [])
        if not 2 <= len(opts) <= 3:
            err(w, "options 要 2–3 项")
        for o in opts:
            if o.get("species") not in allowed:
                err(w, f"选项 {o.get('key')} 的物种 {o.get('species')} 不合法")
            if o.get("species") not in pair:
                err(w, f"选项 {o.get('key')} 的物种不在这一对里")
        if r.get("qr") != r.get("id") or r.get("qr") not in qr_ids:
            err(w, "qr 应等于 id 且在 qr.json 里")
        limit(f"{w} 正面", n(r.get("prompt"), [o.get("text", "") for o in opts]), LIMIT["standard"])
        limit(f"{w} 背面", n(r.get("why")), LIMIT["standard"])
    for p in RETEST_PAIRS:
        if p not in pairs:
            err("retest", f"缺少易混对 {'/'.join(sorted(p))}")


def check_rules(d, qr_ids):
    ids = []
    for r in d["rules"]:
        w = f"rules/{r.get('id')}"
        ids.append(r.get("id"))
        need(r, ["id", "name", "text", "logic", "species", "is_real_template", "qr"], w,
             nullable=("qr", "is_real_template"))
        if r.get("species") != "fox":
            err(w, "规则牌的物种必须是 fox")
        real = r.get("id") in REAL_RULES
        if r.get("is_real_template") is not real:
            err(w, "is_real_template 与是否为四个真实模板不符")
        if real:
            if r.get("name") != REAL_RULES[r["id"]]:
                err(w, f"真实模板的名字必须是“{REAL_RULES[r['id']]}”")
            if r.get("qr") != r.get("id") or r.get("qr") not in qr_ids:
                err(w, "真实模板的 qr 应等于 id 且在 qr.json 里")
            if not r.get("qube_prompt"):
                err(w, "真实模板要有 qube_prompt")
        elif r.get("qr") is not None:
            err(w, "非真实模板的 qr 应为 null")
        if r.get("spoils") not in (None, *SCENES):
            err(w, f"spoils={r.get('spoils')} 不是名场面 id")
        logic = r.get("logic", {})
        t = logic.get("type")
        if t not in LOGIC:
            err(w, f"logic.type={t} 不在允许列表里")
        else:
            keys = set(logic) - {"type"}
            if keys != LOGIC[t]:
                err(w, f"{t} 的参数应为 {sorted(LOGIC[t])}，现在是 {sorted(keys)}")
            if t == "ma_cross" and not logic.get("fast", 0) < logic.get("slow", 0):
                err(w, "ma_cross 要 fast < slow")
            if t == "ma_trend" and logic.get("windows") != sorted(logic.get("windows", [])):
                err(w, "ma_trend 的 windows 要从短到长")
            for k in ("pct", "sell_above_pct", "buy_below_pct"):
                if k in logic and not 0 < logic[k] < 100:
                    err(w, f"{k} 要在 0–100 之间")
            if t == "valuation" and not logic["buy_below_pct"] < logic["sell_above_pct"]:
                err(w, "valuation 要 buy_below_pct < sell_above_pct")
            if t == "position_cap" and logic.get("max_shares") not in (0, 1, 2, 3):
                err(w, "max_shares 只能是 0–3")
        limit(w, n(r.get("name"), r.get("text")), LIMIT["standard"])
    real_count = sum(1 for r in d["rules"] if r.get("id") in REAL_RULES)
    if real_count != 4:
        err("rules", f"真实模板应为 4 张，现在 {real_count} 张")
    return ids


def check_dataport(d, qr_ids, res_ids, sdk):
    answers = Counter()
    for i, c in enumerate(d["dataport"], 1):
        w = f"dataport/{c.get('id')}"
        if c.get("id") != f"dp-{i:02d}":
            err(w, f"id 应为 dp-{i:02d}")
        need(c, ["id", "title", "code", "question", "options", "answer", "explain", "variant", "functions", "qr"], w)
        if c.get("qr") != c.get("id") or c.get("qr") not in qr_ids:
            err(w, "qr 应等于 id 且在 qr.json 里")
        opts = c.get("options", [])
        if [o.get("key") for o in opts] != ["A", "B", "C"]:
            err(w, "options 必须是 A、B、C 三项")
        if c.get("answer") not in ("A", "B", "C"):
            err(w, "answer 必须是 A、B、C 之一")
        answers[c.get("answer")] += 1
        v = c.get("variant", {})
        need(v, ["param", "from", "to", "what_you_see"], f"{w}.variant")
        for r in c.get("related_resource_ids", []):
            if r not in res_ids:
                err(w, f"资源 {r} 不在 resources 里")
        limit(f"{w} 正面（题目+选项）", n(c.get("question"), [o.get("text", "") for o in opts]), LIMIT["standard"])
        limit(f"{w} 背面（解析）", n(c.get("explain")), LIMIT["standard"])
        check_code(c, sdk)
    return answers


def check_tasks(d, qr_ids, res_by_id, placeholders):
    seen = set()
    for t in d["tasks"]:
        w = f"tasks/{t.get('id')}"
        need(t, ["id", "type", "level", "name", "for_whom", "card_text", "play_now", "resources",
                 "because_template", "not_now", "qr"], w)
        m = re.fullmatch(r"task-(\w+)-(basic|adv)", t.get("id", ""))
        if not m or m.group(1) not in TASK_TYPES:
            err(w, "id 应为 task-<type>-<level>")
        elif (m.group(1), m.group(2)) != (t.get("type"), t.get("level")):
            err(w, "type / level 与 id 不一致")
        seen.add((t.get("type"), t.get("level")))
        if t.get("qr") != t.get("id") or t.get("qr") not in qr_ids:
            err(w, "qr 应等于 id 且在 qr.json 里")
        steps = t.get("play_now", [])
        if not isinstance(steps, list) or not 2 <= len(steps) <= 5:
            err(w, "play_now 要写成 2–5 步")
        for r in t.get("resources", []):
            rw = f"{w}.resources/{r.get('id')}"
            need(r, ["name", "url", "kind", "is_real"], rw, nullable=("is_real",))
            if r.get("kind") not in KINDS:
                err(rw, f"kind={r.get('kind')} 不在 {KINDS} 里")
            if r.get("url") not in URL_WHITELIST:
                err(rw, f"url {r.get('url')} 不在真实资源清单里")
            if r.get("is_real") is True:
                top = res_by_id.get(r.get("id"))
                if not top:
                    err(rw, "真实资源要在 resources 里登记同一个 id")
                elif top["url"] != r.get("url") or top["kind"] != r.get("kind"):
                    err(rw, "url 或 kind 与 resources 里的登记不一致")
            elif r.get("is_real") is False:
                if "示例" not in r.get("name", ""):
                    err(rw, "is_real=false 的资源名里要标“示例”")
                if t.get("type") != "chart":
                    err(rw, "只有读图入门可以用 is_real=false 的示例资源")
            else:
                err(rw, "is_real 必须是 true / false")
        for ph in re.findall(r"\{[a-z_0-9]+\}", t.get("because_template", "")):
            if ph not in placeholders:
                err(w, f"占位符 {ph} 没有在 meta.placeholders 里说明")
        limit(f"{w} 牌面", n(t.get("card_text")), LIMIT["standard"])
    for tp in TASK_TYPES:
        for lv in ("basic", "adv"):
            if (tp, lv) not in seen:
                err("tasks", f"缺 task-{tp}-{lv}")


def shares_of(scene_opts, scene, key):
    for o in scene_opts.get(scene, {}).get("options", []):
        if o.get("key") == key:
            return o.get("shares")
    return None


def check_ai(d, rule_ids):
    scene_opts = d["scene_options"]
    species = [a.get("species") for a in d["ai_species"]]
    if sorted(species) != sorted(PUBLIC):
        err("ai_species", f"AI 物种应为除海狸外的 6 种，现在是 {species}")
    by_scene = {s: [] for s in SCENES}
    for a in d["ai_species"]:
        w = f"ai/{a.get('id')}"
        need(a, ["id", "species", "name", "difficulty", "voice", "card_text", "method_stars", "scenes"], w)
        if a.get("id") != f"ai-{a.get('species')}":
            err(w, "id 应为 ai-<species>")
        if DIFFICULTY.get(a.get("species")) != a.get("difficulty"):
            err(w, f"难度应为 {DIFFICULTY.get(a.get('species'))}")
        stars = a.get("method_stars", {})
        if sorted(stars) != sorted(SCENES):
            err(w, "method_stars 要覆盖六个名场面")
        for sc, v in stars.items():
            if not isinstance(v, int) or not 0 <= v <= 4:
                err(w, f"{sc} 的方法星 {v} 要是 0–4 的整数")
        scenes = a.get("scenes", {})
        if sorted(scenes) != sorted(SCENES):
            err(w, "scenes 要覆盖六个名场面")
        for sc, s in scenes.items():
            sw = f"{w}/{sc}"
            need(s, ["option", "reason", "ff_action", "line"], sw)
            opt, ff = s.get("option"), s.get("ff_action")
            if opt not in ("A", "B", "C", "D"):
                err(sw, "option 必须是 A–D")
            by_scene.setdefault(sc, []).append(opt)
            if s.get("reason") not in REASONS:
                err(sw, f"reason={s.get('reason')} 不合法")
            if s.get("reason") == "rule" and s.get("rule") not in rule_ids:
                err(sw, "reason=rule 时要写一个存在的规则牌 id")
            if ff not in FF_ACTIONS:
                err(sw, f"ff_action={ff} 不合法")
            cfg = scene_opts.get(sc, {})
            if ff not in cfg.get("ff_actions", FF_ACTIONS):
                err(sw, f"这一场快进不能 {ff}（只能 {cfg.get('ff_actions')}）")
            sh = shares_of(scene_opts, sc, opt)
            if sh is not None:
                if sh == 0 and ff in ("sell", "add"):
                    err(sw, f"0 份的选项不能 {ff}，要进场请用 enter")
                if sh == 0 and ff == "enter" and opt not in cfg.get("enter_options", []):
                    err(sw, f"选项 {opt} 快进时不能进场")
                if sh > 0 and ff == "enter":
                    err(sw, "已有仓位不能 enter，请用 add")
                if ff == "add" and sh >= 3:
                    err(sw, "已经 3 份，不能再加")
                after = sh + {"hold": 0, "sell": (-1 if sc == "scb" else -sh), "add": 1, "enter": 1}.get(ff, 0)
                if sc == "scb":
                    sec = s.get("second")
                    if sec not in SECOND:
                        err(sw, "冬 A 要写第二次决定 second（add / stop / ignore）")
                    elif sec == "add" and after >= 3:
                        err(sw, "已经 3 份，第二次决定不能补仓")
                    elif sec == "stop" and after == 0:
                        warn(sw, "手里 0 份时选止损没有意义，建议 ignore")
            if sc != "scb" and "second" in s:
                err(sw, "只有冬 A 有第二次决定")
            limit(f"{sw} 台词", n(s.get("line")), LIMIT["ai_line"])
        limit(f"{w} 牌面", n(a.get("card_text")), LIMIT["standard"])
    for sc, opts in by_scene.items():
        if len(set(opts)) < 3:
            err(f"ai/{sc}", f"六只 AI 只选了 {sorted(set(opts))}，要至少 3 种不同选项")
    return by_scene


def check_scene_options(d, scenes_json):
    so = d["scene_options"]
    for sc in SCENES:
        if sc not in so:
            err("scene_options", f"缺 {sc}")
            continue
        cfg = so[sc]
        w = f"scene_options/{sc}"
        need(cfg, ["season", "door", "tier", "reveal_mode", "start_shares", "options", "ff_actions"], w,
             nullable=("start_shares",))
        if [o.get("key") for o in cfg.get("options", [])] != ["A", "B", "C", "D"]:
            err(w, "options 要 A–D 四项")
        shares = [o.get("shares") for o in cfg.get("options", [])]
        if shares != sorted(shares, reverse=True):
            err(w, "份数要从 A 到 D 递减（A 最激进）")
        for path, s in strings(cfg):
            if re.search(r"(19|20)\d\d", s):
                err(w, f"{path} 出现年份，场景选项不能剧透：{s}")
        mp = d["meta"].get("rule_option_map", {}).get(sc)
        if not mp or any(v not in ("A", "B", "C", "D") for v in mp.values()):
            err(f"meta.rule_option_map/{sc}", "缺少或取值不合法")
        if scenes_json:
            src = scenes_json.get(sc)
            if not src:
                warn(w, "scenes.json 里没有这一场")
                continue
            for mine, theirs in zip(cfg.get("options", []), src.get("options", [])):
                if mine.get("shares") != theirs.get("shares"):
                    err(w, f"选项 {mine.get('key')} 份数与 scenes.json 不一致")
                if mine.get("text") != theirs.get("label"):
                    warn(w, f"选项 {mine.get('key')} 文字“{mine.get('text')}”≠ scenes.json“{theirs.get('label')}”")


def check_resources(d):
    res = d["resources"]
    ids = [r.get("id") for r in res]
    for k, c in Counter(ids).items():
        if c > 1:
            err("resources", f"id {k} 重复")
    by_id = {}
    for r in res:
        w = f"resources/{r.get('id')}"
        need(r, ["id", "name", "url", "kind", "one_line"], w)
        if r.get("kind") not in KINDS:
            err(w, f"kind={r.get('kind')} 不合法")
        if r.get("url") not in URL_WHITELIST:
            err(w, f"url {r.get('url')} 不在真实资源清单里")
        u = r.get("url", "")
        if "/skills/" in u and r.get("kind") != "QuantSkills 技能":
            err(w, "quantskills.ai/skills 的 kind 应为 QuantSkills 技能")
        if "/agents/" in u and r.get("kind") != "QuantSkills 智能体":
            err(w, "quantskills.ai/agents 的 kind 应为 QuantSkills 智能体")
        if ("github.com" in u or "gitee.com" in u) and r.get("kind") != "开源工具":
            err(w, "代码仓库的 kind 应为 开源工具")
        if r.get("id", "").startswith(("skill-", "agent-")) and not u.endswith("/" + r["id"]):
            err(w, "QuantSkills 资源的 id 要和网址里的 slug 一致")
        by_id[r.get("id")] = r
    return by_id


def check_misc(d, qr_ids, placeholders):
    qr = d["quickref"]
    limit("quickref 正面", n(qr["front"].get("title"), qr["front"].get("lines", [])), LIMIT["a6"])
    limit("quickref 背面", n(qr["back"].get("title"), qr["back"].get("note"), qr["back"].get("lines", [])), LIMIT["a6"])

    p = d["prologue"]
    need(p, ["read_aloud", "self_assessment"], "prologue")
    limit("prologue 朗读", n(p.get("read_aloud")), LIMIT["prologue"])
    limit("prologue 背面", n(p.get("self_assessment")), LIMIT["a6"])
    if "这个游戏不比谁赚得多" not in p.get("read_aloud", ""):
        err("prologue", "朗读词要引出“这个游戏不比谁赚得多”")
    if "1720" not in p.get("read_aloud", ""):
        err("prologue", "朗读词要写 1720 年")

    debt = d["debt"]
    need(debt, ["card_text", "end_rule"], "debt")
    limit("debt 正面", n(debt.get("card_text")), LIMIT["mini"])
    limit("debt 背面", n(debt.get("end_rule"), debt.get("flavor")), LIMIT["mini"])

    st = d["station"]["card"]
    limit("station 正面", n(st.get("front_title"), st.get("front", [])), LIMIT["a6"])
    limit("station 背面", n(st.get("back_title"), st.get("back", [])), LIMIT["a6"])
    if len(d["station"].get("corners", [])) != 4:
        err("station", "corners 要四个角")
    if "我不同意" not in "".join(st.get("back", [])):
        err("station", "背面要写“我不同意”怎么处理")

    sr = d["self_and_real"]
    if sorted(sr["self_assessment"].get("choices", [])) != sorted(PUBLIC):
        err("self_and_real", "自评要 6 个公开物种（不含海狸）")
    rq = sr.get("real_questions", [])
    prompts = {"real1": "现实里你上一次遇到大跌，实际做了什么", "real2": "你上一次买入的主要原因是什么"}
    if [q.get("id") for q in rq] != ["real1", "real2"]:
        err("self_and_real", "现实题要 real1、real2 两道")
    for q in rq:
        if prompts.get(q.get("id"), "") not in q.get("prompt", ""):
            err(f"self_and_real/{q.get('id')}", "题目措辞要和规定一致")
        if not 4 <= len(q.get("options", [])) <= 5:
            err(f"self_and_real/{q.get('id')}", "选项要 4–5 个")
        for o in q.get("options", []):
            if o.get("species") not in (None, *SPECIES):
                err(f"self_and_real/{q.get('id')}", f"物种 {o.get('species')} 不合法")
    for key, tpl in sr.get("two_you", {}).items():
        for ph in re.findall(r"\{[a-z_0-9]+\}", tpl):
            if ph not in placeholders:
                err(f"self_and_real.two_you/{key}", f"占位符 {ph} 没有在 meta.placeholders 里说明")

    teasers = d["door_teasers"]
    want = set(SCENES) | {"sds", "sgme"}
    if {t.get("scene") for t in teasers} != want:
        err("door_teasers", f"要覆盖 {sorted(want)}")
    for t in teasers:
        for wd in EVENT_WORDS:
            if wd.lower() in t.get("teaser", "").lower():
                err(f"door_teasers/{t.get('scene')}", f"门牌文字不能出现事件词“{wd}”")
        limit(f"door_teasers/{t.get('scene')}", n(t.get("teaser")), 24)

    slip = d.get("forms", {}).get("order_slip")
    if slip:
        for side in ("front", "back"):
            c = n(slip.get(f"{side}_title"), slip.get(side, []))
            if c > LIMIT["a6"] + 60:
                warn(f"forms.order_slip {side}", f"{c} 字，A6 表单偏挤")


def check_cross_scenes(d, scenes_raw):
    if not scenes_raw:
        return
    hints = {s["id"]: s.get("door_hint") for s in scenes_raw.get("scenes", [])}
    hints.update({t["id"]: t.get("door_hint") for t in scenes_raw.get("teasers", [])})
    for t in d["door_teasers"]:
        h = hints.get(t.get("scene"))
        if h and h != t.get("teaser"):
            warn(f"door_teasers/{t.get('scene')}", f"“{t.get('teaser')}”≠ scenes.json“{h}”")


def check_text(d, deck_ids, qr_ids):
    raw = json.dumps(d, ensure_ascii=False)
    for path, s in strings(d):
        low = s.lower()
        for wd in FORBIDDEN:
            if wd in low:
                err(f"decks.{path}", f"出现禁用词“{wd}”")
        for wd in NO_ADVICE:
            if wd in s:
                err(f"decks.{path}", f"出现带收益承诺的说法“{wd}”")
        if SECRET.search(s):
            err(f"decks.{path}", "疑似出现账号或凭据")
        for m in re.finditer(r"牛顿|我能算准天体", s):
            if "相传" not in s[max(0, m.start() - 40):m.start()]:
                err(f"decks.{path}", "提到牛顿或那句话时，前面要有“相传”")
    for u in re.findall(r"https?://[^\s\"'，。）)]+", raw):
        if u not in URL_WHITELIST:
            err("decks", f"出现清单外的网址 {u}")
    for path, s in strings(d):
        if path.endswith("qr") or path.split(".")[-1] == "qr":
            if s not in qr_ids:
                err(f"decks.{path}", f"二维码 id {s} 不在 qr.json 里")


def check_docs(qr_ids, deck_ids):
    out = {}
    for name, (lo, hi) in DOCS.items():
        path = HERE / name
        if not path.exists():
            warn(name, "文件还不存在，跳过")
            continue
        text = path.read_text(encoding="utf-8")
        visible = re.sub(r"(?m)^\s*(#{1,6}|>|[-*+]|\d+\.|\|)\s?", "", text)
        visible = re.sub(r"[|*`#>]|-{3,}|:?-{3,}:?", "", visible)
        nv, nr = n(visible), n(text)
        out[name] = (nv, nr, text.count("\n## ") + text.startswith("## "))
        if not lo <= nv <= hi:
            err(name, f"正文 {nv} 字（去掉 Markdown 符号），要求 {lo}–{hi}")
        low = text.lower()
        for wd in FORBIDDEN:
            if wd in low:
                err(name, f"出现禁用词“{wd}”")
        for wd in NO_ADVICE:
            if wd in text:
                err(name, f"出现带收益承诺的说法“{wd}”")
        if SECRET.search(text):
            err(name, "疑似出现账号或凭据")
        for m in re.finditer(r"牛顿|我能算准天体", text):
            if "相传" not in text[max(0, m.start() - 40):m.start()]:
                err(name, "提到牛顿或那句话时，前面要有“相传”")
        for u in re.findall(r"https?://[^\s\"'，。）)>\]]+", text):
            if u.rstrip("/") + "/" not in URL_WHITELIST and u not in URL_WHITELIST:
                err(name, f"出现清单外的网址 {u}")
        for tok in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", text):
            if tok not in qr_ids and tok not in deck_ids:
                err(name, f"`{tok}` 不是 qr.json 或 decks.json 里的 id")
        if name == "rules-v1.md":
            for must in ("Panda Data", "公开", "AI 生成", "投资建议"):
                if must not in text:
                    err(name, f"制作与数据说明里要写到“{must}”")
        if name == "quickstart.md" and "第一次玩只开门 A" not in text:
            err(name, "要有提示“第一次玩只开门 A”")
    return out


def main():
    d = json.loads(DECKS.read_text(encoding="utf-8"))
    qr_ids = {r["id"] for r in json.loads(QR_FILE.read_text(encoding="utf-8"))}
    scenes_raw = json.loads(SCENES_FILE.read_text(encoding="utf-8")) if SCENES_FILE.exists() else None
    scenes_json = {s["id"]: s for s in scenes_raw["scenes"]} if scenes_raw else None
    sdk = load_sdk()
    if sdk is None:
        warn("dataport", f"本机没找到 {SDK_DIR}，跳过 SDK 签名核对")

    for k in TOP_KEYS:
        if k not in d:
            err("decks", f"缺顶层键 {k}")
    if errors:
        report({}, sdk)
        return 1
    for k, c in COUNTS.items():
        if len(d[k]) != c:
            err(k, f"应为 {c} 张，现在 {len(d[k])} 张")
    if d["meta"].get("species_ids") != SPECIES:
        err("meta.species_ids", "与物种表不一致")
    placeholders = set(d["meta"].get("placeholders", {}))

    deck_ids = []
    for k in ("species", "badges", "chance", "retest", "rules", "dataport", "tasks", "ai_species"):
        deck_ids += [x.get("id") for x in d[k]]
    for k, c in Counter(deck_ids).items():
        if c > 1:
            err("ids", f"id {k} 在牌堆里重复出现 {c} 次")

    res_by_id = check_resources(d)
    res_ids = set(res_by_id)
    check_scene_options(d, scenes_json)
    check_species(d, qr_ids, res_ids)
    check_badges(d, res_ids)
    per_species, per_key = check_chance(d, qr_ids)
    check_retest(d, qr_ids)
    rule_ids = check_rules(d, qr_ids)
    if RULES_EVAL_FILE.exists():
        evaluated = json.loads(RULES_EVAL_FILE.read_text(encoding="utf-8")).get("rules", {})
        for rid in rule_ids:
            if rid not in evaluated:
                warn("rules_eval", f"{rid} 在 rules_eval.json 里还没有真实行情预算")
        for rid in evaluated:
            if rid not in rule_ids:
                warn("rules_eval", f"rules_eval.json 里的 {rid} 没有对应的规则牌")
    answers = check_dataport(d, qr_ids, res_ids, sdk)
    check_tasks(d, qr_ids, res_by_id, placeholders)
    by_scene = check_ai(d, set(rule_ids))
    check_misc(d, qr_ids, placeholders)
    check_cross_scenes(d, scenes_raw)
    check_text(d, set(deck_ids), qr_ids)

    used = set()
    for s in d["species"]:
        used |= set(s.get("recommend_resource_ids", []))
    for b in d["badges"]:
        used |= set(b.get("resource_ids", []))
    for c in d["dataport"]:
        used |= set(c.get("related_resource_ids", []))
    for t in d["tasks"]:
        used |= {r.get("id") for r in t.get("resources", []) if r.get("is_real")}
    used |= set(d["self_and_real"].get("resource_ids", []))
    used |= {"data-api-docs", "learninghub", "quantstudio-gitee"}
    for r in res_ids - used:
        warn("resources", f"{r} 登记了但没有牌用到")

    printed = {"sp-": "species", "chance-": "chance", "retest-": "retest", "dp-": "dataport", "task-": "tasks"}
    used_qr = {v for _, v in strings(d) if v in qr_ids}
    for q in sorted(qr_ids):
        if q.startswith(tuple(printed)) and q not in used_qr:
            warn("qr", f"qr.json 里的 {q} 没有对应的牌")
        if q.startswith("rule-") and q not in rule_ids:
            warn("qr", f"qr.json 里的 {q} 没有对应的规则牌")

    docs = check_docs(qr_ids, set(deck_ids))
    stats = {
        "counts": {k: len(d[k]) for k in COUNTS},
        "chance_species": {sp: per_species[sp] for sp in PUBLIC},
        "chance_ab": {sp: f"A{per_key[(sp, 'A')]}/B{per_key[(sp, 'B')]}" for sp in PUBLIC},
        "dataport_answers": dict(sorted(answers.items())),
        "ai_options": {sc: "".join(v) for sc, v in by_scene.items()},
        "ai_stars": {a["species"]: sum(a["method_stars"][s] for s in ("s924", "s2015", "smt", "scb"))
                     for a in d["ai_species"]},
        "docs": docs,
    }
    report(stats, sdk)
    return 1 if errors else 0


def report(stats, sdk):
    if stats:
        print("牌堆数量：", "，".join(f"{k} {v}" for k, v in stats["counts"].items()))
        print("机会牌物种分布：", stats["chance_species"], "A/B：", stats["chance_ab"])
        print("数据港口答案分布：", stats["dataport_answers"])
        print("AI 每场的选项（猎豹 狐獴 猫头鹰 大象 狐狸 变色龙）：", stats["ai_options"])
        print("AI 四场 P0 方法星合计：", stats["ai_stars"])
        for name, (nv, nr, heads) in stats["docs"].items():
            print(f"{name}：正文 {nv} 字（含 Markdown 符号 {nr}），二级标题 {heads} 个")
    print(f"SDK：{'已按 AST 解析 ' + str(len(sdk)) + ' 个导出函数' if sdk else '未解析'}")
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"结果：{len(errors)} 个错误，{len(warns)} 个提醒。" + ("通过。" if not errors else "未通过。"))


if __name__ == "__main__":
    sys.exit(main())
