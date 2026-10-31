#!/usr/bin/env python3
"""交易物种起源 · AI 复盘小服务（只用标准库）

POST /line   一关结束后的一句旁白
POST /judge  四关结束后的物种判断
GET  /health

key 只从环境变量 DASHSCOPE_API_KEY 读（systemd EnvironmentFile），不写进代码和仓库。
只接收游戏内的操作摘要，不接收、不记录任何个人信息；日志只记路径、耗时和模型。
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("TS_JUDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("TS_JUDGE_PORT", "8796"))
URL = os.environ.get("DASHSCOPE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
MODELS = [m for m in os.environ.get("TS_JUDGE_MODELS", "deepseek-v4.1-flash,qwen3.8-flash").split(",") if m]
MAX_BODY = 16 * 1024

SPECIES = {
    "cheetah": "猎豹：看见趋势就出发，追涨快、拿得短",
    "elephant": "大象：便宜才买，买了就拿，扛得住波动",
    "fox": "狐狸：先怀疑再检验，有自己的规则，多次进出，常和人群反着做（狂热里卖、恐慌里买）",
    "owl": "猫头鹰：证据不够就再等等；大部分时间空仓观望，四关里只出手一两次",
    "meerkat": "狐獴：对消息和人群情绪敏感，跟着人群和弹幕动",
    "chameleon": "变色龙：跟着市场换打法，不同行情做法不同",
}

SYS_COMMON = (
    "你是一款投资者教育游戏《交易物种起源》里的复盘解说。玩家刚在真实历史行情里玩了'按住=持有、松手=卖出'的小游戏，"
    "资金是虚拟的。说话对象是投资新手：用第二人称'你'，口语、具体、短句，不用术语，不说教，不夸张。"
    "绝不给任何真实的买卖建议、不推荐具体股票、不预测行情。只输出 JSON。"
)

LINE_PROMPT = (
    "根据这一关里玩家的操作，写一句旁白（不超过 34 个汉字），点出他这一手最有意思的地方，"
    "可以带一点幽默，但要贴着事实（这一关的真实结局已经揭晓）。"
    '输出格式：{"line": "..."}'
)

JUDGE_PROMPT = (
    "下面是玩家四关的操作摘要、本地规则给出的各物种得分（仅供参考，你可以不同意），以及玩家自己猜的物种。"
    "请综合四关做最终判断，物种只能从以下六个里选一个（填英文 id）：\n"
    + "\n".join(f"- {k}：{v}" for k, v in SPECIES.items())
    + "\n要求：\n"
    "1. species：英文 id。\n"
    "2. title：给他起一个 4~9 字的称号，像'2015 年的幸存者'这样有画面感。\n"
    "3. read：用 40~60 字说清楚你凭什么这么判断，必须引用至少两关里的具体动作。\n"
    "4. moments：3 条，每条不超过 26 字，格式'某关：他做了什么'，挑最能说明性格的瞬间。\n"
    "5. gap：40~60 字，提醒他模拟盘和实盘的差别：真钱的亏损感受更强、实盘还有手续费/滑点/跌停卖不出等，"
    "结合他这局里扛住或没扛住的那一段来说。\n"
    "6. qube：一句可以直接粘贴到量化平台回测的策略描述（40~80 字），把他的习惯写成明确规则"
    "（买入条件、卖出条件、止损），用来检验这个习惯在历史上是否有效；不要写成投资建议。\n"
    "7. self：不超过 30 字，对比他自己猜的物种和你的判断（猜对就肯定一句，猜错就说出差别）；没猜就写空字符串。\n"
    '输出格式：{"species":"","title":"","read":"","moments":["","",""],"gap":"","qube":"","self":""}'
)

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}
_global: list[float] = []


def allow(ip: str) -> bool:
    now = time.time()
    with _lock:
        q = [t for t in _hits.get(ip, []) if now - t < 600]
        g = [t for t in _global if now - t < 3600]
        if len(q) >= 40 or len(g) >= 3000:
            _hits[ip] = q
            _global[:] = g
            return False
        q.append(now)
        g.append(now)
        _hits[ip] = q
        _global[:] = g
        if len(_hits) > 5000:
            for k in list(_hits)[:2500]:
                _hits.pop(k, None)
        return True


def clip(s, n):
    return s.strip()[:n] if isinstance(s, str) else ""


def chat(messages, budget: float, max_tokens: int):
    key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not key:
        return None, None
    t_end = time.time() + budget
    for i, model in enumerate(MODELS):
        left = t_end - time.time()
        if left < 1.2:
            break
        timeout = left if i == len(MODELS) - 1 else max(1.2, left * 0.62)
        body = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "enable_thinking": False,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            txt = data["choices"][0]["message"]["content"]
            txt = txt.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(txt), model
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, ValueError) as e:
            log(f"model {model} failed: {type(e).__name__}")
            continue
    return None, None


def do_line(p):
    facts = {
        "这一关": clip(p.get("level"), 40),
        "他的操作": clip(p.get("did"), 300),
        "系统印章": clip(p.get("stamp"), 80),
        "这一关的教训": clip(p.get("lesson"), 120),
    }
    out, model = chat([
        {"role": "system", "content": SYS_COMMON + LINE_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ], budget=5.2, max_tokens=120)
    line = clip((out or {}).get("line"), 48)
    return ({"line": line, "model": model} if line else None)


def do_judge(p):
    levels = p.get("levels") if isinstance(p.get("levels"), list) else []
    levels = [{"关": clip(x.get("name"), 40), "操作": clip(x.get("did"), 300), "印章": clip(x.get("stamp"), 80)} for x in levels[:4] if isinstance(x, dict)]
    if not levels:
        return None
    sc = p.get("scores") if isinstance(p.get("scores"), dict) else {}
    sc = {k: round(float(v), 2) for k, v in sc.items() if k in SPECIES and isinstance(v, (int, float))}
    guess = p.get("guess") if p.get("guess") in SPECIES else None
    facts = {"四关": levels, "本地得分": sc, "玩家自己猜": SPECIES[guess].split("：")[0] + f"（{guess}）" if guess else "没猜"}
    out, model = chat([
        {"role": "system", "content": SYS_COMMON + JUDGE_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ], budget=8.2, max_tokens=700)
    if not out or out.get("species") not in SPECIES:
        return None
    moments = [clip(m, 40) for m in out.get("moments", []) if isinstance(m, str)][:3] if isinstance(out.get("moments"), list) else []
    return {
        "species": out["species"],
        "title": clip(out.get("title"), 14),
        "read": clip(out.get("read"), 160),
        "moments": [m for m in moments if m],
        "gap": clip(out.get("gap"), 160),
        "qube": clip(out.get("qube"), 110),
        "self": clip(out.get("self"), 44) if guess else "",
        "model": model,
    }


def log(msg):
    sys.stderr.write(time.strftime("%H:%M:%S ") + msg + "\n")
    sys.stderr.flush()


class H(BaseHTTPRequestHandler):
    server_version = "ts-judge"

    def log_message(self, *a):
        pass

    def send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def route(self):
        p = self.path.split("?")[0]
        return p.removeprefix("/ts-api")

    def do_GET(self):
        if self.route() == "/health":
            return self.send(200, {"ok": True, "key": bool(os.environ.get("DASHSCOPE_API_KEY")), "models": MODELS})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        path = self.route()
        if path not in ("/line", "/judge"):
            return self.send(404, {"error": "not found"})
        ip = (self.headers.get("X-Real-IP") or self.headers.get("X-Forwarded-For", "").split(",")[0] or self.client_address[0]).strip()
        if not allow(ip):
            return self.send(429, {"error": "slow down"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_BODY:
            return self.send(413, {"error": "bad size"})
        try:
            p = json.loads(self.rfile.read(n))
            assert isinstance(p, dict)
        except Exception:
            return self.send(400, {"error": "bad json"})
        t0 = time.time()
        res = do_line(p) if path == "/line" else do_judge(p)
        log(f"{path} {'ok' if res else 'fallback'} {time.time() - t0:.2f}s {res.get('model') if res else '-'}")
        if not res:
            return self.send(503, {"error": "ai unavailable"})
        self.send(200, res)


if __name__ == "__main__":
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer((HOST, PORT), H)
    log(f"ts-judge on {HOST}:{PORT} models={MODELS} key={'yes' if os.environ.get('DASHSCOPE_API_KEY') else 'no'}")
    srv.serve_forever()
