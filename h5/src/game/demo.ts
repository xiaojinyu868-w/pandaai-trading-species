import { sceneById, type EvKind, type OptKey, type SceneId } from "../data";
import { aiResult, EVENT_NAMES, iconsOf, starsOf, topOf } from "./engine";
import { REASONS, type Plan, type Reason, type SpeciesId } from "./meta";
import { newSeason, type Game, type SeasonRec } from "./store";

/** 评委演示台：模拟玩家的行为路径。每一步只写玩家做了什么，结果全部交给游戏里同一个画像引擎算。 */
export interface DemoStep {
  scene: SceneId;
  ev: EvKind[];
  option: OptKey;
  reason: Reason;
  plan: Plan;
  ruleId?: string;
  recognized?: boolean;
  /** 打平或没有图标时，补测牌的答案 */
  retest?: SpeciesId;
}

export interface DemoPath {
  id: string;
  name: string;
  who: string;
  self: SpeciesId;
  steps: DemoStep[];
  rules?: string[];
  dataportRight?: number;
  dataportSeen?: number;
  terms?: string[];
}

export const PATHS: DemoPath[] = [
  {
    id: "chase", name: "一路追涨", who: "自评是大象，实际每场都先看走势、敢上满仓", self: "elephant",
    steps: [
      { scene: "s924", ev: ["price"], option: "A", reason: "price", plan: "none" },
      { scene: "s2015", ev: ["price"], option: "A", reason: "price", plan: "none" },
      { scene: "smt", ev: ["price", "news"], option: "B", reason: "price", plan: "none" },
      { scene: "scb", ev: ["price"], option: "A", reason: "price", plan: "none" },
    ],
  },
  {
    id: "careful", name: "等证据", who: "证据看得最全，常选观望，每场都定好计划", self: "owl",
    steps: [
      { scene: "s924", ev: ["data", "price"], option: "C", reason: "data", plan: "cut" },
      { scene: "s2015", ev: ["data", "news"], option: "C", reason: "data", plan: "cut" },
      { scene: "smt", ev: ["data", "price"], option: "D", reason: "data", plan: "cut" },
      { scene: "soil", ev: ["news", "data"], option: "D", reason: "data", plan: "none" },
    ],
  },
  {
    id: "news", name: "跟着消息走", who: "自评是猎豹，实际总是先看消息、跟着人群排队", self: "cheetah",
    steps: [
      { scene: "s924", ev: ["news"], option: "A", reason: "follow", plan: "none" },
      { scene: "s2015", ev: ["news"], option: "B", reason: "news", plan: "none" },
      { scene: "smt", ev: ["news", "price"], option: "A", reason: "follow", plan: "none" },
      { scene: "scb", ev: ["news"], option: "C", reason: "news", plan: "none" },
    ],
    terms: ["融资余额", "市盈率"],
  },
  {
    id: "lost", name: "新手看不懂", who: "证据看得少，三场的理由都是“看不懂”，还查了好几个词", self: "meerkat",
    steps: [
      { scene: "s924", ev: ["price"], option: "B", reason: "lost", plan: "none" },
      { scene: "s2015", ev: ["news"], option: "B", reason: "follow", plan: "none" },
      { scene: "smt", ev: ["tip"], option: "B", reason: "lost", plan: "none", retest: "owl" },
      { scene: "scb", ev: ["price"], option: "D", reason: "lost", plan: "none" },
    ],
    terms: ["成交量", "放量", "杠杆", "融资余额", "市盈率"],
  },
  {
    id: "rules", name: "规则派", who: "研究所留了规则牌并照做，数据港口两次都读懂了代码", self: "fox",
    rules: ["rule-ma520", "rule-stop10"], dataportRight: 2, dataportSeen: 2,
    steps: [
      { scene: "s924", ev: ["price", "data"], option: "B", reason: "rule", ruleId: "rule-stop10", plan: "none" },
      { scene: "s2015", ev: ["data", "price"], option: "C", reason: "rule", ruleId: "rule-stop10", plan: "none" },
      { scene: "smt", ev: ["price", "data"], option: "C", reason: "rule", ruleId: "rule-ma520", plan: "none" },
      { scene: "scb", ev: ["data", "price"], option: "C", reason: "data", plan: "cut" },
    ],
  },
];

const OPP = ["cheetah", "meerkat"];

export function buildRec(p: DemoPath, st: DemoStep): SeasonRec {
  const s = sceneById(st.scene)!;
  const r: SeasonRec = {
    ...newSeason(s.season),
    scene: s.id,
    door: s.door,
    evidence: [...st.ev],
    option: st.option,
    reason: st.reason,
    plan: st.plan,
    ruleId: st.reason === "rule" ? st.ruleId || p.rules?.[0] : undefined,
    recognized: st.recognized ? { name: EVENT_NAMES.find((e) => e.id === s.id)?.name || s.title, correct: true } : null,
    queueSeen: s.decision_mode === "sequential" ? 10 : undefined,
    ff: { actions: [], changes: 0, planTriggered: st.plan !== "none", planFollowed: st.plan !== "none" ? true : null, ruleFollowed: st.reason === "rule" ? true : null },
  };
  const row = s.reveal.payoff_rows.find((x) => x.key === st.option)!;
  r.ai = Object.fromEntries(OPP.map((id) => [id, aiResult(s, id)]));
  const aiAvg = Math.round(OPP.reduce((a, id) => a + r.ai![id].total, 0) / OPP.length);
  r.money = { seg1: row.seg1, seg2: row.seg2, extra: 0, total: row.total, counted: st.recognized ? aiAvg : row.total };
  r.stars = starsOf(r);
  const { icons } = iconsOf(r);
  r.icons = icons;
  const { top } = topOf(icons);
  const rs = REASONS.find((x) => x.id === st.reason)?.species || undefined;
  r.coin = top.length === 1 ? top[0] : st.retest || (rs && top.includes(rs) ? rs : top[0]) || p.self;
  r.coinHalf = !!st.recognized;
  return r;
}

export function buildGame(p: DemoPath): Game {
  const seasons = p.steps.map((st) => buildRec(p, st));
  (p.rules || []).forEach((id, i) => seasons[i] && (seasons[i].ruleKept = id));
  if (p.dataportSeen) seasons[0].dataport = { id: "dp-01", answer: 0, correct: (p.dataportRight || 0) > 0 };
  const money = 20 + seasons.reduce((a, r) => a + (r.money?.counted || 0), 0);
  const aiMoney = Object.fromEntries(OPP.map((id) => [id, 20 + seasons.reduce((a, r) => a + (r.ai?.[id]?.total || 0), 0)]));
  return {
    id: `demo${p.id}`,
    phase: "ending",
    step: "reveal",
    seasonIdx: seasons.length - 1,
    pos: 0,
    money,
    rp: 0,
    self: p.self,
    opponents: OPP,
    aiMoney,
    rules: p.rules || [],
    dataportRight: p.dataportRight || 0,
    dataportSeen: p.dataportSeen || 0,
    seasons,
    terms: p.terms || [],
    mode: "full",
    startedAt: Date.now(),
    finishedAt: Date.now(),
    source: "h5",
  };
}
