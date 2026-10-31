import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { Scene } from "../data";
import { money, pct, sharesOf } from "../game/engine";
import { aiPick, sp } from "../game/meta";
import { cur, useGame } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { LineChart } from "../ui/Chart";
import { Fade, SpeciesAvatar } from "../ui/kit";
import { Big, FFHeader, PlanPrompt, PosBar, useFinish } from "./common";

const md = (d: string) => `${Number(d.slice(5, 7))} 月 ${Number(d.slice(8, 10))} 日`;

/* ---------------- 秋 · 茅台：抱团圈 ---------------- */
export function FFMoutai({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const card = scene.fast_forward.cards[0];
  const path = scene.path!;
  const t1 = path.t + 1;
  const e0 = path.ends[0];
  const s0 = sharesOf(scene, rec.option);
  const dip = card.dip;
  const planOn = !!rec.plan && rec.plan !== "none" && !!dip && (s0 > 0 || rec.plan === "add");
  const [phase, setPhase] = useState<"week" | "plan" | "ring" | "reveal" | "done">("week");
  const [k, setK] = useState(t1);
  const [shares, setShares] = useState(s0);
  const [seg1, setSeg1] = useState(0);
  const [planFollowed, setPlanFollowed] = useState<boolean | null>(null);
  const [choice, setChoice] = useState<"stay" | "leave" | null>(null);
  const ruleSaysStay = rec.reason === "rule" && (rec.ruleId === "rule-ma520" || rec.ruleId === "rule-ma52060") && !card.signal?.red;

  useEffect(() => {
    if (phase !== "week") return;
    if (k > e0) {
      const after = () => {
        if (planOn && planFollowed === null) return setPhase("plan");
        settleWeek(null);
      };
      const t = setTimeout(after, 600);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => { sfx.tick(); setK((x) => x + 1); }, 700);
    return () => clearTimeout(t);
  }, [phase, k]);

  function settleWeek(follow: boolean | null) {
    let r = s0 * card.per_share;
    let s = s0;
    if (follow && dip) {
      if (rec.plan === "cut") {
        r = s0 * dip.per_share_at_trigger;
        s = 0;
      } else {
        r = s0 * dip.per_share_at_trigger + (s0 + 1) * dip.rest_per_share;
        s = s0 + 1;
      }
    }
    setSeg1(r);
    setShares(s);
    s > 0 ? setPhase("ring") : setPhase("reveal");
    sfx.loss();
  }

  const actors = [
    ...g!.opponents.map((id) => {
      const p = aiPick(id, scene.id);
      const has = sharesOf(scene, p.option) > 0;
      return { id, has, leave: has && p.ff === "sell" };
    }),
  ];
  const meLeave = choice === "leave";
  const leavers = actors.filter((a) => a.leave).length + (meLeave ? 1 : 0);
  const squeeze = meLeave ? -(leavers - 1) : 0;
  const aiExtra = Object.fromEntries(actors.map((a) => [a.id, a.leave ? -(leavers - 1) : 0]));

  function done() {
    const seg2 = meLeave ? 0 : shares * scene.reveal.seg2.per_share;
    finish({
      seg1, seg2, extra: squeeze, aiExtra,
      ff: { actions: choice ? [choice] : [], changes: meLeave ? 1 : 0, planTriggered: planOn, planFollowed: planOn ? planFollowed : true, ruleFollowed: ruleSaysStay ? !meLeave : null, leavers },
    });
    setPhase("done");
  }

  const week = path.days.slice(t1 - 3, Math.min(k, e0) + 1);
  const closeNow = path.days[Math.min(k, e0)]?.close;
  const fromT = pct(path.days[path.t].close, closeNow);
  const crowd = 10;
  return (
    <div>
      <FFHeader scene={scene} kicker={card.lines[0]} />
      <div className="card mt12">
        <div className="row between">
          <div>
            <div className="tiny">{md(path.days[Math.min(k, e0)].date)} · {path.instrument}</div>
            <div className="display num" style={{ fontSize: 40 }}>{closeNow?.toFixed(0)}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="tiny">5/20 双均线信号灯</div>
            <div className="row gap6 mt4" style={{ justifyContent: "flex-end" }}>
              <motion.i animate={{ opacity: card.signal?.red ? 1 : 0.2 }} style={{ width: 22, height: 22, borderRadius: "50%", background: "#D4432A", border: "2px solid #2A2A1C", display: "inline-block" }} />
              <motion.i animate={{ opacity: card.signal?.red ? 0.2 : 1, boxShadow: card.signal?.red ? "none" : "0 0 12px #6FA463" }} style={{ width: 22, height: 22, borderRadius: "50%", background: "#3C7A4E", border: "2px solid #2A2A1C", display: "inline-block" }} />
            </div>
            <div className={"bold mt4 " + (fromT >= 0 ? "up" : "down")}>{fromT >= 0 ? "+" : "−"}{Math.abs(fromT).toFixed(1)}%</div>
          </div>
        </div>
        <LineChart values={week.map((d) => d.close)} height={90} animateDraw={false} color="#2A2A1C" />
        <div className="tiny">信号灯还是绿灯：按 5/20 双均线规则，此刻不卖。</div>
      </div>
      <AnimatePresence>
        {phase === "plan" && dip && (
          <div className="mt12">
            <PlanPrompt plan={rec.plan as "cut" | "add"} pctNow={dip.pct_at_trigger} shares={s0}
              onFollow={() => { sfx.stamp(); setPlanFollowed(true); settleWeek(true); }}
              onIgnore={() => { setPlanFollowed(false); settleWeek(false); }} />
          </div>
        )}
      </AnimatePresence>
      {(phase === "ring" || phase === "reveal" || phase === "done") && (
        <Fade>
          <div className="mt12"><PosBar shares={meLeave ? 0 : shares} pnl={seg1 + (phase === "done" ? (cur(g!).money?.seg2 ?? 0) + squeeze : 0)} /></div>
          <div className="card mt12 center" style={{ background: "#2D5F6B", color: "#FBF4E4", padding: 16 }}>
            <b className="h3">抱团圈</b>
            <div style={{ position: "relative", width: 250, height: 250, margin: "10px auto 0" }}>
              <motion.div animate={{ scale: phase === "reveal" || phase === "done" ? 0.8 : 1 }} style={{ position: "absolute", inset: 70, borderRadius: "50%", background: "radial-gradient(circle, #F3D27F, #C79A2E)", border: "3px solid #2A2A1C", display: "grid", placeItems: "center", fontFamily: "var(--display)", fontSize: 22, color: "#2A2A1C" }}>顶流</motion.div>
              {Array.from({ length: crowd }).map((_, i) => {
                const a = (i / (crowd + actors.length + 1)) * Math.PI * 2;
                const out = (phase === "reveal" || phase === "done") && i % 3 === 0;
                return (
                  <motion.span key={i} animate={{ left: 125 + Math.cos(a) * (out ? 150 : 100) - 11, top: 125 + Math.sin(a) * (out ? 150 : 100) - 11, opacity: out ? 0.3 : 1 }} transition={{ duration: 0.9 }}
                    style={{ position: "absolute", width: 22, height: 22, borderRadius: "50%", background: ["#D4432A", "#C79A2E", "#A3AE91", "#9CC3C6"][i % 4], border: "2px solid #FBF4E4" }} />
                );
              })}
              {actors.map((x, j) => {
                const a = ((crowd + j) / (crowd + actors.length + 1)) * Math.PI * 2;
                const out = (phase === "reveal" || phase === "done") && x.leave;
                return (
                  <motion.div key={x.id} animate={{ left: 125 + Math.cos(a) * (out ? 150 : 100) - 17, top: 125 + Math.sin(a) * (out ? 150 : 100) - 17 }} transition={{ duration: 0.9 }} style={{ position: "absolute" }}>
                    <SpeciesAvatar id={x.id} size={34} />
                  </motion.div>
                );
              })}
              {(() => {
                const a = ((crowd + actors.length) / (crowd + actors.length + 1)) * Math.PI * 2;
                const out = (phase === "reveal" || phase === "done") && meLeave;
                return (
                  <motion.div animate={{ left: 125 + Math.cos(a) * (out ? 150 : 100) - 18, top: 125 + Math.sin(a) * (out ? 150 : 100) - 18 }} transition={{ duration: 0.9 }}
                    style={{ position: "absolute", width: 36, height: 36, borderRadius: "50%", background: "#D4432A", border: "2px solid #FBF4E4", display: "grid", placeItems: "center", fontWeight: 900 }}>你</motion.div>
                );
              })()}
            </div>
            {phase === "ring" && (
              <>
                <div className="body mt8">{card.then}</div>
                {ruleSaysStay && <div className="pill warn mt8">你用了 5/20 规则牌：绿灯，规则说留下</div>}
                <div className="row gap8 mt12">
                  <button className="btn grow" onClick={() => { sfx.tap(); setChoice("stay"); setPhase("reveal"); buzz(30); }}>留下</button>
                  <button className="btn primary grow" onClick={() => { sfx.tap(); setChoice("leave"); setPhase("reveal"); buzz(30); }}>离开</button>
                </div>
                <div className="tiny mt8" style={{ color: "#cfe1e1" }}>大家同时选，选完一起公布。同时离开的人每多 1 个，每个离开的人多亏 1 万（出口挤，游戏化处理）。</div>
              </>
            )}
            {(phase === "reveal" || phase === "done") && (
              <div className="mt8 small">
                {actors.map((a) => <div key={a.id}>{sp(a.id).cn}：{a.has ? (a.leave ? "离开" : "留下") : "早就不在圈里"}</div>)}
                {shares > 0 && <div className="bold">你：{meLeave ? "离开" : "留下"}{meLeave && leavers > 1 ? `，和 ${leavers - 1} 只一起挤出口：−${leavers - 1}` : ""}</div>}
              </div>
            )}
          </div>
          {phase === "reveal" && (
            <button className="btn season block mt12" onClick={() => { sfx.loss(); done(); }}>再过三周 →</button>
          )}
          {phase === "done" && (
            <div className="card mt12" style={{ background: "#FFF6DE" }}>
              <div className="small">{scene.reveal.seg2.label}：{scene.reveal.seg2.pct > 0 ? "+" : ""}{scene.reveal.seg2.pct}%。{meLeave || !shares ? "你已经不在场，这一段不影响你。" : `你还拿着 ${shares} 份，这一段 ${money(shares * scene.reveal.seg2.per_share)} 万。`}</div>
            </div>
          )}
        </Fade>
      )}
    </div>
  );
}

/* ---------------- 冬 · 熔断：黑屏冻结 + 调一档 + 第二次决定 ---------------- */
export function FFBreaker({ scene }: { scene: Scene }) {
  const { g } = useGame();
  const rec = cur(g!);
  const finish = useFinish(scene);
  const cards = scene.fast_forward.cards;
  const s0 = sharesOf(scene, rec.option);
  const planOn = !!rec.plan && rec.plan !== "none" && (s0 > 0 || rec.plan === "add");
  const FREEZE = 12;
  const [ci, setCi] = useState(0);
  const [phase, setPhase] = useState<"alarm" | "settle" | "freeze" | "dial" | "plan" | "second" | "done">("alarm");
  const [shares, setShares] = useState(s0);
  const [realized, setRealized] = useState(0);
  const [changes, setChanges] = useState(0);
  const [left, setLeft] = useState(FREEZE);
  const [planFollowed, setPlanFollowed] = useState<boolean | null>(null);
  const [touched, setTouched] = useState(0);
  const settledRef = useRef(-1);
  const c = cards[ci];

  useEffect(() => {
    if (phase === "alarm") {
      sfx.alarm();
      const t = setTimeout(() => setPhase("settle"), 2200);
      return () => clearTimeout(t);
    }
    if (phase === "settle" && settledRef.current !== ci) {
      settledRef.current = ci;
      setRealized((r) => r + shares * c.per_share);
      c.per_share < 0 ? sfx.loss() : sfx.coin();
    }
    if (phase === "freeze") {
      setLeft(FREEZE);
      let n = FREEZE;
      const id = setInterval(() => {
        n -= 1;
        setLeft(n);
        sfx.heart();
        if (n <= 0) {
          clearInterval(id);
          setPhase(ci === 0 && planOn && planFollowed === null && c.dropped ? "plan" : "dial");
        }
      }, 1000);
      return () => clearInterval(id);
    }
  }, [phase, ci]);

  function next(delta: number) {
    if (delta) setChanges((x) => x + 1);
    setShares((s) => Math.max(0, Math.min(4, s + delta)));
    sfx.tap();
    setCi((x) => x + 1);
    setPhase("alarm");
  }

  function second(k: "add" | "stop" | "ignore") {
    let s = shares;
    if (k === "add") s += 1;
    if (k === "stop") s = 0;
    const seg2 = s * scene.reveal.seg2.per_share;
    finish({
      seg1: realized, seg2, extra: 0,
      ff: { actions: [k], changes, planTriggered: planOn && planFollowed !== null, planFollowed: planOn && planFollowed !== null ? planFollowed : true, ruleFollowed: null, second: k },
    });
    setShares(s);
    setPhase("done");
    sfx.stamp();
  }

  const freezeNews = [...scene.blind.lines, ...c.lines.slice(0, 1), "有人在群里说：这次不一样。", "有人说：越跌越买，迟早涨回来。"];
  return (
    <div>
      <FFHeader scene={scene} kicker={`第 ${Math.min(ci + 1, 3)} 张熔断牌 / 3`} />
      <AnimatePresence mode="wait">
        {phase === "alarm" && (
          <motion.div key={"a" + ci} initial={{ opacity: 0 }} animate={{ opacity: 1, backgroundColor: ["#D4432A", "#7a1d10", "#D4432A"] }} transition={{ backgroundColor: { repeat: Infinity, duration: 0.6 } }}
            className="card center mt16" style={{ color: "#fff", padding: "34px 12px", borderColor: "#2A2A1C" }}>
            <div className="kicker" style={{ color: "#fff" }}>{c.title}</div>
            <motion.div className="display" style={{ fontSize: 76 }} animate={{ scale: [1, 1.08, 1] }} transition={{ repeat: Infinity, duration: 0.6 }}>熔断</motion.div>
            <div className="h3">标普 500 当天 {c.us_pct}%</div>
            <div className="small mt8">跌到阈值，交易所暂停交易 15 分钟</div>
          </motion.div>
        )}
        {phase === "settle" && (
          <motion.div key={"s" + ci} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt16 col gap12">
            <div className="card">
              <b className="h3">{c.title}</b>
              <ul className="body" style={{ paddingLeft: 18, margin: "8px 0 0" }}>{c.lines.map((l, i) => <li key={i}>{l}</li>)}</ul>
              <div className="row between mt8"><span>这一段每份</span><b className={c.per_share < 0 ? "down" : c.per_share > 0 ? "up" : ""}>{c.per_share > 0 ? "+" : ""}{c.per_share}</b></div>
              <div className="row between"><span>你 {shares} 份</span><b className={shares * c.per_share < 0 ? "down" : ""}>{shares * c.per_share > 0 ? "+" : ""}{shares * c.per_share}</b></div>
            </div>
            <PosBar shares={shares} pnl={realized} />
            <button className="btn dark big block" onClick={() => { setTouched(0); setPhase(ci < cards.length - 1 ? "freeze" : "second"); }}>
              {ci < cards.length - 1 ? `翻沙漏：${FREEZE} 秒冷静期` : "第三次熔断之后……"}
            </button>
          </motion.div>
        )}
        {phase === "freeze" && (
          <motion.div key={"f" + ci} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt16" onClick={() => { setTouched((t) => t + 1); buzz(20); }}
            style={{ background: "#111", color: "#FBF4E4", borderRadius: 18, border: "2px solid #2A2A1C", padding: 20, minHeight: 360, position: "relative", overflow: "hidden" }}>
            <div className="center">
              <div className="kicker" style={{ color: "#F3D27F" }}>冷静期 · 交易暂停，什么也做不了</div>
              <svg width="90" height="130" viewBox="0 0 90 130" style={{ margin: "14px auto", display: "block" }}>
                <path d="M10 5 H80 M10 125 H80 M18 5 C18 50 72 60 72 120 M72 5 C72 50 18 60 18 120" stroke="#F3D27F" strokeWidth="4" fill="none" />
                <motion.path d="M24 14 H66 L45 58 Z" fill="#C79A2E" initial={{ scaleY: 1 }} animate={{ scaleY: 0 }} transition={{ duration: FREEZE, ease: "linear" }} style={{ originY: "58px", transformBox: "fill-box" as any }} />
                <motion.path d="M45 70 L66 118 H24 Z" fill="#C79A2E" initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ duration: FREEZE, ease: "linear" }} style={{ originY: "118px", transformBox: "fill-box" as any }} />
              </svg>
              <Big color="#FBF4E4">{left}</Big>
            </div>
            <div className="col gap6 mt12">
              {freezeNews.slice(0, Math.min(freezeNews.length, Math.floor((FREEZE - left) / 2) + 1)).map((t, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 0.85, x: 0 }} className="small" style={{ borderLeft: "3px solid #D4432A", paddingLeft: 8 }}>{t}</motion.div>
              ))}
            </div>
            {touched > 0 && <div className="tiny center mt12" style={{ color: "#F3D27F" }}>手放下。现在什么也做不了（你碰了 {touched} 次）</div>}
          </motion.div>
        )}
        {phase === "plan" && (
          <motion.div key="plan" className="mt16">
            <PlanPrompt plan={rec.plan as "cut" | "add"} pctNow={c.pct} shares={shares}
              onFollow={() => {
                setPlanFollowed(true);
                sfx.stamp();
                setShares((s) => (rec.plan === "cut" ? 0 : s + 1));
                setCi((x) => x + 1);
                setPhase("alarm");
              }}
              onIgnore={() => { setPlanFollowed(false); setPhase("dial"); }} />
          </motion.div>
        )}
        {phase === "dial" && (
          <motion.div key={"d" + ci} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="mt16 card center">
            <b className="h3">时间到。要调一档吗？</b>
            <div className="small muted mt4">调好的仓位从下一张熔断牌开始算。每调一次，记一次“改主意”。</div>
            <div className="row gap8 mt16">
              <button className="btn grow" disabled={shares <= 0} onClick={() => next(-1)}>减 1 份</button>
              <button className="btn dark grow" onClick={() => next(0)}>不动</button>
              <button className="btn grow" onClick={() => next(1)}>加 1 份</button>
            </div>
            <div className="tiny mt8">现在 {shares} 份</div>
          </motion.div>
        )}
        {phase === "second" && (
          <motion.div key="second" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt16 card">
            <b className="h3">{scene.fast_forward.second_decision?.prompt}</b>
            <div className="small muted mt4">十天四次熔断。你手里还有 {shares} 份。</div>
            <div className="col gap8 mt12">
              <button className="btn block" onClick={() => second("add")}>补仓（多 1 份）</button>
              <button className="btn block" onClick={() => second("stop")}>止损（全部卖出）</button>
              <button className="btn block" onClick={() => second("ignore")}>不看了（保持不动）</button>
            </div>
          </motion.div>
        )}
        {phase === "done" && (
          <motion.div key="done" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt16 col gap12">
            <PosBar shares={shares} pnl={realized + shares * scene.reveal.seg2.per_share} />
            <div className="card" style={{ background: "#FFF6DE" }}>
              <div className="small">{scene.reveal.seg2.label}：{scene.reveal.seg2.pct > 0 ? "+" : ""}{scene.reveal.seg2.pct}%。{shares > 0 ? `你拿着 ${shares} 份，这一段 ${money(shares * scene.reveal.seg2.per_share)} 万。` : "你已经清仓，这一段不影响你。"}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
