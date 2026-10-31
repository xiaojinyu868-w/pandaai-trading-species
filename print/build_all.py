#!/usr/bin/env python3.11
"""《交易物种起源》印刷文件一键重建。

    python3.11 print/build_all.py              全部重建：PDF + 预览 + 自检 + 印刷说明
    python3.11 print/build_all.py --no-qa      跳过二维码解码等自检（快）
    python3.11 print/build_all.py --only 02,03 只出编号前缀匹配的文件（印刷说明照常按全部生成）

输出：print/out/（交给打印店）、print/preview/（预览、自检报告）。中间文件在 print/build/。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from src import art, c_a6, c_board, c_book, c_box, c_misc, c_std, c_test, content, fontbuild, qrsvg  # noqa: E402
from src.core import GRID_A6, GRID_MINI, GRID_STD, Card, Grid, doc, esc, impose, preview_body, single_pages, tokens_css  # noqa: E402
from src.model import Model  # noqa: E402
from src.paths import BUILD, CONTENT, OUT, PREVIEW, TEMPLATES  # noqa: E402
from src.render import Renderer, pdf_fonts, pdf_pages, pdf_size_mm  # noqa: E402
from src.tokens import PLAYERS, SEASON, SEASON_ORDER  # noqa: E402

VERSION = "v1.0"
SETS = 2  # 物料清单：建议做 2 套


@dataclass
class Output:
    file: str
    body: str
    w: float
    h: float
    group: str
    what: str
    finished: str = ""
    qty: str = ""
    stock: str = ""
    finish: str = ""
    layout: str = ""
    corner: str = ""
    note: str = ""
    sub: str = ""
    pages: list = field(default_factory=list)  # 每页的 Card 列表（二维码自检用）
    pdf: Path | None = None
    n_pages: int = 0
    size: tuple | None = None


@dataclass
class Preview:
    file: str
    cards: list
    cols: int
    dpi: int
    title: str


OUTS: list[Output] = []
PREVS: list[Preview] = []


def add(o: Output):
    OUTS.append(o)
    return o


def page_body(html: str, w: float, h: float) -> str:
    return f'<div class="page sheet" style="width:{w}mm;height:{h}mm;">{html}</div>'


def sheets_of(n, per):
    return max(1, -(-n // per))


def card_set(group, label, pairs, grid: Grid, meta: dict, single_name=None):
    """双面卡：A3 拼版正面 + 镜像反面 + 单张（正反交替）。pairs 里反面可以是 None（单面件）。"""
    fronts = [f for f, _ in pairs]
    backs = [b for _, b in pairs]
    bf, n = impose(fronts, grid, f"{group}_{label}", side="正面")
    add(Output(f"{group}_{label}_正面_拼版_A3_{n}张.pdf", bf, grid.sheet_w, grid.sheet_h, group, f"{label} 正面", **meta,
               layout=f"A3 每张 {grid.per} 个，带裁切线、套位十字"))
    if any(b is not None for b in backs):
        bb, n2 = impose(backs, grid, f"{group}_{label}", mirror=True, side="反面")
        add(Output(f"{group}_{label}_反面_拼版_A3_{n2}张.pdf", bb, grid.sheet_w, grid.sheet_h, group, f"{label} 反面", **meta,
                   layout=f"A3 每张 {grid.per} 个，左右镜像，和正面同一张纸的背面"))
    seq = []
    for f, b in pairs:
        seq.append(f)
        if b is not None:
            seq.append(b)
    bs, w, h = single_pages(seq)
    nm = single_name or f"{group}_{label}_单张_{len(pairs)}张_{len(seq)}页.pdf"
    add(Output(nm, bs, w, h, group, f"{label} 单张（{'正反交替' if len(seq) > len(pairs) else '单面'}）", **meta, sub="单张",
               layout="一页一张，带 3 mm 出血，无裁切线；门店自己拼版时用", pages=[[c] for c in seq]))
    return seq


def singles(group, name, cards: list[Card], what, meta: dict, sub=""):
    body, w, h = single_pages(cards)
    return add(Output(name, body, w, h, group, what, **meta, sub=sub, pages=[[c] for c in cards]))


# ====================================================================== 组装

def assemble(m: Model):
    p0 = [sc for sc in m.scenes if sc.get("tier") != "P1"]
    p1 = [sc for sc in m.scenes if sc.get("tier") == "P1"]

    # 00 测试页
    tcs = c_test.cards(m)
    singles("00", "00_测试页_A3_正反2面.pdf", tcs, "印刷测试页（先印这张）",
            dict(finished="420×297（A3，不用裁）", qty="1 张（双面，长边翻转）", stock="和卡牌同一种纸", finish="和正式件同一工艺（含覆膜）",
                 note="先印这张确认二维码、红绿、最小字、透印和正反套位"))
    PREVS.append(Preview("00_测试页.png", tcs, 2, 60, "A3 测试页 · 正面 / 背面"))

    # 01 主棋盘
    b = c_board.board(m)
    qs = c_board.quadrants(b)
    singles("01", "01_主棋盘_A2_1张.pdf", [b], "主棋盘 A2",
            dict(finished="594×420（A2）", qty="1", stock="250–300g 铜版纸或 PP 合成纸", finish="单面四色，覆哑膜；十字对折两次到 297×210",
                 note="页面 600×426 含出血；折线 x=297、y=210，已避开格子中心"))
    singles("01", "01b_主棋盘_A4四拼_4张.pdf", qs, "主棋盘 A4 四拼（裱 KT 板版）",
            dict(finished="297×210 ×4，拼成 A2", qty="4（一套）", stock="背胶 PP 或相纸", finish="单面四色，覆哑膜，各自裱 3–5 mm KT 板（或 2 mm 灰板）",
                 note="和 A2 版二选一；每张角上印了位置（左上 / 右上 / 左下 / 右下）"))
    PREVS.append(Preview("01_主棋盘.png", [b], 1, 60, "主棋盘 A2"))
    PREVS.append(Preview("01b_主棋盘_A4四拼.png", qs, 2, 60, "主棋盘 · A4 四拼（裱板版）"))

    # 02 A6
    a6 = []
    for sc in p0:
        a6.append((c_a6.scene_blind(m, sc), c_a6.scene_door(m, sc)))
    for sc in p0:
        a6.append((c_a6.reveal_front(m, sc), c_a6.reveal_back()))
    for sp in m.species:
        a6.append((c_a6.species_front(m, sp), c_a6.species_back(m, sp)))
    a6.append((c_a6.prologue_front(m), c_a6.prologue_back(m)))
    for n in range(1, 6):
        a6.append((c_a6.quickref_front(m, n), c_a6.quickref_back(m, n)))
    a6.append(c_misc.station_card(m))
    a6.append((c_a6.prop_sell_window(m), c_a6.prop_back("卖出窗口", "SELL WINDOW", "prop-sellwindow-b", season="summer")))
    a6.append((c_a6.prop_crowd_ring(m), c_a6.prop_back("抱团圈", "CROWD RING", "prop-crowdring-b", season="autumn")))
    meta6 = dict(finished="105×148（A6）", stock="350g 铜版纸；场景牌、揭幕牌用黑芯卡纸或两张对裱", finish="双面四色，双面覆哑膜，按线裁切",
                 corner="R4")
    seq = card_set("02", "A6卡", a6, GRID_A6, dict(meta6, qty=f"{len(a6)} 张"))
    PREVS.append(Preview("02_A6卡.png", seq, 8, 60, f"A6 卡 · {len(a6)} 张（正 / 反成对）"))
    if p1:
        a6p1 = [(c_a6.scene_blind(m, sc), c_a6.scene_door(m, sc)) for sc in p1]
        a6p1 += [(c_a6.reveal_front(m, sc), c_a6.reveal_back()) for sc in p1]
        a6p1.append((c_a6.prop_exit_board(m), c_a6.prop_back("出口板", "EXIT BOARD", "prop-exitboard-b", season="autumn")))
        seq = card_set("02P1", "A6卡_P1扩展", a6p1, GRID_A6, dict(meta6, qty=f"{len(a6p1)} 张", note="P1：秋、冬第二扇门"))
        PREVS.append(Preview("02P1_A6卡_P1扩展.png", seq, 6, 60, f"A6 卡 · P1 扩展 {len(a6p1)} 张"))

    # 03 标准卡
    std = []
    for sc in p0:
        std += c_std.scene_std_cards(m, sc)
    for k, v in c_std.deck_pairs(m).items():
        std += v
    metas = dict(finished="63×88", stock="350g 铜版纸；证据、锦囊、快进牌用黑芯卡纸", finish="双面四色，双面覆哑膜，按线裁切", corner="R3")
    seq = card_set("03", "标准卡", std, GRID_STD, dict(metas, qty=f"{len(std)} 张"))
    PREVS.append(Preview("03_标准卡.png", seq, 16, 55, f"标准卡 · {len(std)} 张（正 / 反成对）"))
    if p1:
        stdp1 = []
        for sc in p1:
            stdp1 += c_std.scene_std_cards(m, sc)
        seq = card_set("03P1", "标准卡_P1扩展", stdp1, GRID_STD, dict(metas, qty=f"{len(stdp1)} 张", note="P1：秋、冬第二扇门"))
        PREVS.append(Preview("03P1_标准卡_P1扩展.png", seq, 10, 70, f"标准卡 · P1 扩展 {len(stdp1)} 张"))

    # 04 迷你卡
    badges, debts = c_misc.mini_pairs(m)
    metam = dict(finished="44×68", stock="350g 铜版纸", finish="双面四色，双面覆哑膜，按线裁切", corner="R3")
    seq = card_set("04", "迷你卡_徽章", badges, GRID_MINI, dict(metam, qty=f"{len(badges)} 张"))
    PREVS.append(Preview("04_迷你卡_徽章.png", seq, 8, 100, f"迷你卡 · 徽章 {len(badges)} 张"))
    seq = card_set("04P1", "迷你卡_负债牌_P1", debts, GRID_MINI, dict(metam, qty=f"{len(debts)} 张", note="P1"))
    PREVS.append(Preview("04P1_迷你卡_负债牌.png", seq[:4], 4, 110, f"迷你卡 · 负债牌 P1 × {len(debts)}（只预览 2 张）"))

    # 05 A5 板
    boards = [c_misc.player_board(m, p, i) for i, p in enumerate(PLAYERS)] + [c_misc.ai_board(m)]
    meta5 = dict(finished="210×148（A5 横）", qty=f"{len(boards)}（玩家板 {len(PLAYERS)} + AI 板 1）", stock="350g 铜版纸（或裱 2 mm 灰板）",
                 finish="单面四色，覆哑膜", corner="R3（可选）")
    singles("05", f"05_玩家板与AI板_A5_{len(boards)}张.pdf", boards, "玩家板 ×5 + AI 板", meta5)
    g5 = Grid(297.0, 420.0, 1, 2, 210, 148)
    body, n = impose(boards, g5, "05_玩家板与AI板", side="单面")
    add(Output(f"05b_玩家板与AI板_拼版_A3_{n}张.pdf", body, g5.sheet_w, g5.sheet_h, "05", "玩家板 + AI 板 拼版", **meta5,
               layout="A3 每张 2 块，带裁切线"))
    PREVS.append(Preview("05_玩家板与AI板.png", boards, 3, 70, "A5 玩家板 ×5 + AI 板"))

    # 06 终局档案卡
    rf, rb = c_misc.record_card(m)
    meta_r = dict(finished="148×210（A5 竖）", qty="每局每人 1 张，建议 50 张", stock="120–157g 哑粉纸（要能用铅笔写）", finish="双面四色，不覆膜",
                  note="消耗品；可做成胶头撕页本")
    singles("06", "06_终局档案卡_A5_正反2页.pdf", [rf, rb], "终局档案卡（正 / 反）", meta_r)
    g6 = Grid(420.0, 297.0, 2, 1, 148, 210)
    bf, n = impose([rf, rf], g6, "06_终局档案卡", side="正面")
    add(Output(f"06b_终局档案卡_正面_拼版_A3_{n}张.pdf", bf, g6.sheet_w, g6.sheet_h, "06", "终局档案卡 正面拼版", **meta_r, layout="A3 每张 2 张"))
    bb, n = impose([rb, rb], g6, "06_终局档案卡", mirror=True, side="反面")
    add(Output(f"06b_终局档案卡_反面_拼版_A3_{n}张.pdf", bb, g6.sheet_w, g6.sheet_h, "06", "终局档案卡 反面拼版", **meta_r, layout="A3 每张 2 张，镜像"))
    PREVS.append(Preview("06_终局档案卡.png", [rf, rb], 2, 110, "终局档案卡 A5 · 正面 / 背面"))

    # 07 委托单
    slips = [c_misc.order_slip(m, s) for s in SEASON_ORDER]
    tints = [c_misc.order_slip(m, s, c_misc.SLIP_TINT[s]) for s in SEASON_ORDER]
    meta_s = dict(finished="105×148（A6）", qty="每季 1 本 × 50 张", stock="80–100g 彩色复印纸（春浅绿、夏浅粉、秋浅黄、冬浅蓝）",
                  finish="单面单色黑（K）；胶头撕页本", note="字朝里对折，扣在玩家板上")
    singles("07", "07_委托单_A6_单色黑_四季4页.pdf", slips, "委托单（单色黑，印在季节色纸上）", meta_s)
    bodies = []
    for s, c in zip(SEASON_ORDER, slips):
        bb, _ = impose([c] * 4, GRID_A6, f"07_委托单 · {SEASON[s]['cn']}季", side="单面")
        bodies.append(bb)
    add(Output("07b_委托单_单色黑_拼版_A3_4张.pdf", "\n".join(bodies), GRID_A6.sheet_w, GRID_A6.sheet_h, "07", "委托单 拼版（单色）", **meta_s,
               layout="A3 每张 4 张同一季，一季一张"))
    bodies = []
    for s, c in zip(SEASON_ORDER, tints):
        bb, _ = impose([c] * 4, GRID_A6, f"07_委托单 · {SEASON[s]['cn']}季 · 季节色版", side="单面")
        bodies.append(bb)
    add(Output("07c_委托单_季节色版_拼版_A3_4张.pdf", "\n".join(bodies), GRID_A6.sheet_w, GRID_A6.sheet_h, "07", "委托单 拼版（季节色底，白纸用）",
               **dict(meta_s, stock="100g 白色双胶纸", finish="单面四色（底色 + 黑）；胶头撕页本", note="找不到彩色纸时用这一版")))
    PREVS.append(Preview("07_委托单.png", slips + tints, 4, 100, "委托单 · 单色黑（上）/ 季节色版（下）"))

    # 08 开户排队条
    q = c_misc.queue_strip(m)
    singles("08", "08_开户排队条_210x60_1张.pdf", [q], "开户排队条",
            dict(finished="210×60", qty="1", stock="350g 铜版纸", finish="单面四色，覆哑膜", corner="R3（可选）"))
    PREVS.append(Preview("08_开户排队条.png", [q], 1, 150, "开户排队条 210×60"))

    # 09 规则书
    pages = c_book.book_pages(m)
    meta_b = dict(finished="148×210（A5）", qty="1 本", stock="封面 250g（第 1、2、15、16 页那张）、内页 157g 铜版纸", finish="彩色双面，骑马钉 2 钉；封面可覆哑膜")
    singles("09", f"09_规则书_A5_{len(pages)}页.pdf", pages, f"规则书 A5 {len(pages)} 页（单页，按页码顺序）",
            dict(meta_b, note="单页版带 3 mm 出血；门店按骑马钉自己拼版时用这个"))
    sp = c_book.spreads(pages)
    sheets = []
    sw = sh = 0
    for l, r in sp:
        h_, sw, sh = c_book.spread_sheet(l, r)
        sheets.append(page_body(h_, sw, sh))
    add(Output(f"09b_规则书_骑马钉对页拼版_{len(sp)}面.pdf", "\n".join(sheets), sw, sh, "09", "规则书 骑马钉对页（印刷顺序）",
               **dict(meta_b, note=f"每面一个对页，顺序 = 第 1 张纸正、反，第 2 张纸正、反…；{len(sp) // 2} 张纸对折套起来"),
               layout=f"对页 296×210 + 外侧出血，页面 {sw:g}×{sh:g}，带裁切线和书脊折线"))
    PREVS.append(Preview("09_规则书.png", pages, 8, 50, f"规则书 A5 · {len(pages)} 页"))

    # 10 快速入门卡
    qk = c_book.quickstart(m)
    singles("10", "10_快速入门卡_A4_1张.pdf", [qk], "快速入门卡",
            dict(finished="210×297（A4）", qty="1", stock="300g 铜版纸", finish="单面四色，覆哑膜"))
    PREVS.append(Preview("10_快速入门卡.png", [qk], 1, 110, "快速入门卡 A4"))

    # 11 盒标
    bx = c_box.cards(m)
    meta_x = dict(stock="铜版不干胶", finish="四色，覆哑膜，按线模切 / 裁切", note="按实际盒子量一下再印：盒盖贴纸每边比盒盖小 2–3 mm")
    for c, nm, fin in zip(bx, ("盒盖_300x215", "长边侧标_300x50", "短边侧标_215x50"), ("300×215", "300×50", "215×50")):
        singles("11", f"11_盒标_{nm}_1张.pdf", [c], c.label, dict(meta_x, finished=fin, qty="1"))
    add(Output("11b_盒标_拼版_A3_2张.pdf", c_box.sheets(bx), 420.0, 297.0, "11", "盒标拼版", **dict(meta_x, finished="见上", qty="1 套"),
               layout="A3 横：第 1 张盒盖，第 2 张两条侧标"))
    PREVS.append(Preview("11_盒标.png", bx, 1, 70, "盒标 · 盒盖 / 长边 / 短边"))


# ====================================================================== 渲染

def text_of(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", html))


def build_fonts():
    blob = [content.all_text_blob()]
    for o in OUTS:
        blob.append(text_of(o.body))
    blob.append(Path(__file__).read_text(encoding="utf-8"))
    for pv in PREVS:
        blob.append(pv.title + "".join(c.label for c in pv.cards))
    t = time.time()
    fontbuild.build("".join(blob))
    return time.time() - t


def render(r: Renderer, only: set | None):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "单张").mkdir(exist_ok=True)
    for o in OUTS:
        if only and not any(o.group.startswith(x) for x in only):
            continue
        dst = (OUT / o.sub / o.file) if o.sub else (OUT / o.file)
        html = doc(o.body, o.w, o.h, title=o.file)
        r.pdf(html, Path(o.file).stem, dst, o.w, o.h)
        o.pdf = dst
        o.n_pages = pdf_pages(dst)
        o.size = pdf_size_mm(dst)
        print(f"  {o.n_pages:>3} 页  {o.size[0]:g}×{o.size[1]:g}  {dst.relative_to(OUT)}", flush=True)


def previews(r: Renderer, only: set | None):
    PREVIEW.mkdir(parents=True, exist_ok=True)
    made = []
    for p in PREVS:
        if only and not any(p.file.startswith(x) for x in only):
            continue
        body, w, h = preview_body(p.cards, cols=p.cols, title=p.title)
        html = doc(body, w, h, title=p.file)
        dst = PREVIEW / p.file
        r.png(html, "pv_" + Path(p.file).stem, dst, dpi=p.dpi, viewport={"width": int(w / 25.4 * 96) + 2, "height": int(h / 25.4 * 96) + 2})
        made.append(dst)
    # 拼版缩略图（每个拼版文件第 1 张）
    sd = PREVIEW / "拼版"
    sd.mkdir(exist_ok=True)
    for o in OUTS:
        if o.pdf and o.sub == "" and ("拼版" in o.file):
            stem = sd / Path(o.file).stem
            subprocess.run(["pdftoppm", "-r", "28", "-f", "1", "-l", "1", "-png", "-singlefile", str(o.pdf), str(stem)], check=False)
    return made


def overview(files: list[Path]):
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(str(BUILD / "fonts" / "NotoSansSC-700.ttf"), 26)
    big = ImageFont.truetype(str(BUILD / "fonts" / "NotoSansSC-700.ttf"), 40)
    cw, chh, cols, pad = 760, 560, 4, 28
    files = [f for f in files if f.exists()]
    rows = -(-len(files) // cols)
    W = cols * cw + (cols + 1) * pad
    H = 100 + rows * (chh + 50) + (rows + 1) * pad
    sheet = Image.new("RGB", (W, H), (125, 122, 108))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 30), f"《交易物种起源》印刷文件总览 {VERSION} · {time.strftime('%Y-%m-%d %H:%M')}", font=big, fill=(251, 244, 228))
    for i, f in enumerate(files):
        r_, c_ = divmod(i, cols)
        x = pad + c_ * (cw + pad)
        y = 100 + pad + r_ * (chh + 50 + pad)
        im = Image.open(f).convert("RGB")
        im.thumbnail((cw, chh))
        sheet.paste(im, (x + (cw - im.width) // 2, y + (chh - im.height) // 2))
        d.text((x, y + chh + 10), f.stem, font=fnt, fill=(251, 244, 228))
    dst = PREVIEW / "00_总览.png"
    sheet.save(dst, optimize=True)
    return dst


# ====================================================================== 自检

QR_GEOM_JS = r"""
() => {
  const px = 96 / 25.4;
  const res = [];
  document.querySelectorAll('.card[data-key]').forEach(card => {
    const t = card.querySelector('.trim');
    if (!t) return;
    const tr = t.getBoundingClientRect();
    card.querySelectorAll('svg[data-qr]').forEach(s => {
      if (s.closest('.card') !== card) return;
      const r = s.getBoundingClientRect();
      res.push({key: card.dataset.key, id: s.dataset.qr, size: r.width / px,
                dist: Math.min(r.left - tr.left, r.top - tr.top, tr.right - r.right, tr.bottom - r.bottom) / px});
    });
  });
  return res;
}
"""


def qr_ids(card: Card) -> list[str]:
    return list(dict.fromkeys(re.findall(r'data-qr="([^"]+)"', card.html)))


def decode_png(path: Path) -> set[str]:
    import cv2
    img = cv2.imread(str(path))
    found = set()
    if img is None:
        return found
    det = cv2.QRCodeDetector()
    for im in (img, cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA), cv2.resize(img, None, fx=1.5, fy=1.5)):
        try:
            ok, infos, _, _ = det.detectAndDecodeMulti(im)
            if ok:
                found |= {s for s in infos if s}
        except cv2.error:
            pass
        try:
            s, _, _ = det.detectAndDecode(im)
            if s:
                found.add(s)
        except cv2.error:
            pass
        if found:
            break
    if not found and hasattr(cv2, "QRCodeDetectorAruco"):
        try:
            ok, infos, _, _ = cv2.QRCodeDetectorAruco().detectAndDecodeMulti(img)
            if ok:
                found |= {s for s in infos if s}
        except cv2.error:
            pass
    return found


def qa(r: Renderer):
    rep = {"qr": [], "qr_geom": [], "fonts": [], "words": [], "placeholders": []}
    qdir = BUILD / "qa"
    if qdir.exists():
        shutil.rmtree(qdir)
    qdir.mkdir(parents=True)
    used_ids = set()
    # 1) 二维码：从单页 PDF 栅格化后用 cv2 解码，和 qr.json 比对
    seen = set()
    for o in OUTS:
        if not o.pdf or not o.pages:
            continue
        for i, cards in enumerate(o.pages):
            ids = []
            for c in cards:
                ids += qr_ids(c)
            if not ids:
                continue
            used_ids |= set(ids)
            sig = (cards[0].key, tuple(ids))
            if sig in seen:
                continue
            seen.add(sig)
            dpi = 300 if max(o.w, o.h) < 230 else 200
            png = qdir / f"{Path(o.file).stem}_p{i + 1}"
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(i + 1), "-l", str(i + 1), "-png", "-singlefile", str(o.pdf), str(png)], check=False)
            got = decode_png(png.with_suffix(".png"))
            for qid in ids:
                want = qrsvg.url(qid)
                rep["qr"].append({"file": o.file, "page": i + 1, "card": cards[0].key, "id": qid, "url": want, "ok": want in got})
            extra = got - {qrsvg.url(q) for q in ids}
            if extra:
                rep["qr"].append({"file": o.file, "page": i + 1, "card": cards[0].key, "id": "?", "url": " ".join(sorted(extra)), "ok": False, "extra": True})
    # 2) 二维码尺寸和离裁切距离（DOM 量）
    for o in OUTS:
        if not o.pdf or not o.pages or not any(qr_ids(c) for cs in o.pages for c in cs):
            continue
        hp = BUILD / "html" / f"{Path(o.file).stem}.html"
        ctx, page = r._open(hp)
        for g in page.evaluate(QR_GEOM_JS):
            g["file"] = o.file
            rep["qr_geom"].append(g)
        ctx.close()
    # 3) PDF：字体嵌入、禁用词、占位符
    bad_words = ["大富翁", "monopoly"]
    for o in OUTS:
        if not o.pdf:
            continue
        for line in pdf_fonts(o.pdf):
            emb = re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
            if "Type 3" in line or (emb and emb.group(1) == "no"):
                rep["fonts"].append({"file": o.file, "line": line.strip()})
        txt = subprocess.run(["pdftotext", "-q", str(o.pdf), "-"], capture_output=True, text=True).stdout
        low = txt.lower()
        for w in bad_words:
            if w in low:
                rep["words"].append({"file": o.file, "word": w})
        for w in ("待补", "TODO", "XXX", "lorem", "undefined", "None", "NaN"):
            if w in txt:
                rep["placeholders"].append({"file": o.file, "word": w, "count": txt.count(w)})
    # 4) qr.json 覆盖
    allq = json.loads((CONTENT / "qr.json").read_text(encoding="utf-8"))
    rep["qr_unused"] = [{"id": q["id"], "tier": q.get("tier"), "printed_on": q.get("printed_on")} for q in allq if q["id"] not in used_ids]
    rep["qr_used"] = sorted(used_ids)
    return rep


def content_stamp():
    out = {}
    for p in sorted(CONTENT.glob("*")):
        if p.suffix in (".json", ".md"):
            out[p.name] = hashlib.md5(p.read_bytes()).hexdigest()[:10]
    return out


def write_qa(rep, issues, secs):
    L = [f"# 印刷文件自检报告 {VERSION}", "", f"生成：{time.strftime('%Y-%m-%d %H:%M')}，用时 {secs:.0f} 秒。", ""]
    L.append("## 内容版本（md5 前 10 位）")
    L += [f"- {k}：{v}" for k, v in content_stamp().items()]
    L.append("")
    if rep:
        q = rep["qr"]
        ok = [x for x in q if x["ok"]]
        bad = [x for x in q if not x["ok"]]
        L.append(f"## 二维码解码（cv2，从 PDF 栅格化）\n\n共检查 {len(q)} 个码位，解码一致 {len(ok)}，失败或不一致 {len(bad)}。用到的 id {len(rep['qr_used'])} 个。\n")
        for x in bad:
            L.append(f"- ✗ {x['file']} 第 {x['page']} 页 {x['card']}：{x['id']} → {x['url']}")
        g = rep["qr_geom"]
        if g:
            small = [x for x in g if x["size"] < 17.95 and not x["key"].startswith("test-")]
            near = [x for x in g if x["dist"] < 4.95 and not x["key"].startswith("test-")]
            L.append(f"\n码区尺寸：最小 {min(x['size'] for x in g if not x['key'].startswith('test-')):.1f} mm，离裁切最近 {min(x['dist'] for x in g if not x['key'].startswith('test-')):.1f} mm。")
            sizes = {}
            for x in g:
                if not x["key"].startswith("test-"):
                    sizes.setdefault(round(x["size"], 1), set()).add(x["key"].split("-")[0])
            L.append("各尺寸：" + "；".join(f"{k:g} mm（{', '.join(sorted(v))}）" for k, v in sorted(sizes.items())))
            for x in small:
                L.append(f"- 小于 18 mm：{x['file']} {x['key']} {x['id']} {x['size']:.1f} mm")
            for x in near:
                L.append(f"- 离裁切 < 5 mm：{x['file']} {x['key']} {x['id']} {x['dist']:.1f} mm")
        L.append("\n### qr.json 里没印出来的码\n")
        L += [f"- {x['id']}（{x['tier']}）：{x['printed_on']}" for x in rep["qr_unused"]] or ["- 无"]
        L.append("\n## PDF 检查\n")
        L.append("- 字体未嵌入 / Type 3：" + ("无" if not rep["fonts"] else "；".join(f"{x['file']}: {x['line']}" for x in rep["fonts"][:10])))
        L.append("- 禁用词（大富翁 / Monopoly）：" + ("无" if not rep["words"] else "；".join(f"{x['file']}: {x['word']}" for x in rep["words"])))
        L.append("- 占位符：" + ("无" if not rep["placeholders"] else "；".join(f"{x['file']}: {x['word']}×{x['count']}" for x in rep["placeholders"])))
    L.append("\n## 排版自动检查（溢出 / 小于 7 pt）\n")
    if not issues:
        L.append("- 无")
    for i in issues:
        if i["type"] == "overflow":
            L.append(f"- 溢出：{i['key']} · {i.get('what', '')}：{i.get('text', '')[:40]}")
        else:
            L.append(f"- 小字 {i['size']} pt：{i['key']}：{i['text']}")
    L.append("\n## 排版时的缩写、替换和内容问题\n")
    L += [f"- {n}" for n in dict.fromkeys(content.NOTES)] or ["- 无"]
    miss = list(dict.fromkeys(art.MISSING)) if hasattr(art, "MISSING") else []
    L.append("\n## 缺图\n")
    L += [f"- {x}" for x in miss] or ["- 无"]
    dst = PREVIEW / "QA_自检报告.md"
    dst.write_text("\n".join(L) + "\n", encoding="utf-8")
    return dst


# ====================================================================== 印刷说明

def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |")
    return out


def spec_md():
    L = [f"# 《交易物种起源》印刷说明 {VERSION}", "",
         f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M')}。本说明由 `print/build_all.py` 自动生成，文件名、页数、尺寸以 `print/out/` 里的实际文件为准。",
         f"> 按一套写数量；建议做 {SETS} 套（一套拍视频和带去展位，一套备用）。先印 **00_测试页**，确认后再印全套。", ""]
    L.append("## 1. 给门店的下单说明（可直接转发）\n")
    L += ["> 您好，我们要做桌游原型，数码快印。文件是 PDF，拼版文件已排在 A3 上、带 3 mm 出血和裁切线；单张文件在 `单张/` 文件夹里，方便您自己拼版。",
          ">",
          "> 1. **先打一张测试页**（00_测试页，A3 双面，长边翻转，用正式纸张和覆膜）。我们确认二维码能扫、红绿分得开、7 pt 小字清楚、背面不透印、正反对位之后，再印全套。",
          "> 2. **卡牌**（A6 105×148、标准卡 63×88、迷你卡 44×68）：双面四色，350g 铜版纸；场景牌、揭幕牌、证据牌、锦囊牌、快进牌请用黑芯卡纸（或两张对裱），对着光不能透字。双面覆哑膜，按线裁切，圆角 A6 用 R4、其余 R3。反面文件已经左右镜像，和正面印在同一张纸的背面。",
          "> 3. **主棋盘**：A2 单面四色，250–300g 铜版纸或 PP 合成纸，覆哑膜，十字对折两次到 297×210；或者用 A4 四拼版，4 张各自裱 3–5 mm KT 板。",
          "> 4. **玩家板 / AI 板** 6 张 A5：单面四色，350g，覆哑膜。**开户排队条** 210×60：同上。",
          "> 5. **终局档案卡** A5：双面四色，120–157g 哑粉纸，不覆膜（要用铅笔写），50 张。",
          "> 6. **委托单** A6：单色黑，印在四种浅色彩纸上（春浅绿、夏浅粉、秋浅黄、冬浅蓝），每季 50 张做成胶头撕页本；没有彩纸就用季节色版印在 100g 白纸上。",
          "> 7. **规则书** A5 16 页：封面 250g、内页 157g 铜版纸，彩色，骑马钉 2 钉。",
          "> 8. **快速入门卡** A4：300g 单面四色，覆哑膜。",
          "> 9. **盒标**：铜版不干胶，四色，覆哑膜，按线裁。盒子是天地盖空白礼盒，内径不小于 300×215×60 mm，尽量选墨绿或黑色：侧标底色是深墨绿，贴纸四周露出的 2–3 mm 盒边才不显眼。",
          ">",
          "> 文件是 RGB（sRGB）PDF，字体已嵌入、文字是矢量。请按门店流程转 CMYK 并先打样，颜色以样张为准。", ""]
    L.append("## 2. 文件清单\n")
    rows = []
    for o in OUTS:
        nm = f"{o.sub}/{o.file}" if o.sub else o.file
        size = f"{o.size[0]:g}×{o.size[1]:g}" if o.size else f"{o.w:g}×{o.h:g}"
        rows.append([nm, o.what, o.finished, o.n_pages or "", size, o.qty, o.stock, o.finish, o.corner or "—", (o.layout + ("；" + o.note if o.note else "")).strip("；")])
    L += md_table(["文件", "内容", "成品尺寸 mm", "页数", "页面尺寸 mm", "每套数量", "纸张", "工艺", "圆角", "拼版 / 备注"], rows)
    L += ["", "## 3. 通用规格\n",
          "- **出血和安全区**：四边各 3 mm 出血；文字和二维码离裁切线不少于 5 mm（A6 卡背的二维码离裁切 ≥ 5 mm，码区 17 mm，是有意的例外，测试页上验证）。",
          "- **拼版**：A3（297×420）。标准卡每张 16 个、A6 每张 4 个、迷你卡每张 25 个、A5 板每张 2 块。裁切线只画在拼版外缘，线宽 0.5 pt，套版黑。",
          "- **正反面**：反面文件左右镜像，和正面用同一张纸；纸边中点有套位十字，正反对着光应重合，偏差 ≤ 0.5 mm。数码印刷正反会偏 1 mm 左右，所以卡背没有细边框。",
          "- **单张文件**（`单张/`）：一页一张、带出血、无裁切线；双面件按“正、反、正、反…”交替排列（不镜像），门店拼版或数码直印时用。",
          "- **字号和线宽**：正文不小于 7 pt，图表标注不小于 6 pt，线宽不小于 0.5 pt。",
          "- **涨跌色**：红涨（#D4432A）绿跌（#3C7A4E），永远配 ▲▼；黑白复印下两色几乎一样深，靠符号区分。",
          "- **二维码**：黑码白底，纠错 M，四周留白 ≥ 2 mm，码区 ≥ 18 mm（推荐 20–22 mm）。只用哑膜，亮膜反光不好扫。",
          "- **圆角**：A6 卡 R4；标准卡、迷你卡 R3；A5 板和排队条可选 R3；棋盘、规则书、快速入门卡、盒标不倒角。",
          "- **棋盘折线**：A2 版对折两次，折线在 x = 297 mm、y = 210 mm（成品坐标），已避开格子中心和文字。", "",
          "## 4. 打样确认清单\n",
          "1. 测试页：三档二维码用两部以上手机在 30 cm / 50 cm 扫，18 mm 也要一次扫中；红绿块分得开；7 pt 小字和反白小字清楚；背面透印块看不到暗影；正反套位十字重合。",
          "2. 卡牌样张：正反对位（翻过来看边缘白边是否均匀），圆角，覆膜后背面对着光看不到正面文字。",
          "3. 棋盘：对折后格子和文字不压在折线上；KT 板版四张拼起来路线连续。",
          "4. 规则书：页码顺序 1–16 正确，骑马钉居中，封面封底没有错位。",
          "5. 委托单：彩纸上黑字清楚；对折后上下两半对得齐。",
          "6. 颜色：插画不发灰、不偏荧光；季节色、玩家色之间分得开（雾紫和海蓝尤其注意）。", "",
          "## 5. 每套数量汇总\n"]
    L += [f"- {o.what.replace(' 单张（正反交替）', '').replace(' 单张（单面）', '')}：{o.qty}" for o in OUTS if o.sub == "单张" or (not o.sub and "拼版" not in o.file)]
    return "\n".join(L) + "\n"


def md_to_html(md: str) -> str:
    out = []
    lines = md.splitlines()
    i = 0

    def inl(t):
        t = esc(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t

    while i < len(lines):
        l = lines[i]
        if l.startswith("# "):
            out.append(f"<h1>{inl(l[2:])}</h1>")
        elif l.startswith("## "):
            out.append(f"<h2>{inl(l[3:])}</h2>")
        elif l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[2:]
            out.append("<table><tr>" + "".join(f"<th>{inl(c)}</th>" for c in head) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>" for r in body) + "</table>")
            continue
        elif l.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            out.append("<blockquote>" + "".join(f"<p>{inl(b)}</p>" if b else "" for b in buf) + "</blockquote>")
            continue
        elif re.match(r"^\d+\. ", l):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inl(x)}</li>" for x in items) + "</ol>")
            continue
        elif l.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inl(x)}</li>" for x in items) + "</ul>")
            continue
        elif l.strip():
            out.append(f"<p>{inl(l)}</p>")
        i += 1
    return "\n".join(out)


SPEC_CSS = """
@page { size: 297mm 210mm; }
body { font-size: 8.4pt; line-height: 1.55; color: #2A2A1C; }
h1 { font-family: "Smiley Sans Oblique", "Noto Sans SC", sans-serif; font-weight: 400; font-size: 20pt; margin: 0 0 3mm; }
h2 { font-family: "Smiley Sans Oblique", "Noto Sans SC", sans-serif; font-weight: 400; font-size: 13pt; margin: 5mm 0 2mm; border-bottom: 0.8pt solid #C79A2E; padding-bottom: 1mm; }
p { margin: 0 0 1.6mm; }
blockquote { background: #FBF4E4; border-left: 1.2mm solid #C79A2E; padding: 2mm 3mm; margin: 0 0 2mm; }
blockquote p { margin: 0 0 1mm; }
ul, ol { margin: 0 0 2mm 5mm; }
li { margin-bottom: 0.8mm; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0 3mm; font-size: 7pt; line-height: 1.35; }
th { background: #2A2A1C; color: #FBF4E4; text-align: left; padding: 1mm 1.4mm; font-weight: 700; }
td { border-bottom: 0.5pt solid #77745A; padding: 1mm 1.4mm; vertical-align: top; }
tr { break-inside: avoid; }
code { font-family: "TS Mono", "Noto Sans SC", monospace; font-size: 0.95em; }
"""


def spec_pdf(r: Renderer, md: str, dst: Path):
    links = "\n".join(f'<link rel="stylesheet" href="{(TEMPLATES / f).as_uri()}">' for f in ("base.css",))
    html = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>印刷说明</title><style>{tokens_css()}</style>{links}'
            f'<style>{SPEC_CSS}</style></head><body>{md_to_html(md)}</body></html>')
    hp = BUILD / "html" / "00_印刷说明.html"
    hp.write_text(html, encoding="utf-8")
    ctx, page = r._open(hp)
    page.emulate_media(media="print")
    page.pdf(path=str(dst), width="297mm", height="210mm", print_background=True, prefer_css_page_size=True,
             margin={"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"})
    ctx.close()


# ====================================================================== main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()} or None
    t0 = time.time()
    (BUILD / "html").mkdir(parents=True, exist_ok=True)
    if not only:
        for d in (OUT, PREVIEW):
            if d.exists():
                shutil.rmtree(d)
    print("组装…", flush=True)
    m = Model()
    assemble(m)
    print(f"字体子集… {build_fonts():.1f}s", flush=True)
    r = Renderer()
    try:
        print("渲染 PDF…", flush=True)
        render(r, only)
        print("预览…", flush=True)
        made = previews(r, only)
        if not only:
            ov = overview(made)
            print("  总览", ov.relative_to(PREVIEW.parent))
        rep = None
        if not a.no_qa and not only:
            print("自检…", flush=True)
            rep = qa(r)
        issues = []
        seen = set()
        for i in r.issues:
            k = (i["type"], i.get("key"), i.get("what", ""), i.get("text", ""))
            if k not in seen:
                seen.add(k)
                issues.append(i)
        if not only:
            md = spec_md()
            (OUT / "00_印刷说明.md").write_text(md, encoding="utf-8")
            spec_pdf(r, md, OUT / "00_印刷说明.pdf")
            if rep is not None:
                for line in pdf_fonts(OUT / "00_印刷说明.pdf"):
                    if "Type 3" in line:
                        rep["fonts"].append({"file": "00_印刷说明.pdf", "line": line.strip()})
        qa_path = write_qa(rep, issues, time.time() - t0)
    finally:
        r.close()
    if rep:
        bad = [x for x in rep["qr"] if not x["ok"]]
        print(f"二维码：{len(rep['qr']) - len(bad)}/{len(rep['qr'])} 解码一致；字体问题 {len(rep['fonts'])}；禁用词 {len(rep['words'])}；占位符 {len(rep['placeholders'])}")
    print(f"排版问题 {len(issues)} 条；报告 {qa_path.relative_to(PREVIEW.parent)}；用时 {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
