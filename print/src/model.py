"""把 scenes.json 和 decks.json 合成排版用的数据模型（只读）。"""

from __future__ import annotations

import re

from . import content
from .content import g
from .tokens import SEASON, SPECIES_ORDER

SCENE_ORDER = ["s924", "s2015", "smt", "scb", "squant", "soil"]
SEASON_OF = {"春": "spring", "夏": "summer", "秋": "autumn", "冬": "winter"}
SEASON_EN = {"spring": "SPRING", "summer": "SUMMER", "autumn": "AUTUMN", "winter": "WINTER"}
SEASON_EN2 = {"spring": "ENTRY", "summer": "MANIA", "autumn": "LOOSENING", "winter": "CRISIS"}


class Model:
    def __init__(self):
        self.S = content.scenes()
        self.D = content.decks()
        by = self.S["_by_id"]
        self.scenes = [by[s] for s in SCENE_ORDER if s in by]
        so = self.D.get("scene_options", {}) or {}
        teasers = {}
        for t in content.deck_list(self.D, "door_teasers"):
            teasers[(SEASON_OF.get(t.get("season"), t.get("season")), t.get("door"))] = t
        self.teasers = teasers
        for sc in self.scenes:
            sid = sc["id"]
            o = so.get(sid, {})
            opts = []
            src_opts = o.get("options") or []
            base = {x["key"]: x for x in sc.get("options", [])}
            for x in (src_opts or sc.get("options", [])):
                b = base.get(x["key"], {})
                opts.append({"key": x["key"], "text": g(x, "text", "label") or g(b, "label", "text"),
                             "shares": x.get("shares", b.get("shares", 0)),
                             "note": g(x, "note", "hint") or g(b, "hint", "note")})
            sc["opts"] = opts
            if src_opts and base:
                diff = [(x["key"], g(x, "text"), base.get(x["key"], {}).get("label")) for x in src_opts
                        if base.get(x["key"]) and g(x, "text") != base[x["key"]].get("label")]
                if diff:
                    content.NOTES.append(f"{sid} 选项文字两处不一致，牌面统一用 decks.json 的 scene_options："
                                         + "；".join(f"{k} “{a}”（scenes.json 为“{b}”）" for k, a, b in diff))
            mode = o.get("reveal_mode") or ("依次明选" if sc.get("decision_mode") == "sequential" else "同时暗选")
            sc["mode_cn"] = mode
            sc["start_note"] = o.get("start_note", "")
            sc["second_decision"] = o.get("second_decision")
            tz = teasers.get((sc["season"], sc.get("door", "A")))
            sc["door_teaser"] = (tz or {}).get("teaser") or sc.get("door_hint", "")
            sc["season_cn"] = sc.get("season_cn") or SEASON[sc["season"]]["cn"]
            sc["season_name"] = sc.get("season_name") or SEASON[sc["season"]]["name"]
        self.species = sorted(content.deck_list(self.D, "species"), key=lambda s: SPECIES_ORDER.index(s["id"]) if s["id"] in SPECIES_ORDER else 99)
        self.sp = {s["id"]: s for s in self.species}

    def scene(self, sid):
        return self.S["_by_id"][sid]

    def door_b(self, season):
        """返回 B 门：真实场景或预告。"""
        for sc in self.scenes:
            if sc["season"] == season and sc.get("door") == "B":
                return {"scene": sc, "teaser": sc["door_teaser"], "open": True, "tier": sc.get("tier")}
        t = self.teasers.get((season, "B"))
        if not t:
            for tz in self.S.get("teasers", []):
                if tz.get("season") == season and tz.get("door") == "B":
                    t = {"teaser": tz.get("door_hint"), "status": tz.get("status")}
        return {"scene": None, "teaser": (t or {}).get("teaser", ""), "open": False, "tier": (t or {}).get("tier", "P2")}


def short_source(s: str, limit: int = 46) -> str:
    """把 source_note 缩成一行“数据：……”。"""
    if not s:
        return ""
    s = re.sub(r"（[^）]*）", "", s)
    s = re.sub(r"\([^)]*\)", "", s)
    s = s.replace("公开日线接口", "公开日线").replace("数据中心", "").replace("为公开报道", "：公开报道")
    parts = [p.strip() for p in re.split(r"[；;。，]", s) if p.strip()]
    parts = [p for p in parts if not p.startswith("口径") and "收益为游戏化" not in p]
    out = "；".join(parts)
    if len(out) > limit:
        acc = []
        for p in parts:
            if len("；".join(acc + [p])) > limit:
                break
            acc.append(p)
        out = "；".join(acc) or parts[0][:limit]
    return out


def strip_teaser_prefix(t: str) -> str:
    return re.sub(r"^未开放\s*[·・]\s*", "", t or "")
