// 全部音效用 WebAudio 现场合成，不下载音频文件。
let ctx: AudioContext | null = null;
let muted = localStorage.getItem("ts-muted") === "1";

export const isMuted = () => muted;
export function setMuted(v: boolean) {
  muted = v;
  localStorage.setItem("ts-muted", v ? "1" : "0");
}

function ac(): AudioContext | null {
  if (muted) return null;
  try {
    if (!ctx) ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  } catch {
    return null;
  }
}

function tone(freq: number, dur: number, type: OscillatorType = "sine", gain = 0.18, when = 0, slideTo?: number) {
  const c = ac();
  if (!c) return;
  const t = c.currentTime + when;
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, t);
  if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(gain, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(c.destination);
  o.start(t);
  o.stop(t + dur + 0.05);
}

function noise(dur: number, gain = 0.2, when = 0, freq = 1800, q = 0.8) {
  const c = ac();
  if (!c) return;
  const t = c.currentTime + when;
  const len = Math.max(1, Math.floor(c.sampleRate * dur));
  const buf = c.createBuffer(1, len, c.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
  const src = c.createBufferSource();
  src.buffer = buf;
  const f = c.createBiquadFilter();
  f.type = "bandpass";
  f.frequency.value = freq;
  f.Q.value = q;
  const g = c.createGain();
  g.gain.value = gain;
  src.connect(f).connect(g).connect(c.destination);
  src.start(t);
}

export function buzz(pattern: number | number[]) {
  if (muted) return;
  try {
    navigator.vibrate?.(pattern);
  } catch {
    /* 不支持震动的浏览器直接忽略 */
  }
}

/** 行情“听得见”：价格越高音越高，ratio 是现价 ÷ 参考价 */
export function blip(ratio: number) {
  tone(Math.min(1500, Math.max(180, 420 * ratio)), 0.04, "triangle", 0.045);
}

export const sfx = {
  tap: () => tone(660, 0.06, "triangle", 0.08),
  thud: () => tone(140, 0.22, "sine", 0.22, 0, 70),
  crowd: () => [0, 0.4, 0.9, 1.5, 2.1].forEach((w, i) => noise(1.1, 0.045, w, 420 + (i % 3) * 190, 0.5)),
  hop: () => tone(520, 0.09, "triangle", 0.12, 0, 820),
  dice: () => {
    for (let i = 0; i < 7; i++) noise(0.05, 0.25, i * 0.07, 2600 + Math.random() * 1500, 2);
  },
  land: () => {
    noise(0.12, 0.35, 0, 400, 1);
    tone(180, 0.15, "sine", 0.2);
  },
  stamp: () => {
    noise(0.16, 0.6, 0, 220, 0.7);
    tone(90, 0.25, "sine", 0.35, 0, 50);
    buzz(40);
  },
  paper: () => noise(0.35, 0.18, 0, 3200, 0.5),
  coin: () => {
    tone(1568, 0.16, "square", 0.05);
    tone(2093, 0.4, "square", 0.05, 0.08);
  },
  gain: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.22, "triangle", 0.12, i * 0.07)),
  loss: () => [392, 330, 262].forEach((f, i) => tone(f, 0.3, "sawtooth", 0.06, i * 0.12)),
  bell: () => {
    [880, 1320, 1760, 2640].forEach((f, i) => tone(f, 1.6 - i * 0.25, "sine", 0.12 / (i + 1)));
    buzz([60, 40, 60]);
  },
  alarm: () => {
    for (let i = 0; i < 4; i++) tone(880, 0.22, "square", 0.07, i * 0.45, 440);
    buzz([200, 100, 200, 100, 200]);
  },
  heart: (when = 0) => {
    tone(60, 0.12, "sine", 0.4, when);
    tone(55, 0.14, "sine", 0.3, when + 0.18);
  },
  tick: () => tone(1200, 0.03, "square", 0.04),
  lock: () => {
    tone(300, 0.08, "square", 0.1);
    tone(200, 0.12, "square", 0.1, 0.09);
    buzz([30, 30, 30]);
  },
  reveal: () => {
    noise(0.6, 0.2, 0, 1200, 0.3);
    [392, 523, 659, 784].forEach((f, i) => tone(f, 0.5, "triangle", 0.08, 0.25 + i * 0.09));
  },
  crack: () => {
    noise(0.08, 0.5, 0, 3000, 3);
    noise(0.1, 0.4, 0.15, 2500, 3);
    noise(0.2, 0.5, 0.35, 1800, 2);
  },
  fanfare: () => [523, 659, 784, 1046, 784, 1046].forEach((f, i) => tone(f, 0.28, "triangle", 0.1, i * 0.12)),
};
