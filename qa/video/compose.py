"""把录屏拼成 1920×1080 的演示视频粗剪：左边手机画面，右边字幕卡；片头、数据、线下、片尾是静帧卡。

  python3.11 qa/video/compose.py --raw /tmp/ts-video/raw --out 提交材料/视频
"""
import argparse, re, subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG, GOLD, CREAM, DIM = "#0E2A27", "#C9A25E", "#F4E4BF", "#B9B39A"
FONT = {k: f"/root/.fonts/NotoSansSC-{v}.otf" for k, v in {"b": "Bold", "m": "Medium", "r": "Regular"}.items()}
PREV = Path("/mnt/pandaai-trading-species/delivery/previews")
PHONE = (229, 40, 462, 1000)  # x, y, w, h
QOFF = 1.2  # 快速版录屏里，标记时间比视频时间早约 1.2 秒

f = lambda k, s: ImageFont.truetype(FONT[k], s)


def wrap(d, text, font, width):
    lines, cur = [], ""
    for ch in re.findall(r"[A-Za-z0-9_./%-]+|.", text, re.S):
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur + ch, font=font) > width and cur:
            if ch in "，。、；：！？）”》":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def base(footer=True):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    if footer:
        d.text((W - 60, H - 46), "交易物种起源 · PandaAI 赛道 · 投资者教育游戏，不构成投资建议", font=f("r", 22), fill=DIM, anchor="rs")
        d.text((W - 60, 66), "meetmind.online/ts", font=f("m", 26), fill=GOLD, anchor="rs")
    return im, d


def text_block(d, x, y, width, kicker, head, sub, head_size=66):
    if kicker:
        d.text((x, y), kicker, font=f("m", 30), fill=GOLD)
        y += 52
        d.rectangle((x, y, x + 90, y + 5), fill=GOLD)
        y += 34
    hf = f("b", head_size)
    for ln in wrap(d, head, hf, width):
        d.text((x, y), ln, font=hf, fill=CREAM)
        y += int(head_size * 1.32)
    if sub:
        y += 22
        sf = f("r", 36)
        for ln in wrap(d, sub, sf, width):
            d.text((x, y), ln, font=sf, fill=DIM)
            y += 56
    return y


def phone_card(kicker, head, sub, path):
    im, d = base()
    x, y, w, h = PHONE
    d.rounded_rectangle((x - 16, y - 16, x + w + 16, y + h + 16), radius=46, fill="#060f0d", outline="#2c4a44", width=3)
    text_block(d, 780, 300, 1060, kicker, head, sub)
    im.save(path)


def still_title(path):
    im, d = base(footer=False)
    box = Image.open(PREV / "包装效果图_外观.jpg").convert("RGB")
    box.thumbnail((980, 700))
    im.paste(box, (W - box.width - 60, (H - box.height) // 2))
    d.text((90, 250), "PandaAI 赛道 · 寻找你的交易人格", font=f("m", 32), fill=GOLD)
    d.text((86, 300), "交易物种起源", font=f("b", 120), fill=CREAM)
    y = text_block(d, 92, 500, 760, None, "同一段行情，有人追，有人等。你是哪一种？", "回到真实的金融史时刻，日期被藏起来。你怎么做决定，就会孵出什么物种。", head_size=48)
    d.text((92, H - 90), "投资者教育游戏，不构成投资建议", font=f("r", 24), fill=DIM)
    im.save(path)


def still_problem(path):
    im, d = base()
    text_block(d, 160, 230, 1600, "为什么做这个游戏",
               "同一套数据和工具，有人不知道从哪开始，有人想验证想法，有人已经很专业。",
               "PandaAI 想知道用户已经会什么、习惯怎么判断、想完成什么。我们不发问卷：让他玩一局，看他怎么做决定，再给一个当场就能做的下一步。", head_size=60)
    im.save(path)


def still_data(path):
    im, d = base()
    y = text_block(d, 160, 120, 1600, "Panda Data 用在哪", "行情、估值和全市场统计，都是真实数据", None, head_size=60)
    rows = [("指数日线", "上证、沪深 300、创业板指、中证 1000、国证 2000", "get_index_daily"),
            ("个股日线与前复权", "贵州茅台：行情与收益结算", "get_stock_daily / get_stock_daily_pre"),
            ("估值", "茅台 PE、PB；上证指数 PE、PB", "get_factor / get_index_indicator"),
            ("全市场逐只统计", "2015 跌停与停牌家数、924 两市成交额", "get_stock_daily"),
            ("基金与期货", "纳指 ETF 513100；上海原油各月合约", "get_fund_daily / get_future_daily")]
    y += 40
    for a, b, c in rows:
        d.text((160, y), a, font=f("b", 38), fill=CREAM)
        d.text((560, y + 4), b, font=f("r", 34), fill=DIM)
        d.text((160, y + 52), c, font=f("m", 26), fill=GOLD)
        y += 108
    d.text((160, y + 20), "盲测只给决定日之前的走势；揭幕时写出标的、代码、接口和完整区间。", font=f("r", 30), fill=CREAM)
    im.save(path)


def still_offline(path):
    im, d = base()
    text_block(d, 120, 110, 1680, "线下", "同一套内容的桌游，扫码接回线上", "卡牌、规则书和记录卡上共 88 个二维码；七个物种手办可以 3D 打印，H5 里能转一转同一个模型。", head_size=56)
    a = Image.open(PREV / "包装效果图_外观.jpg").convert("RGB"); a.thumbnail((840, 600))
    b = Image.open(PREV / "3D手办预览.jpg").convert("RGB"); b.thumbnail((840, 600))
    im.paste(a, (120, H - a.height - 110)); im.paste(b, (W - b.width - 120, H - b.height - 110))
    im.save(path)


def still_end(path):
    im, d = base(footer=False)
    d.text((W // 2, 260), "交易物种起源", font=f("b", 96), fill=CREAM, anchor="mm")
    d.text((W // 2, 420), "meetmind.online/ts", font=f("b", 72), fill=GOLD, anchor="mm")
    d.text((W // 2, 520), "评委演示台：meetmind.online/ts/demo", font=f("m", 40), fill=CREAM, anchor="mm")
    for i, t in enumerate(["评委演示台里是模拟玩家与示例数据；游戏里的 AI 对手是模拟玩家", "画像 JSON 是格式示例，尚未接入 PandaAI 账号", "投资者教育游戏，不构成投资建议"]):
        d.text((W // 2, 700 + i * 58), t, font=f("r", 32), fill=DIM, anchor="mm")
    im.save(path)


# (素材, 起, 止, 倍速, 小标题, 标题, 说明)；快速版的起止用标记时间，自动加偏移
SEGS = [
    ("quick", 0.3, 11.8, 1.0, "开局", "先玩一场 · 3 分钟", "先凭感觉选一个物种。这是“你以为的你”，最后会和“你实际的做法”对照。"),
    ("quick", 11.8, 16.3, 1.0, "选一个历史时刻", "名字和日期都藏起来了", "六个真实的金融史名场面，只给当时能看到的情境。"),
    ("quick", 16.3, 21.1, 1.0, "看情境", "走势只到你做决定那天", "Panda Data 真实日线。之后发生了什么，揭幕才知道。"),
    ("quick", 21.1, 45.5, 1.4, "查证据", "研究点只够看两份", "先看哪份、看了几份，都是画像的线索。"),
    ("quick", 45.5, 55.7, 1.0, "做决定", "填委托单：怎么做、为什么", "再想好跌了 5% 怎么办。理由比选项更重要。"),
    ("quick", 55.7, 63.2, 1.1, "亮牌", "和两只 AI 物种同时翻开", "同样的信息，不同的物种会怎么选？它们会说出自己的理由。"),
    ("quick", 63.2, 88.4, 1.4, "快进", "每个名场面一个招牌机制", "924：长假七天不开门，节后开户要排队。压力下是否照计划做，也会进画像。"),
    ("quick", 88.4, 100.0, 1.0, "揭幕", "原来是 924", "按真实行情结算两本账：收益账记赚了多少，方法账记想得怎么样。"),
    ("quick", 100.0, 106.4, 1.0, "驿站", "这一场，你像哪一种？", "每个图标都写着理由。不同意，可以答一道补测题。"),
    ("quick", 106.4, 112.6, 1.0, "初步画像", "你选了大象，做法更像猎豹", "物种只看你怎么做决定，不看赚没赚钱。"),
    ("quick", 112.6, 119.0, 1.0, "画像还很初步", "再推荐一场最能分清你的", "在没玩过的名场面里，挑两个候选物种做法分歧最大的一场。"),
    ("quick", 119.0, 125.4, 1.0, "PandaAI 下一步", "你的第一条策略，已经写好了", "按你的做法写成一句话，复制到 Qube 就能回测。"),
    ("quick", 125.4, 138.0, 1.0, "推荐和画像", "推荐有理由，画像有依据", "每条推荐写着“因为……”，还有 1 分钟就能做的任务。能力、偏好、习惯分开，证据不够的写进“待确认”。"),
    ("demo", 0.3, 6.6, 1.0, "评委演示台 · 模拟玩家", "同一个画像引擎，五种玩家", "五条行为路径，五种物种和推荐。用的是真实玩家同一个函数。"),
    ("demo", 6.6, 11.7, 1.0, "改一个关键选择", "春 · 924：从“等回调”改成“开盘追入”", "“等证据”这位玩家，其他都不动。"),
    ("demo", 11.7, 19.0, 1.0, "当场重算", "猫头鹰 / 大象 → 大象", "把握：待确认 → 比较确定。推荐：状态判断 → 假设检验。给 Qube 的那句话也换了。"),
    ("demo", 19.0, 27.0, 1.0, "为什么合理", "同样先看数据：看完选等是猫头鹰，看完选买是大象", "推荐理由、暂不推荐、当场任务，跟着一起变。"),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def enc(extra):
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30"] + extra


def still_seg(png, sec, out):
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-t", str(sec), "-i", str(png),
         "-vf", f"fade=t=in:st=0:d=0.4,fade=t=out:st={sec - 0.4}:d=0.4"] + enc([str(out)]))


def clip_seg(png, src, a, b, speed, out):
    dur = (b - a) / speed
    x, y, w, h = PHONE
    fc = (f"[1:v]setpts=(PTS-STARTPTS)/{speed},scale={w}:{h}:flags=lanczos,fps=30[ph];"
          f"[0:v][ph]overlay={x}:{y}:shortest=1,fade=t=in:st=0:d=0.25[v]")
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(png), "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", str(src),
         "-filter_complex", fc, "-map", "[v]", "-t", f"{dur:.2f}"] + enc([str(out)]))
    return dur


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/tmp/ts-video/raw")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    tmp = Path("/tmp/ts-video/build")
    tmp.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    parts, subs, t = [], [], 0.0

    def add_still(fn, name, sec, caption):
        nonlocal t
        png = tmp / f"{name}.png"; fn(png)
        mp4 = tmp / f"{len(parts):02d}_{name}.mp4"; still_seg(png, sec, mp4)
        parts.append(mp4); subs.append((t, t + sec, caption)); t += sec

    add_still(still_title, "title", 5.0, "交易物种起源：同一段行情，有人追，有人等。你是哪一种？")
    add_still(still_problem, "problem", 8.0, "PandaAI 想知道用户会什么、怎么判断、想做什么。我们让他玩一局，看他怎么做决定。")
    for i, (src, s, e, sp, k, hd, sb) in enumerate(SEGS):
        off = QOFF if src == "quick" else 0.0
        png = tmp / f"seg{i:02d}.png"; phone_card(k, hd, sb, png)
        mp4 = tmp / f"{len(parts):02d}_seg{i:02d}.mp4"
        dur = clip_seg(png, raw / f"{src}.webm", s + off, e + off, sp, mp4)
        parts.append(mp4); subs.append((t, t + dur, hd + ("" if hd[-1] in "？！。" else "。") + sb)); t += dur
        if src == "quick" and k == "揭幕":
            add_still(still_data, "data", 9.0, "Panda Data：指数日线、个股日线与前复权、估值、全市场逐只统计、基金与期货日线。")
    add_still(still_offline, "offline", 7.0, "线下是同一套内容的桌游，88 个二维码接回线上；七个物种手办可以 3D 打印。")
    add_still(still_end, "end", 6.0, "meetmind.online/ts · 评委演示台 /ts/demo · 投资者教育游戏，不构成投资建议")

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    final = out / "演示视频_粗剪.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(final)])
    (out / "演示视频_字幕.srt").write_text("".join(f"{i + 1}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n\n" for i, (a, b, c) in enumerate(subs)), encoding="utf-8")
    print(final, f"{t:.1f}s")


if __name__ == "__main__":
    main()
