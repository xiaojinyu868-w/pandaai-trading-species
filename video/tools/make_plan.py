"""按配音的实际时长排镜头，写 plan.json（镜头起止、字幕、手机录屏片段、旁白和音效）。

  python3.11 tools/make_plan.py [--raw /tmp/ts-video/raw]
"""
import argparse, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
LEAD, TAIL = 0.35, 0.5

# clips: 手机录屏片段。src 是录屏文件名；at 是镜头内开始时间；from 可以写成 "标记+偏移"；len 是录屏里的秒数；speed 播放倍速
SHOTS = [
    dict(id="hook", film="promo", vo=["p01"], lead=0.9, headlineEn="1720 · South Sea Bubble", headline="南海泡沫"),
    dict(id="montage", film="promo", vo=["p02"], headline="同样的名场面，一次次重演"),
    dict(id="choices", film="promo", vo=["p03"], tail=0.9, headline="追，还是等？借钱加仓，还是先跑？"),
    dict(id="title", film="promo", vo=["p04"], tail=1.1, headlineEn="The Origin of Trading Species", headline="不是韭菜，那你是哪一种？"),
    dict(id="blind", film="promo", vo=["p05"], headline="名字和日期藏起来",
         clips=[dict(src="play", at=0, frm="tap:pick-scene+1.1", len=99)]),
    dict(id="clues", film="promo", vo=["p06"], tail=0.8, headline="按着 = 拿着，松开 = 卖掉",
         clips=[dict(src="play", at=0, frm="tap:ev price-0.2", len=2.9),
                dict(src="play", at=2.9, frm="tap:plan 走-0.4", len=1.9),
                dict(src="play", at=4.8, frm="finger:down-1.0", len=99)]),
    dict(id="game", film="promo", vo=["p07"], tail=0.7, headline="借钱、跌停、AI 对手",
         clips=[dict(src="play", at=0, frm="game:offer-0.6", len=4.4),
                dict(src="play", at=4.4, frm="game:limit-0.4", len=99)]),
    dict(id="reveal", film="promo", vo=["p08"], tail=0.7, headline="真实走势，真实结算",
         clips=[dict(src="play", at=0, frm="game:reveal-1.2", len=99)]),
    dict(id="judge", film="promo", vo=["p09"], tail=0.7, headline="玩完，AI 给你复盘",
         clips=[dict(src="play", at=0, frm="final:1+0.3", len=99)]),
    dict(id="species", film="promo", vo=["p10"], tail=0.7, headline="你像哪一种，下一步做什么",
         clips=[dict(src="play", at=0, frm="final:0+0.4", len=4.0),
                dict(src="play", at=4.0, frm="final:3+0.3", len=99)]),
    dict(id="demo", film="promo", vo=["p11"], dur=5.4, headline="换一个选择，当场重算",
         clips=[dict(src="demo", at=0, frm="demo:careful+1.4", len=99)]),
    dict(id="handoff", film="promo", vo=["p12"], tail=0.6, headline="八十八个二维码，接回同一部手机",
         clips=[dict(src="qr_blind", at=0, frm="tap:play-here-3.6", len=99)]),
    dict(id="endcard", film="promo", vo=[], dur=3.6),

    dict(id="btitle", film="board", vo=[], dur=3.0),
    dict(id="b01", film="board", vo=["b01"]),
    dict(id="b02", film="board", vo=["b02"]),
    dict(id="b03", film="board", vo=["b03"]),
    dict(id="b04", film="board", vo=["b04"]),
    dict(id="b05", film="board", vo=["b05"]),
    dict(id="b06", film="board", vo=["b06"]),
    dict(id="b07", film="board", vo=["b07"]),
    dict(id="b08", film="board", vo=["b08"]),
    dict(id="b09", film="board", vo=["b09"], tail=0.8),
    dict(id="b10", film="board", vo=["b10"], tail=0.6,
         clips=[dict(src="qr_ff", at=12.2, frm="loaded+0.3", len=99)]),
    dict(id="b11", film="board", vo=["b11"], tail=0.8,
         clips=[dict(src="qr_reveal", at=1.6, frm="loaded+0.0", len=99)]),
    dict(id="b12", film="board", vo=["b12"]),
    dict(id="b13", film="board", vo=["b13"]),
    dict(id="b14", film="board", vo=["b14"]),
    dict(id="b15", film="board", vo=["b15"]),
    dict(id="b16", film="board", vo=["b16"], tail=4.2,
         clips=[dict(src="qr_record", at=0.6, frm="loaded+0.2", len=99)]),
]


def chunks(text):
    """字幕按句读切开，每条不超过 26 个字"""
    parts = [p for p in re.split(r"(?<=[。；？！])", text) if p.strip()]
    out = []
    for p in parts:
        while len(p) > 26:
            cut = max((m.end() for m in re.finditer(r"[，：、]", p[:26])), default=26)
            out.append(p[:cut])
            p = p[cut:]
        if p.strip():
            out.append(p)
    return [c.strip() for c in out]


def resolve(marks, spec, dur):
    m = re.match(r"(.+?)([+-]\d+(?:\.\d+)?)$", spec)
    name, off = (m.group(1), float(m.group(2))) if m else (spec, 0.0)
    hit = [t for t, label in marks if label == name]
    if not hit:
        raise SystemExit(f"mark not found: {name}")
    return max(0.0, hit[0] + off)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/tmp/ts-video/raw")
    a = ap.parse_args()
    vo = {x["id"]: x for x in json.loads((HERE / "narration.json").read_text())}
    marks = json.loads((Path(a.raw) / "marks.json").read_text())
    plan = json.loads((HERE / "plan.json").read_text())
    t = 0.0
    shots, captions, voice, boundary = [], [], [], None
    for s in SHOTS:
        if s["film"] == "board" and boundary is None:
            boundary = round(t, 2)
        lead, tail = s.get("lead", LEAD), s.get("tail", TAIL)
        start = t
        cur = start + lead
        for vid in s["vo"]:
            v = vo[vid]
            voice.append({"at": round(cur, 3), "file": f"assets/vo/{vid}.wav", "id": vid, "dur": v["dur"]})
            parts = chunks(v["text"])
            n = sum(len(p) for p in parts)
            c0 = cur
            for p in parts:
                d = v["dur"] * len(p) / n
                captions.append({"start": round(c0, 3), "end": round(c0 + d, 3), "text": p, "film": s["film"]})
                c0 += d
            cur += v["dur"]
        end = max(cur + tail, start + s.get("dur", 0))
        clips = []
        for c in s.get("clips", []):
            frm = resolve(marks[c["src"]]["marks"], c["frm"], 0)
            clips.append({"src": c["src"], "at": c["at"], "from": round(frm, 3), "len": c["len"], "speed": c.get("speed", 1)})
        for i, c in enumerate(clips):
            nxt = clips[i + 1]["at"] if i + 1 < len(clips) else end - start + 0.8
            c["len"] = round(min(c["len"], (nxt - c["at"]) * c["speed"]), 3)
        shots.append({
            "id": s["id"], "film": s["film"], "start": round(start, 3), "end": round(end, 3),
            "type": "title" if not s.get("clips") else "feature",
            "headlineEn": s.get("headlineEn", ""), "headline": s.get("headline", ""),
            "plainExplanation": " ".join(vo[v]["text"] for v in s["vo"]),
            "description": " ".join(vo[v]["text"] for v in s["vo"]), "descriptionAt": lead,
            "claim": False, "source": [], "component": "录屏：tools/rec_phone.py（线上真站）" if clips else None,
            "actions": [{"id": s["id"] + "-enter", "at": 0, "action": "enter", "soundRequired": False}],
            "vo": [{"id": v, "at": round(x["at"] - start, 3)} for v, x in zip(s["vo"], [y for y in voice if y["id"] in s["vo"]])],
            "clips": clips, "enter": s.get("enter", "fade"),
        })
        t = end
    plan.update({
        "demo": False, "product": "交易物种起源 · 宣传片 + 桌游玩法", "duration": round(t, 2), "boundary": boundary,
        "shots": shots, "captions": captions, "voice": voice,
        "typography": {"mode": "zh", "zhFont": "Smiley Sans Oblique（标题）/ Noto Sans SC（正文）", "enFont": "Smiley Sans Oblique",
                       "zhStyle": "sans-serif", "exceptionReason": "产品和印刷件的标题中英文都用得意黑，沿用产品设计"},
    })
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    print(json.dumps({"duration": plan["duration"], "boundary": boundary, "shots": len(shots), "captions": len(captions)}))


if __name__ == "__main__":
    main()
