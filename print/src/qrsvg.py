"""二维码：按 qr.json 的 id 查 url，生成矢量 SVG（纠错 M，纯黑码白底）。不自己编码短链。"""

from __future__ import annotations

import json

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from .paths import CONTENT

_QR = {r["id"]: r for r in json.loads((CONTENT / "qr.json").read_text(encoding="utf-8"))}
USED: dict[str, list[str]] = {}  # id -> 印在哪些牌上


def reload():
    global _QR
    _QR = {r["id"]: r for r in json.loads((CONTENT / "qr.json").read_text(encoding="utf-8"))}


def url(qid: str) -> str:
    if qid not in _QR:
        raise KeyError(f"qr.json 里没有二维码 id：{qid}")
    return _QR[qid]["url"]


def exists(qid) -> bool:
    return bool(qid) and qid in _QR


def all_ids():
    return list(_QR.keys())


def info(qid):
    return _QR.get(qid)


def matrix(data: str):
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=0, box_size=1)
    q.add_data(data)
    q.make(fit=True)
    return q.get_matrix()


def svg(qid: str, size_mm: float = 20.0, where: str = "") -> str:
    """size_mm 是码区边长（不含留白）。外层留白由调用方的白底框负责（≥2 mm）。"""
    u = url(qid)
    USED.setdefault(qid, []).append(where)
    m = matrix(u)
    n = len(m)
    d = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                s = x
                while x < n and row[x]:
                    x += 1
                d.append(f"M{s} {y}h{x - s}v1h-{x - s}z")
            else:
                x += 1
    return (f'<svg width="{size_mm}mm" height="{size_mm}mm" viewBox="0 0 {n} {n}" shape-rendering="crispEdges" '
            f'data-qr="{qid}"><path fill="#000" d="{"".join(d)}"/></svg>')


def block(qid: str, left: float, top: float, size: float = 20.0, pad: float = 2.5, cap: str = "", cap2: str = "",
          where: str = "", radius: float = 1.2, cap_color: str = "#000") -> str:
    """白底码块：码区 size，四周留白 pad（≥2mm），下方可加一行或两行说明（在白底里）。返回绝对定位 html。"""
    cap_h = 0.0
    if cap:
        cap_h += 3.2
    if cap2:
        cap_h += 2.9
    W = size + 2 * pad
    H = size + 2 * pad + (cap_h + 0.4 if cap_h else 0)
    caps = ""
    if cap:
        caps += f'<div class="qrcap" style="top:{size + pad + 0.9:.2f}mm;color:{cap_color}">{cap}</div>'
    if cap2:
        caps += f'<div class="qrcap" style="top:{size + pad + 0.9 + 3.15:.2f}mm;font-weight:400;color:{cap_color}">{cap2}</div>'
    return (f'<div class="qrbox" style="left:{left:.2f}mm;top:{top:.2f}mm;width:{W:.2f}mm;height:{H:.2f}mm;border-radius:{radius}mm;">'
            f'<div style="position:absolute;left:{pad}mm;top:{pad}mm;width:{size}mm;height:{size}mm;">{svg(qid, size, where)}</div>{caps}</div>')


def block_size(size=20.0, pad=2.5, cap="", cap2=""):
    cap_h = (3.2 if cap else 0) + (2.9 if cap2 else 0)
    return size + 2 * pad, size + 2 * pad + (cap_h + 0.4 if cap_h else 0)
