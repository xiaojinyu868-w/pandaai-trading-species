import { sceneById } from "../data";
import { RULES, ruleView } from "./cards";
import { isWait } from "./engine";
import { REASONS } from "./meta";
import type { Game, SeasonRec } from "./store";

export const QUBE_URL = "https://www.pandaaiquant.com/agent_quant/";

export interface Handoff {
  /** 粘贴进 Qube 的一句话 */
  prompt: string;
  /** 这句话从哪个行为来 */
  from: string;
}

const ruleById = (id?: string) => RULES.find((r) => r.id === id);
const short = (r: SeasonRec) => {
  const s = sceneById(r.scene || "");
  return s ? `${s.season_cn}天的「${s.title.split(" · ")[0]}」` : "";
};

/** 按“看量价”时所在的名场面，给一条同一段历史的回测 */
const PRICE_BY_SCENE: Record<string, string> = {
  s924: "rule-ma52060",
  s2015: "rule-mom20",
  smt: "rule-ma520",
  squant: "rule-vol2x",
};
const PRICE_RAW: Record<string, string> = {
  scb: "帮我回测一条规则：纳斯达克 100 跌破 20 日均线就卖、重新站上再买，看 2020 年 2—4 月和一直拿着相比，最大回撤差多少",
  soil: "帮我回测一条规则：上海原油期货主力合约跌破 20 日均线就平仓、重新站上再买，看 2020 年 3—6 月和一直拿着相比，最大回撤差多少",
};
const REGIME = "帮我做一个每天检查的信号：融资余额回升、成交额放大、5 日均线在 20 日均线上方，三个都满足才买入上证指数，回测 2015—2024 年，和一直持有比收益和最大回撤";

export function handoffOf(g: Game): Handoff {
  const done = g.seasons.filter((r) => r.scene && r.option);
  const revealed = done.map((r) => r.scene!);
  const view = (id: string) => {
    const r = ruleById(id);
    return r ? ruleView(r, revealed) : null;
  };

  const usedAll = done.filter((r) => r.reason === "rule" && r.ruleId && view(r.ruleId)?.qube);
  const used = usedAll.find((r) => ruleById(r.ruleId)?.real) || usedAll[0];
  if (used) {
    const v = view(used.ruleId!)!;
    return { prompt: v.qube!, from: `你在${short(used)}按规则牌「${v.name}」做了决定` };
  }
  const keptRec = g.seasons.find((r) => r.ruleKept && view(r.ruleKept)?.qube);
  if (keptRec) {
    const v = view(keptRec.ruleKept!)!;
    return { prompt: v.qube!, from: `你在研究所留下了规则牌「${v.name}」` };
  }

  const count: Record<string, number> = {};
  done.forEach((r) => r.reason && (count[r.reason] = (count[r.reason] || 0) + 1));
  const waitN = done.filter((r) => isWait(r) && r.reason !== "gut" && r.reason !== "lost").length;
  const top = Object.entries(count).sort((a, b) => b[1] - a[1])[0]?.[0];
  const cn = (k: string) => REASONS.find((x) => x.id === k)?.cn || k;
  const tally = (k: string) => `${count[k]}/${done.length} 场`;

  if (waitN >= 1 && waitN * 2 >= done.length) {
    return { prompt: REGIME, from: `你有 ${waitN} 场选择观望，而且说得出在等什么：把“等什么”写成每天能检查的信号` };
  }
  if (top === "price") {
    const r = done.find((x) => x.reason === "price")!;
    const id = PRICE_BY_SCENE[r.scene!];
    const v = id ? view(id) : null;
    const prompt = v?.qube || PRICE_RAW[r.scene!] || view("rule-vol2x")!.qube!;
    return { prompt, from: `你的理由最常是“量价”（${tally("price")}），在${short(r)}也是看走势做的决定` };
  }
  if (top === "data") {
    const r = done.find((x) => x.reason === "data")!;
    const v = view(r.scene === "smt" ? "rule-lowpb-roe" : "rule-val80");
    return { prompt: v!.qube!, from: `你的理由最常是“数据”（${tally("data")}）：把“贵不贵”写成规则，让历史检验它` };
  }
  if (top === "news" || top === "follow") {
    return { prompt: view("rule-wait3")!.qube!, from: `你的理由常是“${cn(top)}”（${tally(top)}）：先验一验，听到消息马上买和等三天再买，差别有多大` };
  }
  if (top === "lost" || top === "gut") {
    return { prompt: view("rule-stop10")!.qube!, from: `你的理由常是“${cn(top)}”（${tally(top)}）：先从一条最简单的规则开始，让回测替你看图` };
  }
  return { prompt: view("rule-stop10")!.qube!, from: "先从一条最简单的规则开始" };
}
