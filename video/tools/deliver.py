#!/usr/bin/env python3.11
"""拼接分段渲染 + 母带音轨 → 提交版 / 宣传片 / 桌游玩法三条成片与字幕。

用法：python3.11 tools/deliver.py --parts /tmp/ts-video/parts/a.mp4 b.mp4 c.mp4
"""
import argparse, json, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE.parent / '提交材料' / '视频'


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def ts(t):
    ms = int(round(t * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def srt(caps, off, path):
    lines = [f'{i}\n{ts(c["start"] - off)} --> {ts(c["end"] - off)}\n{c["text"]}\n' for i, c in enumerate(caps, 1)]
    path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parts', nargs='+', required=True)
    a = ap.parse_args()
    plan = json.loads((HERE / 'plan.json').read_text())
    B, D = plan['boundary'], plan['duration']
    OUT.mkdir(parents=True, exist_ok=True)

    lst = HERE / 'renders' / 'parts.txt'
    lst.parent.mkdir(exist_ok=True)
    lst.write_text(''.join(f"file '{Path(p).resolve()}'\n" for p in a.parts))
    silent = HERE / 'renders' / 'full-silent.mp4'
    ff('-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(silent))

    full = OUT / '交易物种起源_提交版_宣传片+桌游玩法.mp4'
    ff('-i', str(silent), '-i', str(HERE / 'assets' / 'master.wav'), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
       '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', str(D), '-movflags', '+faststart', str(full))
    silent.unlink()

    enc = ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart']
    promo = OUT / '交易物种起源_宣传片.mp4'
    board = OUT / '交易物种起源_桌游玩法.mp4'
    ff('-i', str(full), '-t', str(B), *enc, str(promo))
    ff('-ss', str(B), '-i', str(full), '-t', str(D - B), *enc, str(board))

    caps = plan['captions']
    srt(caps, 0, full.with_suffix('.srt'))
    srt([c for c in caps if c['start'] < B], 0, promo.with_suffix('.srt'))
    srt([c for c in caps if c['start'] >= B], B, board.with_suffix('.srt'))
    for p in (full, promo, board):
        d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip()
        print(p.name, d, f'{p.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
