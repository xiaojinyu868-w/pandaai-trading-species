import type { Scene } from "../data";
import { sharesOf } from "./engine";
import type { SeasonRec } from "./store";

export interface TradeTag { t: string; sub: string; good: boolean | null }

const SOLD = ["sell", "leave", "stop"];
const ADDED = ["add", "enter"];
const w = (n: number) => `${Math.abs(n)} 万`;

/** 用股民的说法总结这一场：拿你的实际结果，和“按选项一直拿着”比 */
export function tradeTag(scene: Scene, r: SeasonRec): TradeTag | null {
  const m = r.money;
  if (!m || !r.option) return null;
  const s0 = sharesOf(scene, r.option);
  const rows = scene.reveal.payoff_rows;
  const held = rows.find((x) => x.key === r.option)?.total ?? m.total;
  const top = rows.reduce((a, x) => (x.shares > a.shares ? x : a), rows[0]);
  const acts = r.ff?.actions || [];
  const byPlan = !!r.ff?.planTriggered && !!r.ff?.planFollowed;
  const sold = !!r.ff?.sellDay || acts.some((a) => SOLD.includes(a)) || (byPlan && r.plan === "cut");
  const added = acts.some((a) => ADDED.includes(a)) || (byPlan && r.plan === "add");
  const you = m.total;
  if (r.ff?.debt) return { t: "穿仓倒欠", sub: "亏得比本金还多，账户成了负数", good: false };
  if (s0 === 0 && !added) {
    if (top.total > 0) return { t: "踏空", sub: `空仓看着它涨：重仓的人赚了 ${w(top.total)}`, good: null };
    if (top.total < 0) return { t: "躲过一劫", sub: `一分没亏：重仓的人亏了 ${w(top.total)}`, good: true };
    return { t: "空仓观望", sub: "这一段没什么行情", good: null };
  }
  if (you > 0) {
    if (sold && you < held) return { t: "卖飞了", sub: `卖早了：一直拿着能赚 ${w(held)}`, good: null };
    if (sold && you > held) return { t: "高位落袋", sub: `卖对了：一直拿着只${held >= 0 ? "赚" : "亏"} ${w(held)}`, good: true };
    if (added) return { t: s0 === 0 ? "抄到了" : "加仓吃肉", sub: `这一场赚了 ${w(you)}`, good: true };
    return { t: s0 >= 2 ? "重仓吃肉" : "小赚一笔", sub: `这一场赚了 ${w(you)}`, good: true };
  }
  if (you < 0) {
    if (sold && you > held) return { t: "及时止损", sub: `少亏了 ${w(you - held)}：一直拿着要亏 ${w(held)}`, good: true };
    if (sold && you < held) return { t: "割在地板", sub: held >= 0 ? `刚卖完就涨回去：一直拿着能赚 ${w(held)}` : `卖完它反弹了：一直拿着只亏 ${w(held)}`, good: false };
    if (added) return { t: s0 === 0 ? "一进场就被套" : "越补越套", sub: `这一场亏了 ${w(you)}`, good: false };
    return { t: `被套 ${s0} 份`, sub: `拿着没动，亏了 ${w(you)}`, good: false };
  }
  if (sold) return { t: "白忙一场", sub: "进进出出，最后不赚不亏", good: null };
  if (added) return { t: "进场打平", sub: "进去了，最后不赚不亏", good: null };
  return { t: "原地踏步", sub: "拿着没动，不赚不亏", good: null };
}
