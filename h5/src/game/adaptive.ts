import { SCENES, type Scene } from "../data";
import { profileOf } from "./engine";
import { aiPick, PICKABLE, sp, type SpeciesId } from "./meta";
import type { Game } from "./store";

const ORDER = ["s924", "s2015", "smt", "scb", "squant", "soil"];

export const playedIds = (g: Game) => g.seasons.filter((r) => r.scene && r.option).map((r) => r.scene!);

export interface NextScene { scene: Scene; a: SpeciesId; b: SpeciesId; why: string }

/**
 * 下一场去哪：找出画像里最需要分清的两种物种（游戏里最像的 vs 自评或第二像的），
 * 再挑一场这两种物种在 AI 剧本里做法分歧最大的。只说“分歧大”，不说谁会选哪个，免得带偏选择。
 */
export function suggestNext(g: Game): NextScene | null {
  const played = new Set(playedIds(g));
  const pool = ORDER.map((id) => SCENES.find((s) => s.id === id)).filter((s): s is Scene => !!s && !played.has(s.id));
  if (!pool.length) return null;
  const p = profileOf(g);
  const score: Record<string, number> = {};
  g.seasons.forEach((r) => Object.entries(r.icons || {}).forEach(([k, v]) => (score[k] = (score[k] || 0) + (v as number) * 0.1)));
  Object.entries(p.coins).forEach(([k, v]) => (score[k] = (score[k] || 0) + (v as number)));
  const fixed = (id?: string): id is SpeciesId => !!id && id !== "chameleon" && id !== "beaver";
  const ranked = (Object.entries(score).sort((x, y) => y[1] - x[1]).map((e) => e[0]) as SpeciesId[]).filter(fixed);
  const a: SpeciesId = ranked[0] || (fixed(g.self) ? g.self : "cheetah");
  const b: SpeciesId = (fixed(g.self) && g.self !== a ? g.self : ranked.find((x) => x !== a))
    || PICKABLE.map((s) => s.id).find((id) => fixed(id) && id !== a)!;

  let best = pool[0];
  let bestScore = -1;
  for (const s of pool) {
    const pa = aiPick(a, s.id);
    const pb = aiPick(b, s.id);
    const sc = (pa.option !== pb.option ? 2 : 0) + (pa.reason !== pb.reason ? 1 : 0) + (s.tier === "P0" ? 0.5 : 0);
    if (sc > bestScore) {
      best = s;
      bestScore = sc;
    }
  }
  const A = sp(a).cn;
  const B = sp(b).cn;
  let why: string;
  if (g.self && g.self === b && g.self !== a) why = `你觉得自己像${B}，这次的做法更像${A}。在这一场，${A}和${B}的做法分歧最大，最能分清你到底更像谁。`;
  else if (g.self && g.self === a) why = `这次的做法和你的自评一致，都像${A}。再来一场，看看是每次都这样，还是会露出${B}的一面。`;
  else why = `目前你最像${A}，其次是${B}。在这一场，它俩的做法分歧最大，最能分清你更像谁。`;
  return { scene: best, a, b, why };
}
