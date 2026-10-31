import type { EvKind, OptKey, Scene } from "../data";
import { aiPick, type Reason } from "../game/meta";
import type { Foe, Run } from "./Game";
import { LEVELS, ticksOf, tickOf, type Level } from "./levels";

/** 小游戏和桌游之间的桥：同一个名场面，桌游按印刷的牌结算，线上按手上真实的操作结算 */

export const levelOf = (sceneId?: string) => LEVELS.find((l) => l.id === sceneId);

/** AI 对手照桌游里自己的牌出手，在同一段行情里跑一遍 */
export function foeRun(l: Level, aiId: string, cap: number): { foe: Foe; eq: number } {
  const { p } = ticksOf(l);
  const pick = aiPick(aiId, l.id as never);
  const D = tickOf(l, l.decide, "close");
  const shares = { A: l.id === "s924" ? 2 : 3, B: l.id === "s924" ? 1 : 2, C: l.id === "s924" ? 0 : 1, D: 0 }[pick.option];
  const target = shares / 2;
  const hol = l.holiday ? tickOf(l, l.holiday.close, "close") : -1;
  const lock = new Set((l.lock || []).map((d) => tickOf(l, d, "open")));
  const halts = (l.halts || []).map((d) => tickOf(l, d, "close"));
  const trades: Foe["trades"] = [];
  let pos = l.startIn ? 1 : 0;
  let eq = cap;
  let entry = l.startIn ? p[0] : 0;
  let cut = false;
  const set = (k: number, v: number) => {
    v = Math.max(0, v);
    if (v === pos) return;
    trades.push({ i: k, k: v > pos ? "buy" : "sell" });
    if (v > pos) entry = p[k];
    pos = v;
  };
  for (let k = 0; k < p.length; k++) {
    if (k > 0) eq *= 1 + pos * (p[k] / p[k - 1] - 1);
    if (k === D) {
      if (l.id === "s924") {
        if (pick.option === "B") set(k, 0.5);
      } else set(k, target);
    }
    if (l.id === "s924" && k === hol + 1) {
      if (pick.option === "A") set(k, 1);
      if (pick.ff === "enter" && pos === 0) set(k + 2, 0.5);
      if (pick.ff === "sell") set(k + 1, 0);
    }
    if (l.id === "s2015" && pick.ff === "sell" && k > D && pos > 0 && !lock.has(k) && k === D + 3) set(k, 0);
    if (l.id === "smt" && pick.ff === "sell" && k === D + 1) set(k, pos / 2 >= 0.5 ? pos / 2 : 0);
    if (l.id === "scb") {
      if (k === halts[1]) {
        if (pick.ff === "sell") set(k, pos - 0.5);
        if (pick.ff === "add") set(k, pos + 0.5);
      }
      if (k === halts[3]) {
        if (pick.second === "add") set(k, pos + 0.5);
        if (pick.second === "stop") set(k, 0);
      }
    }
    if (pick.plan === "cut" && !cut && pos > 0 && entry && p[k] <= entry * 0.95) {
      cut = true;
      set(k, 0);
    }
    if (eq <= 0) {
      eq = 0;
      set(k, 0);
      break;
    }
  }
  return { foe: { id: aiId, trades: trades.filter((t) => t.i < p.length) }, eq };
}

/** 决策日那天你手里有几份：按住 = 满仓 2 份，借了钱再往上加 */
function sharesAt(l: Level, r: Run, k: number) {
  let held = l.startIn;
  for (const t of r.trades) {
    if (t.i > k) break;
    held = t.k === "buy";
  }
  if (!held) return 0;
  return r.lev >= 2 && r.levAt !== undefined ? 3 : 2;
}

/** 把手上的操作折回印刷委托单上的选项，画像、驿站、资金榜都按它对照桌游 */
export function optionOf(l: Level, scene: Scene, r: Run): OptKey {
  const D = tickOf(l, l.decide, "close");
  const n = sharesAt(l, r, D + (l.id === "s924" ? 1 : 0));
  const near = [...scene.options].sort((a, b) => Math.abs(a.shares - n) - Math.abs(b.shares - n));
  if (l.id === "s924" && n === 0) return r.trades.some((t) => t.k === "buy") ? "C" : "D";
  return near[0].key;
}

/** 理由不再让你选：你最后翻开、最在意的那张线索，就是你的依据；一张没翻是凭感觉 */
export function reasonOf(evidence: EvKind[], ms: Partial<Record<EvKind, number>>): Reason {
  if (!evidence.length) return "gut";
  const k = [...evidence].sort((a, b) => (ms[b] || 0) - (ms[a] || 0))[0];
  return ({ price: "price", data: "data", news: "news", tip: "follow" } as const)[k];
}
