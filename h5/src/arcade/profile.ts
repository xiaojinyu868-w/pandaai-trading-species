import { sp, type SpeciesId } from "../game/meta";
import { CAP, type Run } from "./Game";
import { levelById, ticksOf, tickOf, type Level } from "./levels";

/** 从四局操作里读出物种。AI 拿这些当材料；AI 不在时，这里的结果直接上屏 */

export interface Stamp { t: string; sub: string; good: boolean | null }
export interface Verdict {
  species: SpeciesId;
  title: string;
  read: string;
  moments: string[];
  gap: string;
  qube: string;
  self: string;
  model: string;
}

interface Leg { a: number; b: number; pa: number; pb: number; lo: number; hi: number }

const pct = (x: number, d = 0) => `${x >= 0 ? "+" : "−"}${Math.abs(x * 100).toFixed(d)}%`;
const abs = (x: number) => `${Math.abs(x * 100).toFixed(0)}%`;

/** 每一段“拿着”：从哪买到哪卖，中间最低、最高 */
export function legs(l: Level, r: Run): Leg[] {
  const { p } = ticksOf(l);
  const out: Leg[] = [];
  let open: number | null = l.startIn ? 0 : null;
  let openP = l.startIn ? p[0] : 0;
  for (const t of r.trades) {
    if (t.k === "buy" && open === null) {
      open = t.i;
      openP = t.p;
    } else if (t.k === "sell" && open !== null) {
      const seg = p.slice(open, t.i + 1);
      out.push({ a: open, b: t.i, pa: openP, pb: t.p, lo: Math.min(t.p, ...seg), hi: Math.max(t.p, ...seg) });
      open = null;
    }
  }
  return out;
}

export function stats(l: Level, r: Run) {
  const { p } = ticksOf(l);
  const L = legs(l, r).filter((g) => g.b > g.a);
  const acts = r.trades.filter((t) => t.why !== "start" && t.why !== "end").length;
  const buys = r.trades.filter((t) => t.k === "buy" && t.why !== "start");
  const run5 = (i: number) => p[i] / p[Math.max(0, i - 10)] - 1;
  const chase = buys.filter((t) => run5(t.i) >= 0.08).length;
  const dip = buys.filter((t) => run5(t.i) <= -0.06).length;
  const deep = Math.min(0, ...L.map((g) => g.lo / g.pa - 1));
  const quick = L.filter((g) => g.b - g.a <= 4).length;
  const cuts = L.filter((g) => g.pb < g.pa).map((g) => g.pb / g.pa - 1);
  const peakI = p.indexOf(Math.max(...p));
  return { L, acts, buys, chase, dip, deep, quick, cuts, peakI, ret: r.eq / CAP - 1, soldStart: r.trades.some((t) => t.k === "sell" && t.why === "start") };
}

function generic(ret: number, acts: number): Stamp {
  if (ret >= 0.15) return { t: "大赚一笔", sub: `这一场赚了 ${abs(ret)}`, good: true };
  if (ret > 0.02) return { t: "赚到了", sub: `这一场赚了 ${abs(ret)}`, good: true };
  if (ret >= -0.02) return acts >= 2 ? { t: "白忙一场", sub: "进进出出，基本打平", good: null } : { t: "原地踏步", sub: "基本没赚没亏", good: null };
  if (ret < -0.15) return { t: "伤筋动骨", sub: `这一场亏了 ${abs(ret)}`, good: false };
  return { t: "小亏离场", sub: `这一场亏了 ${abs(ret)}`, good: false };
}

export function stampOf(l: Level, r: Run): Stamp {
  const s = stats(l, r);
  const lastSell = [...r.trades].reverse().find((t) => t.k === "sell" && t.why !== "end" && t.why !== "start");
  if (l.id === "s924") {
    const hol = tickOf(l, l.holiday!.close, "close");
    const first = r.trades.find((t) => t.k === "buy");
    if (!first) return { t: "踏空了", sub: "整段行情你都在场外看着", good: null };
    if (first.i > hol && s.ret < 0) return { t: "追在山顶", sub: "长假后才排进去，买在了最热的那一刻", good: false };
    if (r.holidayHeld && r.openAct === "sell") return { t: "节后逃顶", sub: "长假前上车，开盘大涨那一下卖掉了", good: true };
    if (r.holidayHeld && r.openAct === "hold" && s.ret < 0.12) return { t: "坐了趟过山车", sub: "节后高开没走，又跌了回去", good: null };
  }
  if (l.id === "s2015") {
    if (r.liq) return { t: "被强平", sub: "亏到只剩 5 万，被人替你卖在了低处", good: false };
    if (r.lockTries > 0 && s.ret < 0) return { t: "跌停卖不掉", sub: `想卖 ${r.lockTries} 次，跌停那天都没卖出去`, good: false };
    if (r.lev > 1 && s.ret < 0) return { t: "借钱的代价", sub: `借了 ${r.lev - 1} 倍，亏也放大了 ${r.lev} 倍`, good: false };
    if (lastSell && s.ret > 0 && lastSell.i >= s.peakI - 6 && lastSell.i <= s.peakI + 10) return { t: "逃顶", sub: "卖在了离最高点不远的地方", good: true };
    if (lastSell && s.ret > 0 && lastSell.i < s.peakI - 6) return { t: "提前下车", sub: "没吃到最后一段，也躲过了暴跌", good: true };
  }
  if (l.id === "smt") {
    const n = r.leftRank;
    if (n === -1) return { t: "见顶前就走了", sub: "在圈子最热的时候离开", good: true };
    if (n === 0) return { t: "第一个松手", sub: "圈里还没人走，你先走了", good: true };
    if (n != null && n <= 5) return { t: "跟着人群走", sub: `你走的时候，圈里已经走了 ${n} 个人`, good: null };
    if (n != null) return { t: "最后几个才走", sub: `圈里走了 ${n} 个人，你才松手`, good: false };
    return { t: "抱到最后", sub: "一直没松手", good: s.ret >= 0 ? null : false };
  }
  if (l.id === "scb") {
    if ((r.haltSold || 0) > 0 && !r.panicBuy) return { t: "割在恐慌里", sub: "熔断后马上卖了，没等到后面的反弹", good: false };
    if (r.panicBuy && s.ret > 0) return { t: "恐慌里买入", sub: "别人最怕的时候，你买了", good: true };
    if (s.acts === 0 && !s.soldStart) return { t: "一动不动", sub: "四次熔断都没松手", good: null };
  }
  return generic(s.ret, s.acts);
}

/** 一局的操作，写成一句给 AI、也给结果页用的中文 */
export function describe(l: Level, r: Run): string {
  const s = stats(l, r);
  const { dates } = ticksOf(l);
  const day = (i: number) => Math.floor(i / 2) + 1;
  const out: string[] = [];
  const buys = s.buys;
  if (l.startIn) out.push(s.soldStart ? "开盘就把手里的货卖了" : "开局拿着");
  else out.push(buys.length ? `第 ${day(buys[0].i)} 个交易日第一次买进（之前一周涨跌 ${pct(ticksOf(l).p[buys[0].i] / ticksOf(l).p[Math.max(0, buys[0].i - 10)] - 1)}）` : "全程没买");
  if (l.id === "s924") {
    if (r.holidayHeld) out.push("长假前就在场里，长假里一直拿着");
    else if (buys.length) out.push("长假前不在场");
    if (r.openAct === "buy") out.push("节后开盘高开 10% 时才买进去");
    if (r.openAct === "sell") out.push("节后开盘高开 10% 时卖掉了");
    if (r.openAct === "hold") out.push("节后高开时继续拿着");
  }
  if (l.id === "s2015") {
    out.push(r.lev > 1 ? `行情涨了 ${abs(r.levAt || 0)} 时借了 ${r.lev - 1} 倍（涨跌 ×${r.lev}）` : "有人借钱给他，他没借");
    if (r.liq) out.push("亏到 5 万被强制平仓");
    if (r.lockTries) out.push(`跌停那几天想卖 ${r.lockTries} 次没卖出去`);
  }
  if (l.id === "smt") {
    const n = r.leftRank;
    out.push(n === -1 ? "见顶之前就离开了抱团圈" : n === 0 ? "见顶后第一个离开抱团圈" : n != null ? `抱团圈走了 ${n} 个人之后才离开` : "抱团圈的人都走了，他还拿着");
  }
  if (l.id === "scb") {
    if (r.haltSold) out.push(`熔断后马上卖出 ${r.haltSold} 次`);
    if (r.panicBuy) out.push("在连续熔断的恐慌里买进");
    if (!r.haltSold && !r.panicBuy && s.acts === 0) out.push("四次熔断都没动");
  }
  if (s.acts >= 4) out.push(`一共买卖 ${s.acts} 次`);
  if (s.deep <= -0.08) out.push(`拿着的时候最深扛过 ${pct(s.deep)}`);
  if (s.chase) out.push(`有 ${s.chase} 次是在一周涨了 8% 以上之后追进去`);
  if (s.dip) out.push(`有 ${s.dip} 次是在一周跌了 6% 以上之后买进`);
  if (s.cuts.length) out.push(`亏损离场 ${s.cuts.length} 次（${s.cuts.map((c) => pct(c)).join("、")}）`);
  out.push(`这一场 ${pct(s.ret, 1)}`);
  void dates;
  return out.join("；");
}

export const ORDER: SpeciesId[] = ["cheetah", "elephant", "owl", "meerkat", "fox", "chameleon"];

export function scores(runs: Run[]): Record<SpeciesId, number> {
  const sc = Object.fromEntries(ORDER.map((k) => [k, 0])) as Record<SpeciesId, number>;
  let positive = 0;
  const stamps = new Set<string>();
  const cutDepth: number[] = [];
  runs.forEach((r) => {
    const l = levelById(r.id);
    const s = stats(l, r);
    stamps.add(stampOf(l, r).t);
    if (s.ret > 0.02) positive += 1;
    sc.cheetah += s.chase * 2 + s.quick + (s.acts >= 4 ? 1 : 0);
    sc.elephant += s.dip * 2 + (s.acts <= 1 && s.deep <= -0.12 ? 2 : 0) + (s.acts <= 1 ? 1 : 0);
    sc.owl += r.held < 0.35 ? 1.5 : 0;
    cutDepth.push(...s.cuts);
    if (l.id === "s924") {
      if (r.openAct === "buy") sc.meerkat += 2.5;
      if (!r.trades.some((t) => t.k === "buy")) sc.owl += 2;
      if (r.openAct === "sell") sc.fox += 1;
    }
    if (l.id === "s2015") {
      if (r.lev >= 4) sc.cheetah += 3;
      else if (r.lev >= 2) sc.cheetah += 1.5;
      else sc.owl += 1, sc.fox += 0.5;
      if (r.liq) sc.meerkat += 1;
    }
    if (l.id === "smt") {
      const n = r.leftRank;
      if (n === -1 || n === 0) sc.fox += 1.5, sc.owl += 1;
      else if (n != null && n <= 5) sc.meerkat += 2.5;
      else sc.elephant += 2;
    }
    if (l.id === "scb") {
      sc.meerkat += (r.haltSold || 0) * 2;
      if (r.panicBuy) sc.elephant += 2;
      if (s.acts === 0) sc.elephant += 1.5;
    }
  });
  if (cutDepth.length >= 2) {
    const spread = Math.max(...cutDepth) - Math.min(...cutDepth);
    if (spread <= 0.04) sc.fox += 3;
  }
  if (positive >= 3 && stamps.size >= 3) sc.chameleon += 4;
  return sc;
}

export function topSpecies(sc: Record<SpeciesId, number>): SpeciesId {
  return [...ORDER].sort((a, b) => sc[b] - sc[a])[0];
}

const QUBE: Record<SpeciesId, string> = {
  cheetah: "帮我回测：上证指数一周涨超 8% 时买入、跌破 10 日均线就卖，2015—2024 年和一直拿着比收益和最大回撤",
  elephant: "帮我回测：沪深300 从高点回撤 20% 后分三次买入、拿一年，2015—2024 年的收益和最大回撤",
  owl: "帮我回测：上证指数站上 60 日均线才买、跌破就空仓，2015—2024 年和一直拿着比收益和最大回撤",
  meerkat: "帮我回测：成交额创 20 日新高的第二天买入沪深300、拿 5 天，2015—2024 年胜率和平均收益",
  fox: "帮我回测：买入后跌 7% 止损、涨 15% 止盈，用在沪深300 上，2015—2024 年的收益和最大回撤",
  chameleon: "帮我回测：沪深300 在 60 日均线上方时追趋势、下方时只在回撤 15% 后买，2015—2024 年和一直拿着比",
  beaver: "帮我用 panda_data 拉取沪深300 日线，算 20 日动量，回测 2015—2024 年",
};

export function localVerdict(runs: Run[], guess: string | null): Verdict {
  const sc = scores(runs);
  const top = topSpecies(sc);
  const m = sp(top);
  const all = runs.map((r) => ({ r, l: levelById(r.id), s: stats(levelById(r.id), r), st: stampOf(levelById(r.id), r) }));
  const deep = Math.min(0, ...all.map((x) => x.s.deep));
  const moments = all
    .map((x) => ({ k: Math.abs(x.s.ret) + (x.st.good === null ? 0 : 0.1), t: `${x.l.seasonCn}·${x.st.t}：${x.st.sub}` }))
    .sort((a, b) => b.k - a.k)
    .slice(0, 3)
    .map((x) => x.t);
  const gap = deep <= -0.08
    ? `模拟盘里你最深扛过 ${pct(deep)}。真钱亏损的痛大约是同样赚钱的两倍，实盘里多数人在 ${pct(deep / 2)} 左右就想松手了。`
    : "模拟盘里你跑得很快。实盘里还有手续费和犹豫，进出越多，磨损越大。";
  const g = guess && guess !== top ? sp(guess)?.cn : null;
  return {
    species: top,
    title: m.tagline,
    read: `${m.behavior}。${m.watch.split("。")[0]}。`,
    moments,
    gap,
    qube: QUBE[top],
    self: guess ? (g ? `你以为自己是${g}，操作更像${m.cn}。` : `你猜对了：你就是${m.cn}。`) : "",
    model: "local",
  };
}
