"""旁白配音：阿里云百炼 Qwen-TTS。密钥运行时从环境变量或 /etc/life-plaza/runtime.env 读取，不落盘、不打印。

  python3.11 tools/tts.py --text "……" --voice Ethan --out a.wav
  python3.11 tools/tts.py --script narration.json --outdir assets/vo
"""
import argparse, json, os, sys, urllib.request
from pathlib import Path

URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


def key():
    k = os.environ.get("DASHSCOPE_API_KEY")
    if k:
        return k
    for line in open("/etc/life-plaza/runtime.env"):
        if line.startswith("DASHSCOPE_API_KEY="):
            return line.split("=", 1)[1].strip().strip("'\"")
    sys.exit("DASHSCOPE_API_KEY missing")


def say(text, voice, out, model):
    body = json.dumps({"model": model, "input": {"text": text, "voice": voice, "language_type": "Chinese"}}).encode()
    req = urllib.request.Request(URL, body, {"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    u = d.get("output", {}).get("audio", {}).get("url")
    if not u:
        raise RuntimeError(json.dumps(d, ensure_ascii=False)[:300])
    with urllib.request.urlopen(u, timeout=90) as r:
        Path(out).write_bytes(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text"); ap.add_argument("--out")
    ap.add_argument("--script"); ap.add_argument("--outdir")
    ap.add_argument("--voice", default="Ethan"); ap.add_argument("--model", default="qwen3-tts-flash")
    a = ap.parse_args()
    if a.text:
        say(a.text, a.voice, a.out, a.model); print(a.out); return
    lines = json.loads(Path(a.script).read_text())
    od = Path(a.outdir); od.mkdir(parents=True, exist_ok=True)
    for ln in lines:
        p = od / f"{ln['id']}.wav"
        if p.exists() and not ln.get("redo"):
            continue
        say(ln["text"], ln.get("voice", a.voice), p, a.model); print(p)


if __name__ == "__main__":
    main()
