"""读取内容：content/ 下有真文件就用真文件，没有就用 print/mock/ 的假数据。只读，不改别人的文件。"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .paths import CONTENT, MOCK

SOURCES: dict[str, str] = {}
NOTES: list[str] = []  # 内容问题（缺字段、太长被缩写），写进最终报告


def _pick(name: str) -> Path:
    real = CONTENT / name
    if real.exists() and real.stat().st_size > 0:
        SOURCES[name] = "content"
        return real
    SOURCES[name] = "mock"
    return MOCK / name


def load_json(name: str):
    p = _pick(name)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        NOTES.append(f"{name} 解析失败（{e}），改用假数据")
        SOURCES[name] = "mock(解析失败)"
        return json.loads((MOCK / name).read_text(encoding="utf-8"))


def load_text(name: str) -> str:
    return _pick(name).read_text(encoding="utf-8")


def g(d, *keys, default=None):
    """按多个候选字段名取值（内容设计师的字段名以文件为准）。"""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return default


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [s for s in re.split(r"\n+", v) if s.strip()]
    return [v]


# ---------------- scenes ----------------

def scenes() -> dict:
    d = load_json("scenes.json")
    out = {s["id"]: s for s in d.get("scenes", [])}
    for s in out.values():
        s.setdefault("evidence", {})
        s.setdefault("options", [])
        rv = s.setdefault("reveal", {})
        ch = rv.setdefault("chart", {})
        if "t_index" not in ch:
            for m in ch.get("marks", []):
                if "决策" in str(m.get("label", "")):
                    ch["t_index"] = m.get("i")
                    break
    d["_by_id"] = out
    return d


# ---------------- decks ----------------

def decks() -> dict:
    return load_json("decks.json")


def deck_list(decks: dict, *names) -> list:
    for n in names:
        v = decks.get(n)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            for k in ("cards", "items", "list"):
                if isinstance(v.get(k), list):
                    return v[k]
    return []


def all_text_blob() -> str:
    """所有内容里出现过的字（给字体子集化用）。"""
    parts = []
    for n in ("scenes.json", "decks.json", "rules-v1.md", "quickstart.md"):
        p = CONTENT / n
        if p.exists():
            parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        q = MOCK / n
        if q.exists():
            parts.append(q.read_text(encoding="utf-8", errors="ignore"))
    return "".join(parts)
