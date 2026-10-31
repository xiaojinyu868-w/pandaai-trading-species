// plan.json 里每个镜头 id → 视图；builder 只负责镜头之间的交叉淡入，画面本身是镜头内时间的纯函数。
import * as P from './promo.jsx';
import * as B from './board.jsx';
import {shots, shot, onDrive} from '../engine.js';

export const SHOT_VIEWS = {
  hook: P.Hook, montage: P.Montage, choices: P.Choices, title: P.Title, blind: P.Blind, clues: P.Clues, game: P.Game,
  reveal: P.Reveal, judge: P.Judge, species: P.Species, demo: P.Demo, handoff: P.Handoff, endcard: P.EndCard,
  btitle: B.BTitle, b01: B.B01, b02: B.B02, b03: B.B03, b04: B.B04, b05: B.B05, b06: B.B06, b07: B.B07, b08: B.B08,
  b09: B.B09, b10: B.B10, b11: B.B11, b12: B.B12, b13: B.B13, b14: B.B14, b15: B.B15, b16: B.B16,
};

const CUT = new Set(['hook', 'title', 'btitle']);
const enter = id => tl => {
  const s = shot(id);
  const el = document.querySelector(`section[data-shot="${id}"]`);
  if (CUT.has(id)) tl.set(el, {opacity: 1}, s.start);
  else tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 0.45, ease: 'none'}, s.start);
  onDrive(id, async () => {
    const imgs = [...el.querySelectorAll('img')];
    await Promise.all(imgs.map(i => (i.complete && i.naturalWidth ? null : i.decode().catch(() => {}))));
    await document.fonts.ready;
  });
};
export const SHOT_BUILDERS = Object.fromEntries(shots.map(s => [s.id, enter(s.id)]));
