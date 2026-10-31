#!/usr/bin/env python3.11
"""配乐 + 音效 + 旁白混音 → assets/master.wav 与 evidence/audio-mix.json。

配乐与音效全部由 numpy 现场合成（无第三方音频素材）；旁白来自 assets/vo/*.wav。
用法：python3.11 tools/audio.py
"""
import hashlib, json, subprocess, wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, resample_poly, sosfilt

HERE = Path(__file__).resolve().parent.parent
SR = 48000
rng = np.random.default_rng(7)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def add(buf, at, x, g=1.0):
    i = int(round(at * SR))
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += g * x[:j - i]


# ---------- 乐器 ----------
def pluck(n, dur=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.04)
    return x * env(len(t), 0.003, 0.22)


def epiano(n, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    x = np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.3))
    x += 0.2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.4)
    return x * env(len(t), 0.004, 0.9) * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))


def pad(notes, dur):
    t = np.arange(int(dur * SR)) / SR
    x = sum(sum(np.sin(2 * np.pi * hz(n) * k * t * (1 + 0.0015 * j)) / k ** 1.6 for k in (1, 2, 3)) for j, n in enumerate(notes))
    a = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6)
    return lp(x * a / len(notes), 1800)


def bass(n, dur=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.005, 0.35)


def kick(dur=0.3):
    t = np.arange(int(dur * SR)) / SR
    f = 45 + 80 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.12)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def hat(dur=0.06):
    return hp(noise(dur), 7000) * env(int(dur * SR), 0.001, 0.015)


def brush(dur=0.22):
    return bp(noise(dur), 1500, 6000) * env(int(dur * SR), 0.002, 0.06)


# ---------- 音效 ----------
def sfx_stamp():
    k = kick(0.35) * 1.2
    n = lp(noise(0.18), 900) * env(int(0.18 * SR), 0.001, 0.03) * 2.5
    x = k.copy()
    x[:len(n)] += n
    return x


def sfx_tick():
    d = 0.16
    s = bp(noise(d), 2200, 5500) * env(int(d * SR), 0.01, 0.05)
    return s * (0.6 + 0.4 * np.sin(np.linspace(0, 9 * np.pi, len(s))) ** 2)


def sfx_flip():
    d = 0.32
    t = np.linspace(0, 1, int(d * SR))
    x = noise(d)
    out = np.zeros_like(x)
    for a, b, f in ((0, .5, 1200), (.5, 1, 3500)):
        m = (t >= a) & (t < b)
        out[m] = bp(x, f * 0.6, f * 1.6)[m]
    return out * np.sin(np.pi * t) ** 1.5 * 0.9


def sfx_whoosh():
    d = 0.5
    t = np.linspace(0, 1, int(d * SR))
    return lp(noise(d), 2500) * np.sin(np.pi * t) ** 2 * 0.5


def sfx_dice():
    out = np.zeros(int(0.9 * SR))
    at = 0.0
    for i in range(7):
        c = bp(noise(0.03), 1800, 7000) * env(int(0.03 * SR), 0.0005, 0.006) * (1 - i * 0.1)
        add(out, at, c)
        at += 0.05 + rng.random() * 0.1
    return out * 2


def sfx_coin():
    d = 0.8
    t = np.arange(int(d * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, a, dd in ((2093, 1, .35), (3390, .6, .25), (5230, .35, .15), (7020, .2, .08)))
    return x * env(len(t), 0.001, 1.0) * 0.5


def sfx_beep(f=880, d=0.18):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * t) * env(len(t), 0.003, 0.06) * 0.6


def sfx_hold(d=1.4):
    t = np.arange(int(d * SR)) / SR
    f = 330 + 110 * np.minimum(1, t / 0.5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return x * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.4) * 0.25


def sfx_hit():
    d = 1.6
    t = np.arange(int(d * SR)) / SR
    return kick(d) * 0.9 + hp(noise(d), 4000) * np.exp(-t / 0.5) * 0.25


SFX = {'stamp': sfx_stamp, 'tick': sfx_tick, 'flip': sfx_flip, 'whoosh': sfx_whoosh, 'dice': sfx_dice, 'coin': sfx_coin,
       'beep': sfx_beep, 'beephi': lambda: sfx_beep(1320, 0.3), 'hold': sfx_hold, 'hit': sfx_hit}
GAIN = {'stamp': .55, 'tick': .35, 'flip': .45, 'whoosh': .35, 'dice': .5, 'coin': .4, 'beep': .4, 'beephi': .45, 'hold': .5, 'hit': .5}

# 镜头内时间（与 src/shots/*.jsx 中的 at 一致）
CUES = {
    'hook': [('stamp', 5.6)],
    'montage': [('stamp', 3.45), ('stamp', 6.05), ('stamp', 8.45)],
    'choices': [('stamp', 6.0)],
    'title': [('hit', 0.0), ('stamp', 0.9)],
    'blind': [('stamp', 4.6)],
    'clues': [('hold', 5.85)],
    'judge': [('tick', 1.9), ('tick', 2.6), ('tick', 3.4), ('stamp', 5.0)],
    'species': [('stamp', 7.2)],
    'handoff': [('whoosh', 0.3)],
    'btitle': [('flip', 0.2)],
    'b03': [('flip', 5.6)],
    'b04': [('dice', 0.6)],
    'b05': [('flip', 1.7), ('stamp', 6.0), ('stamp', 6.9)],
    'b06': [('tick', 1.9), ('tick', 2.4), ('coin', 3.4)],
    'b07': [('flip', 2.7)],
    'b08': [('tick', 2.6), ('tick', 3.6), ('tick', 5.0), ('flip', 6.8), ('beep', 7.6), ('beep', 8.45), ('beep', 9.3), ('flip', 10.2), ('stamp', 10.3)],
    'b09': [('tick', 1.0), ('tick', 1.3), ('tick', 2.2), ('tick', 3.3), ('stamp', 5.6)],
    'b10': [('flip', 0.6), ('whoosh', 5.0), ('whoosh', 7.2), ('whoosh', 9.6), ('whoosh', 11.4)],
    'b12': [('coin', 2.4), ('coin', 2.95), ('coin', 3.5), ('coin', 4.05), ('stamp', 6.3)],
    'b15': [('flip', 3.4), ('flip', 3.5)],
}


# ---------- 配乐 ----------
def promo_music(dur, shots):
    out = np.zeros(int(dur * SR))
    beat = 60 / 100
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]
    full_from, end_from = shots['montage']['start'], shots['endcard']['start']
    bar = 0
    t = 0.0
    while t < dur:
        root, ch = prog[bar % 4]
        add(out, t, pad([n + 12 for n in ch], beat * 4 + 0.6), 0.10)
        if t >= full_from - 0.01 and t < end_from:
            for b in range(4):
                tb = t + b * beat
                add(out, tb, bass(root - 12, beat * 0.9), 0.30)
                if b in (0, 2):
                    add(out, tb, kick(), 0.45)
                else:
                    add(out, tb, brush(), 0.16)
                add(out, tb + beat / 2, hat(), 0.10)
            arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
            for k in range(8):
                add(out, t + k * beat / 2, pluck(arp[k % 4], 0.45), 0.13)
        elif t < full_from:
            for k in range(4):
                add(out, t + k * beat, pluck(ch[k % 3] + 24, 0.6), 0.07)
        t += beat * 4
        bar += 1
    add(out, shots['title']['start'] - 1.6, lp(noise(1.6), 3000) * np.linspace(0, 1, int(1.6 * SR)) ** 2, 0.12)
    add(out, end_from, pad([48, 55, 64, 67], dur - end_from), 0.18)
    fade = np.ones_like(out)
    n = int(1.5 * SR)
    fade[-n:] = np.linspace(1, 0, n)
    return out * fade


def board_music(dur):
    out = np.zeros(int(dur * SR))
    beat = 60 / 84
    prog = [(53, [57, 60, 64, 65]), (52, [55, 59, 62, 64]), (50, [53, 57, 60, 62]), (48, [52, 55, 59, 60])]
    bar = 0
    t = 0.0
    while t < dur:
        root, ch = prog[bar % 4]
        add(out, t, pad(ch, beat * 4 + 0.6), 0.06)
        for k, n in enumerate([ch[0], ch[2], ch[1], ch[3]]):
            add(out, t + k * beat, epiano(n, 1.6), 0.10)
        if bar % 2 == 1:
            add(out, t + 3.5 * beat, epiano(ch[3] + 12, 1.2), 0.06)
        for b in range(4):
            tb = t + b * beat
            if b == 0:
                add(out, tb, bass(root - 12, beat * 1.8), 0.28)
                add(out, tb, kick(), 0.30)
            if b == 2:
                add(out, tb, bass(root - 5, beat * 1.5), 0.20)
                add(out, tb, brush(), 0.10)
            add(out, tb + beat / 2, hat(), 0.05)
        t += beat * 4
        bar += 1
    fade = np.ones_like(out)
    a, z = int(1.2 * SR), int(3.0 * SR)
    fade[:a] = np.linspace(0, 1, a)
    fade[-z:] = np.linspace(1, 0, z)
    return out * fade


def load_vo(p):
    with wave.open(str(p)) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = Path(p).read_bytes()[44:]
    x = np.frombuffer(raw[:len(raw) // (sw * ch) * sw * ch], dtype=np.int16).astype(np.float64) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        g = np.gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g)
    return x


def smooth_env(x, att=0.08, rel=0.45):
    a, r = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    lvl = np.abs(x)
    blk = 480
    m = lvl[:len(lvl) // blk * blk].reshape(-1, blk).max(1)
    m = np.append(m, lvl[len(lvl) // blk * blk:].max() if len(lvl) % blk else [])
    g = (m > 0.02).astype(float)
    e = np.zeros_like(g)
    v = 0.0
    ab, rb = a ** blk, r ** blk
    for i, s in enumerate(g):
        v = s + (v - s) * (ab if s > v else rb)
        e[i] = v
    return np.repeat(e, blk)[:len(x)]


def main():
    plan_p = HERE / 'plan.json'
    plan = json.loads(plan_p.read_text())
    dur, B = plan['duration'], plan['boundary']
    shots = {s['id']: s for s in plan['shots']}
    N = int(dur * SR)

    music = np.zeros(N)
    pm = promo_music(B, shots)
    music[:len(pm)] += pm
    bm = board_music(dur - B)
    add(music, B, bm)

    vo = np.zeros(N)
    for c in plan['voice']:
        x = load_vo(HERE / c['file'])
        rms = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2))
        add(vo, c['at'], x * (0.16 / rms))

    sfx = np.zeros(N)
    cues = []
    for sid, lst in CUES.items():
        s = shots[sid]
        for kind, at in lst:
            T = s['start'] + at
            if T >= s['end']:
                continue
            add(sfx, T, SFX[kind](), GAIN[kind])
            cues.append({'at': round(T, 3), 'shot': sid, 'kind': kind, 'role': 'sfx', 'source': 'numpy 合成（tools/audio.py）'})

    duck_db = 9.0
    e = smooth_env(vo)
    music_ducked = music * (1 - (1 - 10 ** (-duck_db / 20)) * e)
    mix = vo + music_ducked + sfx
    mix = np.tanh(mix * 1.1) / 1.1

    out = HERE / 'assets'
    raw = out / 'mix-raw.wav'
    master = out / 'master.wav'
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(raw), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(master)], check=True)
    raw.unlink()

    report = {
        'planSha256': sha(plan_p),
        'master': {'file': 'assets/master.wav', 'sha256': sha(master)},
        'music': {'source': 'numpy 合成（tools/audio.py）：宣传片 100 BPM 小调拨弦，桌游片 84 BPM 电钢琴'},
        'voice': [{'id': c['id'], 'at': c['at'], 'file': c['file']} for c in plan['voice']],
        'cues': cues,
        'ducking': {'musicDuckUnderSpeechDb': duck_db, 'attack': 0.08, 'release': 0.45},
        'loudness': 'ffmpeg loudnorm I=-16 TP=-1.5',
    }
    (HERE / 'evidence' / 'audio-mix.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'duration': dur, 'cues': len(cues), 'voice': len(plan['voice'])}))


if __name__ == '__main__':
    main()
