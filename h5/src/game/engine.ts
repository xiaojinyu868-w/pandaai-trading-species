import { SCENES, sceneById, type EvKind, type OptKey, type Scene, type SceneId } from "../data";
import { CHANCE, RETEST, RULES, ruleView, taskOf, type TaskCard } from "./cards";
import { aiPick, aiStars, BADGES, REASONS, sp, WAIT_OPTIONS, type Reason, type SpeciesId, type TaskType } from "./meta";
import type { AiResult, Game, SeasonRec } from "./store";
import { levelById } from "../arcade/levels";
import { describe, scores, topSpecies } from "../arcade/profile";

/** 1 资金 ≈ 一份仓位涨跌 5%，四舍五入；不到 2.5% 记 0 */
export const ps = (p: number) => (Math.abs(p) >= 2.5 ? Math.round(p / 5) : 0);
export const pct = (a: number, b: number) => (b / a - 1) * 100;
export const signed = (n: number, d = 1) => (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(d);
export const money = (n: number) => (n > 0 ? "+" : n < 0 ? "−" : "±") + Math.abs(n);

export const optOf = (s: Scene, k?: OptKey) => s.options.find((o) => o.key === k);
export const sharesOf = (s: Scene, k?: OptKey) => optOf(s, k)?.shares ?? 0;

/** 2015 快进里这一天卖不卖得掉：有逐只统计时看 grid.lock（三分之二以上跌停或停牌），否则看指数单日跌超 5% */
export function lockedDay(scene: Scene, k: number): boolean {
  const days = scene.path!.days;
  const g = scene.fast_forward.grid?.find((x) => x.date === days[k].date);
  return g?.lock ?? pct(days[k - 1].close, days[k].close) <= -5;
}

export const EVENT_NAMES: { id: string; name: string }[] = [
  { id: "s924", name: "2024 年 924 行情 / 国庆开户潮" },
  { id: "s2015", name: "2015 年杠杆牛和股灾" },
  { id: "smt", name: "2021 年茅台 / 抱团股瓦解" },
  { id: "scb", name: "2020 年美股熔断" },
  { id: "squant", name: "2024 年初量化踩踏 / 微盘股闪崩" },
  { id: "soil", name: "2020 年原油宝穿仓" },
  { id: "x2008", name: "2008 年全球金融危机" },
  { id: "x1987", name: "1987 年黑色星期一" },
  { id: "x2000", name: "2000 年互联网泡沫破裂" },
];

/* ---------------- 每场的 AI 结果 ---------------- */
export function aiResult(scene: Scene, aiId: string, extra = 0): AiResult {
  const p = aiPick(aiId, scene.id);
  const row = scene.reveal.payoff_rows.find((r) => r.key === p.option)!;
  let seg1 = row.seg1;
  let seg2 = row.seg2;
  const s = row.shares;
  const card = scene.fast_forward.cards[0];
  if (scene.id === "s924") {
    if (p.plan === "cut" && card.dip && s > 0) {
      seg1 = s * card.dip.per_share_at_trigger;
      seg2 = 0;
    }
    if (p.ff === "enter") seg2 = 1 * scene.reveal.seg2.per_share;
  }
  if (scene.id === "s2015" && p.ff === "sell" && s > 0 && scene.path) {
    const path = scene.path;
    const e0 = path.ends[0];
    let j = e0 + 1;
    while (j < path.ends[1] && lockedDay(scene, j)) j++;
    seg2 = s * ps(pct(path.days[e0].close, path.days[j].close));
  }
  if (scene.id === "smt" && p.ff === "sell" && s > 0) seg2 = 0;
  if (scene.id === "scb") {
    const cards = scene.fast_forward.cards;
    let n = s;
    seg1 = 0;
    cards.forEach((c, i) => {
      seg1 += n * c.per_share;
      if (i === 0 && p.ff === "sell") n = Math.max(0, n - 1);
      if (i === 0 && p.ff === "add") n = n + 1;
    });
    if (p.second === "add") n += 1;
    if (p.second === "stop") n = 0;
    seg2 = n * scene.reveal.seg2.per_share;
  }
  const total = seg1 + seg2 + extra;
  return { option: p.option, seg1, seg2, extra, total, line: p.line, ff: p.ff, stars: aiStars(aiId, scene.id) };
}

/* ---------------- 方法星、物种图标 ---------------- */
export function reasonConsistent(r: SeasonRec): boolean {
  if (!r.reason) return false;
  if (r.reason === "rule") return r.ff?.ruleFollowed !== false;
  if (r.reason === "follow") return (r.queueSeen ?? 0) > 0 || r.evidence.includes("news") || r.evidence.includes("tip");
  const ev = REASONS.find((x) => x.id === r.reason)?.ev as EvKind | undefined;
  return !!ev && r.evidence.includes(ev);
}

export function starsOf(r: SeasonRec) {
  const kinds = new Set(r.evidence);
  const ev = kinds.size >= 2 ? 2 : kinds.size >= 1 ? 1 : 0;
  const consistent = reasonConsistent(r);
  const rule = r.reason === "rule" && r.ff?.ruleFollowed !== false;
  const plan = rule || (!!r.plan && r.plan !== "none" && r.ff?.planFollowed !== false);
  return { ev, consistent, plan, total: ev + (consistent ? 1 : 0) + (plan ? 1 : 0) };
}

export function isWait(r: SeasonRec) {
  return !!r.scene && !!r.option && (WAIT_OPTIONS[r.scene] || []).includes(r.option);
}

export function iconsOf(r: SeasonRec) {
  const icons: Partial<Record<SpeciesId, number>> = {};
  const why: { species: SpeciesId; n: number; text: string }[] = [];
  const add = (s: SpeciesId | null | undefined, n: number, text: string) => {
    if (!s) return;
    icons[s] = (icons[s] || 0) + n;
    why.push({ species: s, n, text });
  };
  if (r.run) {
    const lv = levelById(r.run.id);
    const top = topSpecies(scores([r.run]));
    if (lv) add(top, 2, `你在行情里的出手：${describe(lv, r.run).split("；")[0]}`);
  }
  const reason = REASONS.find((x) => x.id === r.reason);
  if (reason && isWait(r) && r.reason !== "gut" && r.reason !== "lost") {
    add("owl", 2, `你选了观望，理由是“${reason.cn}”：说得出在等什么`);
  } else if (reason) {
    add(reason.species, 2, `你的理由是“${reason.cn}”`);
  }
  const first = r.evidence[0];
  const firstMap: Record<string, SpeciesId | null> = { price: "cheetah", data: "elephant", news: "meerkat", tip: null };
  if (first && firstMap[first]) add(firstMap[first], 1, `你最先看的是${{ price: "量价", data: "数据", news: "消息", tip: "锦囊" }[first]}`);
  if (r.chance) add(r.chance.species, 1, `你在机会牌上选了“${CHANCE.find((c) => c.id === r.chance!.id)?.a[r.chance.answer]?.text || ""}”`);
  return { icons, why };
}

export function topOf(icons: Partial<Record<SpeciesId, number>>) {
  const entries = Object.entries(icons) as [SpeciesId, number][];
  if (!entries.length) return { top: [] as SpeciesId[], max: 0 };
  const max = Math.max(...entries.map((e) => e[1]));
  return { top: entries.filter((e) => e[1] === max).map((e) => e[0]), max };
}

/* ---------------- 终局画像 ---------------- */
export type Confidence = "很确定" | "比较确定" | "初步" | "待确认";
export interface Claim {
  dim: string;
  kind: "能力" | "偏好" | "习惯" | "能力 / 习惯";
  level: string;
  confidence: number;
  evidence: string[];
  source: "game" | "self" | "real";
  status: "成立" | "待确认";
  next_probe?: string;
}
export interface Profile {
  species: SpeciesId | null;
  tied: SpeciesId[];
  confidence: Confidence;
  coins: Partial<Record<SpeciesId, number>>;
  hidden: SpeciesId | null;
  badges: string[];
  claims: Claim[];
  pending: string[];
  rec: { main: TaskCard; extra: TaskCard | null; because: string[]; notNow: { name: string; reason: string }[]; level: "basic" | "adv" };
  twoYou: { self: SpeciesId | undefined; game: SpeciesId | null; same: boolean; realLines: string[] };
  score: { me: number; stars: number; rankPts: number; money: number; ais: { id: string; money: number; stars: number; score: number }[]; win: boolean; rank: number };
}

const SC = (id?: string) => sceneById(id || "")?.title.split("·")[0].trim() || "";
const sceneShort = (r: SeasonRec) => {
  const s = sceneById(r.scene || "");
  return s ? `${s.season_cn} · ${s.title.split(" · ")[0]}` : "";
};

export function profileOf(g: Game): Profile {
  const done = g.seasons.filter((r) => r.scene && r.option);
  const nCn = ["零", "一", "两", "三", "四", "五", "六"][done.length] || String(done.length);
  const terms = g.terms || [];
  const coins: Partial<Record<SpeciesId, number>> = {};
  done.forEach((r) => {
    if (r.coin) coins[r.coin] = (coins[r.coin] || 0) + (r.coinHalf ? 0.5 : 1);
  });
  const entries = (Object.entries(coins) as [SpeciesId, number][]).sort((a, b) => b[1] - a[1]);
  const max = entries[0]?.[1] || 0;
  let tied = entries.filter((e) => e[1] === max).map((e) => e[0]);
  let species: SpeciesId | null = tied.length === 1 ? tied[0] : null;
  let confidence: Confidence = "待确认";
  const consistentN = done.filter(reasonConsistent).length;
  if (species) confidence = max >= 3.5 ? "很确定" : max >= 2.5 ? "比较确定" : "初步";
  else if (done.length >= 4 && entries.length >= 4 && max <= 1) {
    if (consistentN >= 3) {
      species = "chameleon";
      confidence = consistentN >= 4 ? "比较确定" : "初步";
      tied = [];
    }
  }
  const hidden: SpeciesId | null = g.dataportRight >= 2 ? "beaver" : null;

  /* 徽章 */
  const badges: string[] = [];
  const multiEv = done.filter((r) => new Set(r.evidence).size >= 2).length;
  if (multiEv >= 2 && consistentN >= 3) badges.push("evidence");
  const kept = done.filter((r) => r.plan && r.plan !== "none" && r.ff?.planFollowed !== false).length;
  if (kept >= 2) badges.push("keepword");
  const hist = done.filter((r) => r.recognized?.correct).length;
  if (hist >= 2) badges.push("history");
  if (g.dataportRight >= 2) badges.push("datahand");
  const ruleUsed = done.filter((r) => r.reason === "rule" && r.ff?.ruleFollowed !== false).length;
  if (ruleUsed >= 1) badges.push("rulefan");
  let riskSeen = 0;
  done.forEach((r) => {
    const s = sceneById(r.scene!)!;
    r.evidence.forEach((k) => s.evidence[k]?.risk && riskSeen++);
  });
  if (riskSeen >= 2) badges.push("riskaware");

  /* 维度判断 */
  const claims: Claim[] = [];
  const pending: string[] = [];
  const evCounts = done.map((r) => new Set(r.evidence).size);
  const avgEv = evCounts.reduce((a, b) => a + b, 0) / Math.max(1, done.length);
  const evLines = done.map((r) => {
    const ks = r.evidence.map((k) => ({ price: "量价", data: "数据", news: "消息", tip: "锦囊" }[k]));
    return `${sceneShort(r)}：${ks.length ? "看了" + ks.join("、") : "没看证据"}，理由“${REASONS.find((x) => x.id === r.reason)?.cn || "—"}”${reasonConsistent(r) ? "，和证据一致" : ""}`;
  });
  claims.push({
    dim: "证据使用", kind: "能力 / 习惯",
    level: avgEv >= 2 && consistentN >= 3 ? "高" : avgEv >= 1 && consistentN >= 2 ? "中" : "低",
    confidence: done.length >= 4 ? 0.7 : 0.5, evidence: evLines, source: "game", status: "成立",
  });
  const recog = done.filter((r) => r.recognized);
  claims.push({
    dim: "金融知识与历史", kind: "能力",
    level: hist >= 2 ? "高" : hist === 1 ? "中" : recog.length ? "中" : "还看不出",
    confidence: recog.length ? 0.6 : 0.3,
    evidence: [
      ...(recog.length ? recog.map((r) => `${sceneShort(r)}：说认出来了，写的是“${r.recognized!.name}”${r.recognized!.correct ? "（对）" : "（不对）"}`) : [`${nCn}场都没有说“认出来了”：这不代表不懂历史，只是没有证据`]),
      ...(terms.length ? [`点开查了 ${terms.length} 个词：${terms.slice(0, 6).join("、")}${terms.length > 6 ? "等" : ""}（查词说明在补概念，不扣分）`] : []),
    ],
    source: "game", status: recog.length ? "成立" : "待确认",
  });
  const dpSeen = g.dataportSeen;
  const revealedIds = done.map((r) => r.scene!);
  const ruleKept = g.seasons.filter((r) => r.ruleKept).map((r) => { const c = RULES.find((x) => x.id === r.ruleKept); return c ? ruleView(c, revealedIds).name : r.ruleKept; });
  const quantDoor = done.some((r) => r.scene === "squant");
  const qLines: string[] = [];
  if (dpSeen) qLines.push(`数据港口读了 ${dpSeen} 段代码，答对 ${g.dataportRight} 次`);
  if (ruleKept.length) qLines.push(`研究所留下了规则：${ruleKept.join("、")}`);
  if (ruleUsed) qLines.push(`有 ${ruleUsed} 场用规则牌做决定并照做`);
  if (quantDoor) qLines.push("秋天选了量化那扇门");
  const quantLevel = g.dataportRight >= 2 ? "高" : g.dataportRight === 1 || ruleUsed || quantDoor ? "中" : dpSeen || ruleKept.length ? "低" : "未测";
  claims.push({
    dim: "量化与工具准备度", kind: "能力", level: quantLevel,
    confidence: dpSeen ? 0.6 : 0.3, evidence: qLines.length ? qLines : ["没有落到数据港口和研究所，证据不足"],
    source: "game", status: quantLevel === "未测" ? "待确认" : "成立", next_probe: quantLevel === "未测" ? "第二圈的数据港口" : undefined,
  });
  const rCount: Record<string, number> = {};
  done.forEach((r) => r.reason && (rCount[r.reason] = (rCount[r.reason] || 0) + 1));
  const topReason = Object.entries(rCount).sort((a, b) => b[1] - a[1])[0];
  claims.push({
    dim: "决策依据", kind: "偏好",
    level: topReason ? `主要看${REASONS.find((x) => x.id === topReason[0])?.cn}（${topReason[1]}/${done.length} 场）` : "—",
    confidence: topReason && topReason[1] >= 3 ? 0.7 : 0.5,
    evidence: done.map((r) => `${sceneShort(r)}：理由“${REASONS.find((x) => x.id === r.reason)?.cn || "—"}”，最先看${r.evidence[0] ? { price: "量价", data: "数据", news: "消息", tip: "锦囊" }[r.evidence[0]] : "无"}`),
    source: "game", status: "成立",
  });
  const markets = done.map((r) => sceneById(r.scene!)!.market);
  claims.push({
    dim: "兴趣市场与主题", kind: "偏好", level: Array.from(new Set(markets)).join("、"),
    confidence: 0.5,
    evidence: done.filter((r) => r.door).map((r) => `${sceneById(r.scene!)!.season_cn}天选了 ${r.door} 门：${sceneById(r.scene!)!.market}`),
    source: "game", status: "成立",
  });
  const aCount = done.filter((r) => r.option === "A").length;
  const avgShares = done.reduce((a, r) => a + sharesOf(sceneById(r.scene!)!, r.option), 0) / Math.max(1, done.length);
  const riskLevel = aCount >= 2 || avgShares >= 2.25 ? "偏激进" : avgShares <= 0.75 ? "偏保守" : "中性";
  const riskLines = done.map((r) => `${sceneShort(r)}：选 ${r.option}（${sharesOf(sceneById(r.scene!)!, r.option)} 份）`);
  if (g.real?.drop) riskLines.push(`现实题：上次大跌时${g.real.drop}`);
  claims.push({
    dim: "风险姿态", kind: "偏好", level: riskLevel, confidence: 0.3, evidence: riskLines,
    source: "game", status: "待确认", next_probe: "期货模拟赛",
  });
  pending.push("风险姿态：游戏里没有真钱，只做参考，交给模拟盘校准");
  const crisis = done.find((r) => r.scene === "scb");
  const advLines: string[] = [];
  if (crisis?.ff) {
    advLines.push(`熔断：调了 ${crisis.ff.changes} 次仓位，第二次决定“${{ add: "补仓", stop: "止损", ignore: "不看了" }[crisis.ff.second || "ignore"]}”`);
  }
  done.forEach((r) => {
    if (r.ff?.planTriggered) advLines.push(`${sceneShort(r)}：计划被触发，${r.ff.planFollowed ? "照做了" : "没照做"}`);
  });
  const calm = g.seasons.filter((r) => r.calm);
  calm.forEach((r) => advLines.push(`冷静亭：${r.calm === "sat" ? "坐下了" : "没坐，马上再掷一次"}`));
  claims.push({
    dim: "逆境反应", kind: "习惯", level: advLines.length ? (done.some((r) => r.ff?.planTriggered && r.ff.planFollowed === false) ? "压力下会改主意" : "压力下按原计划") : "证据不足",
    confidence: 0.3, evidence: advLines.length ? advLines : ["没有经历计划触发或熔断，证据不足，不下结论"],
    source: "game", status: "待确认", next_probe: "模拟盘",
  });
  pending.push("逆境反应：没有真金白银的亏损，结论只作参考");
  if (done.length < 4) pending.unshift(`样本：只看了 ${done.length} 场，以上都是初步判断；多玩几场，把握会跟着变`);
  if (!species) pending.unshift(`物种：${tied.map((t) => sp(t).cn).join("、")}并列，${tied.length > 2 ? `${tied.length} 张` : "两张"}物种牌并排放；再玩一局，看哪一种先跑出来`);

  /* 推荐：决策树 */
  const lostN = rCount["lost"] || 0;
  const newsN = (rCount["news"] || 0) + (rCount["follow"] || 0);
  const waitN = done.filter((r) => isWait(r) && r.reason !== "gut" && r.reason !== "lost").length;
  let type: TaskType = "hypo";
  const because: string[] = [];
  const notNow: { name: string; reason: string }[] = [];
  if (lostN >= 2 || (lostN >= 1 && terms.length >= 3)) {
    type = "chart";
    because.push(lostN >= 2 ? `有 ${lostN} 场你的理由是“看不懂”：先把图读懂，比急着下结论更重要` : `有 ${lostN} 场你的理由是“看不懂”，还点开查了 ${terms.length} 个词：先把概念和图读懂，比急着下结论更重要`);
  } else if (badges.includes("datahand")) {
    type = "explore";
    because.push(`数据港口你答对了 ${g.dataportRight} 次：你能读懂 panda_data 的代码，可以自己动手`);
  } else if (species === "owl" || waitN >= 2) {
    type = "regime";
    because.push(waitN >= 2 ? `有 ${waitN} 场你选择观望，而且说得出理由：把“在等什么”变成能监测的信号` : "你的物种是猫头鹰：等待是你的方法，值得把它做得更准");
  } else if (newsN >= 2) {
    type = "verify";
    because.push(`有 ${newsN} 场你的理由是“消息”或“跟别人”：先学会核查，再决定信不信`);
  } else {
    type = "hypo";
    const rs = done.filter((r) => r.reason === "price" || r.reason === "rule" || r.reason === "data").map(sceneShort);
    because.push(rs.length ? `你在${rs.join("、")}${rs.length > 1 ? " 都" : " "}是按看得见的信号做的决定，但这些信号还没用历史数据检验过` : "你已经有自己的交易直觉，下一步是用数据检验它");
  }
  const lvl: "basic" | "adv" = badges.some((b) => ["history", "rulefan", "evidence"].includes(b)) ? "adv" : "basic";
  if (lvl === "adv") because.push(`你拿到了${badges.filter((b) => ["history", "rulefan", "evidence"].includes(b)).map((b) => "“" + BADGES.find((x) => x.id === b)!.cn + "”").join("")}徽章，给你进阶版`);
  const conservativeSelf = g.self === "owl" || g.self === "elephant" || g.real?.drop === "卖了";
  const extra = aCount >= 2 && conservativeSelf ? taskOf("risk", "basic") : null;
  if (extra) because.push(`有 ${aCount} 场你选了最激进的 A，${g.real?.drop === "卖了" ? "但现实里上次大跌你卖了" : `但你觉得自己是${sp(g.self!).cn}`}：没有真钱时的你，和有真钱时的你可能不一样`);
  if (type !== "explore") notNow.push({ name: "panda_data 数据接口", reason: dpSeen ? `数据港口答对 ${g.dataportRight} 次，先从模板开始更顺` : "你还没有打开过数据港口" });
  if (type === "explore") notNow.push({ name: "Qube 新手模板", reason: "你已经能读代码、自己改参数" });
  if (type !== "chart" && lostN === 0) notNow.push({ name: "读图入门课", reason: `${nCn}场里你没有一次因为“看不懂”而做决定` });
  if (type === "chart") notNow.push({ name: "因子评估工具", reason: "先把图读懂，再碰因子" });

  /* 两个你 */
  const realLines: string[] = [];
  if (g.real?.drop) realLines.push(`现实里上次大跌，你${g.real.drop}`);
  if (g.real?.buy) realLines.push(`现实里上次买入，主要因为${g.real.buy}`);

  /* 胜负 */
  const ais = g.opponents.map((id) => {
    const stars = done.reduce((a, r) => a + (r.ai?.[id]?.stars ?? aiStars(id, r.scene)), 0);
    return { id, money: g.aiMoney[id] ?? 20, stars, score: 0 };
  });
  const myStars = done.reduce((a, r) => a + (r.stars?.total || 0), 0);
  const all = [{ id: "me", money: g.money }, ...ais.map((a) => ({ id: a.id, money: a.money }))].sort((a, b) => b.money - a.money);
  const rankPts = (id: string) => {
    const m = all.find((x) => x.id === id)!.money;
    if (m < 0) return 0;
    const better = all.filter((x) => x.money > m).length;
    return [6, 4, 2][better] ?? 1;
  };
  ais.forEach((a) => (a.score = a.stars + rankPts(a.id)));
  const me = myStars + rankPts("me");
  const ahead = (a: { score: number; stars: number }) => a.score > me || (a.score === me && a.stars > myStars);
  const rank = 1 + ais.filter(ahead).length;
  return {
    species, tied: species ? [] : tied, confidence, coins, hidden, badges, claims, pending,
    rec: { main: taskOf(type, lvl), extra, because, notNow, level: lvl },
    twoYou: { self: g.self, game: species, same: !!species && species === g.self, realLines },
    score: { me, stars: myStars, rankPts: rankPts("me"), money: g.money, ais, win: ais.length > 0 && ais.every((a) => me > a.score || (me === a.score && myStars > a.stars)), rank },
  };
}

export function profileJson(g: Game, p: Profile) {
  return {
    schema: "trading-species/profile@1",
    generated_at: new Date().toISOString(),
    source: g.source,
    note: "投资者教育游戏，不构成投资建议。风险类判断没有真钱，只做参考。",
    species: { value: p.species ? sp(p.species).cn : null, kind: "偏好", confidence: p.confidence, coins: Object.fromEntries(Object.entries(p.coins).map(([k, v]) => [sp(k).cn, v])), tied: p.tied.map((t) => sp(t).cn), self_report: g.self ? sp(g.self).cn : null, hidden_trait: p.hidden ? sp(p.hidden).cn : null },
    badges: p.badges.map((b) => BADGES.find((x) => x.id === b)!.cn),
    claims: p.claims,
    pending: p.pending,
    recommendation: {
      task: p.rec.main.cn,
      resources: p.rec.main.resources.map((r) => ({ name: r.name, url: r.url, is_real_resource: !r.example, note: r.note })),
      because: p.rec.because,
      not_now: p.rec.notNow,
      extra: p.rec.extra ? p.rec.extra.cn : null,
    },
    next_step: { type: "in_game_task", id: p.rec.main.id, handoff: p.rec.main.resources[0]?.url },
    calibration_ladder: ["开局自评", "游戏行为", "现实锚点题", "平台研究行为（Qube 回测、因子评估）", "模拟盘"],
    knowledge_lookups: g.terms || [],
    scenes_played: g.seasons.filter((r) => r.scene && r.option).length,
    mode: g.mode || "full",
  };
}

export const allScenes = SCENES;
export const sceneTitle = SC;
export { RETEST };
