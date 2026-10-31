"""首页“按住坐一趟真实行情”用的三段指数日线（Panda Data get_index_daily）。

这三段都不和任何名场面重叠，不剧透：
  2007：上证从 2000 点出头涨到 6124，再跌回 1664
  2009：上证从 1664 反弹到 3478，再回落
  2019：上证春季行情，2440 到 3288，再回落

  python3.11 h5/scripts/fetch_ride_paths.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "data"))
from fetch_market import iso, panda_login, panda_range  # noqa: E402

RIDES = [
    {"id": "y2007", "code": "000001.SH", "name": "上证指数", "start": "2006-11-01", "end": "2008-11-04"},
    {"id": "y2009", "code": "000001.SH", "name": "上证指数", "start": "2008-11-04", "end": "2009-09-30"},
    {"id": "y2019", "code": "000001.SH", "name": "上证指数", "start": "2018-12-20", "end": "2019-08-15"},
]


def main():
    pd_ = panda_login()
    out = {"source": "Panda Data 指数日线（get_index_daily）", "api": "get_index_daily", "rides": []}
    for r in RIDES:
        df = panda_range(pd_.get_index_daily, r["start"], r["end"], symbol=r["code"])
        rows = sorted(({"d": iso(x.date), "c": round(float(x.close), 2)} for x in df.itertuples()), key=lambda x: x["d"])
        rows = [x for x in rows if r["start"] <= x["d"] <= r["end"]]
        closes = [x["c"] for x in rows]
        hi = max(range(len(closes)), key=lambda i: closes[i])
        print(f"{r['id']}: {len(rows)} 天 {rows[0]['d']} {closes[0]} → 高点 {rows[hi]['d']} {closes[hi]} → {rows[-1]['d']} {closes[-1]}")
        out["rides"].append({**r, "dates": [x["d"] for x in rows], "close": closes})
    dst = ROOT / "h5" / "src" / "ride" / "paths.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("写入", dst.relative_to(ROOT), dst.stat().st_size, "字节")


if __name__ == "__main__":
    main()
