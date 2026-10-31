"""取名场面要用的历史行情，存成 data/series/<名字>.json，供 content/build_scenes.py 计算。

两种来源，一条命令切换：
  python3.11 data/fetch_market.py --source panda   Panda Data（账号写在 /root/.config/panda_data/env，见 panda_source）
  python3.11 data/fetch_market.py                  没有 Panda Data 账号时的后备：公开行情接口（腾讯证券日线、东方财富数据中心两融与估值）
  python3.11 data/fetch_market.py --probe          只测试 Panda Data 能否登录、各接口有没有权限，不写文件

Panda Data 提供：A 股指数与个股日线、茅台前复权与估值因子、纳指 ETF 日线、上证指数估值、
全市场个股逐只统计（成交额、跌停、停牌家数）、上海原油期货各月合约。
仍用公开接口：美股指数、WTI 连续合约（Panda Data 不覆盖），两市融资余额（交易所口径）。

原始响应缓存在 data/raw/，重跑不再请求网络（加 --refresh 强制重取）。
每个序列都带 source 字段，牌面和 H5 按它标注数据来源。
"""

import argparse
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "series"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Referer": "https://gu.qq.com/"}

TENCENT = "腾讯证券公开日线接口"
EM_MARGIN = "东方财富数据中心（两融余额）"
EM_VALUE = "东方财富数据中心（个股估值）"

# 名字: (腾讯代码, 起, 止, 复权方式, 说明)
PRICE_SERIES = {
    "sse": ("sh000001", "2004-01-01", "2024-12-31", "", "上证指数"),
    "csi300": ("sh000300", "2019-01-01", "2024-12-31", "", "沪深300"),
    "chinext": ("sz399006", "2023-06-01", "2024-12-31", "", "创业板指"),
    "moutai": ("sh600519", "2011-01-01", "2024-12-31", "", "贵州茅台（不复权，显示真实股价）"),
    "moutai_qfq": ("sh600519", "2011-01-01", "2024-12-31", "qfq", "贵州茅台（前复权，算收益）"),
    "csi1000": ("sh000852", "2020-06-01", "2024-06-30", "", "中证1000"),
    "cn2000": ("sz399303", "2020-06-01", "2024-06-30", "", "国证2000"),
    "nasdaq_etf": ("sh513100", "2019-06-01", "2020-12-31", "qfq", "纳指ETF 513100（前复权）"),
    "ndx": ("us.NDX", "2019-01-01", "2020-12-31", "", "纳斯达克100"),
    "spx": ("us.INX", "1990-01-01", "2020-12-31", "", "标普500"),
}


def http_get(url: str, headers=None) -> str:
    req = urllib.request.Request(url, headers=headers or UA)
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))


def cached(key: str, url: str, refresh: bool, headers=None) -> str:
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / (key + ".txt")
    if f.exists() and not refresh:
        return f.read_text(encoding="utf-8")
    text = http_get(url, headers)
    f.write_text(text, encoding="utf-8")
    time.sleep(0.4)
    return text


def windows(start: str, end: str, years: int = 2):
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    while s <= e:
        w = min(dt.date(s.year + years, s.month, s.day) - dt.timedelta(days=1), e)
        yield s.isoformat(), w.isoformat()
        s = w + dt.timedelta(days=1)


def tencent_daily(code: str, start: str, end: str, fq: str, refresh: bool):
    rows = {}
    for a, b in windows(start, end):
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,{a},{b},640,{fq}"
        text = cached(f"tx_{code}_{fq or 'raw'}_{a}_{b}", url, refresh)
        data = json.loads(text).get("data")
        if not isinstance(data, dict):
            continue
        node = data.get(code, {})
        for r in node.get(f"{fq}day") or node.get("day") or []:
            rows[r[0]] = {"date": r[0], "open": float(r[1]), "close": float(r[2]), "high": float(r[3]),
                          "low": float(r[4]), "volume": float(r[5])}
    return [rows[k] for k in sorted(rows)]


def em_report(report: str, columns: str, filt: str, sort_col: str, key: str, refresh: bool):
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "reportName": report, "columns": columns, "filter": filt, "pageNumber": page, "pageSize": 500,
            "sortColumns": sort_col, "sortTypes": 1, "source": "WEB", "client": "WEB"})
        text = cached(f"em_{key}_{page}", "https://datacenter-web.eastmoney.com/api/data/v1/get?" + q, refresh,
                      {"User-Agent": UA["User-Agent"]})
        res = json.loads(text).get("result") or {}
        out += res.get("data") or []
        if page >= (res.get("pages") or 1):
            return out
        page += 1


def public_source(refresh: bool):
    series = {}
    for name, (code, a, b, fq, desc) in PRICE_SERIES.items():
        rows = tencent_daily(code, a, b, fq, refresh)
        series[name] = {"name": desc, "code": code, "fq": fq or "none", "source": TENCENT, "rows": rows}
        print(f"{name:12} {code:10} {len(rows):5} 行  {rows[0]['date'] if rows else '-'} ~ {rows[-1]['date'] if rows else '-'}")

    margin = em_report("RPTA_RZRQ_LSHJ", "DIM_DATE,RZYE,RQYE,RZMRE,RZRQYE,NEW,ZDF",
                       "(DIM_DATE>='2014-01-01')(DIM_DATE<='2015-12-31')", "DIM_DATE", "margin_2014_2015", refresh)
    series["margin"] = {
        "name": "沪深两市融资余额", "code": "RPTA_RZRQ_LSHJ", "fq": "none", "source": EM_MARGIN,
        "rows": [{"date": r["DIM_DATE"][:10], "rzye": r["RZYE"], "rqye": r.get("RQYE")} for r in margin]}
    print(f"{'margin':12} {'两融':10} {len(margin):5} 行")

    val = em_report("RPT_VALUEANALYSIS_DET", "TRADE_DATE,PE_TTM,PB_MRQ,CLOSE_PRICE",
                    '(SECURITY_CODE="600519")(TRADE_DATE>=\'2011-01-01\')(TRADE_DATE<=\'2021-12-31\')',
                    "TRADE_DATE", "val_600519", refresh)
    series["moutai_val"] = {
        "name": "贵州茅台估值（PE TTM、PB）", "code": "600519", "fq": "none", "source": EM_VALUE,
        "rows": [{"date": r["TRADE_DATE"][:10], "pe_ttm": r["PE_TTM"], "pb": r["PB_MRQ"], "close": r["CLOSE_PRICE"]}
                 for r in val if r.get("PE_TTM") is not None]}
    print(f"{'moutai_val':12} {'600519':10} {len(series['moutai_val']['rows']):5} 行")

    try:  # 原油宝（P1）只用来画盲测走势；连续合约在到期前已换月，负油价那天看不到，揭幕用公开报道的结算价
        url = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_t=/"
               "GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=CL&_=2020_4_21&source=web")
        text = cached("sina_CL", url, refresh, {"User-Agent": UA["User-Agent"], "Referer": "https://finance.sina.com.cn/"})
        body = json.loads(text[text.index("(") + 1:text.rindex(")")])
        rows = [{"date": r["date"], "open": float(r["open"]), "close": float(r["close"]), "high": float(r["high"]),
                 "low": float(r["low"]), "volume": 0.0} for r in body if "2019-06-01" <= r["date"] <= "2020-06-30"]
        series["wti_cont"] = {"name": "NYMEX 原油连续合约", "code": "CL", "fq": "none",
                              "source": "新浪财经公开接口（连续合约）", "rows": rows}
        print(f"{'wti_cont':12} {'CL':10} {len(rows):5} 行")
    except Exception as e:
        print("wti_cont 跳过：", type(e).__name__)
    return series


def panda_env():
    env = {}
    f = Path("/root/.config/panda_data/env")
    if f.exists():
        for line in f.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def panda_login():
    """用户名、密码只在进程里用，不打印、不落盘。"""
    import panda_data
    env = panda_env()
    user, pwd = env.get("PANDA_USERNAME"), env.get("PANDA_PASSWORD")
    if not (user and pwd):
        raise SystemExit("Panda Data 还没有密码：请在 /root/.config/panda_data/env 里追加一行 PANDA_PASSWORD=...")
    if len(user) == 11 and user.isdigit():  # 数据服务的账号写法是“86+手机号”，裸号会报“用户未注册”
        user = "86" + user
    kw = {"base_url": env["PANDA_BASE_URL"]} if env.get("PANDA_BASE_URL") else {}
    panda_data.init_token(user, pwd, **kw)
    return panda_data


# Panda Data 上对应的接口；字段名以接口实际返回为准，在 normalize 里统一成 date/open/close/high/low/volume。
# 前复权用 get_stock_daily_pre（等比复权）：腾讯接口的 qfq 是减去分红的差值复权，会把茅台两年涨幅算大。
PANDA_MAP = {
    "sse": ("get_index_daily", {"symbol": "000001.SH"}),
    "csi300": ("get_index_daily", {"symbol": "000300.SH"}),
    "chinext": ("get_index_daily", {"symbol": "399006.SZ"}),
    "moutai": ("get_stock_daily", {"symbol": "600519.SH"}),
    "moutai_qfq": ("get_stock_daily_pre", {"symbol": "600519.SH"}),
    "csi1000": ("get_index_daily", {"symbol": "000852.SH"}),
    "cn2000": ("get_index_daily", {"symbol": "399303.SZ"}),
    "nasdaq_etf": ("get_fund_daily", {"symbol": "513100.SH"}),
}
PANDA_FQ = {"get_stock_daily_pre": "qfq", "get_stock_daily_post": "post"}
PANDA_CN = {"get_index_daily": "指数日线", "get_stock_daily": "A 股日线", "get_stock_daily_pre": "A 股前复权日线",
            "get_fund_daily": "基金日线", "get_factor": "估值因子", "get_index_indicator": "指数估值",
            "get_future_daily": "期货日线"}


def panda_label(fn, extra=""):
    return f"Panda Data {PANDA_CN.get(fn, fn)}{extra}"


def ymd(d):
    return d.replace("-", "")


def iso(d):
    d = str(d)
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if d[:8].isdigit() else d[:10]


def panda_range(f, a, b, years=4, **kw):
    """日线类接口一次能取的跨度有限（A 股、指数 5 年，基金 1 年）：按自然年分段取，再拼起来。"""
    import pandas as pd
    parts, y = [], int(a[:4])
    while y <= int(b[:4]):
        parts.append(f(start_date=ymd(max(a, f"{y}-01-01")), end_date=ymd(min(b, f"{y + years - 1}-12-31")), **kw))
        y += years
    parts = [p for p in parts if p is not None and len(p)]
    if not parts:
        return None
    df = pd.concat(parts, ignore_index=True)
    return df.drop_duplicates(subset=[c for c in ("symbol", "date") if c in df.columns])


def market_day(pd_, d):
    """沪深两市个股一天的逐只统计：成交额、收盘在跌停价的家数、停牌家数。"""
    df = pd_.get_stock_daily(start_date=ymd(d), end_date=ymd(d))
    df = df[df["symbol"].str.endswith((".SH", ".SZ"))]
    on = df[df["trade_status"] == 0]
    return {"date": d, "n": int(len(df)), "amount": float(on["amount"].sum()),
            "limit_down": int((on["close"] <= on["limit_down"] + 1e-6).sum()),
            "limit_up": int((on["close"] >= on["limit_up"] - 1e-6).sum()),
            "suspended": int((df["trade_status"] != 0).sum())}


def panda_extras(pd_, series):
    """名场面里原来只能写“公开报道”、或者缺估值的地方，用 Panda Data 补上。"""
    close = {r["date"]: r["close"] for r in series["moutai"]["rows"]}
    df = panda_range(pd_.get_factor, "2017-01-01", "2021-12-31", symbol="600519.SH",
                     factors=["pe_ratio_ttm", "market_cap", "total_equity"])
    rows = [{"date": iso(r.date), "pe_ttm": float(r.pe_ratio_ttm), "close": close.get(iso(r.date)),
             "pb": float(r.market_cap) / float(r.total_equity) if r.total_equity else None}
            for r in df.itertuples() if r.pe_ratio_ttm == r.pe_ratio_ttm]
    rows.sort(key=lambda x: x["date"])
    series["moutai_val"] = {"name": "贵州茅台估值（PE TTM；PB = 总市值 ÷ 净资产）", "code": "600519.SH", "fq": "none",
                            "source": panda_label("get_factor"), "api": "get_factor", "rows": rows}
    print(f"{'moutai_val':12} Panda Data get_factor {len(rows)} 行  {rows[0]['date']} ~ {rows[-1]['date']}")

    df = pd_.get_index_indicator(symbol="000001.SH", start_date="20240101", end_date="20241231")
    rows = [{"date": iso(r.date), "pe_ttm": float(r.pe_ttm), "pb": float(r.pb_lf)} for r in df.itertuples()]
    series["sse_val"] = {"name": "上证指数估值（PE TTM、PB LF）", "code": "000001.SH", "fq": "none",
                         "source": panda_label("get_index_indicator"), "api": "get_index_indicator", "rows": sorted(rows, key=lambda x: x["date"])}
    print(f"{'sse_val':12} Panda Data get_index_indicator {len(rows)} 行")

    days = [r["date"] for r in series["sse"]["rows"]
            if "2015-06-12" <= r["date"] <= "2015-07-13" or "2024-09-24" <= r["date"] <= "2024-10-09"]
    rows = [market_day(pd_, d) for d in days]
    series["market_breadth"] = {"name": "沪深两市个股逐日统计（成交额、跌停、停牌）", "code": "A 股全市场", "fq": "none",
                                "source": panda_label("get_stock_daily", "逐只统计"), "api": "get_stock_daily", "rows": rows}
    print(f"{'market_breadth':12} Panda Data get_stock_daily 全市场 {len(rows)} 天")

    syms = [f"SC{(2020 + (4 + k) // 12) % 100:02d}{(4 + k) % 12 + 1:02d}.INE" for k in range(12)]
    df = pd_.get_future_daily(symbol=syms, start_date="20200417", end_date="20200417")
    rows = [{"date": iso(r.date), "symbol": r.symbol, "month": f"20{r.symbol[2:4]}-{r.symbol[4:6]}", "settlement": float(r.settlement),
             "close": float(r.close), "open_interest": float(r.open_interest)} for r in df.itertuples()]
    series["sc_curve"] = {"name": "上海原油期货各月合约结算价（2020-04-17）", "code": "SC", "fq": "none",
                          "source": panda_label("get_future_daily", "（上海原油 SC）"), "api": "get_future_daily",
                          "rows": sorted(rows, key=lambda x: x["month"])}
    print(f"{'sc_curve':12} Panda Data get_future_daily {len(rows)} 个合约")


def panda_source(refresh: bool):
    pd_ = panda_login()
    # 美股指数、WTI 连续合约 Panda Data 不覆盖；两融用交易所口径汇总（Panda Data 逐只加总不含部分品种，约少 9%）
    series = public_source(refresh)
    for name, (fn, kw) in PANDA_MAP.items():
        code, a, b, _, desc = PRICE_SERIES[name]
        try:
            rows = normalize(panda_range(getattr(pd_, fn), a, b, years=1 if fn.startswith("get_fund") else 4, **kw))
        except Exception as e:  # 权限不足等
            print(f"{name}: {fn} 调用失败（{type(e).__name__}），保留公开口径")
            continue
        if rows:
            series[name] = {"name": desc, "code": kw["symbol"], "fq": PANDA_FQ.get(fn, "none"),
                            "source": panda_label(fn), "api": fn, "rows": rows}
            print(f"{name:12} Panda Data {fn} {len(rows):5} 行  {rows[0]['date']} ~ {rows[-1]['date']}")
    panda_extras(pd_, series)
    return series


def normalize(df):
    if df is None or len(df) == 0:
        return []
    cols = {c.lower(): c for c in df.columns}
    pick = lambda *names: next((cols[n] for n in names if n in cols), None)
    c_date = pick("date", "trade_date", "datetime")
    out = []
    for _, r in df.iterrows():
        d = str(r[c_date])[:10]
        if len(d) == 8 and d.isdigit():
            d = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        vol = float(r[pick("volume", "vol")] or 0)
        if not vol:  # 停牌日 Panda Data 也给一行（价格等于前收盘），不算交易日
            continue
        out.append({"date": d, "open": float(r[pick("open")]), "close": float(r[pick("close")]),
                    "high": float(r[pick("high")]), "low": float(r[pick("low")]), "volume": vol})
    return sorted(out, key=lambda x: x["date"])


def probe():
    pd_ = panda_login()
    print("登录成功")
    checks = list(PANDA_MAP.values()) + [
        ("get_factor", {"symbol": "600519.SH", "factors": ["pe_ratio_ttm"]}),
        ("get_index_indicator", {"symbol": "000001.SH"}),
        ("get_stock_daily", {}),
        ("get_future_daily", {"symbol": ["SC2412.INE"]}),
    ]
    for fn, kw in checks:
        f = getattr(pd_, fn, None)
        label = str(kw.get("symbol", "全市场"))[:12]
        if f is None:
            print(f"  {fn:22} SDK 里没有这个函数")
            continue
        try:
            df = f(start_date="20240920", end_date="20240930", **kw)
            print(f"  {fn:22} {label:12} 可用，{len(df)} 行")
        except Exception as e:
            print(f"  {fn:22} {label:12} 不可用：{type(e).__name__} {str(e)[:80]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["public", "panda"], default="public")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    if a.probe:
        return probe()
    series = panda_source(a.refresh) if a.source == "panda" else public_source(a.refresh)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, s in series.items():
        s["fetched_at"] = dt.datetime.now().isoformat(timespec="seconds")
        (OUT / f"{name}.json").write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    print("写入", OUT)


if __name__ == "__main__":
    main()
