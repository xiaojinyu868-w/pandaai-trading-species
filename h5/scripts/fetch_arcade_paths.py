"""主线小游戏用的四段真实行情（开盘价和收盘价）。

和名场面用同一只标的、同一个结束日；往前多取一段，让玩家先经历行情是怎么热起来的。
纳斯达克100 不在 Panda Data 里，沿用名场面数据里那 31 天（公开接口）。

  python3.11 h5/scripts/fetch_arcade_paths.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data"))
from fetch_market import iso, panda_login, panda_range  # noqa: E402

LEVELS = [
    {"id": "s924", "api": "get_index_daily", "symbol": "000001.SH", "name": "上证指数", "start": "2024-09-02", "end": "2024-11-11"},
    {"id": "s2015", "api": "get_index_daily", "symbol": "000001.SH", "name": "上证指数", "start": "2015-03-02", "end": "2015-07-20"},
    {"id": "smt", "api": "get_stock_daily_pre", "symbol": "600519.SH", "name": "贵州茅台（前复权）", "start": "2020-11-02", "end": "2021-03-24"},
]


def main():
    pd_ = panda_login()
    scenes = {s["id"]: s for s in json.loads((ROOT / "h5" / "src" / "data" / "scenes.json").read_text())["scenes"]}
    out = {"source": "Panda Data 日线（get_index_daily、get_stock_daily_pre）；纳斯达克100 为公开接口", "levels": {}}
    for lv in LEVELS:
        df = panda_range(getattr(pd_, lv["api"]), lv["start"], lv["end"], symbol=lv["symbol"])
        rows = sorted(({"d": iso(x.date), "o": round(float(x.open), 2), "c": round(float(x.close), 2)} for x in df.itertuples()), key=lambda x: x["d"])
        rows = [x for x in rows if lv["start"] <= x["d"] <= lv["end"]]
        days = scenes[lv["id"]]["path"]["days"]
        tail = {d["date"]: d for d in days}
        bad = [x["d"] for x in rows if x["d"] in tail and abs(x["c"] / tail[x["d"]]["close"] - 1) > 0.002]
        closes = [x["c"] for x in rows]
        hi = max(range(len(closes)), key=lambda i: closes[i])
        print(f"{lv['id']}: {len(rows)} 天 {rows[0]['d']} {closes[0]} → 高点 {rows[hi]['d']} {closes[hi]} → {rows[-1]['d']} {closes[-1]}" + (f"  和名场面不一致：{bad[:5]}" if bad else "  和名场面一致"))
        out["levels"][lv["id"]] = {"code": lv["symbol"], "name": lv["name"], "api": lv["api"], "dates": [x["d"] for x in rows], "open": [x["o"] for x in rows], "close": closes}
    cb = scenes["scb"]["path"]
    out["levels"]["scb"] = {
        "code": "NDX", "name": cb["instrument"], "api": "public",
        "dates": [d["date"] for d in cb["days"]], "open": [round(d["open"], 2) for d in cb["days"]], "close": [round(d["close"], 2) for d in cb["days"]],
    }
    dst = ROOT / "h5" / "src" / "arcade" / "paths.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("写入", dst.relative_to(ROOT), dst.stat().st_size, "字节")


if __name__ == "__main__":
    main()
