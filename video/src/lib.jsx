import React, {useContext, useSyncExternalStore} from 'react';
import {FilmClock, ShotContext, useShotState} from './film-store.js';
import plan from '../plan.json';
import paths from '../../h5/src/arcade/paths.json';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const prog = (t, at, d) => clamp((t - at) / d);
export const eo = x => 1 - Math.pow(1 - x, 3);
export const ex = x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
export const eio = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
export const sio = x => -(Math.cos(Math.PI * x) - 1) / 2;
export const lerp = (a, b, x) => a + (b - a) * x;

/** 镜头内时间（秒） */
export const useT = () => useShotState(l => Math.round(l * 1000) / 1000);
export const useShot = () => useContext(ShotContext);
/** 镜头时长 */
export const useDur = () => { const s = useShot(); return s.end - s.start; };

/** 入场：at 秒开始，d 秒内从偏移位置落定 */
export function rise(t, at, {d = 0.5, y = 30, x = 0, s = 1, e = eo} = {}) {
  const k = e(prog(t, at, d));
  return {opacity: k, transform: `translate(${(1 - k) * x}px, ${(1 - k) * y}px) scale(${lerp(s, 1, k)})`};
}
export const fadeOut = (t, at, d = 0.4) => 1 - prog(t, at, d);

export const art = n => `art/${n}.webp`;
export const pr = n => `print/${n}.png`;

export function Stamp({t, at, children, style, ink = false, rot = -6, size = 72}) {
  const k = prog(t, at, 0.18);
  const spread = prog(t, at + 0.12, 0.5);
  const s = lerp(2.4, 1, ex(k));
  return <div className={'stamp' + (ink ? ' ink' : '')} style={{fontSize: size, opacity: k > 0 ? Math.min(1, k * 1.6) : 0,
    transform: `rotate(${rot}deg) scale(${s})`, filter: `blur(${(1 - spread) * 0.8}px)`, ...style}}>{children}</div>;
}

/** 卡牌翻面：p 0 = 背面，1 = 正面 */
export function Flip({front, back, p, w, h, style, cls = 'card'}) {
  const a = p * 180;
  const showFront = a > 90;
  return <div className="abs" style={{width: w, height: h, perspective: 1600, ...style}}>
    <div className={cls} style={{width: w, height: h, left: 0, top: 0, transform: `rotateY(${showFront ? a - 180 : a}deg)`}}>
      <img src={showFront ? front : back} alt="" />
    </div>
  </div>;
}

export const LEVELS = paths.levels;

/** 真实走势线（Panda Data 收盘价）。p 是画到哪儿（0–1），upto 是只画到某个日期 */
export function Chart({id, w, h, p = 1, color = 'var(--ink)', width = 5, from = 0, to, style, fill, dot = true, mask = null}) {
  const L = LEVELS[id];
  const c = L.close.slice(from, to ?? L.close.length);
  const lo = Math.min(...c), hi = Math.max(...c);
  const pts = c.map((v, i) => [i / (c.length - 1) * w, h - (v - lo) / (hi - lo || 1) * h]);
  const n = Math.max(2, Math.round(pts.length * clamp(p)));
  const shown = pts.slice(0, n);
  const d = shown.map(([x, y], i) => (i ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1)).join(' ');
  const last = shown[shown.length - 1];
  return <svg className="abs" width={w} height={h} style={{overflow: 'visible', ...style}}>
    {fill && <path d={d + ` L${last[0]} ${h} L0 ${h} Z`} fill={fill} />}
    <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinejoin="round" strokeLinecap="round" />
    {dot && p > 0 && p < 1 && <circle cx={last[0]} cy={last[1]} r={width * 2.2} fill={color} />}
  </svg>;
}
/** 走势线上第 p 处的 x、y（转场跟着线走） */
export function chartPoint(id, w, h, p) {
  const c = LEVELS[id].close, lo = Math.min(...c), hi = Math.max(...c);
  const i = Math.round((c.length - 1) * clamp(p));
  return [i / (c.length - 1) * w, h - (c[i] - lo) / (hi - lo) * h];
}

/** 手机：贴当前时刻的录屏帧。zoom = {s, y}：推近倍数和对准的页面高度比例 */
export function Phone({t, style, zoom, scale = 1, clipIndex}) {
  const s = useShot();
  const clips = s.clips || [];
  let i = clips.length - 1;
  while (i > 0 && clips[i].at > t) i--;
  const c = clips[i];
  let img = null;
  if (c) {
    const f = clamp(Math.floor((t - c.at) * plan.fps) + 1, 1, c.frames || 1);
    img = `clips/${s.id}_${clipIndex ?? i}/${String(f).padStart(4, '0')}.jpg`;
  }
  const z = zoom || {s: 1, y: 0};
  return <div className="phone" style={{transform: `scale(${scale})`, transformOrigin: '50% 50%', ...style}}>
    <div className="scr">{img && <img src={img} alt="" style={{transform: `scale(${z.s})`, transformOrigin: `50% ${z.y * 100}%`}} />}</div>
  </div>;
}

/** 全片字幕 + 免责声明（不随镜头淡入淡出） */
export function Captions() {
  const t = useSyncExternalStore(FilmClock.subscribe, FilmClock.get, FilmClock.get);
  const c = plan.captions.find(x => t >= x.start - 0.05 && t < x.end + 0.12);
  const film = t >= (plan.boundary ?? 1e9) ? 'board' : 'promo';
  const hideDisc = plan.shots.some(s => ['endcard', 'b16'].includes(s.id) && t >= s.end - 4.2 && t < s.end + 0.1);
  return <>
    <div className={'captions ' + film}>{c && <span>{c.text}</span>}</div>
    {!hideDisc && <div className={'disclaimer ' + film}>投资者教育游戏 · 不构成投资建议</div>}
  </>;
}
