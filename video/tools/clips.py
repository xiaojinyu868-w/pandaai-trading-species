"""把 plan.json 里每个镜头用到的录屏片段抽成 30 fps 的 JPEG 序列，片子按时间逐帧贴图。

  python3.11 tools/clips.py [--raw /tmp/ts-video/raw] [--out /tmp/ts-video/clips]
"""
import argparse, json, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/tmp/ts-video/raw")
    ap.add_argument("--out", default="/tmp/ts-video/clips")
    a = ap.parse_args()
    plan = json.loads((HERE / "plan.json").read_text())
    out = Path(a.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    n = 0
    for s in plan["shots"]:
        for i, c in enumerate(s.get("clips", [])):
            d = out / f"{s['id']}_{i}"
            d.mkdir()
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(c["from"]), "-t", str(c["len"]), "-i", str(Path(a.raw) / f"{c['src']}.webm"),
                            "-vf", f"crop=390:844:0:0,setpts=PTS/{c['speed']},fps={plan['fps']}", "-q:v", "3", str(d / "%04d.jpg")], check=True)
            c["frames"] = len(list(d.glob("*.jpg")))
            n += c["frames"]
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    link = HERE / "public" / "clips"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(out)
    print(json.dumps({"frames": n}))


if __name__ == "__main__":
    main()
