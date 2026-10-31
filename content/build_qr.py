"""二维码码表：印在物料上的 https://meetmind.online/ts/q/<短码> 指向 H5 里的哪一页。

短码由编号加盐做哈希得到，5 位，不含事件名，重跑结果不变。
输出：
  content/qr.json        印刷和内容用：短码、编号、落地页、印在哪
  h5/public/q-map.json   H5 用：短码 -> 落地页（nginx 对它不缓存，印好后还能改指向）
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://meetmind.online/ts/q/"
ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"
SALT = "origin-of-trading-species-2026"

P0_SCENES = ["s924", "s2015", "smt", "scb"]
P1_SCENES = ["squant", "soil"]
SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
TASK_TYPES = ["chart", "explore", "regime", "verify", "hypo", "risk"]
REAL_RULES = ["rule-ma520", "rule-ma52060", "rule-mom20", "rule-lowpb-roe"]


def code_for(key: str) -> str:
    n = int.from_bytes(hashlib.sha256((SALT + key).encode()).digest()[:8], "big")
    out = []
    for _ in range(5):
        n, r = divmod(n, len(ALPHABET))
        out.append(ALPHABET[r])
    return "".join(out)


def entries():
    yield "start", "/start", "规则书封底、快速入门卡：开局页", "P0"
    yield "record", "/record", "终局档案卡：照着纸面记录录入，生成完整画像", "P0"
    for tier, scenes in (("P0", P0_SCENES), ("P1", P1_SCENES)):
        for s in scenes:
            yield f"{s}-blind", f"/b/{s}", "场景牌盲测面：只看当时可见的内容", tier
            for kind, where in (("price", "量价证据牌背面"), ("data", "数据证据牌背面"), ("news", "消息证据牌背面"), ("tip", "锦囊牌背面")):
                yield f"{s}-{kind}", f"/e/{s}/{kind}", where, tier
            yield f"{s}-reveal", f"/r/{s}", "揭幕牌：动态揭幕", tier
    yield "scb-ff", "/ff/scb", "熔断快进牌：手机上的 15 秒熔断", "P1"
    for r in REAL_RULES:
        yield r, f"/rule/{r}", "规则牌（真实 Qube 模板）", "P0"
    for sp in SPECIES:
        yield f"sp-{sp}", f"/sp/{sp}", "物种牌背面：物种详情、两个你", "P0"
    for t in TASK_TYPES:
        for lv in ("basic", "adv"):
            yield f"task-{t}-{lv}", f"/task/{t}-{lv}", "任务牌：当场可玩的任务和 PandaAI 入口", "P0"
    for i in range(1, 9):
        yield f"dp-{i:02d}", f"/dp/dp-{i:02d}", "数据港口牌：在手机上改参数重跑", "P1"
    for i in range(1, 13):
        yield f"chance-{i:02d}", f"/c/chance-{i:02d}", "机会牌", "P1"
    for i in range(1, 7):
        yield f"retest-{i:02d}", f"/c/retest-{i:02d}", "补测牌", "P1"


def main():
    rows, seen = [], {}
    for key, route, where, tier in entries():
        c = code_for(key)
        if c in seen:
            raise SystemExit(f"短码冲突：{key} 与 {seen[c]}")
        seen[c] = key
        rows.append({"id": key, "code": c, "url": BASE + c, "route": route, "printed_on": where, "tier": tier})
    (ROOT / "content" / "qr.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    pub = ROOT / "h5" / "public"
    pub.mkdir(parents=True, exist_ok=True)
    (pub / "q-map.json").write_text(json.dumps({r["code"]: r["route"] for r in rows}, ensure_ascii=False, indent=0), encoding="utf-8")
    p0 = sum(r["tier"] == "P0" for r in rows)
    print(f"{len(rows)} 个码，其中 P0 {p0} 个 -> content/qr.json, h5/public/q-map.json")


if __name__ == "__main__":
    main()
