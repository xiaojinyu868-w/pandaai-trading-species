import { motion } from "framer-motion";
import { useState } from "react";
import rulesEval from "../data/rules_eval.json";
import { sceneById, SCENES } from "../data";
import { RULES, ruleView } from "../game/cards";
import type { Profile } from "../game/engine";
import type { Game } from "../game/store";
import { sfx } from "../lib/sound";
import { LineChart } from "../ui/Chart";
import { ExampleTag, Money } from "../ui/kit";

const EV: any = rulesEval;

function Hypo({ g }: { g: Game }) {
  const kept = g.rules.filter((r) => EV.rules?.[r]);
  const options = kept.length ? kept : ["rule-ma520"];
  const [rule, setRule] = useState(options[0]);
  const played = g.seasons.filter((r) => r.scene && (r.money || r.option));
  const rows = played.map((r) => {
    const res = EV.rules?.[rule]?.[r.scene!];
    const scene = sceneById(r.scene!)!;
    const mine = r.money ? r.money.total : scene.reveal.payoff_rows.find((x) => x.key === r.option)?.total ?? 0;
    return { r, res, scene, mine };
  });
  const ruleTotal = rows.reduce((a, x) => a + (x.res?.applicable ? x.res.total : 0), 0);
  const myTotal = rows.reduce((a, x) => a + x.mine, 0);
  const revealed = g.seasons.filter((r) => r.stars).map((r) => r.scene!);
  const nameOf = (id: string) => { const r = RULES.find((x) => x.id === id); return r ? ruleView(r, revealed).name : id; };
  const name = nameOf(rule);
  return (
    <div>
      <div className="small">把{kept.length ? "你在研究所留下的" : "最常用的"}规则放回你走过的名场面：每天收盘看信号，第二天开盘照做，一直算到第 20 个交易日。</div>
      {options.length > 1 && <div className="row wrap gap6 mt8">{options.map((o) => <button key={o} className={"chip" + (o === rule ? " on" : "")} onClick={() => setRule(o)}>{nameOf(o)}</button>)}</div>}
      <table className="ptable mt8">
        <thead><tr><th>名场面</th><th>规则怎么做</th><th>规则</th><th>你</th></tr></thead>
        <tbody>
          {rows.map(({ res, scene, mine }) => (
            <tr key={scene.id}>
              <td>{scene.season_cn} · {scene.title.split(" · ")[0]}</td>
              <td className="tiny" style={{ textAlign: "left" }}>{res ? (res.applicable ? res.trades.map((t: any) => `${t.date.slice(5)} ${t.action}`).join("；") : res.note) : "这条规则不适用于这个产品"}</td>
              <td>{res?.applicable ? <Money n={res.total} /> : "—"}</td>
              <td><Money n={mine} /></td>
            </tr>
          ))}
          <tr className="me"><td>合计</td><td /><td><Money n={ruleTotal} /></td><td><Money n={myTotal} /></td></tr>
        </tbody>
      </table>
      <div className="small mt8">{ruleTotal > myTotal ? `只看这几场，“${name}”比你多赚 ${ruleTotal - myTotal}。` : ruleTotal < myTotal ? `只看这几场，你比“${name}”多赚 ${myTotal - ruleTotal}。` : `只看这几场，你和“${name}”打平。`}几场不够下结论：下一步把它拉长到十年历史。</div>
      <div className="tiny mt4">{EV.note} 你的数字是按收益账算的“合计”，认出来的场次也按你自己的选择算。</div>
    </div>
  );
}

const CLAIMS = [
  { q: "924 行情节后第一天，沪深两市全天成交额约 3.45 万亿元，创历史纪录。", a: true, why: "公开报道的数字。游戏里标了“公开报道”，因为它不是从行情接口算出来的。" },
  { q: "2015 年 6 月 12 日上证指数收在 5166 点，之后到 2024 年底再也没回到过这个位置。", a: true, why: "用上证指数日线核对：2015-06-12 之后到 2024-12-31，最高收盘没有超过它。" },
  { q: "2020 年 3 月，美股在十天里熔断了 3 次。", a: false, why: "是 4 次：3 月 9 日、12 日、16 日、18 日。标普 500 日线可以核对每一天的跌幅。" },
];

function Verify() {
  const [ans, setAns] = useState<(boolean | null)[]>([null, null, null]);
  return (
    <div className="col gap8">
      <div className="row between"><div className="small">三条“流传的说法”，你觉得哪条是真的？</div><ExampleTag>示例核查题</ExampleTag></div>
      {CLAIMS.map((c, i) => (
        <div key={i} className="card flat" style={{ padding: 10, background: ans[i] == null ? "#FBF4E4" : ans[i] === c.a ? "#E3F0D9" : "#FBE3DC" }}>
          <div className="small bold">{c.q}</div>
          {ans[i] == null ? (
            <div className="row gap6 mt8"><button className="chip" onClick={() => { sfx.tap(); setAns(ans.map((x, j) => (j === i ? true : x))); }}>真</button><button className="chip" onClick={() => { sfx.tap(); setAns(ans.map((x, j) => (j === i ? false : x))); }}>假</button></div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="small mt4">{ans[i] === c.a ? "✅ 对了。" : "❌ 不对。"}答案：{c.a ? "真" : "假"}。{c.why}</motion.div>
          )}
        </div>
      ))}
    </div>
  );
}

function ChartDrill() {
  const s = SCENES.find((x) => x.id === "s924")!;
  const v = s.evidence.price.chart?.values || [];
  const [a, setA] = useState<number | null>(null);
  const opts = ["最后一天成交量突然放大到平时的 3 倍多", "成交量一直很平稳", "最后几天成交量在萎缩"];
  return (
    <div>
      <div className="small">30 秒读图：这是 924 前 40 天的成交量（÷ 一年日均）。哪句话对？</div>
      <div className="card flat mt8" style={{ padding: 8 }}><LineChart values={v} height={80} animateDraw /></div>
      <div className="col gap6 mt8">{opts.map((o, i) => <button key={i} className={"opt" + (a === i ? " on" : "")} style={{ gridTemplateColumns: "1fr", background: a != null && i === 0 ? "#E3F0D9" : undefined }} onClick={() => setA(i)}>{o}</button>)}</div>
      {a != null && <div className="small mt8">{a === 0 ? "✅ 对。放量本身不说明涨跌，但说明“所有人都在同一时间行动”。" : "再看一眼最右边：最后几根是不是突然变高了？"}</div>}
    </div>
  );
}

function Explore() {
  const [sid, setSid] = useState("s2015");
  const s = sceneById(sid)!;
  const days = s.path?.days || [];
  const t = s.path?.t || 0;
  const code = { s924: "000001.SH", s2015: "000001.SH", smt: "600519.SH", squant: "399303.SZ", scb: "NDX", soil: "" }[sid as "s924"];
  const fn = sid === "smt" ? "get_stock_daily" : "get_index_daily";
  return (
    <div>
      <div className="small">改一行参数，重跑一个名场面。选一个场景：</div>
      <div className="row wrap gap6 mt8">{["s924", "s2015", "smt", "squant"].map((k) => <button key={k} className={"chip" + (k === sid ? " on" : "")} onClick={() => setSid(k)}>{sceneById(k)!.title.split(" · ")[0]}</button>)}</div>
      <pre style={{ background: "#1f2a26", color: "#d9f0c8", borderRadius: 12, padding: 12, fontSize: 12, marginTop: 8, overflowX: "auto" }}>{`import panda_data\ndf = panda_data.${fn}(\n    symbol="${code}",\n    start_date="${days[0]?.date.replace(/-/g, "")}",\n    end_date="${days[t + 5]?.date.replace(/-/g, "")}")\nprint(df[["date", "close"]].tail(6))`}</pre>
      <table className="ptable" style={{ fontFamily: "monospace" }}>
        <tbody>{days.slice(t, t + 6).map((d) => <tr key={d.date}><td>{d.date}</td><td>{d.close.toFixed(2)}</td></tr>)}</tbody>
      </table>
      <div className="tiny mt4">输出用游戏里的真实日线预先算好（数据来自 Panda Data）；在自己电脑上装好 panda_data、登录后就能跑出同样的表。</div>
    </div>
  );
}

const SIGNALS = ["5 日均线重新站上 20 日均线", "成交量回到一年均值附近", "估值回到历史中位数以下", "融资余额连续两周下降", "波动率回落到 20 以下", "政策细则真正落地"];
function Regime() {
  const [on, setOn] = useState<string[]>([]);
  return (
    <div>
      <div className="row between"><div className="small">你在等哪三个信号？选三个：</div><ExampleTag /></div>
      <div className="row wrap gap6 mt8">{SIGNALS.map((s) => <button key={s} className={"chip" + (on.includes(s) ? " on" : "")} disabled={!on.includes(s) && on.length >= 3} onClick={() => setOn(on.includes(s) ? on.filter((x) => x !== s) : [...on, s])}>{s}</button>)}</div>
      {on.length === 3 && <div className="small mt8">写下来了。下一步：让市场状态智能体每天替你检查这三条，满足几条就提醒你一次。</div>}
    </div>
  );
}

function Risk({ g }: { g: Game }) {
  const a = g.seasons.filter((r) => r.option === "A").length;
  return <div className="small">游戏里你有 {a} 场选了最激进的 A{g.real?.drop ? `；现实里上次大跌你${g.real.drop}` : ""}。没有真钱的时候，人往往更敢。模拟盘的压力更接近真实，是校准风险姿态的下一层。</div>;
}

export function TaskNow({ p, g }: { p: Profile; g: Game }) {
  const t = p.rec.main;
  return (
    <div className="card" style={{ background: "#FFFDF6" }}>
      <div className="row between"><div className="kicker">当场就能做 · {t.cn}</div><span className="pill">约 1 分钟</span></div>
      <div className="mt8">
        {t.type === "hypo" && <Hypo g={g} />}
        {t.type === "verify" && <Verify />}
        {t.type === "chart" && <ChartDrill />}
        {t.type === "explore" && <Explore />}
        {t.type === "regime" && <Regime />}
        {t.type === "risk" && <Risk g={g} />}
      </div>
      <div className="tiny mt8">做完，再去上面的真实入口接着做。</div>
    </div>
  );
}
